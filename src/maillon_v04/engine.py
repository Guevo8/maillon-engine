from __future__ import annotations

from dataclasses import dataclass, field

from src.maillon_v04.actions import Action, ActionResult, apply_action
from src.maillon_v04.bot import BotPolicy, choose_bot_action
from src.maillon_v04.rules import apply_production, winner_by_territory
from src.maillon_v04.state import ActorId, GameState, ResourceName, create_initial_state


@dataclass(frozen=True)
class GameConfig:
    """
    Konfiguration für eine v0.4-Partie.

    side_length:
        4 = 37 Felder
        5 = 61 Felder

    actions_per_turn:
        v0.4 Kandidat: 3

    bot_policy:
        Default: phase_player
    """

    side_length: int = 5
    actions_per_turn: int = 3
    bot_policy: BotPolicy = "phase_player"
    max_rounds: int = 120


@dataclass
class EngineLogEntry:
    round_index: int
    actor: ActorId | str
    message: str


@dataclass
class ActorTurnResult:
    actor: ActorId
    actions: list[ActionResult] = field(default_factory=list)

    @property
    def stopped_by_winner(self) -> bool:
        return any(result.winner is not None for result in self.actions)


@dataclass
class RoundResult:
    round_index: int
    production_waste: dict[ActorId, dict[ResourceName, int]]
    player_turn: ActorTurnResult | None = None
    enemy_turn: ActorTurnResult | None = None
    winner: ActorId | None = None


