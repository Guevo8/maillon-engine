from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.state import CellState, create_initial_state
from src.maillon_v04.tunnel_actions import (
    TunnelAction,
    affordable_repair_build_targets,
    affordable_tunnel_extend_targets,
    affordable_tunnel_raid_pairs,
    apply_tunnel_action,
    repair_build_targets,
    tunnel_entrance_targets,
    tunnel_extend_targets,
    tunnel_raid_pairs,
)
from src.maillon_v04.tunnels import add_tunnel_edge, has_tunnel_edge, tunnel_access_nodes, tunnel_pressure


ActorId = str


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



def test_tunnel_entrance() -> None:
    print_section("1. tunnel_entrance")

    state = create_initial_state(4)
    actor = "player"

    # v0.6.2: tunnel entrances are not allowed on Core fields.
    # Initial player non-core field is (-2, 0).
    target = (-2, 0)

    state.actor_state(actor).resources["Holz"] = 2
    state.actor_state(actor).resources["Stein"] = 2

    before_targets = tunnel_entrance_targets(state, actor)
    result = apply_tunnel_action(
        state,
        TunnelAction(actor=actor, action_type="tunnel_entrance", target=target),
    )

    print("before targets:", before_targets)
    print("result:", result)
    print("resources:", dict(state.actor_state(actor).resources))
    print("pressure:", tunnel_pressure(state, target))

    assert_true(target in before_targets, "entrance target available before action")
    assert_equal(result.ok, True, "tunnel_entrance ok")
    assert_equal(state.cell(target).has_tunnel_entrance, True, "entrance flag")
    assert_equal(tunnel_pressure(state, target), 1, "entrance pressure")
    assert_equal(state.actor_state(actor).resources["Holz"], 1, "Holz after entrance")
    assert_equal(state.actor_state(actor).resources["Stein"], 0, "Stein after entrance")
    assert_true(target not in tunnel_entrance_targets(state, actor), "entrance target removed after action")


def test_tunnel_extend() -> None:
    print_section("2. tunnel_extend")

    state = create_initial_state(4)
    actor = "player"

    # v0.6.2:
    # - entrance must be on an owned non-core field
    # - extend target must be occupied non-core, not neutral
    entrance = (-2, 0)
    target = (-1, 0)

    state.cell(target).owner = actor
    state.cell(target).field_type = "Stein"
    state.cell(target).level = 1
    state.cell(target).active_from_round = 1
    state.cell(target).collapsed = False

    state.actor_state(actor).resources["Holz"] = 3
    state.actor_state(actor).resources["Stein"] = 3

    entrance_result = apply_tunnel_action(
        state,
        TunnelAction(actor=actor, action_type="tunnel_entrance", target=entrance),
    )
    assert_equal(entrance_result.ok, True, "setup entrance ok")

    pairs = affordable_tunnel_extend_targets(state, actor)
    assert_true((entrance, target) in pairs, "occupied extend target available")

    extend_result = apply_tunnel_action(
        state,
        TunnelAction(
            actor=actor,
            action_type="tunnel_extend",
            source=entrance,
            target=target,
        ),
    )

    print("extend pairs:", tunnel_extend_targets(state, actor))
    print("chosen:", (entrance, target))
    print("result:", extend_result)
    print("edges:", sorted(state.tunnel_edges))
    print("access:", sorted(tunnel_access_nodes(state, actor)))

    assert_equal(extend_result.ok, True, "tunnel_extend ok")
    assert_equal(len(state.tunnel_edges), 1, "one tunnel edge after extend")
    assert_equal(tunnel_pressure(state, entrance), 2, "source pressure includes entrance")
    assert_equal(tunnel_pressure(state, target), 1, "target pressure")
    assert_true(entrance in tunnel_access_nodes(state, actor), "source reachable")
    assert_true(target in tunnel_access_nodes(state, actor), "target reachable")


