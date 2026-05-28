# Maillon — Scope-Übergang v0.2 → v0.3

> Stand: 28-05-2026  
> Typ: Designdokument / Übergangsentscheidung

---

## 1. Status v0.2

v0.2 ist **technisch lauffähig** und bleibt als Conflict Prototype erhalten.

Was bewiesen wurde:

- Python-Terminal-Loop funktioniert
- Save/Load mit Versionierung funktioniert
- Gegner (Nachbar) baut, setzt aus, erhält Ertrag
- Raid: Würfelkonflikt, Ressourcenraub, Feldübernahme
- Mondrunde: echter Konflikt, nicht nur Marker
- Siegcheck an mehreren Punkten im Loop

Was v0.2 nicht ist: das finale Regelmodell.

---

## 2. Warum v0.2 nicht das Zielmodell ist

Der Playtest hat drei strukturelle Probleme offengelegt:

### 2.1 Zu eng

8 Felder sind für zwei Akteure zu wenig. Das Brett ist sofort voll, Bauoptionen
verschwinden schnell, taktische Entscheidungen haben keinen Raum.

### 2.2 Start zu weit entwickelt

Beide Akteure starten mit Dorf + Holz + Stein + Korn = 4 Felder und drei
verschiedenen Ressourcentypen. Das simuliert das Endstadium eines Aufbauspiels,
nicht einen organischen Wachstumsprozess.

### 2.3 Snowball-Mechanik ist mathematisch deterministisch

In v0.2 bedeutet ein Feld gleichzeitig:

- Besitz
- Produktion
- Kampfwürfel
- Siegfortschritt
- mögliches Übernahmeobjekt

Das erzeugt einen harten Compound-Vorteil. Die folgende Tabelle zeigt, wie
schnell Felddifferenzen die Kampfwahrscheinlichkeit kippen:

| Felder A | Felder B | E[Diff] | P(A gewinnt) | P(A stiehlt Feld, Vor. ≥5) |
|----------|----------|---------|--------------|-----------------------------|
| 5        | 3        | +7,0    | 92,6 %       | 66,1 %                      |
| 6        | 3        | +10,5   | 98,0 %       | 85,8 %                      |
| 6        | 4        | +7,0    | 90,3 %       | 64,4 %                      |
| 7        | 4        | +10,5   | 96,8 %       | 83,4 %                      |
| 6        | 2        | +14,0   | 99,8 %       | 97,0 %                      |

Ein 5:3-Feldvorteil → 92 % Siegwahrscheinlichkeit im Kampf.  
Ein 6:2-Stand ist de facto entschieden.  
Das ist kein Bug von v0.2 — es ist ein Hinweis, dass das Modell die Räumlichkeit
braucht, die es aktuell nicht hat.

---

## 3. Der entscheidende Gedanke

> Ein Feld darf nicht mehr automatisch alles gleichzeitig bedeuten.

In v0.3 wird **Raum** von **Funktion** getrennt:

- Ein Boardfeld ist zuerst ein **Platz im Raum** (Koordinate, Nachbarschaft)
- Funktion (Ressourcentyp, Upgrade, Spezialstatus) ist eine **zweite Schicht**
- Kampfkraft kommt aus der **Frontlinie**, nicht aus der Gesamtzahl

---

## 4. Hex-Board Grundlagen

### 4.1 Reguläre Hexboards

Die Formel für reguläre Hexboards mit Radius s:

```
Felder(s) = 3 · s · (s − 1) + 1
```

| Radius | Felder | Status               |
|--------|--------|----------------------|
| 2      | 7      | zu klein             |
| 3      | 19     | zu klein             |
| 4      | 37     | **Testboard v0.3**   |
| 5      | 61     | **Zieltest v0.3**    |
| 6      | 91     | spätere Erweiterung  |

45 Felder ist kein reguläres Hexboard und wird nicht als Standard übernommen.

### 4.2 Board-Eigenschaften

**37er Board (Radius 4):**

| Eigenschaft               | Wert                 |
|---------------------------|----------------------|
| Gesamtfelder              | 37                   |
| Randfelder (äußerste Reihe) | 24                 |
| Innenfelder               | 13                   |
| Ø Nachbarn (Innen)        | 6,0                  |
| Ø Nachbarn (Rand)         | 3,8                  |
| Startdistanz (gegenüber)  | 8 Schritte           |
| Rush-Erstkontakt (min)    | Runde 4              |
| Felder ≤3 Schritte Start  | 16 von 37 (43 %)     |

