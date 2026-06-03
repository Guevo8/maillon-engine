from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.runtime_matrix import run_matrix


POLICIES = ("phase_player", "rusher", "utility_balancer")
REQUIRED_COLUMNS = {
    "side_length",
    "board_size",
    "matchup",
    "player_policy",
    "enemy_policy",
    "winner",
    "win_reason",
    "natural_winner",
    "natural_win_reason",
    "final_round",
    "p_controlled",
    "e_controlled",
    "neutral_fields",
    "build",
    "raid",
    "fortify",
    "rebuild",
    "field_upgrade",
    "core_upgrade",
    "wait",
    "raid_takeovers",
    "raid_absorbed_by_shield",
    "final_shield_points",
    "tunnel_entrance",
    "tunnel_extend",
    "tunnel_raid",
    "repair_build",
    "tunnel_raid_takeovers",
    "shield_bypassed",
    "collapsed_fields_total",
    "collapsed_fields_final",
    "tunnel_edges_final",
    "tunnel_nodes_final",
    "network_components_final",
    "largest_tunnel_component",
    "fields_with_tunnel_entrance",
    "max_tunnel_pressure_final",
    "avg_tunnel_pressure_final_x100",
    "p_tunnel_entrance",
    "p_tunnel_extend",
    "p_tunnel_raid",
    "p_repair_build",
    "e_tunnel_entrance",
    "e_tunnel_extend",
    "e_tunnel_raid",
    "e_repair_build",
}

ZERO_TUNNEL_COLUMNS = {
    "tunnel_entrance",
    "tunnel_extend",
    "tunnel_raid",
    "repair_build",
    "tunnel_raid_takeovers",
    "shield_bypassed",
    "collapsed_fields_total",
    "collapsed_fields_final",
    "tunnel_edges_final",
    "tunnel_nodes_final",
    "network_components_final",
    "largest_tunnel_component",
    "fields_with_tunnel_entrance",
    "max_tunnel_pressure_final",
    "avg_tunnel_pressure_final_x100",
    "p_tunnel_entrance",
    "p_tunnel_extend",
    "p_tunnel_raid",
    "p_repair_build",
    "e_tunnel_entrance",
    "e_tunnel_extend",
    "e_tunnel_raid",
    "e_repair_build",
}


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(f"{label}: expected truthy value")


def run_smoke() -> None:
    print("MAILLON v0.6 RUNTIME MATRIX COMPAT SMOKE")
    print("=" * 72)
    print("Purpose: verify that v0.5 bot/runtime matrix still runs after main action integration.")
    print("Tunnel actions are integrated into the main action model, but current bots should not use them yet.")
    print()

    rows = run_matrix(
        side_lengths=[4],
        policies=POLICIES,
        max_rounds=60,
        actions_per_turn=3,
        timeout_majority_margin=5,
    )

    expected_rows = len(POLICIES) * len(POLICIES)
    assert_equal(len(rows), expected_rows, "row count")

    for row in rows:
        missing = REQUIRED_COLUMNS.difference(row.keys())
        assert_equal(missing, set(), f"missing required columns for {row.get('matchup')}")
        assert_true(int(row["final_round"]) >= 1, f"final_round for {row['matchup']}")

        for column in ZERO_TUNNEL_COLUMNS:
            assert_equal(int(row[column]), 0, f"{column} should remain 0 before tunnel-aware bots in {row['matchup']}")

    print("rows:", len(rows))
    print("board,matchup,winner,reason,round,p/e/n,build,raid,fortify,rebuild,wait,tunnel_entrance,tunnel_extend,tunnel_raid,repair_build")

    for row in rows:
        print(
            f"{row['board_size']},"
            f"{row['matchup']},"
            f"{row['winner']},"
            f"{row['win_reason']},"
            f"{row['final_round']},"
            f"{row['p_controlled']}/{row['e_controlled']}/{row['neutral_fields']},"
            f"{row['build']},"
            f"{row['raid']},"
            f"{row['fortify']},"
            f"{row['rebuild']},"
            f"{row['wait']},"
            f"{row['tunnel_entrance']},"
            f"{row['tunnel_extend']},"
            f"{row['tunnel_raid']},"
            f"{row['repair_build']}"
        )

    print()
    print("RESULT: runtime matrix compatibility smoke OK")


if __name__ == "__main__":
    run_smoke()
