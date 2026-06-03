from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .actions import (
    Action,
    affordable_build_targets,
    affordable_core_upgrade_targets,
    affordable_field_upgrade_targets,
    affordable_fortify_targets,
    affordable_raid_targets,
    affordable_rebuild_targets,
)
from .bot_personality import (
    BotPersonality,
    PersonalityWeights,
    get_weights_for_state,
)
from .rules import (
    build_cost_holz,
    core_upgrade_cost_stein,
    field_upgrade_cost_stein,
    fortify_cost_korn,
    raid_cost_korn,
    rebuild_cost_holz,
    territory_threshold_60,
)
from .state import ActorId, Coord, GameState


ResourceType = Literal["Holz", "Stein", "Korn"]
UtilityCategory = Literal[
    "expansion",
    "economy",
    "defense",
    "aggression",
    "development",
    "fallback",
]

FIELD_TYPES: tuple[ResourceType, ...] = ("Holz", "Stein", "Korn")

ACTION_PRIORITY: tuple[str, ...] = (
    "raid",
    "fortify",
    "build",
    "field_upgrade",
    "core_upgrade",
    "rebuild",
    "wait",
)


FIELD_VALUE: dict[str | None, float] = {
    "Core": 12.0,
    "Stein": 7.0,
    "Korn": 7.5,
    "Holz": 7.0,
    "leer": 0.0,
    None: 0.0,
}


@dataclass(frozen=True, slots=True)
class UtilityScore:
    action: Action
    category: UtilityCategory
    raw_score: float
    weight: float
    total_score: float
    reasons: tuple[str, ...] = ()


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def action_priority(action_type: str) -> int:
    try:
        return ACTION_PRIORITY.index(action_type)
    except ValueError:
        return len(ACTION_PRIORITY)


def action_target_sort_key(action: Action) -> tuple[int, int, str]:
    coord = action.target

    if coord is None:
        return (999, 999, action.field_type or "")

    return (coord[0], coord[1], action.field_type or "")


def opponent_core(state: GameState, actor: ActorId) -> Coord:
    opponent = state.opponent(actor)

    for coord, cell in state.cells.items():
        if cell.owner == opponent and cell.is_core:
            return coord

    raise ValueError(f"opponent core not found for actor={actor}")


def own_core(state: GameState, actor: ActorId) -> Coord:
    for coord, cell in state.cells.items():
        if cell.owner == actor and cell.is_core:
            return coord

    raise ValueError(f"own core not found for actor={actor}")


def resource_pressure(state: GameState, actor: ActorId, resource: ResourceType) -> float:
    actor_state = state.actor_state(actor)
    cap = actor_state.caps.get(resource, 0)

    if cap <= 0:
        return 0.0

    return clamp(actor_state.resources.get(resource, 0) / cap)


def resource_need(state: GameState, actor: ActorId, resource: ResourceType) -> float:
    return 1.0 - resource_pressure(state, actor, resource)


def neighbor_owner_counts(state: GameState, actor: ActorId, coord: Coord) -> dict[str, int]:
    opponent = state.opponent(actor)
    counts = {
        "own": 0,
        "enemy": 0,
        "neutral": 0,
    }

    for neighbor in state.board.neighbors(coord):
        owner = state.cell(neighbor).owner

        if owner == actor:
            counts["own"] += 1
        elif owner == opponent:
            counts["enemy"] += 1
        else:
            counts["neutral"] += 1

    return counts


def distance_closeness_to_enemy_core(state: GameState, actor: ActorId, coord: Coord) -> float:
    max_distance = max(1, state.board.radius * 2)
    distance = state.board.distance(coord, opponent_core(state, actor))

    return 1.0 - clamp(distance / max_distance)


def distance_closeness_to_own_core(state: GameState, actor: ActorId, coord: Coord) -> float:
    max_distance = max(1, state.board.radius * 2)
    distance = state.board.distance(coord, own_core(state, actor))

    return 1.0 - clamp(distance / max_distance)


