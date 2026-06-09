from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .actions import (
    Action,
    affordable_tunnel_entrance_targets,
    affordable_tunnel_extend_targets,
    affordable_tunnel_raid_targets,
    affordable_tunnel_repair_build_targets,
)
from .bot_utility import choose_best_utility_action, score_candidate_actions
from .rules import territory_threshold_60
from .state import ActorId, GameState
from .tunnel_collapse import collapse_candidates
from .tunnel_config import DEFAULT_COLLAPSE_THRESHOLD
from .tunnel_rules import (
    repair_build_cost,
    tunnel_entrance_cost,
    tunnel_extend_cost,
    tunnel_raid_cost,
)
from .tunnels import (
    add_tunnel_edge,
    is_under_tunnel,
    tunnel_access_nodes,
    tunnel_pressure,
)


NORMAL_SCORE_NORMALIZATION_CAP: float = 60.0
OPPORTUNITY_COST_TOLERANCE: float = 0.10
BASELINE_PERSONALITY: str = "balancer"
COLLAPSE_THRESHOLD: int = DEFAULT_COLLAPSE_THRESHOLD

_TUNNEL_FIELD_TYPES: tuple[str, ...] = ("Holz", "Stein", "Korn")

_NORMALIZED_FIELD_VALUE: dict[str | None, float] = {
    "Core": 1.0,
    "Korn": 7.5 / 12.0,
    "Stein": 7.0 / 12.0,
    "Holz": 7.0 / 12.0,
    None: 0.0,
}

TUNNEL_ACTION_PRIORITY: dict[str, int] = {
    "tunnel_raid": 0,
    "repair_build": 1,
    "tunnel_extend": 2,
    "tunnel_entrance": 3,
    "wait": 4,
}

TUNNEL_ACTION_WEIGHTS: dict[str, dict[str, float]] = {
    "tunnel_entrance": {
        "resource_fit": 0.25,
        "tunnel_access_gain": 0.30,
        "enemy_tunnel_threat": 0.10,
        "own_tunnel_pressure": 0.00,
        "collapse_risk": -0.10,
        "raid_value": 0.00,
        "repair_value": 0.00,
        "territory_pressure": 0.20,
    },
    "tunnel_extend": {
        "resource_fit": 0.20,
        "tunnel_access_gain": 0.35,
        "enemy_tunnel_threat": 0.15,
        "own_tunnel_pressure": -0.10,
        "collapse_risk": -0.15,
        "raid_value": 0.00,
        "repair_value": 0.00,
        "territory_pressure": 0.20,
    },
    "tunnel_raid": {
        "resource_fit": 0.15,
        "tunnel_access_gain": 0.00,
        "enemy_tunnel_threat": 0.10,
        "own_tunnel_pressure": 0.00,
        "collapse_risk": 0.00,
        "raid_value": 0.45,
        "repair_value": 0.00,
        "territory_pressure": 0.15,
    },
    "repair_build": {
        "resource_fit": 0.20,
        "tunnel_access_gain": 0.10,
        "enemy_tunnel_threat": 0.00,
        "own_tunnel_pressure": 0.00,
        "collapse_risk": 0.00,
        "raid_value": 0.00,
        "repair_value": 0.50,
        "territory_pressure": 0.10,
    },
    "wait": {
        "resource_fit": 0.00,
        "tunnel_access_gain": 0.00,
        "enemy_tunnel_threat": 0.00,
        "own_tunnel_pressure": 0.00,
        "collapse_risk": 0.00,
        "raid_value": 0.00,
        "repair_value": 0.00,
        "territory_pressure": 0.00,
    },
}


@dataclass(frozen=True, slots=True)
class TunnelFeatures:
    resource_fit: float
    tunnel_access_gain: float
    enemy_tunnel_threat: float
    own_tunnel_pressure: float
    collapse_risk: float
    raid_value: float
    repair_value: float
    territory_pressure: float
    normal_action_baseline: float
    opportunity_cost: float


