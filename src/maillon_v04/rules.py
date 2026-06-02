from __future__ import annotations

import math

from src.maillon_v04.board import Coord
from src.maillon_v04.state import ActorId, FieldType, GameState, ResourceName


TERRITORY_WIN_RATIO = 0.60

BUILD_COSTS_HOLZ: tuple[int, ...] = (2, 3, 5, 8, 12)
FIELD_UPGRADE_COSTS_STEIN: tuple[int, ...] = (3, 4, 6, 8, 12)

CORE_UPGRADE_COST_STEIN = 4
REBUILD_COST_HOLZ = 2

BASE_CAP = 6
CORE_LEVEL_2_CAP_BONUS = 6


def tiered_cost(tier: int, values: tuple[int, ...]) -> int:
    if tier < 0:
        tier = 0

    if tier >= len(values):
        return values[-1]

    return values[tier]


def development_tier(state: GameState, actor: ActorId) -> int:
    """
    v0.4-Entwicklungsstufe:
    Alle 5 eigene Nicht-Core-Felder erhöhen die Kostenstufe.
    """

    return state.non_core_controlled_count(actor) // 5


def build_cost_holz(state: GameState, actor: ActorId) -> int:
    return tiered_cost(
        development_tier(state, actor),
        BUILD_COSTS_HOLZ,
    )


def field_upgrade_cost_stein(state: GameState, actor: ActorId) -> int:
    return tiered_cost(
        development_tier(state, actor),
        FIELD_UPGRADE_COSTS_STEIN,
    )


def core_upgrade_cost_stein(state: GameState, actor: ActorId) -> int:
    # v0.4 baseline: only Core Level 1 -> 2.
    # actor is accepted for future scaling / Core Level 3.
    _ = state
    _ = actor
    return CORE_UPGRADE_COST_STEIN


def rebuild_cost_holz(state: GameState, actor: ActorId) -> int:
    # v0.4 baseline: flat rebuild cost.
    _ = state
    _ = actor
    return REBUILD_COST_HOLZ


def active_support_count_for_target(
    state: GameState,
    actor: ActorId,
    target: Coord,
) -> int:
    """
    Zählt aktive eigene Nachbarn am Ziel.
    Dient als Support für Raid-Kosten.
    """

    support = 0

    for neighbor in state.board.neighbors(target):
        cell = state.cell(neighbor)

        if cell.owner == actor and state.is_active(neighbor):
            support += 1

    return support


def raid_cost_korn(state: GameState, actor: ActorId, target: Coord) -> int:
    """
    Raid-Kosten nach Support:

    1 eigener aktiver Nachbar  -> 3 Korn
    2 eigene aktive Nachbarn   -> 2 Korn
    3+ eigene aktive Nachbarn  -> 1 Korn
    """

    support = active_support_count_for_target(state, actor, target)

    if support <= 0:
        raise ValueError(f"raid target has no active support: actor={actor}, target={target}")

    if support == 1:
        return 3

    if support == 2:
        return 2

    return 1


def production_for_field(field_type: FieldType | None, level: int) -> tuple[ResourceName, int] | None:
    """
    Gibt die Produktion eines Feldes zurück.

    Core:
        +1 Korn pro Runde.

    Holz/Stein/Korn:
        Level 1 -> +1
        Level 2 -> +2
    """

    if field_type is None:
        return None

    if field_type == "Core":
        return ("Korn", 1)

    if field_type == "Holz":
        return ("Holz", max(1, level))

    if field_type == "Stein":
        return ("Stein", max(1, level))

    if field_type == "Korn":
        return ("Korn", max(1, level))

    raise ValueError(f"Unknown field_type: {field_type}")


def add_resource_capped(
    state: GameState,
    actor: ActorId,
    resource: ResourceName,
    amount: int,
) -> int:
    """
    Fügt Ressource bis zum Cap hinzu.

    Rückgabe:
        waste / Überlauf, der wegen Cap nicht gespeichert wurde.
    """

    if amount < 0:
        raise ValueError("amount must be >= 0")

    actor_state = state.actor_state(actor)

    before = actor_state.resources[resource]
    cap = actor_state.caps[resource]
    after_uncapped = before + amount
    after = min(after_uncapped, cap)

    actor_state.resources[resource] = after

    return after_uncapped - after


def can_pay(
    state: GameState,
    actor: ActorId,
    costs: dict[ResourceName, int],
) -> bool:
    actor_state = state.actor_state(actor)

    return all(
        actor_state.resources[resource] >= amount
        for resource, amount in costs.items()
    )


def pay_resources(
    state: GameState,
    actor: ActorId,
    costs: dict[ResourceName, int],
) -> None:
    """
    Zieht Ressourcen ab.

    Wirft ValueError, wenn Kosten nicht bezahlt werden können.
    """

    if not can_pay(state, actor, costs):
        raise ValueError(f"actor cannot pay costs: actor={actor}, costs={costs}")

    actor_state = state.actor_state(actor)

    for resource, amount in costs.items():
        if amount < 0:
            raise ValueError("cost amount must be >= 0")

        actor_state.resources[resource] -= amount


def apply_production_for_actor(state: GameState, actor: ActorId) -> dict[ResourceName, int]:
    """
    Produziert für alle aktiven eigenen Felder.

    Rückgabe:
        Waste je Ressource.
    """

    waste: dict[ResourceName, int] = {
        "Holz": 0,
        "Stein": 0,
        "Korn": 0,
    }

    for coord in state.owned_cells(actor):
        if not state.is_active(coord):
            continue

        cell = state.cell(coord)
        production = production_for_field(cell.field_type, cell.level)

        if production is None:
            continue

        resource, amount = production
        waste[resource] += add_resource_capped(state, actor, resource, amount)

    return waste


def apply_production(state: GameState) -> dict[ActorId, dict[ResourceName, int]]:
    """
    Produziert für player und enemy.

    Rückgabe:
        Waste je Actor und Ressource.
    """

    return {
        "player": apply_production_for_actor(state, "player"),
        "enemy": apply_production_for_actor(state, "enemy"),
    }


def apply_core_level_2_caps(state: GameState, actor: ActorId) -> None:
    """
    Erhöht alle Caps um +6.

    Diese Funktion verändert nur Caps.
    Kosten und Core-Level-Setzung passieren später in actions.py.
    """

    actor_state = state.actor_state(actor)

    for resource in actor_state.caps:
        actor_state.caps[resource] += CORE_LEVEL_2_CAP_BONUS


def territory_threshold_60(state: GameState) -> int:
    return math.ceil(state.board.size * TERRITORY_WIN_RATIO)


def has_territory_win(state: GameState, actor: ActorId) -> bool:
    return state.controlled_count(actor) >= territory_threshold_60(state)


def winner_by_territory(state: GameState) -> ActorId | None:
    player_wins = has_territory_win(state, "player")
    enemy_wins = has_territory_win(state, "enemy")

    if player_wins and enemy_wins:
        # Sollte im Normalfall nicht auftreten, aber deterministisch bleiben.
        player_count = state.controlled_count("player")
        enemy_count = state.controlled_count("enemy")

        if player_count > enemy_count:
            return "player"

        if enemy_count > player_count:
            return "enemy"

        return None

    if player_wins:
        return "player"

    if enemy_wins:
        return "enemy"

    return None
