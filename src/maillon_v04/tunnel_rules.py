from __future__ import annotations

from src.maillon_v04.state import ActorId, GameState, ResourceName
from src.maillon_v04.tunnels import TUNNEL_RAID_KORN_COST


TUNNEL_ENTRANCE_COSTS: dict[ResourceName, int] = {
    "Holz": 1,
    "Stein": 2,
}

TUNNEL_EXTEND_COSTS: dict[ResourceName, int] = {
    "Holz": 1,
    "Stein": 1,
}

REPAIR_BUILD_COSTS: dict[ResourceName, int] = {
    "Holz": 2,
    "Stein": 2,
}


def tunnel_entrance_cost(state: GameState, actor: ActorId) -> dict[ResourceName, int]:
    """
    Cost for building a visible tunnel entrance on an owned active field.

    The parameters are accepted for future scaling / scenario rules.
    """

    _ = state
    _ = actor
    return dict(TUNNEL_ENTRANCE_COSTS)


def tunnel_extend_cost(state: GameState, actor: ActorId) -> dict[ResourceName, int]:
    """
    Cost for extending the underground tunnel graph by one adjacent edge.

    The parameters are accepted for future scaling / scenario rules.
    """

    _ = state
    _ = actor
    return dict(TUNNEL_EXTEND_COSTS)


def tunnel_raid_cost(state: GameState, actor: ActorId) -> dict[ResourceName, int]:
    """
    Cost for a shield-bypassing tunnel raid.

    The parameters are accepted for future scaling / scenario rules.
    """

    _ = state
    _ = actor
    return {"Korn": TUNNEL_RAID_KORN_COST}


def repair_build_cost(state: GameState, actor: ActorId) -> dict[ResourceName, int]:
    """
    Cost for repairing, claiming and rebuilding one collapsed field.

    The parameters are accepted for future scaling / scenario rules.
    """

    _ = state
    _ = actor
    return dict(REPAIR_BUILD_COSTS)
