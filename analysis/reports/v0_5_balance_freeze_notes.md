# Maillon v0.5 Balance Freeze Notes

## Status

This document freezes the current v0.5 balancing interpretation after the Utility Bot, Personality Bot, anti-stall diagnostics, timeout adjudication and personality-pool reporting work.

This is not a final gameplay balance declaration. It is a reproducible analysis baseline for the next development phase.

## Current branch / tag context

Relevant v0.5 anchors:

- `v0.5-utility-bot` branch: active implementation branch.
- `v0.5-utility-tuned2d`: utility finish-pressure tuning baseline before personality-pool expansion.
- `v0.5-personality-matrix-baseline`: first personality matrix baseline.
- `v0.5-6j-timeout-adjudication`: runtime-matrix timeout adjudication baseline.
- `v0.5-6k-personality-pools`: competitive/stress pool reporting split.

## Mainline decisions

### 1. Utility Bot architecture remains valid

The Utility Bot is now the preferred bot architecture for explainable tactical behavior. It supports personality weights, phase-dependent behavior and score probing.

The current Utility layer is useful for:

- testing strategic preferences,
- identifying overactive actions,
- comparing personality profiles,
- detecting stall patterns,
- separating normal bot balance from stress-test behavior.

### 2. `utility_rusher` is a stress bot, not a normal competitive bot

`utility_rusher` is intentionally excluded from normal competitive balance reads.

Reason:

- In the full v0.5 6J.1 report it reached roughly `0.94` winrate.
- In the 6K stress pool, all direct opponents scored `0` wins against it.
- It is therefore useful as a pressure/stress test, but distorts the normal personality table.

Decision:

- Keep `utility_rusher`.
- Do not nerf it immediately.
- Do not treat it as a normal balanced personality.
- Use separate stress-pool reports when evaluating it.

### 3. Competitive pool excludes `utility_rusher`

The competitive pool should usually be generated with:

```bash
python analysis/personality_report.py \
  --input analysis/reports/runtime_matrix_v0_5_6j1_full.csv \
  --exclude-policies utility_rusher \
  --title "Maillon v0.5 Competitive Personality Pool Report" \
  --out analysis/reports/personality_report_v0_5_6k_competitive_pool.md \
  --csv-out analysis/reports/personality_report_v0_5_6k_competitive_pool_summary.csv
```

Current 6K competitive read:

| Policy | Winrate | Read |
|---|---:|---|
| `rusher` | 0.79 | Strong legacy stress/reference bot. Still raid-heavy. |
| `utility_opportunist` | 0.75 | Strongest useful non-rusher Utility personality. |
| `phase_player` | 0.64 | Solid legacy reference bot. |
| `utility_economist` | 0.39 | Improved, but still weak at converting economy into wins. |
| `utility_balancer` | 0.32 | Stable baseline, but underpowered. |
| `utility_aggro_turtle` | 0.32 | Thematic hybrid, currently not strong enough. |
| `utility_fortifier` | 0.25 | Defensive identity works, win plan remains weak. |

### 4. Stress pool uses `utility_rusher` focus reports

The stress pool should usually be generated with:

```bash
python analysis/personality_report.py \
  --input analysis/reports/runtime_matrix_v0_5_6j1_full.csv \
  --focus-policy utility_rusher \
  --title "Maillon v0.5 Utility Rusher Stress Pool Report" \
  --out analysis/reports/personality_report_v0_5_6k_stress_pool.md \
  --csv-out analysis/reports/personality_report_v0_5_6k_stress_pool_summary.csv
```

Current 6K stress read:

- `utility_rusher` won 30 of 32 slots in the full report.
- In direct focus-pool reporting, all other policies recorded 0 wins against `utility_rusher`.
- `utility_opportunist` survived longest on average and retained the highest average controlled-field value among non-rusher stress opponents.

Interpretation:

- `utility_rusher` is a useful pressure benchmark.
- It is too strong for normal balance comparison.
- Its purpose is to expose weak finish logic, weak expansion logic and slow defensive plans.

## Anti-stall decisions

### 1. Fortify Breaker remains an experiment, not mainline balance

The Fortify Breaker idea is mechanically interesting and thematically plausible. However, v0.5 balancing showed that many observed stalls were not caused by shields alone.

Decision:

