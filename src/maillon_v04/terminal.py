from __future__ import annotations

from typing import cast

from src.maillon_v04.actions import (
    Action,
    BuildFieldType,
    affordable_build_targets,
    affordable_core_upgrade_targets,
    affordable_field_upgrade_targets,
    affordable_fortify_targets,
    affordable_raid_targets,
    affordable_rebuild_targets,
    affordable_tunnel_entrance_targets,
    affordable_tunnel_extend_targets,
    affordable_tunnel_raid_targets,
    affordable_tunnel_repair_build_targets,
    apply_action,
)
from src.maillon_v04.bot import BotPolicy
from src.maillon_v04.board import Coord
from src.maillon_v04.engine import GameConfig, GameEngine
from src.maillon_v04.render import render_board_with_legend
from src.maillon_v04.run_logging import RunLogger
from src.maillon_v04.rules import (
    build_cost_holz,
    core_upgrade_cost_stein,
    field_upgrade_cost_stein,
    fortify_cost_korn,
    raid_cost_korn,
    rebuild_cost_holz,
)
from src.maillon_v04.state import ActorId, GameState
from src.maillon_v04.tunnel_rules import (
    repair_build_cost,
    tunnel_entrance_cost,
    tunnel_extend_cost,
    tunnel_raid_cost,
)
from src.maillon_v04.tunnels import is_under_tunnel, tunnel_pressure


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


def tunnel_marker_for_coord(state: GameState, coord: Coord) -> str:
    cell = state.cell(coord)
    pressure = tunnel_pressure(state, coord)

    if cell.collapsed:
        return f"X p{pressure}"

    markers: list[str] = []

    if cell.has_tunnel_entrance:
        markers.append("E")
    elif is_under_tunnel(state, coord):
        markers.append("t")
    else:
        markers.append("-")

    if pressure > 0:
        markers.append(f"p{pressure}")

    return " ".join(markers)


def tunnel_overview_label(state: GameState) -> str:
    coords = list(state.cells.keys())
    collapsed = sum(1 for coord in coords if state.cell(coord).collapsed)
    entrances = sum(1 for coord in coords if state.cell(coord).has_tunnel_entrance)
    under_tunnel = sum(1 for coord in coords if is_under_tunnel(state, coord))
    max_pressure = max((tunnel_pressure(state, coord) for coord in coords), default=0)

    return (
        f"Tunnel: edges={len(state.tunnel_edges)} | "
        f"under={under_tunnel} | entrances={entrances} | "
        f"collapsed={collapsed} | max_pressure={max_pressure}"
    )


def print_tunnel_legend() -> None:
    print("Tunnel-Legende: E=Eingang | t=untertunnelt | pN=Druck | X=collapsed")


