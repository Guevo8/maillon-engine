# Utility Weighting Mechanics

This document covers two related but distinct scoring systems:

1. **Normal Utility Scoring** — used by all six `utility_*` policies (`bot_utility.py`)
2. **Utility Tunneler Overlay** — used by `utility_tunneler` (`bot_utility_tunneler.py`)

---

## Normal Utility Scoring

### Step 1 — Candidate Generation

`generate_candidate_actions(state, actor)` builds the full action set before any scoring happens. The function calls each `affordable_*_targets()` function (from `actions.py`) and expands targets into concrete `Action` objects:

| Action type | Variants per target |
|---|---|
| `build` | 3 (one per field type: Holz, Stein, Korn) |
| `raid` | 1 |
| `fortify` | 1 |
| `field_upgrade` | 1 |
| `core_upgrade` | 1 |
| `rebuild` | up to 2 (excludes current field type) |
| `wait` | 1 (always present) |

Only affordable, legal actions are generated. No pruning beyond affordability.

### Step 2 — Local Scoring

Each candidate is scored by an action-type-specific function (`score_build`, `score_raid`, `score_fortify`, `score_rebuild`, `score_field_upgrade`, `score_core_upgrade`, `score_wait`). Each function returns a `(raw_float, reasons_tuple)` pair.

Local scores capture the intrinsic value of the action at the current position:

- **build**: base 10 + enemy-neighbor bonus (3.5/neighbor) + enemy-core closeness (×8) + board-fill pressure (×6) + field-type value (×0.45) − Holz cost (×1.35)
- **raid**: base score for taking an enemy cell, adjusted for shield, field value, distance to core
- **fortify**: contested-field priority, Korn-pressure driven
- **rebuild**: resource need of target type (×14) + pressure of old type (×6) − Holz cost (×1.7)
- **field_upgrade**: Stein pressure (×8) + contested count + field value − cost
- **core_upgrade**: average resource pressure (×18) + controlled-field count − cost
- **wait**: baseline near zero, raised only by anti-stall corrections

All component magnitudes are in roughly the same range so personality weights remain interpretable.

### Step 3 — Strategic Pressure Adjustment

`apply_strategic_pressure(state, actor, action, category, raw, reasons)` modifies the local raw score based on match context. It does not change the action type — it shifts the score up or down to reflect urgency:

- **behind** → expand and raid bonuses, passive action penalties
- **opponent near territory threshold** → interrupt/expand bonuses
- **actor near territory threshold** → finishing build/raid bonuses
- **many neutral fields remaining** → expansion preference
- **anti-stall finish pressure** (tuned2d) → prevents late-game Korn/Stein waste through rebuild oscillation

The result of `apply_strategic_pressure` becomes the final `raw_score` stored in `UtilityScore`.

### Step 4 — Personality Weighting

```
total_score = raw_score × weight
```

`weight` is looked up from the personality's phase-specific `PersonalityWeights` table, indexed by `UtilityCategory`:

| Category | Action types |
|---|---|
| `expansion` | `build` |
| `economy` | `rebuild` |
| `defense` | `fortify` |
| `aggression` | `raid` |
| `development` | `field_upgrade`, `core_upgrade` |
| *(fallback)* | `wait` — always weight 1.0 |

Phase (early / mid / late) is determined from `state.round_index` using fixed round boundaries: Early = rounds 1–7, Mid = 8–14, Late ≥ 15 (see `bot_personality.py:phase_for_round()`). Each of the six personalities has a distinct weight table; `balancer` is the neutral reference with weights near 1.0 across all categories.

#### Personality IDs and character

| ID | Character |
|---|---|
| `balancer` | Neutral reference; moderate weights across all categories |
| `rusher` | Heavily favours aggression + expansion; low defense + economy |
| `economist` | Rebuilds and upgrades aggressively; lower aggression |
| `fortifier` | Invests in defense and development; slower expansion |
| `aggro_turtle` | High defense + aggression; minimal economy |
| `opportunist` | Raid-heavy; adapts weight based on board state |

### Step 5 — Tie-Breaking and Selection

`choose_best_utility_action()` sorts all scored candidates by a three-key tuple:

```python
(-total_score, action_type_priority_index, (coord_x, coord_y, field_type))
```

`action_type_priority_index` resolves equal-scored actions in this order:
`raid < fortify < build < field_upgrade < core_upgrade < rebuild < wait`

Coordinate tie-breaking `(x, y)` is deterministic and board-layout-stable. `field_type` within build/rebuild is lexicographic but rarely reached.

The top element is returned as the chosen action.

---

