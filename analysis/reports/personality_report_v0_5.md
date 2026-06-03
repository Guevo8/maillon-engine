# Maillon v0.5 Personality Report

## Source

- Input matrix: `analysis/reports/runtime_matrix_v0_5_personality_full.csv`
- Summary CSV: `analysis/reports/personality_report_v0_5_summary.csv`
- Rows: 128

## Policy Summary

| Policy | Wins | Slots | Winrate | Draws | Avg round | Fortify | Rebuild | Build | Raid | Wait | Korn waste | Avg controlled | Top win | Top loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `utility_rusher` | 27 | 32 | 0.84 | 3 | 36.1 | 349 | 13 | 587 | 2119 | 246 | 4916 | 28.4 | territory:20 | full_board_majority:2 |
| `rusher` | 23 | 32 | 0.72 | 2 | 55.9 | 0 | 20 | 411 | 3382 | 1366 | 15203 | 24.7 | territory:19 | territory:5 |
| `phase_player` | 20 | 32 | 0.62 | 0 | 42.9 | 801 | 194 | 618 | 1751 | 325 | 12373 | 23.6 | full_board_majority:16 | full_board_majority:6 |
| `utility_opportunist` | 15 | 32 | 0.47 | 5 | 47.6 | 1489 | 165 | 746 | 1682 | 278 | 5745 | 23.4 | full_board_majority:15 | full_board_majority:11 |
| `utility_aggro_turtle` | 13 | 32 | 0.41 | 1 | 39.7 | 1278 | 105 | 760 | 1204 | 233 | 4848 | 22.6 | full_board_majority:11 | full_board_majority:12 |
| `utility_balancer` | 11 | 32 | 0.34 | 2 | 41.1 | 1272 | 378 | 757 | 837 | 461 | 7052 | 21.4 | full_board_majority:11 | full_board_majority:10 |
| `utility_economist` | 6 | 32 | 0.19 | 6 | 47.8 | 1097 | 1482 | 763 | 668 | 260 | 5611 | 20.2 | full_board_majority:6 | full_board_majority:11 |
| `utility_fortifier` | 1 | 32 | 0.03 | 5 | 46.8 | 1146 | 1054 | 743 | 631 | 579 | 7812 | 19.9 | full_board_majority:1 | full_board_majority:16 |

## Method Notes

- `Slots` means appearances as player plus appearances as enemy.
- Fortify/Rebuild/Build/Raid/Wait/Waste are actor-side totals.
- Current runtime matrix conflict columns such as `raid_takeovers`, `raid_absorbed_by_shield` and `final_shield_points` are match-level metrics, not clean per-policy ownership. They are therefore not used in the policy summary table.

## Problem Matchups

| Board | Matchup | Winner | Reason | Round | P/E/N | Fortify | Rebuild | Takeovers |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 61 | `utility_economist_vs_utility_economist` | none | none | 121 | 27/27/7 | 124 | 484 | 15 |
| 61 | `utility_economist_vs_utility_fortifier` | none | none | 121 | 29/29/3 | 142 | 444 | 14 |
| 61 | `utility_fortifier_vs_utility_fortifier` | none | none | 121 | 23/31/7 | 84 | 352 | 2 |
| 61 | `utility_balancer_vs_utility_economist` | none | none | 121 | 26/28/7 | 114 | 349 | 65 |
| 61 | `utility_fortifier_vs_utility_economist` | none | none | 121 | 26/29/6 | 94 | 345 | 7 |
| 61 | `utility_balancer_vs_utility_fortifier` | none | none | 121 | 23/31/7 | 98 | 335 | 8 |
| 61 | `utility_economist_vs_utility_opportunist` | none | none | 121 | 31/29/1 | 158 | 326 | 70 |
| 61 | `utility_opportunist_vs_rusher` | none | none | 121 | 24/29/8 | 65 | 2 | 507 |
| 61 | `utility_rusher_vs_utility_aggro_turtle` | none | none | 121 | 33/25/3 | 57 | 1 | 561 |
| 61 | `utility_rusher_vs_utility_opportunist` | none | none | 121 | 30/24/7 | 32 | 1 | 600 |
| 61 | `rusher_vs_utility_opportunist` | none | none | 121 | 31/26/4 | 107 | 0 | 415 |
| 61 | `utility_opportunist_vs_utility_rusher` | none | none | 121 | 20/29/12 | 32 | 0 | 605 |
| 61 | `utility_balancer_vs_utility_balancer` | player | full_board_majority | 51 | 32/29/0 | 174 | 11 | 28 |
| 61 | `utility_aggro_turtle_vs_utility_opportunist` | enemy | full_board_majority | 51 | 30/31/0 | 172 | 4 | 41 |
| 61 | `utility_opportunist_vs_utility_economist` | player | full_board_majority | 50 | 31/30/0 | 161 | 5 | 44 |
| 61 | `utility_opportunist_vs_utility_aggro_turtle` | enemy | full_board_majority | 50 | 29/32/0 | 167 | 4 | 36 |
| 61 | `utility_opportunist_vs_utility_opportunist` | enemy | full_board_majority | 50 | 30/31/0 | 163 | 4 | 44 |
| 61 | `utility_opportunist_vs_utility_balancer` | enemy | full_board_majority | 48 | 29/32/0 | 159 | 5 | 31 |
| 61 | `utility_opportunist_vs_utility_fortifier` | player | full_board_majority | 48 | 32/29/0 | 159 | 3 | 41 |

## Design Read

- `utility_rusher` can stay as a hard stress bot if its high winrate is intentional.
- `utility_fortifier` needs a stronger win plan if it remains low-win and high-defense.
- `utility_economist` needs better conversion from economy into upgrades, expansion and territory pressure.
- `utility_opportunist` is the strongest candidate for a useful non-rusher personality.

