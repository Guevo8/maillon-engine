# Maillon v0.5 Personality Report

## Source

- Input matrix: `analysis/reports/runtime_matrix_v0_5_personality_tuned1_full.csv`
- Summary CSV: `analysis/reports/personality_report_v0_5_personality_tuned1_full_summary.csv`
- Rows: 128

## Policy Summary

| Policy | Wins | Slots | Winrate | Draws | Avg round | Fortify | Rebuild | Build | Raid | Wait | Korn waste | Avg controlled | Top win | Top loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `utility_rusher` | 26 | 32 | 0.81 | 4 | 39.9 | 363 | 17 | 599 | 2452 | 248 | 5834 | 28.2 | territory:19 | full_board_majority:2 |
| `rusher` | 23 | 32 | 0.72 | 2 | 60.5 | 0 | 20 | 453 | 3666 | 1483 | 17247 | 24.5 | territory:17 | territory:5 |
| `phase_player` | 19 | 32 | 0.59 | 0 | 44.1 | 838 | 191 | 623 | 1824 | 327 | 12599 | 23.4 | full_board_majority:16 | full_board_majority:7 |
| `utility_opportunist` | 14 | 32 | 0.44 | 4 | 45.3 | 1464 | 36 | 753 | 1689 | 217 | 4630 | 23.5 | full_board_majority:14 | full_board_majority:13 |
| `utility_economist` | 12 | 32 | 0.38 | 0 | 37.2 | 1225 | 69 | 750 | 1059 | 208 | 3989 | 21.6 | full_board_majority:12 | full_board_majority:12 |
| `utility_aggro_turtle` | 11 | 32 | 0.34 | 1 | 40.0 | 1341 | 93 | 754 | 1208 | 238 | 4582 | 22.4 | full_board_majority:10 | full_board_majority:14 |
| `utility_balancer` | 9 | 32 | 0.28 | 0 | 35.5 | 1281 | 84 | 760 | 812 | 251 | 3686 | 21.1 | full_board_majority:9 | full_board_majority:13 |
| `utility_fortifier` | 8 | 32 | 0.25 | 1 | 39.9 | 1266 | 69 | 774 | 1255 | 243 | 4342 | 22.1 | full_board_majority:7 | full_board_majority:17 |

## Method Notes

- `Slots` means appearances as player plus appearances as enemy.
- Fortify/Rebuild/Build/Raid/Wait/Waste are actor-side totals.
- Current runtime matrix conflict columns such as `raid_takeovers`, `raid_absorbed_by_shield` and `final_shield_points` are match-level metrics, not clean per-policy ownership. They are therefore not used in the policy summary table.

## Problem Matchups

| Board | Matchup | Winner | Reason | Round | P/E/N | Fortify | Rebuild | Takeovers |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 61 | `utility_opportunist_vs_rusher` | none | none | 121 | 24/29/8 | 65 | 2 | 507 |
| 61 | `utility_rusher_vs_utility_aggro_turtle` | none | none | 121 | 33/25/3 | 57 | 1 | 561 |
| 61 | `utility_rusher_vs_utility_opportunist` | none | none | 121 | 30/24/7 | 32 | 1 | 600 |
| 61 | `rusher_vs_utility_opportunist` | none | none | 121 | 31/26/4 | 107 | 0 | 415 |
| 61 | `utility_opportunist_vs_utility_rusher` | none | none | 121 | 20/29/12 | 32 | 0 | 605 |
| 61 | `utility_rusher_vs_utility_fortifier` | none | none | 121 | 32/22/7 | 29 | 0 | 611 |
| 61 | `utility_balancer_vs_utility_balancer` | player | full_board_majority | 51 | 32/29/0 | 174 | 11 | 28 |
| 61 | `utility_aggro_turtle_vs_utility_opportunist` | enemy | full_board_majority | 51 | 30/31/0 | 172 | 4 | 41 |
| 61 | `utility_opportunist_vs_utility_aggro_turtle` | enemy | full_board_majority | 50 | 29/32/0 | 167 | 4 | 36 |
| 61 | `utility_opportunist_vs_utility_opportunist` | enemy | full_board_majority | 50 | 30/31/0 | 163 | 4 | 44 |
| 61 | `utility_opportunist_vs_utility_fortifier` | player | full_board_majority | 50 | 32/29/0 | 153 | 0 | 51 |
| 61 | `utility_opportunist_vs_utility_balancer` | enemy | full_board_majority | 48 | 29/32/0 | 159 | 5 | 31 |
| 61 | `utility_fortifier_vs_utility_opportunist` | enemy | full_board_majority | 46 | 29/32/0 | 152 | 4 | 31 |

## Design Read

- `utility_rusher` can stay as a hard stress bot if its high winrate is intentional.
- `utility_fortifier` needs a stronger win plan if it remains low-win and high-defense.
- `utility_economist` needs better conversion from economy into upgrades, expansion and territory pressure.
- `utility_opportunist` is the strongest candidate for a useful non-rusher personality.

