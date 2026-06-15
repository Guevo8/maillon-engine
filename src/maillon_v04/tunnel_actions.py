from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.maillon_v04.board import Coord
from src.maillon_v04.state import ActorId, GameState
from src.maillon_v04.rules import can_pay, pay_resources, winner_by_territory
from src.maillon_v04.tunnel_collapse import check_collapses
from src.maillon_v04.tunnel_rules import (
    owned_tunnel_entrance_count,
    repair_build_cost,
    tunnel_entrance_capacity,
    tunnel_entrance_cost,
    tunnel_extend_cost,
    tunnel_raid_cost,
)
from src.maillon_v04.tunnels import (
    actor_tunnel_corridor,
    add_tunnel_edge,
    has_tunnel_edge,
    tunnel_access_nodes,
)


TunnelActionType = Literal[
    "tunnel_entrance",
    "tunnel_extend",
    "tunnel_raid",
    "repair_build",
]
BuildFieldType = Literal["Holz", "Stein", "Korn"]


@dataclass(frozen=True)
class TunnelAction:
    actor: ActorId
    action_type: TunnelActionType
    target: Coord | None = None
    source: Coord | None = None
    field_type: BuildFieldType | None = None


@dataclass(frozen=True)
class TunnelActionResult:
    ok: bool
    action: TunnelAction
    message: str
    winner: ActorId | None = None
    collapsed: tuple[Coord, ...] = ()


def validate_field_type_for_repair_build(field_type: BuildFieldType | None) -> BuildFieldType:
    if field_type not in {"Holz", "Stein", "Korn"}:
        raise ValueError("field_type must be one of: Holz, Stein, Korn")

    return field_type


def tunnel_entrance_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Owned active non-core, non-collapsed fields without a tunnel entrance.

    A tunnel entrance is a visible surface feature and also counts as
    underground intrusion / pressure. Core fields are excluded to avoid
    early special-case rules around core access and core stability.
    """

    if owned_tunnel_entrance_count(state, actor) >= tunnel_entrance_capacity(state, actor):
        return []

    targets: list[Coord] = []

    for coord in state.active_owned_cells(actor):
        cell = state.cell(coord)

        if cell.collapsed:
            continue

        if cell.is_core:
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

    v0.6.2 rule:
    - source must be an actor-reachable tunnel access node
    - source must not be collapsed, neutral or core
    - target must be adjacent by hex side, not corner
    - target must not be collapsed
    - target must not be neutral
    - target must not be core
    - edge must not already exist

    This keeps tunnel play as a conflict layer on occupied surface fields,
    not a second expansion layer through empty neutral land.
    """

    corridor = actor_tunnel_corridor(state, actor)

    if source not in corridor:
        return []

    source_cell = state.cell(source)

    if not state.is_active(source):
        return []

    if source_cell.owner != actor:
        return []

    if source_cell.is_core:
        return []

    targets: list[Coord] = []

    for target in state.board.neighbors(source):
        target_cell = state.cell(target)

        if target_cell.collapsed:
            continue

        if target_cell.owner != actor:
            continue

        if target_cell.is_core:
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

    for source in sorted(actor_tunnel_corridor(state, actor)):
        if not state.is_active(source):
            continue
        for target in tunnel_extend_targets_from(state, actor, source):
            pairs.append((source, target))

    return pairs


def affordable_tunnel_extend_targets(state: GameState, actor: ActorId) -> list[tuple[Coord, Coord]]:
    costs = tunnel_extend_cost(state, actor)

    if not can_pay(state, actor, costs):
        return []

    return tunnel_extend_targets(state, actor)


def tunnel_raid_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Backward-compatible target view derived from the canonical raid pairs.

    A tunnel raid is always an explicit (source, target) action. This helper
    projects the legal pairs onto their unique target coordinates; a target
    reachable from more than one source appears once.
    """

    return sorted({target for _, target in tunnel_raid_pairs(state, actor)})


def affordable_tunnel_raid_targets(state: GameState, actor: ActorId) -> list[Coord]:
    return sorted({target for _, target in affordable_tunnel_raid_pairs(state, actor)})


def tunnel_raid_targets_from(
    state: GameState,
    actor: ActorId,
    source: Coord,
) -> list[Coord]:
    """
    Adjacent enemy raid targets for a single source, with full source contract.

    The source must itself be a legal raid origin: in the actor's tunnel
    corridor, owned by the actor, active, not collapsed and not a core. If any
    of these fail the function returns [] so callers cannot raid from an
    illegal source. Targets must be directly hex-adjacent, enemy-owned,
    non-collapsed and non-core.
    """
    source_cell = state.cell(source)

    if source not in actor_tunnel_corridor(state, actor):
        return []
    if source_cell.owner != actor:
        return []
    if not state.is_active(source):
        return []
    if source_cell.collapsed:
        return []
    if source_cell.is_core:
        return []

    enemy = state.opponent(actor)
    targets = []
    for neighbor in state.board.neighbors(source):
        cell = state.cell(neighbor)
        if cell.owner != enemy:
            continue
        if cell.collapsed:
            continue
        if cell.is_core:
            continue
        targets.append(neighbor)
    return sorted(targets)


def tunnel_raid_pairs(state: GameState, actor: ActorId) -> list[tuple[Coord, Coord]]:
    pairs = []
    for source in sorted(actor_tunnel_corridor(state, actor)):
        for target in tunnel_raid_targets_from(state, actor, source):
            pairs.append((source, target))
    return pairs


def affordable_tunnel_raid_pairs(
    state: GameState,
    actor: ActorId,
) -> list[tuple[Coord, Coord]]:
    if not can_pay(state, actor, tunnel_raid_cost(state, actor)):
        return []
    return tunnel_raid_pairs(state, actor)


def repair_build_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Collapsed fields adjacent to at least one active owned non-collapsed field.

    repair_build is a special build-like action for broken coordinates. It is
    not normal build on neutral land.
    """

    targets: set[Coord] = set()

    for origin in state.active_owned_cells(actor):
        if state.cell(origin).collapsed:
            continue

        for target in state.board.neighbors(origin):
            if state.cell(target).collapsed:
                targets.add(target)

    return sorted(targets)


