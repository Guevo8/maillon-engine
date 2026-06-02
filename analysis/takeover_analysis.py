from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from typing import Literal


Coord = tuple[int, int]
ActorId = Literal["player", "enemy"]
ActionType = Literal["build", "raid", "upgrade", "core_upgrade", "rebuild", "wait"]
PolicyName = Literal["rusher", "expander", "upgrader", "balanced", "tempo_expander", "cap_aware_balanced", "phase_player"]

DIRECTIONS: list[Coord] = [
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
]


@dataclass(frozen=True)
class HexBoard:
    side_length: int
    radius: int
    cells: tuple[Coord, ...]

    @classmethod
    def create(cls, side_length: int) -> "HexBoard":
        if side_length < 2:
            raise ValueError("side_length must be >= 2")

        radius = side_length - 1
        cells: list[Coord] = []

        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                s = -q - r
                if max(abs(q), abs(r), abs(s)) <= radius:
                    cells.append((q, r))

        return cls(
            side_length=side_length,
            radius=radius,
            cells=tuple(sorted(cells)),
        )

    @property
    def size(self) -> int:
        return len(self.cells)

    def neighbors(self, coord: Coord) -> tuple[Coord, ...]:
        cell_set = set(self.cells)
        found: list[Coord] = []

        for dq, dr in DIRECTIONS:
            candidate = (coord[0] + dq, coord[1] + dr)
            if candidate in cell_set:
                found.append(candidate)

        return tuple(sorted(found))

    @staticmethod
    def distance(a: Coord, b: Coord) -> int:
        aq, ar = a
        bq, br = b

        ax, az = aq, ar
        ay = -ax - az

        bx, bz = bq, br
        by = -bx - bz

        return max(abs(ax - bx), abs(ay - by), abs(az - bz))


@dataclass
class CellState:
    owner: ActorId | None = None
    field_type: str | None = None
    upgraded: bool = False
    active_from_round: int = 1
    contested_count: int = 0


@dataclass(frozen=True)
class Action:
    type: ActionType
    actor: ActorId
    target: Coord | None = None


@dataclass
class GameState:
    board: HexBoard
    cells: dict[Coord, CellState]
    player_core: Coord
    enemy_core: Coord
    round_index: int = 1
    player_build_count: int = 0
    enemy_build_count: int = 0
    resources: dict[ActorId, dict[str, int]] = field(default_factory=dict)
    caps: dict[ActorId, dict[str, int]] = field(default_factory=dict)
    stats: dict[str, int] = field(default_factory=dict)
    action_log: list[dict[str, object]] = field(default_factory=list)

    def clone(self) -> "GameState":
        return GameState(
            board=self.board,
            cells={
                coord: CellState(
                    owner=cell.owner,
                    field_type=cell.field_type,
                    upgraded=cell.upgraded,
                    active_from_round=cell.active_from_round,
                    contested_count=cell.contested_count,
                )
                for coord, cell in self.cells.items()
            },
            player_core=self.player_core,
            enemy_core=self.enemy_core,
            round_index=self.round_index,
            player_build_count=self.player_build_count,
            enemy_build_count=self.enemy_build_count,
            resources={
                actor: dict(values)
                for actor, values in self.resources.items()
            },
            caps={
                actor: dict(values)
                for actor, values in self.caps.items()
            },
            stats=dict(self.stats),
            action_log=[dict(entry) for entry in self.action_log],
        )


@dataclass(frozen=True)
class Matchup:
    name: str
    player_policy: PolicyName
    enemy_policy: PolicyName


MATCHUPS: tuple[Matchup, ...] = (
    # Existing baseline matchups
    Matchup("rusher_vs_rusher", "rusher", "rusher"),
    Matchup("rusher_vs_expander", "rusher", "expander"),
    Matchup("expander_vs_expander", "expander", "expander"),
    Matchup("upgrader_vs_rusher", "upgrader", "rusher"),
    Matchup("balanced_vs_balanced", "balanced", "balanced"),
    Matchup("balanced_vs_rusher", "balanced", "rusher"),

    # Patch 13: policy comparison matchups
    Matchup("tempo_expander_vs_rusher", "tempo_expander", "rusher"),
    Matchup("tempo_expander_vs_cap_aware", "tempo_expander", "cap_aware_balanced"),
    Matchup("cap_aware_vs_rusher", "cap_aware_balanced", "rusher"),
    Matchup("cap_aware_vs_balanced", "cap_aware_balanced", "balanced"),
    Matchup("phase_player_vs_phase_player", "phase_player", "phase_player"),
    Matchup("phase_player_vs_rusher", "phase_player", "rusher"),
    Matchup("phase_player_vs_cap_aware", "phase_player", "cap_aware_balanced"),
)


def opponent(actor: ActorId) -> ActorId:
    return "enemy" if actor == "player" else "player"


def actor_core(state: GameState, actor: ActorId) -> Coord:
    return state.player_core if actor == "player" else state.enemy_core


def enemy_core_for(state: GameState, actor: ActorId) -> Coord:
    return state.enemy_core if actor == "player" else state.player_core


def setup_initial_state(
    board: HexBoard,
    start_holz: int = 2,
    start_stein: int = 0,
    start_korn: int = 3,
    base_cap: int = 6,
) -> GameState:
    r = board.radius

    player_core = (-r, 0)
    enemy_core = (r, 0)

    player_wood = (-r + 1, 0)
    enemy_wood = (r - 1, 0)

    cells = {coord: CellState() for coord in board.cells}

    cells[player_core] = CellState(owner="player", field_type="Core", active_from_round=1)
    cells[player_wood] = CellState(owner="player", field_type="Holz", active_from_round=1)

    cells[enemy_core] = CellState(owner="enemy", field_type="Core", active_from_round=1)
    cells[enemy_wood] = CellState(owner="enemy", field_type="Holz", active_from_round=1)

    return GameState(
        board=board,
        cells=cells,
        player_core=player_core,
        enemy_core=enemy_core,
        resources={
            "player": {"Holz": start_holz, "Stein": start_stein, "Korn": start_korn},
            "enemy": {"Holz": start_holz, "Stein": start_stein, "Korn": start_korn},
        },
        caps={
            "player": {"Holz": base_cap, "Stein": base_cap, "Korn": base_cap},
            "enemy": {"Holz": base_cap, "Stein": base_cap, "Korn": base_cap},
        },
        stats={
            "build_count": 0,
            "raid_count": 0,
            "upgrade_count": 0,
            "wait_count": 0,
            "rebuild_count": 0,
            "blocked_rebuild_no_holz": 0,
            "holz_spent_on_rebuild": 0,
            "core_upgrade_count": 0,
            "blocked_core_upgrade_no_stein": 0,
            "stein_spent_on_core_upgrade": 0,
            "blocked_upgrade_no_stein": 0,
            "stein_spent_on_upgrade": 0,
            "blocked_build_no_holz": 0,
            "holz_spent_on_build": 0,
            "blocked_raid_no_korn": 0,
            "korn_produced": 0,
            "holz_produced": 0,
            "stein_produced": 0,
            "holz_cap_waste": 0,
            "stein_cap_waste": 0,
            "korn_cap_waste": 0,
            "korn_spent_on_raid": 0,
            "takeover_count": 0,
        },
    )


