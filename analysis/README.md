# Analysis Tools

Stand: 03-06-2026  
Status: Arbeitsbereich für deterministische Design- und Balancing-Analysen.

## Zweck

Der Ordner `analysis/` enthält Analysewerkzeuge für Maillon. Diese Skripte sind **nicht** die finale Spiel-Runtime. Sie dienen dazu, Regelvarianten reproduzierbar zu simulieren und Designentscheidungen mit Messwerten zu prüfen.

Die Analyse beantwortet Fragen wie:

- Wie schnell entsteht Erstkontakt auf 37er- und 61er-Hexboards?
- Wann erreichen Spieler 60 Prozent Gebietskontrolle?
- Wann greift Domination-Win?
- Wann greift Full-Board-Majority-Win?
- Welche Ressourcen laufen zuerst ins Cap?
- Wie stark wirkt Fortify / Raid-Shield?
- Wie viele Raids führen zu echten Takeovers?
- Wie viele Raids werden durch Schutz absorbiert?
- Welche Bot-Policies erzeugen stabile Spiele oder Front-Stalls?
- Wie stark beeinflusst die Zugreihenfolge das Ergebnis?

Das Ziel ist nicht, jeden Playtest dauerhaft zu speichern, sondern die Werkzeuge und ausgewählte Meilenstein-Reports zu behalten, die Designentscheidungen nachvollziehbar machen.

## Source of Truth

Primäre Quelle der Wahrheit:

- `src/maillon_v04/` — Spielregeln, Engine, Actions, Bot-Logik
- `analysis/*.py` — reproduzierbare Analyse-Skripte
- ausgewählte Dateien in `analysis/reports/` — benannte Meilenstein-Reports

Nicht primäre Quelle der Wahrheit:

- `runs/latest_run.jsonl`
- `runs/latest_state.json`
- `runs/latest_summary.json`
- `runs/latest_digest.txt`

Diese Runtime-Dateien entstehen bei lokalen Playtests und bleiben ignoriert. Sie sind wertvoll für die aktuelle Auswertung, aber nicht als dauerhaftes Repo-Artefakt gedacht.

## Current Analysis Tool

### `fortify_bot_matrix.py`

Dieses Skript erzeugt Bot-vs-Bot-Balancing-Matrizen für:

- Boardgröße 37 und 61
- `phase_player`
- `rusher`
- Fortify / Raid-Shield
- Raid-Takeovers vs. shield-absorbed raids
- Turn-Order-Analyse
- Ressourcen-Waste
- finalen Gebietszustand

Beispiel:

```bash
python analysis/fortify_bot_matrix.py \
  --side-lengths 4 5 \
  --max-rounds 120 \
  --actions-per-turn 3 \
  --out analysis/reports/fortify_bot_matrix_v0_4.csv
```

## Milestone Reports

### `fortify_bot_matrix_turn_order_v0_4.csv`

Zweck:

- testete feste Zugreihenfolge `player_first` vs. `enemy_first`
- zeigte, dass der zuerst handelnde Akteur jedes Matchup gewann
- führte zur Alternating-Initiative-Regel

Hauptschluss:

- der frühere Player-Vorteil war primär ein Initiative-/First-Actor-Vorteil

### `fortify_bot_matrix_alternating_fullboard_v0_4.csv`

Zweck:

- testete Alternating Initiative plus Full-Board-Majority-Win
- bestätigte, dass volle Boards nicht mehr ohne Sieger bis zum Max-Round-Limit laufen müssen
- erzeugte brauchbarere Balancing-Signale als feste Zugreihenfolge

Hauptschluss:

- Alternating Initiative reduziert First-Actor-Dominanz
- Full-Board-Majority ist nötig, wenn das Board vollständig besetzt ist und weder 60-Prozent-Sieg noch Domination-Win greift

## Commit Policy

Committen:

- wiederverwendbare Analyse-Skripte
- kleine Meilenstein-CSV-Reports
- Reports, die eine Designentscheidung begründen
- Dokumentation, die Analyseparameter und Interpretation erklärt

Nicht committen:

- rohe `runs/latest_*` Dateien
- große experimentelle Batch-Läufe
- doppelte Scratch-CSV-Dateien
- temporäre Diagnose-Dateien ohne Designrelevanz

Für große spätere Simulationen sollten kompakte Summaries oder ausgewählte Snapshots commitfähig sein, nicht die komplette Rohdatenmenge.

## Current v0.4 Rule Patches Reflected Here

Dieser Analyse-Stand spiegelt folgende v0.4-Regeländerungen wider:

- Domination-Win
- Fortify / Raid-Shield
- konservative Fortify-Bot-Heuristik
- Alternating Initiative für Bot-vs-Bot
- Full-Board-Majority-Win

## Interpretation Notes

Die Reports sind keine endgültige Balance-Aussage. Sie sind Messpunkte.

Aktueller Arbeitsstand:

- Fortify wirkt messbar als defensive Bremse gegen direkte Raid-Takeovers.
- `rusher` bleibt ein Stressbot und sollte nicht als normaler Spielstandard gelesen werden.
- `phase_player_vs_phase_player` ist aktuell der wichtigste Referenzlauf.
- 37er Board eignet sich für schnelle Crash- und Extremtests.
- 61er Board eignet sich besser für Standard-Balancing.

Bei jeder neuen Regeländerung sollten die bestehenden Matrix-Reports nicht überschrieben, sondern als neuer benannter Snapshot erzeugt werden.