## Utility Tunneler Overlay

`utility_tunneler` is not a variant of the normal utility engine. It is a separate module (`bot_utility_tunneler.py`) that scores tunnel-specific actions using explicit named features, then decides via opportunity cost whether to play a tunnel action at all.

### Candidate Set

`generate_tunnel_candidates(state, actor)` generates only:

- `tunnel_entrance` — one per affordable target
- `tunnel_extend` — one per affordable `(source, target)` pair
- `tunnel_raid` — one per affordable target
- `repair_build` — three variants per affordable target (Holz, Stein, Korn)
- `wait` — always present

Normal surface actions (build, raid, fortify, …) are not candidates here.

### Feature Extraction

Each candidate is evaluated on eight named features (all clamped to `[0.0, 1.0]`):

| Feature | Meaning |
|---|---|
| `resource_fit` | Mean remaining resource slack after paying the action cost |
| `tunnel_access_gain` | Increase in reachable tunnel nodes (clone + diff for `tunnel_extend`; neighbor count for `tunnel_entrance`; adjacency bonus for `repair_build`) |
| `enemy_tunnel_threat` | Total tunnel pressure on owned cells ÷ (owned count × collapse threshold) |
| `own_tunnel_pressure` | Source-node pressure ÷ collapse threshold (`tunnel_extend` only) |
| `collapse_risk` | Fraction of owned cells near collapse threshold; doubled if the extend would push a node over |
| `raid_value` | Normalised field value + shield-bypass bonus (`tunnel_raid` only) |
| `repair_value` | Active own neighbours ÷ 4 (`repair_build` only) |
| `territory_pressure` | Urgency (opponent near threshold) + behind ratio |

Two additional fields are computed per candidate but are informational, not used in the weighted sum:

- `normal_action_baseline` — the normal baseline score (shared across all candidates in a round)
- `opportunity_cost` — `max(0, baseline − raw_score)`; logged in `reasons` as `("opportunity_cost", -value)`

### Tunnel Score

```
weighted_sum = Σ (weight[feature] × feature_value)   [zero-weighted features skipped]
tunnel_score = clamp(weighted_sum, 0.0, 1.0)
```

Each action type has its own weight row (`TUNNEL_ACTION_WEIGHTS`). Negative weights (e.g. `collapse_risk`, `own_tunnel_pressure` for `tunnel_extend`) subtract from the score.

`wait` has all-zero weights, so its score is always `0.0`.

### Normal Baseline

Once per decision round (not per candidate):

```python
best_raw = max(s.total_score for s in score_candidate_actions(state, actor, "balancer"))
normal_baseline = clamp(best_raw / 60.0, 0.0, 1.0)
```

`60.0` (`NORMAL_SCORE_NORMALIZATION_CAP`) is the empirically determined upper bound of normal utility `total_score` values. The clamp ensures the baseline stays in `[0, 1]` even in high-resource states where raw scores can exceed the cap.

### Opportunity-Cost Decision

```python
if best_tunnel.score >= normal_baseline - OPPORTUNITY_COST_TOLERANCE:
    return best_tunnel.action          # play the best tunnel action
else:
    return choose_best_utility_action(state, actor, "balancer")  # fall back
```

`OPPORTUNITY_COST_TOLERANCE = 0.10`. The tunnel action is chosen unless the best available normal action scores more than 10 percentage points higher. This prevents the bot from pursuing tunnel actions when a clearly stronger normal move is available.

Candidate ranking before the threshold check uses:

```python
(-score, TUNNEL_ACTION_PRIORITY[action_type], coord_x, coord_y)
```

`TUNNEL_ACTION_PRIORITY`: `tunnel_raid=0, repair_build=1, tunnel_extend=2, tunnel_entrance=3, wait=4`

### Decision Logging (optional)

If a `log_path: Path` is passed to `choose_utility_tunneler_action()`, each decision is appended as a JSONL record to that path. Logging is disabled by default. The record includes the round, actor, chosen action and score, normal baseline, opportunity cost, and the top-5 candidates and feature contributions.

---

## Design Goal

Both systems prioritise **explainability before raw strength**.

The normal utility scorer exposes every score component via the `reasons` tuple on `UtilityScore`. The tunnel overlay exposes a named `TunnelFeatures` dataclass and a `reasons` tuple per candidate. This makes it straightforward to trace why a specific action was chosen — or why it wasn't — without running a debugger.

Raw win-rate optimisation (weight search, minimax, lookahead) is a deliberate non-goal for the current version. The weight tables are tuned by hand, validated by the runtime matrix, and kept interpretable so design changes can be reasoned about directly.