def owned_cells(state: GameState, actor: ActorId) -> list[Coord]:
    return sorted(coord for coord, cell in state.cells.items() if cell.owner == actor)


def active_owned_cells(state: GameState, actor: ActorId) -> list[Coord]:
    return sorted(
        coord
        for coord, cell in state.cells.items()
        if cell.owner == actor and cell.active_from_round <= state.round_index
    )


def neutral_cells(state: GameState) -> list[Coord]:
    return sorted(coord for coord, cell in state.cells.items() if cell.owner is None)


def contact_front_cells(state: GameState, actor: ActorId) -> list[Coord]:
    result: list[Coord] = []

    for coord in owned_cells(state, actor):
        for neighbor in state.board.neighbors(coord):
            if state.cells[neighbor].owner == opponent(actor):
                result.append(coord)
                break

    return sorted(result)


def frontier_cells(state: GameState, actor: ActorId) -> list[Coord]:
    result: list[Coord] = []

    for coord in owned_cells(state, actor):
        for neighbor in state.board.neighbors(coord):
            owner = state.cells[neighbor].owner
            if owner is None or owner == opponent(actor):
                result.append(coord)
                break

    return sorted(result)


def build_targets(state: GameState, actor: ActorId) -> list[Coord]:
    targets: set[Coord] = set()

    for origin in active_owned_cells(state, actor):
        for neighbor in state.board.neighbors(origin):
            if state.cells[neighbor].owner is None:
                targets.add(neighbor)

    return sorted(targets)


def raw_raid_targets(state: GameState, actor: ActorId) -> list[Coord]:
    targets: set[Coord] = set()

    for origin in active_owned_cells(state, actor):
        for neighbor in state.board.neighbors(origin):
            target_cell = state.cells[neighbor]
            if (
                target_cell.owner == opponent(actor)
                and target_cell.field_type != "Core"
                and target_cell.active_from_round <= state.round_index
            ):
                targets.add(neighbor)

    return sorted(targets)


def raid_support(state: GameState, actor: ActorId, target: Coord) -> int:
    support = 0

    for neighbor in state.board.neighbors(target):
        cell = state.cells[neighbor]
        if cell.owner == actor and cell.active_from_round <= state.round_index:
            support += 1

    return support


def raid_cost_for_support(support: int) -> int:
    if support <= 0:
        return 999

    return max(1, 4 - support)


def raid_cost(state: GameState, actor: ActorId, target: Coord) -> int:
    return raid_cost_for_support(raid_support(state, actor, target))


def raid_targets(state: GameState, actor: ActorId) -> list[Coord]:
    affordable: list[Coord] = []

    for target in raw_raid_targets(state, actor):
        cost = raid_cost(state, actor, target)
        if state.resources[actor]["Korn"] >= cost:
            affordable.append(target)

    return sorted(affordable)

def upgrade_targets(state: GameState, actor: ActorId) -> list[Coord]:
    return sorted(
        coord
        for coord, cell in state.cells.items()
        if cell.owner == actor
        and cell.field_type != "Core"
        and not cell.upgraded
        and cell.active_from_round <= state.round_index
    )


def legal_actions(state: GameState, actor: ActorId) -> list[Action]:
    actions: list[Action] = []

    for target in build_targets(state, actor):
        actions.append(Action("build", actor, target))

    for target in raid_targets(state, actor):
        actions.append(Action("raid", actor, target))

    for target in upgrade_targets(state, actor):
        actions.append(Action("upgrade", actor, target))

    actions.append(Action("wait", actor, None))
    return actions


def actor_view(actor: ActorId, coord: Coord) -> Coord:
    q, r = coord
    if actor == "enemy":
        return (-q, -r)
    return (q, r)


def tie_min(actor: ActorId, coord: Coord) -> tuple[int, int]:
    return actor_view(actor, coord)


def tie_max(actor: ActorId, coord: Coord) -> tuple[int, int]:
    q, r = actor_view(actor, coord)
    return (-q, -r)


def future_buildable_count(state: GameState, actor: ActorId, candidate: Coord) -> int:
    future = state.clone()
    future.cells[candidate].owner = actor
    future.cells[candidate].field_type = "Probe"
    future.cells[candidate].active_from_round = state.round_index
    return len(build_targets(future, actor))


def future_frontier_count(state: GameState, actor: ActorId, candidate: Coord) -> int:
    future = state.clone()
    future.cells[candidate].owner = actor
    future.cells[candidate].field_type = "Probe"
    future.cells[candidate].active_from_round = state.round_index
    return len(frontier_cells(future, actor))



def controlled_non_core_count(state: GameState, actor: ActorId) -> int:
    return sum(
        1
        for coord, cell in state.cells.items()
        if cell.owner == actor and cell.field_type != "Core"
    )


def development_tier(state: GameState, actor: ActorId) -> int:
    # Every 5 controlled non-core fields increase the cost tier.
    return controlled_non_core_count(state, actor) // 5


def tiered_cost(tier: int, values: tuple[int, ...]) -> int:
    if tier < 0:
        tier = 0

    if tier >= len(values):
        return values[-1]

    return values[tier]