def category_for_action(action: Action) -> UtilityCategory:
    if action.action_type == "build":
        return "expansion"

    if action.action_type == "raid":
        return "aggression"

    if action.action_type == "fortify":
        return "defense"

    if action.action_type in {"field_upgrade", "core_upgrade"}:
        return "development"

    if action.action_type == "rebuild":
        return "economy"

    return "fallback"


def weight_for_category(weights: PersonalityWeights, category: UtilityCategory) -> float:
    if category == "expansion":
        return weights.expansion

    if category == "economy":
        return weights.economy

    if category == "defense":
        return weights.defense

    if category == "aggression":
        return weights.aggression

    if category == "development":
        return weights.development

    return 1.0


def score_build(state: GameState, actor: ActorId, action: Action) -> tuple[float, tuple[str, ...]]:
    assert action.target is not None
    assert action.field_type in FIELD_TYPES

    target = action.target
    field_type = action.field_type
    cost = build_cost_holz(state, actor)
    neighbors = neighbor_owner_counts(state, actor, target)
    need = resource_need(state, actor, field_type)
    enemy_core_closeness = distance_closeness_to_enemy_core(state, actor, target)

    neutral_remaining = sum(1 for cell in state.cells.values() if cell.owner is None)
    board_fill_pressure = 1.0 - clamp(neutral_remaining / state.board.size)

    raw = 10.0
    raw += 12.0 * need
    raw += 4.5 * neighbors["own"]
    raw += 3.5 * neighbors["enemy"]
    raw += 8.0 * enemy_core_closeness
    raw += 6.0 * board_fill_pressure
    raw += FIELD_VALUE[field_type] * 0.45
    raw -= cost * 1.35

    return max(raw, 0.0), (
        f"type={field_type}",
        f"need={need:.2f}",
        f"own_neighbors={neighbors['own']}",
        f"enemy_neighbors={neighbors['enemy']}",
        f"cost_holz={cost}",
    )


def score_raid(state: GameState, actor: ActorId, action: Action) -> tuple[float, tuple[str, ...]]:
    assert action.target is not None

    target = action.target
    cell = state.cell(target)
    cost = raid_cost_korn(state, actor, target)
    shield = cell.raid_shield
    enemy_core_closeness = distance_closeness_to_enemy_core(state, actor, target)
    opponent = state.opponent(actor)
    opponent_non_core = state.non_core_controlled_count(opponent)

    raw = 14.0
    raw += FIELD_VALUE[cell.field_type]
    raw += cell.level * 3.0
    raw += enemy_core_closeness * 14.0
    raw += max(0, 4 - opponent_non_core) * 7.0
    raw += cell.contested_count * 1.5
    raw -= cost * 2.2

    if shield > 0:
        raw -= shield * 13.0
        raw += 2.0  # shield removal still has tactical value, but should not dominate

    return max(raw, 0.0), (
        f"target_type={cell.field_type}",
        f"level={cell.level}",
        f"shield={shield}",
        f"cost_korn={cost}",
        f"opponent_non_core={opponent_non_core}",
    )


def score_fortify(state: GameState, actor: ActorId, action: Action) -> tuple[float, tuple[str, ...]]:
    assert action.target is not None

    target = action.target
    cell = state.cell(target)
    cost = fortify_cost_korn(state, actor, target)
    neighbors = neighbor_owner_counts(state, actor, target)
    own_core_closeness = distance_closeness_to_own_core(state, actor, target)

    raw = 4.0
    raw += neighbors["enemy"] * 12.0
    raw += cell.contested_count * 5.0
    raw += FIELD_VALUE[cell.field_type] * 0.5
    raw += own_core_closeness * 4.0
    raw += max(0, 3 - cell.raid_shield) * 2.0
    raw -= cost * 1.8

    if neighbors["enemy"] == 0 and cell.contested_count == 0:
        raw *= 0.12

    return max(raw, 0.0), (
        f"type={cell.field_type}",
        f"shield={cell.raid_shield}",
        f"enemy_neighbors={neighbors['enemy']}",
        f"contested={cell.contested_count}",
        f"cost_korn={cost}",
    )


