# Maillon v0.6 Tunnel Design

## Status

Draft for v0.6 planning.

This document defines the first stable design direction for the Maillon tunnel system. It is not yet an implementation spec, but it is precise enough to guide later code, tests and bot logic.

v0.6 should not reopen the v0.5 balance freeze. Tunnel mechanics are treated as a new module.

---

## Design Goal

The tunnel system should add a second strategic axis without creating a full second board.

Surface play remains about:

- field control,
- production,
- raids,
- shields,
- upgrades,
- territory victory.

Tunnel play adds:

- infiltration,
- shield bypass,
- network momentum,
- structural instability,
- collapse risk,
- repair and counterplay.

The core fantasy is:

> A player can build a visible tunnel entrance on the surface, dig an underground network, connect into existing tunnel systems, bypass fortified fields, trigger instability and use the network for sudden momentum turns.

---

## Non-Goals for v0.6.1

The first tunnel prototype should avoid the following:

- no hidden tunnels,
- no fog of war,
- no underground combat,
- no underground capture score,
- no dynamic board-size shrinking,
- no separate underground victory condition.

These may be revisited later, but v0.6.1 should stay deterministic and testable.

---

## Resolved v0.6.1 Rule Decisions

The following decisions are accepted for the first implementation pass.

1. Tunnel pressure counts active tunnel edges that are incident to a field.
2. A relevant tunnel edge is an active tunnel connection where the field is either the start coordinate or the end coordinate.
3. Tunnel pressure does not count abstract “through” edges between two other fields.
4. `COLLAPSE_THRESHOLD = 4` for the first implementation pass.
5. Collapse is checked immediately after the action that may have changed tunnel pressure.
6. Collapse pressure aggregates all active tunnel edges across the whole physical tunnel graph, regardless of who created them.
7. `TUNNEL_RAID_KORN_COST = 3` for the first implementation pass.
8. `tunnel_raid` can only target an enemy field that is actually under a reachable tunnel.
9. `is_under_tunnel(state, coord)` should use the same criterion as pressure calculation: `tunnel_pressure(state, coord) > 0`.
10. `repair_build` follows normal build activation logic.
11. A tunnel entrance requires an active owned field; therefore a freshly repaired field cannot receive a tunnel entrance until it is active under the normal activation rules.
12. When a field collapses, its `level` becomes `0`.

The numeric constants should be centralized so they can later move into `GameConfig`, a rules object or scenario JSON without rewriting action logic.

Recommended constant names:

```python
TUNNEL_RAID_KORN_COST = 3
COLLAPSE_THRESHOLD = 4
```

---

## Core Concepts

### Surface Field

A normal Maillon field still has the existing core properties:

- `owner`
- `field_type`
- `level`
- `raid_shield`
- `active`
- `collapsed`

A surface field may additionally have:

- `has_tunnel_entrance`

The tunnel entrance is a visible feature on a normal surface field.

A collapsed field is a broken special state, not a normal neutral field. For a collapsed field, implementation should set:

- `collapsed = True`
- `owner = None`
- `field_type = None`
- `level = 0`
- `raid_shield = 0`
- `has_tunnel_entrance = False`

---

### Tunnel Entrance

A tunnel entrance is not a separate field. It is a surface feature attached to an existing controlled field.

Rules:

- A tunnel entrance must be built with a separate action.
- Building a normal field does not automatically create a tunnel entrance.
- A tunnel entrance can only be built on an owned, active, non-collapsed field.
- If a field with a tunnel entrance is captured, the tunnel entrance is captured with it.
- A tunnel entrance gives access to the connected tunnel network.
- A tunnel entrance works immediately after it is built.

Design reason:

This prevents tunnels from dominating the early game and keeps the surface layer relevant.

---

### Tunnel Network

Tunnel connections form a graph underneath the existing board.

A tunnel connection is an active undirected edge between two adjacent board coordinates.

Important:

- Tunnel connections do not count as controlled fields.
- Tunnel connections do not produce resources.
- Tunnel connections do not have their own capture mechanic.
- Tunnel connections can exist under own, enemy or neutral surface fields.
- Tunnel connections can remain permanently until removed by collapse/repair logic.
- A tunnel edge is relevant to a field when the field is one of the edge endpoints.

