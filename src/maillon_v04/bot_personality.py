from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .state import GameState


BotPersonality = Literal[
    "rusher",
    "economist",
    "fortifier",
    "balancer",
    "aggro_turtle",
    "opportunist",
]

GamePhase = Literal["early", "mid", "late"]


PERSONALITY_IDS: tuple[BotPersonality, ...] = (
    "rusher",
    "economist",
    "fortifier",
    "balancer",
    "aggro_turtle",
    "opportunist",
)

GAME_PHASES: tuple[GamePhase, ...] = (
    "early",
    "mid",
    "late",
)


@dataclass(frozen=True, slots=True)
class PersonalityWeights:
    """
    Gewichtungsvektor für einen Utility-Bot.

    Diese Werte entscheiden noch keine Aktion direkt.
    Sie gewichten später nur die Bewertungskategorien einer gemeinsamen
    Utility-Funktion.

    expansion:
        Wert von Ausbreitung / neuen Feldern.

    economy:
        Wert von Ressourcenaufbau und Ressourcen-Effizienz.

    defense:
        Wert von Fortify, Frontschutz und Stabilisierung.

    aggression:
        Wert von Raids und offensivem Druck.

    development:
        Wert von Core Upgrade, Field Upgrade und Rebuild.
    """

    expansion: float
    economy: float
    defense: float
    aggression: float
    development: float


PERSONALITY_WEIGHTS: dict[BotPersonality, dict[GamePhase, PersonalityWeights]] = {
    "rusher": {
        "early": PersonalityWeights(
            expansion=1.65,
            economy=0.55,
            defense=0.35,
            aggression=1.70,
            development=0.60,
        ),
        "mid": PersonalityWeights(
            expansion=1.30,
            economy=0.70,
            defense=0.45,
            aggression=1.80,
            development=0.75,
        ),
        "late": PersonalityWeights(
            expansion=0.90,
            economy=0.80,
            defense=0.50,
            aggression=1.90,
            development=0.85,
        ),
    },
    "economist": {
        "early": PersonalityWeights(
            expansion=1.25,
            economy=1.70,
            defense=0.80,
            aggression=0.65,
            development=1.55,
        ),
        "mid": PersonalityWeights(
            expansion=1.10,
            economy=1.75,
            defense=1.05,
            aggression=0.80,
            development=1.60,
        ),
        "late": PersonalityWeights(
            expansion=0.85,
            economy=1.65,
            defense=1.20,
            aggression=1.00,
            development=1.40,
        ),
    },
    "fortifier": {
        # 6E.1 tuned1: Fortifier soll defensiv bleiben, aber nicht mehr in
        # passiven Fortify-/Rebuild-Schleifen stecken. Defense bleibt über
        # Durchschnitt, Economy/Development werden gedämpft, Expansion und
        # Counter-Raid steigen über die Phasen an.
        "early": PersonalityWeights(
            expansion=1.25,
            economy=0.95,
            defense=1.35,
            aggression=0.90,
            development=0.95,
        ),
        "mid": PersonalityWeights(
            expansion=1.15,
            economy=0.85,
            defense=1.45,
            aggression=1.15,
            development=1.00,
        ),
        "late": PersonalityWeights(
            expansion=1.05,
            economy=0.75,
            defense=1.50,
            aggression=1.35,
            development=1.05,
        ),
    },
    "balancer": {
        "early": PersonalityWeights(
            expansion=1.25,
            economy=1.20,
            defense=1.00,
            aggression=1.05,
            development=1.10,
        ),
        "mid": PersonalityWeights(
            expansion=1.15,
            economy=1.25,
            defense=1.15,
            aggression=1.20,
            development=1.20,
        ),
        "late": PersonalityWeights(
            expansion=1.00,
            economy=1.30,
            defense=1.25,
            aggression=1.25,
            development=1.15,
        ),
    },
    "aggro_turtle": {
        "early": PersonalityWeights(
            expansion=1.50,
            economy=1.10,
            defense=1.45,
            aggression=1.25,
            development=0.95,
        ),
        "mid": PersonalityWeights(
            expansion=1.25,
            economy=1.15,
            defense=1.60,
            aggression=1.50,
            development=1.20,
        ),
        "late": PersonalityWeights(
            expansion=0.95,
            economy=1.20,
            defense=1.70,
            aggression=1.45,
            development=1.25,
        ),
    },
    "opportunist": {
        "early": PersonalityWeights(
            expansion=1.30,
            economy=1.15,
            defense=0.90,
            aggression=1.35,
            development=1.05,
        ),
        "mid": PersonalityWeights(
            expansion=1.20,
            economy=1.30,
            defense=1.10,
            aggression=1.60,
            development=1.25,
        ),
        "late": PersonalityWeights(
            expansion=1.05,
            economy=1.35,
            defense=1.20,
            aggression=1.70,
            development=1.30,
        ),
    },
}


def phase_for_round(round_index: int) -> GamePhase:
    """
    Einfache v0.5-Alpha-Phasendefinition.

    Diese Definition ist bewusst vorläufig und rundenbasiert.
    Später kann sie durch board- und kontaktbasierte Phasen ergänzt werden.
    """

    if round_index <= 7:
        return "early"

    if round_index <= 14:
        return "mid"

    return "late"


def get_game_phase(state: GameState) -> GamePhase:
    return phase_for_round(state.round_index)


def normalize_personality(value: str) -> BotPersonality:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")

    if normalized not in PERSONALITY_IDS:
        valid = ", ".join(PERSONALITY_IDS)
        raise ValueError(f"unknown bot personality: {value!r}. valid: {valid}")

    return normalized  # type: ignore[return-value]


def get_personality_weights(
    personality: BotPersonality | str,
    phase: GamePhase,
) -> PersonalityWeights:
    normalized = normalize_personality(personality)

    if phase not in GAME_PHASES:
        valid = ", ".join(GAME_PHASES)
        raise ValueError(f"unknown game phase: {phase!r}. valid: {valid}")

    return PERSONALITY_WEIGHTS[normalized][phase]


def get_weights_for_state(
    state: GameState,
    personality: BotPersonality | str,
) -> PersonalityWeights:
    return get_personality_weights(
        personality=personality,
        phase=get_game_phase(state),
    )


def personality_table_rows() -> list[dict[str, object]]:
    """
    Flache Tabellenform für spätere CSV-/Markdown-Ausgaben.
    """

    rows: list[dict[str, object]] = []

    for personality in PERSONALITY_IDS:
        for phase in GAME_PHASES:
            weights = PERSONALITY_WEIGHTS[personality][phase]

            rows.append(
                {
                    "personality": personality,
                    "phase": phase,
                    "expansion": weights.expansion,
                    "economy": weights.economy,
                    "defense": weights.defense,
                    "aggression": weights.aggression,
                    "development": weights.development,
                }
            )

    return rows
