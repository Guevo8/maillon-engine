from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.maillon_v04.board import Coord
from src.maillon_v04.state import ActorId, GameState
from src.maillon_v04.rules import can_pay, pay_resources, winner_by_territory
from src.maillon_v04.tunnel_rules import tunnel_entrance_cost


TunnelActionType = Literal["tunnel_entrance"]


@dataclass(frozen=True)
class TunnelAction:
    actor: ActorId
    action_type: TunnelActionType
    target: Coord | None = None


@dataclass(frozen=True)
class TunnelActionResult:
    ok: bool
    action: TunnelAction
    message: str
    winner: ActorId | None = None


def tunnel_entrance_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Owned active non-collapsed fields without a tunnel entrance.

    A tunnel entrance is a visible surface feature. It does not create a tunnel
    edge by itself; tunnel_extend will later use this access point.
    """

    targets: list[Coord] = []

    for coord in state.active_owned_cells(actor):
        cell = state.cell(coord)

        if cell.collapsed:
            continue

        if cell.has_tunnel_entrance:
            continue

        targets.append(coord)

    return sorted(targets)


def affordable_tunnel_entrance_targets(state: GameState, actor: ActorId) -> list[Coord]:
    costs = tunnel_entrance_cost(state, actor)

    if not can_pay(state, actor, costs):
        return []

    return tunnel_entrance_targets(state, actor)


def apply_tunnel_entrance(state: GameState, action: TunnelAction) -> TunnelActionResult:
    actor = action.actor
    target = action.target

    if action.action_type != "tunnel_entrance":
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"unknown tunnel action type: {action.action_type}",
            winner=winner_by_territory(state),
        )

    if target is None:
        return TunnelActionResult(
            ok=False,
            action=action,
            message="tunnel_entrance requires a target.",
            winner=winner_by_territory(state),
        )

    if target not in state.cells:
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"target is not on board: {target}",
            winner=winner_by_territory(state),
        )

    if target not in tunnel_entrance_targets(state, actor):
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"invalid tunnel_entrance target: {target}",
            winner=winner_by_territory(state),
        )

    costs = tunnel_entrance_cost(state, actor)

    if not can_pay(state, actor, costs):
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"not enough resources for tunnel_entrance. need={costs}",
            winner=winner_by_territory(state),
        )

    pay_resources(state, actor, costs)
    state.cell(target).has_tunnel_entrance = True

    return TunnelActionResult(
        ok=True,
        action=action,
        message=f"{actor} builds tunnel entrance at {target} for {costs}.",
        winner=winner_by_territory(state),
    )