def build_cost_holz_for_actor(state: GameState, actor: ActorId) -> int:
    return tiered_cost(
        development_tier(state, actor),
        (2, 3, 5, 8, 12),
    )


def field_upgrade_cost_stein_for_actor(state: GameState, actor: ActorId) -> int:
    return tiered_cost(
        development_tier(state, actor),
        (3, 4, 6, 8, 12),
    )


def choose_raid_action(state: GameState, actor: ActorId) -> Action | None:
    targets = raid_targets(state, actor)
    if not targets:
        if raw_raid_targets(state, actor):
            state.stats["blocked_raid_no_korn"] += 1
        return None

    target_enemy_core = enemy_core_for(state, actor)

    target = min(
        targets,
        key=lambda c: (
            raid_cost(state, actor, c),
            state.board.distance(c, target_enemy_core),
            *tie_min(actor, c),
        ),
    )
    return Action("raid", actor, target)


def choose_build_action(state: GameState, actor: ActorId, style: str) -> Action | None:
    targets = build_targets(state, actor)
    if not targets:
        return None

    build_cost_holz = build_cost_holz_for_actor(state, actor)
    if state.resources[actor]["Holz"] < build_cost_holz:
        state.stats["blocked_build_no_holz"] += 1
        return None

    target_enemy_core = enemy_core_for(state, actor)
    own_core = actor_core(state, actor)

    if style == "toward_enemy":
        target = min(
            targets,
            key=lambda c: (
                state.board.distance(c, target_enemy_core),
                *tie_min(actor, c),
            ),
        )
    elif style == "max_expansion":
        target = max(
            targets,
            key=lambda c: (
                future_buildable_count(state, actor, c),
                -state.board.distance(c, own_core),
                *tie_max(actor, c),
            ),
        )
    elif style == "wide_front":
        target = max(
            targets,
            key=lambda c: (
                future_frontier_count(state, actor, c),
                state.board.distance(c, own_core),
                -state.board.distance(c, target_enemy_core),
                *tie_max(actor, c),
            ),
        )
    else:
        raise ValueError(f"Unknown build style: {style}")

    return Action("build", actor, target)



def choose_core_upgrade_action(state: GameState, actor: ActorId) -> Action | None:
    core = actor_core(state, actor)
    core_cell = state.cells[core]

    if core_cell.owner != actor or core_cell.upgraded:
        return None

    core_upgrade_cost_stein = 4
    if state.resources[actor]["Stein"] < core_upgrade_cost_stein:
        state.stats["blocked_core_upgrade_no_stein"] += 1
        return None

    return Action("core_upgrade", actor, core)


def choose_upgrade_action(state: GameState, actor: ActorId) -> Action | None:
    targets = upgrade_targets(state, actor)
    if not targets:
        return None

    upgrade_cost_stein = field_upgrade_cost_stein_for_actor(state, actor)
    if state.resources[actor]["Stein"] < upgrade_cost_stein:
        state.stats["blocked_upgrade_no_stein"] += 1
        return None

    # Deterministisch: zuerst die aus Actor-Sicht "älteste/kleinste" Zelle.
    target = min(targets, key=lambda c: tie_min(actor, c))
    return Action("upgrade", actor, target)



def choose_rebuild_field_type(state: GameState, actor: ActorId, current_field_type: str | None) -> str | None:
    # Choose the resource with the strongest shortage / strategic need,
    # but avoid rebuilding into the same field type.
    scores = {
        "Holz": resource_need_bonus(state, actor, "Holz"),
        "Stein": resource_need_bonus(state, actor, "Stein"),
        "Korn": resource_need_bonus(state, actor, "Korn"),
    }

    # If raids are available but Korn is low, Korn is urgent.
    if raw_raid_targets(state, actor) and state.resources[actor]["Korn"] < 3:
        scores["Korn"] += 45

    # If upgrades/core upgrade are possible but Stein is low, Stein is urgent.
    if upgrade_targets(state, actor) and state.resources[actor]["Stein"] < 3:
        scores["Stein"] += 35

    core = actor_core(state, actor)
    core_cell = state.cells[core]
    if core_cell.owner == actor and not core_cell.upgraded and state.resources[actor]["Stein"] < 4:
        scores["Stein"] += 30

    # If expansion is still possible and Holz is low, Holz remains useful.
    if build_targets(state, actor) and state.resources[actor]["Holz"] < build_cost_holz_for_actor(state, actor):
        scores["Holz"] += 25

    # Never rebuild into a capped resource unless every option is bad.
    for resource in ("Holz", "Stein", "Korn"):
        if state.resources[actor][resource] >= state.caps[actor][resource]:
            scores[resource] -= 80

    # Do not rebuild into same type.
    if current_field_type in scores:
        scores[current_field_type] -= 100

    target_type = max(
        ("Holz", "Stein", "Korn"),
        key=lambda resource: (
            scores[resource],
            {"Holz": 0, "Stein": 1, "Korn": 2}[resource] * -1,
        ),
    )

    if scores[target_type] <= 0:
        return None

    return target_type


def rebuild_targets(state: GameState, actor: ActorId) -> list[Coord]:
    return sorted(
        coord
        for coord, cell in state.cells.items()
        if cell.owner == actor
        and cell.field_type in {"Holz", "Stein", "Korn"}
        and cell.active_from_round <= state.round_index
    )


def choose_rebuild_action(state: GameState, actor: ActorId) -> Action | None:
    rebuild_cost_holz = 2

    if state.resources[actor]["Holz"] < rebuild_cost_holz:
        # Only count as blocked when rebuild would otherwise be meaningful.
        if rebuild_targets(state, actor):
            state.stats["blocked_rebuild_no_holz"] += 1
        return None

    candidates: list[tuple[int, int, int, Coord]] = []

    for coord in rebuild_targets(state, actor):
        cell = state.cells[coord]
        new_type = choose_rebuild_field_type(state, actor, cell.field_type)
        if new_type is None:
            continue

        # Prefer rebuilding fields that are less strategically placed,
        # so front/core-adjacent structure is not churned first.
        distance_from_core = state.board.distance(coord, actor_core(state, actor))
        candidates.append((
            1 if cell.upgraded else 0,
            distance_from_core,
            -len(state.board.neighbors(coord)),
            coord,
        ))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1], item[2], tie_min(actor, item[3])))
    return Action("rebuild", actor, candidates[0][3])


