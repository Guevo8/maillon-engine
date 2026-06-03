from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Literal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.bot import BotPolicy
from src.maillon_v04.engine import ActorTurnResult, GameConfig, GameEngine
from src.maillon_v04.rules import territory_threshold_60


POLICIES: tuple[BotPolicy, ...] = ("phase_player", "rusher")
RESOURCES = ("Holz", "Stein", "Korn")
TurnOrder = Literal["player_first", "enemy_first"]


def is_shield_absorb(message: str) -> bool:
    return "raid_shield reduced" in message or "No takeover" in message


def win_reason(engine: GameEngine, winner: str | None) -> str:
    if winner is None:
        return "none"

    state = engine.state
    opponent = state.opponent(winner)  # type: ignore[arg-type]

    if state.non_core_controlled_count(opponent) == 0:
        return "domination"

    if state.controlled_count(winner) >= territory_threshold_60(state):  # type: ignore[arg-type]
        return "territory"

    return "unknown"


def shield_stats(engine: GameEngine) -> dict[str, int]:
    shielded_fields = 0
    shield_points = 0
    max_shield = 0

    for cell in engine.state.cells.values():
        shield = int(cell.raid_shield)

        if shield <= 0:
            continue

        shielded_fields += 1
        shield_points += shield
        max_shield = max(max_shield, shield)

    return {
        "final_shielded_fields": shielded_fields,
        "final_shield_points": shield_points,
        "final_max_shield": max_shield,
    }


def run_bot_vs_bot_round_ordered(
    engine: GameEngine,
    *,
    player_policy: BotPolicy,
    enemy_policy: BotPolicy,
    turn_order: TurnOrder,
) -> dict[str, Any]:
    """
    Bot-vs-Bot-Runde mit expliziter Zugreihenfolge.

    player_first entspricht der bisherigen Engine-Reihenfolge.
    enemy_first spiegelt nur die Reihenfolge, nicht die Startposition.
    """

    if engine.is_game_over():
        return {
            "round_index": engine.state.round_index,
            "production_waste": {
                "player": {"Holz": 0, "Stein": 0, "Korn": 0},
                "enemy": {"Holz": 0, "Stein": 0, "Korn": 0},
            },
            "player_turn": None,
            "enemy_turn": None,
            "winner": engine.current_winner(),
        }

    round_index = engine.state.round_index
    production_waste = engine.start_round()

    player_turn: ActorTurnResult | None = None
    enemy_turn: ActorTurnResult | None = None

    if turn_order == "player_first":
        player_turn = engine.run_bot_turn("player", player_policy)
        winner = engine.current_winner()

        if winner is None:
            enemy_turn = engine.run_bot_turn("enemy", enemy_policy)
            winner = engine.current_winner()

    elif turn_order == "enemy_first":
        enemy_turn = engine.run_bot_turn("enemy", enemy_policy)
        winner = engine.current_winner()

        if winner is None:
            player_turn = engine.run_bot_turn("player", player_policy)
            winner = engine.current_winner()

    else:
        raise ValueError(f"invalid turn_order: {turn_order}")

    if winner is None:
        engine.advance_round()

    return {
        "round_index": round_index,
        "production_waste": production_waste,
        "player_turn": player_turn,
        "enemy_turn": enemy_turn,
        "winner": winner,
    }


def collect_turn_metrics(
    *,
    result: dict[str, Any],
    action_counts: Counter[str],
    action_counts_by_actor: dict[str, Counter[str]],
) -> tuple[int, int, int]:
    raid_success_total = 0
    raid_takeovers = 0
    raid_absorbed_by_shield = 0

    turns = [result["player_turn"], result["enemy_turn"]]

    for turn in turns:
        if turn is None:
            continue

        for action_result in turn.actions:
            action = action_result.action
            action_type = action.action_type
            actor = action.actor
            message = action_result.message

            action_counts[action_type] += 1
            action_counts_by_actor[actor][action_type] += 1

            if action_type == "raid" and action_result.ok:
                raid_success_total += 1

                if is_shield_absorb(message):
                    raid_absorbed_by_shield += 1
                else:
                    raid_takeovers += 1

    return raid_success_total, raid_takeovers, raid_absorbed_by_shield


