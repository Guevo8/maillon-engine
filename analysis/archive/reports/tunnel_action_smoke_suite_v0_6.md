# Maillon v0.6 Tunnel Action Smoke Suite

## Status

Smoke suite passed locally after adding the isolated v0.6 tunnel action set.

This report documents the intended coverage of:

```text
analysis/tunnel_action_smoke_suite.py
```

The suite is intentionally lightweight. It is not a full test framework yet, but it gives a reproducible command-line validation layer before the tunnel actions are integrated into the main action pipeline.

---

## Covered Modules

```text
src/maillon_v04/tunnels.py
src/maillon_v04/tunnel_collapse.py
src/maillon_v04/tunnel_rules.py
src/maillon_v04/tunnel_actions.py
analysis/tunnel_action_smoke_suite.py
```

---

## Covered Rule Cases

### 1. tunnel_entrance

The suite verifies that a player can build a visible tunnel entrance on an owned, active, non-collapsed field if resources are available.

Expected effects:

- `has_tunnel_entrance = True`
- tunnel entrance cost is paid
- the same field is removed from later tunnel entrance candidates
- no tunnel edge is created by the entrance alone

---

### 2. tunnel_extend

The suite verifies that an isolated tunnel entrance can start a tunnel network.

Expected effects:

- actor-owned entrance becomes a tunnel access node
- `tunnel_extend` creates one active tunnel edge
- pressure on source and target becomes `1`
- both source and target become reachable through the tunnel network

---

### 3. tunnel_extend collapse

The suite verifies that repeated tunnel extension can trigger immediate collapse.

Expected behavior:

- first three incident edges on the center field do not collapse it
- fourth incident edge triggers collapse immediately
- collapsed field state is applied
- incident tunnel edges are removed
- pressure on the collapsed field returns to `0`

Expected collapsed field state:

- `collapsed = True`
- `owner = None`
- `field_type = None`
- `level = 0`
- `raid_shield = 0`
- `has_tunnel_entrance = False`

---

### 4. tunnel_raid

The suite verifies shield-bypassing tunnel raid behavior.

Expected behavior:

- target must be an enemy non-core field reachable through the actor's tunnel network
- target shield is bypassed
- actor pays 3 Korn
- target owner changes to actor
- `field_type` remains unchanged
- `level` remains unchanged
- `raid_shield` becomes `0`
- no tunnel entrance is created on the target
- tunnel edge remains after the raid

---

### 5. repair_build

The suite verifies the collapsed-field recovery action.

Expected behavior:

- target must be collapsed
- target must be adjacent to an active owned non-collapsed field
- actor pays repair_build cost
- field is restored and claimed
- selected field type is built
- `level = 1`
- `raid_shield = 0`
- `has_tunnel_entrance = False`
- `active_from_round = current round + 1`
- repaired field is not a same-round tunnel entrance target

---

## Run Commands

```bash
python -m py_compile \
  src/maillon_v04/tunnels.py \
  src/maillon_v04/tunnel_collapse.py \
  src/maillon_v04/tunnel_rules.py \
  src/maillon_v04/tunnel_actions.py \
  analysis/tunnel_action_smoke_suite.py

python analysis/tunnel_action_smoke_suite.py
```

Expected final line:

```text
RESULT: tunnel action smoke suite OK
```

---

## Design Read

The isolated tunnel action layer is now coherent enough to proceed, but it is still not wired into the normal runtime engine.

Current confirmed design properties:

- tunnel entrance is a surface feature,
- tunnel network is a physical graph,
- collapse is pressure-based and immediate,
- tunnel raid is a precise shield-bypass action,
- repair_build restores collapsed fields using normal activation delay.

---

## Next Recommended Step

Proceed with runtime integration planning before changing bots.

Recommended order:

```text
7F.2 pull + confirm report
7F.3 tag isolated smoke-suite state
7G.1 integrate tunnel action types into main Action / ActionType model
7G.2 integrate affordable target summaries
7G.3 extend runtime metrics
7G.4 only then add bot scoring
```

The tunnel system should remain isolated until the main action pipeline can run the smoke suite and existing v0.5 matrices without regression.