def score_field_upgrade(state: GameState, actor: ActorId, action: Action) -> tuple[float, tuple[str, ...]]:
    assert action.target is not None

    target = action.target
    cell = state.cell(target)
    cost = field_upgrade_cost_stein(state, actor)
    pressure = resource_pressure(state, actor, "Stein")

    raw = 10.0
    raw += FIELD_VALUE[cell.field_type]
    raw += pressure * 8.0
    raw += cell.contested_count * 1.5
    raw -= cost * 1.4

    return max(raw, 0.0), (
        f"type={cell.field_type}",
        f"level={cell.level}",
        f"stein_pressure={pressure:.2f}",
        f"cost_stein={cost}",
    )


def score_core_upgrade(state: GameState, actor: ActorId, action: Action) -> tuple[float, tuple[str, ...]]:
    _ = action

    cost = core_upgrade_cost_stein(state, actor)
    avg_pressure = sum(
        resource_pressure(state, actor, resource)
        for resource in FIELD_TYPES
    ) / len(FIELD_TYPES)

    raw = 18.0
    raw += avg_pressure * 18.0
    raw += state.non_core_controlled_count(actor) * 0.7
    raw -= cost * 1.5

    return max(raw, 0.0), (
        f"avg_resource_pressure={avg_pressure:.2f}",
        f"cost_stein={cost}",
    )


def score_rebuild(state: GameState, actor: ActorId, action: Action) -> tuple[float, tuple[str, ...]]:
    assert action.target is not None
    assert action.field_type in FIELD_TYPES

    target = action.target
    new_type = action.field_type
    cell = state.cell(target)
    old_type = cell.field_type

    if old_type == new_type:
        return 0.0, ("same_type",)

    cost = rebuild_cost_holz(state, actor)
    new_need = resource_need(state, actor, new_type)
    old_pressure = (
        resource_pressure(state, actor, old_type)
        if old_type in FIELD_TYPES
        else 0.0
    )

    raw = 5.0
    raw += new_need * 14.0
    raw += old_pressure * 6.0
    raw += cell.contested_count * 1.0
    raw -= cost * 1.7

    return max(raw, 0.0), (
        f"old_type={old_type}",
        f"new_type={new_type}",
        f"new_need={new_need:.2f}",
        f"old_pressure={old_pressure:.2f}",
        f"cost_holz={cost}",
    )


def score_wait(state: GameState, actor: ActorId, action: Action) -> tuple[float, tuple[str, ...]]:
    _ = state
    _ = actor
    _ = action

    return 0.05, ("fallback",)



def neutral_field_count(state: GameState) -> int:
    return sum(1 for cell in state.cells.values() if cell.owner is None)


