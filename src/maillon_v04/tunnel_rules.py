from __future__ import annotations

from src.maillon_v04.state import ActorId, GameState, ResourceName


TUNNEL_ENTRANCE_COSTS: dict[ResourceName, int] = {
    "Holz": 1,
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