def coord_label(state: GameState, coord: Coord) -> str:
    cell = state.cell(coord)
    tunnel = tunnel_marker_for_coord(state, coord)

    if cell.collapsed:
        return (
            f"{coord} | X collapsed | tunnel={tunnel} | "
            f"shield={cell.raid_shield} | contested={cell.contested_count}"
        )

    owner = cell.owner if cell.owner is not None else "neutral"
    field_type = cell.field_type if cell.field_type is not None else "leer"
    active = "aktiv" if state.is_active(coord) else f"instabil bis R{cell.active_from_round}"

    return (
        f"{coord} | {owner} | {field_type} L{cell.level} | "
        f"{active} | shield={cell.raid_shield} | "
        f"tunnel={tunnel} | contested={cell.contested_count}"
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
    print(tunnel_overview_label(state))
    print_tunnel_legend()
    print()


def print_owned_fields(state: GameState, actor: ActorId = "player") -> None:
    print()
    print(f"{actor.upper()} FELDER")
    print("-" * 72)

    for coord in state.owned_cells(actor):
        print(coord_label(state, coord))


def print_front_targets(state: GameState, actor: ActorId = "player") -> None:
    print()
    print(f"{actor.upper()} DEBUG-AKTIONSÜBERSICHT")
    print("-" * 72)

    print(f"Build-Ziele:            {len(affordable_build_targets(state, actor))}")
    print(f"Raid-Ziele:             {len(affordable_raid_targets(state, actor))}")
    print(f"Rebuild-Ziele:          {len(affordable_rebuild_targets(state, actor))}")
    print(f"Field-Upgrade-Ziele:    {len(affordable_field_upgrade_targets(state, actor))}")
    print(f"Fortify-Ziele:          {len(affordable_fortify_targets(state, actor))}")
    print(f"Core-Upgrade-Ziele:     {len(affordable_core_upgrade_targets(state, actor))}")
    print(f"Tunnel-Entrance-Ziele:  {len(affordable_tunnel_entrance_targets(state, actor))}")
    print(f"Tunnel-Extend-Ziele:    {len(affordable_tunnel_extend_targets(state, actor))}")
    print(f"Tunnel-Raid-Ziele:      {len(affordable_tunnel_raid_targets(state, actor))}")
    print(f"Repair-Build-Ziele:     {len(affordable_tunnel_repair_build_targets(state, actor))}")


def print_board_map(engine: GameEngine) -> None:
    print()
    print(render_board_with_legend(engine.state))
    print()
    print(tunnel_overview_label(engine.state))
    print_tunnel_legend()
    print()


def print_status_and_map(engine: GameEngine) -> None:
    print_status(engine)
    print_board_map(engine)


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


def fortify_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_fortify_targets(state, actor)

    items: list[tuple[str, object]] = [
        (
            f"{coord_label(state, coord)} | Schutz={state.cell(coord).raid_shield}/3 "
            f"| Kosten: {fortify_cost_korn(state, actor, coord)} Korn",
            coord,
        )
        for coord in targets
    ]

    target = choose_from_numbered_list("Fortify-Ziel wählen", items)

    if target is None:
        return None

    return Action(
        actor=actor,
        action_type="fortify",
        target=cast(Coord, target),
    )



def cost_label(costs: dict[str, int]) -> str:
    return " + ".join(
        f"{amount} {resource}"
        for resource, amount in costs.items()
        if amount > 0
    )


def tunnel_entrance_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_tunnel_entrance_targets(state, actor)
    cost = tunnel_entrance_cost(state, actor)

    items: list[tuple[str, object]] = [
        (f"{coord_label(state, coord)} | Kosten: {cost_label(cost)}", coord)
        for coord in targets
    ]

    target = choose_from_numbered_list("Tunnel-Eingang bauen", items)

    if target is None:
        return None

    return Action(
        actor=actor,
        action_type="tunnel_entrance",
        target=cast(Coord, target),
    )


def tunnel_extend_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_tunnel_extend_targets(state, actor)
    cost = tunnel_extend_cost(state, actor)

    items: list[tuple[str, object]] = [
        (
            f"{source} -> {target} | "
            f"Quelle: {coord_label(state, source)} | "
            f"Ziel: {coord_label(state, target)} | "
            f"Kosten: {cost_label(cost)}",
            (source, target),
        )
        for source, target in targets
    ]

    pair = choose_from_numbered_list("Tunnel erweitern", items)

    if pair is None:
        return None

    source, target = cast(tuple[Coord, Coord], pair)

    return Action(
        actor=actor,
        action_type="tunnel_extend",
        source=source,
        target=target,
    )


def tunnel_raid_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_tunnel_raid_targets(state, actor)
    cost = tunnel_raid_cost(state, actor)

    items: list[tuple[str, object]] = [
        (
            f"{coord_label(state, coord)} | Shield-Bypass | Kosten: {cost_label(cost)}",
            coord,
        )
        for coord in targets
    ]

    target = choose_from_numbered_list("Tunnel-Raid-Ziel wählen", items)

    if target is None:
        return None

    return Action(
        actor=actor,
        action_type="tunnel_raid",
        target=cast(Coord, target),
    )


def repair_build_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    targets = affordable_tunnel_repair_build_targets(state, actor)
    cost = repair_build_cost(state, actor)

    items: list[tuple[str, object]] = [
        (f"{coord_label(state, coord)} | Kosten: {cost_label(cost)}", coord)
        for coord in targets
    ]

    target = choose_from_numbered_list("Repair-Build-Ziel wählen", items)

    if target is None:
        return None

    field_type = choose_field_type()

    if field_type is None:
        return None

    return Action(
        actor=actor,
        action_type="repair_build",
        target=cast(Coord, target),
        field_type=field_type,
    )


def choose_tunnel_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    counts = {
        "tunnel_entrance": len(affordable_tunnel_entrance_targets(state, actor)),
        "tunnel_extend": len(affordable_tunnel_extend_targets(state, actor)),
        "tunnel_raid": len(affordable_tunnel_raid_targets(state, actor)),
        "repair_build": len(affordable_tunnel_repair_build_targets(state, actor)),
    }

    menu: list[tuple[str, str]] = []

    if counts["tunnel_entrance"] > 0:
        menu.append(("tunnel_entrance", f"Tunnel-Eingang bauen ({counts['tunnel_entrance']})"))

    if counts["tunnel_extend"] > 0:
        menu.append(("tunnel_extend", f"Tunnel erweitern ({counts['tunnel_extend']})"))

    if counts["tunnel_raid"] > 0:
        menu.append(("tunnel_raid", f"Tunnel-Raid ({counts['tunnel_raid']})"))

    if counts["repair_build"] > 0:
        menu.append(("repair_build", f"Repair-Build ({counts['repair_build']})"))

    selected = choose_from_numbered_list("Tunnelaktionen", [(label, key) for key, label in menu])

    if selected is None:
        return None

    key = cast(str, selected)

    if key == "tunnel_entrance":
        return tunnel_entrance_action_from_input(state, actor)

    if key == "tunnel_extend":
        return tunnel_extend_action_from_input(state, actor)

    if key == "tunnel_raid":
        return tunnel_raid_action_from_input(state, actor)

    if key == "repair_build":
        return repair_build_action_from_input(state, actor)

    return None



def choose_develop_action_from_input(state: GameState, actor: ActorId) -> Action | None:
    counts = {
        "rebuild": len(affordable_rebuild_targets(state, actor)),
        "field_upgrade": len(affordable_field_upgrade_targets(state, actor)),
        "fortify": len(affordable_fortify_targets(state, actor)),
        "core_upgrade": len(affordable_core_upgrade_targets(state, actor)),
    }

    menu: list[tuple[str, str]] = []

    if counts["rebuild"] > 0:
        menu.append(("rebuild", f"Rebuild ({counts['rebuild']})"))

    if counts["field_upgrade"] > 0:
        menu.append(("field_upgrade", f"Field Upgrade ({counts['field_upgrade']})"))

    if counts["fortify"] > 0:
        menu.append(("fortify", f"Fortify ({counts['fortify']})"))

    if counts["core_upgrade"] > 0:
        menu.append(("core_upgrade", f"Core Upgrade ({counts['core_upgrade']})"))

    selected = choose_from_numbered_list("Develop / Upgrade", [(label, key) for key, label in menu])

    if selected is None:
        return None

    key = cast(str, selected)

    if key == "rebuild":
        return rebuild_action_from_input(state, actor)

    if key == "field_upgrade":
        return field_upgrade_action_from_input(state, actor)

    if key == "fortify":
        return fortify_action_from_input(state, actor)

    if key == "core_upgrade":
        return core_upgrade_action_from_input(state, actor)

    return None



def player_available_counts(state: GameState) -> dict[str, int]:
    counts = {
        "build": len(affordable_build_targets(state, "player")),
        "raid": len(affordable_raid_targets(state, "player")),
        "rebuild": len(affordable_rebuild_targets(state, "player")),
        "field_upgrade": len(affordable_field_upgrade_targets(state, "player")),
        "fortify": len(affordable_fortify_targets(state, "player")),
        "core_upgrade": len(affordable_core_upgrade_targets(state, "player")),
        "tunnel_entrance": len(affordable_tunnel_entrance_targets(state, "player")),
        "tunnel_extend": len(affordable_tunnel_extend_targets(state, "player")),
        "tunnel_raid": len(affordable_tunnel_raid_targets(state, "player")),
        "repair_build": len(affordable_tunnel_repair_build_targets(state, "player")),
    }

    counts["group_build"] = counts["build"]
    counts["group_attack"] = counts["raid"]
    counts["group_develop"] = (
        counts["rebuild"]
        + counts["field_upgrade"]
        + counts["fortify"]
        + counts["core_upgrade"]
    )
    counts["group_tunnel"] = (
        counts["tunnel_entrance"]
        + counts["tunnel_extend"]
        + counts["tunnel_raid"]
        + counts["repair_build"]
    )
    counts["group_total"] = (
        counts["group_build"]
        + counts["group_attack"]
        + counts["group_develop"]
        + counts["group_tunnel"]
    )

    return counts


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
        f"Build {counts['group_build']} | "
        f"Attack {counts['group_attack']} | "
        f"Develop {counts['group_develop']} | "
        f"Tunnel {counts['group_tunnel']}"
    )

    if counts["group_tunnel"] > 0:
        print(
            "Tunnel: "
            f"Entrance {counts['tunnel_entrance']} | "
            f"Extend {counts['tunnel_extend']} | "
            f"Raid {counts['tunnel_raid']} | "
            f"Repair {counts['repair_build']}"
        )

    return counts