A player can use a tunnel network if they own at least one active, non-collapsed surface field with a tunnel entrance connected to that network.

---

## Ownership and Access

Tunnel access is based on surface access, not tunnel ownership.

A player may use a connected tunnel component if:

1. the player owns a surface field,
2. that field is active,
3. that field has a tunnel entrance,
4. the field is not collapsed,
5. the tunnel entrance connects to the tunnel component.

Once connected, the player can use the reachable network, including parts originally dug by the opponent.

This creates the intended momentum effect:

> Connecting into a network can suddenly open multiple attack routes.

Implementation implication:

- Collapse and pressure use the physical aggregate tunnel graph.
- Access and action legality use the actor's reachable tunnel component.

---

## Tunnel Crossing

If a player extends a tunnel into a field where opponent tunnel connections already exist, the networks connect.

Crossing rules:

- opponent tunnels do not block extension,
- crossing does not remove opponent tunnels,
- crossing does not create underground combat,
- crossing may connect both players to the same network,
- crossing increases structural pressure,
- collapse is checked immediately after the new edge is added.

Design rule:

> Tunnel crossing means network connection, not tunnel ownership transfer.

Implementation note:

The pressure calculation must aggregate existing tunnel edges across both actors. A newly created crossing edge can push an already partially tunnelled field over the collapse threshold.

---

## Structural Pressure

Tunnel instability is physical, not ownership-based.

Every active tunnel edge contributes to structural pressure regardless of who built it.

Important rule:

> A tunnel is a tunnel. Own tunnels can collapse own fields too.

This avoids hidden capture-like logic and keeps the mechanic physically intuitive.

For v0.6.1, tunnel pressure is defined exactly as:

```text
tunnel_pressure(state, coord) = number of active tunnel edges where coord is one endpoint
```

An active tunnel edge is therefore relevant to exactly the two fields it connects.

Do not count edges that merely appear to “pass near” or “pass through” a coordinate unless the coordinate is one endpoint of that edge.

Suggested pressure model:

- 0 incident tunnel edges: stable
- 1 incident tunnel edge: tunnelled
- 2 incident tunnel edges: undermined
- 3 incident tunnel edges: unstable
- 4+ incident tunnel edges: collapsed

Ownership does not reduce pressure.

Recommended helper functions:

```python
def tunnel_pressure(state, coord) -> int: ...
def is_under_tunnel(state, coord) -> bool:
    return tunnel_pressure(state, coord) > 0
```

`is_under_tunnel` should use the exact same criterion as pressure calculation. This keeps tunnel raid legality and collapse pressure aligned.

---

## Collapse

A field collapses when structural pressure reaches the collapse threshold.

Accepted threshold for the first implementation:

```text
COLLAPSE_THRESHOLD = 4
```

Collapsed field effects:

- `collapsed = True`
- `owner = None`
- `field_type = None`
- `level = 0`
- `raid_shield = 0`
- `has_tunnel_entrance = False`
- production stops,
- field does not count as controlled,
- field cannot raid,
- field cannot fortify,
- field cannot upgrade,
- field cannot be normally built on,
- field cannot be normally raided,
- field blocks tunnel access through that coordinate,
- all incident tunnel edges are removed,
- field can only be restored with `repair_build`.

Collapse is checked immediately after the action that may change tunnel pressure. For the first implementation, this primarily means after `tunnel_extend`, but the collapse check should be reusable.

Collapsed fields are not removed from the board in v0.6.1.

The territory threshold remains stable.

---

## Repair Build

`repair_build` is a special build-like action for collapsed fields.

It combines:

- repairing,
- claiming,
- rebuilding.

Conditions:

- target field is collapsed,
- actor owns an adjacent non-collapsed surface field,
- actor can afford the repair/build cost.

Effect:

- `collapsed = False`
- `owner = actor`
- `field_type = selected field type`
- `level = 1`
- `raid_shield = 0`
- `has_tunnel_entrance = False`
- tunnel connections in the repaired field remain removed
- activation follows normal build activation logic

After repair, a new tunnel entrance must be built separately if desired.

If normal build uses an activation delay, `repair_build` should use the same activation behavior. This prevents a single turn from chaining `repair_build` into immediate `tunnel_entrance` on the repaired field.

Design reason:

