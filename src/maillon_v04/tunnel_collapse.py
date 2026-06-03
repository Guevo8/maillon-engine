from __future__ import annotations

from src.maillon_v04.board import Coord
from src.maillon_v04.state import GameState, TunnelEdge
from src.maillon_v04.tunnels import COLLAPSE_THRESHOLD, incident_tunnel_edges, remove_incident_tunnel_edges, tunnel_pressure


def collapse_candidates(
    state: GameState,
    *,
    threshold: int = COLLAPSE_THRESHOLD,
) -> list[Coord]:
    """
    Return all non-collapsed fields at or above collapse threshold.

    This is a snapshot query. check_collapses() first gathers all candidates
    and only then mutates state, so simultaneous collapse does not depend on
    coordinate order.
    """

    return sorted(
        coord
        for coord in state.board.cells
        if not state.cell(coord).collapsed
        and tunnel_pressure(state, coord) >= threshold
    )


def apply_collapsed_field_state(state: GameState, coord: Coord) -> None:
    """
    Set surface state for a collapsed field.

    Collapse makes the coordinate a broken special state, not a normal neutral
    field. Tunnel edges are removed separately so simultaneous collapse can
    collect all affected edges before mutating the graph.
    """

    if not state.board.contains(coord):
        raise ValueError(f"coord is not on board: {coord}")

    cell = state.cell(coord)
    cell.collapsed = True
    cell.owner = None
    cell.field_type = None
    cell.level = 0
    cell.raid_shield = 0
    cell.has_tunnel_entrance = False


def collapse_field(state: GameState, coord: Coord) -> int:
    """
    Collapse one field and remove all incident tunnel edges.

    Use check_collapses() after tunnel-changing actions when simultaneous
    collapse matters. This helper is mainly useful for direct rule tests and
    targeted future effects.
    """

    apply_collapsed_field_state(state, coord)
    return remove_incident_tunnel_edges(state, coord)


def check_collapses(
    state: GameState,
    *,
    threshold: int = COLLAPSE_THRESHOLD,
) -> list[Coord]:
    """
    Apply simultaneous collapse for all fields above threshold.

    Order of operations:
    1. Gather all candidates from the current graph snapshot.
    2. Set all candidate fields to collapsed state.
    3. Remove all tunnel edges incident to any collapsed field.
    """

    candidates = collapse_candidates(state, threshold=threshold)
    if not candidates:
        return []

    edges_to_remove: set[TunnelEdge] = set()

    for coord in candidates:
        edges_to_remove.update(incident_tunnel_edges(state, coord))

    for coord in candidates:
        apply_collapsed_field_state(state, coord)

    for edge in edges_to_remove:
        state.tunnel_edges.discard(edge)

    return candidates
