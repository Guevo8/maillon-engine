from __future__ import annotations

from collections import deque

from src.maillon_v04.board import Coord
from src.maillon_v04.state import ActorId, GameState, TunnelEdge


TUNNEL_RAID_KORN_COST = 3
COLLAPSE_THRESHOLD = 4


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
    v0.6.1 pressure definition.

    Pressure is the number of active tunnel edges incident to coord.
    Ownership does not matter. A tunnel is a tunnel.
    """

    return len(incident_tunnel_edges(state, coord))


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
    return sorted(
        coord
        for coord in state.active_owned_cells(actor)
        if state.cell(coord).has_tunnel_entrance
        and not state.cell(coord).collapsed
        and is_under_tunnel(state, coord)
    )


def reachable_tunnel_nodes(state: GameState, actor: ActorId) -> set[Coord]:
    """
    Return the tunnel component reachable by actor-owned active entrances.

    Tunnel edges themselves are not owned. Once an actor has an active entrance
    into a connected component, all non-collapsed nodes in that component are
    reachable.
    """

    starts = actor_tunnel_entrances(state, actor)
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

        reachable.add(coord)

        for neighbor in tunnel_neighbors(state, coord):
            if state.cell(neighbor).collapsed:
                continue

            if neighbor not in reachable:
                queue.append(neighbor)

    return reachable
