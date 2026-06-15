# Entwicklungsnotiz — Der Schnitt zwischen v0.2 und v0.3

## Kurzfassung

Maillon hat mit v0.2 bewiesen, dass der Kern als Python-Terminalspiel funktioniert. Der Prototyp kann Ressourcen verwalten, Felder bauen, Upgrades anwenden, speichern, laden, einen regelbasierten Gegner steuern, Raids ausführen und Mondrunden-Konflikte auslösen.

Der Playtest hat aber ebenso klar gezeigt: v0.2 ist nicht das eigentliche Zielsystem. Es ist ein funktionierender Konflikt-Prototyp auf zu engem Raum. Das Spielgefühl kippt zu schnell, weil acht Felder, sofortiger Startbesitz und direkte Feldübernahme das System extrem komprimieren.

Der nächste Schritt ist deshalb nicht, v0.2 fein zu balancen, sondern v0.3 als räumlich saubere Board-State-Engine vorzubereiten.

---

## Was v0.2 geleistet hat

v0.2 war ein wichtiger technischer Durchbruch. Aus dem ursprünglichen Solo-Ressourcenmodell wurde eine erste Duell-Version. Der Spieler hatte nicht mehr nur einen Aufbaukreislauf, sondern einen Gegner, der ebenfalls Ressourcen sammelt, Felder besitzt und auf Sieg zusteuert.

Damit wurden mehrere Grundbausteine bestätigt:

- Das Terminal-Menü funktioniert als einfache spielbare Oberfläche.
- Save/Load ist stabil genug für weitere Tests.
- Ein regelbasierter Gegner ist ausreichend, um Druck zu erzeugen.
- Raid und Mondrunde aktivieren das Spiel sofort stärker als reines Sammeln.
- Feldübernahme ist als Konfliktfolge technisch machbar.
- Die Python-Struktur ist als Prototyping-Basis brauchbar.

Das ist wichtig: v0.2 war nicht verschwendet. Ohne diesen Stand wäre nicht sichtbar geworden, wo das Modell zu eng wird.

---

## Was der Playtest sichtbar gemacht hat

Der v0.2-Playtest hat gezeigt, dass der aktuelle Raum zu klein ist. Beide Seiten starten mit Dorf, Holz, Stein und Korn und brauchen nur wenige weitere Felder bis zum Sieg. Dadurch wird jede Feldübernahme sofort massiv.

Ein einzelner Feldwechsel bedeutet im kleinen 8-Feld-Modell nicht nur „ein Feld mehr“. Er bedeutet zugleich:

- mehr Produktion,
- mehr Kampfwürfel,
- weniger Optionen für den Gegner,
- stärkeren nächsten Raid,
- schnelleren Siegfortschritt.

Dadurch entsteht ein harter Snowball-Effekt. Wenn eine Seite einmal vorne liegt, verstärkt das System diesen Vorsprung. Zustände wie 6:4, 7:3 oder 8:2 entstehen zu schnell und fühlen sich weniger wie Strategie und mehr wie abrupte Eskalation an.

Das Problem liegt nicht nur in einzelnen Zahlen wie Raid-Bonus oder Feldübernahme-Schwelle. Das tiefere Problem ist, dass v0.2 Besitz, Produktion, Kampfkraft und Siegfortschritt zu stark in dieselbe Feldliste legt.

---

## Die wichtigste Erkenntnis

Ein Feld darf künftig nicht automatisch alles gleichzeitig sein.

In v0.2 bedeutet ein Feld praktisch:

- Es gehört jemandem.
- Es produziert.
- Es zählt für den Sieg.
- Es zählt als Kampfwürfel.
- Es kann direkt übernommen werden.

Für v0.3 muss das getrennt werden. Ein Feld ist zuerst ein Platz im Raum. Es hat Nachbarn, kann frei oder kontrolliert sein, kann aktiv oder inaktiv sein, kann produzieren oder nur Raum sichern, kann geschützt oder gefährdet sein.

Das ist der eigentliche Schnitt: Maillon wechselt von einer kleinen Feldliste zu einem räumlichen Board-State.

---

## Neue Board-Logik

v0.3 soll auf Hex-Nachbarschaft basieren. Das bedeutet nicht, dass Maillon ein analoges Brettspiel werden soll. Es bedeutet nur, dass der Raum nach einer klaren Nachbarschaftslogik funktioniert.

Ein Innenfeld hat bis zu sechs angrenzende Felder. Randfelder haben weniger. Diese Nachbarschaft bestimmt, wo gebaut werden kann, wo Fronten entstehen, wann ein Raid möglich wird und wie sich Spieler ausbreiten können.

Die natürliche Hex-Logik führt zu regulären Boardgrößen:

