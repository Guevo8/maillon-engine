from __future__ import annotations

from typing import Literal

from src.maillon_v04.actions import Action
from src.maillon_v04.bot_exploit import (
    choose_opening_resource_spammer_action,
    choose_tunnel_all_in_probe_action,
)
from src.maillon_v04.bot_legacy import choose_phase_player_action, choose_rusher_action
from src.maillon_v04.bot_personality import BotPersonality, PERSONALITY_IDS
from src.maillon_v04.bot_tunnel_probe import choose_tunnel_probe_action
from src.maillon_v04.bot_utility import choose_best_utility_action
from src.maillon_v04.bot_utility_tunneler import choose_utility_tunneler_action
from src.maillon_v04.state import ActorId, GameState


BotPolicy = Literal[
    "rusher",
    "phase_player",
    "utility_balancer",
    "utility_rusher",
    "utility_economist",
    "utility_fortifier",
    "utility_aggro_turtle",
    "utility_opportunist",
    "tunnel_probe",
    "utility_tunneler",
    "opening_resource_spammer",
    "tunnel_all_in_probe",
]

UTILITY_POLICY_TO_PERSONALITY: dict[str, BotPersonality] = {
    f"utility_{personality}": personality
    for personality in PERSONALITY_IDS
}


def utility_personality_for_policy(policy: str) -> BotPersonality | None:
    return UTILITY_POLICY_TO_PERSONALITY.get(policy)


def choose_bot_action(
    state: GameState,
    actor: ActorId = "enemy",
    policy: BotPolicy = "phase_player",
) -> Action:
    if policy == "rusher":
        return choose_rusher_action(state, actor)

    if policy == "phase_player":
        return choose_phase_player_action(state, actor)

    if policy == "tunnel_probe":
        return choose_tunnel_probe_action(state, actor)

    if policy == "utility_tunneler":
        return choose_utility_tunneler_action(state, actor)

    if policy == "opening_resource_spammer":
        return choose_opening_resource_spammer_action(state, actor)

    if policy == "tunnel_all_in_probe":
        return choose_tunnel_all_in_probe_action(state, actor)

    personality = utility_personality_for_policy(policy)
    if personality is not None:
        return choose_best_utility_action(
            state=state,
            actor=actor,
            personality=personality,
        )

    raise ValueError(f"Unknown bot policy: {policy}")