@dataclass(frozen=True, slots=True)
class TunnelScore:
    action: Action
    features: TunnelFeatures
    score: float
    reasons: tuple[tuple[str, float], ...]


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _get_normal_baseline(state: GameState, actor: ActorId) -> float:
    scores = score_candidate_actions(state, actor, BASELINE_PERSONALITY)
    if not scores:
        return 0.0
    best_raw = max(s.total_score for s in scores)
    return best_raw / NORMAL_SCORE_NORMALIZATION_CAP


def _feature_resource_fit(
    state: GameState,
    actor: ActorId,
    action: Action,
) -> float:
    action_type = action.action_type
    if action_type == "tunnel_entrance":
        costs = tunnel_entrance_cost(state, actor)
    elif action_type == "tunnel_extend":
        costs = tunnel_extend_cost(state, actor)
    elif action_type == "tunnel_raid":
        costs = tunnel_raid_cost(state, actor)
    elif action_type == "repair_build":
        costs = repair_build_cost(state, actor)
    else:
        return 0.0

    actor_state = state.actor_state(actor)
    slacks: list[float] = []
    for resource, cost in costs.items():
        remaining = actor_state.resources.get(resource, 0) - cost
        cap = actor_state.caps.get(resource, 1)
        slack = max(0.0, float(remaining)) / max(1, cap)
        slacks.append(_clamp(slack))

    return sum(slacks) / len(slacks) if slacks else 0.0


def _feature_tunnel_access_gain(
    state: GameState,
    actor: ActorId,
    action: Action,
) -> float:
    if action.action_type == "tunnel_entrance":
        if action.target is None:
            return 0.0
        count = sum(
            1
            for n in state.board.neighbors(action.target)
            if state.cell(n).owner == actor and not state.cell(n).collapsed
        )
        return _clamp(count / 6.0)

    if action.action_type == "tunnel_extend":
        if action.source is None or action.target is None:
            return 0.0
        before = len(tunnel_access_nodes(state, actor))
        cloned = state.clone()
        add_tunnel_edge(cloned, action.source, action.target)
        after = len(tunnel_access_nodes(cloned, actor))
        delta = after - before
        return _clamp(delta / max(1, state.board.radius * 2))

    if action.action_type == "repair_build":
        if action.target is None:
            return 0.0
        access = tunnel_access_nodes(state, actor)
        adjacent_to_access = any(
            n in access for n in state.board.neighbors(action.target)
        )
        return 0.3 if adjacent_to_access else 0.0

    return 0.0


def _feature_enemy_tunnel_threat(state: GameState, actor: ActorId) -> float:
    owned = state.owned_cells(actor)
    if not owned:
        return 0.0
    total_pressure = sum(
        tunnel_pressure(state, c) for c in owned if is_under_tunnel(state, c)
    )
    return _clamp(total_pressure / (len(owned) * COLLAPSE_THRESHOLD))


def _feature_own_tunnel_pressure(state: GameState, action: Action) -> float:
    if action.action_type != "tunnel_extend" or action.source is None:
        return 0.0
    return _clamp(tunnel_pressure(state, action.source) / COLLAPSE_THRESHOLD)


def _feature_collapse_risk(
    state: GameState,
    actor: ActorId,
    action: Action,
) -> float:
    at_risk = collapse_candidates(state, threshold=COLLAPSE_THRESHOLD)
    own_at_risk = [c for c in at_risk if state.cell(c).owner == actor]
    base_risk = _clamp(len(own_at_risk) / max(1, state.controlled_count(actor)))

    if (
        action.action_type == "tunnel_extend"
        and action.source is not None
        and action.target is not None
    ):
        source_after = tunnel_pressure(state, action.source) + 1
        target_after = tunnel_pressure(state, action.target) + 1
        if source_after >= COLLAPSE_THRESHOLD or target_after >= COLLAPSE_THRESHOLD:
            base_risk = _clamp(base_risk * 2.0)

    return base_risk


