# Changelog

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

Siehe `docs/transition_v0_2_to_v0_3_scope.md` für vollständige Analyse.

---

## v0.2 — Neighbor Conflict Loop

Maillon Pocket v0.2 erweitert den spielbaren v0.1-Kern um den ersten echten Gegenspieler.

> Status: Conflict Prototype — technisch lauffähig, nicht mehr das Zielregelwerk.
> Übergang dokumentiert in `docs/transition_v0_2_to_v0_3_scope.md`.

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
- Regeldatei `docs/rules_v0_2.md`

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