def test_tunnel_extend_collapse() -> None:
    print_section("3. tunnel_extend collapse")

    state = create_initial_state(4)
    actor = "player"
    center = (0, 0)

    state.cells[center] = CellState(
        owner=actor,
        field_type="Holz",
        level=1,
        active_from_round=1,
    )

    state.actor_state(actor).resources["Holz"] = 10
    state.actor_state(actor).resources["Stein"] = 10

    entrance_result = apply_tunnel_action(
        state,
        TunnelAction(actor=actor, action_type="tunnel_entrance", target=center),
    )
    assert_equal(entrance_result.ok, True, "center entrance ok")
    assert_equal(tunnel_pressure(state, center), 1, "center pressure after entrance")

    # v0.6.2: entrance already counts as pressure +1.
    # Therefore collapse happens after 3 additional tunnel edges:
    # pressure = entrance 1 + 3 edges = 4.
    neighbors = state.board.neighbors(center)[:3]

    for neighbor in neighbors:
        cell = state.cell(neighbor)
        cell.owner = actor
        cell.field_type = "Stein"
        cell.level = 1
        cell.active_from_round = 1
        cell.collapsed = False

    for index, neighbor in enumerate(neighbors, start=1):
        result = apply_tunnel_action(
            state,
            TunnelAction(
                actor=actor,
                action_type="tunnel_extend",
                source=center,
                target=neighbor,
            ),
        )

        print(
            f"extend {index}: result={result.ok}, collapsed={result.collapsed}, "
            f"center_pressure={tunnel_pressure(state, center)}, "
            f"center_collapsed={state.cell(center).collapsed}, "
            f"edges={sorted(state.tunnel_edges)}"
        )

        assert_equal(result.ok, True, f"extend {index} ok")

        if index < 3:
            assert_equal(result.collapsed, (), f"extend {index} no collapse")
            assert_equal(state.cell(center).collapsed, False, f"center not collapsed after extend {index}")
            assert_equal(tunnel_pressure(state, center), index + 1, f"pressure after extend {index}")
        else:
            assert_equal(result.collapsed, (center,), "extend 3 collapses center")
            assert_equal(state.cell(center).collapsed, True, "center collapsed")
            assert_equal(state.cell(center).owner, None, "collapsed owner")
            assert_equal(state.cell(center).field_type, None, "collapsed field_type")
            assert_equal(state.cell(center).level, 0, "collapsed level")
            assert_equal(state.cell(center).raid_shield, 0, "collapsed shield")
            assert_equal(state.cell(center).has_tunnel_entrance, False, "collapsed entrance")
            assert_equal(len(state.tunnel_edges), 0, "collapse removes incident edges")
            assert_equal(tunnel_pressure(state, center), 0, "pressure after collapse")


def test_tunnel_raid() -> None:
    print_section("4. tunnel_raid")

    state = create_initial_state(4)
    actor = "player"
    enemy = "enemy"

    # source in corridor (own active entrance), target is adjacent enemy cell
    source = (-2, 0)
    target = (-1, 0)

    state.cell(source).owner = actor
    state.cell(source).field_type = "Holz"
    state.cell(source).level = 1
    state.cell(source).active_from_round = 1
    state.cell(source).has_tunnel_entrance = True

    state.cell(target).owner = enemy
    state.cell(target).field_type = "Stein"
    state.cell(target).level = 2
    state.cell(target).raid_shield = 3
    state.cell(target).has_tunnel_entrance = True
    state.cell(target).active_from_round = 1
    state.cell(target).collapsed = False

    state.actor_state(actor).resources["Holz"] = 1
    state.actor_state(actor).resources["Stein"] = 1
    state.actor_state(actor).resources["Korn"] = 3

    pairs = tunnel_raid_pairs(state, actor)
    affordable = affordable_tunnel_raid_pairs(state, actor)
    result = apply_tunnel_action(
        state,
        TunnelAction(actor=actor, action_type="tunnel_raid", source=source, target=target),
    )

    print("pairs:", pairs)
    print("affordable:", affordable)
    print("result:", result)
    print("after:", {
        "owner": state.cell(target).owner,
        "field_type": state.cell(target).field_type,
        "level": state.cell(target).level,
        "shield": state.cell(target).raid_shield,
        "entrance": state.cell(target).has_tunnel_entrance,
        "contested": state.cell(target).contested_count,
        "active_from": state.cell(target).active_from_round,
        "holz": state.actor_state(actor).resources["Holz"],
        "stein": state.actor_state(actor).resources["Stein"],
        "korn": state.actor_state(actor).resources["Korn"],
        "edges": sorted(state.tunnel_edges),
    })

    assert_equal(pairs, [(source, target)], "tunnel raid pairs")
    assert_equal(affordable, [(source, target)], "affordable tunnel raid pairs")
    assert_equal(result.ok, True, "tunnel_raid ok")
    assert_equal(state.cell(target).owner, actor, "target owner after tunnel_raid")
    assert_equal(state.cell(target).field_type, "Stein", "target field_type after tunnel_raid")
    assert_equal(state.cell(target).level, 2, "target level after tunnel_raid")
    assert_equal(state.cell(target).raid_shield, 0, "target shield after tunnel_raid")
    assert_equal(state.cell(target).has_tunnel_entrance, False, "target entrance cleared after tunnel_raid")
    assert_equal(state.actor_state(actor).resources["Holz"], 0, "Holz after tunnel_raid")
    assert_equal(state.actor_state(actor).resources["Stein"], 0, "Stein after tunnel_raid")
    assert_equal(state.actor_state(actor).resources["Korn"], 0, "Korn after tunnel_raid")
    assert_equal(has_tunnel_edge(state, source, target), True, "tunnel edge created after tunnel_raid")
    assert_equal(len(state.tunnel_edges), 1, "exactly one tunnel edge after tunnel_raid")

