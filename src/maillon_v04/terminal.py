from __future__ import annotations

from typing import cast

from src.maillon_v04.actions import (
    Action,
    BuildFieldType,
    affordable_build_targets,
    affordable_core_upgrade_targets,
    affordable_field_upgrade_targets,
    affordable_raid_targets,
    affordable_rebuild_targets,
    apply_action,
)
from src.maillon_v04.bot import BotPolicy
from src.maillon_v04.board import Coord
from src.maillon_v04.engine import GameConfig, GameEngine
from src.maillon_v04.rules import (
    build_cost_holz,
    core_upgrade_cost_stein,
    field_upgrade_cost_stein,
    raid_cost_korn,
    rebuild_cost_holz,
)
from src.maillon_v04.state import ActorId, GameState


FIELD_TYPE_CHOICES: tuple[BuildFieldType, ...] = ("Holz", "Stein", "Korn")

END_TURN = object()
QUIT_GAME = object()


def input_int(prompt: str, *, default: int | None = None) -> int:
    while True:
        raw = input(prompt).strip()

        if raw == "" and default is not None:
            return default

        try:
            return int(raw)
        except ValueError:
            print("Bitte eine Zahl eingeben.")


def choose_from_numbered_list(
    title: str,
    items: list[tuple[str, object]],
) -> object | None:
    if not items:
        print(f"{title}: keine gültigen Optionen.")
        return None

    print()
    print(title)

    for index, (label, _value) in enumerate(items, start=1):
        print(f"[{index}] {label}")

    print("[0] Zurück")

    while True:
        choice = input_int("> ")

        if choice == 0:
            return None

        if 1 <= choice <= len(items):
            return items[choice - 1][1]

        print("Ungültige Auswahl.")


def choose_field_type() -> BuildFieldType | None:
    items: list[tuple[str, object]] = [
        ("Holz", "Holz"),
        ("Stein", "Stein"),
        ("Korn", "Korn"),
    ]

    value = choose_from_numbered_list("Feldtyp wählen", items)

    if value is None:
        return None

    return cast(BuildFieldType, value)


def coord_label(state: GameState, coord: Coord) -> str:
    cell = state.cell(coord)

    owner = cell.owner if cell.owner is not None else "neutral"
    field_type = cell.field_type if cell.field_type is not None else "leer"
    active = "aktiv" if state.is_active(coord) else f"instabil bis R{cell.active_from_round}"

    return (
        f"{coord} | {owner} | {field_type} L{cell.level} | "
        f"{active} | contested={cell.contested_count}"
    )


def print_header() -> None:
    print()
    print("=" * 72)
    print("MAILLON v0.4 TERMINAL PROTOTYPE")
    print("=" * 72)


def print_status(engine: GameEngine) -> None:
    state = engine.state
    summary = engine.status_summary()

    print()
    print("-" * 72)
    print(f"Runde: {summary['round']} | Board: {summary['board_size']} Felder")
    print(f"Sieger: {summary['winner']}")
    print("-" * 72)

    for actor in ("player", "enemy"):
        actor_state = state.actor_state(cast(ActorId, actor))
        print()
        print(actor.upper())
        print(f"Kontrollierte Felder: {state.controlled_count(cast(ActorId, actor))}")
        print(f"Nicht-Core-Felder:    {state.non_core_controlled_count(cast(ActorId, actor))}")
        print(
            "Ressourcen: "
            f"Holz {actor_state.resources['Holz']}/{actor_state.caps['Holz']} | "
            f"Stein {actor_state.resources['Stein']}/{actor_state.caps['Stein']} | "
            f"Korn {actor_state.resources['Korn']}/{actor_state.caps['Korn']}"
        )

    print()


def print_owned_fields(state: GameState, actor: ActorId = "player") -> None:
    print()
    print(f"{actor.upper()} FELDER")
    print("-" * 72)

    for coord in state.owned_cells(actor):
        print(coord_label(state, coord))


def print_front_targets(state: GameState, actor: ActorId = "player") -> None:
    print()
    print(f"{actor.upper()} AKTIONSÜBERSICHT")
    print("-" * 72)

    print(f"Build-Ziele:         {len(affordable_build_targets(state, actor))}")
    print(f"Raid-Ziele:          {len(affordable_raid_targets(state, actor))}")
    print(f"Rebuild-Ziele:       {len(affordable_rebuild_targets(state, actor))}")
    print(f"Field-Upgrade-Ziele: {len(affordable_field_upgrade_targets(state, actor))}")
    print(f"Core-Upgrade-Ziele:  {len(affordable_core_upgrade_targets(state, actor))}")