def _feature_raid_value(state: GameState, action: Action) -> float:
    if action.action_type != "tunnel_raid" or action.target is None:
        return 0.0
    cell = state.cell(action.target)
    field_score = _NORMALIZED_FIELD_VALUE.get(cell.field_type, 0.0)
    shield_bypass_bonus = _clamp(cell.raid_shield / 3.0) * 0.3
    return _clamp(field_score + shield_bypass_bonus)


def _feature_repair_value(
    state: GameState,
    actor: ActorId,
    action: Action,
) -> float:
    if action.action_type != "repair_build" or action.target is None:
        return 0.0
    adjacent_own = sum(
        1
        for n in state.board.neighbors(action.target)
        if state.cell(n).owner == actor and not state.cell(n).collapsed
    )
    return _clamp(adjacent_own / 4.0)


def _feature_territory_pressure(state: GameState, actor: ActorId) -> float:
    actor_controlled = state.controlled_count(actor)
    opponent = state.opponent(actor)
    opponent_controlled = state.controlled_count(opponent)
    threshold = territory_threshold_60(state)

    opponent_to_threshold = max(0, threshold - opponent_controlled)
    urgency = _clamp(1.0 - (opponent_to_threshold / max(1, threshold)))
    behind_ratio = _clamp(
        (opponent_controlled - actor_controlled) / max(1, state.board.size)
    )
    return _clamp(0.5 * urgency + 0.5 * behind_ratio)


def extract_tunnel_features(
    state: GameState,
    actor: ActorId,
    action: Action,
    normal_baseline: float,
) -> TunnelFeatures:
    return TunnelFeatures(
        resource_fit=_feature_resource_fit(state, actor, action),
        tunnel_access_gain=_feature_tunnel_access_gain(state, actor, action),
        enemy_tunnel_threat=_feature_enemy_tunnel_threat(state, actor),
        own_tunnel_pressure=_feature_own_tunnel_pressure(state, action),
        collapse_risk=_feature_collapse_risk(state, actor, action),
        raid_value=_feature_raid_value(state, action),
        repair_value=_feature_repair_value(state, actor, action),
        territory_pressure=_feature_territory_pressure(state, actor),
        normal_action_baseline=normal_baseline,
        opportunity_cost=0.0,
    )


def score_tunnel_candidate(
    state: GameState,
    actor: ActorId,
    action: Action,
    normal_baseline: float,
) -> TunnelScore:
    features = extract_tunnel_features(state, actor, action, normal_baseline)
    weights = TUNNEL_ACTION_WEIGHTS.get(
        action.action_type, TUNNEL_ACTION_WEIGHTS["wait"]
    )

    feature_values: dict[str, float] = {
        "resource_fit": features.resource_fit,
        "tunnel_access_gain": features.tunnel_access_gain,
        "enemy_tunnel_threat": features.enemy_tunnel_threat,
        "own_tunnel_pressure": features.own_tunnel_pressure,
        "collapse_risk": features.collapse_risk,
        "raid_value": features.raid_value,
        "repair_value": features.repair_value,
        "territory_pressure": features.territory_pressure,
    }

    weighted_sum = sum(
        weights[fname] * fval
        for fname, fval in feature_values.items()
        if weights.get(fname, 0.0) != 0.0
    )

    raw_score = _clamp(weighted_sum)
    opportunity_cost = max(0.0, normal_baseline - raw_score)

    reasons: tuple[tuple[str, float], ...] = tuple(
        (fname, round(weights.get(fname, 0.0) * fval, 4))
        for fname, fval in feature_values.items()
        if weights.get(fname, 0.0) != 0.0
    ) + (("opportunity_cost", round(-opportunity_cost, 4)),)

    updated_features = TunnelFeatures(
        resource_fit=features.resource_fit,
        tunnel_access_gain=features.tunnel_access_gain,
        enemy_tunnel_threat=features.enemy_tunnel_threat,
        own_tunnel_pressure=features.own_tunnel_pressure,
        collapse_risk=features.collapse_risk,
        raid_value=features.raid_value,
        repair_value=features.repair_value,
        territory_pressure=features.territory_pressure,
        normal_action_baseline=normal_baseline,
        opportunity_cost=opportunity_cost,
    )

    return TunnelScore(
        action=action,
        features=updated_features,
        score=raw_score,
        reasons=reasons,
    )


