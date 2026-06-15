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
    fortify_cost_korn,
    MAX_RAID_SHIELD,
    pay_resources,
    raid_cost_korn,
    rebuild_cost_holz,
    winner_by_territory,
)
from src.maillon_v04.tunnel_actions import (
    TunnelAction,
    affordable_repair_build_targets as affordable_tunnel_repair_build_targets,
    affordable_tunnel_entrance_targets,
    affordable_tunnel_extend_targets,
    affordable_tunnel_raid_pairs,
    affordable_tunnel_raid_targets,
    apply_tunnel_action as apply_isolated_tunnel_action,
    repair_build_targets as tunnel_repair_build_targets,
    tunnel_entrance_targets,
    tunnel_extend_targets,
    tunnel_raid_pairs,
    tunnel_raid_targets,
)


ActionType = Literal[
    "build",
    "raid",
    "rebuild",
    "field_upgrade",
    "core_upgrade",
    "fortify",
    "tunnel_entrance",
    "tunnel_extend",
    "tunnel_raid",
    "repair_build",
    "wait",
]

BuildFieldType = Literal["Holz", "Stein", "Korn"]
TUNNEL_ACTION_TYPES = {
    "tunnel_entrance",
    "tunnel_extend",
    "tunnel_raid",
    "repair_build",
}


@dataclass(frozen=True)
class Action:
    actor: ActorId
    action_type: ActionType
    target: Coord | None = None
    field_type: BuildFieldType | None = None
    source: Coord | None = None


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    action: Action
    message: str
    winner: ActorId | None = None
    collapsed: tuple[Coord, ...] = ()