- Keep Fortify Breaker results as experiment data.
- Do not treat it as required mainline v0.5 balance.
- Revisit later if shield-heavy metas become dominant.

### 2. Raid-churn was the main stall type

The major stall pattern was:

```text
many raids / many takeovers / open neutral fields / no finish
```

This was especially visible on the 61-field board.

Response:

- Utility finish pressure was added/tuned.
- Legacy rusher finish-build logic was added.
- Runtime timeout adjudication was added for analytical classification.

### 3. Timeout adjudication is analysis-only

`runtime_matrix.py` now supports timeout-majority adjudication.

Default:

```text
--timeout-majority-margin 5
```

Meaning:

- If max rounds are reached and no natural winner exists, the controlled-field leader wins by `timeout_majority` only if the lead is at least 5 fields.
- Otherwise the result becomes `timeout_draw`.

This does not change engine rules. It changes the analysis matrix classification only.

New runtime columns:

- `natural_winner`
- `natural_win_reason`
- `timeout_margin`
- `timeout_controlled_diff`

Use these columns to distinguish real engine wins from analysis-only timeout decisions.

## Current known issues

### 1. `utility_rusher` is extremely strong

This is currently accepted because it is treated as a stress bot.

Open question:

- Later, should there be a second, softer `utility_rusher_competitive` profile?

### 2. `utility_fortifier` lacks a win plan

`utility_fortifier` can defend, but still converts poorly into territory wins.

Potential future improvements:

- Better counter-raid timing.
- Stronger late expansion after stabilization.
- A clearer “fortified advance” plan instead of static defense.

### 3. `utility_economist` still under-converts

`utility_economist` improved after tuning, but remains below the top competitive group.

Potential future improvements:

- Upgrade-to-finish logic.
- More aggressive expansion when resource caps are high.
- Better transition from economy to raid or territory closeout.

### 4. `utility_balancer` is stable but weak

`utility_balancer` is useful as a baseline but not competitive enough.

Potential future improvements:

- Slightly more opportunistic finish behavior.
- Better role-switching when ahead/behind.
- Less passive defense when territory is still open.

### 5. `utility_aggro_turtle` is thematically clear but underpowered

The hybrid idea is good, but the current profile may pay too much for both aggression and defense without a sharp win condition.

Potential future improvements:

- Expansion-first opening.
- Selective fortification rather than broad shielding.
- Better transition into raids once a protected front exists.

## Deferred mechanics

### Tunnel system

The tunnel / underground layer is strategically promising but should not be added during v0.5 balance stabilization.

Potential v0.6 module:

- second underground field layer,
- tunnel tag / tunnel build action,
- shield bypass routes,
- underground-only raids,
- sabotage / undermining,
- repair mechanics,
- possible shrinking board / destroyed fields state.

Reason to defer:

- It changes board topology, victory logic, field state and tactical depth at the same time.
- It should be designed as a full v0.6 module, not as a late v0.5 patch.

### Weather system

A random weather system is also promising but should be handled after the core bot balance is frozen.

Possible effects:

- rain increases raid costs,
- heat changes resource efficiency,
- frost increases build cost,
- storm/hail disrupts fortify or upgrades.

Reason to defer:

- Random global modifiers can make deterministic balance analysis noisier.
- Weather should probably have seedable deterministic runs before entering the main test matrix.

## Recommended next phase

### 6M: v0.5 Freeze Pack

Before moving to v0.6 mechanics, create one small freeze pack:

- final v0.5 runtime matrix,
- competitive pool report,
- stress pool report,
- balance freeze notes,
- known issues list,
- tag.

Suggested tag:

```text
v0.5-balance-freeze
```

### 6N / v0.6 Planning

After v0.5 freeze:

1. Draft tunnel module as design document.
2. Define exact field-state model.
3. Decide if tunnel is a field tag, second board layer or separate graph.
4. Add deterministic tests before adding bot behavior.
5. Only then extend Utility AI.

## Practical interpretation

v0.5 now answers three important questions:

1. Can Maillon produce measurable bot-vs-bot balance data?
   - Yes.

2. Can the project distinguish normal balance from stress testing?
   - Yes, via 6K competitive/stress pool reports.

3. Are the remaining problems rule problems or bot-personality problems?
   - Mostly bot-personality and finish-conversion problems, not core rule failure.

This makes v0.5 a valid technical balancing baseline for future mechanics.
