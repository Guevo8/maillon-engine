from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.actions import (
    Action,
    action_summary,
    apply_action,
    build_targets,
    field_upgrade_targets,
    fortify_targets,
    raid_targets,
    rebuild_targets,
)
from src.maillon_v04.state import create_initial_state


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


def test_wait() -> None:
    print_section("1. wait")

    state = create_initial_state(4)
    result = apply_action(state, Action(actor="player", action_type="wait"))

    print("result:", result)

    assert_equal(result.ok, True, "wait ok")
    assert_equal(result.winner, None, "wait winner")


def test_build() -> None:
    print_section("2. build")

    state = create_initial_state(4)
    actor = "player"
    state.actor_state(actor).resources["Holz"] = 10

    targets = build_targets(state, actor)
    target = targets[0]
    result = apply_action(
        state,
        Action(actor=actor, action_type="build", target=target, field_type="Stein"),
    )

    print("targets:", targets)
    print("chosen:", target)
    print("result:", result)
    print("after:", {
        "owner": state.cell(target).owner,
        "field_type": state.cell(target).field_type,
        "level": state.cell(target).level,
        "active_from": state.cell(target).active_from_round,
        "holz": state.actor_state(actor).resources["Holz"],
    })

    assert_equal(result.ok, True, "build ok")
    assert_equal(state.cell(target).owner, actor, "build owner")
    assert_equal(state.cell(target).field_type, "Stein", "build field_type")
    assert_equal(state.cell(target).level, 1, "build level")
    assert_equal(state.cell(target).active_from_round, 2, "build activation delay")


def test_rebuild() -> None:
    print_section("3. rebuild")

    state = create_initial_state(4)
    actor = "player"
    target = (-2, 0)
    state.actor_state(actor).resources["Holz"] = 2

    targets = rebuild_targets(state, actor)
    result = apply_action(
        state,
        Action(actor=actor, action_type="rebuild", target=target, field_type="Stein"),
    )

    print("targets:", targets)
    print("result:", result)
    print("after:", {
        "field_type": state.cell(target).field_type,
        "active_from": state.cell(target).active_from_round,
        "holz": state.actor_state(actor).resources["Holz"],
    })

    assert_true(target in targets, "rebuild target available")
    assert_equal(result.ok, True, "rebuild ok")
    assert_equal(state.cell(target).field_type, "Stein", "rebuild field_type")
    assert_equal(state.cell(target).active_from_round, 2, "rebuild activation delay")
    assert_equal(state.actor_state(actor).resources["Holz"], 0, "Holz after rebuild")


def test_field_upgrade() -> None:
    print_section("4. field_upgrade")

    state = create_initial_state(4)
    actor = "player"
    target = (-2, 0)
    state.actor_state(actor).resources["Stein"] = 3

    targets = field_upgrade_targets(state, actor)
    result = apply_action(
        state,
        Action(actor=actor, action_type="field_upgrade", target=target),
    )

    print("targets:", targets)
    print("result:", result)
    print("after:", {
        "level": state.cell(target).level,
        "stein": state.actor_state(actor).resources["Stein"],
    })

    assert_true(target in targets, "field upgrade target available")
    assert_equal(result.ok, True, "field_upgrade ok")
    assert_equal(state.cell(target).level, 2, "field upgrade level")
    assert_equal(state.actor_state(actor).resources["Stein"], 0, "Stein after field_upgrade")


def test_core_upgrade() -> None:
    print_section("5. core_upgrade")

    state = create_initial_state(4)
    actor = "player"
    target = state.player_core
    state.actor_state(actor).resources["Stein"] = 4

    result = apply_action(
        state,
        Action(actor=actor, action_type="core_upgrade", target=target),
    )

    print("result:", result)
    print("after:", {
        "core_level": state.cell(target).level,
        "stein": state.actor_state(actor).resources["Stein"],
        "caps": dict(state.actor_state(actor).caps),
    })

    assert_equal(result.ok, True, "core_upgrade ok")
    assert_equal(state.cell(target).level, 2, "core level")
    assert_equal(state.actor_state(actor).resources["Stein"], 0, "Stein after core_upgrade")


def test_fortify() -> None:
    print_section("6. fortify")

    state = create_initial_state(4)
    actor = "player"
    target = (-2, 0)
    state.actor_state(actor).resources["Korn"] = 2

    targets = fortify_targets(state, actor)
    result = apply_action(
        state,
        Action(actor=actor, action_type="fortify", target=target),
    )

    print("targets:", targets)
    print("result:", result)
    print("after:", {
        "shield": state.cell(target).raid_shield,
        "korn": state.actor_state(actor).resources["Korn"],
    })

    assert_true(target in targets, "fortify target available")
    assert_equal(result.ok, True, "fortify ok")
    assert_equal(state.cell(target).raid_shield, 1, "fortify shield")
    assert_equal(state.actor_state(actor).resources["Korn"], 0, "Korn after fortify")