def build_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_build_targets(state, actor)
    cost = build_cost_holz(state, actor)

    items: list[tuple[str, object]] = [
        (f"{coord_label(state, coord)} | Kosten: {cost} Holz", coord)
        for coord in targets
    ]

    target = choose_from_numbered_list("Build-Ziel wählen", items)

    if target is None:
        return None

    field_type = choose_field_type()

    if field_type is None:
        return None

    return Action(
        actor=actor,
        action_type="build",
        target=cast(Coord, target),
        field_type=field_type,
    )


def raid_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_raid_targets(state, actor)

    items: list[tuple[str, object]] = [
        (
            f"{coord_label(state, coord)} | Kosten: {raid_cost_korn(state, actor, coord)} Korn",
            coord,
        )
        for coord in targets
    ]

    target = choose_from_numbered_list("Raid-Ziel wählen", items)

    if target is None:
        return None

    return Action(
        actor=actor,
        action_type="raid",
        target=cast(Coord, target),
    )


def rebuild_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_rebuild_targets(state, actor)
    cost = rebuild_cost_holz(state, actor)

    items: list[tuple[str, object]] = [
        (f"{coord_label(state, coord)} | Kosten: {cost} Holz", coord)
        for coord in targets
    ]

    target = choose_from_numbered_list("Rebuild-Ziel wählen", items)

    if target is None:
        return None

    field_type = choose_field_type()

    if field_type is None:
        return None

    return Action(
        actor=actor,
        action_type="rebuild",
        target=cast(Coord, target),
        field_type=field_type,
    )


def field_upgrade_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_field_upgrade_targets(state, actor)
    cost = field_upgrade_cost_stein(state, actor)

    items: list[tuple[str, object]] = [
        (f"{coord_label(state, coord)} | Kosten: {cost} Stein", coord)
        for coord in targets
    ]

    target = choose_from_numbered_list("Field-Upgrade-Ziel wählen", items)

    if target is None:
        return None

    return Action(
        actor=actor,
        action_type="field_upgrade",
        target=cast(Coord, target),
    )


def core_upgrade_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_core_upgrade_targets(state, actor)
    cost = core_upgrade_cost_stein(state, actor)

    items: list[tuple[str, object]] = [
        (f"{coord_label(state, coord)} | Kosten: {cost} Stein", coord)
        for coord in targets
    ]

    target = choose_from_numbered_list("Core-Upgrade-Ziel wählen", items)

    if target is None:
        return None

    return Action(
        actor=actor,
        action_type="core_upgrade",
        target=cast(Coord, target),
    )



def player_available_counts(state: GameState) -> dict[str, int]:
    return {
        "build": len(affordable_build_targets(state, "player")),
        "raid": len(affordable_raid_targets(state, "player")),
        "rebuild": len(affordable_rebuild_targets(state, "player")),
        "field_upgrade": len(affordable_field_upgrade_targets(state, "player")),
        "core_upgrade": len(affordable_core_upgrade_targets(state, "player")),
    }


def print_player_action_header(engine: GameEngine, action_number: int) -> dict[str, int]:
    state = engine.state
    player = state.actor_state("player")
    counts = player_available_counts(state)

    print()
    print(f"Spieleraktion {action_number}/{engine.config.actions_per_turn}")
    print(
        "Ressourcen: "
        f"Holz {player.resources['Holz']}/{player.caps['Holz']} | "
        f"Stein {player.resources['Stein']}/{player.caps['Stein']} | "
        f"Korn {player.resources['Korn']}/{player.caps['Korn']}"
    )
    print(
        "Möglich: "
        f"Build {counts['build']} | "
        f"Raid {counts['raid']} | "
        f"Rebuild {counts['rebuild']} | "
        f"Upgrade {counts['field_upgrade']} | "
        f"Core {counts['core_upgrade']}"
    )

    return counts


