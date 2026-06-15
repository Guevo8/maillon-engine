from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.actions import Action
from src.maillon_v04.bot import choose_bot_action
from src.maillon_v04.bot_utility_tunneler import (
    OPPORTUNITY_COST_TOLERANCE,
    TunnelScore,
    choose_utility_tunneler_action,
    generate_tunnel_candidates,
    score_tunnel_candidate,
    _get_normal_baseline,
)
from src.maillon_v04.state import CellState, create_initial_state
from src.maillon_v04.tunnels import add_tunnel_edge


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(f"{label}: expected truthy value")


def assert_in_range(value: float, lo: float, hi: float, label: str) -> None:
    if not (lo <= value <= hi):
        raise AssertionError(f"{label}: expected [{lo}, {hi}], got {value!r}")


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * 72)


def _setup_entrance_state():
    state = create_initial_state(4)
    actor = "player"
    # Player start wood is at (-2, 0) on side_length=4 board
    player_wood = (-2, 0)
    state.actor_state(actor).resources["Holz"] = 5
    state.actor_state(actor).resources["Stein"] = 5
    state.actor_state(actor).resources["Korn"] = 5
    state.cell(player_wood).has_tunnel_entrance = True
    return state, actor, player_wood


def test_candidates_generated() -> None:
    print_section("1. candidates_generated")

    # Use a fresh state WITHOUT pre-set entrance, so tunnel_entrance is affordable
    state = create_initial_state(4)
    actor = "player"
    state.actor_state(actor).resources["Holz"] = 5
    state.actor_state(actor).resources["Stein"] = 5
    state.actor_state(actor).resources["Korn"] = 5

    candidates = generate_tunnel_candidates(state, actor)

    assert_true(len(candidates) > 0, "at_least_one_candidate")

    action_types = {c.action_type for c in candidates}
    assert_true("wait" in action_types, "wait_in_candidates")
    # player has Holz=5 Stein=5, tunnel_entrance costs Holz=1 Stein=2
    assert_true("tunnel_entrance" in action_types, "tunnel_entrance_in_candidates")

    print(f"  candidate count: {len(candidates)}")
    print(f"  action types: {sorted(action_types)}")


def test_no_illegal_candidates_when_broke() -> None:
    print_section("2. no_illegal_candidates_when_broke")

    state = create_initial_state(4)
    actor = "player"
    state.actor_state(actor).resources["Holz"] = 0
    state.actor_state(actor).resources["Stein"] = 0
    state.actor_state(actor).resources["Korn"] = 0

    candidates = generate_tunnel_candidates(state, actor)
    action_types = {c.action_type for c in candidates}

    # No tunnel action should be affordable with zero resources
    assert_true("tunnel_entrance" not in action_types, "no_tunnel_entrance_when_broke")
    assert_true("tunnel_extend" not in action_types, "no_tunnel_extend_when_broke")
    assert_true("tunnel_raid" not in action_types, "no_tunnel_raid_when_broke")
    assert_equal(action_types, {"wait"}, "only_wait_when_broke")

    print(f"  candidates: {[c.action_type for c in candidates]}")


def test_scores_in_range() -> None:
    print_section("3. scores_in_range")

    state, actor, player_wood = _setup_entrance_state()
    normal_baseline = _get_normal_baseline(state, actor)
    candidates = generate_tunnel_candidates(state, actor)
    scores = [score_tunnel_candidate(state, actor, c, normal_baseline) for c in candidates]

    for ts in scores:
        assert_in_range(ts.score, 0.0, 1.0, f"score_{ts.action.action_type}")

    print(f"  scored {len(scores)} candidates, baseline={normal_baseline:.3f}")
    for ts in scores[:5]:
        print(f"  {ts.action.action_type:20s} score={ts.score:.4f}")


def test_opportunity_cost_blocks_tunnel() -> None:
    print_section("4. opportunity_cost_blocks_tunnel")

    # In the initial state with no tunnel network and many build opportunities,
    # the normal baseline is high, so wait (score=0.0) must be blocked.
    state = create_initial_state(4)
    actor = "player"
    state.actor_state(actor).resources["Holz"] = 6
    state.actor_state(actor).resources["Stein"] = 6
    state.actor_state(actor).resources["Korn"] = 6

    normal_baseline = _get_normal_baseline(state, actor)
    candidates = generate_tunnel_candidates(state, actor)

    # With no tunnel entrance, only "wait" and possibly tunnel_entrance are candidates
    scores = [score_tunnel_candidate(state, actor, c, normal_baseline) for c in candidates]
    best_tunnel = max(scores, key=lambda s: s.score)

    # Choose action and verify fallback occurs when tunnel is not competitive
    chosen = choose_utility_tunneler_action(state, actor)

    if best_tunnel.score < normal_baseline - OPPORTUNITY_COST_TOLERANCE:
        # Should NOT be wait (fallback to normal action)
        assert_true(
            chosen.action_type != "wait",
            "fallback_not_wait",
        )
        print(f"  fallback triggered: best_tunnel={best_tunnel.score:.3f} < normal={normal_baseline:.3f} - tol={OPPORTUNITY_COST_TOLERANCE}")
    else:
        print(f"  tunnel competitive: best_tunnel={best_tunnel.score:.3f} >= normal={normal_baseline:.3f} - tol={OPPORTUNITY_COST_TOLERANCE}")

    print(f"  chosen: {chosen.action_type}")
    print(f"  normal_baseline: {normal_baseline:.4f}")