def affordable_repair_build_targets(state: GameState, actor: ActorId) -> list[Coord]:
    costs = repair_build_cost(state, actor)

    if not can_pay(state, actor, costs):
        return []

    return repair_build_targets(state, actor)


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


def apply_tunnel_raid(state: GameState, action: TunnelAction) -> TunnelActionResult:
    actor = action.actor
    source = action.source
    target = action.target

    if action.action_type != "tunnel_raid":
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
            message="tunnel_raid requires source and target.",
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

    if (source, target) not in tunnel_raid_pairs(state, actor):
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"invalid tunnel_raid pair: source={source}, target={target}",
            winner=winner_by_territory(state),
        )

    costs = tunnel_raid_cost(state, actor)

    if not can_pay(state, actor, costs):
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"not enough resources for tunnel_raid. need={costs}",
            winner=winner_by_territory(state),
        )

    pay_resources(state, actor, costs)

    cell = state.cell(target)
    old_shield = cell.raid_shield
    cell.owner = actor
    cell.raid_shield = 0
    cell.contested_count += 1
    cell.has_tunnel_entrance = False

    cooldown = min(3, cell.contested_count)
    cell.active_from_round = state.round_index + cooldown

    if not has_tunnel_edge(state, source, target):
        add_tunnel_edge(state, source, target)

    # A raid edge is a physical tunnel edge and changes pressure, so it must
    # trigger the same collapse check as tunnel_extend. Winner is evaluated
    # after collapses so a self-collapse cannot be masked by a stale board.
    collapsed = tuple(check_collapses(state))

    return TunnelActionResult(
        ok=True,
        action=action,
        message=(
            f"{actor} tunnel-raids {source}->{target} for {costs}. "
            f"shield bypassed from {old_shield} to 0, "
            f"contested={cell.contested_count}, active_from_round={cell.active_from_round}. "
            f"collapsed={collapsed}."
        ),
        winner=winner_by_territory(state),
        collapsed=collapsed,
    )


def apply_repair_build(state: GameState, action: TunnelAction) -> TunnelActionResult:
    actor = action.actor
    target = action.target

    if action.action_type != "repair_build":
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
            message="repair_build requires a target.",
            winner=winner_by_territory(state),
        )

    if target not in state.cells:
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"target is not on board: {target}",
            winner=winner_by_territory(state),
        )

    field_type = validate_field_type_for_repair_build(action.field_type)

    if target not in repair_build_targets(state, actor):
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"invalid repair_build target: {target}",
            winner=winner_by_territory(state),
        )

    costs = repair_build_cost(state, actor)

    if not can_pay(state, actor, costs):
        return TunnelActionResult(
            ok=False,
            action=action,
            message=f"not enough resources for repair_build. need={costs}",
            winner=winner_by_territory(state),
        )

    pay_resources(state, actor, costs)

    cell = state.cell(target)
    cell.collapsed = False
    cell.owner = actor
    cell.field_type = field_type
    cell.level = 1
    cell.raid_shield = 0
    cell.has_tunnel_entrance = False
    cell.contested_count = 0
    cell.active_from_round = state.round_index + 1

    return TunnelActionResult(
        ok=True,
        action=action,
        message=(
            f"{actor} repair-builds {field_type} at {target} for {costs}. "
            f"active_from_round={cell.active_from_round}."
        ),
        winner=winner_by_territory(state),
    )


def apply_tunnel_action(state: GameState, action: TunnelAction) -> TunnelActionResult:
    if action.action_type == "tunnel_entrance":
        return apply_tunnel_entrance(state, action)

    if action.action_type == "tunnel_extend":
        return apply_tunnel_extend(state, action)

    if action.action_type == "tunnel_raid":
        return apply_tunnel_raid(state, action)

    if action.action_type == "repair_build":
        return apply_repair_build(state, action)

    return TunnelActionResult(
        ok=False,
        action=action,
        message=f"unknown tunnel action type: {action.action_type}",
        winner=winner_by_territory(state),
    )