def choose_player_action(engine: GameEngine, action_number: int) -> object:
    state = engine.state

    while True:
        counts = print_player_action_header(engine, action_number)

        menu: list[tuple[str, str]] = []

        if counts["group_build"] > 0:
            menu.append(("build", f"Build / Expand ({counts['group_build']})"))

        if counts["group_attack"] > 0:
            menu.append(("attack", f"Attack / Raid ({counts['group_attack']})"))

        if counts["group_develop"] > 0:
            menu.append(("develop", f"Develop / Upgrade ({counts['group_develop']})"))

        if counts["group_tunnel"] > 0:
            menu.append(("tunnel", f"Tunnel ({counts['group_tunnel']})"))

        menu.append(("status_map", "Status / Karte"))
        menu.append(("end_turn", "Zug beenden"))
        menu.append(("quit", "Partie abbrechen"))

        for index, (_key, label) in enumerate(menu, start=1):
            print(f"[{index}] {label}")

        choice = input_int("> ")

        if not (1 <= choice <= len(menu)):
            print("Ungültige Auswahl.")
            continue

        key = menu[choice - 1][0]

        if key == "quit":
            return QUIT_GAME

        if key == "end_turn":
            return END_TURN

        if key == "status_map":
            print_status_and_map(engine)
            continue

        if key == "build":
            action = build_action_from_input(state, "player")
            if action is None:
                continue
            return action

        if key == "attack":
            action = raid_action_from_input(state, "player")
            if action is None:
                continue
            return action

        if key == "develop":
            action = choose_develop_action_from_input(state, "player")
            if action is None:
                continue
            return action

        if key == "tunnel":
            action = choose_tunnel_action_from_input(state, "player")
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
    print("[3] tunnel_probe — Tunnel-Stressbot / Mechaniktest")
    print("[Enter] phase_player")

    while True:
        choice = input_int("> ", default=1)

        if choice == 1:
            return "phase_player"

        if choice == 2:
            return "rusher"

        if choice == 3:
            return "tunnel_probe"

        print("Ungültige Auswahl.")


