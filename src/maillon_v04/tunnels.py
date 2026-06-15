from __future__ import annotations

from collections import deque

from src.maillon_v04.board import Coord
from src.maillon_v04.state import ActorId, GameState, TunnelEdge
from src.maillon_v04.tunnel_config import (
    DEFAULT_COLLAPSE_THRESHOLD,
    DEFAULT_TUNNEL_RAID_KORN,
)


TUNNEL_RAID_KORN_COST = DEFAULT_TUNNEL_RAID_KORN
COLLAPSE_THRESHOLD = DEFAULT_COLLAPSE_THRESHOLD


def normalize_tunnel_edge(a: Coord, b: Coord) -> TunnelEdge:
    """
    Return a deterministic undirected tunnel edge.

    Tunnel edges are physical graph connections, not owned resources.
    The normalized tuple makes set membership stable and prevents duplicate
    a-b / b-a edges.
    """

    if a == b:
        raise ValueError("tunnel edge requires two distinct coordinates")

    return (a, b) if a <= b else (b, a)


def validate_tunnel_edge(state: GameState, a: Coord, b: Coord) -> TunnelEdge:
    if not state.board.contains(a):
        raise ValueError(f"tunnel edge start is not on board: {a}")

    if not state.board.contains(b):
        raise ValueError(f"tunnel edge end is not on board: {b}")

    if b not in state.board.neighbors(a):
        raise ValueError(f"tunnel edge coordinates are not adjacent: {a} -> {b}")

    return normalize_tunnel_edge(a, b)


def has_tunnel_edge(state: GameState, a: Coord, b: Coord) -> bool:
    return normalize_tunnel_edge(a, b) in state.tunnel_edges


def add_tunnel_edge(state: GameState, a: Coord, b: Coord) -> TunnelEdge:
    edge = validate_tunnel_edge(state, a, b)
    state.tunnel_edges.add(edge)
    return edge


def remove_tunnel_edge(state: GameState, a: Coord, b: Coord) -> None:
    state.tunnel_edges.discard(normalize_tunnel_edge(a, b))


def incident_tunnel_edges(state: GameState, coord: Coord) -> set[TunnelEdge]:
    if not state.board.contains(coord):
        raise ValueError(f"coord is not on board: {coord}")

    return {
        edge
        for edge in state.tunnel_edges
        if coord in edge
    }


def tunnel_pressure(state: GameState, coord: Coord) -> int:
    """
    v0.6.2 pressure definition.

    Pressure is:
    - number of tunnel edges incident to coord
    - plus 1 if the field has a tunnel entrance

    A tunnel entrance is always also an underground intrusion.
    Therefore T implies U.
    Ownership does not matter for pressure.
    """

    pressure = len(incident_tunnel_edges(state, coord))

    if state.cell(coord).has_tunnel_entrance:
        pressure += 1

    return pressure


def is_under_tunnel(state: GameState, coord: Coord) -> bool:
    return tunnel_pressure(state, coord) > 0


def tunnel_neighbors(state: GameState, coord: Coord) -> tuple[Coord, ...]:
    neighbors: list[Coord] = []

    for a, b in incident_tunnel_edges(state, coord):
        neighbors.append(b if a == coord else a)

    return tuple(sorted(neighbors))


def remove_incident_tunnel_edges(state: GameState, coord: Coord) -> int:
    edges = incident_tunnel_edges(state, coord)

    for edge in edges:
        state.tunnel_edges.discard(edge)

    return len(edges)


def tunnel_nodes(state: GameState) -> set[Coord]:
    nodes: set[Coord] = set()

    for a, b in state.tunnel_edges:
        nodes.add(a)
        nodes.add(b)

    return nodes


def tunnel_components(state: GameState) -> list[set[Coord]]:
    remaining = tunnel_nodes(state)
    components: list[set[Coord]] = []

    while remaining:
        start = min(remaining)
        queue: deque[Coord] = deque([start])
        component: set[Coord] = set()

        while queue:
            coord = queue.popleft()
            if coord in component:
                continue

            component.add(coord)
            remaining.discard(coord)

            for neighbor in tunnel_neighbors(state, coord):
                if neighbor not in component:
                    queue.append(neighbor)

        components.append(component)

    return components


def actor_tunnel_entrances(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Active owned entrance fields.

    An entrance is a valid reachable tunnel node even before the first tunnel
    edge is built from it. This is required so tunnel_extend can start a fresh
    network from an isolated entrance.
    """

    return sorted(
        coord
        for coord in state.active_owned_cells(actor)
        if state.cell(coord).has_tunnel_entrance
        and not state.cell(coord).collapsed
    )


def actor_tunnel_corridor(state: GameState, actor: ActorId) -> set[Coord]:
    """
    Own non-collapsed cells reachable via tunnel edges from active own entrances.

    Starting points: own, active, non-collapsed entrance fields.
    Traversal: follows tunnel edges through own non-collapsed cells only.
    Inactive own cells may be in the corridor but cannot be action sources.
    Enemy and neutral cells are never included even if an edge leads to them.
    """

    starts = [
        coord for coord in actor_tunnel_entrances(state, actor)
        if state.is_active(coord) and not state.cell(coord).collapsed
    ]
    if not starts:
        return set()

    reachable: set[Coord] = set()
    queue: deque[Coord] = deque(starts)

    while queue:
        coord = queue.popleft()
        if coord in reachable:
            continue
        if state.cell(coord).collapsed:
            continue
        if state.cell(coord).owner != actor:
            continue
        reachable.add(coord)
        for neighbor in tunnel_neighbors(state, coord):
            if neighbor not in reachable:
                queue.append(neighbor)

    return reachable


def tunnel_access_nodes(state: GameState, actor: ActorId) -> set[Coord]:
    """Alias for actor_tunnel_corridor()."""
    return actor_tunnel_corridor(state, actor)


def reachable_tunnel_nodes(state: GameState, actor: ActorId) -> set[Coord]:
    """Alias for actor_tunnel_corridor()."""
    return actor_tunnel_corridor(state, actor)