def build_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Neutrale Nachbarfelder eigener aktiver Felder.
    """

    targets: set[Coord] = set()

    for origin in state.active_owned_cells(actor):
        for neighbor in state.board.neighbors(origin):
            cell = state.cell(neighbor)

            if cell.owner is None and not cell.collapsed:
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

            if cell.collapsed:
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

        if cell.collapsed:
            continue

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

        if cell.collapsed:
            continue

        if cell.is_core:
            continue

        if cell.field_type in {"Holz", "Stein", "Korn"} and cell.level < 2:
            targets.append(coord)

    return sorted(targets)


def fortify_targets(state: GameState, actor: ActorId) -> list[Coord]:
    """
    Eigene aktive Nicht-Core-Felder mit Raid-Schutz < MAX_RAID_SHIELD.
    """

    targets: list[Coord] = []

    for coord in state.active_owned_cells(actor):
        cell = state.cell(coord)

        if cell.collapsed:
            continue

        if cell.is_core:
            continue

        if cell.field_type in {"Holz", "Stein", "Korn"} and cell.raid_shield < MAX_RAID_SHIELD:
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

    if cell.collapsed:
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


def affordable_fortify_targets(state: GameState, actor: ActorId) -> list[Coord]:
    result: list[Coord] = []

    for target in fortify_targets(state, actor):
        cost = fortify_cost_korn(state, actor, target)

        if can_pay(state, actor, {"Korn": cost}):
            result.append(target)

    return result


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
        "fortify_targets": len(fortify_targets(state, actor)),
        "affordable_fortify_targets": len(affordable_fortify_targets(state, actor)),
        "tunnel_entrance_targets": len(tunnel_entrance_targets(state, actor)),
        "affordable_tunnel_entrance_targets": len(affordable_tunnel_entrance_targets(state, actor)),
        "tunnel_extend_targets": len(tunnel_extend_targets(state, actor)),
        "affordable_tunnel_extend_targets": len(affordable_tunnel_extend_targets(state, actor)),
        "tunnel_raid_targets": len(tunnel_raid_targets(state, actor)),
        "affordable_tunnel_raid_targets": len(affordable_tunnel_raid_targets(state, actor)),
        "repair_build_targets": len(tunnel_repair_build_targets(state, actor)),
        "affordable_repair_build_targets": len(affordable_tunnel_repair_build_targets(state, actor)),
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

    if action.action_type in TUNNEL_ACTION_TYPES:
        return apply_tunnel_action_from_main(state, action)

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

    if action.action_type == "fortify":
        return apply_fortify(state, action)

    return ActionResult(
        ok=False,
        action=action,
        message=f"unknown action type: {action.action_type}",
        winner=winner_by_territory(state),
    )


def apply_tunnel_action_from_main(state: GameState, action: Action) -> ActionResult:
    tunnel_action = TunnelAction(
        actor=action.actor,
        action_type=action.action_type,  # type: ignore[arg-type]
        target=action.target,
        source=action.source,
        field_type=action.field_type,
    )
    result = apply_isolated_tunnel_action(state, tunnel_action)

    return ActionResult(
        ok=result.ok,
        action=action,
        message=result.message,
        winner=result.winner,
        collapsed=result.collapsed,
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


def adjacent_attacker_field_count(
    state: GameState,
    actor: ActorId,
    target: Coord,
) -> int:
    """
    Anzahl aktiver eigener Felder, die an das Raid-Ziel angrenzen.

    Diese Zahl wird für den Fortify-Breaker genutzt.
    Nur aktive Felder zählen als echte Angriffsanker.
    """

    count = 0

    for neighbor in state.board.neighbors(target):
        cell = state.cell(neighbor)

        if cell.owner != actor:
            continue

        if cell.collapsed:
            continue

        if not state.is_active(neighbor):
            continue

        count += 1

    return count


def raid_shield_damage_by_adjacent_attackers(adjacent_attackers: int) -> int:
    """
    Fortify-Breaker v0.5 experiment:

    1 angrenzendes Angreiferfeld  -> 1 Shield Damage
    2 angrenzende Angreiferfelder -> 1 Shield Damage
    3 angrenzende Angreiferfelder -> 2 Shield Damage
    4+ angrenzende Angreiferfelder -> 3 Shield Damage
    """

    if adjacent_attackers >= 4:
        return 3

    if adjacent_attackers >= 3:
        return 2

    return 1


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

    if cell.raid_shield > 0:
        adjacent_attackers = adjacent_attacker_field_count(state, actor, target)
        shield_damage = raid_shield_damage_by_adjacent_attackers(adjacent_attackers)
        old_shield = cell.raid_shield

        cell.raid_shield = max(0, cell.raid_shield - shield_damage)
        cell.contested_count += 1

        cooldown = min(3, cell.contested_count)
        cell.active_from_round = state.round_index + cooldown

        return ActionResult(
            ok=True,
            action=action,
            message=(
                f"{actor} raids {target} for {cost} Korn. "
                f"raid_shield reduced from {old_shield} to {cell.raid_shield} "
                f"by shield_damage={shield_damage} "
                f"(adjacent_attackers={adjacent_attackers}), "
                f"contested={cell.contested_count}, active_from_round={cell.active_from_round}. "
                "No takeover."
            ),
            winner=winner_by_territory(state),
        )

    cell.owner = actor
    cell.raid_shield = 0
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


def apply_fortify(state: GameState, action: Action) -> ActionResult:
    actor = action.actor
    target = action.target
    assert target is not None

    if target not in fortify_targets(state, actor):
        return ActionResult(
            ok=False,
            action=action,
            message=f"invalid fortify target: {target}",
            winner=winner_by_territory(state),
        )

    cost = fortify_cost_korn(state, actor, target)

    if not can_pay(state, actor, {"Korn": cost}):
        return ActionResult(
            ok=False,
            action=action,
            message=f"not enough Korn for fortify. need={cost}",
            winner=winner_by_territory(state),
        )

    pay_resources(state, actor, {"Korn": cost})

    cell = state.cell(target)
    cell.raid_shield += 1

    return ActionResult(
        ok=True,
        action=action,
        message=(
            f"{actor} fortifies {target} for {cost} Korn. "
            f"raid_shield={cell.raid_shield}/{MAX_RAID_SHIELD}."
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
