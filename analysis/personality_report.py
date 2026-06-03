from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_INPUT = Path("analysis/reports/runtime_matrix_v0_5_personality_full.csv")
DEFAULT_OUT = Path("analysis/reports/personality_report_v0_5.md")
DEFAULT_CSV = Path("analysis/reports/personality_report_v0_5_summary.csv")


def i(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    try:
        return int(value) if value != "" else 0
    except ValueError:
        return 0


def pct(value: float) -> str:
    return f"{value:.2f}"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_policy_filter(values: list[str] | None) -> set[str]:
    if not values:
        return set()

    policies: set[str] = set()
    for value in values:
        for part in value.split(","):
            policy = part.strip()
            if policy:
                policies.add(policy)

    return policies


def filter_rows(
    rows: list[dict[str, str]],
    *,
    include_policies: set[str],
    exclude_policies: set[str],
    focus_policy: str | None,
) -> list[dict[str, str]]:
    filtered: list[dict[str, str]] = []

    for row in rows:
        player_policy = row["player_policy"]
        enemy_policy = row["enemy_policy"]
        pair = {player_policy, enemy_policy}

        if include_policies and not pair.issubset(include_policies):
            continue

        if exclude_policies and pair.intersection(exclude_policies):
            continue

        if focus_policy and focus_policy not in pair:
            continue

        filtered.append(row)

    return filtered


def new_stats() -> dict[str, object]:
    return {
        "slots": 0,
        "as_player": 0,
        "as_enemy": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "player_wins": 0,
        "enemy_wins": 0,
        "rounds": 0,
        "final_controlled": 0,
        "neutral_seen": 0,
        "fortify": 0,
        "rebuild": 0,
        "build": 0,
        "raid": 0,
        "wait": 0,
        "field_upgrade": 0,
        "core_upgrade": 0,
        "holz_waste": 0,
        "stein_waste": 0,
        "korn_waste": 0,
        "win_reasons": Counter(),
        "loss_reasons": Counter(),
    }


def add_side(stats: dict[str, object], row: dict[str, str], prefix: str) -> None:
    for key in (
        "fortify",
        "rebuild",
        "build",
        "raid",
        "wait",
        "field_upgrade",
        "core_upgrade",
        "holz_waste",
        "stein_waste",
        "korn_waste",
    ):
        stats[key] = int(stats[key]) + i(row, f"{prefix}_{key}")

    stats["final_controlled"] = int(stats["final_controlled"]) + i(row, f"{prefix}_controlled")


def summarize(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    stats: dict[str, dict[str, object]] = defaultdict(new_stats)

    for row in rows:
        player_policy = row["player_policy"]
        enemy_policy = row["enemy_policy"]
        winner = row.get("winner", "")
        reason = row.get("win_reason", "none") or "none"
        final_round = i(row, "final_round")
        neutral = i(row, "neutral_fields")

        p = stats[player_policy]
        e = stats[enemy_policy]

        p["slots"] = int(p["slots"]) + 1
        e["slots"] = int(e["slots"]) + 1
        p["as_player"] = int(p["as_player"]) + 1
        e["as_enemy"] = int(e["as_enemy"]) + 1
        p["rounds"] = int(p["rounds"]) + final_round
        e["rounds"] = int(e["rounds"]) + final_round
        p["neutral_seen"] = int(p["neutral_seen"]) + neutral
        e["neutral_seen"] = int(e["neutral_seen"]) + neutral

        add_side(p, row, "p")
        add_side(e, row, "e")

        if winner == "player":
            p["wins"] = int(p["wins"]) + 1
            p["player_wins"] = int(p["player_wins"]) + 1
            e["losses"] = int(e["losses"]) + 1
            p["win_reasons"][reason] += 1  # type: ignore[index]
            e["loss_reasons"][reason] += 1  # type: ignore[index]
        elif winner == "enemy":
            e["wins"] = int(e["wins"]) + 1
            e["enemy_wins"] = int(e["enemy_wins"]) + 1
            p["losses"] = int(p["losses"]) + 1
            e["win_reasons"][reason] += 1  # type: ignore[index]
            p["loss_reasons"][reason] += 1  # type: ignore[index]
        else:
            p["draws"] = int(p["draws"]) + 1
            e["draws"] = int(e["draws"]) + 1

    return dict(stats)


def top(counter: Counter[str]) -> str:
    if not counter:
        return "-"
    key, value = counter.most_common(1)[0]
    return f"{key}:{value}"


def ordered(stats: dict[str, dict[str, object]]) -> list[tuple[str, dict[str, object]]]:
    def sort_key(item: tuple[str, dict[str, object]]) -> tuple[float, float, str]:
        policy, s = item
        slots = max(1, int(s["slots"]))
        return (-int(s["wins"]) / slots, int(s["rounds"]) / slots, policy)

    return sorted(stats.items(), key=sort_key)


def problem_rows(rows: list[dict[str, str]], stall_round: int) -> list[dict[str, str]]:
    selected = []
    for row in rows:
        if not row.get("winner") or row.get("win_reason") in {"none", "timeout_draw"}:
            selected.append(row)
        elif i(row, "final_round") >= stall_round:
            selected.append(row)
        elif i(row, "rebuild") >= 300 or i(row, "fortify") >= 150:
            selected.append(row)
    return sorted(selected, key=lambda r: (-i(r, "final_round"), -i(r, "rebuild"), r.get("matchup", "")))


def write_csv(path: Path, stats: dict[str, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "policy",
        "wins",
        "slots",
        "win_rate",
        "draws",
        "avg_rounds",
        "as_player",
        "as_enemy",
        "player_wins",
        "enemy_wins",
        "fortify",
        "rebuild",
        "build",
        "raid",
        "wait",
        "korn_waste",
        "avg_final_controlled",
        "top_win_reason",
        "top_loss_reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for policy, s in ordered(stats):
            slots = max(1, int(s["slots"]))
            writer.writerow({
                "policy": policy,
                "wins": s["wins"],
                "slots": s["slots"],
                "win_rate": pct(int(s["wins"]) / slots),
                "draws": s["draws"],
                "avg_rounds": pct(int(s["rounds"]) / slots),
                "as_player": s["as_player"],
                "as_enemy": s["as_enemy"],
                "player_wins": s["player_wins"],
                "enemy_wins": s["enemy_wins"],
                "fortify": s["fortify"],
                "rebuild": s["rebuild"],
                "build": s["build"],
                "raid": s["raid"],
                "wait": s["wait"],
                "korn_waste": s["korn_waste"],
                "avg_final_controlled": pct(int(s["final_controlled"]) / slots),
                "top_win_reason": top(s["win_reasons"]),
                "top_loss_reason": top(s["loss_reasons"]),
            })


def build_report(
    rows: list[dict[str, str]],
    stats: dict[str, dict[str, object]],
    source: Path,
    csv_out: Path,
    stall_round: int,
    title: str,
    original_row_count: int,
    include_policies: set[str],
    exclude_policies: set[str],
    focus_policy: str | None,
) -> str:
    lines = [
        f"# {title}",
        "",
        "## Source",
        "",
        f"- Input matrix: `{source}`",
        f"- Summary CSV: `{csv_out}`",
        f"- Rows used: {len(rows)} / {original_row_count}",
        f"- Include policies: `{', '.join(sorted(include_policies)) if include_policies else 'all'}`",
        f"- Exclude policies: `{', '.join(sorted(exclude_policies)) if exclude_policies else '-'}`",
        f"- Focus policy: `{focus_policy or '-'}`",
        "",
        "## Policy Summary",
        "",
        "| Policy | Wins | Slots | Winrate | Draws | Avg round | Fortify | Rebuild | Build | Raid | Wait | Korn waste | Avg controlled | Top win | Top loss |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    for policy, s in ordered(stats):
        slots = max(1, int(s["slots"]))
        lines.append(
            f"| `{policy}` | {s['wins']} | {s['slots']} | {int(s['wins']) / slots:.2f} | {s['draws']} | "
            f"{int(s['rounds']) / slots:.1f} | {s['fortify']} | {s['rebuild']} | {s['build']} | {s['raid']} | "
            f"{s['wait']} | {s['korn_waste']} | {int(s['final_controlled']) / slots:.1f} | "
            f"{top(s['win_reasons'])} | {top(s['loss_reasons'])} |"
        )

    lines.extend([
        "",
        "## Method Notes",
        "",
        "- `Slots` means appearances as player plus appearances as enemy within the filtered pool.",
        "- Fortify/Rebuild/Build/Raid/Wait/Waste are actor-side totals.",
        "- `timeout_majority` is an analysis-only max-round adjudication from runtime_matrix.py, not an engine win rule.",
        "- Current runtime matrix conflict columns such as `raid_takeovers`, `raid_absorbed_by_shield` and `final_shield_points` are match-level metrics, not clean per-policy ownership. They are therefore not used in the policy summary table.",
        "",
        "## Problem Matchups",
        "",
    ])

    problems = problem_rows(rows, stall_round)
    if problems:
        lines.append("| Board | Matchup | Winner | Reason | Natural | Round | P/E/N | Fortify | Rebuild | Takeovers |")
        lines.append("|---:|---|---|---|---|---:|---:|---:|---:|---:|")
        for row in problems[:30]:
            natural = row.get("natural_win_reason") or row.get("win_reason") or "none"
            lines.append(
                f"| {i(row, 'board_size')} | `{row.get('matchup', '-')}` | {row.get('winner') or 'none'} | "
                f"{row.get('win_reason') or 'none'} | {natural} | {i(row, 'final_round')} | "
                f"{i(row, 'p_controlled')}/{i(row, 'e_controlled')}/{i(row, 'neutral_fields')} | "
                f"{i(row, 'fortify')} | {i(row, 'rebuild')} | {i(row, 'raid_takeovers')} |"
            )
    else:
        lines.append("No obvious stalls or extreme rebuild/fortify cases detected.")

    lines.extend([
        "",
        "## Design Read",
        "",
        "- Competitive pool reports should usually exclude dedicated stress bots such as `utility_rusher`.",
        "- Stress pool reports should show whether normal bots survive against the hard pressure bot.",
        "- `utility_fortifier` and `utility_economist` should be judged by conversion behavior, not only raw winrate.",
        "- `utility_opportunist` is the strongest candidate for a useful non-rusher personality.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Maillon personality report from runtime_matrix CSV output.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--stall-round", type=int, default=121)
    parser.add_argument("--title", default="Maillon v0.5 Personality Report")
    parser.add_argument(
        "--include-policies",
        nargs="*",
        default=None,
        help="Only include matchups where both policies are in this list. Comma-separated values are accepted.",
    )
    parser.add_argument(
        "--exclude-policies",
        nargs="*",
        default=None,
        help="Exclude matchups where either side uses one of these policies. Comma-separated values are accepted.",
    )
    parser.add_argument(
        "--focus-policy",
        default=None,
        help="Only include matchups where this policy appears on either side.",
    )
    args = parser.parse_args()

    all_rows = read_rows(args.input)
    include_policies = parse_policy_filter(args.include_policies)
    exclude_policies = parse_policy_filter(args.exclude_policies)
    focus_policy = args.focus_policy.strip() if args.focus_policy else None

    rows = filter_rows(
        all_rows,
        include_policies=include_policies,
        exclude_policies=exclude_policies,
        focus_policy=focus_policy,
    )

    if not rows:
        raise ValueError("No rows left after applying report filters.")

    stats = summarize(rows)
    write_csv(args.csv_out, stats)

    report = build_report(
        rows,
        stats,
        args.input,
        args.csv_out,
        args.stall_round,
        args.title,
        len(all_rows),
        include_policies,
        exclude_policies,
        focus_policy,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report + "\n", encoding="utf-8")

    print(report)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.csv_out}")


if __name__ == "__main__":
    main()
