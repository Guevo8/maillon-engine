from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_RUN_PATH = Path("runs/latest_run.jsonl")
DEFAULT_SUMMARY_PATH = Path("runs/latest_summary.json")
DEFAULT_STATE_PATH = Path("runs/latest_state.json")


RESOURCE_ORDER = ("Holz", "Stein", "Korn")
ACTION_ORDER = (
    "build",
    "raid",
    "rebuild",
    "field_upgrade",
    "core_upgrade",
    "fortify",
    "wait",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Run log not found: {path}")

    events: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc

    return events


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def resource_text(resources: dict[str, int] | None) -> str:
    if not resources:
        return "-"

    return " | ".join(
        f"{name} {resources.get(name, 0)}"
        for name in RESOURCE_ORDER
    )


def caps_text(caps: dict[str, int] | None) -> str:
    if not caps:
        return "-"

    return " | ".join(
        f"{name} {caps.get(name, 0)}"
        for name in RESOURCE_ORDER
    )


def add_waste_totals(
    waste_totals: dict[str, Counter[str]],
    waste_payload: dict[str, Any],
) -> None:
    for actor in ("player", "enemy"):
        actor_waste = waste_payload.get(actor, {})

        for resource in RESOURCE_ORDER:
            waste_totals[actor][resource] += int(actor_waste.get(resource, 0))


def print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def is_shield_absorb_raid(payload: dict[str, Any]) -> bool:
    if payload.get("action_type") != "raid":
        return False

    if not bool(payload.get("ok", False)):
        return False

    message = str(payload.get("message", ""))

    return "raid_shield reduced" in message or "No takeover" in message


def is_takeover_raid(payload: dict[str, Any]) -> bool:
    if payload.get("action_type") != "raid":
        return False

    if not bool(payload.get("ok", False)):
        return False

    return not is_shield_absorb_raid(payload)


def print_run_header(
    events: list[dict[str, Any]],
    summary: dict[str, Any] | None,
    state: dict[str, Any] | None,
    run_path: Path,
    summary_path: Path,
    state_path: Path,
) -> None:
    first_event = events[0] if events else {}
    last_event = events[-1] if events else {}

    run_id = (
        (summary or {}).get("run_id")
        or (state or {}).get("run_id")
        or first_event.get("run_id")
        or "unknown"
    )

    print_section("MAILLON v0.4 RUN REPORT")
    print(f"Run ID:        {run_id}")
    print(f"Run log:       {run_path}")
    print(f"Summary:       {summary_path if summary is not None else 'missing'}")
    print(f"State:         {state_path if state is not None else 'missing'}")
    print(f"Events:        {len(events)}")
    print(f"First round:   {first_event.get('round', '-')}")
    print(f"Last round:    {last_event.get('round', '-')}")

    if summary is not None:
        print(f"Winner:        {summary.get('winner')}")
        print(f"Reason:        {summary.get('reason')}")
        print(f"Board size:    {summary.get('board_size')}")
        print(f"60% threshold: {summary.get('territory_threshold_60')}")


def print_action_stats(events: list[dict[str, Any]]) -> None:
    action_counts = Counter()
    action_counts_by_actor: dict[str, Counter[str]] = defaultdict(Counter)
    failed_counts_by_actor: dict[str, Counter[str]] = defaultdict(Counter)

    raid_success_total = 0
    raid_takeovers = 0
    raid_absorbed_by_shield = 0

    for event in events:
        if event.get("event_type") != "action_result":
            continue

        payload = event.get("payload", {})
        actor = str(payload.get("actor", "unknown"))
        action_type = str(payload.get("action_type", "unknown"))
        ok = bool(payload.get("ok", False))

        action_counts[action_type] += 1
        action_counts_by_actor[actor][action_type] += 1

        if not ok:
            failed_counts_by_actor[actor][action_type] += 1

        if action_type == "raid" and ok:
            raid_success_total += 1

            if is_shield_absorb_raid(payload):
                raid_absorbed_by_shield += 1
            else:
                raid_takeovers += 1

    print_section("ACTION STATS")

    total_actions = sum(action_counts.values())
    print(f"Total action results:     {total_actions}")
    print(f"Successful raids total:   {raid_success_total}")
    print(f"Raid takeovers:           {raid_takeovers}")
    print(f"Raids absorbed by shield: {raid_absorbed_by_shield}")

    print()
    print("By action type:")

    for action_type in ACTION_ORDER:
        if action_counts[action_type]:
            print(f"- {action_type}: {action_counts[action_type]}")

    for action_type, count in action_counts.items():
        if action_type not in ACTION_ORDER:
            print(f"- {action_type}: {count}")

    print()
    print("By actor:")

    for actor in ("player", "enemy"):
        counter = action_counts_by_actor.get(actor, Counter())
        failed = failed_counts_by_actor.get(actor, Counter())

        if not counter:
            print(f"- {actor}: no actions")
            continue

        parts = [
            f"{action_type}={counter[action_type]}"
            for action_type in ACTION_ORDER
            if counter[action_type]
        ]

        other_parts = [
            f"{action_type}={count}"
            for action_type, count in counter.items()
            if action_type not in ACTION_ORDER
        ]

        failed_total = sum(failed.values())

        print(f"- {actor}: " + ", ".join(parts + other_parts))

        if failed_total:
            failed_parts = [
                f"{action_type}={count}"
                for action_type, count in failed.items()
            ]
            print(f"  failed: " + ", ".join(failed_parts))


def print_fortify_stats(
    events: list[dict[str, Any]],
    state: dict[str, Any] | None,
) -> None:
    fortify_success_by_actor: dict[str, int] = defaultdict(int)
    shield_absorb_by_actor: dict[str, int] = defaultdict(int)

    for event in events:
        if event.get("event_type") != "action_result":
            continue

        payload = event.get("payload", {})
        actor = str(payload.get("actor", "unknown"))
        action_type = payload.get("action_type")
        ok = bool(payload.get("ok", False))

        if action_type == "fortify" and ok:
            fortify_success_by_actor[actor] += 1

        if is_shield_absorb_raid(payload):
            shield_absorb_by_actor[actor] += 1

    fortify_success_total = sum(fortify_success_by_actor.values())
    shield_absorb_total = sum(shield_absorb_by_actor.values())

    final_shield_points = 0
    final_shielded_fields = 0
    max_final_shield = 0
    top_shielded: list[dict[str, Any]] = []

    if state is not None:
        cells = state.get("cells", [])

        for cell in cells:
            shield = int(cell.get("raid_shield") or 0)

            if shield <= 0:
                continue

            final_shield_points += shield
            final_shielded_fields += 1
            max_final_shield = max(max_final_shield, shield)
            top_shielded.append(cell)

        top_shielded.sort(
            key=lambda cell: int(cell.get("raid_shield") or 0),
            reverse=True,
        )

    print_section("FORTIFY / RAID-SHIELD")

    print(f"Successful fortify actions:  {fortify_success_total}")
    print(f"Shield points created:       {fortify_success_total}")
    print(f"Raids absorbed by shield:    {shield_absorb_total}")

    print()
    print("Fortify by actor:")
    for actor in ("player", "enemy"):
        print(f"- {actor}: {fortify_success_by_actor.get(actor, 0)}")

    print()
    print("Shield-absorbing raids by actor:")
    for actor in ("player", "enemy"):
        print(f"- {actor}: {shield_absorb_by_actor.get(actor, 0)}")

    print()
    print("Final shield state:")
    if state is None:
        print("- latest_state.json missing")
        return

    print(f"- shielded fields:      {final_shielded_fields}")
    print(f"- total shield points:  {final_shield_points}")
    print(f"- max field shield:     {max_final_shield}")

    if top_shielded:
        print()
        print("Top shielded fields:")
        for cell in top_shielded[:10]:
            print(
                f"- {cell.get('coord')} "
                f"owner={cell.get('owner')} "
                f"type={cell.get('field_type')} "
                f"L{cell.get('level')} "
                f"shield={cell.get('raid_shield')} "
                f"contested={cell.get('contested_count')} "
                f"active={cell.get('active')}"
            )


def print_production_stats(events: list[dict[str, Any]]) -> None:
    production_events = 0
    waste_totals: dict[str, Counter[str]] = {
        "player": Counter(),
        "enemy": Counter(),
    }

    for event in events:
        if event.get("event_type") != "production":
            continue

        production_events += 1
        payload = event.get("payload", {})
        waste = payload.get("waste", {})

        add_waste_totals(waste_totals, waste)

    print_section("PRODUCTION / WASTE")
    print(f"Production events: {production_events}")

    for actor in ("player", "enemy"):
        print(f"- {actor} waste: {resource_text(dict(waste_totals[actor]))}")


def print_final_summary(summary: dict[str, Any] | None) -> None:
    print_section("FINAL SUMMARY")

    if summary is None:
        print("No latest_summary.json found.")
        return

    print(f"Round:          {summary.get('round')}")
    print(f"Winner:         {summary.get('winner')}")
    print(f"Reason:         {summary.get('reason')}")
    print(f"Board size:     {summary.get('board_size')}")
    print(f"60% threshold:  {summary.get('territory_threshold_60')}")

    for actor in ("player", "enemy"):
        actor_summary = summary.get(actor, {})

        print()
        print(actor.upper())
        print(f"Controlled:     {actor_summary.get('controlled')}")
        print(f"Non-core:       {actor_summary.get('non_core')}")
        print(f"Resources:      {resource_text(actor_summary.get('resources'))}")
        print(f"Caps:           {caps_text(actor_summary.get('caps'))}")


def print_recent_actions(events: list[dict[str, Any]], limit: int) -> None:
    print_section(f"RECENT ACTIONS LAST {limit}")

    action_events = [
        event
        for event in events
        if event.get("event_type") == "action_result"
    ]

    if not action_events:
        print("No action_result events found.")
        return

    for event in action_events[-limit:]:
        payload = event.get("payload", {})
        round_index = event.get("round", "-")
        actor = payload.get("actor", "-")
        action_type = payload.get("action_type", "-")
        ok = payload.get("ok", "-")
        message = payload.get("message", "")

        print(f"R{round_index} | {actor} | {action_type} | ok={ok} | {message}")


def run_report(
    run_path: Path = DEFAULT_RUN_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    state_path: Path = DEFAULT_STATE_PATH,
    recent_limit: int = 10,
) -> None:
    events = load_jsonl(run_path)
    summary = load_optional_json(summary_path)
    state = load_optional_json(state_path)

    print_run_header(events, summary, state, run_path, summary_path, state_path)
    print_action_stats(events)
    print_fortify_stats(events, state)
    print_production_stats(events)
    print_final_summary(summary)
    print_recent_actions(events, recent_limit)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a compact report for a Maillon v0.4 terminal run."
    )
    parser.add_argument(
        "--run",
        type=Path,
        default=DEFAULT_RUN_PATH,
        help="Path to latest_run.jsonl",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY_PATH,
        help="Path to latest_summary.json",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Path to latest_state.json",
    )
    parser.add_argument(
        "--recent",
        type=int,
        default=10,
        help="Number of recent action_result events to print",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    run_report(
        run_path=args.run,
        summary_path=args.summary,
        state_path=args.state,
        recent_limit=args.recent,
    )


if __name__ == "__main__":
    main()
