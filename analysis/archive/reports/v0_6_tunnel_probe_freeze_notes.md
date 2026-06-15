# Maillon v0.6 Tunnel Probe Freeze Notes

## Status

Branch: `v0.6-tunnel-prototype`  
Tag: `v0.6-tunnel-probe-smoke`  
Freeze purpose: document the first working tunnel-aware bot and the current v0.6 tunnel mechanics before balance work starts.

This is a technical probe freeze, not a final gameplay balance freeze.

---

## Confirmed Working Modules

```text
src/maillon_v04/state.py
src/maillon_v04/tunnels.py
src/maillon_v04/tunnel_collapse.py
src/maillon_v04/tunnel_rules.py
src/maillon_v04/tunnel_actions.py
src/maillon_v04/actions.py
src/maillon_v04/bot_tunnel_probe.py
src/maillon_v04/bot.py
analysis/tunnel_action_smoke_suite.py
analysis/main_action_regression_smoke.py
analysis/runtime_matrix_compat_smoke.py
analysis/runtime_matrix.py
```

---

## Confirmed Mechanics

### Tunnel State

Cells can now carry tunnel-relevant surface state:

```text
has_tunnel_entrance: bool
collapsed: bool
level = 0 for collapsed fields
```

The game state now contains a physical tunnel graph:

```text
tunnel_edges: set[tuple[Coord, Coord]]
```

Tunnel edges are not owned. Access comes from owned active tunnel entrances.

---

## Tunnel Pressure and Collapse

Tunnel pressure is defined as the number of active tunnel edges incident to a field.

Collapse rule:

```text
pressure >= 4 -> collapsed
```

Collapse is simultaneous after tunnel-relevant actions:

```text
1. collect all collapse candidates
2. set all candidates to collapsed
3. remove all tunnel edges incident to collapsed fields
```

Collapsed fields become a special broken state:

```text
owner = None
field_type = None
level = 0
raid_shield = 0
has_tunnel_entrance = False
```

Collapsed fields are not normal neutral build targets.

---

## Implemented Tunnel Actions

### tunnel_entrance

Builds a visible surface entrance on an owned active non-collapsed field.

Current cost:

```text
1 Holz + 2 Stein
```

A tunnel entrance alone does not create a tunnel edge.

---

### tunnel_extend

Extends the tunnel graph by one adjacent edge from an actor-accessible tunnel node.

Current cost:

```text
1 Holz + 1 Stein
```

After extension, collapse is checked immediately.

---

### tunnel_raid

Performs a shield-bypassing takeover on a reachable enemy non-core surface field.

Current cost:

```text
3 Korn
```

Effects:

```text
owner changes to actor
field_type remains
level remains
raid_shield -> 0
contested_count +1
active_from_round uses normal raid cooldown logic
```

Tunnel raid does not create a tunnel entrance on the captured field.

---

### repair_build

Repairs and rebuilds a collapsed field adjacent to an active owned non-collapsed field.

Current cost:

```text
2 Holz + 2 Stein
```

Effects:

```text
collapsed = False
owner = actor
field_type = selected field type
level = 1
raid_shield = 0
has_tunnel_entrance = False
contested_count = 0
active_from_round = current round + 1
```

A freshly repaired field cannot receive a tunnel entrance in the same round.

---

## Runtime Matrix Integration

`runtime_matrix.py` now records tunnel metrics:

```text
tunnel_entrance
tunnel_extend
tunnel_raid
repair_build
tunnel_raid_takeovers
shield_bypassed
collapsed_fields_total
collapsed_fields_final
tunnel_edges_final
tunnel_nodes_final
network_components_final
largest_tunnel_component
fields_with_tunnel_entrance
max_tunnel_pressure_final
avg_tunnel_pressure_final_x100
p_tunnel_entrance / e_tunnel_entrance
p_tunnel_extend / e_tunnel_extend
p_tunnel_raid / e_tunnel_raid
p_repair_build / e_repair_build
```

Old bots still produce tunnel values of `0`, which is expected.

---

## tunnel_probe Bot

A first tunnel-aware policy exists:

```text
tunnel_probe
```

Purpose:

```text
stress/probe bot
not a balance bot
not intended as final personality
```

Confirmed behavior:

```text
- produces tunnel_entrance
- produces tunnel_extend
- produces tunnel_raid
- can trigger repair_build / collapse in tunnel_probe matchups
- runtime matrix records non-zero tunnel metrics
```

Observed weakness:

```text
tunnel_probe over-prioritizes underground play
surface control collapses too early
normal bots can dominate it quickly
```

Example from smoke matrix:

```text
phase_player_vs_tunnel_probe:
round 8, phase_player wins by domination

tunnel_probe_vs_phase_player:
round 12, phase_player wins by domination

tunnel_probe_vs_tunnel_probe:
tunnel metrics are active, including tunnel_extend, tunnel_raid and repair_build
```

---

## Design Read

The tunnel system is now technically viable.

The important design conclusion is:

```text
Tunnel must become a strategic layer on top of surface control,
not a replacement for surface control.
```

Therefore, `tunnel_probe` should remain a stress/mechanic bot.

A later real bot should be separate, likely:

```text
utility_tunneler
```

That bot should probably require:

```text
minimum surface base
minimum build/production stability
tunnel actions only after surface presence exists
tunnel raid as conversion tool
repair_build as recovery tool, not first priority
```

---

## Freeze Decision

Freeze accepted for:

```text
v0.6 tunnel actions isolated
v0.6 main action integration
v0.6 runtime tunnel metrics
v0.6 tunnel_probe smoke validation
```

Not frozen as balanced:

```text
tunnel_probe behavior
tunnel costs
collapse threshold
repair_build cost
bot action priorities
UI/terminal display
Fog-of-war / hidden tunnels
```

---

## Next Recommended Step

Proceed with 7L.2 / next design step:

```text
Design utility_tunneler as a real balance candidate
or
write a tunnel_probe report first and classify it as stress bot
```

Recommended direction:

```text
Keep tunnel_probe as stress bot.
Build utility_tunneler separately.
```
