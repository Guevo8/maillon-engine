# Maillon v0.5 Utility Rusher Stress Pool Report

## Source

- Input matrix: `analysis/reports/runtime_matrix_v0_5_6j1_full.csv`
- Summary CSV: `analysis/reports/personality_report_v0_5_6k_stress_pool_summary.csv`
- Rows used: 30 / 128
- Include policies: `all`
- Exclude policies: `-`
- Focus policy: `utility_rusher`

## Policy Summary

| Policy | Wins | Slots | Winrate | Draws | Avg round | Fortify | Rebuild | Build | Raid | Wait | Korn waste | Avg controlled | Top win | Top loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `utility_rusher` | 30 | 32 | 0.94 | 0 | 33.9 | 366 | 23 | 644 | 1827 | 255 | 4369 | 28.4 | territory:17 | full_board_majority:2 |
| `utility_balancer` | 0 | 4 | 0.00 | 0 | 23.0 | 38 | 1 | 97 | 79 | 34 | 108 | 14.8 | - | territory:3 |
| `utility_aggro_turtle` | 0 | 4 | 0.00 | 0 | 30.8 | 69 | 0 | 95 | 152 | 31 | 439 | 19.8 | - | full_board_majority:3 |
| `utility_economist` | 0 | 4 | 0.00 | 0 | 33.2 | 49 | 2 | 95 | 189 | 26 | 212 | 15.5 | - | territory:4 |
| `utility_fortifier` | 0 | 4 | 0.00 | 0 | 34.8 | 54 | 0 | 94 | 212 | 36 | 433 | 18.0 | - | territory:2 |
| `phase_player` | 0 | 4 | 0.00 | 0 | 35.5 | 100 | 13 | 64 | 146 | 38 | 739 | 12.0 | - | territory:4 |
| `rusher` | 0 | 4 | 0.00 | 0 | 35.5 | 0 | 0 | 54 | 180 | 177 | 502 | 11.2 | - | territory:3 |
| `utility_opportunist` | 0 | 4 | 0.00 | 0 | 47.8 | 68 | 1 | 96 | 359 | 28 | 596 | 21.5 | - | full_board_majority:4 |

## Method Notes

- `Slots` means appearances as player plus appearances as enemy within the filtered pool.
- Fortify/Rebuild/Build/Raid/Wait/Waste are actor-side totals.
- `timeout_majority` is an analysis-only max-round adjudication from runtime_matrix.py, not an engine win rule.
- Current runtime matrix conflict columns such as `raid_takeovers`, `raid_absorbed_by_shield` and `final_shield_points` are match-level metrics, not clean per-policy ownership. They are therefore not used in the policy summary table.

## Problem Matchups

No obvious stalls or extreme rebuild/fortify cases detected.

## Design Read

- Competitive pool reports should usually exclude dedicated stress bots such as `utility_rusher`.
- Stress pool reports should show whether normal bots survive against the hard pressure bot.
- `utility_fortifier` and `utility_economist` should be judged by conversion behavior, not only raw winrate.
- `utility_opportunist` is the strongest candidate for a useful non-rusher personality.

