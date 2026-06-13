from __future__ import annotations

from src.maillon_v04.actions import (
    Action,
    affordable_build_targets,
    affordable_core_upgrade_targets,
    affordable_field_upgrade_targets,
    affordable_fortify_targets,
    affordable_raid_targets,
    affordable_rebuild_targets,
)
from src.maillon_v04.board import Coord
from src.maillon_v04.rules import (
    build_cost_holz,
    field_upgrade_cost_stein,
    raid_cost_korn,
    territory_threshold_60,
)
from src.maillon_v04.state import ActorId, GameState


def actor_core(state: GameState, actor: ActorId) -> Coord:
    return state.player_core if actor == "player" else state.enemy_core


def opponent_core(state: GameState, actor: ActorId) -> Coord:
    return state.enemy_core if actor == "player" else state.player_core


def choose_closest_to_opponent_core(
    state: GameState,
    actor: ActorId,
    options: list[Coord],
) -> Coord:
    target_core = opponent_core(state, actor)

    return min(
        options,
        key=lambda coord: (
            state.board.distance(coord, target_core),
            coord[0],
            coord[1],
        ),
    )


def choose_best_raid_target(
    state: GameState,
    actor: ActorId,
    options: list[Coord],
) -> Coord:
    """
    Deterministische Raid-Auswahl.

    Priorität:
    - günstige Kornkosten
    - höherwertige Feldtypen leicht bevorzugen
    - Nähe zum gegnerischen Core
    """

    field_value = {
        "Core": 100,
        "Stein": 3,
        "Korn": 2,
        "Holz": 1,
        None: 0,
    }

    target_core = opponent_core(state, actor)

    return min(
        options,
        key=lambda coord: (
            raid_cost_korn(state, actor, coord),
            -field_value[state.cell(coord).field_type],
            state.board.distance(coord, target_core),
            coord[0],
            coord[1],
        ),
    )


def choose_expansion_target(
    state: GameState,
    actor: ActorId,
    options: list[Coord],
) -> Coord:
    """
    Baut Richtung Gegner, aber deterministisch.
    """

    return choose_closest_to_opponent_core(state, actor, options)


def resource_pressure(state: GameState, actor: ActorId, resource: str) -> float:
    actor_state = state.actor_state(actor)
    value = actor_state.resources[resource]  # type: ignore[index]
    cap = actor_state.caps[resource]  # type: ignore[index]

    if cap <= 0:
        return 0.0

    return value / cap


def choose_build_field_type_for_phase_player(state: GameState, actor: ActorId) -> str:
    """
    Einfache, erklärbare Feldtypwahl.

    Ziel:
    - Early Game: Holz sichern.
    - Wenn Stein knapp ist: Stein.
    - Wenn Raid möglich/absehbar ist: Korn.
    """

    resources = state.actor_state(actor).resources
    non_core = state.non_core_controlled_count(actor)

    if non_core <= 2:
        return "Holz"

    if resources["Stein"] < 3:
        return "Stein"

    if resources["Korn"] < 4:
        return "Korn"

    # Wenn Holz niedrig ist, wieder Holz nachziehen.
    if resources["Holz"] < build_cost_holz(state, actor):
        return "Holz"

    # Default: Korn, weil v0.4-Konflikt stark über Raid läuft.
    return "Korn"


def choose_build_field_type_for_rusher(state: GameState, actor: ActorId) -> str:
    resources = state.actor_state(actor).resources

    # Rusher braucht Korn für Raid und Holz für Expansion.
    if resources["Korn"] < 4:
        return "Korn"

    if resources["Holz"] < build_cost_holz(state, actor):
        return "Holz"

    return "Korn"


def is_front_field(state: GameState, actor: ActorId, coord: Coord) -> bool:
    opponent = state.opponent(actor)

    for neighbor in state.board.neighbors(coord):
        if state.cell(neighbor).owner == opponent:
            return True

    return False


def choose_fortify_target(
    state: GameState,
    actor: ActorId,
    options: list[Coord],
) -> Coord:
    """
    Konservative Fortify-Auswahl.

    Priorität:
    - umkämpfte Felder zuerst,
    - wichtige Feldtypen leicht bevorzugen,
    - Nähe zum gegnerischen Core,
    - deterministische Koordinatenreihenfolge.
    """

    field_value = {
        "Stein": 3,
        "Korn": 2,
        "Holz": 1,
        None: 0,
    }

    target_core = opponent_core(state, actor)

    return min(
        options,
        key=lambda coord: (
            -state.cell(coord).contested_count,
            -field_value[state.cell(coord).field_type],
            state.board.distance(coord, target_core),
            coord[0],
            coord[1],
        ),
    )


