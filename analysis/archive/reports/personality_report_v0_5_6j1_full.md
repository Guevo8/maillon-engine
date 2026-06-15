# Maillon v0.5 Personality Report

## Source

- Input matrix: `analysis/reports/runtime_matrix_v0_5_6j1_full.csv`
- Summary CSV: `analysis/reports/personality_report_v0_5_6j1_full_summary.csv`
- Rows: 128

## Policy Summary

| Policy | Wins | Slots | Winrate | Draws | Avg round | Fortify | Rebuild | Build | Raid | Wait | Korn waste | Avg controlled | Top win | Top loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `utility_rusher` | 30 | 32 | 0.94 | 0 | 33.9 | 366 | 23 | 644 | 1827 | 255 | 4369 | 28.4 | territory:17 | full_board_majority:2 |
| `rusher` | 22 | 32 | 0.69 | 1 | 50.8 | 0 | 9 | 513 | 2899 | 1302 | 14283 | 23.9 | full_board_majority:12 | territory:4 |
| `utility_opportunist` | 21 | 32 | 0.66 | 0 | 39.0 | 1379 | 24 | 750 | 1201 | 215 | 3770 | 24.5 | full_board_majority:21 | full_board_majority:10 |
| `phase_player` | 18 | 32 | 0.56 | 0 | 43.1 | 850 | 144 | 618 | 1789 | 316 | 11580 | 23.7 | full_board_majority:14 | full_board_majority:8 |
| `utility_economist` | 11 | 32 | 0.34 | 1 | 35.4 | 1112 | 35 | 771 | 1020 | 196 | 3861 | 22.5 | full_board_majority:11 | full_board_majority:15 |
| `utility_balancer` | 9 | 32 | 0.28 | 0 | 32.6 | 1150 | 51 | 769 | 712 | 253 | 3168 | 22.2 | full_board_majority:8 | full_board_majority:16 |
| `utility_aggro_turtle` | 9 | 32 | 0.28 | 0 | 34.1 | 1198 | 79 | 751 | 805 | 238 | 3392 | 22.8 | full_board_majority:8 | full_board_majority:18 |
| `utility_fortifier` | 7 | 32 | 0.22 | 0 | 36.2 | 1178 | 52 | 765 | 1021 | 241 | 3894 | 22.4 | full_board_majority:6 | full_board_majority:21 |

## Method Notes

- `Slots` means appearances as player plus appearances as enemy.
- Fortify/Rebuild/Build/Raid/Wait/Waste are actor-side totals.
- Current runtime matrix conflict columns such as `raid_takeovers`, `raid_absorbed_by_shield` and `final_shield_points` are match-level metrics, not clean per-policy ownership. They are therefore not used in the policy summary table.

## Problem Matchups

| Board | Matchup | Winner | Reason | Round | P/E/N | Fortify | Rebuild | Takeovers |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 61 | `rusher_vs_utility_economist` | none | timeout_draw | 121 | 29/28/4 | 165 | 15 | 254 |
| 61 | `rusher_vs_rusher` | enemy | timeout_majority | 121 | 22/31/8 | 0 | 6 | 433 |
| 61 | `utility_opportunist_vs_utility_aggro_turtle` | player | full_board_majority | 49 | 31/30/0 | 155 | 4 | 40 |
| 61 | `utility_aggro_turtle_vs_utility_opportunist` | enemy | full_board_majority | 49 | 30/31/0 | 153 | 0 | 51 |
| 61 | `utility_opportunist_vs_utility_balancer` | player | full_board_majority | 46 | 31/30/0 | 150 | 4 | 33 |
| 61 | `utility_balancer_vs_utility_balancer` | enemy | full_board_majority | 46 | 29/32/0 | 153 | 1 | 34 |

## Design Read

- `utility_rusher` can stay as a hard stress bot if its high winrate is intentional.
- `utility_fortifier` needs a stronger win plan if it remains low-win and high-defense.
- `utility_economist` needs better conversion from economy into upgrades, expansion and territory pressure.
- `utility_opportunist` is the strongest candidate for a useful non-rusher personality.

