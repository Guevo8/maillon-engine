# Maillon v0.5 Competitive Personality Pool Report

## Source

- Input matrix: `analysis/reports/runtime_matrix_v0_5_6j1_full.csv`
- Summary CSV: `analysis/reports/personality_report_v0_5_6k_competitive_pool_summary.csv`
- Rows used: 98 / 128
- Include policies: `all`
- Exclude policies: `utility_rusher`
- Focus policy: `-`

## Policy Summary

| Policy | Wins | Slots | Winrate | Draws | Avg round | Fortify | Rebuild | Build | Raid | Wait | Korn waste | Avg controlled | Top win | Top loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `rusher` | 22 | 28 | 0.79 | 1 | 53.0 | 0 | 9 | 459 | 2719 | 1125 | 13781 | 25.7 | full_board_majority:12 | full_board_majority:2 |
| `utility_opportunist` | 21 | 28 | 0.75 | 0 | 37.8 | 1311 | 23 | 654 | 842 | 187 | 3174 | 25.0 | full_board_majority:21 | full_board_majority:6 |
| `phase_player` | 18 | 28 | 0.64 | 0 | 44.2 | 750 | 131 | 554 | 1643 | 278 | 10841 | 25.4 | full_board_majority:14 | full_board_majority:8 |
| `utility_economist` | 11 | 28 | 0.39 | 1 | 35.8 | 1063 | 33 | 676 | 831 | 170 | 3649 | 23.5 | full_board_majority:11 | full_board_majority:15 |
| `utility_balancer` | 9 | 28 | 0.32 | 0 | 34.0 | 1112 | 50 | 672 | 633 | 219 | 3060 | 23.3 | full_board_majority:8 | full_board_majority:15 |
| `utility_aggro_turtle` | 9 | 28 | 0.32 | 0 | 34.6 | 1129 | 79 | 656 | 653 | 207 | 2953 | 23.2 | full_board_majority:8 | full_board_majority:15 |
| `utility_fortifier` | 7 | 28 | 0.25 | 0 | 36.4 | 1124 | 52 | 671 | 809 | 205 | 3461 | 23.0 | full_board_majority:6 | full_board_majority:19 |

## Method Notes

- `Slots` means appearances as player plus appearances as enemy within the filtered pool.
- Fortify/Rebuild/Build/Raid/Wait/Waste are actor-side totals.
- `timeout_majority` is an analysis-only max-round adjudication from runtime_matrix.py, not an engine win rule.
- Current runtime matrix conflict columns such as `raid_takeovers`, `raid_absorbed_by_shield` and `final_shield_points` are match-level metrics, not clean per-policy ownership. They are therefore not used in the policy summary table.

## Problem Matchups

| Board | Matchup | Winner | Reason | Natural | Round | P/E/N | Fortify | Rebuild | Takeovers |
|---:|---|---|---|---|---:|---:|---:|---:|---:|
| 61 | `rusher_vs_utility_economist` | none | timeout_draw | none | 121 | 29/28/4 | 165 | 15 | 254 |
| 61 | `rusher_vs_rusher` | enemy | timeout_majority | none | 121 | 22/31/8 | 0 | 6 | 433 |
| 61 | `utility_opportunist_vs_utility_aggro_turtle` | player | full_board_majority | full_board_majority | 49 | 31/30/0 | 155 | 4 | 40 |
| 61 | `utility_aggro_turtle_vs_utility_opportunist` | enemy | full_board_majority | full_board_majority | 49 | 30/31/0 | 153 | 0 | 51 |
| 61 | `utility_opportunist_vs_utility_balancer` | player | full_board_majority | full_board_majority | 46 | 31/30/0 | 150 | 4 | 33 |
| 61 | `utility_balancer_vs_utility_balancer` | enemy | full_board_majority | full_board_majority | 46 | 29/32/0 | 153 | 1 | 34 |

## Design Read

- Competitive pool reports should usually exclude dedicated stress bots such as `utility_rusher`.
- Stress pool reports should show whether normal bots survive against the hard pressure bot.
- `utility_fortifier` and `utility_economist` should be judged by conversion behavior, not only raw winrate.
- `utility_opportunist` is the strongest candidate for a useful non-rusher personality.

