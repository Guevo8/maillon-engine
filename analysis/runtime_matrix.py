from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.engine import GameConfig, GameEngine
from src.maillon_v04.rules import territory_threshold_60


DEFAULT_POLICIES = ("phase_player", "rusher", "utility_balancer")
RESOURCES = ("Holz", "Stein", "Korn")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Maillon v0.5 bot-vs-bot runtime matrix."
    )

    parser.add_argument(
        "--side-lengths",
        type=int,
        nargs="+",
        default=[4, 5],
        help="Board side lengths to test. Example: --side-lengths 4 5",
    )

    parser.add_argument(
        "--policies",
        nargs="+",
        default=list(DEFAULT_POLICIES),
        help="Bot policies to test. Example: --policies phase_player rusher utility_balancer",
    )

    parser.add_argument(
        "--max-rounds",
        type=int,
        default=120,
        help="Maximum rounds per matchup.",
    )

    parser.add_argument(
        "--actions-per-turn",
        type=int,
        default=3,
        help="Actions per actor turn.",
    )

    parser.add_argument(
        "--timeout-majority-margin",
        type=int,
        default=5,
        help=(
            "If max_rounds is reached without a winner, award timeout_majority "
            "to the controlled-field leader when the margin is at least this value. "
            "Use 0 to disable timeout adjudication."
        ),
    )

    parser.add_argument(
        "--out",
        default="analysis/reports/runtime_matrix.csv",
        help="CSV output path.",
    )

    return parser.parse_args()


def is_absorb(message: str) -> bool:
    return "raid_shield reduced" in message or "No takeover" in message


def neutral_field_count(engine: GameEngine) -> int:
    return sum(1 for cell in engine.state.cells.values() if cell.owner is None)


def timeout_adjudication(
    engine: GameEngine,
    *,
    margin: int,
) -> tuple[str | None, str, int]:
    """
    Analysis-only max-round adjudication.

    This does not change engine rules. It only classifies runtime-matrix rows
    that reached max_rounds without a normal winner.

    If one actor leads by at least `margin` controlled fields, the matrix marks
    that actor as timeout_majority. Otherwise the row remains a timeout_draw.
    """

    if margin <= 0:
        return None, "none", 0

    player_controlled = engine.state.controlled_count("player")
    enemy_controlled = engine.state.controlled_count("enemy")
    diff = player_controlled - enemy_controlled

    if abs(diff) < margin:
        return None, "timeout_draw", diff

    if diff > 0:
        return "player", "timeout_majority", diff

    return "enemy", "timeout_majority", diff


def win_reason(engine: GameEngine, winner: str | None) -> str:
    if winner is None:
        return "none"

    state = engine.state
    opponent = state.opponent(winner)
    neutral = neutral_field_count(engine)

    if state.non_core_controlled_count(opponent) == 0:
        return "domination"

    if state.controlled_count(winner) >= territory_threshold_60(state):
        return "territory"

    if neutral == 0:
        return "full_board_majority"

    return "unknown"


def final_shield_stats(engine: GameEngine) -> dict[str, int]:
    shield_values = [cell.raid_shield for cell in engine.state.cells.values()]

    return {
        "final_shielded_fields": sum(1 for value in shield_values if value > 0),
        "final_shield_points": sum(shield_values),
        "final_max_shield": max(shield_values) if shield_values else 0,
    }


