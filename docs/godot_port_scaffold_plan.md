# Scaffold Plan: maillon-godot

This document outlines the proposed file and folder structure for the `maillon-godot` repository.

## Project Configuration & Constraints
- **Godot Version**: 4.7-stable (`project.godot`)
- **Rendering Method**: Mobile (`rendering/renderer/rendering_method="mobile"`)
- **Language**: Typed GDScript (`enable_static_type_hint=true`)
- **Board Visualization**: 3D Hex Grid (`Node3D`, `MeshInstance3D`, spatial camera), no 2D TileMap.
- **Core Domain Architecture**: Pure logic classes derive from `RefCounted`. `Node` derived classes are strictly used for scene tree hierarchy, controllers, and view presentation.
- **Runtime Dependencies**: Self-contained GDScript engine. No Python dependency at runtime.
- **Fixtures**: JSON fixtures copied from `Guevo8/maillon-engine` commit `0c9c4bd550e681273c9e5b33ae12c1d3e7a2551e`.
- **First Port Scope**: Surface rules only (no tunnel actions or tunnel collapse in phase 1).

---

## Folder & File Structure Overview

```
maillon-godot/
├── project.godot
├── README.md
├── .gitignore
├── addons/
│   └── gdUnit4/                               # Unit testing framework for Godot 4
├── fixtures/                                  # Reference fixtures from maillon-engine (commit 0c9c4bd550e681273c9e5b33ae12c1d3e7a2551e)
│   ├── apply_build_v1.json
│   ├── domination_win_v1.json
│   ├── initial_state_v1.json
│   ├── phase_order_even_v1.json
│   ├── phase_order_odd_v1.json
│   ├── phase_player_decision_v1.json
│   ├── production_v1.json
│   ├── raid_vs_shield_v1.json
│   ├── surface_action_sandbox_v1.json
│   └── territory_win_v1.json
├── scripts/
│   ├── core/                                  # Pure RefCounted Domain Models & Logic
│   │   ├── hex_coord.gd
│   │   ├── game_enums.gd
│   │   ├── cell_state.gd
│   │   ├── actor_state.gd
│   │   ├── game_state.gd
│   │   ├── action_data.gd
│   │   ├── surface_rules.gd
│   │   ├── surface_legal_actions.gd
│   │   ├── bot_policy.gd
│   │   └── turn_engine.gd
│   ├── controllers/                           # Node-based Controllers & Orchestrators
│   │   ├── game_controller.gd
│   │   └── input_controller.gd
│   ├── view/                                  # 3D Presentation & Visual Nodes
│   │   ├── hex_board_3d.gd
│   │   ├── hex_tile_3d.gd
│   │   ├── actor_unit_3d.gd
│   │   └── board_camera_3d.gd
│   └── ui/                                    # Control UI Presentation Nodes
│       ├── hud_view.gd
│       ├── action_picker_ui.gd
│       └── game_over_ui.gd
├── scenes/
│   ├── main.tscn                              # Main game scene combining UI, 3D Board, and Controller
│   ├── components/
│   │   ├── hex_tile_3d.tscn                   # 3D Hex Tile Mesh/Scene
│   │   └── actor_unit_3d.tscn                 # 3D Actor Unit/Structure Mesh/Scene
│   └── ui/
│       ├── hud_view.tscn                      # Resource HUD and Round Indicators
│       ├── action_picker_ui.tscn              # Action selection UI buttons
│       └── game_over_ui.tscn                  # Game over overlay
├── assets/
│   ├── materials/                             # 3D Shaders and StandardMaterial3D resources
│   │   ├── hex_tile_mat.tres
│   │   ├── owner_player_mat.tres
│   │   └── owner_enemy_mat.tres
│   └── meshes/                                # Mesh Resources (.tres / .blend / .obj)
│       └── hex_prism.tres
└── tests/                                     # Automated GdUnit4 Tests & Fixture Runners
    ├── unit/
    │   ├── test_hex_coord.gd
    │   ├── test_surface_rules.gd
    │   └── test_surface_legal_actions.gd
    └── integration/
        └── test_fixture_regression.gd
```

---

## Step-by-Step Scaffold Plan & Component Responsibilities

### Step 1: Project Base Setup & Configuration
1. **`project.godot`**
   - Configures project settings for Godot 4.7-stable.
   - Sets `rendering/renderer/rendering_method="mobile"`.
   - Enables typed GDScript linting warnings (`debug/gdscript/warnings/enable_static_type_hint=true`).
   - Registers main scene entry point (`application/run/main_scene="res://scenes/main.tscn"`).

2. **`fixtures/`**
   - Stores raw JSON test fixtures copied from `maillon-engine` commit `0c9c4bd550e681273c9e5b33ae12c1d3e7a2551e`.
   - Used by test runners to ensure 1:1 rule regression compatibility with Python engine.

---

### Step 2: Core Domain Layer (`scripts/core/`) - RefCounted Logic
*All core domain models inherit strictly from `RefCounted`. They contain zero `Node` dependency and run deterministically.*

1. **`scripts/core/hex_coord.gd` (`RefCounted`)**
   - Represents axial hex coordinates `(q: int, r: int)`.
   - Calculates cubic `s` coordinate (`-q - r`), axial distance, neighbor coordinates, and canonical coordinate sorting.

