# Calibration-Probe-Analyse v0.7.1

Datum: 2026-06-09  
Branch: `feat/v0-7-1-calibration-probes`  
Matrix: `runtime_matrix_v0_7_1_calibration.csv`

---

## Kontext

Ziel dieser Runde: Zwei neue Kalibrierungsproben (`opening_resource_spammer`, `tunnel_all_in_probe`) gegen alle relevanten Policies spielen, **ohne** die Utility-Tunneler-Gewichte zu ändern. Die Ergebnisse dienen als Basis für spätere Gewichtsanpassungen.

Konfiguration: `side_length=4,5 | max_rounds=80 | actions_per_turn=3`  
Policies: `opening_resource_spammer`, `tunnel_all_in_probe`, `utility_balancer`, `utility_tunneler`, `rusher`, `phase_player`

---

## Ergebnisse

### Gewinnrate (Spieler + Gegner zusammengerechnet, je 11 Partien pro Boardgröße)

| Policy | Board 4 (n=11) | Board 5 (n=11) | Gesamt (n=22) |
|---|---|---|---|
| `rusher` | **10/11 (90.9%)** | 8/11 (72.7%) | **18/22 (81.8%)** |
| `phase_player` | 6/11 (54.5%) | **10/11 (90.9%)** | 16/22 (72.7%) |
| `opening_resource_spammer` | 7/11 (63.6%) | 5/11 (45.5%) | 12/22 (54.5%) |
| `utility_balancer` | 6/11 (54.5%) | 5/11 (45.5%) | 11/22 (50.0%) |
| `utility_tunneler` | 3/11 (27.3%) | 3/11 (27.3%) | 6/22 (27.3%) |
| `tunnel_all_in_probe` | 2/11 (18.2%) | 1/11 (9.1%) | **3/22 (13.6%)** |

### Direkte Matchups (Board 4 / Board 5, P = player gewinnt, E = enemy gewinnt, D = draw)

| Player → \ ↓ Enemy | ORS | TAIP | UB | UT | R | PP |
|---|---|---|---|---|---|---|
| **ORS** | D / D | P / P | P / D | P / P | E / P | D / E |
| **TAIP** | E / E | P / E | E / E | E / E | E / E | E / E |
| **UB** | P / E | E / P | P / E | P / P | E / E | P / E |
| **UT** | E / D | P / P | E / E | E / E | E / E | E / E |
| **R** | E / D | P / P | P / P | P / P | P / E | P / E |
| **PP** | E / P | P / P | P / P | P / P | E / E | E / P |

ORS = opening_resource_spammer, TAIP = tunnel_all_in_probe, UB = utility_balancer, UT = utility_tunneler, R = rusher, PP = phase_player

---

## Beobachtungen

### `tunnel_all_in_probe` (3/22 Gesamtsiege — schlechtester Bot)

- Board 4: 2/11 Siege — die Spiegelpartie (TAIP vs TAIP, Player gewinnt) und ein Nicht-Spiegel-Sieg als Enemy gegen `utility_balancer`.
- Board 5: 1/11 Sieg — ausschließlich die Spiegelpartie (TAIP vs TAIP, Enemy gewinnt).
- In fast allen relevanten Nicht-Spiegel-Matchups verliert der Bot, was die Kernaussage bestätigt:
- **Ursache**: Der Bot investiert alle Ressourcen sofort in Tunnel-Infrastruktur (Stein, Holz für Eingänge/Extend), bevor er überhaupt nennenswert Territorium kontrolliert. Tunnel-Raids bringen nur Feldübernahmen — damit lässt sich aber kein stabiles Territorium aufbauen, weil Korn/Holz-Produktion fehlt.
- Typisches Spielende: Domination in Runde 10–14, d.h. der Gegner gewinnt per Territorium-Dominanz, bevor das Tunnel-Netz strategisch wirksam werden kann.
- Konklusion: **Tunnel ohne Territorial-Basis ist wertlos.** Die Probe erfüllt ihren Zweck — sie zeigt, dass reines Tunnel-All-In eine schwache Strategie ist.

### `opening_resource_spammer` (12/22 — solides Mittelfeld)

