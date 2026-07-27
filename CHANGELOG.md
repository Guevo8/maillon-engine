# Changelog

## v0.4 — Prototype Core Analysis

Maillon v0.4 konkretisiert die v0.3-Board-Hypothese durch deterministische Analyse-Simulationen.

> Status: analysierter Prototypkern — noch nicht die spielbare Runtime.
> Regelkern dokumentiert in `docs/archive/maillon_v0_4_rules.md`.
> Analysebefunde dokumentiert in `docs/archive/analysis_findings_v0_4.md`.

### Added

- Analyseordner mit Einordnung: `analysis/README.md`
- Hauptsimulation: `analysis/takeover_analysis.py`
- v0.4-Hauptreport: `analysis/reports/takeover_report_3actions_v0_4.json`
- Hotspot-Report: `analysis/reports/hotspots_61_cap_aware_vs_rusher_v0_4.csv`
- v0.4-Regeldokumentation: `docs/archive/maillon_v0_4_rules.md`
- v0.4-Analysebefunde: `docs/archive/analysis_findings_v0_4.md`
- v0.4-Designnotizen: `docs/archive/design_notes_v0_4.md`
- kompakter Entwicklungslog: `docs/archive/dev_log_short.md`

### Analyzed

- 37er- und 61er-Hexboards
- Direct Takeover als Feldübernahme-Kern
- Raid-Kosten nach Support
- Ressourcen-Caps für Holz, Stein und Korn
- Rebuild/Umbau als Holz-Sink
- tiered cost scaling für Build und Field Upgrade
- Feld-Instabilität nach Raid
- 2 Aktionen vs. 3 Aktionen pro Zug
- Action-Log für Einzelaktionen
- Hotspot-Analyse chronisch umkämpfter Felder

### Current interpretation

- v0.1/v0.2 bleiben historische Runtime.
- v0.3 bleibt Board-Baseline-Hypothese.
- v0.4 ist der aktuell analysierte Prototypkern für die nächste Terminal-Version.

### Not included

- neue spielbare v0.4-Terminal-Runtime
- GUI
- Godot-/Engine-Integration
- Editor
- Utility-Scoring-Bot
- Core Level 3
- Repair/Stabilisieren
- Raid +1 Holz

---

## v0.3 — Board Baseline (geplant)

Maillon Pocket v0.3 ersetzt die 8-Feld-Liste durch ein räumliches Hex-Board.

### Ziel

- Hex-Nachbarschaft als räumliches Grundgesetz
- 37 Felder als Testboard (Seitenlänge 4 / axialer Radius 3)
- 61 Felder als Zieltest (Seitenlänge 5 / axialer Radius 4)
- Dorf/Core + Start-Holz statt Dorf + alle drei Ressourcentypen
- räumliches Bauen: Feld muss an eigenes Feld angrenzen
- Kampfwürfel-Formel neu kalibrieren (Frontfelder oder √n)
- Ressourcenlimit neu: Upkeep oder Hard Cap

### Nicht in v0.3

- Mehrspieler (3+)
- Named Combos
- Wonder
- Heilige Felder
- Fokus-Token
- Backend/KI
- GUI

### Nächster technischer Schritt

Analyse-Skript: Hex-Board erzeugen, Nachbarschaften berechnen,
Startpositionen setzen, Bauoptionen und Rush-Distanzen ermitteln.

Siehe `docs/archive/transition_v0_2_to_v0_3_scope.md` für vollständige Analyse.

---

## v0.2 — Neighbor Conflict Loop

Maillon Pocket v0.2 erweitert den spielbaren v0.1-Kern um den ersten echten Gegenspieler.

> Status: Conflict Prototype — technisch lauffähig, nicht mehr das Zielregelwerk.
> Übergang dokumentiert in `docs/archive/transition_v0_2_to_v0_3_scope.md`.

### Added

- Nachbar als regelbasierter Gegner
- Nachbar-Statusanzeige
- Nachbar-Ertrag und automatischer Nachbar-Zug
- Nachbar-Sieg bei 8 Feldern
- Raid als vierte Spieleraktion
- echte Mondrunde mit Würfelkonflikt
- Omen-Hinweis eine Runde vor der Mondrunde
- Feldübernahme bei deutlichem Konfliktsieg
- Bauen mit 2x W3 und Spielerwahl
- v0.2-Save-Struktur mit Spieler und Nachbar
- Regeldatei `docs/archive/rules_v0_2.md`

### Changed

- Upgrade ist nur noch auf aktive Nicht-Dorf-Felder möglich
- Statusanzeige während der Aktionsphase zeigt Spieler und Nachbar
- Savegame wird am normalen Rundenende nach Erhöhung des Rundenzählers gespeichert
- alte v0.1-Saves erzeugen beim Laden automatisch einen frischen Nachbar
- Mondrunde ist nicht mehr nur ein Marker, sondern ein echter Konflikt

### Not included

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

---

## v0.1 — Solo Resource Executor

Erste lauffähige Terminal-Version von Maillon Pocket.

### Added

- Ressourcen Holz, Stein und Korn
- Dorfkern und Startfelder
- Ertrag per W6
- Bauen
- Upgrade
- Aussetzen
- Überfluss-Check
- Mondrunde als Marker ohne Effekt
- Imperium-Sieg
- Ausdauer-Sieg
- JSON Save/Load