def run_player_phase(engine: GameEngine, logger: RunLogger | None = None) -> bool:
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

        if logger is not None:
            logger.append_action_result(engine, result)

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


def run_enemy_phase(engine: GameEngine, logger: RunLogger | None = None) -> bool:
    if engine.current_winner() is not None:
        return False

    print()
    print("Gegnerzug")
    print("-" * 72)

    result = engine.run_bot_turn("enemy", engine.config.bot_policy)

    for action_result in result.actions:
        print(action_result.message)

        if logger is not None:
            logger.append_action_result(engine, action_result)

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

    logger = RunLogger.create(engine)

    print()
    print("Neues Spiel gestartet.")
    print(f"Run-Log: {logger.latest_run_path}")
    print(f"Latest State: {logger.latest_state_path}")
    print_status(engine)

    while not engine.is_game_over():
        print()
        print("=" * 72)
        print(f"RUNDE {engine.state.round_index}")
        print("=" * 72)

        waste = engine.start_round()
        logger.append_production(engine, waste)

        print()
        print("Produktion abgeschlossen.")
        print(f"Waste player: {waste['player']}")
        print(f"Waste enemy:  {waste['enemy']}")

        print_status(engine)

        keep_playing = run_player_phase(engine, logger)

        if not keep_playing:
            break

        keep_playing = run_enemy_phase(engine, logger)

        if not keep_playing:
            break

        if engine.current_winner() is None:
            engine.advance_round()
            logger.write_latest_state(engine)

    winner = engine.current_winner()

    logger.write_summary(
        engine,
        reason="winner" if winner is not None else "stopped_without_winner",
    )
    logger.write_latest_state(engine)

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