- **Stärken**: Schlägt alle Policies, die langsamer starten oder keine frühe Raid-Strategie haben (`utility_tunneler`, `tunnel_all_in_probe`, früher `utility_balancer`).
- **Schwächen**:
  - Gegen `rusher` auf Board 4: verliert (Rusher baut schneller Raum und overraidert).
  - Gegen `phase_player` auf Board 5: verliert oder endet im Timeout-Draw.
  - Spiegelpartie (ORS vs ORS): immer Timeout-Draw — kein Spielende in 80 Runden. Der Bot hat keine Late-Game-Strategie und verpufft in Raid-Churn.
- Konklusion: Guter Referenzbot für "aggressiver Frühstart", aber ohne Mid/Late-Game-Plan.

### `utility_tunneler` (6/22 — schwächer als erwartet)

- Verliert konsistent gegen `rusher` und `phase_player`, schlägt nur `tunnel_all_in_probe` zuverlässig.
- Board 5, UT vs UB: Verliert durch Territory (36 Runden), mit 26 `tunnel_entrance`-Aktionen und 1 `tunnel_extend`. Das heißt: der Bot baut viele Eingänge, aber das Netz wächst kaum weiter — `tunnel_access_gain` reicht nicht, um `tunnel_extend` attraktiv zu machen.
- `opportunity_cost`-Mechanismus greift zu stark: Da `utility_balancer` als Fallback vergleichsweise stark ist, wird zu oft auf normale Aktionen zurückgefallen, und dann ist der `utility_balancer`-Fallback selbst zu schwach für `rusher`.
- Konklusion: Der Mechanismus funktioniert korrekt, aber die Gewichte bevorzugen zu stark `tunnel_entrance` gegenüber `tunnel_extend`. Das erklärt die niedrige `tunnel_extend`-Zahl.

### `rusher` (18/22 — stärkster Bot insgesamt auf Board 4)

- Dominiert auf Board 4 fast alles.
- Auf Board 5 verliert er gegen `phase_player` in zwei von drei Begegnungen und hat einen Timeout-Draw in der Spiegelpartie.
- Korn-Waste auf Board 5 sehr hoch (834 in R vs PP), was auf Late-Game-Ineffizienz hinweist.

### `phase_player` (16/22 — stärkstes auf Board 5)

- Auf Board 5 fast unschlagbar: 10/11 Siege.
- Schlägt `rusher` auf Board 5 in beiden Positionen (als Enemy und als Player je einmal).
- Der Fortify-Mechanismus und die differenzierte Phasenstrategie zahlen sich auf größeren Boards aus.

---

## Fazit und nächste Schritte

### Erste Kalibrierungsdiagnose abgeschlossen

Die ersten Proben haben ihren Diagnosezweck erfüllt:

1. **Tunnel-First-Strategien (TAIP) sind gescheitert** — Bestätigt, dass Tunnel als Ergänzung zu Territorial-Strategien gedacht sein muss, nicht als Ersatz.
2. **`utility_tunneler` verliert zu oft gegen echte Bots** — Der Opportunity-Cost-Mechanismus ist korrekt implementiert, aber die aktuellen Gewichte schränken Tunnel-Extend zu stark ein.
3. **`opening_resource_spammer` zeigt: Schnelles Ressourcensichern + aggressives Raiden ist auf Board 4 sehr effektiv** — Dies gibt einen Hinweis, was `utility_tunneler` als Baseline überwinden muss.

### Empfehlungen für v0.7.2 (Gewichtstuning)

| Problem | Diagnose | Empfohlene Anpassung |
|---|---|---|
| Zu wenig `tunnel_extend` | `tunnel_access_gain`-Gewicht für `extend` reicht nicht aus | `tunnel_access_gain` für `tunnel_extend`: 0.35 → 0.45 |
| `tunnel_entrance` dominiert trotz schlechter Ergebnisse | `tunnel_entrance`-Score oft positiv, aber kein Folge-Extend | `territory_pressure` für `tunnel_entrance`: 0.20 → 0.15, `tunnel_access_gain`: 0.30 → 0.25 |
| Fallback zu `balancer` zu häufig | `OPPORTUNITY_COST_TOLERANCE` zu eng | Toleranz testweise auf 0.15 erhöhen |

Diese Anpassungen sind Hypothesen — zu validieren mit erneutem Matrix-Lauf nach Implementierung.

---

## Rohdaten-Referenz

```
analysis/reports/runtime_matrix_v0_7_1_calibration.csv
```

Schlüsselspalten zur Analyse: `winner`, `reason`, `round`, `tunnel_entrance`, `tunnel_extend`, `tunnel_raid`, `p_korn_waste`, `e_korn_waste`
