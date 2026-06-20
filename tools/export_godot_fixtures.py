#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.maillon_v04.actions import (
    Action,
    affordable_build_targets,
    affordable_core_upgrade_targets,
    affordable_field_upgrade_targets,
    affordable_fortify_targets,
    affordable_raid_targets,
    affordable_rebuild_targets,
    apply_action,
)
from src.maillon_v04.bot_legacy import choose_phase_player_action
from src.maillon_v04.engine import GameConfig, GameEngine
from src.maillon_v04.rules import apply_production, territory_threshold_60
from src.maillon_v04.state import ActorId, CellState, GameState, create_initial_state


SCHEMA_VERSION = 1

FIELD_TYPES = (
    "Holz",
    "Stein",
    "Korn",
)

ACTION_ORDER = (
    "build",
    "raid",
    "fortify",
    "rebuild",
    "field_upgrade",
    "core_upgrade",
    "wait",
)

ACTION_RANK = {
    name: index
    for index, name in enumerate(ACTION_ORDER)
}

FIELD_RANK = {
    name: index
    for index, name in enumerate(FIELD_TYPES)
}

NO_COORD = (10_000, 10_000)


def coord_json(coord: tuple[int, int]) -> list[int]:
    return [coord[0], coord[1]]


def action_json(action: Action) -> dict[str, Any]:
    data: dict[str, Any] = {
        "actor": action.actor,
        "action_type": action.action_type,
    }

    if action.source is not None:
        data["source"] = coord_json(action.source)

    if action.target is not None:
        data["target"] = coord_json(action.target)

    if action.field_type is not None:
        data["field_type"] = action.field_type

    return data


def cell_json(cell: CellState) -> dict[str, Any]:
    return {
        "owner": cell.owner,
        "field_type": cell.field_type,
        "level": cell.level,
        "active_from_round": cell.active_from_round,
        "contested_count": cell.contested_count,
        "raid_shield": cell.raid_shield,
        "has_tunnel_entrance": cell.has_tunnel_entrance,
        "collapsed": cell.collapsed,
    }


def actor_json(
    state: GameState,
    actor: ActorId,
) -> dict[str, Any]:
    actor_state = state.actor_state(actor)

    return {
        "resources": {
            name: actor_state.resources[name]
            for name in FIELD_TYPES
        },
        "caps": {
            name: actor_state.caps[name]
            for name in FIELD_TYPES
        },
    }


def actors_json(state: GameState) -> dict[str, Any]:
    return {
        "player": actor_json(state, "player"),
        "enemy": actor_json(state, "enemy"),
    }


def edges_json(
    edges: Iterable[
        tuple[
            tuple[int, int],
            tuple[int, int],
        ]
    ],
) -> list[list[list[int]]]:
    normalized = sorted({
        tuple(sorted(edge))
        for edge in edges
    })

    return [
        [
            coord_json(edge[0]),
            coord_json(edge[1]),
        ]
        for edge in normalized
    ]


def state_overrides(state: GameState) -> dict[str, Any]:
    baseline = create_initial_state(state.board.side_length)
    result: dict[str, Any] = {}

    if state.round_index != baseline.round_index:
        result["round_index"] = state.round_index

    cells: list[dict[str, Any]] = []

    for coord in sorted(state.cells):
        current = cell_json(state.cell(coord))
        initial = cell_json(baseline.cell(coord))

        if current != initial:
            cells.append({
                "coord": coord_json(coord),
                **current,
            })

    if cells:
        result["cells"] = cells

    actors: dict[str, Any] = {}

    for actor in ("player", "enemy"):
        current = actor_json(state, actor)
        initial = actor_json(baseline, actor)

        if current != initial:
            actors[actor] = current

    if actors:
        result["actors"] = actors

    if state.tunnel_edges:
        result["tunnel_edges"] = edges_json(
            state.tunnel_edges
        )

    return result


def action_key(
    action: Action,
) -> tuple[int, int, int, int, int, int]:
    source = (
        action.source
        if action.source is not None
        else NO_COORD
    )

    target = (
        action.target
        if action.target is not None
        else NO_COORD
    )

    return (
        ACTION_RANK.get(
            action.action_type,
            len(ACTION_RANK),
        ),
        source[0],
        source[1],
        target[0],
        target[1],
        FIELD_RANK.get(
            action.field_type,
            len(FIELD_RANK),
        ),
    )


