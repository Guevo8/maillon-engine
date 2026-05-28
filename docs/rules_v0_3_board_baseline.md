# Maillon v0.3 — Board Baseline & Rule Update Draft

## Zweck

Dieses Dokument hält die nächste Regel- und Strukturentscheidung nach dem v0.2-Playtest fest.

v0.2 bleibt als **Conflict Prototype** erhalten: technisch funktionsfähig, aber strukturell zu eng, weil Startbesitz, Produktion, Kampf und Sieg zu stark in einer kleinen Feldliste zusammenfallen.

v0.3 ist kein Balance-Patch von v0.2, sondern ein neuer Board-Baseline-Entwurf.

## Kernentscheidung

Maillon nutzt künftig **Hex-Nachbarschaft als räumliches Grundgesetz**.

Das bedeutet:

- Ein Innenfeld hat maximal 6 angrenzende Felder.
- Randfelder haben weniger angrenzende Felder.
- „Nachbarn“ bezeichnet angrenzende Felder, nicht mehrere Gegner.
- Das Board beschreibt Raum, Nähe, Fronten, Baurichtung und Raid-Reichweite.
- Der Boardplatz gibt nicht automatisch den Ressourcentyp vor.

## Natürliche Hexgrößen

Für ein reguläres Hexfeld mit Seitenlänge `s` gilt:

```text
Feldzahl = 3s(s - 1) + 1
Reihenzahl = 2s - 1
maximaler Durchmesser in Hex-Schritten = 2(s - 1)
```

Relevante Größen:

```text
Seitenlänge 3: 19 Felder | 5 Reihen | zu klein
Seitenlänge 4: 37 Felder | 7 Reihen | erstes sauberes Testboard
Seitenlänge 5: 61 Felder | 9 Reihen | Zieltest / strategischer Raum
Seitenlänge 6: 91 Felder | 11 Reihen | vorerst zu groß
```

## Entscheidung: 37 und 61

Für v0.3 werden zwei natürliche Hexgrößen betrachtet:

```text
37 Felder = Testboard
61 Felder = Zieltest
```

37 ist das erste sinnvolle saubere Minimum. Es ist klein genug für schnelle Tests, aber groß genug, um nicht sofort wie ein 8-Feld-Rennen zu wirken.

61 ist das gedankliche Zielboard für echtes strategisches Spielgefühl: mehr Flanken, mehr Aufbauzeit, mehr Ausweichbewegung, mehr Raum für Rush, Breite und defensive Verdichtung.

45 wird vorerst nicht als Standard übernommen, weil es kein reguläres Hexfeld ist. 45 bleibt später als Custom-Map oder Szenario-Variante denkbar.

## Startlogik

Der Start soll Softlocks verhindern und trotzdem nicht mit allen Ressourcentypen vollständig entwickelt beginnen.

Arbeitsentscheidung:

```text
Jeder Spieler startet mit:
- 1 Dorf / Core
- 1 Start-Holzzugang
```

Dorf / Core:

- ist kein normales eroberbares Feld
- produziert oder sichert Kornversorgung
- dient als Basisanker
- soll nicht wie ein gewöhnliches Produktionsfeld behandelt werden

Start-Holz:

- verhindert Bau-Softlock
- ist der erste Expansionsanker auf dem Board
- liegt fair und gespiegelt zum gegnerischen Start-Holz

Stein und weitere Ressourcenfelder sollen durch Ausbau/Entscheidung entstehen, nicht automatisch von Anfang an vollständig vorhanden sein.

## Spiellogik, die vorerst stabil bleibt

Die bestehenden v0.2-Aktionen bleiben als Basisset erhalten:

```text
Bauen
Upgrade
Aussetzen / Warten
Raid
Status
```

Wichtig: v0.3 ändert zuerst den Raum, nicht alle Regeln gleichzeitig.

Das bedeutet:

- keine Lager-Regel in diesem Schritt
- keine Schmiede-Regel in diesem Schritt
- keine neuen Gebäudeketten in diesem Schritt
- keine neuen Siegbedingungen in diesem Schritt
- keine 3+ Spieler in diesem Schritt

## Feldtyp und Boardtyp

