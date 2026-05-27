# maillon-engine

Maillon Pocket Solo v0.1 ist ein kleines textbasiertes Python-Terminalspiel. Es rekonstruiert den Maillon-/Holz+Stein-Prototyp als schlanke Ressourcen-Engine: Du sammelst Holz, Stein und Korn, baust Felder, verbesserst Felder zu Spezialfeldern und erreichst den Imperium- oder Ausdauer-Sieg.

## Start

Startbefehl:

python main.py

Beim Start kannst du ein neues Spiel beginnen oder einen vorhandenen Spielstand laden. Der Spielstand wird automatisch unter data/savegame.json gespeichert; diese Datei ist bewusst in .gitignore, damit persönliche Testläufe nicht ins Repo wandern.

## Scope v0.1

Enthalten sind Solo-Spiel, Ressourcen Holz/Stein/Korn, Dorfkern, maximal 8 Felder, Ertrag per W6, Bauen, Upgrade, Aussetzen, Überfluss-Check, Mondrunde als Marker ohne Effekt, Imperium-Sieg, Ausdauer-Sieg und JSON Save/Load.

Nicht enthalten sind Raid, echter Mondrunden-Konflikt, Multiplayer, Items, Crafting, Gebäude, GUI, Tests, Jahreszeiten, Bürger, Lager und Reichweite.
