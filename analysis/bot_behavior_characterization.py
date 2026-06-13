"""
Characterization tests for choose_bot_action.

Purpose: lock current observable dispatch behavior so a later no-behavior
refactor of bot.py (extracting bot_registry.py / bot_legacy.py) can be
verified safe by re-running this suite.

Board layout for side_length=4 (radius=3):
    player_core=(-3,0)  player_wood=(-2,0)
    enemy_core=(3,0)    enemy_wood=(2,0)
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.actions import Action
from src.maillon_v04.bot import choose_bot_action
from src.maillon_v04.state import CellState, create_initial_state
from src.maillon_v04.tunnels import add_tunnel_edge


# ---------------------------------------------------------------------------
# Assertion helpers (same style as analysis/utility_tunneler_smoke.py)
# ---------------------------------------------------------------------------

def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(f"{label}: expected truthy value")


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * 72)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rusher_raids_adjacent_enemy() -> None:
    print_section("1. rusher_raids_adjacent_enemy")

    state = create_initial_state(4)
    # Holz=0 prevents rusher_finish_build_action from firing (needs affordable builds)
    state.actor_state("player").resources["Holz"] = 0
    # Place an active enemy Korn field adjacent to the player's wood at (-2,0)
    state.cells[(-1, 0)] = CellState(
        owner="enemy", field_type="Korn", level=1, active_from_round=1
    )

    action = choose_bot_action(state, "player", "rusher")

    assert_equal(action.action_type, "raid", "rusher_raids")
    assert_equal(action.target, (-1, 0), "rusher_raid_target")
    assert_equal(action.actor, "player", "rusher_actor")
    print(f"  action={action.action_type} target={action.target} ✓")


def test_rusher_builds_toward_opponent_core() -> None:
    print_section("2. rusher_builds_toward_opponent_core")

    state = create_initial_state(4)
    state.actor_state("player").resources["Holz"] = 5
    # No adjacent enemy cells → raids list is empty
    # rusher_finish_build_action fires (near_territory_finish=True with 1 controlled cell)

    action = choose_bot_action(state, "player", "rusher")

    assert_equal(action.action_type, "build", "rusher_builds")
    assert_equal(action.target, (-1, 0), "rusher_build_target")   # uniquely closest to (3,0)
    assert_equal(action.field_type, "Korn", "rusher_field_korn")  # Korn=3 < threshold=4
    assert_equal(action.actor, "player", "rusher_actor")
    print(f"  action={action.action_type} target={action.target} field={action.field_type} ✓")


def test_phase_player_builds_in_early_game() -> None:
    print_section("3. phase_player_builds_in_early_game")

    state = create_initial_state(4)
    state.actor_state("player").resources["Holz"] = 5
    # non_core_controlled = 1 < 5 → early-game build branch

    action = choose_bot_action(state, "player", "phase_player")

    assert_equal(action.action_type, "build", "phase_builds")
    assert_equal(action.target, (-1, 0), "phase_target")   # uniquely closest to (3,0)
    assert_equal(action.field_type, "Holz", "phase_holz")  # non_core ≤ 2 → "Holz"
    assert_equal(action.actor, "player", "phase_actor")
    print(f"  action={action.action_type} target={action.target} field={action.field_type} ✓")


def test_opening_resource_spammer_builds_holz_first() -> None:
    print_section("4. opening_resource_spammer_builds_holz_first")

    state = create_initial_state(4)
    state.actor_state("player").resources.update({"Holz": 5, "Stein": 5, "Korn": 5})
    # holz_fields = 1 < _SPAMMER_HOLZ_TARGET = 2 → build Holz

    action = choose_bot_action(state, "player", "opening_resource_spammer")

    assert_equal(action.action_type, "build", "ors_builds")
    assert_equal(action.field_type, "Holz", "ors_holz_first")
    assert_equal(action.target, (-1, 0), "ors_closest_to_enemy")
    assert_equal(action.actor, "player", "ors_actor")
    print(f"  action={action.action_type} target={action.target} field={action.field_type} ✓")


def test_opening_resource_spammer_builds_korn_after_holz_met() -> None:
    print_section("5. opening_resource_spammer_builds_korn_after_holz_met")

    state = create_initial_state(4)
    # Second Holz field at (-1,0), adjacent to existing wood at (-2,0)
    state.cells[(-1, 0)].owner = "player"
    state.cells[(-1, 0)].field_type = "Holz"
    state.cells[(-1, 0)].active_from_round = 1
    state.actor_state("player").resources.update({"Holz": 5, "Stein": 5, "Korn": 5})
    # holz_fields = 2 ≥ 2, korn_fields = 0 < 2 → build Korn

    action = choose_bot_action(state, "player", "opening_resource_spammer")

    assert_equal(action.action_type, "build", "ors_korn_builds")
    assert_equal(action.field_type, "Korn", "ors_korn_field_type")
    assert_equal(action.target, (0, 0), "ors_korn_target")  # uniquely closest (dist=3)
    assert_equal(action.actor, "player", "ors_actor")
    print(f"  action={action.action_type} target={action.target} field={action.field_type} ✓")


def test_tunnel_probe_builds_entrance() -> None:
    print_section("6. tunnel_probe_builds_entrance")

    state = create_initial_state(4)
    state.actor_state("player").resources.update({"Holz": 5, "Stein": 5, "Korn": 5})
    # No tunnel infrastructure; tunnel_raid/extend/repair targets all empty
    # tunnel_entrance cost = Holz=1, Stein=2; only eligible own non-core field = (-2,0)

    action = choose_bot_action(state, "player", "tunnel_probe")

    assert_equal(action.action_type, "tunnel_entrance", "tp_entrance")
    assert_equal(action.target, (-2, 0), "tp_entrance_target")
    assert_equal(action.actor, "player", "tp_actor")
    print(f"  action={action.action_type} target={action.target} ✓")


def test_tunnel_all_in_probe_builds_entrance() -> None:
    print_section("7. tunnel_all_in_probe_builds_entrance")

    state = create_initial_state(4)
    state.actor_state("player").resources.update({"Holz": 5, "Stein": 5, "Korn": 5})

    action = choose_bot_action(state, "player", "tunnel_all_in_probe")

    assert_equal(action.action_type, "tunnel_entrance", "taip_entrance")
    assert_equal(action.target, (-2, 0), "taip_entrance_target")
    assert_equal(action.actor, "player", "taip_actor")
    print(f"  action={action.action_type} target={action.target} ✓")


def test_utility_balancer_builds_korn() -> None:
    print_section("8. utility_balancer_builds_korn")

    state = create_initial_state(4)
    state.actor_state("player").resources.update({"Holz": 4, "Stein": 4, "Korn": 4})
    # Caps=6; resource_need=0.333 for all types (equal) → Korn wins on FIELD_VALUE (7.5 vs 7.0)
    # (-3,1) and (-2,-1) tie at total_score=59.086; coord tie-break picks (-3,1) (x=-3 < x=-2)

    action = choose_bot_action(state, "player", "utility_balancer")

    assert_equal(action.action_type, "build", "ub_builds")
    assert_equal(action.field_type, "Korn", "ub_korn")
    assert_equal(action.target, (-3, 1), "ub_target")
    assert_equal(action.actor, "player", "ub_actor")
    print(f"  action={action.action_type} target={action.target} field={action.field_type} ✓")


def test_utility_tunneler_raids_via_tunnel() -> None:
    print_section("9. utility_tunneler_raids_via_tunnel")

    state = create_initial_state(4)
    player_wood = (-2, 0)
    # Holz=0, Stein=0 → no normal build/fortify/upgrade affordable → baseline near zero
    # Korn=4 covers tunnel_raid cost (=3); Korn=4 also defeats surface action threshold
    state.actor_state("player").resources.update({"Holz": 0, "Stein": 0, "Korn": 4})
    state.cell(player_wood).has_tunnel_entrance = True
    # Enemy field in cooldown: surface raids blocked (active_from_round check),
    # tunnel raids bypass cooldown — canonical use-case for utility_tunneler
    state.cells[(-1, 0)] = CellState(
        owner="enemy", field_type="Korn", level=1, active_from_round=999
    )
    add_tunnel_edge(state, player_wood, (-1, 0))

    action = choose_bot_action(state, "player", "utility_tunneler")

    assert_equal(action.action_type, "tunnel_raid", "ut_tunnel_raid")
    assert_equal(action.target, (-1, 0), "ut_tunnel_raid_target")
    assert_equal(action.actor, "player", "ut_actor")
    print(f"  action={action.action_type} target={action.target} ✓")


def test_all_policies_dispatch_valid_action() -> None:
    print_section("10. all_policies_dispatch_valid_action")

    ALL_POLICIES = [
        "rusher",
        "phase_player",
        "utility_balancer",
        "utility_rusher",
        "utility_economist",
        "utility_fortifier",
        "utility_aggro_turtle",
        "utility_opportunist",
        "tunnel_probe",
        "utility_tunneler",
        "opening_resource_spammer",
        "tunnel_all_in_probe",
    ]

    state = create_initial_state(4)
    state.actor_state("player").resources.update({"Holz": 5, "Stein": 5, "Korn": 5})

    for policy in ALL_POLICIES:
        action = choose_bot_action(state, "player", policy)
        assert_true(isinstance(action, Action), f"{policy}_returns_action")
        assert_equal(action.actor, "player", f"{policy}_actor_matches")
        assert_true(action.action_type is not None, f"{policy}_has_action_type")
        print(f"  {policy:30s} → {action.action_type}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_smoke_suite() -> None:
    print("=" * 72)
    print("bot behavior characterization suite")
    print("=" * 72)

    tests = [
        test_rusher_raids_adjacent_enemy,
        test_rusher_builds_toward_opponent_core,
        test_phase_player_builds_in_early_game,
        test_opening_resource_spammer_builds_holz_first,
        test_opening_resource_spammer_builds_korn_after_holz_met,
        test_tunnel_probe_builds_entrance,
        test_tunnel_all_in_probe_builds_entrance,
        test_utility_balancer_builds_korn,
        test_utility_tunneler_raids_via_tunnel,
        test_all_policies_dispatch_valid_action,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1

    print()
    print("=" * 72)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 72)

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    run_smoke_suite()
