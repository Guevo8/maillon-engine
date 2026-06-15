from __future__ import annotations

from src.maillon_v04.state import ActorId, GameState, ResourceName
from src.maillon_v04.tunnel_config import (
    DEFAULT_REPAIR_BUILD_HOLZ,
    DEFAULT_REPAIR_BUILD_STEIN,
    DEFAULT_TUNNEL_ENTRANCE_HOLZ,
    DEFAULT_TUNNEL_ENTRANCE_STEIN,
    DEFAULT_TUNNEL_ENTRANCES_CORE_LEVEL_1,
    DEFAULT_TUNNEL_ENTRANCES_CORE_LEVEL_2,
    DEFAULT_TUNNEL_EXTEND_HOLZ,
    DEFAULT_TUNNEL_EXTEND_STEIN,
    DEFAULT_TUNNEL_RAID_HOLZ,
    DEFAULT_TUNNEL_RAID_KORN,
    DEFAULT_TUNNEL_RAID_STEIN,
)


TUNNEL_ENTRANCE_COSTS: dict[ResourceName, int] = {
    "Holz": DEFAULT_TUNNEL_ENTRANCE_HOLZ,
    "Stein": DEFAULT_TUNNEL_ENTRANCE_STEIN,
}

TUNNEL_EXTEND_COSTS: dict[ResourceName, int] = {
    "Holz": DEFAULT_TUNNEL_EXTEND_HOLZ,
    "Stein": DEFAULT_TUNNEL_EXTEND_STEIN,
}

TUNNEL_RAID_COSTS: dict[ResourceName, int] = {
    "Holz": DEFAULT_TUNNEL_RAID_HOLZ,
    "Stein": DEFAULT_TUNNEL_RAID_STEIN,
    "Korn": DEFAULT_TUNNEL_RAID_KORN,
}

REPAIR_BUILD_COSTS: dict[ResourceName, int] = {
    "Holz": DEFAULT_REPAIR_BUILD_HOLZ,
    "Stein": DEFAULT_REPAIR_BUILD_STEIN,
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
    return dict(TUNNEL_RAID_COSTS)


def owned_tunnel_entrance_count(state: GameState, actor: ActorId) -> int:
    """Non-collapsed own fields that have a tunnel entrance."""
    return sum(
        1
        for coord in state.owned_cells(actor)
        if not state.cell(coord).collapsed
        and state.cell(coord).has_tunnel_entrance
    )


def tunnel_entrance_capacity(state: GameState, actor: ActorId) -> int:
    """Maximum tunnel entrances allowed based on core level."""
    core_coord = state.player_core if actor == "player" else state.enemy_core
    if state.cell(core_coord).level >= 2:
        return DEFAULT_TUNNEL_ENTRANCES_CORE_LEVEL_2
    return DEFAULT_TUNNEL_ENTRANCES_CORE_LEVEL_1


def repair_build_cost(state: GameState, actor: ActorId) -> dict[ResourceName, int]:
    """
    Cost for repairing, claiming and rebuilding one collapsed field.

    The parameters are accepted for future scaling / scenario rules.
    """

    _ = state
    _ = actor
    return dict(REPAIR_BUILD_COSTS)
