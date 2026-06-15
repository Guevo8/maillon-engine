# Maillon v0.5 Personality Report

## Source

- Input matrix: `analysis/reports/runtime_matrix_v0_5_personality_6g_full.csv`
- Summary CSV: `analysis/reports/personality_report_v0_5_personality_6g_full_summary.csv`
- Rows: 128

## Policy Summary

| Policy | Wins | Slots | Winrate | Draws | Avg round | Fortify | Rebuild | Build | Raid | Wait | Korn waste | Avg controlled | Top win | Top loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `utility_rusher` | 26 | 32 | 0.81 | 1 | 32.1 | 254 | 7 | 745 | 1584 | 298 | 3907 | 26.7 | full_board_majority:17 | full_board_majority:4 |
| `utility_opportunist` | 25 | 32 | 0.78 | 0 | 30.9 | 626 | 19 | 756 | 1151 | 226 | 3269 | 26.3 | full_board_majority:17 | full_board_majority:7 |
| `utility_fortifier` | 17 | 32 | 0.53 | 0 | 32.7 | 879 | 33 | 753 | 1033 | 240 | 4107 | 24.2 | full_board_majority:14 | full_board_majority:12 |
| `utility_balancer` | 16 | 32 | 0.50 | 0 | 33.9 | 893 | 26 | 745 | 1154 | 224 | 3867 | 24.2 | full_board_majority:12 | full_board_majority:12 |
| `utility_economist` | 14 | 32 | 0.44 | 1 | 33.4 | 570 | 6 | 753 | 1417 | 204 | 4181 | 24.7 | full_board_majority:9 | full_board_majority:17 |
| `rusher` | 13 | 32 | 0.41 | 2 | 52.7 | 0 | 27 | 444 | 2770 | 1597 | 12927 | 17.9 | full_board_majority:7 | territory:12 |
| `utility_aggro_turtle` | 9 | 32 | 0.28 | 0 | 33.9 | 991 | 27 | 751 | 1065 | 224 | 4256 | 24.4 | full_board_majority:5 | full_board_majority:23 |
| `phase_player` | 6 | 32 | 0.19 | 0 | 41.4 | 704 | 204 | 566 | 1654 | 291 | 12770 | 19.8 | full_board_majority:6 | territory:17 |

## Method Notes

- `Slots` means appearances as player plus appearances as enemy.
- Fortify/Rebuild/Build/Raid/Wait/Waste are actor-side totals.
- Current runtime matrix conflict columns such as `raid_takeovers`, `raid_absorbed_by_shield` and `final_shield_points` are match-level metrics, not clean per-policy ownership. They are therefore not used in the policy summary table.

## Problem Matchups

| Board | Matchup | Winner | Reason | Round | P/E/N | Fortify | Rebuild | Takeovers |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 61 | `utility_economist_vs_rusher` | none | none | 121 | 25/25/11 | 28 | 0 | 571 |
| 61 | `utility_rusher_vs_rusher` | none | none | 121 | 25/25/11 | 26 | 0 | 571 |

## Design Read

- `utility_rusher` can stay as a hard stress bot if its high winrate is intentional.
- `utility_fortifier` needs a stronger win plan if it remains low-win and high-defense.
- `utility_economist` needs better conversion from economy into upgrades, expansion and territory pressure.
- `utility_opportunist` is the strongest candidate for a useful non-rusher personality.

