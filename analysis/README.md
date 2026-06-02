# Analysis Tools

Stand: 02-06-2026  
Status: Arbeitsbereich für deterministische Design- und Balancing-Analysen.

## Zweck

Der Ordner `analysis/` enthält Analysewerkzeuge für Maillon. Diese Skripte sind **nicht** die finale Spiel-Runtime. Sie dienen dazu, Regelvarianten reproduzierbar zu simulieren und Designentscheidungen mit Messwerten zu prüfen.

Die Analyse beantwortet Fragen wie:

- Wie schnell entsteht Erstkontakt auf 37er- und 61er-Hexboards?
- Wann erreichen Spieler 60 Prozent Gebietskontrolle?
- Welche Ressourcen laufen zuerst ins Cap?
- Welche Bot-Policies erzeugen stabile Spiele oder Front-Stalls?
- Wie stark reduzieren tiered costs und Feld-Instabilität Raid-Pingpong?
- Welche Felder werden zu chronischen Front-Hotspots?

## Einordnung

Die Analysewerkzeuge bilden eine Zwischenschicht zwischen Design-Dokumentation und späterer Runtime:

```text
Regelidee
→ deterministische Simulation
→ JSON/CSV-Report
→ Auswertung
→ Regelentscheidung
→ spätere Terminal-/Game-Runtime
```

Das Ziel ist nicht, perfekte KI zu bauen. Die Bot-Policies sind regelbasierte Simulationsagenten, die unterschiedliche Spielweisen repräsentieren.

## Relevante Artefakte v0.4

Empfohlene Struktur:

```text
analysis/
  README.md
  takeover_analysis.py
  reports/
    takeover_report_3actions_v0_4.json
    hotspots_61_cap_aware_vs_rusher_v0_4.csv
```

Aktuell relevante Analyseartefakte:

| Datei | Zweck |
|---|---|
| `takeover_analysis.py` | Hauptsimulation für Board, Ressourcen, Bot-Policies, Raids und Hotspots |
| `reports/takeover_report_3actions_v0_4.json` | v0.4-Hauptreport mit 3 Aktionen pro Zug |
| `reports/hotspots_61_cap_aware_vs_rusher_v0_4.csv` | Hotspot-Auswertung des Stressfalls `61 / cap_aware_vs_rusher` |

## Empfohlene Ausführung

Report erzeugen:

```bash
python analysis/takeover_analysis.py --side-lengths 4 5 --max-rounds 80 --actions-per-turn 3 --format json > analysis/reports/takeover_report_3actions_v0_4.json
```

Hotspot-Report erzeugen, nachdem ein Action-Log vorhanden ist:

```bash
# Beispiel-Ausgabeziel:
analysis/reports/hotspots_61_cap_aware_vs_rusher_v0_4.csv
```

## Interpretation

Die Reports sind Messwerkzeuge, keine finalen Spielurteile. Besonders wichtig ist die Trennung zwischen:

- **normalen Referenzläufen** wie `rusher`, `expander`, `phase_player`,
- **Stressfällen** wie `cap_aware_vs_rusher`,
- und späteren menschlichen Playtests im Terminal.

Ein Ausreißer bedeutet nicht automatisch, dass die Regel falsch ist. Er kann auch anzeigen, dass eine Bot-Policy als Stressbot funktioniert und ein Extremverhalten sichtbar macht.

## Nicht-Ziele

Die Analyse ist vorerst nicht:

- finale Gegner-KI,
- Monte-Carlo-Suche,
- Reinforcement Learning,
- GUI,
- Godot-/Engine-Integration,
- finaler Editor.

Diese Themen bleiben spätere Ausbaustufen.
