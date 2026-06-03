from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Iterable

from src.maillon_v04.actions import ActionResult, action_summary
from src.maillon_v04.engine import GameConfig, GameEngine, RoundResult
from src.maillon_v04.rules import build_cost_holz, territory_threshold_60
from src.maillon_v04.state import ActorId, GameState, RESOURCE_NAMES


DEFAULT_MATRIX = Path("analysis/reports/runtime_matrix_v0_5_personality_tuned1_full.csv")
DEFAULT_OUT_DIR = Path("analysis/reports/stall_diagnostics_v0_5")
DEFAULT_CASES: tuple[tuple[str, str], ...] = (
    ("rusher", "utility_opportunist"),
    ("utility_rusher", "utility_fortifier"),
    ("utility_rusher", "utility_aggro_turtle"),
    ("utility_rusher", "utility_opportunist"),
    ("utility_opportunist", "rusher"),
    ("utility_opportunist", "utility_rusher"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose long-running / stalled Maillon bot matchups."
    )
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--side-length", type=int, default=5)
    parser.add_argument("--max-rounds", type=int, default=120)
    parser.add_argument("--actions-per-turn", type=int, default=3)
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Specific case in form player_policy:enemy_policy. Can be repeated.",
    )
    parser.add_argument("--recent-rounds", type=int, default=20)
    return parser.parse_args()


def as_int(row: dict[str, str], key: str, default: int = 0) -> int:
    raw = row.get(key, "")
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def parse_case(value: str) -> tuple[str, str]:
    if ":" not in value:
        raise ValueError(f"case must use player_policy:enemy_policy format: {value!r}")
    player_policy, enemy_policy = value.split(":", 1)
    return player_policy.strip(), enemy_policy.strip()


def read_matrix_cases(matrix: Path, side_length: int, max_rounds: int) -> list[tuple[str, str]]:
    if not matrix.exists():
        return []

    cases: list[tuple[str, str]] = []
    with matrix.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if as_int(row, "side_length") not in {0, side_length}:
                # Some old matrices do not carry side_length robustly; board_size covers that.
                board_size = as_int(row, "board_size")
                if side_length == 5 and board_size != 61:
                    continue
                if side_length == 4 and board_size != 37:
                    continue

            winner = row.get("winner", "")
            reason = row.get("win_reason", "")
            final_round = as_int(row, "final_round")

            if not winner or reason == "none" or final_round >= max_rounds + 1:
                cases.append((row["player_policy"], row["enemy_policy"]))

    return unique_cases(cases)


def unique_cases(cases: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str]] = []
    for case in cases:
        if case in seen:
            continue
        seen.add(case)
        result.append(case)
    return result


def win_reason(state: GameState, winner: ActorId | None) -> str:
    if winner is None:
        return "none"

    threshold = territory_threshold_60(state)
    if state.controlled_count(winner) >= threshold:
        return "territory"

    if state.non_core_controlled_count(state.opponent(winner)) == 0:
        return "domination"

    if len(state.neutral_cells()) == 0:
        return "full_board_majority"

    return "unknown"


def actor_resources(state: GameState, actor: ActorId) -> dict[str, int]:
    return dict(state.actor_state(actor).resources)


def actor_caps(state: GameState, actor: ActorId) -> dict[str, int]:
    return dict(state.actor_state(actor).caps)


def field_counts(state: GameState) -> Counter[str]:
    counts: Counter[str] = Counter()
    for cell in state.cells.values():
        owner = cell.owner or "neutral"
        field_type = cell.field_type or "leer"
        counts[f"{owner}:{field_type}"] += 1
    return counts


def front_stats(state: GameState, actor: ActorId) -> dict[str, int]:
    opponent = state.opponent(actor)
    front_fields = 0
    shielded_front = 0
    front_shield = 0
    contested_front = 0

    for coord in state.owned_cells(actor):
        cell = state.cell(coord)
        if cell.is_core:
            continue

        is_front = any(state.cell(neighbor).owner == opponent for neighbor in state.board.neighbors(coord))
        if not is_front:
            continue

        front_fields += 1
        if cell.raid_shield > 0:
            shielded_front += 1
            front_shield += cell.raid_shield
        if cell.contested_count > 0:
            contested_front += 1

    return {
        "front_fields": front_fields,
        "shielded_front": shielded_front,
        "front_shield": front_shield,
        "contested_front": contested_front,
    }


