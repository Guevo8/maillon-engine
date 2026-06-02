# maillon-engine

Maillon Engine ist ein kleines textbasiertes Python-Terminalspiel und ein experimenteller Regelkern für ein ressourcenbasiertes Gebietskontrollspiel.

Der aktuelle Projektstand besteht aus drei Schichten:

```text
v0.1/v0.2 = historische Runtime
v0.3      = Board-Baseline-Hypothese
v0.4      = analysierter Prototypkern
```

Die vorhandene spielbare Runtime basiert noch auf v0.2: Spieler und Nachbar bauen ein 8-Feld-Maillon auf, sammeln Holz, Stein und Korn, verbessern Felder und geraten über Raid und Mondrunde in Konflikt. Der Nachbar ist keine komplexe KI, sondern ein regelbasierter Gegner, der als Bedrohungsuhr funktioniert.

v0.3 beschreibt den Übergang zu einem räumlichen Hex-Board mit 37er- und 61er-Testboards. v0.4 konkretisiert diese Board-Hypothese durch deterministische Analyse-Simulationen und dient als Grundlage für die nächste spielbare Terminal-Version.

## Start

Startbefehl für die historische Terminal-Runtime:

    python main.py

Beim Start kannst du ein neues Spiel beginnen oder einen vorhandenen Spielstand laden.

Der Spielstand wird automatisch unter `data/savegame.json` gespeichert. Diese Datei ist bewusst in `.gitignore`, damit persönliche Testläufe nicht ins Repo wandern.

## Aktueller Dokumentationsstand

| Bereich | Datei | Zweck |
|---|---|---|
| v0.2 Runtime | `docs/rules_v0_2.md` | historisches spielbares Regelwerk |
| v0.3 Board-Hypothese | `docs/rules_v0_3_board_baseline.md` | Hex-Board, 37/61 Felder, räumliches Bauen |
| v0.4 Prototypkern | `docs/maillon_v0_4_rules.md` | aktuell analysierter Regelkern |
| v0.4 Analysebefunde | `docs/analysis_findings_v0_4.md` | zentrale Ergebnisse der Simulationen |
| v0.4 Designnotizen | `docs/design_notes_v0_4.md` | offene Optionen und spätere Kandidaten |
| Kurzchronologie | `docs/dev_log_short.md` | kompakter Entwicklungsverlauf |
| Analysewerkzeuge | `analysis/README.md` | Einordnung der Analyse-Skripte und Reports |

## Analysewerkzeuge

Der Ordner `analysis/` enthält deterministische Design- und Balancing-Werkzeuge. Diese Skripte sind nicht die finale Spiel-Runtime. Sie dienen dazu, Regelvarianten, Bot-Policies, Ressourcendruck, Raid-Verhalten und Front-Hotspots reproduzierbar zu testen.

Aktuell relevante Artefakte:

```text
analysis/takeover_analysis.py
analysis/reports/takeover_report_3actions_v0_4.json
analysis/reports/hotspots_61_cap_aware_vs_rusher_v0_4.csv
```

## Scope v0.2 Runtime

Enthalten sind:

- Solo-Terminalspiel
- Ressourcen Holz, Stein und Korn
- Dorfkern und maximal 8 Felder
- Spieler und Nachbar
- Nachbar als regelbasierter Gegner
- Ertrag per W6
- Bauen mit 2x W3 und Spielerwahl
- Upgrade aktiver Felder
- Aussetzen
- Raid
- echte Mondrunde
- Omen vor Mondrunde
- Überfluss-Check
- Imperium-Sieg
- Ausdauer-Sieg
- Nachbar-Sieg
- JSON Save/Load mit v0.1-Backward-Compatibility

Nicht enthalten sind:

- Nachbar-Profile
- Sabotage
- Stagnationssystem
- Fokus-Token
- Hex-Alterung
- Named Combos
- Heilige Felder
- Wonder
- Backend/KI
- GUI

## Nächster Entwicklungsschritt

Der nächste Hauptschritt ist die Vorbereitung einer neuen Terminal-Runtime auf Basis des v0.4-Prototypkerns:

- BoardState für Hex-Board.
- Ressourcenstand und Caps.
- gültige Aktionen pro Zustand.
- Untermenüs für Build, Raid, Rebuild, Field Upgrade und Core Upgrade.
- einfacher Gegnerbot.
- später wieder Save/Load.
