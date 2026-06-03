from __future__ import annotations

from src.maillon_v04.actions import (
    Action,
    affordable_build_targets,
    affordable_core_upgrade_targets,
    affordable_field_upgrade_targets,
    affordable_raid_targets,
    affordable_rebuild_targets,
    affordable_tunnel_entrance_targets,
    affordable_tunnel_extend_targets,
    affordable_tunnel_raid_targets,
    affordable_tunnel_repair_build_targets,
)
from src.maillon_v04.board import Coord
from src.maillon_v04.rules import build_cost_holz, field_upgrade_cost_stein, raid_cost_korn
from src.maillon_v04.state import ActorId, GameState
from src.maillon_v04.tunnels import tunnel_pressure


FIELD_VALUE = {
    "Core": 100,
    "Stein": 3,
    "Korn": 2,
    "Holz": 1,
    None: 0,
}


def opponent_core(state: GameState, actor: ActorId) -> Coord:
    return state.enemy_core if actor == "player" else state.player_core


def resource_pressure(state: GameState, actor: ActorId, resource: str) -> float:
    actor_state = state.actor_state(actor)
    value = actor_state.resources[resource]  # type: ignore[index]
    cap = actor_state.caps[resource]  # type: ignore[index]

    if cap <= 0:
        return 0.0

    return value / cap


def actor_field_type_count(state: GameState, actor: ActorId, field_type: str) -> int:
    return sum(
        1
        for cell in state.cells.values()
        if cell.owner == actor
        and not cell.collapsed
        and not cell.is_core
        and cell.field_type == field_type
    )


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


def choose_build_field_type_for_tunnel_probe(state: GameState, actor: ActorId) -> str:
    resources = state.actor_state(actor).resources

    if actor_field_type_count(state, actor, "Stein") <= 0 or resources["Stein"] < 2:
        return "Stein"

    if actor_field_type_count(state, actor, "Holz") < 2 or resources["Holz"] < build_cost_holz(state, actor):
        return "Holz"

    if resources["Korn"] < 3:
        return "Korn"

    return "Stein"


def choose_rebuild_field_type(state: GameState, actor: ActorId, target: Coord) -> str | None:
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


def choose_best_raid_target(state: GameState, actor: ActorId, options: list[Coord]) -> Coord:
    target_core = opponent_core(state, actor)

    return min(
        options,
        key=lambda coord: (
            raid_cost_korn(state, actor, coord),
            -FIELD_VALUE[state.cell(coord).field_type],
            state.board.distance(coord, target_core),
            coord[0],
            coord[1],
        ),
    )


def choose_tunnel_entrance_target(state: GameState, actor: ActorId, options: list[Coord]) -> Coord:
    target_core = opponent_core(state, actor)

    return min(
        options,
        key=lambda coord: (
            state.board.distance(coord, target_core),
            -FIELD_VALUE[state.cell(coord).field_type],
            coord[0],
            coord[1],
        ),
    )


def choose_tunnel_extend_pair(
    state: GameState,
    actor: ActorId,
    options: list[tuple[Coord, Coord]],
) -> tuple[Coord, Coord]:
    target_core = opponent_core(state, actor)
    opponent = state.opponent(actor)

    def owner_priority(coord: Coord) -> int:
        owner = state.cell(coord).owner
        if owner == opponent:
            return 0
        if owner is None:
            return 1
        return 2

    return min(
        options,
        key=lambda pair: (
            owner_priority(pair[1]),
            state.board.distance(pair[1], target_core),
            tunnel_pressure(state, pair[0]),
            tunnel_pressure(state, pair[1]),
            pair[0][0],
            pair[0][1],
            pair[1][0],
            pair[1][1],
        ),
    )


def choose_tunnel_raid_target(state: GameState, actor: ActorId, options: list[Coord]) -> Coord:
    target_core = opponent_core(state, actor)

    return min(
        options,
        key=lambda coord: (
            -state.cell(coord).raid_shield,
            -FIELD_VALUE[state.cell(coord).field_type],
            state.board.distance(coord, target_core),
            coord[0],
            coord[1],
        ),
    )


def choose_tunnel_probe_action(state: GameState, actor: ActorId) -> Action:
    """
    Minimaler tunnel-aware Probe-Bot.

    Ziel: nachweisen, dass Bots echte Tunnelaktionen erzeugen können.
    Kein finaler Balance-Bot.
    """

    tunnel_raids = affordable_tunnel_raid_targets(state, actor)
    if tunnel_raids:
        return Action(
            actor=actor,
            action_type="tunnel_raid",
            target=choose_tunnel_raid_target(state, actor, tunnel_raids),
        )

    repair_targets = affordable_tunnel_repair_build_targets(state, actor)
    if repair_targets:
        return Action(
            actor=actor,
            action_type="repair_build",
            target=choose_closest_to_opponent_core(state, actor, repair_targets),
            field_type=choose_build_field_type_for_tunnel_probe(state, actor),  # type: ignore[arg-type]
        )

    tunnel_extensions = affordable_tunnel_extend_targets(state, actor)
    if tunnel_extensions:
        source, target = choose_tunnel_extend_pair(state, actor, tunnel_extensions)
        return Action(
            actor=actor,
            action_type="tunnel_extend",
            source=source,
            target=target,
        )

    tunnel_entrances = affordable_tunnel_entrance_targets(state, actor)
    if tunnel_entrances:
        return Action(
            actor=actor,
            action_type="tunnel_entrance",
            target=choose_tunnel_entrance_target(state, actor, tunnel_entrances),
        )

    builds = affordable_build_targets(state, actor)
    if builds:
        return Action(
            actor=actor,
            action_type="build",
            target=choose_closest_to_opponent_core(state, actor, builds),
            field_type=choose_build_field_type_for_tunnel_probe(state, actor),  # type: ignore[arg-type]
        )

    raids = affordable_raid_targets(state, actor)
    if raids:
        return Action(
            actor=actor,
            action_type="raid",
            target=choose_best_raid_target(state, actor, raids),
        )

    upgrades = affordable_field_upgrade_targets(state, actor)
    if upgrades and resource_pressure(state, actor, "Stein") >= 0.65:
        return Action(actor=actor, action_type="field_upgrade", target=upgrades[0])

    core_upgrades = affordable_core_upgrade_targets(state, actor)
    if core_upgrades and resource_pressure(state, actor, "Stein") >= 0.8:
        return Action(actor=actor, action_type="core_upgrade", target=core_upgrades[0])

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