def apply_strategic_pressure(
    state: GameState,
    actor: ActorId,
    action: Action,
    category: UtilityCategory,
    raw: float,
    reasons: tuple[str, ...],
) -> tuple[float, tuple[str, ...]]:
    """
    v0.5 tuned2 strategic context layer.

    The base score still evaluates the action locally.
    This layer changes priority based on match state:
    - behind -> prefer build/raid, reduce fortify/wait/economy
    - opponent near territory -> prefer interrupt/expand, reduce passive actions
    - actor near territory -> prefer finishing build/raid
    - many neutral fields -> prefer expansion
    """

    actor_controlled = state.controlled_count(actor)
    opponent = state.opponent(actor)
    opponent_controlled = state.controlled_count(opponent)
    threshold = territory_threshold_60(state)
    neutral = neutral_field_count(state)

    actor_to_threshold = max(0, threshold - actor_controlled)
    opponent_to_threshold = max(0, threshold - opponent_controlled)

    behind = actor_controlled < opponent_controlled
    far_behind = (opponent_controlled - actor_controlled) >= max(4, state.board.radius)

    multiplier = 1.0
    bonus = 0.0
    context: list[str] = []

    # If we can finish soon, expansion and decisive raids matter more than passive play.
    if actor_to_threshold <= 3:
        if action.action_type == "build":
            bonus += 18.0 + (4 - actor_to_threshold) * 6.0
            context.append(f"actor_near_territory_build_bonus actor_to={actor_to_threshold}")
        elif action.action_type == "raid":
            bonus += 8.0
            context.append(f"actor_near_territory_raid_bonus actor_to={actor_to_threshold}")
        elif category in {"defense", "economy", "development", "fallback"}:
            multiplier *= 0.55
            context.append(f"actor_near_territory_passive_down actor_to={actor_to_threshold}")

    # If the opponent is close to territory victory, passive actions are dangerous.
    if opponent_to_threshold <= 4:
        if action.action_type == "raid":
            multiplier *= 1.35
            bonus += 5.0
            context.append(f"opponent_near_territory_raid_up opponent_to={opponent_to_threshold}")
        elif action.action_type == "build":
            multiplier *= 1.55
            bonus += 6.0
            context.append(f"opponent_near_territory_build_up opponent_to={opponent_to_threshold}")
        elif action.action_type == "fortify":
            multiplier *= 0.28
            context.append(f"opponent_near_territory_fortify_down opponent_to={opponent_to_threshold}")
        elif action.action_type == "rebuild":
            multiplier *= 0.08
            context.append(f"opponent_near_territory_rebuild_hard_down opponent_to={opponent_to_threshold}")
        elif category in {"economy", "development"}:
            multiplier *= 0.20
            context.append(f"opponent_near_territory_dev_econ_down opponent_to={opponent_to_threshold}")
        elif action.action_type == "wait":
            multiplier *= 0.02
            context.append(f"opponent_near_territory_wait_down opponent_to={opponent_to_threshold}")

    # When behind, the bot should stop turtling and look for progress.
    if behind:
        if action.action_type == "build":
            multiplier *= 1.60
            bonus += 4.0
            context.append("behind_build_up")
        elif action.action_type == "raid":
            multiplier *= 1.12
            context.append("behind_raid_moderate_up")
        elif action.action_type == "fortify":
            multiplier *= 0.38
            context.append("behind_fortify_down")
        elif action.action_type == "rebuild":
            multiplier *= 0.30
            context.append("behind_rebuild_down")
        elif category in {"economy", "development"}:
            multiplier *= 0.45
            context.append("behind_dev_econ_down")
        elif action.action_type == "wait":
            multiplier *= 0.04
            context.append("behind_wait_down")

        if far_behind and action.action_type == "fortify":
            multiplier *= 0.45
            context.append("far_behind_fortify_extra_down")

    # If a lot of the board is still neutral, expansion must stay attractive.
    if neutral > 0:
        neutral_ratio = neutral / state.board.size

        if action.action_type == "build" and neutral_ratio >= 0.12:
            expansion_boost = 1.0 + min(0.65, neutral_ratio * 1.4)
            multiplier *= expansion_boost
            bonus += neutral_ratio * 8.0
            context.append(f"neutral_expansion_boost={expansion_boost:.2f}")

        if behind and neutral_ratio >= 0.12:
            if action.action_type == "fortify":
                multiplier *= 0.70
                context.append("neutral_behind_fortify_extra_down")
            elif action.action_type == "rebuild":
                multiplier *= 0.45
                context.append("neutral_behind_rebuild_extra_down")
            elif action.action_type == "wait":
                multiplier *= 0.15
                context.append("neutral_behind_wait_extra_down")

    # 6G tuned1: finish expansion pressure.
    #
    # 61er-Stall-Diagnose zeigte Raid-Churn:
    # sehr viele Raids/Takeovers, aber neutrale Felder bleiben offen.
    #
    # Ziel:
    # - führende oder gleichstarke Utility-Bots sollen offene neutrale Felder
    #   im späten/nahen Finish stärker schließen,
    # - passive Aktionen werden in diesen Zuständen gedämpft,
    # - Raid bleibt erlaubt, dominiert aber nicht jeden Endgame-Zug.
    finish_window = (
        neutral > 0
        and actor_controlled >= opponent_controlled
        and actor_to_threshold <= max(5, neutral + 3)
    )
    late_open_board = neutral > 0 and state.round_index >= 45

    if finish_window:
        if action.action_type == "build":
            multiplier *= 2.20
            bonus += 20.0 + max(0, 8 - actor_to_threshold) * 3.0
            context.append(
                f"finish_window_build_up actor_to={actor_to_threshold} neutral={neutral}"
            )
        elif action.action_type == "raid":
            multiplier *= 0.82
            context.append(
                f"finish_window_raid_soft_down actor_to={actor_to_threshold} neutral={neutral}"
            )
        elif action.action_type == "fortify":
            multiplier *= 0.35
            context.append("finish_window_fortify_down")
        elif action.action_type == "rebuild":
            multiplier *= 0.20
            context.append("finish_window_rebuild_down")
        elif action.action_type == "wait":
            multiplier *= 0.05
            context.append("finish_window_wait_down")
        elif category in {"economy", "development"}:
            multiplier *= 0.55
            context.append("finish_window_dev_econ_down")

    if late_open_board:
        if action.action_type == "build":
            multiplier *= 1.65
            bonus += min(18.0, neutral * 1.8)
            context.append(f"late_open_board_build_up neutral={neutral}")
        elif action.action_type == "raid":
            multiplier *= 0.90
            context.append("late_open_board_raid_soft_down")
        elif action.action_type == "fortify":
            multiplier *= 0.65
            context.append("late_open_board_fortify_down")
        elif action.action_type == "rebuild":
            multiplier *= 0.30
            context.append("late_open_board_rebuild_down")
        elif action.action_type == "wait":
            multiplier *= 0.05
            context.append("late_open_board_wait_down")

    adjusted = max(raw * multiplier + bonus, 0.0)

    resources = state.actor_state(actor).resources

    has_holz_production = any(
        cell.owner == actor
        and not cell.is_core
        and cell.field_type == "Holz"
        for cell in state.cells.values()
    )

    should_save_for_build = (
        behind
        and neutral > 0
        and has_holz_production
        and resources["Holz"] < build_cost_holz(state, actor)
    )

    # tuned2d: if expansion is still possible but the bot is short on Holz,
    # rebuilding is usually destructive because it spends the exact resource
    # needed for the next build. In that state, wait becomes a valid saving move.
    if should_save_for_build:
        if action.action_type == "rebuild":
            adjusted = 0.0
            context.append("save_for_build_rebuild_zero")

        elif action.action_type == "wait":
            adjusted = max(adjusted, 9.0)
            context.append("save_for_build_wait_floor=9")

    # tuned2c/tuned2d: hard caps for rebuild in losing / pressure states.
    # Rebuild can be useful in stable economy phases, but it must not beat
    # build/raid when the bot is behind, when many neutral fields remain,
    # or when the opponent is close to territory victory.
    if action.action_type == "rebuild":
        if behind:
            adjusted = min(adjusted, 4.0)
            context.append("behind_rebuild_score_cap=4")

        if behind and neutral > 0:
            adjusted = min(adjusted, 1.0)
            context.append("behind_neutral_rebuild_score_cap=1")

        if opponent_to_threshold <= 4:
            adjusted = min(adjusted, 0.5)
            context.append("opponent_near_rebuild_score_cap=0.5")

    if context:
        reasons = reasons + (
            f"context_multiplier={multiplier:.2f}",
            f"context_bonus={bonus:.2f}",
            *context,
        )

    return adjusted, reasons