def resource_at_or_near_cap(state: GameState, actor: ActorId, resource: str, ratio: float = 0.90) -> bool:
    cap = state.caps[actor][resource]
    if cap <= 0:
        return False
    return state.resources[actor][resource] >= int(cap * ratio)


def choose_cap_spending_action(state: GameState, actor: ActorId) -> Action | None:
    # Spend capped resources before they become waste.
    # Korn cap pressure -> Raid.
    if resource_at_or_near_cap(state, actor, "Korn", 0.85):
        raid = choose_raid_action(state, actor)
        if raid is not None:
            return raid

    # Holz cap pressure -> Build or Rebuild.
    if resource_at_or_near_cap(state, actor, "Holz", 0.85):
        build = choose_build_action(state, actor, "max_expansion")
        if build is not None:
            return build

        rebuild = choose_rebuild_action(state, actor)
        if rebuild is not None:
            return rebuild

    # Stein cap pressure -> Core Upgrade or Field Upgrade.
    if resource_at_or_near_cap(state, actor, "Stein", 0.85):
        core = choose_core_upgrade_action(state, actor)
        if core is not None:
            return core

        upgrade = choose_upgrade_action(state, actor)
        if upgrade is not None:
            return upgrade

    return None


def choose_phase_player_action(state: GameState, actor: ActorId) -> Action:
    # Board-size-aware phase split.
    # 37-board: early <= 8, mid <= 18
    # 61-board: early <= 12, mid <= 30
    if state.board.size >= 61:
        early_end = 12
        mid_end = 30
    else:
        early_end = 8
        mid_end = 18

    # Early game: claim territory and establish resource base.
    if state.round_index <= early_end:
        return (
            choose_build_action(state, actor, "max_expansion")
            or choose_cap_spending_action(state, actor)
            or choose_rebuild_action(state, actor)
            or choose_core_upgrade_action(state, actor)
            or choose_upgrade_action(state, actor)
            or choose_raid_action(state, actor)
            or Action("wait", actor)
        )

    # Mid game: convert contact into pressure, but avoid resource waste.
    if state.round_index <= mid_end:
        return (
            choose_cap_spending_action(state, actor)
            or choose_raid_action(state, actor)
            or choose_build_action(state, actor, "max_expansion")
            or choose_core_upgrade_action(state, actor)
            or choose_upgrade_action(state, actor)
            or choose_rebuild_action(state, actor)
            or Action("wait", actor)
        )

    # Late game: push win pressure and convert capped resources.
    return (
        choose_cap_spending_action(state, actor)
        or choose_raid_action(state, actor)
        or choose_rebuild_action(state, actor)
        or choose_core_upgrade_action(state, actor)
        or choose_upgrade_action(state, actor)
        or choose_build_action(state, actor, "toward_enemy")
        or Action("wait", actor)
    )


def choose_action(state: GameState, actor: ActorId, policy: PolicyName) -> Action:
    if policy == "rusher":
        return (
            choose_raid_action(state, actor)
            or choose_build_action(state, actor, "toward_enemy")
            or choose_rebuild_action(state, actor)
            or choose_core_upgrade_action(state, actor)
            or choose_upgrade_action(state, actor)
            or Action("wait", actor)
        )

    if policy == "expander":
        return (
            choose_build_action(state, actor, "max_expansion")
            or choose_rebuild_action(state, actor)
            or choose_raid_action(state, actor)
            or choose_core_upgrade_action(state, actor)
            or choose_upgrade_action(state, actor)
            or Action("wait", actor)
        )

    if policy == "upgrader":
        return (
            choose_core_upgrade_action(state, actor)
            or choose_upgrade_action(state, actor)
            or choose_rebuild_action(state, actor)
            or choose_raid_action(state, actor)
            or choose_build_action(state, actor, "max_expansion")
            or Action("wait", actor)
        )

    if policy == "balanced":
        return (
            choose_raid_action(state, actor)
            or choose_build_action(state, actor, "max_expansion")
            or choose_rebuild_action(state, actor)
            or choose_core_upgrade_action(state, actor)
            or choose_upgrade_action(state, actor)
            or Action("wait", actor)
        )

    if policy == "tempo_expander":
        # Tests whether Holz waste can be an acceptable price for territory tempo.
        # Build remains high priority; cap correction comes later.
        return (
            choose_build_action(state, actor, "max_expansion")
            or choose_raid_action(state, actor)
            or choose_rebuild_action(state, actor)
            or choose_core_upgrade_action(state, actor)
            or choose_upgrade_action(state, actor)
            or Action("wait", actor)
        )

    if policy == "cap_aware_balanced":
        # Tests whether resource efficiency beats raw tempo.
        return (
            choose_cap_spending_action(state, actor)
            or choose_raid_action(state, actor)
            or choose_build_action(state, actor, "max_expansion")
            or choose_rebuild_action(state, actor)
            or choose_core_upgrade_action(state, actor)
            or choose_upgrade_action(state, actor)
            or Action("wait", actor)
        )

    if policy == "phase_player":
        # Tests a human-readable early/mid/late strategy.
        return choose_phase_player_action(state, actor)

    raise ValueError(f"Unknown policy: {policy}")


def resource_fill_ratio(state: GameState, actor: ActorId, resource: str) -> float:
    cap = state.caps[actor][resource]
    if cap <= 0:
        return 1.0

    return state.resources[actor][resource] / cap


def resource_need_bonus(state: GameState, actor: ActorId, resource: str) -> int:
    value = state.resources[actor][resource]
    cap = state.caps[actor][resource]

    if value >= cap:
        return -100

    ratio = resource_fill_ratio(state, actor, resource)

    if ratio <= 0.25:
        return 35
    if ratio <= 0.50:
        return 20
    if ratio <= 0.75:
        return 8

    return 0


