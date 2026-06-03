from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.actions import apply_action
from src.maillon_v04.bot_utility import top_utility_scores
from src.maillon_v04.engine import ActorTurnResult, GameConfig, GameEngine
from src.maillon_v04.rules import territory_threshold_60
from src.maillon_v04.state import ActorId


DEFAULT_MATCHUPS = (
    "utility_balancer:phase_player",
    "utility_balancer:rusher",
    "utility_balancer:utility_balancer",
    "phase_player:utility_balancer",
    "rusher:utility_balancer",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe utility_balancer decisions action-by-action."
    )

    parser.add_argument(
        "--side-lengths",
        type=int,
        nargs="+",
        default=[4, 5],
    )

    parser.add_argument(
        "--matchups",
        nargs="+",
        default=list(DEFAULT_MATCHUPS),
        help="Matchups as player_policy:enemy_policy",
    )

    parser.add_argument(
        "--max-rounds",
        type=int,
        default=120,
    )

    parser.add_argument(
        "--actions-per-turn",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="How many top utility candidates to store per utility decision.",
    )

    parser.add_argument(
        "--out",
        default="analysis/reports/utility_decision_probe_v0_5.csv",
    )

    parser.add_argument(
        "--summary-out",
        default="analysis/reports/utility_decision_probe_v0_5_summary.txt",
    )

    return parser.parse_args()


def parse_matchup(value: str) -> tuple[str, str]:
    if ":" not in value:
        raise ValueError(f"Invalid matchup '{value}'. Use player_policy:enemy_policy.")

    player_policy, enemy_policy = value.split(":", 1)

    return player_policy.strip(), enemy_policy.strip()


def resource_json(engine: GameEngine, actor: ActorId) -> str:
    return json.dumps(
        dict(engine.state.actor_state(actor).resources),
        ensure_ascii=False,
        sort_keys=True,
    )


def action_target_text(target: object) -> str:
    if target is None:
        return ""

    return str(target)


def is_utility_policy(policy: str) -> bool:
    return policy == "utility_balancer"


def policy_personality(policy: str) -> str:
    if policy == "utility_balancer":
        return "balancer"

    raise ValueError(f"Unsupported utility policy for probe: {policy}")


def neutral_field_count(engine: GameEngine) -> int:
    return sum(1 for cell in engine.state.cells.values() if cell.owner is None)


def win_reason(engine: GameEngine, winner: ActorId | None) -> str:
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


def matchup_key(
    *,
    side_length: int,
    player_policy: str,
    enemy_policy: str,
    actor: ActorId,
) -> tuple[int, str, ActorId]:
    return (
        side_length,
        f"{player_policy}_vs_{enemy_policy}",
        actor,
    )