**61er Board (Radius 5):**

| Eigenschaft               | Wert                 |
|---------------------------|----------------------|
| Gesamtfelder              | 61                   |
| Randfelder                | 30                   |
| Innenfelder               | 31                   |
| Ø Nachbarn (Innen)        | 6,0                  |
| Ø Nachbarn (Rand)         | 3,8                  |
| Startdistanz (gegenüber)  | 10 Schritte          |
| Rush-Erstkontakt (min)    | Runde 5              |
| Felder ≤3 Schritte Start  | 16 von 61 (26 %)     |

### 4.3 Interpretation

Das 37er Board ist groß genug, damit kein sofortiges 8-Feld-Rennen entsteht,
aber klein genug für schnelle Iterationen. Das 61er Board gibt echten
strategischen Raum: mehr Flanken, mehr Ausweichbewegung, mehr Zeit in der
Aufbauphase.

---

## 5. Startlogik v0.3

v0.2-Start: Dorf + Holz + Stein + Korn → zu weit entwickelt.

v0.3-Start: **Dorf/Core + 1 Holzfeld**

Warum:

- Bauen kostet 2 Holz + 1 Korn → ohne Holz sofort Softlock
- Korn produziert das Dorf (Core) → Versorgung gesichert
- Stein und weitere Typen entstehen durch Bauoptionen oder Testvariablen
- Dieser Start simuliert den echten Anfang, nicht das Mittelspiel

**Baugeschwindigkeit ab Start (ohne Ressourcenlimit):**

| Runde | Holz | Korn | Aktion        |
|-------|------|------|---------------|
| 1     | 1    | 1    | kein Bau      |
| 2     | 2    | 2    | Bau möglich ✓ |

Ab Runde 2 kann gebaut werden — das ist der Mindestaufbau, bevor Konflikt sinnvoll ist.

---

## 6. Ressourcenlimit-Mathematik

Die v0.2-Überflusskegel (>5 → -1) funktioniert **nur bei ≤3-4 Feldern**.

Ab 6+ Feldern ist sie wirkungslos:

| Felder | Produktion/R | Netto nach Überfluss |
|--------|-------------|----------------------|
| 2      | 2           | 1                    |
| 4      | 4           | 3 → Stacking         |
| 6      | 6           | 5 → Stacking         |
| 10     | 10          | 9 → Stacking         |
| 15     | 15          | 14 → Stacking        |

Für v0.3 ist eines der folgenden Systeme notwendig:

### Option A — Hartes Cap

```
max(Ressource) = 8  oder  max = 10
```

- Einfach zu implementieren und kommunizierbar
- Skaliert nicht mit Spielgröße

### Option B — Diminishing Returns

```
Ertrag_effektiv = n · (1 / (1 + n/k))   [k = 6 empfohlen]
```

| Felder | Eff. Produktion |
|--------|----------------|
| 4      | 2,4            |
| 8      | 3,4            |
| 12     | 4,0            |
| 20     | 4,6            |

Produktion wächst, aber gegen eine asymptotische Grenze (~5). Kein Stacking
möglich, ohne zu verbrauchen.

### Option C — Upkeep (Korn-Unterhalt)

```
Upkeep = floor(Felder / 3) Korn pro Runde
```

| Felder | Korn-Upkeep |
|--------|------------|
| 3      | 1          |
| 6      | 2          |
| 9      | 3          |
| 15     | 5          |
| 18     | 6          |

Korn wird Limitressource — mehr Felder = mehr Unterhaltsbedarf.  
**Empfehlung:** Option C testen, weil es das Dorf/Core thematisch stärkt
und einen natürlichen Wachstumsdeccel erzeugt.

---

## 7. Kampfwürfel-Formel

### Problem v0.2

Formel: 1W6 pro eigenes Feld. Das erzeugt bei einem Feldvorteil von +2
bereits eine Siegwahrscheinlichkeit von ~75–92 %. Wer einmal vorne liegt,
gewinnt Kämpfe leichter, gewinnt Felder leichter, liegt noch weiter vorne.

### Alternative 1: Nur Frontfelder würfeln

Frontfelder = Felder, die an ein neutrales oder gegnerisches Feld grenzen.

