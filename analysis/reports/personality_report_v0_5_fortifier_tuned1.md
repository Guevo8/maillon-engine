# Maillon v0.5 Personality Report

## Source

- Input matrix: `analysis/reports/runtime_matrix_v0_5_fortifier_tuned1.csv`
- Summary CSV: `analysis/reports/personality_report_v0_5_fortifier_tuned1_summary.csv`
- Rows: 50

## Policy Summary

| Policy | Wins | Slots | Winrate | Draws | Avg round | Fortify | Rebuild | Build | Raid | Wait | Korn waste | Avg controlled | Top win | Top loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `rusher` | 15 | 20 | 0.75 | 2 | 65.0 | 0 | 20 | 297 | 2433 | 1010 | 12314 | 26.1 | territory:12 | territory:2 |
| `phase_player` | 12 | 20 | 0.60 | 0 | 47.6 | 535 | 163 | 399 | 1264 | 210 | 9638 | 24.4 | full_board_majority:11 | full_board_majority:6 |
| `utility_opportunist` | 9 | 20 | 0.45 | 2 | 44.4 | 980 | 29 | 481 | 907 | 141 | 3049 | 23.8 | full_board_majority:9 | full_board_majority:8 |
| `utility_balancer` | 6 | 20 | 0.30 | 0 | 38.9 | 873 | 44 | 485 | 622 | 170 | 2554 | 21.2 | full_board_majority:6 | full_board_majority:8 |
| `utility_fortifier` | 6 | 20 | 0.30 | 0 | 41.1 | 827 | 63 | 503 | 762 | 162 | 2758 | 22.8 | full_board_majority:5 | full_board_majority:11 |

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