def run_matchup(
    *,
    side_length: int,
    player_policy: BotPolicy,
    enemy_policy: BotPolicy,
    max_rounds: int,
    actions_per_turn: int,
    turn_order: TurnOrder,
) -> dict[str, Any]:
    engine = GameEngine.new_game(
        GameConfig(
            side_length=side_length,
            actions_per_turn=actions_per_turn,
            bot_policy=enemy_policy,
            max_rounds=max_rounds,
        )
    )

    action_counts = Counter()
    action_counts_by_actor: dict[str, Counter[str]] = {
        "player": Counter(),
        "enemy": Counter(),
    }
    waste_totals: dict[str, Counter[str]] = {
        "player": Counter(),
        "enemy": Counter(),
    }

    raid_success_total = 0
    raid_takeovers = 0
    raid_absorbed_by_shield = 0

    while not engine.is_game_over():
        result = run_bot_vs_bot_round_ordered(
            engine,
            player_policy=player_policy,
            enemy_policy=enemy_policy,
            turn_order=turn_order,
        )

        for actor in ("player", "enemy"):
            for resource in RESOURCES:
                waste_totals[actor][resource] += int(
                    result["production_waste"].get(actor, {}).get(resource, 0)
                )

        round_raid_total, round_takeovers, round_absorbs = collect_turn_metrics(
            result=result,
            action_counts=action_counts,
            action_counts_by_actor=action_counts_by_actor,
        )

        raid_success_total += round_raid_total
        raid_takeovers += round_takeovers
        raid_absorbed_by_shield += round_absorbs

        if result["winner"] is not None:
            break

    winner = engine.current_winner()
    state = engine.state
    shields = shield_stats(engine)

    first_actor = "player" if turn_order == "player_first" else "enemy"
    winner_went_first = bool(winner == first_actor) if winner is not None else False

    row: dict[str, Any] = {
        "side_length": side_length,
        "board_size": state.board.size,
        "turn_order": turn_order,
        "first_actor": first_actor,
        "matchup": f"{player_policy}_vs_{enemy_policy}",
        "player_policy": player_policy,
        "enemy_policy": enemy_policy,
        "winner": winner,
        "winner_went_first": winner_went_first,
        "win_reason": win_reason(engine, winner),
        "final_round": state.round_index,
        "threshold_60": territory_threshold_60(state),
        "p_controlled": state.controlled_count("player"),
        "e_controlled": state.controlled_count("enemy"),
        "p_non_core": state.non_core_controlled_count("player"),
        "e_non_core": state.non_core_controlled_count("enemy"),
        "neutral_fields": sum(1 for cell in state.cells.values() if cell.owner is None),
        "build": action_counts["build"],
        "raid": action_counts["raid"],
        "raid_success_total": raid_success_total,
        "raid_takeovers": raid_takeovers,
        "raid_absorbed_by_shield": raid_absorbed_by_shield,
        "fortify": action_counts["fortify"],
        "rebuild": action_counts["rebuild"],
        "field_upgrade": action_counts["field_upgrade"],
        "core_upgrade": action_counts["core_upgrade"],
        "wait": action_counts["wait"],
        "p_build": action_counts_by_actor["player"]["build"],
        "p_raid": action_counts_by_actor["player"]["raid"],
        "p_fortify": action_counts_by_actor["player"]["fortify"],
        "p_wait": action_counts_by_actor["player"]["wait"],
        "e_build": action_counts_by_actor["enemy"]["build"],
        "e_raid": action_counts_by_actor["enemy"]["raid"],
        "e_fortify": action_counts_by_actor["enemy"]["fortify"],
        "e_wait": action_counts_by_actor["enemy"]["wait"],
        "p_holz_waste": waste_totals["player"]["Holz"],
        "p_stein_waste": waste_totals["player"]["Stein"],
        "p_korn_waste": waste_totals["player"]["Korn"],
        "e_holz_waste": waste_totals["enemy"]["Holz"],
        "e_stein_waste": waste_totals["enemy"]["Stein"],
        "e_korn_waste": waste_totals["enemy"]["Korn"],
        "p_holz": state.actor_state("player").resources["Holz"],
        "p_stein": state.actor_state("player").resources["Stein"],
        "p_korn": state.actor_state("player").resources["Korn"],
        "e_holz": state.actor_state("enemy").resources["Holz"],
        "e_stein": state.actor_state("enemy").resources["Stein"],
        "e_korn": state.actor_state("enemy").resources["Korn"],
        **shields,
    }

    return row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--side-lengths", type=int, nargs="+", default=[4, 5])
    parser.add_argument("--max-rounds", type=int, default=120)
    parser.add_argument("--actions-per-turn", type=int, default=3)
    parser.add_argument(
        "--turn-orders",
        choices=["player_first", "enemy_first"],
        nargs="+",
        default=["player_first", "enemy_first"],
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("analysis/reports/fortify_bot_matrix_v0_4.csv"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for side_length in args.side_lengths:
        for turn_order in args.turn_orders:
            for player_policy in POLICIES:
                for enemy_policy in POLICIES:
                    rows.append(
                        run_matchup(
                            side_length=side_length,
                            player_policy=player_policy,
                            enemy_policy=enemy_policy,
                            max_rounds=args.max_rounds,
                            actions_per_turn=args.actions_per_turn,
                            turn_order=turn_order,
                        )
                    )

    fieldnames = list(rows[0].keys())

    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {args.out} with {len(rows)} rows")


if __name__ == "__main__":
    main()