- Innere Felder geben Produktion, nicht Kampfpower
- Frontgröße ist gedeckelt (räumlich begrenzt)
- Snowball wird strukturell gebrochen

### Alternative 2: √n Würfel

```
Würfel = sqrt(Felder)   →   E[Summe] = 3.5 · sqrt(n)
```

| Felder | Würfel | E[Summe] |
|--------|--------|----------|
| 4      | 2,00   | 7,0      |
| 9      | 3,00   | 10,5     |
| 16     | 4,00   | 14,0     |
| 25     | 5,00   | 17,5     |
| 37     | 6,08   | 21,3     |

Ein 37-Feld-Imperium würfelt ~6W6 — gleich viel wie ein v0.2-Spieler mit 6
Feldern. Das skaliert logarithmisch statt linear.

**Empfehlung für v0.3:** Frontfelder-Formel testen — sie ist räumlich
konsistent mit dem Hex-Board-Modell und verhindert den Compound-Effekt
strukturell statt durch Zahlencaps.

---

## 8. Siegbedingungen auf Hex-Board

### Imperium-Sieg (Feldanteil)

| Schwelle | 37er Board | 61er Board |
|----------|-----------|------------|
| 50 %     | 19 Felder | 31 Felder  |
| 60 %     | 23 Felder | 37 Felder  |
| 70 %     | 26 Felder | 43 Felder  |
| 80 %     | 30 Felder | 49 Felder  |

**Empfehlung Testboard:** 60 % → 23 Felder. Gibt Spielraum ohne dass das
Spiel zu lang wird.

### Distanz-Sieg

Gegner-Dorf erreichen (Pfad der Distanz 8 / 10 kontrollieren).
Ermöglicht Rush-Strategien ohne Imperium-Schwelle.

### Ausdauer-Sieg

Bleibt wie v0.2: alle Ressourcentypen des Gegners auf 0 — nur sinnvoll
wenn Upkeep-Regel aktiv ist.

---

## 9. Offene Balanceparameter (bewusst offen)

Diese Punkte werden erst nach dem Board-Analyse-Skript und ersten Testrunden
entschieden:

- Kampfwürfel-Formel (alle Felder / Frontfelder / √n)
- Feldübernahme: sofort oder gestuft?
- Upgrade: nur Produktion oder auch Schutz/Verteidigung?
- Feldtyp beim Bauen: freie Wahl oder 2×W3 wähle 1?
- Siegschwelle: 50 % / 60 % / Distanz?
- Ressourcenlimit: Hard Cap / Diminishing Returns / Upkeep?

---

## 10. Nächster technischer Schritt

Ein Analyse-Skript erstellen, das:

1. Hex-Boards mit 37 und 61 Feldern generiert
2. Nachbarschaften für alle Koordinaten berechnet
3. Startpositionen setzt (gegenüberliegende Ecken)
4. Baubare Felder pro Runde simuliert (räumlich: Ausdehnung von Start)
5. Rush-Distanzen und Erstkontaktpunkte berechnet
6. Breitenoptionen (verfügbare Bauoptionen pro Runde) zählt
7. Erste Kontaktpunkte zwischen den Fronten bestimmt

Erst danach: Ressourcen, Kampf, Feldübernahme, Upgrades und Siegbedingungen
neu kalibrieren.

---

## 11. Zusammenfassung des Schnitts

| Aspekt             | v0.2                          | v0.3                            |
|--------------------|-------------------------------|---------------------------------|
| Board              | 8-Feld-Liste                  | Hex-Grid (37 Test / 61 Ziel)    |
| Start              | Dorf + Holz + Stein + Korn    | Dorf/Core + Holzfeld            |
| Baulogik           | Feld an Liste anhängen        | räumlich: grenzt an eigenes Feld|
| Kampfwürfel        | alle eigenen Felder           | Frontfelder (zu testen)         |
| Ressourcenlimit    | Überfluss >5 → -1 (unwirksam) | Upkeep oder Hard Cap (zu testen)|
| Snowball           | deterministisch (mathematisch)| strukturell gedämpft            |
| Status             | Conflict Prototype ✓          | Board Baseline (nächster Schritt)|

v0.2 beweist die Konfliktmechanik.  
v0.3 baut den Raum, in dem diese Mechanik sinnvoll wird.
