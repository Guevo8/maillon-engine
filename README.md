# maillon-engine

Maillon Engine ist ein kleines textbasiertes Python-Terminalspiel. Das Projekt rekonstruiert den Maillon-/Holz+Stein-Prototyp als schlanke Ressourcen- und Konflikt-Engine.

In v0.2 spielen Spieler und Nachbar gegeneinander: Beide bauen ein 8-Feld-Maillon auf, sammeln Holz, Stein und Korn, verbessern Felder und geraten über Raid und Mondrunde in Konflikt. Der Nachbar ist keine komplexe KI, sondern ein regelbasierter Gegner, der als Bedrohungsuhr funktioniert.

## Start

Startbefehl:

    python main.py

Beim Start kannst du ein neues Spiel beginnen oder einen vorhandenen Spielstand laden.

Der Spielstand wird automatisch unter `data/savegame.json` gespeichert. Diese Datei ist bewusst in `.gitignore`, damit persönliche Testläufe nicht ins Repo wandern.

## Scope v0.2

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