def surface_actions(
    state: GameState,
    actor: ActorId,
) -> list[Action]:
    actions: list[Action] = []

    for target in affordable_build_targets(
        state,
        actor,
    ):
        for field_type in FIELD_TYPES:
            actions.append(
                Action(
                    actor=actor,
                    action_type="build",
                    target=target,
                    field_type=field_type,  # type: ignore[arg-type]
                )
            )

    for target in affordable_raid_targets(
        state,
        actor,
    ):
        actions.append(
            Action(
                actor=actor,
                action_type="raid",
                target=target,
            )
        )

    for target in affordable_fortify_targets(
        state,
        actor,
    ):
        actions.append(
            Action(
                actor=actor,
                action_type="fortify",
                target=target,
            )
        )

    for target in affordable_rebuild_targets(
        state,
        actor,
    ):
        old_type = state.cell(target).field_type

        for field_type in FIELD_TYPES:
            if field_type == old_type:
                continue

            actions.append(
                Action(
                    actor=actor,
                    action_type="rebuild",
                    target=target,
                    field_type=field_type,  # type: ignore[arg-type]
                )
            )

    for target in affordable_field_upgrade_targets(
        state,
        actor,
    ):
        actions.append(
            Action(
                actor=actor,
                action_type="field_upgrade",
                target=target,
            )
        )

    for target in affordable_core_upgrade_targets(
        state,
        actor,
    ):
        actions.append(
            Action(
                actor=actor,
                action_type="core_upgrade",
                target=target,
            )
        )

    actions.append(
        Action(
            actor=actor,
            action_type="wait",
        )
    )

    return sorted(
        actions,
        key=action_key,
    )


def changed_cells(
    before: GameState,
    after: GameState,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for coord in sorted(after.cells):
        before_cell = cell_json(
            before.cell(coord)
        )

        after_cell = cell_json(
            after.cell(coord)
        )

        if before_cell != after_cell:
            result.append({
                "coord": coord_json(coord),
                **after_cell,
            })

    return result


def write_fixture(
    out_dir: Path,
    fixture_id: str,
    state: GameState,
    query: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "fixture_id": fixture_id,
        "base_state": {
            "kind": "initial",
            "side_length": state.board.side_length,
        },
        "overrides": state_overrides(state),
        "query": query,
        "expected": expected,
    }

    path = out_dir / f"{fixture_id}.json"

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"wrote {path}")


def export_legal_actions(
    out_dir: Path,
    fixture_id: str,
    state: GameState,
    actor: ActorId,
) -> None:
    actions = surface_actions(
        state,
        actor,
    )

    write_fixture(
        out_dir,
        fixture_id,
        state,
        {
            "type": "legal_actions",
            "actor": actor,
        },
        {
            "actions": [
                action_json(action)
                for action in actions
            ],
        },
    )


def export_apply_action(
    out_dir: Path,
    fixture_id: str,
    state: GameState,
    action: Action,
    *,
    production_before: bool = False,
) -> None:
    before = state.clone()

    waste = (
        apply_production(state)
        if production_before
        else None
    )

    result = apply_action(
        state,
        action,
    )

    expected: dict[str, Any] = {
        "ok": result.ok,
        "winner": result.winner,
        "round_index": state.round_index,
        "actors": actors_json(state),
        "cell_changes": changed_cells(
            before,
            state,
        ),
        "tunnel_edges": edges_json(
            state.tunnel_edges
        ),
        "collapsed": [
            coord_json(coord)
            for coord in sorted(result.collapsed)
        ],
    }

    if waste is not None:
        expected["production_waste"] = waste

    write_fixture(
        out_dir,
        fixture_id,
        before,
        {
            "type": "apply_action",
            "apply_production_before": production_before,
            "action": action_json(action),
        },
        expected,
    )


def set_cell(
    state: GameState,
    coord: tuple[int, int],
    *,
    owner: ActorId | None,
    field_type: str | None,
    level: int = 1,
    raid_shield: int = 0,
) -> None:
    cell = state.cell(coord)

    cell.owner = owner
    cell.field_type = field_type  # type: ignore[assignment]
    cell.level = level
    cell.active_from_round = 1
    cell.contested_count = 0
    cell.raid_shield = raid_shield
    cell.has_tunnel_entrance = False
    cell.collapsed = False


def set_resources(
    state: GameState,
    actor: ActorId,
    *,
    holz: int,
    stein: int,
    korn: int,
    cap: int | None = None,
) -> None:
    actor_state = state.actor_state(actor)

    actor_state.resources.update({
        "Holz": holz,
        "Stein": stein,
        "Korn": korn,
    })

    if cap is not None:
        actor_state.caps.update({
            "Holz": cap,
            "Stein": cap,
            "Korn": cap,
        })


def give_connected_player_fields(
    state: GameState,
    total: int,
) -> None:
    while state.controlled_count("player") < total:
        candidates: set[tuple[int, int]] = set()

        for origin in state.active_owned_cells(
            "player"
        ):
            for neighbor in state.board.neighbors(
                origin
            ):
                if state.cell(neighbor).is_empty:
                    candidates.add(neighbor)

        if not candidates:
            raise RuntimeError(
                f"cannot reach {total} player fields"
            )

        set_cell(
            state,
            min(candidates),
            owner="player",
            field_type="Holz",
        )


