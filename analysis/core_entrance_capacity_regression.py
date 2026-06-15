"""Regression checks for the tunnel-entrance core-capacity invariant.

The current state model stores each actor's core at a canonical board
coordinate. Gameplay treats that core as immutable actor infrastructure: it
is not a normal capturable or collapsible field. These checks deliberately
construct invalid synthetic states to ensure downstream tunnel legality fails
closed instead of granting level-1 entrance capacity.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.state import ActorId, GameState, create_initial_state
from src.maillon_v04.tunnel_actions import (
    affordable_tunnel_entrance_targets,
    repair_build_targets,
    tunnel_entrance_targets,
)
from src.maillon_v04.tunnel_rules import tunnel_entrance_capacity


_PASSED = 0
_FAILED = 0


def assert_equal(actual: object, expected: object, label: str) -> None:
    global _PASSED, _FAILED
    if actual != expected:
        print(f"  FAIL [{label}]: expected {expected!r}, got {actual!r}")
        _FAILED += 1
    else:
        _PASSED += 1


def assert_true(value: bool, label: str) -> None:
    global _PASSED, _FAILED
    if not value:
        print(f"  FAIL [{label}]: expected truthy, got {value!r}")
        _FAILED += 1
    else:
        _PASSED += 1


def core_coord(state: GameState, actor: ActorId):
    return state.player_core if actor == "player" else state.enemy_core


def prepare_state(actor: ActorId) -> GameState:
    state = create_initial_state(4)
    state.actor_state(actor).resources.update({"Holz": 10, "Stein": 10, "Korn": 10})
    return state


def assert_no_capacity_or_targets(state: GameState, actor: ActorId, label: str) -> None:
    assert_equal(tunnel_entrance_capacity(state, actor), 0, f"{label}: capacity=0")
    assert_equal(tunnel_entrance_targets(state, actor), [], f"{label}: no legal targets")
    assert_equal(
        affordable_tunnel_entrance_targets(state, actor),
        [],
        f"{label}: no affordable targets",
    )


def test_actor(actor: ActorId) -> None:
    print(f"\n{actor}: live canonical core")
    print("-" * 72)

    baseline = prepare_state(actor)
    canonical_core = core_coord(baseline, actor)
    owned_non_core = next(
        coord
        for coord in baseline.active_owned_cells(actor)
        if not baseline.cell(coord).is_core
    )

    assert_equal(tunnel_entrance_capacity(baseline, actor), 1, f"{actor} L1 core capacity")
    assert_true(canonical_core not in tunnel_entrance_targets(baseline, actor), f"{actor} core is never a target")
    assert_true(owned_non_core in tunnel_entrance_targets(baseline, actor), f"{actor} non-core field is a target")

    baseline.cell(canonical_core).level = 2
    assert_equal(tunnel_entrance_capacity(baseline, actor), 2, f"{actor} L2 core capacity")

    print(f"\n{actor}: invalid synthetic core states fail closed")
    print("-" * 72)

    collapsed = prepare_state(actor)
    collapsed.cell(core_coord(collapsed, actor)).collapsed = True
    assert_no_capacity_or_targets(collapsed, actor, f"{actor} collapsed core")

    unowned = prepare_state(actor)
    unowned.cell(core_coord(unowned, actor)).owner = None
    assert_no_capacity_or_targets(unowned, actor, f"{actor} unowned core")

    captured = prepare_state(actor)
    captured.cell(core_coord(captured, actor)).owner = captured.opponent(actor)
    assert_no_capacity_or_targets(captured, actor, f"{actor} opponent-owned core coordinate")

    not_core = prepare_state(actor)
    not_core.cell(core_coord(not_core, actor)).field_type = "Holz"
    assert_no_capacity_or_targets(not_core, actor, f"{actor} canonical coordinate is not Core")

    # repair_build must not target the core even in a synthetic collapsed state.
    # A collapsed non-core field adjacent to the same origin IS a valid target;
    # only the core coordinate is defended.
    print(f"\n{actor}: collapsed core is not a repair_build target")
    print("-" * 72)

    collapsed_core_state = prepare_state(actor)
    core = core_coord(collapsed_core_state, actor)
    collapsed_core_state.cell(core).collapsed = True
    rb_targets = repair_build_targets(collapsed_core_state, actor)
    assert_true(core not in rb_targets, f"{actor} collapsed core not in repair_build_targets")


def run_regression() -> None:
    global _PASSED, _FAILED
    _PASSED = 0
    _FAILED = 0

    print("=" * 72)
    print("CORE ENTRANCE CAPACITY REGRESSION")
    print("=" * 72)

    test_actor("player")
    test_actor("enemy")

    print()
    print("=" * 72)
    print(f"RESULT: {_PASSED} passed, {_FAILED} failed")
    print("=" * 72)

    if _FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    run_regression()