- 19 Felder: zu klein für das gewünschte Spielgefühl.
- 37 Felder: erstes sinnvolles Testboard.
- 61 Felder: Zieltest für strategischen Raum.
- 91 Felder: vorerst zu groß.

Für v0.3 wird deshalb festgehalten:

- 37 Felder dienen als erstes Testboard.
- 61 Felder bleiben der gedankliche Zieltest.
- 45 Felder werden nicht verworfen, aber vorerst nur als spätere Custom-Map betrachtet.

Damit wird der Raum nicht mehr improvisiert, sondern mathematisch sauber aus der Hex-Struktur abgeleitet.

---

## Neue Startlogik

Der Startzustand aus v0.2 wird ersetzt.

Statt mit Dorf, Holz, Stein und Korn gleichzeitig zu beginnen, soll jeder Spieler künftig mit einem Core und einem Start-Holzzugang starten.

Das Dorf beziehungsweise der Core ist kein normales Feld. Es ist der Basisanker. Es soll nicht wie ein gewöhnliches Produktionsfeld eroberbar sein. Es sichert die Kornversorgung oder erzeugt Korn, damit der Start nicht blockiert.

Das Start-Holz verhindert den Bau-Softlock. Wenn Bauen Holz kostet, muss Holz früh sicher zugänglich sein. Stein und weitere Ressourcentypen sollen nicht automatisch am Anfang vollständig vorhanden sein, sondern durch Ausbau, Entscheidung oder spätere Testregeln ins Spiel kommen.

Damit wird der Start weniger fertig und mehr erschließend.

---

## Was aus v0.2 erhalten bleibt

Die bestehenden Aktionen bleiben als Grundsprache des Spiels erhalten:

- Bauen
- Upgrade
- Aussetzen / Warten
- Raid
- Status

Auch der regelbasierte Gegner bleibt wichtig. Er wird aber langfristig eher als „Gegner“ oder „Akteur“ verstanden, nicht als „Nachbar“, weil „Nachbarn“ im Boardmodell angrenzende Felder meint.

Die v0.2-Codebasis bleibt also wertvoll. Sie zeigt, wie Aktionen, Gegnerzüge, Konflikte und Speichern grundsätzlich funktionieren. v0.3 muss diese Logik nicht wegwerfen, sondern in einen besseren Raum übertragen.

---

## Was vorerst gestrichen oder geparkt wird

Für den nächsten Schritt werden keine zusätzlichen Systeme eingebaut. Keine Lager, keine Schmiede, keine neuen Gebäudeketten, keine neuen Siegbedingungen, keine drei oder mehr Spieler.

Diese Ideen bleiben interessant, aber sie würden den nächsten Test verwässern. Zuerst muss geklärt werden, wie sich Raum, Abstand, Bauoptionen und Kontakt auf 37 und 61 Feldern verhalten.

Vorerst offen bleiben:

- Ressourcenlimit auf größeren Boards,
- Kampfwürfel-Formel,
- ob ein Feld weiterhin einem Kampfwürfel entspricht,
- direkte oder gestufte Feldübernahme,
- ob Upgrades nur Produktion oder auch Schutz geben,
- ob Feldtypen frei gewählt oder über `2x W3` bestimmt werden,
- neue Siegbedingungen auf größeren Boards.

Diese Punkte werden nicht vergessen. Sie werden bewusst nicht gleichzeitig verändert.

---

## Der neue Entwicklungsstand

Der Projektstand lässt sich jetzt so einordnen:

v0.1 war der Solo-Ressourcen-Executor.

v0.2 ist der Conflict Prototype. Er beweist, dass Gegner, Raid, Mondrunde und Save/Load funktionieren. Er zeigt aber auch, dass acht Felder und sofortiger Startbesitz das Spiel zu stark komprimieren.

v0.3 wird der Board-Baseline-Prototyp. Er soll nicht sofort ein fertiges neues Spiel werden, sondern zuerst den Raum korrekt herstellen: Hex-Nachbarschaft, 37-Felder-Test, 61-Felder-Zieltest, Core/Start-Holz und räumliches Bauen.

Der nächste technische Schritt ist deshalb kein Gameplay-Patch, sondern ein Analyse-Skript. Dieses Skript soll 37er- und 61er-Hexboards erzeugen, Nachbarschaften berechnen, Startpositionen setzen, baubare Felder anzeigen, Rush-Distanzen messen und zeigen, wie breit oder eng sich die Spieloptionen wirklich entwickeln.

---

## Leitsatz für die nächste Iteration

v0.2 beweist, dass Konflikt funktioniert.

v0.3 muss den Raum schaffen, in dem dieser Konflikt strategisch sinnvoll wird.