def test_repair_build() -> None:
    print_section("5. repair_build")

    state = create_initial_state(4)
    actor = "player"
    target = (-2, 0)

    cell = state.cell(target)
    cell.collapsed = True
    cell.owner = None
    cell.field_type = None
    cell.level = 0
    cell.raid_shield = 0
    cell.has_tunnel_entrance = False

    state.actor_state(actor).resources["Holz"] = 2
    state.actor_state(actor).resources["Stein"] = 2

    targets = repair_build_targets(state, actor)
    affordable = affordable_repair_build_targets(state, actor)
    result = apply_tunnel_action(
        state,
        TunnelAction(
            actor=actor,
            action_type="repair_build",
            target=target,
            field_type="Stein",
        ),
    )

    print("targets:", targets)
    print("affordable:", affordable)
    print("result:", result)
    print("after:", {
        "collapsed": state.cell(target).collapsed,
        "owner": state.cell(target).owner,
        "field_type": state.cell(target).field_type,
        "level": state.cell(target).level,
        "shield": state.cell(target).raid_shield,
        "entrance": state.cell(target).has_tunnel_entrance,
        "active_from": state.cell(target).active_from_round,
        "resources": dict(state.actor_state(actor).resources),
        "entrance_targets_same_round": tunnel_entrance_targets(state, actor),
    })

    assert_equal(targets, [target], "repair_build targets")
    assert_equal(affordable, [target], "affordable repair_build targets")
    assert_equal(result.ok, True, "repair_build ok")
    assert_equal(state.cell(target).collapsed, False, "target no longer collapsed")
    assert_equal(state.cell(target).owner, actor, "repair owner")
    assert_equal(state.cell(target).field_type, "Stein", "repair field_type")
    assert_equal(state.cell(target).level, 1, "repair level")
    assert_equal(state.cell(target).raid_shield, 0, "repair shield")
    assert_equal(state.cell(target).has_tunnel_entrance, False, "repair entrance")
    assert_equal(state.cell(target).active_from_round, 2, "repair activation delay")
    assert_true(target not in tunnel_entrance_targets(state, actor), "repaired field is not same-round entrance target")


def run_smoke_suite() -> None:
    print("MAILLON v0.6 TUNNEL ACTION SMOKE SUITE")
    print("=" * 72)

    test_tunnel_entrance()
    test_tunnel_extend()
    test_tunnel_extend_collapse()
    test_tunnel_raid()
    test_repair_build()

    print()
    print("RESULT: tunnel action smoke suite OK")


if __name__ == "__main__":
    run_smoke_suite()