def choose_field_type_for_build(state: GameState, actor: ActorId, policy: PolicyName) -> str:
    # Resource-aware field choice:
    # Holz = expansion fuel
    # Korn = raid fuel
    # Stein = upgrade / cap infrastructure

    if policy == "rusher":
        scores = {
            "Holz": 20,
            "Stein": 10,
            "Korn": 45,
        }
    elif policy == "expander":
        scores = {
            "Holz": 45,
            "Stein": 15,
            "Korn": 20,
        }
    elif policy == "upgrader":
        scores = {
            "Holz": 15,
            "Stein": 50,
            "Korn": 15,
        }
    elif policy == "balanced":
        scores = {
            "Holz": 28,
            "Stein": 28,
            "Korn": 28,
        }
    else:
        scores = {
            "Holz": 25,
            "Stein": 25,
            "Korn": 25,
        }

    # General shortage / cap awareness.
    for resource in ("Holz", "Stein", "Korn"):
        scores[resource] += resource_need_bonus(state, actor, resource)

    # If expansion is still available but Holz is low, Holz becomes urgent.
    if build_targets(state, actor) and state.resources[actor]["Holz"] < build_cost_holz_for_actor(state, actor):
        scores["Holz"] += 40

    # If Raid targets exist but Korn is low, Korn becomes urgent.
    if raw_raid_targets(state, actor) and state.resources[actor]["Korn"] < 3:
        scores["Korn"] += 45

    # If field upgrades exist but Stein is low, Stein becomes urgent.
    if upgrade_targets(state, actor) and state.resources[actor]["Stein"] < 3:
        scores["Stein"] += 35

    # If Core upgrade is still possible but Stein is low, Stein becomes urgent.
    core = actor_core(state, actor)
    core_cell = state.cells[core]
    if core_cell.owner == actor and not core_cell.upgraded and state.resources[actor]["Stein"] < 4:
        scores["Stein"] += 30

    # Avoid overbuilding Holz if it is already capped and there is no immediate expansion pressure.
    if state.resources[actor]["Holz"] >= state.caps[actor]["Holz"]:
        scores["Holz"] -= 80

    # Avoid overbuilding Korn if no raid pressure exists and Korn is capped.
    if not raw_raid_targets(state, actor) and state.resources[actor]["Korn"] >= state.caps[actor]["Korn"]:
        scores["Korn"] -= 80

    # Avoid overbuilding Stein if both Core and most upgrades are unavailable and Stein is capped.
    if state.resources[actor]["Stein"] >= state.caps[actor]["Stein"]:
        scores["Stein"] -= 80

    # Deterministic tie break:
    # Balanced prefers the cycle-ish stable order Holz > Stein > Korn only on true score ties.
    tie_order = {
        "Holz": 0,
        "Stein": 1,
        "Korn": 2,
    }

    return max(
        ("Holz", "Stein", "Korn"),
        key=lambda resource: (
            scores[resource],
            -tie_order[resource],
        ),
    )


def stat_add(state: GameState, key: str, amount: int) -> None:
    state.stats[key] = state.stats.get(key, 0) + amount


def add_resource_capped(
    state: GameState,
    actor: ActorId,
    resource: str,
    amount: int,
) -> None:
    if amount <= 0:
        return

    current = state.resources[actor][resource]
    cap = state.caps[actor][resource]
    new_value = min(cap, current + amount)
    stored = new_value - current
    wasted = amount - stored

    state.resources[actor][resource] = new_value

    key = resource.lower()
    stat_add(state, f"{key}_produced", amount)

    if wasted > 0:
        stat_add(state, f"{key}_cap_waste", wasted)


def production_amount_for_cell(cell: CellState) -> int:
    return 2 if cell.upgraded else 1


def produce_resources(state: GameState, actor: ActorId) -> None:
    # Core gives basic Korn supply.
    core = actor_core(state, actor)
    if state.cells[core].owner == actor:
        add_resource_capped(state, actor, "Korn", 1)

    for coord in active_owned_cells(state, actor):
        cell = state.cells[coord]

        if cell.field_type == "Holz":
            add_resource_capped(state, actor, "Holz", production_amount_for_cell(cell))
        elif cell.field_type == "Stein":
            add_resource_capped(state, actor, "Stein", production_amount_for_cell(cell))
        elif cell.field_type == "Korn":
            add_resource_capped(state, actor, "Korn", production_amount_for_cell(cell))



def snapshot_actor_resources(state: GameState, actor: ActorId) -> dict[str, int]:
    return {
        "Holz": state.resources[actor]["Holz"],
        "Stein": state.resources[actor]["Stein"],
        "Korn": state.resources[actor]["Korn"],
    }


def append_action_log(
    state: GameState,
    *,
    actor: ActorId,
    policy: PolicyName,
    action_type: str,
    target: Coord | None,
    result: str,
    field_type_before: str | None,
    field_type_after: str | None,
    owner_before: ActorId | None,
    owner_after: ActorId | None,
    resources_before: dict[str, int],
    resources_after: dict[str, int],
    cost_holz: int = 0,
    cost_stein: int = 0,
    cost_korn: int = 0,
    contested_count_after: int | None = None,
    active_from_round_after: int | None = None,
) -> None:
    state.action_log.append({
        "round": state.round_index,
        "actor": actor,
        "policy": policy,
        "action_type": action_type,
        "target": str(target) if target is not None else None,
        "result": result,
        "field_type_before": field_type_before,
        "field_type_after": field_type_after,
        "owner_before": owner_before,
        "owner_after": owner_after,
        "holz_before": resources_before["Holz"],
        "stein_before": resources_before["Stein"],
        "korn_before": resources_before["Korn"],
        "holz_after": resources_after["Holz"],
        "stein_after": resources_after["Stein"],
        "korn_after": resources_after["Korn"],
        "cost_holz": cost_holz,
        "cost_stein": cost_stein,
        "cost_korn": cost_korn,
        "contested_count_after": contested_count_after,
        "active_from_round_after": active_from_round_after,
    })