def conservative_fortify_action(state: GameState, actor: ActorId) -> Action | None:
    """
    Minimaler Bot-Fortify-Hebel.

    Der Bot befestigt nur:
    - eigene aktive Frontfelder,
    - mit Schutz 0,
    - wenn Korn-Druck hoch genug ist.

    Dadurch wird Korn-Waste reduziert, ohne dass der Bot sofort jedes Feld
    zu einer Festung ausbaut.
    """

    # Nicht zu früh das gesamte Early Game in Defense verwandeln.
    if state.non_core_controlled_count(actor) < 3:
        return None

    # Genug Korn / Cap-Druck: Fortify darf als Korn-Sink genutzt werden.
    if resource_pressure(state, actor, "Korn") < 0.65:
        return None

    candidates = [
        coord
        for coord in affordable_fortify_targets(state, actor)
        if state.cell(coord).raid_shield == 0
        and is_front_field(state, actor, coord)
    ]

    if not candidates:
        return None

    return Action(
        actor=actor,
        action_type="fortify",
        target=choose_fortify_target(state, actor, candidates),
    )


def choose_rebuild_field_type(state: GameState, actor: ActorId, target: Coord) -> str | None:
    """
    Simpler Rebuild:
    - Wenn Korn knapp: zu Korn.
    - Wenn Stein knapp: zu Stein.
    - Wenn Holz knapp: zu Holz.
    - Nie in denselben Typ umbauen.
    """

    cell = state.cell(target)
    resources = state.actor_state(actor).resources

    desired_order: list[str] = []

    if resources["Korn"] < 4:
        desired_order.append("Korn")

    if resources["Stein"] < field_upgrade_cost_stein(state, actor):
        desired_order.append("Stein")

    if resources["Holz"] < build_cost_holz(state, actor):
        desired_order.append("Holz")

    desired_order.extend(["Korn", "Stein", "Holz"])

    for field_type in desired_order:
        if cell.field_type != field_type:
            return field_type

    return None


def neutral_field_count(state: GameState) -> int:
    return sum(1 for cell in state.cells.values() if cell.owner is None)


def actor_field_type_count(
    state: GameState,
    actor: ActorId,
    field_type: str,
) -> int:
    return sum(
        1
        for cell in state.cells.values()
        if cell.owner == actor
        and not cell.is_core
        and cell.field_type == field_type
    )


def rusher_should_save_for_build(state: GameState, actor: ActorId) -> bool:
    """
    Finish-Fix für den Rusher.

    Wenn noch neutrale Felder offen sind und der Rusher Holzproduktion hat,
    soll er Holz nicht durch Rebuild-Oszillation verbrennen, sondern auf
    den nächsten Build sparen.
    """

    if neutral_field_count(state) <= 0:
        return False

    resources = state.actor_state(actor).resources
    build_cost = build_cost_holz(state, actor)

    if resources["Holz"] >= build_cost:
        return False

    # Wenn gar keine Holzproduktion mehr existiert, darf Rebuild als Notfall
    # wieder sinnvoll sein. Sonst lieber sparen.
    if actor_field_type_count(state, actor, "Holz") <= 0:
        return False

    return True


def rusher_finish_build_action(state: GameState, actor: ActorId) -> Action | None:
    """
    6H.1: Legacy-Rusher Anti-Stall-Finish.

    Der alte Rusher ist absichtlich raidlastig. Auf großen Boards kann das aber
    zu Raid-Churn führen: wenige neutrale Felder bleiben offen, obwohl ein
    Build-Finish oder Full-Board-Finish möglich wäre.

    Deshalb darf der Rusher im späten/nahen Finish Build vor Raid wählen.
    Early-/Midgame bleibt aggressiv.
    """

    neutral = neutral_field_count(state)
    if neutral <= 0:
        return None

    builds = affordable_build_targets(state, actor)
    if not builds:
        return None

    actor_controlled = state.controlled_count(actor)
    opponent_controlled = state.controlled_count(state.opponent(actor))
    threshold = territory_threshold_60(state)
    actor_to_threshold = threshold - actor_controlled

    near_territory_finish = actor_to_threshold <= max(5, neutral + 1)

    full_board_finish_lane = (
        state.round_index >= 40
        and neutral <= 8
        and actor_controlled >= opponent_controlled
    )

    hard_late_stall_lane = (
        state.round_index >= 75
        and neutral <= 12
        and actor_controlled >= opponent_controlled - 2
    )

    if not (near_territory_finish or full_board_finish_lane or hard_late_stall_lane):
        return None

    return Action(
        actor=actor,
        action_type="build",
        target=choose_expansion_target(state, actor, builds),
        field_type=choose_build_field_type_for_rusher(state, actor),  # type: ignore[arg-type]
    )