def score_action(
    state: GameState,
    actor: ActorId,
    action: Action,
    personality: BotPersonality | str = "balancer",
) -> UtilityScore:
    category = category_for_action(action)
    weights = get_weights_for_state(state, personality)
    weight = weight_for_category(weights, category)

    if action.action_type == "build":
        raw, reasons = score_build(state, actor, action)
    elif action.action_type == "raid":
        raw, reasons = score_raid(state, actor, action)
    elif action.action_type == "fortify":
        raw, reasons = score_fortify(state, actor, action)
    elif action.action_type == "field_upgrade":
        raw, reasons = score_field_upgrade(state, actor, action)
    elif action.action_type == "core_upgrade":
        raw, reasons = score_core_upgrade(state, actor, action)
    elif action.action_type == "rebuild":
        raw, reasons = score_rebuild(state, actor, action)
    else:
        raw, reasons = score_wait(state, actor, action)

    raw, reasons = apply_strategic_pressure(
        state=state,
        actor=actor,
        action=action,
        category=category,
        raw=raw,
        reasons=reasons,
    )

    return UtilityScore(
        action=action,
        category=category,
        raw_score=raw,
        weight=weight,
        total_score=raw * weight,
        reasons=reasons,
    )


def generate_candidate_actions(state: GameState, actor: ActorId) -> list[Action]:
    actions: list[Action] = []

    for target in affordable_build_targets(state, actor):
        for field_type in FIELD_TYPES:
            actions.append(
                Action(
                    actor=actor,
                    action_type="build",
                    target=target,
                    field_type=field_type,
                )
            )

    for target in affordable_raid_targets(state, actor):
        actions.append(
            Action(
                actor=actor,
                action_type="raid",
                target=target,
            )
        )

    for target in affordable_fortify_targets(state, actor):
        actions.append(
            Action(
                actor=actor,
                action_type="fortify",
                target=target,
            )
        )

    for target in affordable_field_upgrade_targets(state, actor):
        actions.append(
            Action(
                actor=actor,
                action_type="field_upgrade",
                target=target,
            )
        )

    for target in affordable_core_upgrade_targets(state, actor):
        actions.append(
            Action(
                actor=actor,
                action_type="core_upgrade",
                target=target,
            )
        )

    for target in affordable_rebuild_targets(state, actor):
        current_type = state.cell(target).field_type

        for field_type in FIELD_TYPES:
            if field_type == current_type:
                continue

            actions.append(
                Action(
                    actor=actor,
                    action_type="rebuild",
                    target=target,
                    field_type=field_type,
                )
            )

    actions.append(Action(actor=actor, action_type="wait"))

    return actions


def score_candidate_actions(
    state: GameState,
    actor: ActorId,
    personality: BotPersonality | str = "balancer",
) -> list[UtilityScore]:
    return [
        score_action(state, actor, action, personality)
        for action in generate_candidate_actions(state, actor)
    ]


def choose_best_utility_action(
    state: GameState,
    actor: ActorId,
    personality: BotPersonality | str = "balancer",
) -> Action:
    scores = score_candidate_actions(state, actor, personality)

    best = sorted(
        scores,
        key=lambda score: (
            -score.total_score,
            action_priority(score.action.action_type),
            action_target_sort_key(score.action),
        ),
    )[0]

    return best.action


def top_utility_scores(
    state: GameState,
    actor: ActorId,
    personality: BotPersonality | str = "balancer",
    limit: int = 10,
) -> list[UtilityScore]:
    scores = score_candidate_actions(state, actor, personality)

    return sorted(
        scores,
        key=lambda score: (
            -score.total_score,
            action_priority(score.action.action_type),
            action_target_sort_key(score.action),
        ),
    )[:limit]