def apply_action(state: GameState, action: Action, policy: PolicyName) -> str:
    target_cell: CellState | None = None

    if action.target is not None:
        target_cell = state.cells[action.target]

    resources_before = snapshot_actor_resources(state, action.actor)
    field_type_before = target_cell.field_type if target_cell is not None else None
    owner_before = target_cell.owner if target_cell is not None else None

    def log_and_return(
        result: str,
        *,
        cost_holz: int = 0,
        cost_stein: int = 0,
        cost_korn: int = 0,
    ) -> str:
        resources_after = snapshot_actor_resources(state, action.actor)
        field_type_after = target_cell.field_type if target_cell is not None else None
        owner_after = target_cell.owner if target_cell is not None else None
        contested_after = target_cell.contested_count if target_cell is not None else None
        active_after = target_cell.active_from_round if target_cell is not None else None

        append_action_log(
            state,
            actor=action.actor,
            policy=policy,
            action_type=action.type,
            target=action.target,
            result=result,
            field_type_before=field_type_before,
            field_type_after=field_type_after,
            owner_before=owner_before,
            owner_after=owner_after,
            resources_before=resources_before,
            resources_after=resources_after,
            cost_holz=cost_holz,
            cost_stein=cost_stein,
            cost_korn=cost_korn,
            contested_count_after=contested_after,
            active_from_round_after=active_after,
        )
        return result

    if action.type == "wait":
        state.stats["wait_count"] += 1
        return log_and_return("wait")

    if action.target is None:
        raise ValueError("Non-wait action requires a target")

    cell = state.cells[action.target]

    if action.type == "build":
        if cell.owner is not None:
            state.stats["wait_count"] += 1
            return log_and_return("invalid_build")

        build_cost_holz = build_cost_holz_for_actor(state, action.actor)
        if state.resources[action.actor]["Holz"] < build_cost_holz:
            state.stats["blocked_build_no_holz"] += 1
            state.stats["wait_count"] += 1
            return log_and_return("blocked_build_no_holz")

        state.resources[action.actor]["Holz"] -= build_cost_holz
        state.stats["holz_spent_on_build"] += build_cost_holz

        cell.owner = action.actor
        cell.field_type = choose_field_type_for_build(state, action.actor, policy)
        cell.upgraded = False
        cell.active_from_round = state.round_index + 1

        if action.actor == "player":
            state.player_build_count += 1
        else:
            state.enemy_build_count += 1

        state.stats["build_count"] += 1
        return log_and_return("build", cost_holz=build_cost_holz)

    if action.type == "raid":
        if (
            cell.owner != opponent(action.actor)
            or cell.field_type == "Core"
            or cell.active_from_round > state.round_index
        ):
            state.stats["wait_count"] += 1
            return log_and_return("invalid_raid")

        cost = raid_cost(state, action.actor, action.target)
        if state.resources[action.actor]["Korn"] < cost:
            state.stats["blocked_raid_no_korn"] += 1
            state.stats["wait_count"] += 1
            return log_and_return("blocked_raid_no_korn")

        state.resources[action.actor]["Korn"] -= cost
        state.stats["korn_spent_on_raid"] += cost

        cell.owner = action.actor
        cell.contested_count += 1
        cooldown = min(3, cell.contested_count)
        cell.active_from_round = state.round_index + cooldown

        state.stats["raid_count"] += 1
        state.stats["takeover_count"] += 1
        return log_and_return("takeover", cost_korn=cost)

    if action.type == "rebuild":
        if (
            cell.owner != action.actor
            or cell.field_type not in {"Holz", "Stein", "Korn"}
            or cell.active_from_round > state.round_index
        ):
            state.stats["wait_count"] += 1
            return log_and_return("invalid_rebuild")

        rebuild_cost_holz = 2
        if state.resources[action.actor]["Holz"] < rebuild_cost_holz:
            state.stats["blocked_rebuild_no_holz"] += 1
            state.stats["wait_count"] += 1
            return log_and_return("blocked_rebuild_no_holz")

        new_type = choose_rebuild_field_type(state, action.actor, cell.field_type)
        if new_type is None:
            state.stats["wait_count"] += 1
            return log_and_return("no_useful_rebuild")

        state.resources[action.actor]["Holz"] -= rebuild_cost_holz
        state.stats["holz_spent_on_rebuild"] += rebuild_cost_holz

        cell.field_type = new_type
        cell.active_from_round = state.round_index + 1

        state.stats["rebuild_count"] += 1
        return log_and_return("rebuild", cost_holz=rebuild_cost_holz)

    if action.type == "core_upgrade":
        if cell.owner != action.actor or cell.field_type != "Core" or cell.upgraded:
            state.stats["wait_count"] += 1
            return log_and_return("invalid_core_upgrade")

        core_upgrade_cost_stein = 4
        if state.resources[action.actor]["Stein"] < core_upgrade_cost_stein:
            state.stats["blocked_core_upgrade_no_stein"] += 1
            state.stats["wait_count"] += 1
            return log_and_return("blocked_core_upgrade_no_stein")

        state.resources[action.actor]["Stein"] -= core_upgrade_cost_stein
        state.stats["stein_spent_on_core_upgrade"] += core_upgrade_cost_stein

        cell.upgraded = True
        state.caps[action.actor]["Holz"] += 6
        state.caps[action.actor]["Stein"] += 6
        state.caps[action.actor]["Korn"] += 6

        state.stats["core_upgrade_count"] += 1
        return log_and_return("core_upgrade", cost_stein=core_upgrade_cost_stein)

    if action.type == "upgrade":
        if cell.owner != action.actor or cell.field_type == "Core" or cell.upgraded:
            state.stats["wait_count"] += 1
            return log_and_return("invalid_upgrade")

        upgrade_cost_stein = field_upgrade_cost_stein_for_actor(state, action.actor)
        if state.resources[action.actor]["Stein"] < upgrade_cost_stein:
            state.stats["blocked_upgrade_no_stein"] += 1
            state.stats["wait_count"] += 1
            return log_and_return("blocked_upgrade_no_stein")

        state.resources[action.actor]["Stein"] -= upgrade_cost_stein
        state.stats["stein_spent_on_upgrade"] += upgrade_cost_stein

        cell.upgraded = True
        state.stats["upgrade_count"] += 1
        return log_and_return("upgrade", cost_stein=upgrade_cost_stein)

    raise ValueError(f"Unknown action type: {action.type}")

def controlled_count(state: GameState, actor: ActorId) -> int:
    return len(owned_cells(state, actor))


def territory_gap(state: GameState) -> int:
    return abs(controlled_count(state, "player") - controlled_count(state, "enemy"))


