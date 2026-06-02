from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.maillon_v04.board import Coord
from src.maillon_v04.state import ActorId, FieldType, GameState, ResourceName
from src.maillon_v04.rules import (
    apply_core_level_2_caps,
    build_cost_holz,
    can_pay,
    core_upgrade_cost_stein,
    field_upgrade_cost_stein,
    pay_resources,
    raid_cost_korn,
    rebuild_cost_holz,
    winner_by_territory,
)


ActionType = Literal[
    "build",
    "raid",
    "rebuild",
    "field_upgrade",
    "core_upgrade",
    "wait",
]

BuildFieldType = Literal["Holz", "Stein", "Korn"]


@dataclass(frozen=True)
class Action:
    actor: ActorId
    action_type: ActionType
    target: Coord | None = None
    field_type: BuildFieldType | None = None


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    action: Action
    message: str
    winner: ActorId | None = None


def build_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Neutrale Nachbarfelder eigener aktiver Felder.
    """

    targets: set[Coord] = set()

    for origin in state.active_owned_cells(actor):
        for neighbor in state.board.neighbors(origin):
            if state.cell(neighbor).owner is None:
                targets.add(neighbor)

    return sorted(targets)


def raid_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Aktive gegnerische Nicht-Core-Felder neben eigenen aktiven Feldern.
    """

    enemy = state.opponent(actor)
    targets: set[Coord] = set()

    for origin in state.active_owned_cells(actor):
        for neighbor in state.board.neighbors(origin):
            cell = state.cell(neighbor)

            if cell.owner != enemy:
                continue

            if cell.is_core:
                continue

            if not state.is_active(neighbor):
                continue

            targets.add(neighbor)

    return sorted(targets)


def rebuild_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Eigene aktive Nicht-Core-Ressourcenfelder.
    """

    targets: list[Coord] = []

    for coord in state.active_owned_cells(actor):
        cell = state.cell(coord)

        if cell.is_core:
            continue

        if cell.field_type in {"Holz", "Stein", "Korn"}:
            targets.append(coord)

    return sorted(targets)


def field_upgrade_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Eigene aktive Nicht-Core-Felder mit Level < 2.
    """

    targets: list[Coord] = []

    for coord in state.active_owned_cells(actor):
        cell = state.cell(coord)

        if cell.is_core:
            continue

        if cell.field_type in {"Holz", "Stein", "Korn"} and cell.level < 2:
            targets.append(coord)

    return sorted(targets)


