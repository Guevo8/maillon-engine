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
        if not row.get("winner") or row.get("win_reason") == "none":
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


def build_report(rows: list[dict[str, str]], stats: dict[str, dict[str, object]], source: Path, csv_out: Path, stall_round: int) -> str:
    lines = [
        "# Maillon v0.5 Personality Report",
        "",
        "## Source",
        "",
        f"- Input matrix: `{source}`",
        f"- Summary CSV: `{csv_out}`",
        f"- Rows: {len(rows)}",
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
        "- `Slots` means appearances as player plus appearances as enemy.",
        "- Fortify/Rebuild/Build/Raid/Wait/Waste are actor-side totals.",
        "- Current runtime matrix conflict columns such as `raid_takeovers`, `raid_absorbed_by_shield` and `final_shield_points` are match-level metrics, not clean per-policy ownership. They are therefore not used in the policy summary table.",
        "",
        "## Problem Matchups",
        "",
    ])

    problems = problem_rows(rows, stall_round)
    if problems:
        lines.append("| Board | Matchup | Winner | Reason | Round | P/E/N | Fortify | Rebuild | Takeovers |")
        lines.append("|---:|---|---|---|---:|---:|---:|---:|---:|")
        for row in problems[:30]:
            lines.append(
                f"| {i(row, 'board_size')} | `{row.get('matchup', '-')}` | {row.get('winner') or 'none'} | "
                f"{row.get('win_reason') or 'none'} | {i(row, 'final_round')} | "
                f"{i(row, 'p_controlled')}/{i(row, 'e_controlled')}/{i(row, 'neutral_fields')} | "
                f"{i(row, 'fortify')} | {i(row, 'rebuild')} | {i(row, 'raid_takeovers')} |"
            )
    else:
        lines.append("No obvious stalls or extreme rebuild/fortify cases detected.")

    lines.extend([
        "",
        "## Design Read",
        "",
        "- `utility_rusher` can stay as a hard stress bot if its high winrate is intentional.",
        "- `utility_fortifier` needs a stronger win plan if it remains low-win and high-defense.",
        "- `utility_economist` needs better conversion from economy into upgrades, expansion and territory pressure.",
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
    args = parser.parse_args()

    rows = read_rows(args.input)
    stats = summarize(rows)
    write_csv(args.csv_out, stats)

    report = build_report(rows, stats, args.input, args.csv_out, args.stall_round)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report + "\n", encoding="utf-8")

    print(report)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.csv_out}")


if __name__ == "__main__":
    main()
