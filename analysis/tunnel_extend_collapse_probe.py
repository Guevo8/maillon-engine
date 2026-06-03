from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.maillon_v04.state import CellState, create_initial_state
from src.maillon_v04.tunnel_actions import TunnelAction, apply_tunnel_action
from src.maillon_v04.tunnels import tunnel_access_nodes, tunnel_pressure


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def run_probe() -> None:
    state = create_initial_state(4)
    actor = "player"
    center = (0, 0)

    # Probe setup: create an active owned center field so the action pipeline can
    # build a tunnel entrance and then extend four incident tunnel edges from it.
    state.cells[center] = CellState(
        owner=actor,
        field_type="Holz",
        level=1,
        active_from_round=1,
    )
    state.actor_state(actor).resources["Holz"] = 10
    state.actor_state(actor).resources["Stein"] = 10
    state.actor_state(actor).resources["Korn"] = 10

    print("TUNNEL EXTEND COLLAPSE PROBE")
    print("=" * 72)
    print(f"center: {center}")
    print(f"neighbors: {state.board.neighbors(center)}")
    print()

    entrance_result = apply_tunnel_action(
        state,
        TunnelAction(
            actor=actor,
            action_type="tunnel_entrance",
            target=center,
        ),
    )
    print("entrance:", entrance_result)
    assert_equal(entrance_result.ok, True, "entrance ok")
    assert_equal(state.cell(center).has_tunnel_entrance, True, "center entrance")

    neighbors = state.board.neighbors(center)[:4]

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
        print(f"extend {index}:", result)
        print(
            f"  pressure center={tunnel_pressure(state, center)} | "
            f"collapsed={state.cell(center).collapsed} | "
            f"edges={sorted(state.tunnel_edges)} | "
            f"access={sorted(tunnel_access_nodes(state, actor))}"
        )

        assert_equal(result.ok, True, f"extend {index} ok")

        if index < 4:
            assert_equal(result.collapsed, (), f"extend {index} collapsed")
            assert_equal(state.cell(center).collapsed, False, f"center not collapsed after extend {index}")
            assert_equal(tunnel_pressure(state, center), index, f"pressure after extend {index}")
        else:
            assert_equal(result.collapsed, (center,), "extend 4 collapsed")
            assert_equal(state.cell(center).collapsed, True, "center collapsed after extend 4")
            assert_equal(state.cell(center).owner, None, "collapsed owner")
            assert_equal(state.cell(center).field_type, None, "collapsed field_type")
            assert_equal(state.cell(center).level, 0, "collapsed level")
            assert_equal(state.cell(center).raid_shield, 0, "collapsed shield")
            assert_equal(state.cell(center).has_tunnel_entrance, False, "collapsed entrance")
            assert_equal(len(state.tunnel_edges), 0, "incident edges removed")
            assert_equal(tunnel_pressure(state, center), 0, "pressure after collapse")

    print()
    print("RESULT: tunnel_extend collapse probe OK")


if __name__ == "__main__":
    run_probe()