Der Boardplatz bestimmt in v0.3 nicht automatisch den Ressourcentyp.

Arbeitsregel:

```text
Board = Position / Nachbarschaft / Raum
Feldtyp = Ergebnis einer Bauentscheidung
```

Damit bleiben mehrere Strategien möglich:

- direkter Rush Richtung Gegner
- breite Expansion
- defensive Verdichtung
- früher Raid
- ressourcenorientierter Aufbau
- Upgrade-orientierter Aufbau

Ob der Feldtyp beim Bauen frei gewählt wird oder weiterhin über `2x W3, wähle 1` entsteht, bleibt eine gesonderte Testvariable.

## Bau-Logik im Boardmodell

Bauen soll künftig räumlich geprüft werden:

```text
Ein Feld ist baubar, wenn:
- es innerhalb des Boards liegt
- es noch neutral / frei ist
- es an mindestens ein eigenes Boardfeld grenzt
```

Die Auswahl im Terminal soll nur gültige Optionen zeigen, nicht das gesamte Board.

Beispiel:

```text
Baubare Felder:
[12] Richtung Mitte
[18] linke Flanke
[19] rechte Flanke
```

## Gegner / Nachbar

Für v0.3 bleibt es bei 2 aktiven Akteuren:

```text
Spieler
Gegner
```

Der alte Begriff `Nachbar` aus v0.2 bezeichnet im Code den Gegner, sollte langfristig aber nicht mit Nachbarschaft im Board verwechselt werden.

Langfristig sollte das Datenmodell mehrere Akteure erlauben. 3+ Spieler werden aber vorerst nicht umgesetzt, weil sie Dogpiling, Mehrfrontenlogik und zusätzliche Balanceprobleme erzeugen.

## Testlogik

v0.3 soll nicht sofort alle Regeln umbauen. Stattdessen werden Boardgrößen und Raumwirkung getestet.

Zu vergleichen:

```text
37 Felder
61 Felder
```

Messfragen:

- Wie viele Runden dauert ein direkter Rush bis zum ersten Kontakt?
- Wie viele baubare Optionen entstehen pro Runde?
- Wie schnell wird die Auswahl im Terminal unübersichtlich?
- Wie stark unterscheidet sich Rush von breiter Expansion?
- Ab wann wird Raid möglich?
- Wie stark beeinflusst die Boardgröße Feldübernahme und Snowballing?
- Ab wann werden Upgrades sinnvoller als weiteres Bauen?

## Offene Regelparameter

Diese Punkte werden bewusst noch nicht final entschieden:

- Ressourcenlimit bei größerem Board
- Kampfwürfel-Formel
- ob 1 Feld = 1 Kampfwürfel haltbar bleibt
- Feldübernahme sofort oder gestuft
- ob Upgrades nur Produktion oder auch Schutz/Stabilität geben
- ob Feldtyp frei gewählt oder weiter über `2x W3` bestimmt wird
- genaue Siegbedingungen auf 37/61 Feldern

## Aktuelle Interpretation von v0.2

v0.2 ist als technischer Proof gültig:

- Nachbar funktioniert
- Raid funktioniert
- Mondrunde funktioniert
- Save/Load funktioniert
- Konflikt aktiviert das Spiel

Aber v0.2 ist nicht das finale Regelmodell:

- 8 Felder sind zu eng
- Start mit zu vielen Besitzfeldern verzerrt das Spiel
- Feldübernahme ist auf kleinem Board extrem swingy
- Upgrades haben kaum Zeit, relevant zu werden
- Board-/Raumlogik fehlt

## Nächster technischer Schritt

Vor weiterem Gameplay-Patching soll ein Analyse-Skript entstehen:

```text
scripts/analyze_hex_growth.py
```

Aufgaben:

- reguläre Hexboards mit 37 und 61 Feldern erzeugen
- Nachbarschaften berechnen
- Startpositionen setzen
- baubare Felder pro Runde ermitteln
- direkte Rush-Distanzen messen
- Breitenoptionen zählen
- erste Kontaktpunkte bestimmen

Erst danach sollten Ressourcen, Kampf und Feldübernahme auf dem neuen Board erneut bewertet werden.