def choose_player_action(engine: GameEngine, action_number: int) -> object:
    state = engine.state

    while True:
        counts = print_player_action_header(engine, action_number)

        menu: list[tuple[str, str]] = []

        if counts["build"] > 0:
            menu.append(("build", f"Build ({counts['build']})"))

        if counts["raid"] > 0:
            menu.append(("raid", f"Raid ({counts['raid']})"))

        if counts["rebuild"] > 0:
            menu.append(("rebuild", f"Rebuild ({counts['rebuild']})"))

        if counts["field_upgrade"] > 0:
            menu.append(("field_upgrade", f"Field Upgrade ({counts['field_upgrade']})"))

        if counts["core_upgrade"] > 0:
            menu.append(("core_upgrade", f"Core Upgrade ({counts['core_upgrade']})"))

        for index, (_key, label) in enumerate(menu, start=1):
            print(f"[{index}] {label}")

        print("[6] Status")
        print("[7] Eigene Felder")
        print("[8] Aktionsübersicht")
        print("[9] Zug beenden")
        print("[0] Partie abbrechen")

        if not menu:
            print("Keine ausführbare Aktion verfügbar. Du kannst Status prüfen oder den Zug beenden.")

        choice = input_int("> ")

        if choice == 0:
            return QUIT_GAME

        if choice == 6:
            print_status(engine)
            continue

        if choice == 7:
            print_owned_fields(state, "player")
            continue

        if choice == 8:
            print_front_targets(state, "player")
            continue

        if choice == 9:
            return END_TURN

        if 1 <= choice <= len(menu):
            key = menu[choice - 1][0]

            if key == "build":
                action = build_action_from_input(state, "player")
                if action is None:
                    continue
                return action

            if key == "raid":
                action = raid_action_from_input(state, "player")
                if action is None:
                    continue
                return action

            if key == "rebuild":
                action = rebuild_action_from_input(state, "player")
                if action is None:
                    continue
                return action

            if key == "field_upgrade":
                action = field_upgrade_action_from_input(state, "player")
                if action is None:
                    continue
                return action

            if key == "core_upgrade":
                action = core_upgrade_action_from_input(state, "player")
                if action is None:
                    continue
                return action

        print("Ungültige Auswahl.")


def choose_board_side_length() -> int:
    print()
    print("Boardgröße wählen")
    print("[1] 37 Felder — Schnelltest")
    print("[2] 61 Felder — Standard")
    print("[Enter] 61 Felder")

    choice = input_int("> ", default=2)

    if choice == 1:
        return 4

    return 5


def choose_bot_policy() -> BotPolicy:
    print()
    print("Gegner-Policy wählen")
    print("[1] phase_player — normaler Referenzbot")
    print("[2] rusher — aggressiver Testbot")
    print("[Enter] phase_player")

    choice = input_int("> ", default=1)

    if choice == 2:
        return "rusher"

    return "phase_player"


def run_player_phase(engine: GameEngine) -> bool:
    """
    Rückgabe:
        True, wenn weitergespielt werden soll.
        False, wenn Partie endet oder abgebrochen wird.

    Fehlgeschlagene Aktionen verbrauchen keine Aktion.
    Zurück aus einem Untermenü verbraucht ebenfalls keine Aktion.
    """

    action_number = 1

    while action_number <= engine.config.actions_per_turn:
        if engine.current_winner() is not None:
            return False

        choice = choose_player_action(engine, action_number)

        if choice is QUIT_GAME:
            print("Partie abgebrochen.")
            return False

        if choice is END_TURN:
            print("Spieler beendet den Zug.")
            return True

        action = cast(Action, choice)
        result = apply_action(engine.state, action)
        engine.add_log("player", result.message)

        print()
        print(result.message)

        if not result.ok:
            print("Aktion fehlgeschlagen. Du kannst eine andere Aktion wählen.")
            continue

        if result.winner is not None:
            print(f"SIEGER: {result.winner}")
            return False

        action_number += 1

    return True


def run_enemy_phase(engine: GameEngine) -> bool:
    if engine.current_winner() is not None:
        return False

    print()
    print("Gegnerzug")
    print("-" * 72)

    result = engine.run_bot_turn("enemy", engine.config.bot_policy)

    for action_result in result.actions:
        print(action_result.message)

    if result.stopped_by_winner:
        winner = engine.current_winner()
        print(f"SIEGER: {winner}")
        return False

    return True


def run_game() -> None:
    print_header()

    side_length = choose_board_side_length()
    bot_policy = choose_bot_policy()

    engine = GameEngine.new_game(
        GameConfig(
            side_length=side_length,
            actions_per_turn=3,
            bot_policy=bot_policy,
            max_rounds=120,
        )
    )

    print()
    print("Neues Spiel gestartet.")
    print_status(engine)

    while not engine.is_game_over():
        print()
        print("=" * 72)
        print(f"RUNDE {engine.state.round_index}")
        print("=" * 72)

        waste = engine.start_round()

        print()
        print("Produktion abgeschlossen.")
        print(f"Waste player: {waste['player']}")
        print(f"Waste enemy:  {waste['enemy']}")

        print_status(engine)

        keep_playing = run_player_phase(engine)

        if not keep_playing:
            break

        keep_playing = run_enemy_phase(engine)

        if not keep_playing:
            break

        if engine.current_winner() is None:
            engine.advance_round()

    winner = engine.current_winner()

    print()
    print("=" * 72)

    if winner is None:
        print("Spiel beendet ohne Sieger.")
    else:
        print(f"SIEGER: {winner}")

    print("=" * 72)
    print_status(engine)


def main() -> None:
    run_game()


if __name__ == "__main__":
    main()
