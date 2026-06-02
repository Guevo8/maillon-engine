from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.maillon_v04.actions import ActionResult
from src.maillon_v04.board import Coord
from src.maillon_v04.engine import GameEngine
from src.maillon_v04.rules import territory_threshold_60


RUNS_DIR = Path("runs")


def utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_utc")


def coord_to_json(coord: Coord | None) -> list[int] | None:
    if coord is None:
        return None

    return [coord[0], coord[1]]


def json_dump(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def jsonl_append(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, sort_keys=True))
        f.write("\n")


@dataclass
class RunLogger:
    run_id: str
    run_dir: Path
    event_index: int = 0

    @classmethod
    def create(cls, engine: GameEngine, run_dir: Path | str = RUNS_DIR) -> "RunLogger":
        logger = cls(
            run_id=utc_run_id(),
            run_dir=Path(run_dir),
        )

        logger.run_dir.mkdir(parents=True, exist_ok=True)

        # latest_run.jsonl soll pro Spiel neu beginnen.
        if logger.latest_run_path.exists():
            logger.latest_run_path.unlink()

        logger.write_event(
            engine,
            "game_start",
            {
                "config": asdict(engine.config),
                "message": "Maillon v0.4 terminal run started.",
            },
        )
        logger.write_latest_state(engine)

        return logger

    @property
    def latest_state_path(self) -> Path:
        return self.run_dir / "latest_state.json"

    @property
    def latest_run_path(self) -> Path:
        return self.run_dir / "latest_run.jsonl"

    @property
    def latest_summary_path(self) -> Path:
        return self.run_dir / "latest_summary.json"

    def write_event(self, engine: GameEngine, event_type: str, payload: dict[str, Any]) -> None:
        self.event_index += 1

        event = {
            "run_id": self.run_id,
            "event_index": self.event_index,
            "round": engine.state.round_index,
            "event_type": event_type,
            "payload": payload,
        }

        jsonl_append(self.latest_run_path, event)

    def write_latest_state(self, engine: GameEngine) -> None:
        json_dump(self.latest_state_path, serialize_engine_state(engine, self.run_id))

    def append_production(
        self,
        engine: GameEngine,
        waste: dict[str, dict[str, int]],
    ) -> None:
        self.write_event(
            engine,
            "production",
            {
                "waste": waste,
                "player_resources": dict(engine.state.actor_state("player").resources),
                "enemy_resources": dict(engine.state.actor_state("enemy").resources),
            },
        )
        self.write_latest_state(engine)

    def append_action_result(self, engine: GameEngine, result: ActionResult) -> None:
        action = result.action

        self.write_event(
            engine,
            "action_result",
            {
                "ok": result.ok,
                "actor": action.actor,
                "action_type": action.action_type,
                "target": coord_to_json(action.target),
                "field_type": action.field_type,
                "message": result.message,
                "winner": result.winner,
                "player_controlled": engine.state.controlled_count("player"),
                "enemy_controlled": engine.state.controlled_count("enemy"),
                "player_resources": dict(engine.state.actor_state("player").resources),
                "enemy_resources": dict(engine.state.actor_state("enemy").resources),
            },
        )
        self.write_latest_state(engine)

    def write_summary(self, engine: GameEngine, reason: str) -> None:
        summary = {
            "run_id": self.run_id,
            "reason": reason,
            "round": engine.state.round_index,
            "winner": engine.current_winner(),
            "board_size": engine.state.board.size,
            "territory_threshold_60": territory_threshold_60(engine.state),
            "player": {
                "controlled": engine.state.controlled_count("player"),
                "non_core": engine.state.non_core_controlled_count("player"),
                "resources": dict(engine.state.actor_state("player").resources),
                "caps": dict(engine.state.actor_state("player").caps),
            },
            "enemy": {
                "controlled": engine.state.controlled_count("enemy"),
                "non_core": engine.state.non_core_controlled_count("enemy"),
                "resources": dict(engine.state.actor_state("enemy").resources),
                "caps": dict(engine.state.actor_state("enemy").caps),
            },
            "config": asdict(engine.config),
            "latest_state_path": str(self.latest_state_path),
            "latest_run_path": str(self.latest_run_path),
        }

        json_dump(self.latest_summary_path, summary)

        self.write_event(
            engine,
            "game_summary",
            summary,
        )


def serialize_engine_state(engine: GameEngine, run_id: str | None = None) -> dict[str, Any]:
    state = engine.state

    cells = []

    for coord in sorted(state.cells):
        cell = state.cell(coord)

        cells.append(
            {
                "coord": coord_to_json(coord),
                "owner": cell.owner,
                "field_type": cell.field_type,
                "level": cell.level,
                "active_from_round": cell.active_from_round,
                "active": state.is_active(coord),
                "contested_count": cell.contested_count,
            }
        )

    return {
        "run_id": run_id,
        "round": state.round_index,
        "winner": engine.current_winner(),
        "board": {
            "side_length": state.board.side_length,
            "radius": state.board.radius,
            "size": state.board.size,
            "territory_threshold_60": territory_threshold_60(state),
            "player_core": coord_to_json(state.player_core),
            "enemy_core": coord_to_json(state.enemy_core),
        },
        "config": asdict(engine.config),
        "actors": {
            "player": {
                "controlled": state.controlled_count("player"),
                "non_core": state.non_core_controlled_count("player"),
                "resources": dict(state.actor_state("player").resources),
                "caps": dict(state.actor_state("player").caps),
            },
            "enemy": {
                "controlled": state.controlled_count("enemy"),
                "non_core": state.non_core_controlled_count("enemy"),
                "resources": dict(state.actor_state("enemy").resources),
                "caps": dict(state.actor_state("enemy").caps),
            },
        },
        "cells": cells,
    }
