# Maillon v0.5 Personality Report

## Source

- Input matrix: `analysis/reports/runtime_matrix_v0_5_economist_tuned1.csv`
- Summary CSV: `analysis/reports/personality_report_v0_5_economist_tuned1_summary.csv`
- Rows: 72

## Policy Summary

| Policy | Wins | Slots | Winrate | Draws | Avg round | Fortify | Rebuild | Build | Raid | Wait | Korn waste | Avg controlled | Top win | Top loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `rusher` | 19 | 24 | 0.79 | 2 | 65.4 | 0 | 20 | 358 | 2960 | 1211 | 14985 | 26.5 | territory:14 | territory:2 |
| `phase_player` | 16 | 24 | 0.67 | 0 | 46.4 | 635 | 171 | 485 | 1473 | 253 | 10729 | 25.0 | full_board_majority:14 | full_board_majority:6 |
| `utility_opportunist` | 11 | 24 | 0.46 | 2 | 42.8 | 1178 | 30 | 569 | 998 | 162 | 3355 | 24.0 | full_board_majority:11 | full_board_majority:10 |
| `utility_economist` | 10 | 24 | 0.42 | 0 | 39.2 | 1014 | 61 | 560 | 832 | 161 | 3325 | 22.4 | full_board_majority:10 | full_board_majority:10 |
| `utility_balancer` | 7 | 24 | 0.29 | 0 | 37.7 | 1066 | 46 | 573 | 676 | 191 | 2982 | 21.8 | full_board_majority:7 | full_board_majority:11 |
| `utility_fortifier` | 7 | 24 | 0.29 | 0 | 39.5 | 1008 | 63 | 590 | 828 | 184 | 3180 | 23.0 | full_board_majority:6 | full_board_majority:14 |

## Method Notes

- `Slots` means appearances as player plus appearances as enemy.
- Fortify/Rebuild/Build/Raid/Wait/Waste are actor-side totals.
- Current runtime matrix conflict columns such as `raid_takeovers`, `raid_absorbed_by_shield` and `final_shield_points` are match-level metrics, not clean per-policy ownership. They are therefore not used in the policy summary table.

## Problem Matchups

| Board | Matchup | Winner | Reason | Round | P/E/N | Fortify | Rebuild | Takeovers |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 61 | `utility_opportunist_vs_rusher` | none | none | 121 | 24/29/8 | 65 | 2 | 507 |
| 61 | `rusher_vs_utility_opportunist` | none | none | 121 | 31/26/4 | 107 | 0 | 415 |
| 61 | `utility_balancer_vs_utility_balancer` | player | full_board_majority | 51 | 32/29/0 | 174 | 11 | 28 |
| 61 | `utility_opportunist_vs_utility_opportunist` | enemy | full_board_majority | 50 | 30/31/0 | 163 | 4 | 44 |
| 61 | `utility_opportunist_vs_utility_fortifier` | player | full_board_majority | 50 | 32/29/0 | 153 | 0 | 51 |
| 61 | `utility_opportunist_vs_utility_balancer` | enemy | full_board_majority | 48 | 29/32/0 | 159 | 5 | 31 |
| 61 | `utility_fortifier_vs_utility_opportunist` | enemy | full_board_majority | 46 | 29/32/0 | 152 | 4 | 31 |

## Design Read

- `utility_rusher` can stay as a hard stress bot if its high winrate is intentional.
- `utility_fortifier` needs a stronger win plan if it remains low-win and high-defense.
- `utility_economist` needs better conversion from economy into upgrades, expansion and territory pressure.
- `utility_opportunist` is the strongest candidate for a useful non-rusher personality.

