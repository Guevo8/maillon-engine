# Utility-Tunneler — Design-Plan v0.7

## Ziel

Der Utility-Tunneler ist ein isoliertes, erklärbares Bot-Modul, das Tunnel-Aktionen anhand eines Feature-basierten Scoring-Systems bewertet. Er ersetzt keine bestehenden Utility-Bots, sondern ergänzt das System als QA- und Balance-Werkzeug.

Policy-Name: `utility_tunneler`  
Modul: `src/maillon_v04/bot_utility_tunneler.py`

---

## Abgrenzung zu `tunnel_probe`

| Kriterium | tunnel_probe | utility_tunneler |
|---|---|---|
| Entscheidungslogik | Prioritätsbasierter Fallback-Baum | Feature-basiertes Scoring |
| Erklärbarkeit | Keine | Score + Reasons pro Kandidat |
| Opportunity Cost | Nein | Ja (normaler Utility-Score als Referenz) |
| Logging | Nein | Optional (JSONL) |
| Determinismus | Ja | Ja |
| Ziel | Beweist, dass Tunnelaktionen ausgeführt werden | Bewertet, OB Tunnelspiel besser ist |

---

## Abgrenzung zu `bot_utility.py`

`bot_utility.py` bewertet **alle** Aktionstypen (build, raid, fortify, etc.) mit Persönlichkeitsgewichten.

Der Utility-Tunneler bewertet **nur** Tunnel-Aktionen plus `wait`, nutzt aber den besten normalen Utility-Score als Opportunity-Cost-Referenz.

---

## Kandidaten-Aktionen (Layer 1)

- `tunnel_entrance` — neuer Eingang bauen
- `tunnel_extend` — Tunnel-Kante verlängern
- `tunnel_raid` — gegnerisches Feld per Tunnel übernehmen
- `repair_build` — kollabiertes Feld reparieren
- `wait` — immer enthalten als Fallback

Nur legal und bezahlbare Aktionen werden als Kandidaten generiert.

---

## Feature-Liste (Layer 2)

| Feature | Beschreibung |
|---|---|
| `resource_fit` | Anteil verbleibender Ressourcen nach Bezahlung (Slack) |
| `tunnel_access_gain` | Zuwachs erreichbarer Tunnel-Knoten durch diese Aktion |
| `enemy_tunnel_threat` | Tunnel-Druck des Gegners auf eigene Felder |
| `own_tunnel_pressure` | Druck am Quellknoten (nur tunnel_extend) |
| `collapse_risk` | Anteil eigener Felder nahe am Collapse-Threshold |
| `raid_value` | Feldwert + Schild-Bypass-Bonus (nur tunnel_raid) |
| `repair_value` | Anzahl eigener aktiver Nachbarn (nur repair_build) |
| `territory_pressure` | Gegner nahe am Siegschwellenwert + Rückstand |
| `normal_action_baseline` | Informativ: bester normaler Utility-Score / 60.0 |
| `opportunity_cost` | max(0, baseline - tunnel_score_raw) |

---

## Scoring (Layer 3)

```
weighted_sum = Σ (weight[feature] × feature_value)
tunnel_score = clamp(weighted_sum, 0.0, 1.0)
opportunity_cost = max(0.0, normal_baseline - tunnel_score)
```

Jeder Score wird als Reasons-Liste gespeichert.

---

## Opportunity Cost (Layer 4)

Der beste normale Utility-Score wird einmalig pro Entscheidung berechnet:

```python
best_raw = max(s.total_score for s in score_candidate_actions(state, actor, "balancer"))
normal_baseline = clamp(best_raw / 60.0, 0.0, 1.0)
```

Entscheidungsschwelle:

```
Tunnel-Aktion gewählt, wenn:
    best_tunnel.score >= normal_baseline - OPPORTUNITY_COST_TOLERANCE (= 0.10)
Sonst: Fallback auf besten normalen Utility-Zug
```

---

## Action Selection (Layer 5)

Deterministisch. Sortierung: `(-score, action_type_priority, coord_x, coord_y)`

Priority: `tunnel_raid=0, repair_build=1, tunnel_extend=2, tunnel_entrance=3, wait=4`

---

## Decision Logging (Layer 6)

Optional (deaktiviert per Default). Aktivierung via `log_path: Path`.

JSONL-Format (ein Eintrag pro Entscheidung):
```json
{
  "round": 12,
  "actor": "player",
  "policy": "utility_tunneler",
  "chosen_action": "tunnel_raid",
  "chosen_score": 0.82,
  "candidate_count": 7,
  "best_normal_score": 0.61,
  "opportunity_cost": 0.0,
  "top_candidates": [["tunnel_raid", 0.82], ["tunnel_extend", 0.55]],
  "top_reasons": [["raid_value", 0.45], ["enemy_tunnel_threat", 0.22]]
}
```

---

## Nicht-Ziele dieser Version

- Kein Minimax
- Kein tiefer Lookahead
- Keine Persönlichkeits-Varianten
- Keine Integration der Tunnel-Aktionen in den normalen Utility-Scorer
- Keine automatische Runtime-Matrix-Integration (manuell möglich über `--policies utility_tunneler`)

---

## Analyse-Tools

| Datei | Zweck |
|---|---|
| `analysis/utility_tunneler_smoke.py` | 7 Smoke-Tests: Kandidaten, Scores, Opportunity Cost, Dispatch |
| `analysis/utility_tunneler_decision_probe.py` | Per-Entscheidungs-CSV für Matchup-Analyse |