def test_raid_takeover() -> None:
    print_section("7. raid takeover")

    state = create_initial_state(4)
    actor = "player"
    target = (-1, 0)

    state.cell(target).owner = "enemy"
    state.cell(target).field_type = "Stein"
    state.cell(target).level = 1
    state.cell(target).active_from_round = 1
    state.cell(target).raid_shield = 0
    state.actor_state(actor).resources["Korn"] = 3

    targets = raid_targets(state, actor)
    result = apply_action(
        state,
        Action(actor=actor, action_type="raid", target=target),
    )

    print("targets:", targets)
    print("result:", result)
    print("after:", {
        "owner": state.cell(target).owner,
        "shield": state.cell(target).raid_shield,
        "contested": state.cell(target).contested_count,
        "active_from": state.cell(target).active_from_round,
        "korn": state.actor_state(actor).resources["Korn"],
    })

    assert_true(target in targets, "raid target available")
    assert_equal(result.ok, True, "raid takeover ok")
    assert_equal(state.cell(target).owner, actor, "raid owner")
    assert_equal(state.cell(target).raid_shield, 0, "raid shield")
    assert_equal(state.cell(target).contested_count, 1, "raid contested")
    assert_equal(state.cell(target).active_from_round, 2, "raid cooldown")
    assert_equal(state.actor_state(actor).resources["Korn"], 0, "Korn after raid")


def test_raid_shield_damage() -> None:
    print_section("8. raid shield damage")

    state = create_initial_state(4)
    actor = "player"
    target = (-1, 0)

    state.cell(target).owner = "enemy"
    state.cell(target).field_type = "Stein"
    state.cell(target).level = 1
    state.cell(target).active_from_round = 1
    state.cell(target).raid_shield = 2
    state.actor_state(actor).resources["Korn"] = 3

    result = apply_action(
        state,
        Action(actor=actor, action_type="raid", target=target),
    )

    print("result:", result)
    print("after:", {
        "owner": state.cell(target).owner,
        "shield": state.cell(target).raid_shield,
        "contested": state.cell(target).contested_count,
        "active_from": state.cell(target).active_from_round,
        "korn": state.actor_state(actor).resources["Korn"],
    })

    assert_equal(result.ok, True, "raid shield ok")
    assert_equal(state.cell(target).owner, "enemy", "shield raid keeps owner")
    assert_equal(state.cell(target).raid_shield, 1, "shield reduced by one")
    assert_equal(state.cell(target).contested_count, 1, "shield raid contested")
    assert_equal(state.cell(target).active_from_round, 2, "shield raid cooldown")
    assert_equal(state.actor_state(actor).resources["Korn"], 0, "Korn after shield raid")


def test_collapsed_exclusion() -> None:
    print_section("9. collapsed field exclusion")

    state = create_initial_state(4)
    actor = "player"
    collapsed_target = (-1, 0)

    cell = state.cell(collapsed_target)
    cell.collapsed = True
    cell.owner = None
    cell.field_type = None
    cell.level = 0
    cell.raid_shield = 0
    cell.has_tunnel_entrance = False

    summary = action_summary(state, actor)

    print("summary:", summary)
    print("build targets:", build_targets(state, actor))
    print("raid targets:", raid_targets(state, actor))

    assert_true(collapsed_target not in build_targets(state, actor), "collapsed not build target")
    assert_true(collapsed_target not in raid_targets(state, actor), "collapsed not raid target")


def test_tunnel_dispatch_from_main() -> None:
    print_section("10. tunnel dispatch from main apply_action")

    state = create_initial_state(4)
    actor = "player"

    # v0.6.2 rule:
    # - tunnel entrances are not allowed on Core fields
    # - tunnel_extend targets must be occupied non-core fields
    #
    # Initial player non-core field is (-2, 0).
    # We prepare an adjacent occupied non-core target at (-1, 0).
    entrance_target = (-2, 0)
    extend_target = (-1, 0)

    state.actor_state(actor).resources["Holz"] = 6
    state.actor_state(actor).resources["Stein"] = 6
    state.actor_state(actor).resources["Korn"] = 6

    target_cell = state.cell(extend_target)
    target_cell.owner = actor
    target_cell.field_type = "Stein"
    target_cell.level = 1
    target_cell.active_from_round = 1
    target_cell.collapsed = False

    entrance_result = apply_action(
        state,
        Action(
            actor=actor,
            action_type="tunnel_entrance",
            target=entrance_target,
        ),
    )

    extend_result = apply_action(
        state,
        Action(
            actor=actor,
            action_type="tunnel_extend",
            source=entrance_target,
            target=extend_target,
        ),
    )

    print("entrance:", entrance_result)
    print("extend:", extend_result)
    print("edges:", sorted(state.tunnel_edges))

    assert_equal(entrance_result.ok, True, "main tunnel_entrance ok")
    assert_equal(extend_result.ok, True, "main tunnel_extend ok")
    assert_equal(state.cell(entrance_target).has_tunnel_entrance, True, "entrance set")
    assert_equal(len(state.tunnel_edges), 1, "one tunnel edge")

def run_smoke() -> None:
    print("MAILLON v0.6 MAIN ACTION REGRESSION SMOKE")
    print("=" * 72)

    test_wait()
    test_build()
    test_rebuild()
    test_field_upgrade()
    test_core_upgrade()
    test_fortify()
    test_raid_takeover()
    test_raid_shield_damage()
    test_collapsed_exclusion()
    test_tunnel_dispatch_from_main()

    print()
    print("RESULT: main action regression smoke OK")


if __name__ == "__main__":
    run_smoke()
