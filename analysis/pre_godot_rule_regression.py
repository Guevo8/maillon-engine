"""Pre-Godot rule regression suite.

Covers: collapse-aware victory, entrance capacity, tunnel extend semantics,
local corridor, local tunnel raid, normal raid side effects, repair-build.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.actions import (
    Action,
    action_summary,
    apply_action,
    tunnel_raid_targets,
)
from src.maillon_v04.bot import choose_bot_action
from src.maillon_v04.bot_tunnel_probe import choose_tunnel_raid_pair
from src.maillon_v04.bot_utility_tunneler import generate_tunnel_candidates
from src.maillon_v04.rules import (
    effective_board_size,
    has_territory_win,
    territory_threshold_60,
    winner_by_full_board,
    winner_by_territory,
)
from src.maillon_v04.state import CellState, create_initial_state
from src.maillon_v04.tunnel_actions import (
    TunnelAction,
    affordable_tunnel_entrance_targets,
    affordable_tunnel_raid_pairs,
    apply_tunnel_action,
    repair_build_targets,
    tunnel_extend_targets,
    tunnel_extend_targets_from,
    tunnel_raid_pairs,
    tunnel_raid_targets_from,
)
from src.maillon_v04.tunnel_rules import (
    owned_tunnel_entrance_count,
    tunnel_entrance_capacity,
)
from src.maillon_v04.tunnels import (
    actor_tunnel_corridor,
    add_tunnel_edge,
    has_tunnel_edge,
    tunnel_pressure,
)


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


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * 72)


# ---------------------------------------------------------------------------
# Group A — Victory thresholds (collapse-aware)
# ---------------------------------------------------------------------------

def test_group_a_victory_thresholds() -> None:
    print_section("A. Victory thresholds (collapse-aware)")

    # Direct boundary table on a side=5 board (61 cells). Collapse cells one
    # at a time and check the exact threshold at each effective board size.
    s5 = create_initial_state(5)
    collapsible = [c for c in s5.cells if c not in (s5.player_core, s5.enemy_core)]
    assert_equal(effective_board_size(s5), 61, "A0: 61 active cells")
    assert_equal(territory_threshold_60(s5), 37, "A0: 61 → threshold 37")
    s5.cell(collapsible[0]).collapsed = True
    assert_equal(effective_board_size(s5), 60, "A0: 60 active cells")
    assert_equal(territory_threshold_60(s5), 36, "A0: 60 → threshold 36")
    s5.cell(collapsible[1]).collapsed = True
    assert_equal(effective_board_size(s5), 59, "A0: 59 active cells")
    assert_equal(territory_threshold_60(s5), 36, "A0: 59 → threshold 36")
    s5.cell(collapsible[2]).collapsed = True
    assert_equal(effective_board_size(s5), 58, "A0: 58 active cells")
    assert_equal(territory_threshold_60(s5), 35, "A0: 58 → threshold 35")

    # Player controls 36/61 → below threshold 37 → no territory win.
    s5b = create_initial_state(5)
    non_core = [c for c in s5b.cells if c not in (s5b.player_core, s5b.enemy_core)]
    for coord in non_core:
        s5b.cell(coord).owner = None  # reset to neutral for a precise count
    # player_core stays player-owned; add 35 non-core cells → exactly 36.
    controlled = non_core[:35]
    for coord in controlled:
        s5b.cell(coord).owner = "player"
    assert_equal(s5b.controlled_count("player"), 36, "A0b: player controls 36")
    assert_equal(territory_threshold_60(s5b), 37, "A0b: 61 active → threshold 37")
    assert_equal(has_territory_win(s5b, "player"), False, "A0b: 36 < 37 → no win")
    # One collapse OUTSIDE the controlled set → 60 active → threshold 36 → win.
    outside = non_core[35]
    s5b.cell(outside).collapsed = True
    assert_equal(effective_board_size(s5b), 60, "A0b: 60 active after collapse")
    assert_equal(territory_threshold_60(s5b), 36, "A0b: threshold drops to 36")
    assert_equal(has_territory_win(s5b, "player"), True, "A0b: 36 >= 36 → immediate win")

    # Full-board tie → deterministically no winner. Collapse one cell so no
    # non-collapsed neutral remains, split the rest evenly 18/18.
    s5c = create_initial_state(4)
    coords4 = list(s5c.cells.keys())
    s5c.cell(coords4[0]).owner = None
    s5c.cell(coords4[0]).collapsed = True
    rest = coords4[1:]
    half = len(rest) // 2  # 36 / 2 = 18
    for coord in rest[:half]:
        s5c.cell(coord).owner = "player"
    for coord in rest[half:]:
        s5c.cell(coord).owner = "enemy"
    assert_equal(len(s5c.neutral_cells()), 0, "A0c: no non-collapsed neutral remains")
    assert_equal(s5c.controlled_count("player"), s5c.controlled_count("enemy"), "A0c: counts tie")
    assert_equal(winner_by_full_board(s5c), None, "A0c: full-board tie → no winner")

    # side=4 board has 37 cells; threshold = ceil(37 * 0.60) = 23
    state = create_initial_state(4)
    assert_equal(effective_board_size(state), 37, "A1: initial effective_board_size=37")
    assert_equal(territory_threshold_60(state), 23, "A1: initial threshold=23")

    # Collapse 1 cell
    some_cell = (-2, -1)
    state.cell(some_cell).collapsed = True
    assert_equal(effective_board_size(state), 36, "A2: after 1 collapse, size=36")
    assert_equal(territory_threshold_60(state), 22, "A2: after 1 collapse, threshold=22")

    # Collapse 2nd cell
    some_cell2 = (-2, 1)
    state.cell(some_cell2).collapsed = True
    assert_equal(effective_board_size(state), 35, "A3: after 2 collapses, size=35")
    assert_equal(territory_threshold_60(state), 21, "A3: after 2 collapses, threshold=21")

    # Collapse 3rd cell
    some_cell3 = (-1, -1)
    state.cell(some_cell3).collapsed = True
    assert_equal(effective_board_size(state), 34, "A4: after 3 collapses, size=34")
    assert_equal(territory_threshold_60(state), 21, "A4: after 3 collapses, threshold=21")

    # Repair 1st cell: size restores
    state.cell(some_cell).collapsed = False
    assert_equal(effective_board_size(state), 35, "A5: after repair, size=35")
    assert_equal(territory_threshold_60(state), 21, "A5: after repair, threshold=21")

    # Collapse can create immediate winner
    state2 = create_initial_state(4)
    # Initial threshold=23; give player 22 cells → not yet winning
    player_cells = list(state2.cells.keys())[:22]
    for coord in player_cells:
        state2.cell(coord).owner = "player"
    # With 22 cells and threshold=23, player doesn't win
    assert_equal(has_territory_win(state2, "player"), False, "A6: 22 cells, threshold=23 → no win")
    # Collapse 1 cell (not owned by player): threshold drops to 22
    neutral_cell = [c for c in state2.cells if c not in player_cells][0]
    state2.cell(neutral_cell).collapsed = True
    assert_equal(territory_threshold_60(state2), 22, "A7: threshold drops after collapse")
    assert_equal(has_territory_win(state2, "player"), True, "A7: 22 cells, threshold=22 → win")

    # Full-board check ignores collapsed: collapsed neutral doesn't block win
    state3 = create_initial_state(4)
    # Set all cells to player or enemy, leave one collapsed neutral
    all_coords = list(state3.cells.keys())
    # Collapse the first non-core non-player cell
    for coord in all_coords:
        if state3.cell(coord).owner is None:
            state3.cell(coord).owner = "player"
    # Give one non-player cell to enemy
    for coord in all_coords:
        if coord != state3.player_core and coord != state3.enemy_core:
            state3.cell(coord).owner = "enemy"
            break
    # Now collapse one neutral (set back to None and collapsed)
    state3.cell(all_coords[0]).owner = None
    state3.cell(all_coords[0]).collapsed = True
    # winner_by_full_board should not return None because the only neutral cell is collapsed
    # (neutral_cells() excludes collapsed)
    winner = winner_by_full_board(state3)
    # Either player or enemy wins (enemy has more non-core), not None
    assert_true(winner is not None, "A8: full-board ignores collapsed neutral")


# ---------------------------------------------------------------------------
# Group B — Entrance capacity
# ---------------------------------------------------------------------------

def test_group_b_entrance_capacity() -> None:
    print_section("B. Entrance capacity")

    state = create_initial_state(4)
    actor = "player"
    player_wood = (-2, 0)
    # Give player a second and third non-core field to have targets available
    field_b = (-2, -1)
    field_c = (-1, 0)
    for f in (field_b, field_c):
        state.cell(f).owner = actor
        state.cell(f).field_type = "Korn"
        state.cell(f).level = 1
        state.cell(f).active_from_round = 1

    state.actor_state(actor).resources.update({"Holz": 5, "Stein": 5, "Korn": 5})

    # Core L1: capacity=1
    assert_equal(tunnel_entrance_capacity(state, actor), 1, "B1: core L1 capacity=1")
    assert_equal(owned_tunnel_entrance_count(state, actor), 0, "B1: initially 0 entrances")

    # With 0 entrances, player_wood is available
    targets = affordable_tunnel_entrance_targets(state, actor)
    assert_true(player_wood in targets, "B2: can build first entrance")

    # Build entrance on player_wood
    state.cell(player_wood).has_tunnel_entrance = True
    assert_equal(owned_tunnel_entrance_count(state, actor), 1, "B3: count=1 after build")

    # Core L1 capacity=1; no more entrances allowed even though field_b is free
    targets2 = affordable_tunnel_entrance_targets(state, actor)
    assert_equal(targets2, [], "B4: blocked at capacity 1 (core L1)")

    # Upgrade core to L2: capacity=2
    state.cell(state.player_core).level = 2
    assert_equal(tunnel_entrance_capacity(state, actor), 2, "B5: core L2 capacity=2")
    targets3 = affordable_tunnel_entrance_targets(state, actor)
    assert_true(len(targets3) > 0, "B6: can build second entrance at core L2")

    # Build second entrance on field_b
    state.cell(field_b).has_tunnel_entrance = True
    assert_equal(owned_tunnel_entrance_count(state, actor), 2, "B7: count=2")
    targets4 = affordable_tunnel_entrance_targets(state, actor)
    assert_equal(targets4, [], "B8: blocked at capacity 2 (core L2)")

    # Collapsed entrance frees a slot (field_c is available as new target)
    state.cell(player_wood).collapsed = True
    assert_equal(owned_tunnel_entrance_count(state, actor), 1, "B9: collapsed entrance not counted")
    targets5 = affordable_tunnel_entrance_targets(state, actor)
    assert_true(len(targets5) > 0, "B10: slot freed by collapse")

    # Restore player_wood; capture field_b (owner change) frees slot
    state.cell(player_wood).collapsed = False
    state.cell(field_b).owner = "enemy"
    assert_equal(owned_tunnel_entrance_count(state, actor), 1, "B11: captured-away entrance not counted")
    targets6 = affordable_tunnel_entrance_targets(state, actor)
    assert_true(len(targets6) > 0, "B12: slot freed after capture-away")

    # An INACTIVE own entrance still occupies a slot. Core L1 therefore blocks
    # a second entrance even though a free active field exists.
    s2 = create_initial_state(4)
    free_active = (-2, 0)  # own active, no entrance → would be a candidate
    inactive_ent = (-1, 0)
    s2.cell(inactive_ent).owner = actor
    s2.cell(inactive_ent).field_type = "Korn"
    s2.cell(inactive_ent).level = 1
    s2.cell(inactive_ent).active_from_round = 999  # inactive
    s2.cell(inactive_ent).has_tunnel_entrance = True
    s2.actor_state(actor).resources.update({"Holz": 5, "Stein": 5, "Korn": 5})
    assert_equal(owned_tunnel_entrance_count(s2, actor), 1, "B13: inactive entrance still counted")
    assert_true(s2.is_active(free_active), "B13: free field is active")
    assert_equal(
        affordable_tunnel_entrance_targets(s2, actor),
        [],
        "B14: inactive entrance occupies the only core-L1 slot",
    )

    # Repair does not recreate an entrance: a repaired collapsed cell has no
    # entrance, so the slot count does not rise from the repair itself.
    s3 = create_initial_state(4)
    own_origin = (-2, 0)
    collapsed_cell = (-1, 0)
    s3.cell(collapsed_cell).collapsed = True
    s3.cell(collapsed_cell).has_tunnel_entrance = True  # stale flag pre-repair
    s3.actor_state(actor).resources.update({"Holz": 5, "Stein": 5, "Korn": 5})
    before_count = owned_tunnel_entrance_count(s3, actor)
    apply_tunnel_action(
        s3,
        TunnelAction(actor=actor, action_type="repair_build", target=collapsed_cell, field_type="Korn"),
    )
    assert_equal(s3.cell(collapsed_cell).has_tunnel_entrance, False, "B15: repair leaves no entrance")
    assert_equal(owned_tunnel_entrance_count(s3, actor), before_count, "B16: repair does not add a slot")
    _ = own_origin


# ---------------------------------------------------------------------------
# Group C — Tunnel Extend rules
# ---------------------------------------------------------------------------

def test_group_c_tunnel_extend() -> None:
    print_section("C. Tunnel Extend rules")

    state = create_initial_state(4)
    actor = "player"
    source = (-2, 0)  # own active, has entrance → in corridor

    state.cell(source).has_tunnel_entrance = True

    # Own adjacent non-core non-collapsed → allowed
    own_target = (-1, 0)
    state.cell(own_target).owner = actor
    state.cell(own_target).field_type = "Holz"
    state.cell(own_target).level = 1
    state.cell(own_target).active_from_round = 1
    targets_from = tunnel_extend_targets_from(state, actor, source)
    assert_true(own_target in targets_from, "C1: own adjacent target allowed")

    # Core adjacent → not in targets ((-3,0) is player core)
    assert_true((-3, 0) not in targets_from, "C2: core adjacent excluded")

    # Neutral adjacent → not in targets
    neutral_adj = (-2, -1)  # still neutral in initial state
    assert_true(neutral_adj not in targets_from, "C3: neutral adjacent excluded")

    # Enemy adjacent → not in targets
    enemy_adj = (-1, -1)
    state.cell(enemy_adj).owner = "enemy"
    targets_from2 = tunnel_extend_targets_from(state, actor, source)
    assert_true(enemy_adj not in targets_from2, "C4: enemy adjacent excluded")

    # Collapsed own adjacent → not in targets
    state.cell(own_target).collapsed = True
    targets_from3 = tunnel_extend_targets_from(state, actor, source)
    assert_true(own_target not in targets_from3, "C5: collapsed own excluded")
    state.cell(own_target).collapsed = False

    # Inactive source → not a valid source in pairs
    state.cell(source).active_from_round = 999
    pairs_inactive = tunnel_extend_targets(state, actor)
    # source is inactive so filtered in tunnel_extend_targets
    source_in_pairs = any(s == source for s, _ in pairs_inactive)
    assert_true(not source_in_pairs, "C6: inactive source excluded from extend pairs")
    state.cell(source).active_from_round = 1

    # Inactive own target → valid (source active, target may be inactive)
    state.cell(own_target).active_from_round = 999
    targets_from4 = tunnel_extend_targets_from(state, actor, source)
    assert_true(own_target in targets_from4, "C7: inactive own target allowed")
    state.cell(own_target).active_from_round = 1

    # Duplicate edge → not returned a second time
    add_tunnel_edge(state, source, own_target)
    targets_from5 = tunnel_extend_targets_from(state, actor, source)
    assert_true(own_target not in targets_from5, "C8: existing edge not returned again")


# ---------------------------------------------------------------------------
# Group D — Corridor semantics
# ---------------------------------------------------------------------------

def test_group_d_corridor() -> None:
    print_section("D. Corridor semantics")

    state = create_initial_state(4)
    actor = "player"
    entrance_coord = (-2, 0)

    # Active entrance: corridor contains entrance cell
    state.cell(entrance_coord).has_tunnel_entrance = True
    corridor = actor_tunnel_corridor(state, actor)
    assert_true(entrance_coord in corridor, "D1: active entrance in corridor")

    # Inactive entrance: does NOT start corridor
    state.cell(entrance_coord).active_from_round = 999
    corridor2 = actor_tunnel_corridor(state, actor)
    assert_equal(corridor2, set(), "D2: inactive entrance → empty corridor")
    state.cell(entrance_coord).active_from_round = 1

    # Inactive own cell reachable from active entrance via edge: IS in corridor
    inactive_own = (-1, 0)
    state.cell(inactive_own).owner = actor
    state.cell(inactive_own).field_type = "Korn"
    state.cell(inactive_own).level = 1
    state.cell(inactive_own).active_from_round = 999  # inactive
    add_tunnel_edge(state, entrance_coord, inactive_own)
    corridor3 = actor_tunnel_corridor(state, actor)
    assert_true(inactive_own in corridor3, "D3: inactive own cell reachable from entrance is in corridor")

    # Enemy cell adjacent (no edge): NOT in corridor
    enemy_adj = (-2, -1)
    state.cell(enemy_adj).owner = "enemy"
    corridor4 = actor_tunnel_corridor(state, actor)
    assert_true(enemy_adj not in corridor4, "D4: enemy adjacent cell not in corridor")

    # Enemy cell connected via edge: NOT in corridor (BFS stops at non-own)
    state2 = create_initial_state(4)
    state2.cell(entrance_coord).has_tunnel_entrance = True
    enemy_via_edge = (-1, 0)
    state2.cell(enemy_via_edge).owner = "enemy"
    state2.cell(enemy_via_edge).field_type = "Korn"
    state2.cell(enemy_via_edge).active_from_round = 1
    add_tunnel_edge(state2, entrance_coord, enemy_via_edge)
    corridor5 = actor_tunnel_corridor(state2, actor)
    assert_true(enemy_via_edge not in corridor5, "D5: enemy cell via edge not in corridor")

    # Disconnected own cell with no active entrance: NOT in corridor
    state3 = create_initial_state(4)
    disconnected = (-2, 0)
    state3.cell(disconnected).owner = actor
    # No entrance set, so no BFS starts
    corridor6 = actor_tunnel_corridor(state3, actor)
    assert_true(disconnected not in corridor6, "D6: own cell without entrance not in corridor")

    # Own network WITH edges but no ACTIVE entrance → not accessible.
    state7 = create_initial_state(4)
    a = (-2, 0)
    b = (-1, 0)
    state7.cell(a).has_tunnel_entrance = True
    state7.cell(a).active_from_round = 999  # entrance present but inactive
    state7.cell(b).owner = actor
    state7.cell(b).field_type = "Korn"
    state7.cell(b).active_from_round = 1
    add_tunnel_edge(state7, a, b)
    assert_equal(actor_tunnel_corridor(state7, actor), set(), "D7: edges but no active entrance → empty corridor")

    # An ENEMY tunnel entrance does not start the actor's corridor.
    state8 = create_initial_state(4)
    enemy_ent = (1, 0)
    state8.cell(enemy_ent).owner = "enemy"
    state8.cell(enemy_ent).field_type = "Korn"
    state8.cell(enemy_ent).active_from_round = 1
    state8.cell(enemy_ent).has_tunnel_entrance = True
    assert_equal(actor_tunnel_corridor(state8, actor), set(), "D8: enemy entrance does not start own corridor")

    # An enemy cell in a physical chain blocks traversal to the own cell behind.
    state9 = create_initial_state(4)
    own_ent = (-2, 0)
    enemy_mid = (-1, 0)
    own_behind = (0, 0)
    state9.cell(own_ent).has_tunnel_entrance = True
    state9.cell(enemy_mid).owner = "enemy"
    state9.cell(enemy_mid).field_type = "Korn"
    state9.cell(enemy_mid).active_from_round = 1
    state9.cell(own_behind).owner = actor
    state9.cell(own_behind).field_type = "Korn"
    state9.cell(own_behind).active_from_round = 1
    add_tunnel_edge(state9, own_ent, enemy_mid)
    add_tunnel_edge(state9, enemy_mid, own_behind)
    corridor9 = actor_tunnel_corridor(state9, actor)
    assert_true(own_ent in corridor9, "D9: entrance in corridor")
    assert_true(own_behind not in corridor9, "D9: enemy mid blocks traversal to own cell behind")

    # An inactive own cell stays in the corridor but is NOT a valid source for
    # either tunnel_extend or tunnel_raid.
    state10 = create_initial_state(4)
    ent10 = (-2, 0)
    inactive_own10 = (-1, 0)
    enemy_neighbor10 = (0, 0)
    state10.cell(ent10).has_tunnel_entrance = True
    state10.cell(inactive_own10).owner = actor
    state10.cell(inactive_own10).field_type = "Korn"
    state10.cell(inactive_own10).active_from_round = 999  # inactive
    add_tunnel_edge(state10, ent10, inactive_own10)
    state10.cell(enemy_neighbor10).owner = "enemy"
    state10.cell(enemy_neighbor10).field_type = "Korn"
    state10.cell(enemy_neighbor10).active_from_round = 1
    assert_true(inactive_own10 in actor_tunnel_corridor(state10, actor), "D10: inactive own cell stays in corridor")
    assert_equal(tunnel_extend_targets_from(state10, actor, inactive_own10), [], "D10: inactive own not an extend source")
    assert_equal(tunnel_raid_targets_from(state10, actor, inactive_own10), [], "D11: inactive own not a raid source")


# ---------------------------------------------------------------------------
# Group E — Tunnel Raid semantics
# ---------------------------------------------------------------------------

def test_group_e_tunnel_raid() -> None:
    print_section("E. Tunnel Raid semantics")

    def _base_state():
        state = create_initial_state(4)
        source = (-2, 0)
        target = (-1, 0)
        state.cell(source).has_tunnel_entrance = True  # source in corridor
        state.cell(target).owner = "enemy"
        state.cell(target).field_type = "Korn"
        state.cell(target).level = 1
        state.cell(target).active_from_round = 1
        state.cell(target).collapsed = False
        state.actor_state("player").resources.update({"Holz": 5, "Stein": 5, "Korn": 5})
        return state, source, target

    actor = "player"

    # Adjacent enemy cell: in tunnel_raid_pairs
    state, source, target = _base_state()
    pairs = tunnel_raid_pairs(state, actor)
    assert_true((source, target) in pairs, "E1: adjacent enemy in pairs")

    # Non-adjacent enemy cell: NOT in pairs
    far_enemy = (2, 0)
    state.cell(far_enemy).owner = "enemy"
    pairs2 = tunnel_raid_pairs(state, actor)
    assert_true(not any(t == far_enemy for _, t in pairs2), "E2: non-adjacent enemy not in pairs")

    # Inactive source: NOT a valid pair source
    state3, source3, target3 = _base_state()
    state3.cell(source3).active_from_round = 999
    pairs3 = tunnel_raid_pairs(state3, actor)
    assert_true(not any(s == source3 for s, _ in pairs3), "E3: inactive source not valid")

    # Source not in corridor: NOT valid
    state4, source4, target4 = _base_state()
    state4.cell(source4).has_tunnel_entrance = False  # remove entrance → no corridor
    pairs4 = tunnel_raid_pairs(state4, actor)
    assert_equal(pairs4, [], "E4: no corridor → no pairs")

    # Full apply: shield bypassed, target captured
    state5, source5, target5 = _base_state()
    state5.cell(target5).raid_shield = 3
    result = apply_tunnel_action(
        state5,
        TunnelAction(actor=actor, action_type="tunnel_raid", source=source5, target=target5),
    )
    assert_equal(result.ok, True, "E5: tunnel_raid ok")
    assert_equal(state5.cell(target5).owner, actor, "E5: target captured")
    assert_equal(state5.cell(target5).raid_shield, 0, "E5: shield fully bypassed")

    # Target entrance cleared after raid
    state6, source6, target6 = _base_state()
    state6.cell(target6).has_tunnel_entrance = True
    apply_tunnel_action(
        state6,
        TunnelAction(actor=actor, action_type="tunnel_raid", source=source6, target=target6),
    )
    assert_equal(state6.cell(target6).has_tunnel_entrance, False, "E6: target entrance cleared")

    # Tunnel edge created after raid
    state7, source7, target7 = _base_state()
    apply_tunnel_action(
        state7,
        TunnelAction(actor=actor, action_type="tunnel_raid", source=source7, target=target7),
    )
    assert_equal(has_tunnel_edge(state7, source7, target7), True, "E7: tunnel edge created")

    # No duplicate edge if already exists
    state8, source8, target8 = _base_state()
    add_tunnel_edge(state8, source8, target8)
    apply_tunnel_action(
        state8,
        TunnelAction(actor=actor, action_type="tunnel_raid", source=source8, target=target8),
    )
    assert_equal(len(state8.tunnel_edges), 1, "E8: no duplicate edge")

    # Full costs deducted
    state9, source9, target9 = _base_state()
    state9.actor_state(actor).resources.update({"Holz": 1, "Stein": 1, "Korn": 3})
    apply_tunnel_action(
        state9,
        TunnelAction(actor=actor, action_type="tunnel_raid", source=source9, target=target9),
    )
    assert_equal(state9.actor_state(actor).resources["Holz"], 0, "E9: Holz deducted")
    assert_equal(state9.actor_state(actor).resources["Stein"], 0, "E9: Stein deducted")
    assert_equal(state9.actor_state(actor).resources["Korn"], 0, "E9: Korn deducted")

    # contested_count incremented; cooldown set
    state10, source10, target10 = _base_state()
    state10.cell(target10).contested_count = 0
    apply_tunnel_action(
        state10,
        TunnelAction(actor=actor, action_type="tunnel_raid", source=source10, target=target10),
    )
    assert_equal(state10.cell(target10).contested_count, 1, "E10: contested_count=1")
    assert_equal(
        state10.cell(target10).active_from_round,
        state10.round_index + 1,
        "E10: cooldown=1 (first contest)",
    )

    # tunnel_raid_targets_from self-validates the source contract.
    s, src, tgt = _base_state()
    assert_equal(tunnel_raid_targets_from(s, actor, (-2, -1)), [], "E11: neutral source → []")
    assert_equal(tunnel_raid_targets_from(s, actor, tgt), [], "E11: enemy source → []")
    assert_equal(tunnel_raid_targets_from(s, actor, s.player_core), [], "E11: core source → []")
    s_in, src_in, _ = _base_state()
    s_in.cell(src_in).active_from_round = 999
    assert_equal(tunnel_raid_targets_from(s_in, actor, src_in), [], "E11: inactive source → []")
    s_oc, _, _ = _base_state()
    out_src = (0, 0)  # own active, but not connected to any active entrance
    s_oc.cell(out_src).owner = actor
    s_oc.cell(out_src).field_type = "Korn"
    s_oc.cell(out_src).active_from_round = 1
    assert_equal(tunnel_raid_targets_from(s_oc, actor, out_src), [], "E11: source outside corridor → []")

    # A valid pair appears in pairs AND its target in tunnel_raid_targets; the
    # action summary reports a non-zero affordable raid count.
    s_v, src_v, tgt_v = _base_state()
    assert_true((src_v, tgt_v) in tunnel_raid_pairs(s_v, actor), "E12: valid pair present")
    assert_true(tgt_v in tunnel_raid_targets(s_v, actor), "E12: target consistent in tunnel_raid_targets")
    assert_true(
        action_summary(s_v, actor)["affordable_tunnel_raid_targets"] > 0,
        "E12: action_summary reports the raid",
    )

    # Cost contract: each of Holz/Stein/Korn is required; exactly 1/1/3 pays.
    def _affordable_with(res):
        s_c, _, _ = _base_state()
        s_c.actor_state(actor).resources.update(res)
        return len(affordable_tunnel_raid_pairs(s_c, actor)) > 0

    assert_equal(_affordable_with({"Holz": 0, "Stein": 5, "Korn": 5}), False, "E13: no Holz → not affordable")
    assert_equal(_affordable_with({"Holz": 5, "Stein": 0, "Korn": 5}), False, "E13: no Stein → not affordable")
    assert_equal(_affordable_with({"Holz": 5, "Stein": 5, "Korn": 2}), False, "E13: <3 Korn → not affordable")
    assert_equal(_affordable_with({"Holz": 1, "Stein": 1, "Korn": 3}), True, "E13: exactly 1/1/3 → affordable")

    # Bot candidate sets source AND target explicitly.
    s_b, src_b, tgt_b = _base_state()
    raid_candidates = [c for c in generate_tunnel_candidates(s_b, actor) if c.action_type == "tunnel_raid"]
    assert_true(len(raid_candidates) > 0, "E14: bot produces a raid candidate")
    assert_true(raid_candidates[0].source is not None, "E14: candidate has source")
    assert_true(raid_candidates[0].target is not None, "E14: candidate has target")

    # Pre-existing edge: not duplicated, and full cost still deducted (no discount).
    s_e, src_e, tgt_e = _base_state()
    s_e.actor_state(actor).resources.update({"Holz": 1, "Stein": 1, "Korn": 3})
    add_tunnel_edge(s_e, src_e, tgt_e)
    apply_tunnel_action(
        s_e,
        TunnelAction(actor=actor, action_type="tunnel_raid", source=src_e, target=tgt_e),
    )
    assert_equal(len(s_e.tunnel_edges), 1, "E15: pre-existing edge not duplicated")
    assert_equal(s_e.actor_state(actor).resources["Holz"], 0, "E15: full Holz cost despite existing edge")
    assert_equal(s_e.actor_state(actor).resources["Stein"], 0, "E15: full Stein cost despite existing edge")
    assert_equal(s_e.actor_state(actor).resources["Korn"], 0, "E15: full Korn cost despite existing edge")

    # Collapse invariant: a raid edge raises pressure and must trigger the same
    # collapse check as tunnel_extend. Pre-load the target with pressure 3 so
    # the new raid edge tips it to the threshold (4).
    s_col, src_col, tgt_col = _base_state()
    pre_edge_neighbors = [n for n in s_col.board.neighbors(tgt_col) if n != src_col][:3]
    for n in pre_edge_neighbors:
        add_tunnel_edge(s_col, tgt_col, n)
    assert_equal(tunnel_pressure(s_col, tgt_col), 3, "E16: target pre-loaded to pressure 3")
    result_col = apply_tunnel_action(
        s_col,
        TunnelAction(actor=actor, action_type="tunnel_raid", source=src_col, target=tgt_col),
    )
    assert_true(tgt_col in result_col.collapsed, "E16: raid edge triggers collapse of target")
    assert_equal(s_col.cell(tgt_col).collapsed, True, "E16: target collapsed")
    assert_equal(s_col.cell(tgt_col).owner, None, "E16: collapsed target has no owner")


# ---------------------------------------------------------------------------
# Group F — Normal Raid side effects
# ---------------------------------------------------------------------------

def test_group_f_normal_raid_side_effects() -> None:
    print_section("F. Normal Raid side effects")

    actor = "player"

    def _base_state():
        state = create_initial_state(4)
        # Own cell adjacent to target
        own = (-2, 0)
        target = (-1, 0)
        state.cell(own).owner = actor
        state.cell(own).field_type = "Holz"
        state.cell(own).level = 1
        state.cell(own).active_from_round = 1

        state.cell(target).owner = "enemy"
        state.cell(target).field_type = "Korn"
        state.cell(target).level = 1
        state.cell(target).raid_shield = 0
        state.cell(target).active_from_round = 1
        state.cell(target).has_tunnel_entrance = True
        state.actor_state(actor).resources.update({"Holz": 5, "Stein": 5, "Korn": 10})
        return state, own, target

    # Shield-hit (no capture): has_tunnel_entrance unchanged
    state, own, target = _base_state()
    state.cell(target).raid_shield = 2
    before_entrance = state.cell(target).has_tunnel_entrance
    apply_action(state, Action(actor=actor, action_type="raid", target=target))
    assert_equal(
        state.cell(target).has_tunnel_entrance,
        before_entrance,
        "F1: shield-hit doesn't clear entrance",
    )
    assert_equal(state.cell(target).owner, "enemy", "F1: no capture on shield-hit")

    # Capture: has_tunnel_entrance = False
    state2, own2, target2 = _base_state()
    state2.cell(target2).raid_shield = 0
    apply_action(state2, Action(actor=actor, action_type="raid", target=target2))
    assert_equal(state2.cell(target2).owner, actor, "F2: capture happened")
    assert_equal(state2.cell(target2).has_tunnel_entrance, False, "F2: entrance cleared on capture")

    # Capture: no tunnel edge added
    state3, own3, target3 = _base_state()
    state3.cell(target3).raid_shield = 0
    initial_edges = set(state3.tunnel_edges)
    apply_action(state3, Action(actor=actor, action_type="raid", target=target3))
    assert_equal(state3.tunnel_edges, initial_edges, "F3: no tunnel edge added by normal raid")

    # Existing edge: not removed after capture
    state4, own4, target4 = _base_state()
    state4.cell(target4).raid_shield = 0
    add_tunnel_edge(state4, own4, target4)
    apply_action(state4, Action(actor=actor, action_type="raid", target=target4))
    assert_equal(has_tunnel_edge(state4, own4, target4), True, "F4: existing edge kept after capture")


# ---------------------------------------------------------------------------
# Group G — Repair Build
# ---------------------------------------------------------------------------

def test_group_g_repair_build() -> None:
    print_section("G. Repair Build")

    state = create_initial_state(4)
    actor = "player"
    own = (-2, 0)  # player-owned active anchor
    collapsed_adj = (-1, 0)
    far_collapsed = (2, 0)  # collapsed but NOT adjacent to any active own cell

    # Adjacent collapsed cell is reparable; a genuinely collapsed but distant
    # cell is not (the earlier non-collapsed far cell was an insufficient test).
    state.cell(collapsed_adj).collapsed = True
    state.cell(far_collapsed).owner = None
    state.cell(far_collapsed).collapsed = True
    targets = repair_build_targets(state, actor)
    assert_true(collapsed_adj in targets, "G1: adjacent collapsed cell in targets")
    assert_true(state.cell(far_collapsed).collapsed, "G2: far cell is genuinely collapsed")
    assert_true(far_collapsed not in targets, "G2: distant collapsed cell not reparable")

    # Non-collapsed cell: not in targets
    not_collapsed = (-2, -1)
    assert_true(not_collapsed not in targets, "G3: non-collapsed cell not in targets")

    # A CHAIN of collapsed cells must not let a far-repair leak through it. Only
    # the link directly adjacent to the active own anchor is reparable.
    chain_state = create_initial_state(4)
    anchor = (-2, 0)  # player active
    link1 = (-1, 0)   # adjacent to anchor
    link2 = (0, 0)    # adjacent to link1, two hops from anchor
    chain_state.cell(link1).owner = None
    chain_state.cell(link1).collapsed = True
    chain_state.cell(link2).owner = None
    chain_state.cell(link2).collapsed = True
    chain_targets = repair_build_targets(chain_state, actor)
    assert_true(link1 in chain_targets, "G_chain: first link (adjacent to anchor) reparable")
    assert_true(link2 not in chain_targets, "G_chain: no far-repair through the collapsed chain")
    _ = anchor

    # Repair sets correct fields, including the chosen field type.
    state.actor_state(actor).resources.update({"Holz": 5, "Stein": 5, "Korn": 5})
    state.cell(collapsed_adj).has_tunnel_entrance = True  # should be cleared by repair
    apply_tunnel_action(
        state,
        TunnelAction(
            actor=actor,
            action_type="repair_build",
            target=collapsed_adj,
            field_type="Holz",
        ),
    )
    cell = state.cell(collapsed_adj)
    assert_equal(cell.collapsed, False, "G4: repaired cell not collapsed")
    assert_equal(cell.owner, actor, "G4: repaired cell owned by actor")
    assert_equal(cell.field_type, "Holz", "G4: repaired cell field_type set to chosen type")
    assert_equal(cell.level, 1, "G4: repaired cell level=1")
    assert_equal(cell.raid_shield, 0, "G4: repaired cell shield=0")
    assert_equal(cell.has_tunnel_entrance, False, "G4: repaired cell entrance=False")
    assert_equal(cell.active_from_round, state.round_index + 1, "G4: repaired cell active next round")
    _ = own


# ---------------------------------------------------------------------------
# Group H — Tunnel probe raid target heuristic
# ---------------------------------------------------------------------------

def test_group_h_tunnel_probe_heuristic() -> None:
    print_section("H. Tunnel probe raid target heuristic")

    actor = "player"
    source = (-2, 0)       # player's starting Holz field — only corridor source
    target_holz = (-2, 1)  # weaker: Holz, sorted first (target x=-2 < x=-1)
    target_korn = (-1, 0)  # stronger: Korn, sorted second (target x=-1)

    state = create_initial_state(4)
    state.cell(source).has_tunnel_entrance = True
    state.actor_state(actor).resources.update({"Holz": 1, "Stein": 1, "Korn": 3})

    # Two affordable enemy targets adjacent to the entrance
    state.cells[target_holz] = CellState(
        owner="enemy", field_type="Holz", level=1, active_from_round=1
    )
    state.cells[target_korn] = CellState(
        owner="enemy", field_type="Korn", level=1, active_from_round=1
    )

    pairs = affordable_tunnel_raid_pairs(state, actor)
    assert_true(len(pairs) >= 2, "H1: at least two affordable pairs exist")

    # Verify sorted order puts the Holz target first (source equal, -2 < -1 on target x)
    first_source, first_target = pairs[0]
    assert_equal(first_target, target_holz, "H2: first sorted pair targets the Holz (weaker) cell")

    # choose_tunnel_raid_pair must prefer the Korn target (higher FIELD_VALUE)
    best_source, best_target = choose_tunnel_raid_pair(state, actor, pairs)
    assert_equal(best_target, target_korn, "H3: choose_tunnel_raid_pair picks the Korn target")
    assert_equal(best_source, source, "H4: source is the entrance cell")

    # Bot policy must also produce the Korn target
    action = choose_bot_action(state, actor, "tunnel_probe")
    assert_equal(action.action_type, "tunnel_raid", "H5: tunnel_probe dispatches tunnel_raid")
    assert_equal(action.target, target_korn, "H6: tunnel_probe picks the Korn (better) target")
    assert_equal(action.source, source, "H7: tunnel_probe source is the entrance cell")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_smoke_suite() -> None:
    print()
    print("=" * 72)
    print("Pre-Godot Rule Regression Suite")
    print("=" * 72)

    test_group_a_victory_thresholds()
    test_group_b_entrance_capacity()
    test_group_c_tunnel_extend()
    test_group_d_corridor()
    test_group_e_tunnel_raid()
    test_group_f_normal_raid_side_effects()
    test_group_g_repair_build()
    test_group_h_tunnel_probe_heuristic()

    print()
    print("=" * 72)
    print(f"Results: {_PASSED} passed, {_FAILED} failed")
    print("=" * 72)

    if _FAILED > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_smoke_suite()