def choose_rusher_action(state: GameState, actor: ActorId) -> Action:
    finish_build = rusher_finish_build_action(state, actor)
    if finish_build is not None:
        return finish_build

    raids = affordable_raid_targets(state, actor)
    if raids:
        return Action(
            actor=actor,
            action_type="raid",
            target=choose_best_raid_target(state, actor, raids),
        )

    builds = affordable_build_targets(state, actor)
    if builds:
        return Action(
            actor=actor,
            action_type="build",
            target=choose_expansion_target(state, actor, builds),
            field_type=choose_build_field_type_for_rusher(state, actor),  # type: ignore[arg-type]
        )

    upgrades = affordable_field_upgrade_targets(state, actor)
    if upgrades:
        return Action(
            actor=actor,
            action_type="field_upgrade",
            target=upgrades[0],
        )

    core_upgrades = affordable_core_upgrade_targets(state, actor)
    if core_upgrades:
        return Action(
            actor=actor,
            action_type="core_upgrade",
            target=core_upgrades[0],
        )

    if rusher_should_save_for_build(state, actor):
        return Action(actor=actor, action_type="wait")

    rebuilds = affordable_rebuild_targets(state, actor)
    for target in rebuilds:
        new_type = choose_rebuild_field_type(state, actor, target)
        if new_type is not None:
            return Action(
                actor=actor,
                action_type="rebuild",
                target=target,
                field_type=new_type,  # type: ignore[arg-type]
            )

    return Action(actor=actor, action_type="wait")


def choose_phase_player_action(state: GameState, actor: ActorId) -> Action:
    """
    Normalerer Referenzbot.

    Grobe Phasenlogik:
    - Early: expandieren.
    - Mid: Core/Upgrade/Rebuild nutzen.
    - Front: günstige Raids nehmen.
    """

    non_core = state.non_core_controlled_count(actor)

    # 1) Early Game: erst Raum gewinnen.
    if non_core < 5:
        builds = affordable_build_targets(state, actor)
        if builds:
            return Action(
                actor=actor,
                action_type="build",
                target=choose_expansion_target(state, actor, builds),
                field_type=choose_build_field_type_for_phase_player(state, actor),  # type: ignore[arg-type]
            )

    # 2) Günstige Raids nehmen, aber nicht blind vor allem anderen.
    raids = affordable_raid_targets(state, actor)
    cheap_raids = [
        target
        for target in raids
        if raid_cost_korn(state, actor, target) <= 2
    ]

    if cheap_raids:
        return Action(
            actor=actor,
            action_type="raid",
            target=choose_best_raid_target(state, actor, cheap_raids),
        )

    # 3) Frontfelder konservativ befestigen, wenn Korn am Cap drückt.
    fortify = conservative_fortify_action(state, actor)
    if fortify is not None:
        return fortify

    # 4) Core Upgrade, wenn möglich.
    core_upgrades = affordable_core_upgrade_targets(state, actor)
    if core_upgrades:
        return Action(
            actor=actor,
            action_type="core_upgrade",
            target=core_upgrades[0],
        )

    # 5) Weiterbauen, wenn möglich.
    builds = affordable_build_targets(state, actor)
    if builds:
        return Action(
            actor=actor,
            action_type="build",
            target=choose_expansion_target(state, actor, builds),
            field_type=choose_build_field_type_for_phase_player(state, actor),  # type: ignore[arg-type]
        )

    # 6) Upgrades, wenn Stein am Cap drückt oder genug Stein da ist.
    upgrades = affordable_field_upgrade_targets(state, actor)
    if upgrades:
        stein_pressure = resource_pressure(state, actor, "Stein")

        if stein_pressure >= 0.5:
            return Action(
                actor=actor,
                action_type="field_upgrade",
                target=upgrades[0],
            )

    # 7) Teurere Raids erst nach Aufbau-/Upgrade-Prüfung.
    if raids:
        return Action(
            actor=actor,
            action_type="raid",
            target=choose_best_raid_target(state, actor, raids),
        )

    # 8) Rebuild als letzter sinnvoller Ressourcenumbau.
    rebuilds = affordable_rebuild_targets(state, actor)
    for target in rebuilds:
        new_type = choose_rebuild_field_type(state, actor, target)
        if new_type is not None:
            return Action(
                actor=actor,
                action_type="rebuild",
                target=target,
                field_type=new_type,  # type: ignore[arg-type]
            )

    return Action(actor=actor, action_type="wait")
