# Maillon Pocket v0.2 — Regelwerk

## Ziel von v0.2

Maillon Pocket v0.2 macht aus dem Solo-Ressourcen-Executor von v0.1 die erste echte Duell-Version.

Spieler und Nachbar bauen gleichzeitig ein 8-Feld-Maillon auf. Der Spieler kann bauen, upgraden, aussetzen oder raiden. Der Nachbar erntet, baut oder setzt aus. Alle vier Runden erzwingt die Mondrunde einen Konflikt.

Der zentrale Test von v0.2 lautet:

> Wenn ich nichts tue, werde ich dann bestraft?

## Startzustand Spieler

Ressourcen:

- Holz: 2
- Stein: 1
- Korn: 1

Felder:

- Dorf
- Holz
- Stein
- Korn

Maximal 8 Felder. Das Dorf zählt mit.

## Nachbar

Der Nachbar ist keine echte KI, sondern ein regelbasierter Gegner.

Startzustand:

- Holz: 2
- Stein: 1
- Korn: 1
- Felder: Dorf, Holz, Stein, Korn

Der Nachbar hat ebenfalls maximal 8 Felder.

## Nachbar-Zug

Nach den Spieleraktionen erhält der Nachbar Ertrag und führt dann seinen Zug aus.

Wenn der Nachbar bauen kann, baut er.

Baukosten:

- 2 Holz
- 1 Korn

Wenn der Nachbar nicht bauen kann, setzt er aus.

Beim Aussetzen würfelt der Nachbar W4:

- 1 = +1 Korn
- 2 = +1 Holz
- 3 = +1 Stein
- 4 = +2 auf die Ressource mit dem niedrigsten Bestand

Bei Gleichstand gilt die Priorität:

Holz vor Stein vor Korn.

## Bauen v0.2

Bauen kostet:

- 2 Holz
- 1 Korn

Der Spieler würfelt zweimal W3.

Tabelle:

- 1 = Korn
- 2 = Holz
- 3 = Stein

Der Spieler wählt einen der beiden gewürfelten Feldtypen. Wenn beide Würfe denselben Typ ergeben, wird dieser Typ gebaut.

Das neue Feld wird ab der nächsten Runde aktiv.

## Upgrade

Upgrade kostet:

- 3 Stein

Effekt:

- Das Feld wird Spezial.
- Spezialfelder erzeugen bei einer 6 +2 statt +1.

Einschränkungen:

- Dorf darf nicht upgegradet werden.
- Jedes Feld darf nur einmal upgegradet werden.
- Nur aktive Felder dürfen upgegradet werden.

Frisch gebaute Felder dürfen also erst ab ihrer Aktivierungsrunde upgegradet werden.

## Raid

Raid kostet:

- 1 Aktion
- keine Ressourcen

Ablauf:

- Spieler würfelt 1W6 pro eigenem Feld.
- Nachbar würfelt 1W6 pro eigenem Feld.
- Spieler erhält +2 Initiative-Bonus.
- Höhere Summe gewinnt.
- Bei Gleichstand gewinnt der Nachbar als Verteidiger.

Wenn der Spieler gewinnt:

- Spieler nimmt 2 Ressourcen eines gewählten Typs vom Nachbarn.
- Wenn der Nachbar weniger als 2 davon hat, nimmt der Spieler nur den vorhandenen Bestand.
- Ab Runde 5 und bei Vorsprung >= 5 übernimmt der Spieler zusätzlich das neueste Nicht-Dorf-Feld des Nachbarn.

Wenn der Spieler verliert:

- Nachbar nimmt 1 Ressource vom Spieler.
- Ab Runde 5 und bei Vorsprung >= 5 übernimmt der Nachbar zusätzlich das neueste Nicht-Dorf-Feld des Spielers.

## Feldübernahme

Bei Feldübernahme wird immer das neueste Nicht-Dorf-Feld des Verlierers übernommen.

Das Dorf darf nie übernommen werden.

Ein übernommenes Feld wird beim Gewinner angehängt und ist frühestens ab der nächsten Runde aktiv.

## Omen

Eine Runde vor jeder Mondrunde erscheint ein Hinweis:

- Runde 3
- Runde 7
- Runde 11
- Runde 15

Text:

🌘 Omen: Die Mondrunde naht. Bereite dich vor.

Das Omen hat keinen eigenen Spieleffekt.

## Mondrunde

Die Mondrunde findet alle 4 Runden statt:

- Runde 4
- Runde 8
- Runde 12
- Runde 16

Ablauf:

- Spieler würfelt 1W6 pro eigenem Feld.
- Nachbar würfelt 1W6 pro eigenem Feld.
- Kein Initiative-Bonus.
- Höhere Summe gewinnt.
- Bei Gleichstand passiert nichts.

Wenn jemand gewinnt:

- Gewinner nimmt 1 Ressource vom Verlierer.
- Bei Vorsprung >= 5 übernimmt der Gewinner zusätzlich das neueste Nicht-Dorf-Feld des Verlierers.

## Überfluss

Überfluss bleibt weich.

Am Ende der Runde gilt:

Wenn eine Ressource > 5 ist, verliert der Besitzer 1 davon.

Das ist keine harte Obergrenze.

## Sieg und Niederlage

Spieler gewinnt durch Imperium-Sieg:

- Spieler erreicht 8 Felder.

Spieler gewinnt durch Ausdauer-Sieg:

- Holz = 0
- Stein = 0
- Korn = 0

Spieler verliert durch Nachbar-Sieg:

- Nachbar erreicht 8 Felder.

## Nicht in v0.2 enthalten

Nicht enthalten sind:

- Nachbar-Profile
- Sabotage
- Stagnationssystem
- Rache-Bonus
- Catch-up-Regeln
- Heilige Felder
- Fokus-Token
- Hex-Alterung
- Named Combos
- Wonder
- VP-System
- Backend
- KI
- GUI

## Playtest-Fragen

Nach Umsetzung sollen folgende Fragen geprüft werden:

- Wird Aussetzen weniger dominant?
- Fühlt sich der Nachbar gefährlich, aber nicht unfair an?
- Kommt Raid sinnvoll zum Einsatz?
- Ist die Mondrunde spürbar?
- Endet das Spiel grob zwischen Runde 10 und 18?
- Erreicht der Nachbar zu schnell 8 Felder?
- Ist die 2x-W3-Bauwahl zu stark oder genau richtig?
