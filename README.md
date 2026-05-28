# maillon-engine

Maillon Pocket ist ein textbasiertes Python-Terminalspiel. Du und ein regelbasierter Nachbar bauen gleichzeitig ein 8-Feld-Maillon auf — wer zuerst 8 Felder hat, gewinnt.

## Start

Startbefehl:

    python main.py

Beim Start kannst du ein neues Spiel beginnen oder einen vorhandenen Spielstand laden. Der Spielstand wird automatisch unter `data/savegame.json` gespeichert; diese Datei ist bewusst in `.gitignore`, damit persönliche Testläufe nicht ins Repo wandern.

## Scope v0.2

Enthalten sind Spieler + Nachbar als Gegner, Ressourcen Holz/Stein/Korn, Dorfkern, maximal 8 Felder pro Seite, Ertrag per W6, Bauen mit 2x W3 und Spielerwahl, Upgrade, Aussetzen, Raid, echte Mondrunde mit Würfelkonflikt, Omen-Hinweis, Feldübernahme, Überfluss-Check für beide Akteure, Imperium-Sieg, Ausdauer-Sieg, Nachbar-Sieg und JSON Save/Load.

Nicht enthalten sind Nachbar-Profile, Sabotage, Stagnation, Fokus-Token, Hex-Alterung, Named Combos, Heilige Felder, Wonder, VP-System, Multiplayer, GUI, Tests, Backend und KI.

## v0.2 — Neighbor Conflict Loop

v0.2 erweitert den v0.1-Kern um:

- **Nachbar** als einfachen Gegner (Bedrohungsuhr, kein input())
- **Raid** als vierte Spieler-Aktion (1 Aktion, keine Ressourcenkosten)
- **Echte Mondrunde** mit Würfelkonflikt und Feldübernahme
- **2x W3 Bauwahl** — Spieler wählt zwischen zwei gewürfelten Typen
- **Upgrade-Fix** — nur aktive Felder können upgegradet werden
- **Save-Kompatibilität** — alte v0.1-Saves crashen nicht
