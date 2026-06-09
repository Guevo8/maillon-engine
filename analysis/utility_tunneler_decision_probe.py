from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.actions import apply_action
from src.maillon_v04.bot_utility_tunneler import (
    _get_normal_baseline,
    choose_utility_tunneler_action,
    generate_tunnel_candidates,
    score_tunnel_candidate,
)
from src.maillon_v04.engine import GameConfig, GameEngine
from src.maillon_v04.state import ActorId


DEFAULT_MATCHUPS = (
    "utility_tunneler:phase_player",
    "utility_tunneler:utility_balancer",
)

CSV_FIELDNAMES = [
    "side_length",
    "matchup",
    "round",
    "actor",
    "actor_policy",
    "action_index",
    "candidate_action_type",
    "candidate_target",
    "candidate_source",
    "candidate_field_type",
    "tunnel_score",
    "normal_baseline",
    "opportunity_cost",
    "chosen",
    "reasons",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe utility_tunneler decisions action-by-action."
    )
    parser.add_argument("--side-lengths", type=int, nargs="+", default=[4, 5])
    parser.add_argument(
        "--matchups",
        nargs="+",
        default=list(DEFAULT_MATCHUPS),
        help="Matchups as player_policy:enemy_policy",
    )
    parser.add_argument("--max-rounds", type=int, default=80)
    parser.add_argument("--actions-per-turn", type=int, default=3)
    parser.add_argument(
        "--out",
        default="analysis/reports/utility_tunneler_decision_probe_v0_7.csv",
    )
    return parser.parse_args()


def parse_matchup(value: str) -> tuple[str, str]:
    if ":" not in value:
        raise ValueError(f"Invalid matchup '{value}'. Use player_policy:enemy_policy.")
    player_policy, enemy_policy = value.split(":", 1)
    return player_policy.strip(), enemy_policy.strip()


def _run_tunneler_action(
    *,
    rows: list[dict[str, Any]],
    engine: GameEngine,
    side_length: int,
    matchup: str,
    player_policy: str,
    enemy_policy: str,
    actor: ActorId,
    action_index: int,
) -> bool:
    """
    Run one tunneler action, collect a row per candidate.

    Returns True if a game winner was found.
    """
    state = engine.state
    policy = player_policy if actor == "player" else enemy_policy

    normal_baseline = _get_normal_baseline(state, actor)
    candidates = generate_tunnel_candidates(state, actor)
    scores = [score_tunnel_candidate(state, actor, c, normal_baseline) for c in candidates]
    chosen_action = choose_utility_tunneler_action(state, actor)

    for ts in scores:
        action = ts.action
        is_chosen = (
            action.action_type == chosen_action.action_type
            and action.target == chosen_action.target
            and action.source == chosen_action.source
            and action.field_type == chosen_action.field_type
        )
        reasons_str = "|".join(f"{name}:{value:.4f}" for name, value in ts.reasons)
        rows.append(
            {
                "side_length": side_length,
                "matchup": matchup,
                "round": state.round_index,
                "actor": actor,
                "actor_policy": policy,
                "action_index": action_index,
                "candidate_action_type": action.action_type,
                "candidate_target": str(action.target) if action.target else "",
                "candidate_source": str(action.source) if action.source else "",
                "candidate_field_type": action.field_type or "",
                "tunnel_score": round(ts.score, 4),
                "normal_baseline": round(normal_baseline, 4),
                "opportunity_cost": round(ts.features.opportunity_cost, 4),
                "chosen": "T" if is_chosen else "F",
                "reasons": reasons_str,
            }
        )

    result = apply_action(state, chosen_action)
    return result.winner is not None


def run_probe(
    *,
    side_lengths: list[int],
    matchups: list[str],
    max_rounds: int,
    actions_per_turn: int,
    out_path: Path,
) -> None:
    rows: list[dict[str, Any]] = []

    for side_length in side_lengths:
        for matchup_str in matchups:
            player_policy, enemy_policy = parse_matchup(matchup_str)
            matchup_label = f"{player_policy}_vs_{enemy_policy}"

            print(
                f"  running {matchup_label} side_length={side_length} ...",
                end="",
                flush=True,
            )

            config = GameConfig(
                side_length=side_length,
                actions_per_turn=actions_per_turn,
                bot_policy=enemy_policy,
                max_rounds=max_rounds,
            )
            engine = GameEngine.new_game(config)
            rows_before = len(rows)

            while not engine.is_game_over():
                engine.start_round()
                first = engine.initiative_first_actor()
                second: ActorId = "enemy" if first == "player" else "player"
                actor_order = [first, second]

                for actor in actor_order:
                    policy = player_policy if actor == "player" else enemy_policy
                    is_tunneler = policy == "utility_tunneler"

                    if is_tunneler:
                        for action_index in range(1, actions_per_turn + 1):
                            if engine.current_winner() is not None:
                                break
                            winner_found = _run_tunneler_action(
                                rows=rows,
                                engine=engine,
                                side_length=side_length,
                                matchup=matchup_label,
                                player_policy=player_policy,
                                enemy_policy=enemy_policy,
                                actor=actor,
                                action_index=action_index,
                            )
                            if winner_found:
                                break
                    else:
                        engine.run_bot_turn(actor, policy)

                    if engine.current_winner() is not None:
                        break

                if engine.current_winner() is None:
                    engine.advance_round()

            print(f" {len(rows) - rows_before} rows")

    if not rows:
        print("No rows collected.")
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {out_path}")


def main() -> None:
    args = parse_args()
    out_path = Path(args.out)

    print("utility_tunneler decision probe")
    print("=" * 60)

    run_probe(
        side_lengths=args.side_lengths,
        matchups=args.matchups,
        max_rounds=args.max_rounds,
        actions_per_turn=args.actions_per_turn,
        out_path=out_path,
    )


if __name__ == "__main__":
    main()