def classify_result(result: ActionResult) -> str:
    if not result.ok:
        return "failed"
    if result.action.action_type != "raid":
        return result.action.action_type
    if "No takeover" in result.message:
        return "raid_absorbed"
    return "raid_takeover"


def turn_action_counts(turn) -> Counter[str]:
    counts: Counter[str] = Counter()
    if turn is None:
        return counts
    for result in turn.actions:
        if result.ok:
            counts[result.action.action_type] += 1
        else:
            counts[f"failed_{result.action.action_type}"] += 1
    return counts


def append_actions(
    action_rows: list[dict[str, object]],
    round_index: int,
    turn,
    state: GameState,
) -> None:
    if turn is None:
        return
    for result in turn.actions:
        action = result.action
        action_rows.append(
            {
                "round": round_index,
                "actor": action.actor,
                "action_type": action.action_type,
                "target": action.target,
                "field_type": action.field_type,
                "ok": result.ok,
                "class": classify_result(result),
                "message": result.message,
                "p_controlled": state.controlled_count("player"),
                "e_controlled": state.controlled_count("enemy"),
                "neutral": len(state.neutral_cells()),
                "p_res": actor_resources(state, "player"),
                "e_res": actor_resources(state, "enemy"),
            }
        )


def run_case(
    *,
    side_length: int,
    max_rounds: int,
    actions_per_turn: int,
    player_policy: str,
    enemy_policy: str,
) -> dict[str, object]:
    engine = GameEngine.new_game(
        GameConfig(
            side_length=side_length,
            actions_per_turn=actions_per_turn,
            bot_policy=enemy_policy,  # type: ignore[arg-type]
            max_rounds=max_rounds,
        )
    )

    round_rows: list[dict[str, object]] = []
    action_rows: list[dict[str, object]] = []
    waste_total: dict[str, Counter[str]] = {
        "player": Counter(),
        "enemy": Counter(),
    }
    action_total: Counter[str] = Counter()
    actor_action_total: dict[str, Counter[str]] = {
        "player": Counter(),
        "enemy": Counter(),
    }

    while not engine.is_game_over():
        current_round = engine.state.round_index
        first_actor = engine.initiative_first_actor()
        result: RoundResult = engine.run_bot_vs_bot_round(
            player_policy=player_policy,  # type: ignore[arg-type]
            enemy_policy=enemy_policy,  # type: ignore[arg-type]
        )

        for actor in ("player", "enemy"):
            for resource in RESOURCE_NAMES:
                waste_total[actor][resource] += result.production_waste[actor][resource]

        append_actions(action_rows, current_round, result.player_turn, engine.state)
        append_actions(action_rows, current_round, result.enemy_turn, engine.state)

        p_counts = turn_action_counts(result.player_turn)
        e_counts = turn_action_counts(result.enemy_turn)
        action_total.update(p_counts)
        action_total.update(e_counts)
        actor_action_total["player"].update(p_counts)
        actor_action_total["enemy"].update(e_counts)

        for turn in (result.player_turn, result.enemy_turn):
            if turn is None:
                continue
            for action_result in turn.actions:
                action_total[classify_result(action_result)] += 1

        p_summary = action_summary(engine.state, "player")
        e_summary = action_summary(engine.state, "enemy")

        round_rows.append(
            {
                "round": current_round,
                "first_actor": first_actor,
                "p_controlled": engine.state.controlled_count("player"),
                "e_controlled": engine.state.controlled_count("enemy"),
                "neutral": len(engine.state.neutral_cells()),
                "p_res": actor_resources(engine.state, "player"),
                "e_res": actor_resources(engine.state, "enemy"),
                "p_build_cost": build_cost_holz(engine.state, "player"),
                "e_build_cost": build_cost_holz(engine.state, "enemy"),
                "p_affordable_build": p_summary["affordable_build_targets"],
                "e_affordable_build": e_summary["affordable_build_targets"],
                "p_affordable_raid": p_summary["affordable_raid_targets"],
                "e_affordable_raid": e_summary["affordable_raid_targets"],
                "p_actions": dict(p_counts),
                "e_actions": dict(e_counts),
                "p_waste": dict(result.production_waste["player"]),
                "e_waste": dict(result.production_waste["enemy"]),
            }
        )

        if result.winner is not None:
            break

    state = engine.state
    winner = engine.current_winner()

    return {
        "engine": engine,
        "state": state,
        "winner": winner,
        "reason": win_reason(state, winner),
        "round_rows": round_rows,
        "action_rows": action_rows,
        "waste_total": waste_total,
        "action_total": action_total,
        "actor_action_total": actor_action_total,
    }