def core_upgrade_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Eigener aktiver Core mit Level 1.
    v0.4 Baseline: nur Core Level 1 -> 2.
    """

    core = state.player_core if actor == "player" else state.enemy_core
    cell = state.cell(core)

    if cell.owner != actor:
        return []

    if not cell.is_core:
        return []

    if not state.is_active(core):
        return []

    if cell.level >= 2:
        return []

    return [core]


def affordable_build_targets(state: GameState, actor: ActorId) -> list[Coord]:
    if not can_pay(state, actor, {"Holz": build_cost_holz(state, actor)}):
        return []

    return build_targets(state, actor)


def affordable_raid_targets(state: GameState, actor: ActorId) -> list[Coord]:
    result: list[Coord] = []

    for target in raid_targets(state, actor):
        cost = raid_cost_korn(state, actor, target)

        if can_pay(state, actor, {"Korn": cost}):
            result.append(target)

    return result


def affordable_rebuild_targets(state: GameState, actor: ActorId) -> list[Coord]:
    if not can_pay(state, actor, {"Holz": rebuild_cost_holz(state, actor)}):
        return []

    return rebuild_targets(state, actor)


def affordable_field_upgrade_targets(state: GameState, actor: ActorId) -> list[Coord]:
    if not can_pay(state, actor, {"Stein": field_upgrade_cost_stein(state, actor)}):
        return []

    return field_upgrade_targets(state, actor)


def affordable_core_upgrade_targets(state: GameState, actor: ActorId) -> list[Coord]:
    if not can_pay(state, actor, {"Stein": core_upgrade_cost_stein(state, actor)}):
        return []

    return core_upgrade_targets(state, actor)


def action_summary(state: GameState, actor: ActorId) -> dict[str, int]:
    """
    Kompakte Zählung für Terminal-Status und Tests.
    """

    return {
        "build_targets": len(build_targets(state, actor)),
        "affordable_build_targets": len(affordable_build_targets(state, actor)),
        "raid_targets": len(raid_targets(state, actor)),
        "affordable_raid_targets": len(affordable_raid_targets(state, actor)),
        "rebuild_targets": len(rebuild_targets(state, actor)),
        "affordable_rebuild_targets": len(affordable_rebuild_targets(state, actor)),
        "field_upgrade_targets": len(field_upgrade_targets(state, actor)),
        "affordable_field_upgrade_targets": len(affordable_field_upgrade_targets(state, actor)),
        "core_upgrade_targets": len(core_upgrade_targets(state, actor)),
        "affordable_core_upgrade_targets": len(affordable_core_upgrade_targets(state, actor)),
    }


def validate_field_type_for_build_or_rebuild(field_type: BuildFieldType | None) -> BuildFieldType:
    if field_type not in {"Holz", "Stein", "Korn"}:
        raise ValueError("field_type must be one of: Holz, Stein, Korn")

    return field_type


def apply_action(state: GameState, action: Action) -> ActionResult:
    """
    Wendet eine Aktion auf den GameState an.

    Diese Funktion ist bewusst deterministisch und ohne User-Input.
    Terminal-Input wird später außerhalb dieser Funktion verarbeitet.
    """

    actor = action.actor

    if action.action_type == "wait":
        return ActionResult(
            ok=True,
            action=action,
            message=f"{actor} waits.",
            winner=winner_by_territory(state),
        )

    if action.target is None:
        return ActionResult(
            ok=False,
            action=action,
            message=f"{action.action_type} requires a target.",
            winner=winner_by_territory(state),
        )

    if action.target not in state.cells:
        return ActionResult(
            ok=False,
            action=action,
            message=f"target is not on board: {action.target}",
            winner=winner_by_territory(state),
        )

    if action.action_type == "build":
        return apply_build(state, action)

    if action.action_type == "raid":
        return apply_raid(state, action)

    if action.action_type == "rebuild":
        return apply_rebuild(state, action)

    if action.action_type == "field_upgrade":
        return apply_field_upgrade(state, action)

    if action.action_type == "core_upgrade":
        return apply_core_upgrade(state, action)

    return ActionResult(
        ok=False,
        action=action,
        message=f"unknown action type: {action.action_type}",
        winner=winner_by_territory(state),
    )


def apply_build(state: GameState, action: Action) -> ActionResult:
    actor = action.actor
    target = action.target
    assert target is not None

    field_type = validate_field_type_for_build_or_rebuild(action.field_type)

    if target not in build_targets(state, actor):
        return ActionResult(
            ok=False,
            action=action,
            message=f"invalid build target: {target}",
            winner=winner_by_territory(state),
        )

    cost = build_cost_holz(state, actor)

    if not can_pay(state, actor, {"Holz": cost}):
        return ActionResult(
            ok=False,
            action=action,
            message=f"not enough Holz for build. need={cost}",
            winner=winner_by_territory(state),
        )

    pay_resources(state, actor, {"Holz": cost})

    cell = state.cell(target)
    cell.owner = actor
    cell.field_type = field_type
    cell.level = 1
    cell.active_from_round = state.round_index + 1
    cell.contested_count = 0

    return ActionResult(
        ok=True,
        action=action,
        message=f"{actor} builds {field_type} at {target} for {cost} Holz.",
        winner=winner_by_territory(state),
    )


def apply_raid(state: GameState, action: Action) -> ActionResult:
    actor = action.actor
    target = action.target
    assert target is not None

    if target not in raid_targets(state, actor):
        return ActionResult(
            ok=False,
            action=action,
            message=f"invalid raid target: {target}",
            winner=winner_by_territory(state),
        )

    cost = raid_cost_korn(state, actor, target)

    if not can_pay(state, actor, {"Korn": cost}):
        return ActionResult(
            ok=False,
            action=action,
            message=f"not enough Korn for raid. need={cost}",
            winner=winner_by_territory(state),
        )

    pay_resources(state, actor, {"Korn": cost})

    cell = state.cell(target)
    cell.owner = actor
    cell.contested_count += 1

    cooldown = min(3, cell.contested_count)
    cell.active_from_round = state.round_index + cooldown

    return ActionResult(
        ok=True,
        action=action,
        message=(
            f"{actor} raids {target} for {cost} Korn. "
            f"contested={cell.contested_count}, active_from_round={cell.active_from_round}."
        ),
        winner=winner_by_territory(state),
    )


def apply_rebuild(state: GameState, action: Action) -> ActionResult:
    actor = action.actor
    target = action.target
    assert target is not None

    field_type = validate_field_type_for_build_or_rebuild(action.field_type)

    if target not in rebuild_targets(state, actor):
        return ActionResult(
            ok=False,
            action=action,
            message=f"invalid rebuild target: {target}",
            winner=winner_by_territory(state),
        )

    cell = state.cell(target)

    if cell.field_type == field_type:
        return ActionResult(
            ok=False,
            action=action,
            message=f"field already has type {field_type}: {target}",
            winner=winner_by_territory(state),
        )

    cost = rebuild_cost_holz(state, actor)

    if not can_pay(state, actor, {"Holz": cost}):
        return ActionResult(
            ok=False,
            action=action,
            message=f"not enough Holz for rebuild. need={cost}",
            winner=winner_by_territory(state),
        )

    old_type = cell.field_type

    pay_resources(state, actor, {"Holz": cost})

    cell.field_type = field_type
    cell.active_from_round = state.round_index + 1

    return ActionResult(
        ok=True,
        action=action,
        message=f"{actor} rebuilds {target}: {old_type} -> {field_type} for {cost} Holz.",
        winner=winner_by_territory(state),
    )


def apply_field_upgrade(state: GameState, action: Action) -> ActionResult:
    actor = action.actor
    target = action.target
    assert target is not None

    if target not in field_upgrade_targets(state, actor):
        return ActionResult(
            ok=False,
            action=action,
            message=f"invalid field upgrade target: {target}",
            winner=winner_by_territory(state),
        )

    cost = field_upgrade_cost_stein(state, actor)

    if not can_pay(state, actor, {"Stein": cost}):
        return ActionResult(
            ok=False,
            action=action,
            message=f"not enough Stein for field upgrade. need={cost}",
            winner=winner_by_territory(state),
        )

    pay_resources(state, actor, {"Stein": cost})

    cell = state.cell(target)
    cell.level = 2

    return ActionResult(
        ok=True,
        action=action,
        message=f"{actor} upgrades {target} to level 2 for {cost} Stein.",
        winner=winner_by_territory(state),
    )


def apply_core_upgrade(state: GameState, action: Action) -> ActionResult:
    actor = action.actor
    target = action.target
    assert target is not None

    if target not in core_upgrade_targets(state, actor):
        return ActionResult(
            ok=False,
            action=action,
            message=f"invalid core upgrade target: {target}",
            winner=winner_by_territory(state),
        )

    cost = core_upgrade_cost_stein(state, actor)

    if not can_pay(state, actor, {"Stein": cost}):
        return ActionResult(
            ok=False,
            action=action,
            message=f"not enough Stein for core upgrade. need={cost}",
            winner=winner_by_territory(state),
        )

    pay_resources(state, actor, {"Stein": cost})

    cell = state.cell(target)
    cell.level = 2
    apply_core_level_2_caps(state, actor)

    return ActionResult(
        ok=True,
        action=action,
        message=f"{actor} upgrades Core to level 2 for {cost} Stein.",
        winner=winner_by_territory(state),
    )