def winner_at_threshold(state: GameState, threshold: int) -> ActorId | None:
    if controlled_count(state, "player") >= threshold:
        return "player"
    if controlled_count(state, "enemy") >= threshold:
        return "enemy"
    return None



def max_contested_count(state: GameState) -> int:
    return max((cell.contested_count for cell in state.cells.values()), default=0)


def contested_fields_at_least(state: GameState, minimum: int) -> int:
    return sum(
        1
        for cell in state.cells.values()
        if cell.contested_count >= minimum
    )


def contested_fields_total(state: GameState) -> int:
    return sum(
        1
        for cell in state.cells.values()
        if cell.contested_count > 0
    )


def snapshot(state: GameState) -> dict[str, object]:
    def actor_snapshot(actor: ActorId) -> dict[str, object]:
        res = state.resources[actor]
        caps = state.caps[actor]

        return {
            "controlled": controlled_count(state, actor),
            "resources": {
                "Holz": res["Holz"],
                "Stein": res["Stein"],
                "Korn": res["Korn"],
            },
            "caps": {
                "Holz": caps["Holz"],
                "Stein": caps["Stein"],
                "Korn": caps["Korn"],
            },
            # Compatibility fields for older report code / quick grep reading.
            "holz": res["Holz"],
            "stein": res["Stein"],
            "korn": res["Korn"],
            "holz_cap": caps["Holz"],
            "stein_cap": caps["Stein"],
            "korn_cap": caps["Korn"],
            "build_targets": len(build_targets(state, actor)),
            "raid_targets": len(raid_targets(state, actor)),
            "all_raid_targets": len(raw_raid_targets(state, actor)),
            "upgrade_targets": len(upgrade_targets(state, actor)),
            "rebuild_targets": len(rebuild_targets(state, actor)),
            "frontier": len(frontier_cells(state, actor)),
            "contact_front": len(contact_front_cells(state, actor)),
        }

    return {
        "round": state.round_index,
        "player": actor_snapshot("player"),
        "enemy": actor_snapshot("enemy"),
        "neutral": len(neutral_cells(state)),
        "territory_gap": territory_gap(state),
        "contested": {
            "max_contested_count": max_contested_count(state),
            "contested_fields_total": contested_fields_total(state),
            "contested_fields_2plus": contested_fields_at_least(state, 2),
            "contested_fields_3plus": contested_fields_at_least(state, 3),
        },
        "stats": dict(state.stats),
    }


def select_milestone_snapshots(timeline: list[dict[str, object]]) -> list[dict[str, object]]:
    if not timeline:
        return []

    last_index = len(timeline) - 1
    candidates = [
        ("start", 0),
        ("25_percent", round(last_index * 0.25)),
        ("50_percent", round(last_index * 0.50)),
        ("75_percent", round(last_index * 0.75)),
        ("final", last_index),
    ]

    result: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()

    for label, index in candidates:
        index = max(0, min(last_index, index))
        snap = timeline[index]
        round_value = int(snap["round"])
        key = (label, round_value)

        if key in seen:
            continue

        seen.add(key)
        result.append({
            "label": label,
            "snapshot": snap,
        })

    return result

def simulate_matchup(
    side_length: int,
    matchup: Matchup,
    max_rounds: int,
    actions_per_turn: int,
) -> dict[str, object]:
    board = HexBoard.create(side_length)
    state = setup_initial_state(board)

    threshold_60 = math.ceil(board.size * 0.60)

    first_takeover_round: int | None = None
    first_60_round: int | None = None
    winner: ActorId | None = None
    territory_gap_max = territory_gap(state)
    no_non_wait_round: int | None = None

    timeline: list[dict[str, object]] = [snapshot(state)]

    for round_index in range(1, max_rounds + 1):
        state.round_index = round_index
        round_events: list[str] = []

        produce_resources(state, "player")
        produce_resources(state, "enemy")

        for actor, policy in (
            ("player", matchup.player_policy),
            ("enemy", matchup.enemy_policy),
        ):
            for _ in range(actions_per_turn):
                action = choose_action(state, actor, policy)
                event = apply_action(state, action, policy)
                round_events.append(event)

                if event == "takeover" and first_takeover_round is None:
                    first_takeover_round = round_index

                territory_gap_max = max(territory_gap_max, territory_gap(state))

                if first_60_round is None:
                    current_winner = winner_at_threshold(state, threshold_60)
                    if current_winner is not None:
                        first_60_round = round_index
                        winner = current_winner
                        break

            if winner is not None:
                break

        if no_non_wait_round is None and all(event == "wait" for event in round_events):
            no_non_wait_round = round_index

        timeline.append(snapshot(state))

        if winner is not None:
            break

    if winner is None:
        player_cells = controlled_count(state, "player")
        enemy_cells = controlled_count(state, "enemy")

        if player_cells > enemy_cells:
            winner = "player"
        elif enemy_cells > player_cells:
            winner = "enemy"

    return {
        "analysis_version": "0.1",
        "mode": "direct_takeover",
        "side_length": side_length,
        "board_size": board.size,
        "matchup": matchup.name,
        "player_policy": matchup.player_policy,
        "enemy_policy": matchup.enemy_policy,
        "actions_per_turn": actions_per_turn,
        "max_rounds": max_rounds,
        "threshold_60": threshold_60,
        "first_takeover_round": first_takeover_round,
        "first_60_percent_round": first_60_round,
        "winner": winner,
        "final_round": state.round_index,
        "territory_gap_max": territory_gap_max,
        "no_non_wait_round": no_non_wait_round,
        "max_contested_count": max_contested_count(state),
        "contested_fields_total": contested_fields_total(state),
        "contested_fields_2plus": contested_fields_at_least(state, 2),
        "contested_fields_3plus": contested_fields_at_least(state, 3),
        "final_snapshot": snapshot(state),
        "milestone_snapshots": select_milestone_snapshots(timeline),
        "timeline": timeline,
        "action_log": state.action_log,
    }


