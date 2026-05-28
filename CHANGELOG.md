# CHANGELOG

## v0.2 — Neighbor Conflict Loop

Maillon Pocket v0.2 erweitert den spielbaren v0.1-Kern um den ersten echten Gegenspieler.

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

### Changed

- Upgrade ist nur noch auf aktive Nicht-Dorf-Felder möglich
- Statusanzeige während der Aktionsphase zeigt Spieler und Nachbar
- Savegame wird am normalen Rundenende nach Erhöhung des Rundenizählers gespeichert
- alte v0.1-Saves erzeugen beim Laden automatisch einen frischen Nachbar

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