def append_utility_decision_rows(
    *,
    rows: list[dict[str, Any]],
    summary: dict[tuple[int, str, ActorId], Counter],
    engine: GameEngine,
    side_length: int,
    player_policy: str,
    enemy_policy: str,
    actor: ActorId,
    action_index: int,
    top_limit: int,
) -> None:
    state = engine.state
    opponent = state.opponent(actor)
    policy = player_policy if actor == "player" else enemy_policy
    personality = policy_personality(policy)

    top_scores = top_utility_scores(
        state,
        actor,
        personality,
        limit=top_limit,
    )

    if not top_scores:
        raise RuntimeError("No utility scores produced.")

    chosen_score = top_scores[0]
    chosen_action = chosen_score.action

    actor_controlled = state.controlled_count(actor)
    opponent_controlled = state.controlled_count(opponent)
    actor_non_core = state.non_core_controlled_count(actor)
    opponent_non_core = state.non_core_controlled_count(opponent)
    threshold = territory_threshold_60(state)
    neutral = neutral_field_count(engine)

    is_behind = actor_controlled < opponent_controlled
    actor_to_threshold = max(0, threshold - actor_controlled)
    opponent_to_threshold = max(0, threshold - opponent_controlled)

    result = apply_action(state, chosen_action)

    key = matchup_key(
        side_length=side_length,
        player_policy=player_policy,
        enemy_policy=enemy_policy,
        actor=actor,
    )

    summary[key]["decisions"] += 1
    summary[key][f"chosen_action:{chosen_action.action_type}"] += 1
    summary[key][f"chosen_category:{chosen_score.category}"] += 1

    if is_behind:
        summary[key]["behind_decisions"] += 1
        summary[key][f"behind_action:{chosen_action.action_type}"] += 1
        summary[key][f"behind_category:{chosen_score.category}"] += 1

    if opponent_to_threshold <= 3:
        summary[key]["opponent_near_territory_decisions"] += 1
        summary[key][f"opponent_near_action:{chosen_action.action_type}"] += 1

    if actor_to_threshold <= 3:
        summary[key]["actor_near_territory_decisions"] += 1
        summary[key][f"actor_near_action:{chosen_action.action_type}"] += 1

    for rank, score in enumerate(top_scores, start=1):
        action = score.action
        chosen = rank == 1

        rows.append(
            {
                "side_length": side_length,
                "board_size": state.board.size,
                "matchup": f"{player_policy}_vs_{enemy_policy}",
                "round": state.round_index,
                "action_index": action_index,
                "actor": actor,
                "actor_policy": policy,
                "first_actor": engine.initiative_first_actor(),
                "p_controlled": state.controlled_count("player"),
                "e_controlled": state.controlled_count("enemy"),
                "neutral_fields": neutral,
                "actor_controlled_before": actor_controlled,
                "opponent_controlled_before": opponent_controlled,
                "actor_non_core_before": actor_non_core,
                "opponent_non_core_before": opponent_non_core,
                "territory_threshold": threshold,
                "actor_to_threshold_before": actor_to_threshold,
                "opponent_to_threshold_before": opponent_to_threshold,
                "actor_behind_before": str(is_behind),
                "p_resources_before": resource_json(engine, "player"),
                "e_resources_before": resource_json(engine, "enemy"),
                "rank": rank,
                "candidate_action_type": action.action_type,
                "candidate_target": action_target_text(action.target),
                "candidate_field_type": action.field_type or "",
                "candidate_category": score.category,
                "raw_score": f"{score.raw_score:.4f}",
                "weight": f"{score.weight:.4f}",
                "total_score": f"{score.total_score:.4f}",
                "reasons": " | ".join(score.reasons),
                "chosen": str(chosen),
                "chosen_ok": str(result.ok) if chosen else "",
                "chosen_message": result.message if chosen else "",
                "winner_after": result.winner or "",
            }
        )


def run_utility_turn_with_probe(
    *,
    rows: list[dict[str, Any]],
    summary: dict[tuple[int, str, ActorId], Counter],
    engine: GameEngine,
    side_length: int,
    player_policy: str,
    enemy_policy: str,
    actor: ActorId,
    top_limit: int,
) -> ActorTurnResult:
    turn_result = ActorTurnResult(actor=actor)

    for action_index in range(1, engine.config.actions_per_turn + 1):
        if engine.current_winner() is not None:
            break

        append_utility_decision_rows(
            rows=rows,
            summary=summary,
            engine=engine,
            side_length=side_length,
            player_policy=player_policy,
            enemy_policy=enemy_policy,
            actor=actor,
            action_index=action_index,
            top_limit=top_limit,
        )

        # The chosen action was already applied in append_utility_decision_rows.
        # Re-read the latest chosen row to keep ActorTurnResult lightweight here.
        # For this probe, the CSV is the source of truth for chosen messages.

    return turn_result