2. **`scripts/core/game_enums.gd` (`RefCounted`)**
   - Declares statically typed enums for actors (`PLAYER`, `ENEMY`, `NONE`), field types (`HOLZ`, `STEIN`, `KORN`, `UNSET`), action types (`BUILD`, `RAID`, `FORTIFY`, `REBUILD`, `FIELD_UPGRADE`, `CORE_UPGRADE`, `WAIT`), and win conditions.

3. **`scripts/core/cell_state.gd` (`RefCounted`)**
   - Data container for individual hex cell state (`coord: HexCoord`, `owner: GameEnums.Actor`, `field_type: GameEnums.FieldType`, `level: int`, `active_from_round: int`, `contested_count: int`, `raid_shield: int`).

4. **`scripts/core/actor_state.gd` (`RefCounted`)**
   - Tracks resource balances (`holz`, `stein`, `korn`) and storage capacities (`cap_holz`, `cap_stein`, `cap_korn`) for a given player/actor.

5. **`scripts/core/game_state.gd` (`RefCounted`)**
   - Holds overall game state (`round_index: int`, `cells: Dictionary[HexCoord, CellState]`, `actors: Dictionary[GameEnums.Actor, ActorState]`, `side_length: int`).
   - Provides deep copy (`duplicate_state()`) method for legal action calculation and bot simulation.

6. **`scripts/core/action_data.gd` (`RefCounted`)**
   - Data structure encapsulating a chosen action (`actor`, `action_type`, `target_coord`, `field_type`, `source_coord`).
   - Includes canonical sorting comparator according to fixture schema specification.

7. **`scripts/core/surface_rules.gd` (`RefCounted`)**
   - Pure functional implementation of Maillon surface rules:
     - Resource production calculation and cap waste calculation (`apply_production()`).
     - Action validation and state transition (`apply_action()`).
     - Territory control evaluation and victory condition check (`check_winner()`).

8. **`scripts/core/surface_legal_actions.gd` (`RefCounted`)**
   - Generates all canonical legal surface actions (`get_legal_surface_actions(state: GameState, actor: GameEnums.Actor) -> Array[ActionData]`).
   - Checks adjacency, resource costs, level limits, and phase rules.

9. **`scripts/core/bot_policy.gd` (`RefCounted`)**
   - Evaluates state and selects actions for computer opponents (e.g., `phase_player` policy).

10. **`scripts/core/turn_engine.gd` (`RefCounted`)**
    - Manages turn phase ordering (`phase_order` calculation based on round index parity), turn progression, action execution, and end-of-turn production steps.

---

### Step 3: View Presentation Layer (`scripts/view/` & `scenes/components/`) - 3D Visuals
*3D presentation logic using Node3D nodes to render the hex grid in 3D space.*

1. **`scripts/view/hex_board_3d.gd` (`Node3D`)**
   - Spawns and manages 3D visual hex tiles based on `GameState`.
   - Converts axial hex coordinates `(q, r)` into 3D world space positions `(x, y, z)`.

2. **`scripts/view/hex_tile_3d.gd` (`Node3D`)**
   - Renders individual hex tile using `MeshInstance3D`.
   - Updates visual state (owner color materials, field type mesh indicators, shield icons, level indicators).
   - Emits mouse click / hover signals for input selection.

3. **`scripts/view/board_camera_3d.gd` (`Camera3D`)**
   - Controls 3D camera positioning, pan, zoom, and framing over the hex board.

---

### Step 4: UI Presentation Layer (`scripts/ui/` & `scenes/ui/`) - 2D HUD
*Control nodes for UI controls and overlays.*

1. **`scripts/ui/hud_view.gd` (`Control`)**
   - Displays resource totals (Holz, Stein, Korn), storage caps, current round index, and active actor turn indicators.

2. **`scripts/ui/action_picker_ui.gd` (`Control`)**
   - Contextual UI menu listing legal surface actions for the currently selected hex cell.

3. **`scripts/ui/game_over_ui.gd` (`Control`)**
   - Modal banner displayed when victory/domination condition is reached.

---

### Step 5: Controller & Orchestration Layer (`scripts/controllers/`)
*Node-based controllers linking 3D visuals, UI, and RefCounted core domain logic.*

1. **`scripts/controllers/game_controller.gd` (`Node`)**
   - Main game controller. Initializes `GameState` and `TurnEngine`.
   - Listens to player input and bot decision events, invokes `SurfaceRules.apply_action()`, updates core state, and notifies `HexBoard3D` and `HUDView` to re-render.

2. **`scripts/controllers/input_controller.gd` (`Node`)**
   - Handles Raycasting from `Camera3D` through screen coordinates to detect selected 3D hex tiles, passing selection to `GameController`.

---

### Step 6: Test Suite & Fixture Regression (`tests/`)
*Automated verification suite validating GDScript implementation against Python reference fixtures.*

1. **`tests/integration/test_fixture_regression.gd` (`GdUnitTestSuite`)**
   - Loads JSON fixtures from `fixtures/`.
   - Validates `initial_state`, `phase_order`, `surface_legal_actions`, `apply_action`, `production`, and victory states against Python reference output.
