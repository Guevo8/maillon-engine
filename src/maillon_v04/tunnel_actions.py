from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.maillon_v04.board import Coord
from src.maillon_v04.state import ActorId, GameState
from src.maillon_v04.rules import can_pay, pay_resources, winner_by_territory
from src.maillon_v04.tunnel_collapse import check_collapses
from src.maillon_v04.tunnel_rules import tunnel_entrance_cost, tunnel_extend_cost
from src.maillon_v04.tunnels import add_tunnel_edge, has_tunnel_edge, tunnel_access_nodes


TunnelActionType = Literal["tunnel_entrance", "tunnel_extend"]


@dataclass(frozen=True)
class TunnelAction:
    actor: ActorId
    action_type: TunnelActionType
    target: Coord | None = None
    source: Coord | None = None


@dataclass(frozen=True)
class TunnelActionResult:
    ok: bool
    action: TunnelAction
    message: str
    winner: ActorId | None = None
    collapsed: tuple[Coord, ...] = ()


def tunnel_entrance_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Owned active non-collapsed fields without a tunnel entrance.

    A tunnel entrance is a visible surface feature. It does not create a tunnel
    edge by itself; tunnel_extend uses this access point.
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


def tunnel_extend_targets_from(
    state: GameState,
    actor: ActorId,
    source: Coord,
) -> list[Coord]:
    """
    Adjacent target coordinates reachable from one tunnel access node.

    The source must be an actor-reachable tunnel access node. The target may be
    owned, neutral or enemy, but source and target must not be collapsed and the
    edge must not already exist.
    """

    if source not in tunnel_access_nodes(state, actor):
        return []

    if state.cell(source).collapsed:
        return []

    targets: list[Coord] = []

    for target in state.board.neighbors(source):
        if state.cell(target).collapsed:
            continue

        if has_tunnel_edge(state, source, target):
            continue

        targets.append(target)

    return sorted(targets)


def tunnel_extend_targets(state: GameState, actor: ActorId) -> list[tuple[Coord, Coord]]:
    """
    Return all legal (source, target) tunnel extension pairs.
    """

    pairs: list[tuple[Coord, Coord]] = []

    for source in sorted(tunnel_access_nodes(state, actor)):
        for target in tunnel_extend_targets_from(state, actor, source):
            pairs.append((source, target))

    return pairs


def affordable_tunnel_extend_targets(state: GameState, actor: ActorId) -> list[tuple[Coord, Coord]]:
    costs = tunnel_extend_cost(state, actor)

    if not can_pay(state, actor, costs):
        return []

    return tunnel_extend_targets(state, actor)


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


def apply_tunnel_extend(state: GameState, action: TunnelAction) -> TunnelActionResult:
    actor = action.actor
    source = action.source
    target = action.target

    if action.action_type != "tunnel_extend":
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"unknown tunnel action type: {action.action_type}",
            winner=winner_by_territory(state),
        )

    if source is None or target is None:
        return TunnelActionResult(
            ok=False,
            action=action,
            message="tunnel_extend requires source and target.",
            winner=winner_by_territory(state),
        )

    if source not in state.cells:
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"source is not on board: {source}",
            winner=winner_by_territory(state),
        )

    if target not in state.cells:
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"target is not on board: {target}",
            winner=winner_by_territory(state),
        )

    if target not in tunnel_extend_targets_from(state, actor, source):
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"invalid tunnel_extend target: source={source}, target={target}",
            winner=winner_by_territory(state),
        )

    costs = tunnel_extend_cost(state, actor)

    if not can_pay(state, actor, costs):
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"not enough resources for tunnel_extend. need={costs}",
            winner=winner_by_territory(state),
        )

    pay_resources(state, actor, costs)
    add_tunnel_edge(state, source, target)
    collapsed = tuple(check_collapses(state))

    return TunnelActionResult(
        ok=True,
        action=action,
        message=(
            f"{actor} extends tunnel {source}->{target} for {costs}. "
            f"collapsed={collapsed}."
        ),
        winner=winner_by_territory(state),
        collapsed=collapsed,
    )


def apply_tunnel_action(state: GameState, action: TunnelAction) -> TunnelActionResult:
    if action.action_type == "tunnel_entrance":
        return apply_tunnel_entrance(state, action)

    if action.action_type == "tunnel_extend":
        return apply_tunnel_extend(state, action)

    return TunnelActionResult(
        ok=False,
        action=action,
        message=f"unknown tunnel action type: {action.action_type}",
        winner=winner_by_territory(state),
    )