def run_probe_matchup(
    *,
    rows: list[dict[str, Any]],
    summary: dict[tuple[int, str, ActorId], Counter],
    side_length: int,
    player_policy: str,
    enemy_policy: str,
    max_rounds: int,
    actions_per_turn: int,
    top_limit: int,
) -> None:
    engine = GameEngine.new_game(
        GameConfig(
            side_length=side_length,
            actions_per_turn=actions_per_turn,
            bot_policy=enemy_policy,
            max_rounds=max_rounds,
        )
    )

    while not engine.is_game_over():
        engine.start_round()

        first_actor = engine.initiative_first_actor()

        if first_actor == "player":
            actor_order: tuple[ActorId, ActorId] = ("player", "enemy")
        else:
            actor_order = ("enemy", "player")

        for actor in actor_order:
            if engine.current_winner() is not None:
                break

            policy = player_policy if actor == "player" else enemy_policy

            if is_utility_policy(policy):
                run_utility_turn_with_probe(
                    rows=rows,
                    summary=summary,
                    engine=engine,
                    side_length=side_length,
                    player_policy=player_policy,
                    enemy_policy=enemy_policy,
                    actor=actor,
                    top_limit=top_limit,
                )
            else:
                engine.run_bot_turn(actor, policy)

        if engine.current_winner() is None:
            engine.advance_round()

    key_base = (
        side_length,
        f"{player_policy}_vs_{enemy_policy}",
        "match",
    )

    match_counter = summary[key_base]  # type: ignore[index]
    winner = engine.current_winner()
    match_counter["final_round"] = engine.state.round_index
    match_counter[f"winner:{winner or 'none'}"] += 1
    match_counter[f"reason:{win_reason(engine, winner)}"] += 1
    match_counter["p_controlled_final"] = engine.state.controlled_count("player")
    match_counter["e_controlled_final"] = engine.state.controlled_count("enemy")
    match_counter["neutral_final"] = neutral_field_count(engine)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise ValueError("No probe rows produced.")

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(
    path: Path,
    summary: dict[tuple[int, str, object], Counter],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("UTILITY DECISION PROBE SUMMARY")
    lines.append("=" * 72)
    lines.append("")

    for key in sorted(summary.keys(), key=lambda item: (item[0], item[1], str(item[2]))):
        side_length, matchup, actor = key
        counter = summary[key]

        lines.append(f"side_length={side_length} | matchup={matchup} | actor={actor}")
        lines.append("-" * 72)

        for name, value in counter.most_common():
            lines.append(f"{name}: {value}")

        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()

    rows: list[dict[str, Any]] = []
    summary: dict[tuple[int, str, object], Counter] = defaultdict(Counter)

    matchups = [parse_matchup(value) for value in args.matchups]

    for side_length in args.side_lengths:
        for player_policy, enemy_policy in matchups:
            run_probe_matchup(
                rows=rows,
                summary=summary,
                side_length=side_length,
                player_policy=player_policy,
                enemy_policy=enemy_policy,
                max_rounds=args.max_rounds,
                actions_per_turn=args.actions_per_turn,
                top_limit=args.top,
            )

    out = Path(args.out)
    summary_out = Path(args.summary_out)

    write_csv(out, rows)
    write_summary(summary_out, summary)

    print(f"Wrote {out} with {len(rows)} rows")
    print(f"Wrote {summary_out}")
    print("")
    print("Quick summary:")
    print("-" * 72)

    for key in sorted(summary.keys(), key=lambda item: (item[0], item[1], str(item[2]))):
        side_length, matchup, actor = key
        counter = summary[key]

        if actor == "match":
            print(
                f"{side_length} {matchup} | final_round={counter.get('final_round', 0)} "
                f"p/e/n={counter.get('p_controlled_final', 0)}/"
                f"{counter.get('e_controlled_final', 0)}/"
                f"{counter.get('neutral_final', 0)}"
            )
            continue

        print(
            f"{side_length} {matchup} {actor} | "
            f"decisions={counter.get('decisions', 0)} "
            f"behind={counter.get('behind_decisions', 0)} "
            f"build={counter.get('chosen_action:build', 0)} "
            f"raid={counter.get('chosen_action:raid', 0)} "
            f"fortify={counter.get('chosen_action:fortify', 0)} "
            f"rebuild={counter.get('chosen_action:rebuild', 0)} "
            f"upgrade={counter.get('chosen_action:field_upgrade', 0) + counter.get('chosen_action:core_upgrade', 0)} "
            f"wait={counter.get('chosen_action:wait', 0)}"
        )


if __name__ == "__main__":
    main()
