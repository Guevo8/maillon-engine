# Maillon v0.4 Terminal Runtime

## Status

The Maillon v0.4 terminal runtime is the current playable reference prototype for the analyzed v0.4 rule core.

It is not the final UI and not a Godot/Web implementation. Its purpose is to make the v0.4 rules playable, inspectable, and testable from Termux or a normal Python terminal.

## Start

Run from the repository root:

    python -m src.maillon_v04.terminal

Default setup:

- Board: 61 fields
- Actions per turn: 3
- Bot policy: phase_player
- Win condition: 60% territory control

The 61-field board uses a 60% win threshold of 37 controlled fields.

## Runtime Modules

The v0.4 runtime is split into core logic and clients:

    src/maillon_v04/
      board.py        # Hex board, coordinates, neighbors, distance
      state.py        # GameState, CellState, ActorState
      rules.py        # Costs, production, caps, win threshold
      actions.py      # Legal targets and action execution
      bot.py          # Runtime bot policies
      engine.py       # Round loop, production, turns
      render.py       # Text board rendering
      terminal.py     # Playable terminal client
      run_logging.py  # Local run export / snapshots
      run_report.py   # Compact report from local run logs

## Controls

During a player turn, the terminal displays only currently executable actions.

Typical menu entries:

    Build
    Raid
    Rebuild
    Field Upgrade
    Core Upgrade
    Status
    Eigene Felder
    Aktionsübersicht
    Karte anzeigen
    Zug beenden
    Partie abbrechen

Only legal and affordable gameplay actions are shown in the action list.

Status and overview entries remain available for inspection.

## Board Map

The terminal client includes an on-demand board view.

Use:

    Karte anzeigen

The compact map uses two-character tokens:

    PC = Player Core
    EC = Enemy Core
    PH = Player Holz
    PS = Player Stein
    PK = Player Korn
    EH = Enemy Holz
    ES = Enemy Stein
    EK = Enemy Korn
    .. = neutral

Lowercase tokens indicate unstable / inactive fields after raid or rebuild cooldown.

Example:

    r= 0 PC PH .. .. .. .. .. EH EC

## Core Rules Implemented

Current implemented v0.4 rule core:

- Fixed hex board
- 37-field quick board option
- 61-field standard board option
- 3 actions per turn
- Resources: Holz, Stein, Korn
- Resource caps
- Core Level 2 cap upgrade
- Build
- Raid
- Rebuild
- Field Upgrade
- Direct Takeover
- Field instability after Raid
- Tiered Build costs
- Tiered Field Upgrade costs
- 60% territory win condition
- Runtime bot policies: phase_player, rusher

## Current Non-Goals

The terminal runtime does not currently include:

- Godot implementation
- Web UI
- Full Textual UI client
- Clickable board
- Real fog of war
- Core Level 3
- Repair / stabilization action
- Save/load menu
- Multiplayer
- Final balancing

## Local Run Logging

The terminal runtime writes local playtest artifacts to:

    runs/
      latest_state.json
      latest_run.jsonl
      latest_summary.json

These files are ignored by Git and are intended for local analysis.

### latest_state.json

Current snapshot of the latest run.

Contains:

- round
- winner
- board metadata
- actor resources/caps
- controlled field counts
- all cell states

### latest_run.jsonl

Event log of the latest run.

Contains event types such as:

    game_start
    production
    action_result
    game_summary

This file is useful for debugging, replay-style analysis, and later UI/data bridges.

### latest_summary.json

Compact final summary of the latest run.

Contains:

- run ID
- final round
- winner
- stop reason
- player/enemy territory
- final resources
- board size
- 60% threshold

## Run Report

After a playtest, generate a compact report:

    python -m src.maillon_v04.run_report

Optional shorter recent action block:

    python -m src.maillon_v04.run_report --recent 5

The report summarizes:

- run ID
- event count
- first/last round
- winner
- action counts
- actor action counts
- production events
- resource waste
- final territory
- final resources
- recent actions

## Development Role

This runtime is the playable reference client for Maillon v0.4.

It should remain stable while future UI experiments are developed separately.

Recommended separation:

    terminal.py      = playable reference client
    textual_app.py   = experimental UI spike / visual client
    run_logging.py   = export bridge
    run_report.py    = local analysis utility

The rule core should remain UI-independent so that future clients can reuse the same game logic.

## Recommended Next Steps

1. Complete one full playthrough to victory.
2. Run python -m src.maillon_v04.run_report.
3. Review action balance, waste, round count, and win timing.
4. Only then decide whether the next iteration should focus on:
   - terminal polish,
   - Textual UI,
   - bot policy tuning,
   - balance changes,
   - or documentation cleanup.