def run_matchup(
    *,
    side_length: int,
    player_policy: str,
    enemy_policy: str,
    max_rounds: int,
    actions_per_turn: int,
    timeout_majority_margin: int,
) -> dict[str, int | str]:
    engine = GameEngine.new_game(
        GameConfig(
            side_length=side_length,
            actions_per_turn=actions_per_turn,
            bot_policy=enemy_policy,
            max_rounds=max_rounds,
        )
    )

    actions = Counter()
    actor_actions = {
        "player": Counter(),
        "enemy": Counter(),
    }

    waste = {
        "player": Counter(),
        "enemy": Counter(),
    }

    first_actor_counts = Counter()

    raid_takeovers = 0
    raid_absorbed = 0

    while not engine.is_game_over():
        first_actor_counts[engine.initiative_first_actor()] += 1

        result = engine.run_bot_vs_bot_round(
            player_policy=player_policy,
            enemy_policy=enemy_policy,
        )

        for actor in ("player", "enemy"):
            for resource in RESOURCES:
                waste[actor][resource] += result.production_waste[actor][resource]

        for turn in (result.player_turn, result.enemy_turn):
            if turn is None:
                continue

            for action_result in turn.actions:
                actor = action_result.action.actor
                action_type = action_result.action.action_type

                actions[action_type] += 1
                actor_actions[actor][action_type] += 1

                if action_type == "raid" and action_result.ok:
                    if is_absorb(action_result.message):
                        raid_absorbed += 1
                    else:
                        raid_takeovers += 1

        if result.winner is not None:
            break

    state = engine.state
    natural_winner = engine.current_winner()
    natural_reason = win_reason(engine, natural_winner)
    timeout_diff = 0

    if natural_winner is None:
        winner, reason, timeout_diff = timeout_adjudication(
            engine,
            margin=timeout_majority_margin,
        )
    else:
        winner = natural_winner
        reason = natural_reason

    shield_stats = final_shield_stats(engine)

    row: dict[str, int | str] = {
        "side_length": side_length,
        "board_size": state.board.size,
        "matchup": f"{player_policy}_vs_{enemy_policy}",
        "player_policy": player_policy,
        "enemy_policy": enemy_policy,
        "winner": winner or "",
        "win_reason": reason,
        "natural_winner": natural_winner or "",
        "natural_win_reason": natural_reason,
        "timeout_margin": timeout_majority_margin,
        "timeout_controlled_diff": timeout_diff,
        "final_round": state.round_index,
        "threshold_60": territory_threshold_60(state),
        "player_first_rounds": first_actor_counts["player"],
        "enemy_first_rounds": first_actor_counts["enemy"],
        "p_controlled": state.controlled_count("player"),
        "e_controlled": state.controlled_count("enemy"),
        "p_non_core": state.non_core_controlled_count("player"),
        "e_non_core": state.non_core_controlled_count("enemy"),
        "neutral_fields": neutral_field_count(engine),
        "build": actions["build"],
        "raid": actions["raid"],
        "raid_takeovers": raid_takeovers,
        "raid_absorbed_by_shield": raid_absorbed,
        "fortify": actions["fortify"],
        "rebuild": actions["rebuild"],
        "field_upgrade": actions["field_upgrade"],
        "core_upgrade": actions["core_upgrade"],
        "wait": actions["wait"],
        "p_build": actor_actions["player"]["build"],
        "p_raid": actor_actions["player"]["raid"],
        "p_fortify": actor_actions["player"]["fortify"],
        "p_rebuild": actor_actions["player"]["rebuild"],
        "p_wait": actor_actions["player"]["wait"],
        "e_build": actor_actions["enemy"]["build"],
        "e_raid": actor_actions["enemy"]["raid"],
        "e_fortify": actor_actions["enemy"]["fortify"],
        "e_rebuild": actor_actions["enemy"]["rebuild"],
        "e_wait": actor_actions["enemy"]["wait"],
        "p_holz_waste": waste["player"]["Holz"],
        "p_stein_waste": waste["player"]["Stein"],
        "p_korn_waste": waste["player"]["Korn"],
        "e_holz_waste": waste["enemy"]["Holz"],
        "e_stein_waste": waste["enemy"]["Stein"],
        "e_korn_waste": waste["enemy"]["Korn"],
        "p_holz": state.actor_state("player").resources["Holz"],
        "p_stein": state.actor_state("player").resources["Stein"],
        "p_korn": state.actor_state("player").resources["Korn"],
        "e_holz": state.actor_state("enemy").resources["Holz"],
        "e_stein": state.actor_state("enemy").resources["Stein"],
        "e_korn": state.actor_state("enemy").resources["Korn"],
        **shield_stats,
    }

    return row


def run_matrix(
    *,
    side_lengths: Iterable[int],
    policies: Iterable[str],
    max_rounds: int,
    actions_per_turn: int,
    timeout_majority_margin: int,
) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    policy_list = list(policies)

    for side_length in side_lengths:
        for player_policy in policy_list:
            for enemy_policy in policy_list:
                rows.append(
                    run_matchup(
                        side_length=side_length,
                        player_policy=player_policy,
                        enemy_policy=enemy_policy,
                        max_rounds=max_rounds,
                        actions_per_turn=actions_per_turn,
                        timeout_majority_margin=timeout_majority_margin,
                    )
                )

    return rows


def write_csv(path: Path, rows: list[dict[str, int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise ValueError("No rows to write.")

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    rows = run_matrix(
        side_lengths=args.side_lengths,
        policies=args.policies,
        max_rounds=args.max_rounds,
        actions_per_turn=args.actions_per_turn,
        timeout_majority_margin=args.timeout_majority_margin,
    )

    out_path = Path(args.out)
    write_csv(out_path, rows)

    print(f"Wrote {out_path} with {len(rows)} rows")

    print(
        "board,matchup,winner,reason,natural_winner,natural_reason,round,p/e/n,"
        "timeout_diff,fortify,absorbed,takeovers,rebuild,p_rebuild,e_rebuild,"
        "p_korn_waste,e_korn_waste,shield_points"
    )
    for row in rows:
        print(
            f"{row['board_size']},"
            f"{row['matchup']},"
            f"{row['winner']},"
            f"{row['win_reason']},"
            f"{row['natural_winner']},"
            f"{row['natural_win_reason']},"
            f"{row['final_round']},"
            f"{row['p_controlled']}/{row['e_controlled']}/{row['neutral_fields']},"
            f"{row['timeout_controlled_diff']},"
            f"{row['fortify']},"
            f"{row['raid_absorbed_by_shield']},"
            f"{row['raid_takeovers']},"
            f"{row['rebuild']},"
            f"{row['p_rebuild']},"
            f"{row['e_rebuild']},"
            f"{row['p_korn_waste']},"
            f"{row['e_korn_waste']},"
            f"{row['final_shield_points']}"
        )


if __name__ == "__main__":
    main()