def generate_tunnel_candidates(state: GameState, actor: ActorId) -> list[Action]:
    actions: list[Action] = []

    for target in affordable_tunnel_entrance_targets(state, actor):
        actions.append(
            Action(actor=actor, action_type="tunnel_entrance", target=target)
        )

    for source, target in affordable_tunnel_extend_targets(state, actor):
        actions.append(
            Action(
                actor=actor,
                action_type="tunnel_extend",
                source=source,
                target=target,
            )
        )

    for target in affordable_tunnel_raid_targets(state, actor):
        actions.append(
            Action(actor=actor, action_type="tunnel_raid", target=target)
        )

    for target in affordable_tunnel_repair_build_targets(state, actor):
        for field_type in _TUNNEL_FIELD_TYPES:
            actions.append(
                Action(
                    actor=actor,
                    action_type="repair_build",
                    target=target,
                    field_type=field_type,  # type: ignore[arg-type]
                )
            )

    actions.append(Action(actor=actor, action_type="wait"))
    return actions


def _tunnel_sort_key(score: TunnelScore) -> tuple:
    coord = score.action.target
    cx = coord[0] if coord is not None else 999
    cy = coord[1] if coord is not None else 999
    return (
        -score.score,
        TUNNEL_ACTION_PRIORITY.get(score.action.action_type, 99),
        cx,
        cy,
    )


def _log_decision(
    state: GameState,
    actor: ActorId,
    scores: list[TunnelScore],
    chosen_score: TunnelScore,
    normal_baseline: float,
    log_path: Path,
) -> None:
    import json

    top_reasons = sorted(
        chosen_score.reasons,
        key=lambda r: abs(r[1]),
        reverse=True,
    )[:5]

    record: dict = {
        "round": state.round_index,
        "actor": actor,
        "policy": "utility_tunneler",
        "chosen_action": chosen_score.action.action_type,
        "chosen_score": round(chosen_score.score, 4),
        "candidate_count": len(scores),
        "best_normal_score": round(normal_baseline, 4),
        "opportunity_cost": round(chosen_score.features.opportunity_cost, 4),
        "top_candidates": [
            [s.action.action_type, round(s.score, 4)]
            for s in scores[:5]
        ],
        "top_reasons": [
            [name, round(value, 4)]
            for name, value in top_reasons
        ],
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        f.write("\n")


def choose_utility_tunneler_action(
    state: GameState,
    actor: ActorId,
    log_path: Path | None = None,
) -> Action:
    candidates = generate_tunnel_candidates(state, actor)
    normal_baseline = _get_normal_baseline(state, actor)

    scores = [
        score_tunnel_candidate(state, actor, c, normal_baseline)
        for c in candidates
    ]

    sorted_scores = sorted(scores, key=_tunnel_sort_key)
    best_tunnel = sorted_scores[0]

    if best_tunnel.score >= normal_baseline - OPPORTUNITY_COST_TOLERANCE:
        chosen = best_tunnel.action
        chosen_score = best_tunnel
    else:
        chosen = _fallback_to_normal(state, actor)
        chosen_score = best_tunnel  # log best tunnel candidate even when falling back

    if log_path is not None:
        _log_decision(state, actor, sorted_scores, chosen_score, normal_baseline, log_path)

    return chosen


def _fallback_to_normal(state: GameState, actor: ActorId) -> Action:
    return choose_best_utility_action(state, actor, BASELINE_PERSONALITY)