def diagnosis_notes(data: dict[str, object]) -> list[str]:
    state: GameState = data["state"]  # type: ignore[assignment]
    winner = data["winner"]
    reason = data["reason"]
    round_rows: list[dict[str, object]] = data["round_rows"]  # type: ignore[assignment]
    action_total: Counter[str] = data["action_total"]  # type: ignore[assignment]
    actor_action_total: dict[str, Counter[str]] = data["actor_action_total"]  # type: ignore[assignment]

    notes: list[str] = []
    neutral = len(state.neutral_cells())

    if winner is None:
        notes.append("No winner before max_rounds: this is a true stall candidate.")
    elif reason == "full_board_majority":
        notes.append("Resolved by full-board majority, not by clean territory pressure.")

    if neutral > 0 and winner is None:
        notes.append("Neutral fields remain open at max_rounds; finish-expansion pressure may be too weak.")

    raids = action_total.get("raid", 0)
    takeovers = action_total.get("raid_takeover", 0)
    absorbed = action_total.get("raid_absorbed", 0)
    if raids >= 200 or takeovers >= 200:
        notes.append("Very high raid volume: likely raid/front churn rather than resource starvation only.")
    if absorbed >= 50:
        notes.append("Many shield absorptions: Fortify/Breaker/front density may be extending conflict.")

    for actor in ("player", "enemy"):
        waits = actor_action_total[actor].get("wait", 0)
        builds = actor_action_total[actor].get("build", 0)
        if waits >= 100 and builds < 30:
            notes.append(f"{actor} has high wait count with low build count: possible affordability/target bottleneck.")

    if round_rows:
        recent = round_rows[-10:]
        no_neutral_change = len({row["neutral"] for row in recent}) == 1
        if no_neutral_change and recent[-1]["neutral"] > 0:
            notes.append("Neutral count is flat in the last 10 rounds; expansion is stalled.")

    if not notes:
        notes.append("No single dominant stall signature detected; inspect recent actions.")

    return notes