def build_fixtures(out_dir: Path) -> None:
    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for old in out_dir.glob("*.json"):
        old.unlink()

    # 1. Initialzustand
    initial = create_initial_state(5)

    export_legal_actions(
        out_dir,
        "initial_state_v1",
        initial,
        "player",
    )

    # 2. Surface Action Sandbox
    sandbox = create_initial_state(5)

    set_cell(
        sandbox,
        (-2, 0),
        owner="player",
        field_type="Korn",
    )

    set_cell(
        sandbox,
        (-1, 0),
        owner="player",
        field_type="Stein",
    )

    set_cell(
        sandbox,
        (0, 0),
        owner="enemy",
        field_type="Holz",
    )

    set_resources(
        sandbox,
        "player",
        holz=6,
        stein=6,
        korn=6,
    )

    action_types = {
        action.action_type
        for action in surface_actions(
            sandbox,
            "player",
        )
    }

    if action_types != set(ACTION_ORDER):
        raise RuntimeError(
            "sandbox action types mismatch: "
            f"{sorted(action_types)}"
        )

    export_legal_actions(
        out_dir,
        "surface_action_sandbox_v1",
        sandbox,
        "player",
    )

    # 3. Build
    export_apply_action(
        out_dir,
        "apply_build_v1",
        create_initial_state(5),
        Action(
            actor="player",
            action_type="build",
            target=(-2, 0),
            field_type="Korn",
        ),
    )

    # 4. Raid gegen Shield
    raid = create_initial_state(5)

    set_cell(
        raid,
        (-1, 0),
        owner="player",
        field_type="Holz",
    )

    set_cell(
        raid,
        (0, 0),
        owner="enemy",
        field_type="Stein",
        raid_shield=2,
    )

    set_resources(
        raid,
        "player",
        holz=4,
        stein=0,
        korn=6,
    )

    export_apply_action(
        out_dir,
        "raid_vs_shield_v1",
        raid,
        Action(
            actor="player",
            action_type="raid",
            target=(0, 0),
        ),
    )

    # 5. Produktion
    production = create_initial_state(5)

    set_resources(
        production,
        "player",
        holz=5,
        stein=0,
        korn=3,
    )

    export_apply_action(
        out_dir,
        "production_v1",
        production,
        Action(
            actor="player",
            action_type="wait",
        ),
        production_before=True,
    )

    # 6. Territory-Sieg
    territory = create_initial_state(5)

    give_connected_player_fields(
        territory,
        territory_threshold_60(territory) - 1,
    )

    set_resources(
        territory,
        "player",
        holz=12,
        stein=0,
        korn=3,
        cap=12,
    )

    territory_targets = affordable_build_targets(
        territory,
        "player",
    )

    if not territory_targets:
        raise RuntimeError(
            "territory fixture has no legal build target"
        )

    export_apply_action(
        out_dir,
        "territory_win_v1",
        territory,
        Action(
            actor="player",
            action_type="build",
            target=territory_targets[0],
            field_type="Holz",
        ),
    )

    # 7. Domination-Sieg
    domination = create_initial_state(5)

    set_cell(
        domination,
        (2, 0),
        owner="player",
        field_type="Korn",
    )

    set_resources(
        domination,
        "player",
        holz=2,
        stein=0,
        korn=6,
    )

    export_apply_action(
        out_dir,
        "domination_win_v1",
        domination,
        Action(
            actor="player",
            action_type="raid",
            target=(3, 0),
        ),
    )

    # 8 und 9. Initiative
    for fixture_id, round_index in (
        ("phase_order_odd_v1", 1),
        ("phase_order_even_v1", 2),
    ):
        state = create_initial_state(5)
        state.round_index = round_index

        engine = GameEngine(
            config=GameConfig(),
            state=state,
        )

        first = engine.initiative_first_actor()
        second = (
            "enemy"
            if first == "player"
            else "player"
        )

        write_fixture(
            out_dir,
            fixture_id,
            state,
            {
                "type": "phase_order",
                "round_index": round_index,
            },
            {
                "first": first,
                "second": second,
            },
        )

    # 10. phase_player-Entscheidung
    bot_state = create_initial_state(5)

    bot_action = choose_phase_player_action(
        bot_state,
        "enemy",
    )

    write_fixture(
        out_dir,
        "phase_player_decision_v1",
        bot_state,
        {
            "type": "bot_decision",
            "actor": "enemy",
            "policy": "phase_player",
        },
        {
            "action": action_json(bot_action),
        },
    )

    files = sorted(
        out_dir.glob("*.json")
    )

    print(
        f"\nExported {len(files)} fixtures "
        f"to {out_dir}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export deterministic fixtures "
            "for the Maillon Godot port."
        )
    )

    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "port" / "fixtures",
        help="Output directory. Default: port/fixtures",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir

    if not out_dir.is_absolute():
        out_dir = (
            Path.cwd() / out_dir
        ).resolve()

    build_fixtures(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
