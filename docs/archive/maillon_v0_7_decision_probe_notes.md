# Maillon v0.7 — Utility-Tunneler Decision Probe Notes

## Probe

Input:

- `analysis/reports/utility_tunneler_decision_probe_v0_7.csv`
- 13.401 candidate rows
- 143 chosen rows

## Candidate Distribution

| Action | Candidates | Chosen | Approx. Selection Rate |
|---|---:|---:|---:|
| tunnel_entrance | 1.218 | 71 | 5.83% |
| tunnel_extend | 11.741 | 19 | 0.16% |
| tunnel_raid | 75 | 18 | 24.00% |
| wait | 367 | 35 | 9.54% |

## Initial Interpretation

The Utility-Tunneler does not spam tunnel actions.

The strongest signal is that `tunnel_extend` dominates the candidate space but is rarely selected. This suggests that the bot sees many extension options but usually prefers the normal utility baseline.

This is not an OP signal. It points toward a conservative bot or an extension score that may be too weak compared to normal actions.

## Opportunity Cost

Chosen actions were mostly selected only when opportunity cost was zero or very low:

| Opportunity Cost Band | Chosen Rows |
|---|---:|
| 0.0000 | 77 |
| 0.0001–0.1000 | 60 |
| 0.1001–0.2500 | 6 |

No chosen action had opportunity cost above 0.25.

This indicates conservative action selection and no obvious tunnel exploit.

## Action Notes

### tunnel_entrance

`tunnel_entrance` is the most selected tunnel action. The bot opens tunnels regularly enough to use the mechanic.

### tunnel_extend

`tunnel_extend` has the largest candidate count but a very low selection rate. This is the main v0.7 tuning question.

Possible interpretations:

- Most extension options are correctly bad.
- The normal utility baseline is too dominant.
- Future tunnel value is underweighted.
- The bot opens tunnels but does not convert them into strategic routes often enough.

### tunnel_raid

`tunnel_raid` appears rarely but has the highest selection rate among tunnel actions. This looks healthy at first glance: raid is not spammed, but when available it can matter.

The next validation step should test whether chosen raids correlate with fast or unavoidable wins.

### wait

`wait` is selected 35 times. This is acceptable for now, but repeated early waits should be watched. If waits appear when legal useful actions exist, this may indicate missing fallback logic or overly strict scoring thresholds.

## Current Risk Assessment

| Risk | Current Signal |
|---|---|
| Tunnel spam | Low |
| Tunnel extend exploit | Low |
| Tunnel raid exploit | Not proven; requires outcome test |
| Bot too conservative | Medium |
| Normal baseline too dominant | Medium |
| Candidate explosion from tunnel_extend | Medium |
| Broken score scale | Low |

## Next Validation Question

The next required test is an outcome matrix:

- Winrate by matchup
- Average round count
- Win reason distribution
- Chosen tunnel actions per game
- Whether `tunnel_raid` leads to wins within a short number of rounds
- Whether `tunnel_extend` is underused despite plausible strategic positions

## Decision

Do not balance yet.

First create an outcome-level report. The current probe shows that the bot is technically functional and conservative, but it does not yet prove whether the tunnel strategy is strategically strong, weak, or merely situational.