This keeps collapsed fields special, but avoids a clunky multi-step neutral repair phase.

---

## Tunnel Actions

### `tunnel_entrance`

Builds a tunnel entrance on an owned surface field.

Conditions:

- actor owns the target field,
- target is active,
- target is not collapsed,
- target does not already have a tunnel entrance,
- actor can afford the cost.

Suggested cost placeholder:

```text
2 Stein + 1 Holz
```

Effect:

- target gains `has_tunnel_entrance = True`,
- entrance is usable immediately.

---

### `tunnel_extend`

Extends a tunnel from a reachable tunnel node to an adjacent coordinate.

Conditions:

- actor has access to the source tunnel node,
- target is adjacent to source,
- source is not collapsed,
- target is not collapsed,
- tunnel connection does not already exist,
- actor can afford the cost.

Suggested cost placeholder:

```text
1 Stein + 1 Holz
```

Effect:

- active tunnel edge is created between source and target,
- structural pressure updates,
- collapse checks run immediately.

Notes:

- target may be own, enemy or neutral surface field,
- target does not become captured,
- target does not become a tunnel entrance,
- tunnel extension is usable immediately if it remains non-collapsed after the collapse check.

---

### `tunnel_raid`

Uses a reachable tunnel under an enemy surface field to raid from below.

Conditions:

- actor has access to a tunnel network,
- target is an enemy-owned, non-collapsed surface field,
- target is under a tunnel by the shared `is_under_tunnel(state, target)` definition,
- target is part of the actor's reachable tunnel component,
- actor can afford the cost.

Accepted cost for the first implementation:

```text
TUNNEL_RAID_KORN_COST = 3
```

Effect:

- performs a raid against the target,
- ignores `raid_shield`,
- can capture the surface field,
- does not create a tunnel entrance,
- tunnel network remains,
- captured field keeps `field_type` and `level`,
- captured field has `raid_shield = 0`.

Design reason:

Tunnel raid should reward infiltration, but should not hand over a fully fortified field.

---

### `repair_build`

Repairs and rebuilds a collapsed field in one action.

Suggested cost placeholder:

```text
2 Holz + 2 Stein
```

Effect:

- restores the field,
- claims it,
- builds a selected field type,
- sets `level = 1`,
- sets `raid_shield = 0`,
- keeps `has_tunnel_entrance = False`,
- uses normal build activation logic.

---

## Capture Interactions

### Capturing a field with a tunnel entrance

If a field with a tunnel entrance is captured by normal raid or tunnel raid:

- field owner changes,
- `has_tunnel_entrance` remains true,
- new owner can use the entrance if the field is active and not collapsed.

This creates strategic value for capturing entrance fields.

---

### Capturing an under-tunnelled field

If a field has tunnel connections underneath but no tunnel entrance:

- owner changes,
- tunnel connections remain,
- no tunnel entrance is created,
- new owner does not automatically gain tunnel access unless connected through another entrance.

---

### Capturing a fortified field by tunnel raid

If a tunnel raid succeeds:

- owner changes,
- `field_type` remains,
- `level` remains,
- `raid_shield` becomes 0,
- no tunnel entrance is created automatically.

---

## Strategic Intent

The tunnel system should create several new strategic patterns:

### Infiltration

A player can bypass fortified front lines by investing in underground routes.

### Momentum

A player who gains access to a large connected tunnel network can suddenly threaten multiple fields.

### Counter-risk

A player who overuses tunnels can destabilize their own territory.

### Network Capture

Capturing a surface field with a tunnel entrance can give access to an existing network.

### Collapse Pressure

Repeated tunneling can make important fields collapse, temporarily removing production and control.

### Repair Choice

Repairing a collapsed field restores control but does not restore the old tunnel access. A new entrance must be built separately.

---

## Bot Implications

The current v0.5 bot engine will not automatically understand tunnels.

v0.6 needs new candidate-action categories:

- `tunnel_entrance`
- `tunnel_extend`
- `tunnel_raid`
- `repair_build`

Utility categories may include:

- tunnel_access
- infiltration
- shield_bypass
- collapse_pressure
- network_control
- repair
- anti_collapse

Bots need new scoring questions:

- Is this tunnel entrance useful?
- Does this tunnel extend toward valuable enemy fields?
- Does this tunnel connect into a larger network?
- Can this tunnel raid capture high-value fields?
- Does this tunnel risk collapsing own key fields?
- Should a collapsed field be repaired for territory or production?
- Is the opponent close to using this network?

---

## Runtime Metrics

v0.6 reports should add new columns:

- `tunnel_entrance`
- `tunnel_extend`
- `tunnel_raid`
- `repair_build`
- `tunnel_raid_takeovers`
- `shield_bypassed`
- `collapsed_fields_total`
- `collapsed_fields_final`
- `repair_build_total`
- `tunnel_nodes_final`
- `tunnel_edges_final`
- `network_components_final`
- `largest_tunnel_component`
- `fields_with_tunnel_entrance`
- `collapse_from_own_tunnels`
- `collapse_from_mixed_tunnels`
- `max_tunnel_pressure_final`
- `avg_tunnel_pressure_final`

If later hidden/fog-of-war is added, additional metrics will be needed.

---

## Implementation Direction

Suggested order:

1. State erweitern:
   - `Cell` gets `has_tunnel_entrance: bool` and `collapsed: bool` if not already present.
   - Add a tunnel graph as a set/dict of active coordinate edges.
2. Add centralized constants:
   - `TUNNEL_RAID_KORN_COST = 3`
   - `COLLAPSE_THRESHOLD = 4`
3. Add tunnel graph helper functions:
   - normalize edge pairs,
   - list incident edges,
   - compute tunnel components,
   - compute actor-reachable tunnel component.
4. Add tunnel pressure calculation:
   - count active incident tunnel edges for each coordinate.
5. Add `is_under_tunnel(state, coord)`:
   - uses `tunnel_pressure(state, coord) > 0`.
6. Add collapse check and collapse effect:
   - pressure >= threshold,
   - set collapsed state,
   - clear owner/field/shield/entrance,
   - set level to 0,
   - remove all incident tunnel edges.
7. Add `tunnel_entrance`.
8. Add `tunnel_extend`.
9. Add `tunnel_raid`.
10. Add `repair_build`.
11. Add affordable-target helpers for all tunnel actions.
12. Extend terminal UI:
   - e.g. `E` for entrance,
   - `t` for tunnel presence,
   - `X` for collapsed.
13. Extend runtime matrix metrics and logging.
14. Add basic rule tests before bot scoring.
15. Add simple Utility scoring.
16. Only then explore hidden/fog-of-war.

---

## Current v0.6.1 Recommendation

Recommended first implementation:

```text
1. Tunnel entrances are visible surface features.
2. Tunnel entrances must be built separately.
3. Tunnel networks are permanent graph connections.
4. Tunnel networks have no capture score.
5. Tunnel access comes from owning an active surface field with a tunnel entrance.
6. Capturing a tunnel entrance captures the access point.
7. Under-tunnelled fields are not automatic entrances.
8. Tunnel crossing connects networks.
9. All tunnels increase structural pressure, regardless of builder.
10. Tunnel pressure counts active incident tunnel edges only.
11. 4+ incident tunnel edges collapse a field.
12. Collapse is checked immediately after the pressure-changing action.
13. Collapse sets level to 0 and removes incident tunnel edges.
14. Collapsed fields block tunnel usage through that coordinate.
15. Tunnel raid ignores shields.
16. Tunnel raid costs 3 Korn.
17. Tunnel raid requires a reachable tunnel under the target field.
18. Tunnel raid captures field_type and level, but shield becomes 0.
19. Tunnel raid does not create a tunnel entrance.
20. repair_build restores, captures and rebuilds collapsed fields.
21. repair_build uses normal build activation logic.
22. repair_build does not restore tunnel entrance or old tunnel edges.
23. No hidden tunnel logic in v0.6.1.
24. No underground combat in v0.6.1.
25. No dynamic board shrinking in v0.6.1.
```

---

## One-Sentence Design Summary

Tunnel are permanent physical graph connections under the existing board. They do not create a second capture layer, but they provide network access, shield-bypass raids, structural collapse pressure and repair-driven counterplay. For v0.6.1, tunnel pressure is defined by active incident tunnel edges, collapse triggers immediately at four or more incident edges, collapse resets level to 0 and removes incident tunnel edges, and tunnel raid costs 3 Korn.