def test_tunnel_raid_preferred_when_valuable() -> None:
    print_section("5. tunnel_raid_preferred_when_valuable")

    state = create_initial_state(4)
    actor = "player"
    player_wood = (-2, 0)

    # Minimal resources: Holz/Stein insufficient for build or entrance/extend,
    # Korn insufficient for normal surface raid support. Only tunnel_raid is
    # affordable, so its positive score comfortably exceeds the threshold.
    state.actor_state(actor).resources["Holz"] = 1
    state.actor_state(actor).resources["Stein"] = 1
    state.actor_state(actor).resources["Korn"] = 3  # exactly tunnel_raid cost

    # Player has a tunnel entrance and an edge to an enemy field.
    # The enemy field is put into cooldown (active_from_round far in future) so
    # normal surface raids are blocked (they require is_active), while tunnel
    # raids bypass the cooldown check entirely.  This is the canonical use case:
    # tunnel_raid reaches fields that are currently unraidable on the surface.
    state.cell(player_wood).has_tunnel_entrance = True
    enemy_target = (-1, 0)
    state.cells[enemy_target] = CellState(
        owner="enemy",
        field_type="Korn",
        level=1,
        active_from_round=999,  # in cooldown — surface raid blocked
    )
    add_tunnel_edge(state, player_wood, enemy_target)

    candidates = generate_tunnel_candidates(state, actor)
    action_types = [c.action_type for c in candidates]
    assert_true("tunnel_raid" in action_types, "tunnel_raid_in_candidates")

    normal_baseline = _get_normal_baseline(state, actor)
    scores = [score_tunnel_candidate(state, actor, c, normal_baseline) for c in candidates]
    raid_scores = [s for s in scores if s.action.action_type == "tunnel_raid"]
    assert_true(len(raid_scores) > 0, "raid_scored")

    best_raid = max(raid_scores, key=lambda s: s.score)
    print(f"  best_raid_score={best_raid.score:.4f} normal_baseline={normal_baseline:.4f}")
    assert_true(best_raid.score > 0.0, "raid_score_positive")

    # With low normal baseline, the raid should pass the opportunity-cost threshold
    from src.maillon_v04.bot_utility_tunneler import OPPORTUNITY_COST_TOLERANCE as TOL
    assert_true(
        best_raid.score >= normal_baseline - TOL,
        "raid_competitive_vs_baseline",
    )

    chosen = choose_utility_tunneler_action(state, actor)
    assert_equal(chosen.action_type, "tunnel_raid", "tunnel_raid_chosen")
    assert_true(chosen.source is not None, "tunnel_raid_has_source")
    print(f"  chosen: {chosen.action_type} source={chosen.source} target={chosen.target} ✓")


def test_bot_dispatch() -> None:
    print_section("6. bot_dispatch")

    state = create_initial_state(4)
    actor = "player"
    state.actor_state(actor).resources["Holz"] = 3
    state.actor_state(actor).resources["Stein"] = 3
    state.actor_state(actor).resources["Korn"] = 3

    action = choose_bot_action(state, actor, "utility_tunneler")
    assert_true(isinstance(action, Action), "returns_action_instance")
    assert_true(action.action_type is not None, "action_type_set")
    assert_equal(action.actor, actor, "actor_matches")

    print(f"  chosen: {action.action_type} target={action.target}")


def test_wait_always_present() -> None:
    print_section("7. wait_always_present")

    for side_length in (3, 4, 5):
        state = create_initial_state(side_length)
        actor = "player"
        candidates = generate_tunnel_candidates(state, actor)
        action_types = [c.action_type for c in candidates]
        assert_true("wait" in action_types, f"wait_present_side{side_length}")

    print("  wait present for side_length=3,4,5 ✓")


def run_smoke_suite() -> None:
    print("=" * 72)
    print("utility_tunneler smoke suite")
    print("=" * 72)

    tests = [
        test_candidates_generated,
        test_no_illegal_candidates_when_broke,
        test_scores_in_range,
        test_opportunity_cost_blocks_tunnel,
        test_tunnel_raid_preferred_when_valuable,
        test_bot_dispatch,
        test_wait_always_present,
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