def run_analysis(
    side_lengths: list[int],
    max_rounds: int,
    actions_per_turn: int,
) -> dict[str, object]:
    results: list[dict[str, object]] = []

    for side_length in sorted(side_lengths):
        for matchup in MATCHUPS:
            results.append(
                simulate_matchup(
                    side_length=side_length,
                    matchup=matchup,
                    max_rounds=max_rounds,
                    actions_per_turn=actions_per_turn,
                )
            )

    return {
        "analysis_version": "0.1",
        "purpose": "Direct takeover simulation for Maillon v0.3 board combat.",
        "determinism": {
            "timestamps": False,
            "randomness": False,
            "stable_sorting": True,
        },
        "side_lengths": sorted(side_lengths),
        "max_rounds": max_rounds,
        "actions_per_turn": actions_per_turn,
        "results": results,
    }


def print_markdown(report: dict[str, object]) -> None:
    def stat(stats: dict[str, object], key: str) -> int:
        value = stats.get(key, 0)
        return int(value) if isinstance(value, int) else 0

    print("# Maillon Resource Economy + Direct Takeover Analysis v0.3")
    print()
    print(f"- Max rounds: {report['max_rounds']}")
    print(f"- Actions per turn: {report['actions_per_turn']}")
    print(f"- Side lengths: {', '.join(str(x) for x in report['side_lengths'])}")
    print("- Deterministic: yes")
    print("- Timestamps: no")
    print()

    for result in report["results"]:
        assert isinstance(result, dict)

        print(f"## Board {result['board_size']} / `{result['matchup']}`")
        print()
        print(f"- Side length: {result['side_length']}")
        print(f"- Policies: {result['player_policy']} vs {result['enemy_policy']}")
        print(f"- 60% threshold: {result['threshold_60']} cells")
        print(f"- First takeover round: {result['first_takeover_round']}")
        print(f"- First 60% round: {result['first_60_percent_round']}")
        print(f"- Winner: {result['winner']}")
        print(f"- Final round: {result['final_round']}")
        print(f"- Max territory gap: {result['territory_gap_max']}")
        print(f"- No non-wait round: {result['no_non_wait_round']}")
        print()

        milestones = result.get("milestone_snapshots", [])
        assert isinstance(milestones, list)

        print("Resource timeline:")
        print()
        print("| Point | Round | Actor | Cells | Holz | Stein | Korn | Holz Cap | Stein Cap | Korn Cap | Build | Raid | Upgrade |")
        print("|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

        for item in milestones:
            assert isinstance(item, dict)
            label = item["label"]
            snap = item["snapshot"]
            assert isinstance(snap, dict)

            for actor_label, actor_key in (("Player", "player"), ("Enemy", "enemy")):
                actor = snap[actor_key]
                assert isinstance(actor, dict)

                print(
                    f"| {label} | {snap['round']} | {actor_label} | "
                    f"{actor['controlled']} | "
                    f"{actor['holz']} | {actor['stein']} | {actor['korn']} | "
                    f"{actor['holz_cap']} | {actor['stein_cap']} | {actor['korn_cap']} | "
                    f"{actor['build_targets']} | {actor['raid_targets']} | {actor['upgrade_targets']} |"
                )

        print()

        final_snapshot = result["final_snapshot"]
        assert isinstance(final_snapshot, dict)

        player = final_snapshot["player"]
        enemy = final_snapshot["enemy"]
        stats = final_snapshot["stats"]
        assert isinstance(player, dict)
        assert isinstance(enemy, dict)
        assert isinstance(stats, dict)

        print("Final action/resource stats:")
        print()
        print("| Build | Raid | Takeover | Rebuild | Field Upgrade | Core Upgrade | Wait |")
        print("|---:|---:|---:|---:|---:|---:|---:|")
        print(
            f"| {stat(stats, 'build_count')} | "
            f"{stat(stats, 'raid_count')} | "
            f"{stat(stats, 'takeover_count')} | "
            f"{stat(stats, 'rebuild_count')} | "
            f"{stat(stats, 'upgrade_count')} | "
            f"{stat(stats, 'core_upgrade_count')} | "
            f"{stat(stats, 'wait_count')} |"
        )
        print()

        print("| Blocked Build no Holz | Blocked Rebuild no Holz | Blocked Raid no Korn | Blocked Upgrade no Stein | Blocked Core Upgrade no Stein |")
        print("|---:|---:|---:|---:|---:|")
        print(
            f"| {stat(stats, 'blocked_build_no_holz')} | "
            f"{stat(stats, 'blocked_rebuild_no_holz')} | "
            f"{stat(stats, 'blocked_raid_no_korn')} | "
            f"{stat(stats, 'blocked_upgrade_no_stein')} | "
            f"{stat(stats, 'blocked_core_upgrade_no_stein')} |"
        )
        print()

        print("| Holz produced | Stein produced | Korn produced | Holz spent build | Holz spent rebuild | Stein spent upgrade | Stein spent core | Korn spent raid |")
        print("|---:|---:|---:|---:|---:|---:|---:|---:|")
        print(
            f"| {stat(stats, 'holz_produced')} | "
            f"{stat(stats, 'stein_produced')} | "
            f"{stat(stats, 'korn_produced')} | "
            f"{stat(stats, 'holz_spent_on_build')} | "
            f"{stat(stats, 'holz_spent_on_rebuild')} | "
            f"{stat(stats, 'stein_spent_on_upgrade')} | "
            f"{stat(stats, 'stein_spent_on_core_upgrade')} | "
            f"{stat(stats, 'korn_spent_on_raid')} |"
        )
        print()

        print("| Holz cap waste | Stein cap waste | Korn cap waste |")
        print("|---:|---:|---:|")
        print(
            f"| {stat(stats, 'holz_cap_waste')} | "
            f"{stat(stats, 'stein_cap_waste')} | "
            f"{stat(stats, 'korn_cap_waste')} |"
        )
        print()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Direct takeover analysis for Maillon v0.3."
    )
    parser.add_argument(
        "--side-lengths",
        nargs="+",
        type=int,
        default=[4, 5],
        help="Hex side lengths. 4 = 37 cells, 5 = 61 cells.",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=80,
        help="Maximum number of rounds.",
    )
    parser.add_argument(
        "--actions-per-turn",
        type=int,
        default=2,
        help="Actions per actor turn.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "md"],
        default="md",
        help="Output format.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_analysis(
        side_lengths=args.side_lengths,
        max_rounds=args.max_rounds,
        actions_per_turn=args.actions_per_turn,
    )

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_markdown(report)


if __name__ == "__main__":
    main()