@dataclass
class GameEngine:
    config: GameConfig
    state: GameState
    log: list[EngineLogEntry] = field(default_factory=list)

    @classmethod
    def new_game(cls, config: GameConfig | None = None) -> "GameEngine":
        if config is None:
            config = GameConfig()

        state = create_initial_state(config.side_length)

        return cls(
            config=config,
            state=state,
        )

    def add_log(self, actor: ActorId | str, message: str) -> None:
        self.log.append(
            EngineLogEntry(
                round_index=self.state.round_index,
                actor=actor,
                message=message,
            )
        )

    def current_winner(self) -> ActorId | None:
        return winner_by_territory(self.state)

    def is_game_over(self) -> bool:
        if self.current_winner() is not None:
            return True

        return self.state.round_index > self.config.max_rounds

    def initiative_first_actor(self) -> ActorId:
        """
        v0.4 alternating initiative for bot-vs-bot analysis.

        Odd rounds:  player acts first.
        Even rounds: enemy acts first.
        """

        if self.state.round_index % 2 == 1:
            return "player"

        return "enemy"

    def start_round(self) -> dict[ActorId, dict[ResourceName, int]]:
        """
        Führt die Produktion zu Beginn der Runde aus.

        Rückgabe:
            Waste je Actor/Ressource.
        """

        waste = apply_production(self.state)

        self.add_log("system", f"Round {self.state.round_index} production resolved.")

        return waste

    def run_actor_actions(
        self,
        actor: ActorId,
        actions: list[Action],
    ) -> ActorTurnResult:
        """
        Führt bis zu actions_per_turn Aktionen eines Akteurs aus.

        Für Spieleraktionen wird die Liste vom Terminal kommen.
        Für Botaktionen gibt es run_bot_turn().
        """

        result = ActorTurnResult(actor=actor)

        for action_index, action in enumerate(actions[: self.config.actions_per_turn], start=1):
            if self.current_winner() is not None:
                break

            action_result = apply_action(self.state, action)
            result.actions.append(action_result)

            self.add_log(actor, f"Action {action_index}/{self.config.actions_per_turn}: {action_result.message}")

            if action_result.winner is not None:
                break

        return result

    def run_bot_turn(
        self,
        actor: ActorId = "enemy",
        policy: BotPolicy | None = None,
    ) -> ActorTurnResult:
        """
        Führt einen vollständigen Bot-Zug aus.

        Der Bot wählt jede Aktion neu anhand des aktuellen GameState.
        """

        if policy is None:
            policy = self.config.bot_policy

        result = ActorTurnResult(actor=actor)

        for action_index in range(1, self.config.actions_per_turn + 1):
            if self.current_winner() is not None:
                break

            action = choose_bot_action(self.state, actor=actor, policy=policy)
            action_result = apply_action(self.state, action)
            result.actions.append(action_result)

            self.add_log(actor, f"Bot action {action_index}/{self.config.actions_per_turn}: {action_result.message}")

            if action_result.winner is not None:
                break

        return result

    def advance_round(self) -> None:
        self.state.round_index += 1
        self.add_log("system", f"Advanced to round {self.state.round_index}.")

    def run_round(
        self,
        player_actions: list[Action],
    ) -> RoundResult:
        """
        Führt eine vollständige Runde aus:

        1. Produktion
        2. Spieleraktionen
        3. Gegnerbot-Aktionen
        4. Siegcheck
        5. Rundenvorschub, falls kein Sieger

        Hinweis:
            Das Terminal muss später player_actions erzeugen.
        """

        if self.is_game_over():
            return RoundResult(
                round_index=self.state.round_index,
                production_waste={
                    "player": {"Holz": 0, "Stein": 0, "Korn": 0},
                    "enemy": {"Holz": 0, "Stein": 0, "Korn": 0},
                },
                winner=self.current_winner(),
            )

        round_index = self.state.round_index
        production_waste = self.start_round()

        player_turn = self.run_actor_actions("player", player_actions)
        winner = self.current_winner()

        enemy_turn: ActorTurnResult | None = None

        if winner is None:
            enemy_turn = self.run_bot_turn("enemy", self.config.bot_policy)
            winner = self.current_winner()

        result = RoundResult(
            round_index=round_index,
            production_waste=production_waste,
            player_turn=player_turn,
            enemy_turn=enemy_turn,
            winner=winner,
        )

        if winner is None:
            self.advance_round()

        return result

    def run_bot_vs_bot_round(
        self,
        player_policy: BotPolicy = "phase_player",
        enemy_policy: BotPolicy | None = None,
    ) -> RoundResult:
        """
        Debug-/Smoke-Test:
        Lässt beide Seiten per Bot handeln.
        Nützlich, bevor terminal.py existiert.
        """

        if enemy_policy is None:
            enemy_policy = self.config.bot_policy

        if self.is_game_over():
            return RoundResult(
                round_index=self.state.round_index,
                production_waste={
                    "player": {"Holz": 0, "Stein": 0, "Korn": 0},
                    "enemy": {"Holz": 0, "Stein": 0, "Korn": 0},
                },
                winner=self.current_winner(),
            )

        round_index = self.state.round_index
        production_waste = self.start_round()

        first_actor = self.initiative_first_actor()

        player_turn: ActorTurnResult | None = None
        enemy_turn: ActorTurnResult | None = None

        if first_actor == "player":
            player_turn = self.run_bot_turn("player", player_policy)
            winner = self.current_winner()

            if winner is None:
                enemy_turn = self.run_bot_turn("enemy", enemy_policy)
                winner = self.current_winner()

        else:
            enemy_turn = self.run_bot_turn("enemy", enemy_policy)
            winner = self.current_winner()

            if winner is None:
                player_turn = self.run_bot_turn("player", player_policy)
                winner = self.current_winner()

        result = RoundResult(
            round_index=round_index,
            production_waste=production_waste,
            player_turn=player_turn,
            enemy_turn=enemy_turn,
            winner=winner,
        )

        if winner is None:
            self.advance_round()

        return result

    def status_summary(self) -> dict[str, object]:
        """
        Kompakter Status für Tests und später terminal.py.
        """

        player = self.state.actor_state("player")
        enemy = self.state.actor_state("enemy")

        return {
            "round": self.state.round_index,
            "board_size": self.state.board.size,
            "winner": self.current_winner(),
            "player": {
                "controlled": self.state.controlled_count("player"),
                "non_core": self.state.non_core_controlled_count("player"),
                "resources": dict(player.resources),
                "caps": dict(player.caps),
            },
            "enemy": {
                "controlled": self.state.controlled_count("enemy"),
                "non_core": self.state.non_core_controlled_count("enemy"),
                "resources": dict(enemy.resources),
                "caps": dict(enemy.caps),
            },
        }
