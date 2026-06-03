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

---

### Tunnel Entrance

A tunnel entrance is not a separate field. It is a surface feature attached to an existing controlled field.

Rules:

- A tunnel entrance must be built with a separate action.
- Building a normal field does not automatically create a tunnel entrance.
- A tunnel entrance can only be built on an owned, non-collapsed field.
- If a field with a tunnel entrance is captured, the tunnel entrance is captured with it.
- A tunnel entrance gives access to the connected tunnel network.

Design reason:

This prevents tunnels from dominating the early game and keeps the surface layer relevant.

---

### Tunnel Network

Tunnel connections form a graph underneath the existing board.

A tunnel connection links two adjacent board coordinates.

Important:

- Tunnel connections do not count as controlled fields.
- Tunnel connections do not produce resources.
- Tunnel connections do not have their own capture mechanic.
- Tunnel connections can exist under own, enemy or neutral surface fields.
- Tunnel connections can remain permanently until removed by collapse/repair logic.

A player can use a tunnel network if they own at least one non-collapsed surface field with a tunnel entrance connected to that network.

---

## Ownership and Access

Tunnel access is based on surface access, not tunnel ownership.

A player may use a connected tunnel component if:

1. the player owns a surface field,
2. that field has a tunnel entrance,
3. the field is not collapsed,
4. the tunnel entrance connects to the tunnel component.

Once connected, the player can use the reachable network, including parts originally dug by the opponent.

This creates the intended momentum effect:

> Connecting into a network can suddenly open multiple attack routes.

---

## Tunnel Crossing

If a player extends a tunnel into a field where opponent tunnel connections already exist, the networks connect.

Crossing rules:

- opponent tunnels do not block extension,
- crossing does not remove opponent tunnels,
- crossing does not create underground combat,
- crossing may connect both players to the same network,
- crossing increases structural pressure.

Design rule:

> Tunnel crossing means network connection, not tunnel ownership transfer.

---

## Structural Pressure

Tunnel instability is physical, not ownership-based.

Every tunnel connection contributes to structural pressure regardless of who built it.

Important rule:

> A tunnel is a tunnel. Own tunnels can collapse own fields too.

This avoids hidden capture-like logic and keeps the mechanic physically intuitive.

Suggested pressure model:

- 0 tunnel directions: stable
- 1 tunnel direction: tunnelled
- 2 tunnel directions: undermined
- 3 tunnel directions: unstable
- 4+ tunnel directions: collapsed

For v0.6.1, pressure should be calculated from active tunnel connections touching or passing through a field.

Ownership does not reduce pressure.

---

## Collapse

A field collapses when structural pressure reaches the collapse threshold.

Recommended threshold:

```text
4+ tunnel directions/connections around or under a field
```

Collapsed field effects:

- owner becomes `None`,
- production stops,
- field does not count as controlled,
- field cannot raid,
- field cannot fortify,
- field cannot upgrade,
- field blocks tunnel access through that coordinate,
- field can only be restored with `repair_build`.

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

- `collapsed = false`
- `owner = actor`
- `field_type = selected field type`
- `level = 1`
- `raid_shield = 0`
- tunnel connections in the repaired field are removed
- `has_tunnel_entrance = false`

After repair, a new tunnel entrance must be built separately if desired.

Design reason:

This keeps collapsed fields special, but avoids a clunky multi-step neutral repair phase.

---

## Tunnel Actions

### `tunnel_entrance`

Builds a tunnel entrance on an owned surface field.

Conditions:

- actor owns the target field,
- target is not collapsed,
- target does not already have a tunnel entrance,
- actor can afford the cost.

Suggested cost placeholder:

```text
2 Stein + 1 Holz
```

Effect:

- target gains `has_tunnel_entrance = true`.

---

### `tunnel_extend`

Extends a tunnel from a reachable tunnel node to an adjacent coordinate.

Conditions:

- actor has access to the source tunnel node,
- target is adjacent to source,
- target is not collapsed,
- tunnel connection does not already exist,
- actor can afford the cost.

Suggested cost placeholder:

```text
1 Stein + 1 Holz
```

Effect:

- tunnel connection is created between source and target,
- structural pressure updates,
- collapse checks run.

Notes:

- target may be own, enemy or neutral surface field,
- target does not become captured,
- target does not become a tunnel entrance.

---

### `tunnel_raid`

Uses a reachable tunnel under an enemy surface field to raid from below.

Conditions:

- actor has access to a tunnel network,
- target is an enemy-owned, non-collapsed surface field,
- target has a reachable tunnel node or tunnel connection,
- actor can afford the cost.

Suggested cost placeholder:

```text
2 Korn or 3 Korn
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
- removes tunnel connections in that coordinate.

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
- `raid_shield` becomes 0.

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

Repairing a collapsed field restores control but removes the tunnel node in that coordinate.

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

If later hidden/fog-of-war is added, additional metrics will be needed.

---

## Open Design Questions

These must be decided before coding:

1. Exact tunnel pressure calculation:
   - count tunnel edges,
   - count tunnel directions,
   - count tunnel nodes,
   - or hybrid model?

2. Exact collapse timing:
   - immediately after tunnel extension,
   - end of action,
   - end of turn,
   - end of round?

3. Exact tunnel raid cost:
   - 2 Korn,
   - 3 Korn,
   - or scaling by target level?

4. Can tunnel raid target only fields directly under the network, or also adjacent from network nodes?

5. Does repair_build remove only tunnel connections in the repaired coordinate, or also adjacent broken links?

6. Should tunnel entrances require active fields?

7. Should tunnel entrances work immediately or only after `active_from_round`?

8. Should tunnel_extend trigger activation delay?

9. Should tunnel collapse destroy field_type permanently or preserve it in history?

10. Should normal build ever be allowed on collapsed fields?
    - current recommendation: no, only repair_build.

---

## Current v0.6.1 Recommendation

Recommended first implementation:

```text
1. Tunnel entrances are visible surface features.
2. Tunnel entrances must be built separately.
3. Tunnel networks are permanent graph connections.
4. Tunnel networks have no capture score.
5. Tunnel access comes from owning a surface field with a tunnel entrance.
6. Capturing a tunnel entrance captures the access point.
7. Under-tunnelled fields are not automatic entrances.
8. Tunnel crossing connects networks.
9. All tunnels increase structural pressure, regardless of builder.
10. 4+ tunnel pressure collapses a field.
11. Collapsed fields block tunnel usage through that coordinate.
12. Tunnel raid ignores shields.
13. Tunnel raid captures field_type and level, but shield becomes 0.
14. Tunnel raid does not create a tunnel entrance.
15. repair_build restores, captures and rebuilds collapsed fields.
16. repair_build removes tunnel connections in the repaired coordinate.
17. No hidden tunnel logic in v0.6.1.
18. No underground combat in v0.6.1.
19. No dynamic board shrinking in v0.6.1.
```

---

## Implementation Direction

Suggested order:

1. Add tunnel state fields to `Cell`.
2. Add tunnel graph helper functions.
3. Add tunnel pressure calculation.
4. Add collapse state and collapse checks.
5. Add `tunnel_entrance`.
6. Add `tunnel_extend`.
7. Add `tunnel_raid`.
8. Add `repair_build`.
9. Extend runtime matrix metrics.
10. Add basic rule tests.
11. Add simple Utility scoring.
12. Only then explore hidden/fog-of-war.

---

## One-Sentence Design Summary

Tunnel are permanent physical graph connections under the existing board. They do not create a second capture layer, but they provide network access, shield-bypass raids, structural collapse pressure and repair-driven counterplay.