def write_case_report(
    path: Path,
    *,
    player_policy: str,
    enemy_policy: str,
    data: dict[str, object],
    recent_rounds: int,
) -> None:
    state: GameState = data["state"]  # type: ignore[assignment]
    winner = data["winner"]
    reason = data["reason"]
    round_rows: list[dict[str, object]] = data["round_rows"]  # type: ignore[assignment]
    action_rows: list[dict[str, object]] = data["action_rows"]  # type: ignore[assignment]
    waste_total: dict[str, Counter[str]] = data["waste_total"]  # type: ignore[assignment]
    action_total: Counter[str] = data["action_total"]  # type: ignore[assignment]
    actor_action_total: dict[str, Counter[str]] = data["actor_action_total"]  # type: ignore[assignment]

    shielded = sorted(
        ((coord, cell) for coord, cell in state.cells.items() if cell.raid_shield > 0),
        key=lambda item: (-item[1].raid_shield, -item[1].contested_count, item[0]),
    )
    contested = sorted(
        ((coord, cell) for coord, cell in state.cells.items() if cell.contested_count > 0),
        key=lambda item: (-item[1].contested_count, -item[1].raid_shield, item[0]),
    )
    inactive = [coord for coord, cell in state.cells.items() if cell.owner is not None and not state.is_active(coord)]

    lines: list[str] = []
    lines.append("MAILLON STALL DIAGNOSTIC")
    lines.append("=" * 72)
    lines.append(f"Case: board={state.board.size} | player={player_policy} | enemy={enemy_policy}")
    lines.append("")
    lines.append("FINAL")
    lines.append("-" * 72)
    lines.append(f"Round:        {state.round_index}")
    lines.append(f"Winner:       {winner}")
    lines.append(f"Reason:       {reason}")
    lines.append(f"Threshold 60: {territory_threshold_60(state)}")
    lines.append(
        f"Controlled:   player {state.controlled_count('player')} | "
        f"enemy {state.controlled_count('enemy')} | neutral {len(state.neutral_cells())}"
    )
    lines.append(
        f"Non-core:     player {state.non_core_controlled_count('player')} | "
        f"enemy {state.non_core_controlled_count('enemy')}"
    )
    lines.append("")
    lines.append("FINAL RESOURCES")
    lines.append("-" * 72)
    lines.append(f"Player: {actor_resources(state, 'player')} / caps {actor_caps(state, 'player')}")
    lines.append(f"Enemy:  {actor_resources(state, 'enemy')} / caps {actor_caps(state, 'enemy')}")
    lines.append(f"Player build cost now: {build_cost_holz(state, 'player')}")
    lines.append(f"Enemy build cost now:  {build_cost_holz(state, 'enemy')}")
    lines.append("")
    lines.append("ACTION COUNTS")
    lines.append("-" * 72)
    lines.append(f"Total:  {dict(action_total)}")
    lines.append(f"Player: {dict(actor_action_total['player'])}")
    lines.append(f"Enemy:  {dict(actor_action_total['enemy'])}")
    lines.append("")
    lines.append("WASTE TOTAL")
    lines.append("-" * 72)
    lines.append(f"Player: {dict(waste_total['player'])}")
    lines.append(f"Enemy:  {dict(waste_total['enemy'])}")
    lines.append("")
    lines.append("FIELD COUNTS")
    lines.append("-" * 72)
    for key, value in sorted(field_counts(state).items()):
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append("FRONT / SHIELD")
    lines.append("-" * 72)
    lines.append(f"Player front: {front_stats(state, 'player')}")
    lines.append(f"Enemy front:  {front_stats(state, 'enemy')}")
    lines.append(f"Inactive owned cells: {len(inactive)}")
    lines.append(f"Shielded fields:      {len(shielded)}")
    lines.append(f"Shield points:        {sum(cell.raid_shield for _, cell in shielded)}")
    lines.append(f"Contested fields:     {len(contested)}")
    lines.append("")
    lines.append("DIAGNOSIS NOTES")
    lines.append("-" * 72)
    for note in diagnosis_notes(data):
        lines.append(f"- {note}")
    lines.append("")
    lines.append("TOP CONTESTED FIELDS")
    lines.append("-" * 72)
    for coord, cell in contested[:12]:
        lines.append(
            f"{coord} owner={cell.owner} type={cell.field_type} L{cell.level} "
            f"shield={cell.raid_shield} contested={cell.contested_count} "
            f"active={state.is_active(coord)} active_from={cell.active_from_round}"
        )
    lines.append("")
    lines.append("TOP SHIELDED FIELDS")
    lines.append("-" * 72)
    for coord, cell in shielded[:12]:
        lines.append(
            f"{coord} owner={cell.owner} type={cell.field_type} L{cell.level} "
            f"shield={cell.raid_shield} contested={cell.contested_count} "
            f"active={state.is_active(coord)} active_from={cell.active_from_round}"
        )
    lines.append("")
    lines.append(f"LAST {recent_rounds} ROUNDS")
    lines.append("-" * 72)
    lines.append("round | first | p/e/n | p_build/raid | e_build/raid | p_res | e_res | p_actions | e_actions | p_waste | e_waste")
    for row in round_rows[-recent_rounds:]:
        lines.append(
            f"{row['round']:>5} | {row['first_actor']} | "
            f"{row['p_controlled']}/{row['e_controlled']}/{row['neutral']} | "
            f"{row['p_affordable_build']}/{row['p_affordable_raid']} | "
            f"{row['e_affordable_build']}/{row['e_affordable_raid']} | "
            f"{row['p_res']} | {row['e_res']} | "
            f"{row['p_actions']} | {row['e_actions']} | "
            f"{row['p_waste']} | {row['e_waste']}"
        )
    lines.append("")
    lines.append(f"LAST {recent_rounds} ACTIONS")
    lines.append("-" * 72)
    for entry in action_rows[-recent_rounds:]:
        lines.append(
            f"R{entry['round']} | {entry['actor']} | {entry['action_type']} | "
            f"class={entry['class']} | ok={entry['ok']} | {entry['message']}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def safe_case_name(side_length: int, player_policy: str, enemy_policy: str) -> str:
    return f"stall_diag_s{side_length}_{player_policy}_vs_{enemy_policy}.txt"


def main() -> None:
    args = parse_args()

    if args.case:
        cases = unique_cases(parse_case(value) for value in args.case)
    else:
        cases = read_matrix_cases(args.matrix, args.side_length, args.max_rounds)
        if not cases:
            cases = list(DEFAULT_CASES)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, object]] = []

    for player_policy, enemy_policy in cases:
        data = run_case(
            side_length=args.side_length,
            max_rounds=args.max_rounds,
            actions_per_turn=args.actions_per_turn,
            player_policy=player_policy,
            enemy_policy=enemy_policy,
        )
        state: GameState = data["state"]  # type: ignore[assignment]
        winner = data["winner"]
        reason = data["reason"]
        action_total: Counter[str] = data["action_total"]  # type: ignore[assignment]
        actor_action_total: dict[str, Counter[str]] = data["actor_action_total"]  # type: ignore[assignment]
        waste_total: dict[str, Counter[str]] = data["waste_total"]  # type: ignore[assignment]

        out_path = args.out_dir / safe_case_name(args.side_length, player_policy, enemy_policy)
        write_case_report(
            out_path,
            player_policy=player_policy,
            enemy_policy=enemy_policy,
            data=data,
            recent_rounds=args.recent_rounds,
        )

        summary_rows.append(
            {
                "side_length": args.side_length,
                "board_size": state.board.size,
                "matchup": f"{player_policy}_vs_{enemy_policy}",
                "winner": winner or "",
                "reason": reason,
                "round": state.round_index,
                "p_controlled": state.controlled_count("player"),
                "e_controlled": state.controlled_count("enemy"),
                "neutral": len(state.neutral_cells()),
                "p_build": actor_action_total["player"].get("build", 0),
                "e_build": actor_action_total["enemy"].get("build", 0),
                "p_raid": actor_action_total["player"].get("raid", 0),
                "e_raid": actor_action_total["enemy"].get("raid", 0),
                "p_wait": actor_action_total["player"].get("wait", 0),
                "e_wait": actor_action_total["enemy"].get("wait", 0),
                "raid_takeovers": action_total.get("raid_takeover", 0),
                "raid_absorbed": action_total.get("raid_absorbed", 0),
                "p_korn_waste": waste_total["player"].get("Korn", 0),
                "e_korn_waste": waste_total["enemy"].get("Korn", 0),
                "report": str(out_path),
            }
        )

    summary_path = args.out_dir / f"stall_diagnostic_summary_s{args.side_length}.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(summary_rows[0].keys()) if summary_rows else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Wrote {summary_path} with {len(summary_rows)} rows")
    print("side,matchup,winner,reason,round,p/e/n,p_build/e_build,p_raid/e_raid,p_wait/e_wait,takeovers,absorbed,p_kwaste/e_kwaste")
    for row in summary_rows:
        print(
            f"{row['board_size']},"
            f"{row['matchup']},"
            f"{row['winner']},"
            f"{row['reason']},"
            f"{row['round']},"
            f"{row['p_controlled']}/{row['e_controlled']}/{row['neutral']},"
            f"{row['p_build']}/{row['e_build']},"
            f"{row['p_raid']}/{row['e_raid']},"
            f"{row['p_wait']}/{row['e_wait']},"
            f"{row['raid_takeovers']},"
            f"{row['raid_absorbed']},"
            f"{row['p_korn_waste']}/{row['e_korn_waste']}"
        )


if __name__ == "__main__":
    main()
