# Maillon Engine

![Regression](https://github.com/Guevo8/maillon-engine/actions/workflows/regression.yml/badge.svg)

> Rundenbasiertes Hex-Strategiespiel mit Ressourcenmanagement, Gebietskontrolle und Tunnelsystem.

Maillon begann als Python-Terminalspiel und entwickelte sich über mehrere Regel-, Bot- und Validierungsphasen zu einem spielbaren Strategieprototyp.

Aktuell spielt eine Person gegen computergesteuerte Gegner mit unterschiedlichen Strategien. Der bestehende Python-Prototyp bildet die Grundlage für eine grafische Umsetzung in Godot 4.

## Schnellstart

Vorausgesetzt wird eine aktuelle Python-3-Installation. Zusätzliche Pakete werden derzeit nicht benötigt.

```bash
git clone https://github.com/Guevo8/maillon-engine.git
cd maillon-engine
python -m src.maillon_v04.terminal
```

Beim Start können Boardgröße und Gegner ausgewählt werden.

## Spielprinzip

Beide Seiten starten an gegenüberliegenden Enden eines Hexboards und erweitern ihr Gebiet über angrenzende Felder.

Kontrollierte Felder produzieren:

- Holz
- Stein
- Korn

Die Ressourcen werden für Expansion, Angriffe, Verteidigung, Umbauten und Aufwertungen eingesetzt. Begrenzte Speicherkapazitäten erhöhen den Entscheidungsdruck und verhindern unbegrenztes Ansammeln.

Eine Partie wird über Gebietskontrolle entschieden.

## Enthaltene Mechaniken

- Hexboards in mehreren Größen
- mehrere Aktionen pro Zugphase
- räumliches Bauen und Expansion
- Feld- und Basisaufwertungen
- Umbau von Produktionsfeldern
- Raid und direkte Feldübernahme
- Verteidigung und Schutzwerte
- wechselnde Initiative
- Tunnelbau, Tunnelerweiterung und Tunnelangriffe
- lokale Tunnelbelastung und Feldkollaps
- Reparatur kollabierter Felder
- mehrere Bot-Strategien

## Bots und Balancing

Maillon enthält Gegner mit festen Prioritäten sowie Bots, die mögliche Aktionen anhand gewichteter Merkmale des Spielzustands bewerten.

Zusätzliche Probe-Bots untersuchen gezielt bestimmte Spielweisen:

- schnelle Expansion
- frühe Aggression
- Ressourcenfokus
- defensiver Aufbau
- Tunnel-All-In
- ausgewogenes Utility-Spiel

Automatisierte Partien erfassen unter anderem Gewinnraten, Aktionshäufigkeiten, Ressourcennutzung, Gebietsentwicklung und strategische Auffälligkeiten.

Der Ordner `analysis/` enthält die zugehörigen Regressionstests, Simulationen und ausgewählten Auswertungen.

## Tests ausführen

Zentrale Regelregression:

```bash
python -m analysis.pre_godot_rule_regression
```

Weitere relevante Prüfungen:

```bash
python -m analysis.bot_behavior_characterization
python -m analysis.main_action_regression_smoke
python -m analysis.tunnel_action_smoke_suite
python -m analysis.utility_tunneler_smoke
```

## Repository-Struktur

| Bereich | Inhalt |
|---|---|
| `src/maillon_v04/` | Spielzustand, Board, Regeln, Aktionen, Engine, Bots und Terminalclient |
| `analysis/` | Regressionen, Simulationen, Bot-Matrizen und Balancing-Auswertungen |
| `docs/` | Regeln, Architektur, Entwicklungsstände und Designentscheidungen |
| `tools/` | Hilfswerkzeuge, aktuell insbesondere deterministischer Fixture-Export für den Godot-Port |
| `port/` | Godot-Port-Fixtures und Fixture-Schema als Referenzdaten |
| `legacy/` | Historische Prototypen, nicht aktueller Einstiegspunkt |
| `.github/workflows/` | Automatisierte Regressionen über GitHub Actions |

## Projektstatus

Maillon ist aktuell:

- ein funktionsfähiger Python-Regelkern
- ein spielbarer Terminal-Prototyp
- ein Bot- und Balancing-Labor

Die zentralen Mechaniken sind implementiert und durch automatisierte Regressionen abgesichert.

Der nächste Meilenstein ist die Vorbereitung eines visuellen Clients für die Portierung nach Godot 4.

## Dokumentation

- [Bot-Architektur](docs/bot_architecture_overview.md)
- [Utility-Gewichtung und Tunneler-Overlay](docs/utility_weighting_mechanics.md)
- [Analysewerkzeuge und Reports](analysis/README.md)
- [Entwicklungsverlauf](CHANGELOG.md)
- [Historische Dokumente](docs/archive/)

## Lizenz

Maillon Engine steht unter der [MIT-Lizenz](LICENSE).
