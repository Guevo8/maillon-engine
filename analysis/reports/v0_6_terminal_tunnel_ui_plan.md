# Maillon v0.6 Terminal Tunnel UI Plan

Stand: 04-06-2026  
Branch: `v0.6-tunnel-prototype`  
Purpose: define the next terminal/UI integration step for the v0.6 tunnel prototype.

---

## 1. Decision

Terminal/UI integration should happen before `utility_tunneler` balancing.

Reason:

```text
The tunnel rules already exist in the simulation layer,
but the player cannot yet read and operate them comfortably in the terminal UI.
```

Therefore, the next implementation block should make tunnel state and tunnel actions visible and playable in the existing terminal interface.

---

## 2. Important UX Decision

The player action menu should become more dynamic, not more crowded.

The current menu already risks overwhelming the player with too many options. Adding four tunnel actions directly as always-visible choices would make this worse.

Design decision:

```text
Only currently available actions should be shown.
Status and map should be merged.
The separate action overview should be removed or de-emphasized.
The dynamic action menu itself should communicate what is possible.
```

---

## 3. Terminal UI Principles

### 3.1 Reduce Menu Noise

Do not show unavailable actions.

Good:

```text
[1] Build (3)
[2] Tunnel (2)
[3] Status / Karte
[4] Zug beenden
[0] Partie abbrechen
```

Bad:

```text
Build
Raid
Rebuild
Field Upgrade
Fortify
Core Upgrade
Tunnel Entrance
Tunnel Extend
Tunnel Raid
Repair Build
Status
Eigene Felder
Aktionsübersicht
Karte anzeigen
Zug beenden
```

The second version exposes too many conceptual layers at once.

---

### 3.2 Group Tunnel Actions

Tunnel actions should preferably appear under one grouped menu entry:

```text
Tunnel (N)
```

Inside that submenu:

```text
Tunnel Entrance
Tunnel Extend
Tunnel Raid
Repair Build
```

This keeps the main action menu readable while still exposing the new mechanic.

---

### 3.3 Merge Status and Map

The current terminal UI has separate status, own fields, action overview and board map options.

For v0.6, status and map should be merged into one option:

```text
Status / Karte
```

This view should show:

```text
round
winner
resources
controlled fields
board map
owned fields or relevant field detail
basic tunnel legend
```

---

### 3.4 Remove or Hide Action Overview

The old action overview is less useful once the action menu becomes dynamic.

Decision:

```text
Remove it from the main menu,
or keep it as a debug-only option later.
```

The normal player should infer available actions directly from the dynamic menu.

---

## 4. Required Display Additions

Field labels should expose the minimum tunnel state.

Current label pattern:

```text
(coord) | owner | field_type Lx | active | contested=n
```

New label pattern should include:

```text
shield
collapsed
entrance
pressure
under-tunnel marker
```

Possible compact format:

```text
(-2, 0) | player | Stein L1 | aktiv | shield=0 | tunnel=E p2 | contested=1
```

Legend:

```text
E  = tunnel entrance
t  = under tunnel / incident tunnel edge
pN = tunnel pressure N
X  = collapsed
```

Collapsed fields should be unmistakable:

```text
(-1, 0) | X collapsed | repairable? | p0
```

---

## 5. Required Action Menu Changes

### 5.1 Dynamic Main Menu

The main menu should be generated from available action groups.

Suggested main groups:

```text
Build / Expand
Attack / Raid
Develop / Upgrade
Tunnel
Status / Karte
Zug beenden
Partie abbrechen
```

Only groups with available actions should appear, except status/end/quit.

---

### 5.2 Tunnel Submenu

Tunnel submenu should only show available tunnel actions.

Possible structure:

```text
Tunnelaktionen
[1] Eingang bauen (2)
[2] Tunnel erweitern (5)
[3] Tunnel-Raid (1)
[4] Repair-Build (1)
[0] Zurück
```

Each action then uses a numbered target list.

---

### 5.3 tunnel_extend Input

`tunnel_extend` is the only special input case because it needs source and target.

Do not ask the user to manually type both coordinates.

Use numbered pairs:

```text
[1] (-2, 0) -> (-1, 0)
[2] (-2, 0) -> (-2, 1)
[3] (-1, 0) -> (0, 0)
```

This reduces input errors and keeps behavior deterministic.

---

## 6. Required Code Areas

Primary file:

```text
src/maillon_v04/terminal.py
```

Relevant functions to modify:

```text
coord_label
print_status
print_front_targets
player_available_counts
print_player_action_header
choose_player_action
choose_bot_policy
```

New functions likely needed:

```text
tunnel_entrance_action_from_input
tunnel_extend_action_from_input
tunnel_raid_action_from_input
repair_build_action_from_input
choose_tunnel_action_from_input
print_status_and_map
```

Imports likely needed from `actions.py`:

```text
affordable_tunnel_entrance_targets
affordable_tunnel_extend_targets
affordable_tunnel_raid_targets
affordable_tunnel_repair_build_targets
```

Imports likely needed from tunnel modules:

```text
tunnel_pressure
is_under_tunnel
```

Costs likely needed from `tunnel_rules.py`:

```text
tunnel_entrance_cost
tunnel_extend_cost
tunnel_raid_cost
repair_build_cost
```

---

## 7. Implementation Order

### 7M.1 Display only

First add tunnel information to labels and status/map output.

No new player actions yet.

Goal:

```text
The player can see entrances, pressure and collapsed fields.
```

---

### 7M.2 Dynamic counts and action grouping

Add grouped action counts, including tunnel counts.

Goal:

```text
The UI knows whether Tunnel should appear as an action group.
```

---

### 7M.3 Tunnel submenu and input functions

Add tunnel action input functions and submenu.

Goal:

```text
The player can manually execute tunnel_entrance, tunnel_extend, tunnel_raid and repair_build.
```

---

### 7M.4 Main menu cleanup

Refactor main menu so it does not become overloaded.

Decisions:

```text
Dynamic action groups only.
Status and map merged.
Action overview removed or hidden.
```

---

### 7M.5 Enemy policy selection

Add tunnel-aware enemy option:

```text
tunnel_probe
```

Optional later:

```text
utility_balancer
utility_opportunist
utility_tunneler
```

---

## 8. What Not To Do Yet

Do not implement `utility_tunneler` before the terminal UI can display and operate tunnel mechanics.

Do not balance tunnel costs only from CSV results before manual terminal playtesting.

Do not add fog-of-war or hidden tunnel rules yet.

Do not over-polish the terminal UI. The target is readable technical playability, not final UX.

---

## 9. Next Step

Proceed with:

```text
7M.1 Terminal display: coord_label + status/map tunnel markers
```

After display works, continue with dynamic menu grouping and tunnel input functions.
