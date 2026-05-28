# Maillon — Scope-Übergang v0.2 → v0.3

> Stand: 28-05-2026  
> Typ: Mathematischer Analyseentwurf / Hypothesensammlung  
> Kanonische Designentscheidungen: siehe `docs/rules_v0_3_board_baseline.md`  
> Lesbare Entwicklungsnotiz: siehe `docs/transition_note_v0_2_to_v0_3.md`

---

## Dokumenthierarchie

Dieses Repo enthält mehrere v0.3-Dokumente mit unterschiedlichem Status:

| Dokument | Typ | Verbindlichkeit |
|---|---|---|
| `rules_v0_3_board_baseline.md` | Kanonische Designentscheidungen | verbindlich |
| `transition_note_v0_2_to_v0_3.md` | Lesbare Entwicklungsnotiz | informell |
| `transition_v0_2_to_v0_3_scope.md` (dieses Dokument) | Mathematischer Analyseentwurf | Hypothesen, noch zu verifizieren |

Dieses Dokument ist kein Freeze. Es formuliert Hypothesen und Rechenwege,
die durch das Analyse-Skript (nächster technischer Schritt) überprüft werden müssen.

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

### 2.3 Compound-Vorteil durch Feld-Multifunktion

In v0.2 bedeutet ein Feld gleichzeitig:

- Besitz
- Produktion
- Kampfwürfel
- Siegfortschritt
- mögliches Übernahmeobjekt

Das erzeugt einen Compound-Vorteil. Die folgende Tabelle zeigt, wie schnell
Felddifferenzen die Kampfwahrscheinlichkeit kippen:

> **Hinweis:** Die Tabelle basiert auf einer Normalverteilungs-Approximation
> (Summe mehrerer W6 → approximativ normalverteilt). Die W6-Summe ist diskret,
> nicht exakt normalverteilt. Die Werte sind Näherungen, **noch durch exakte
> Simulation per Skript zu verifizieren.**

| Felder A | Felder B | E[Diff] | P(A gewinnt) ≈ | P(A stiehlt Feld, Vor. ≥5) ≈ |
|----------|----------|---------|----------------|-------------------------------|
| 5        | 3        | +7,0    | ~93 %          | ~66 %                         |
| 6        | 3        | +10,5   | ~98 %          | ~86 %                         |
| 6        | 4        | +7,0    | ~90 %          | ~64 %                         |
| 7        | 4        | +10,5   | ~97 %          | ~83 %                         |
| 6        | 2        | +14,0   | ~99,8 %        | ~97 %                         |

Ein 5:3-Feldvorteil führt näherungsweise zu ~93 % Siegwahrscheinlichkeit im Kampf.
Das ist kein Bug von v0.2 — es ist ein Hinweis, dass das Modell Räumlichkeit
braucht, die es aktuell nicht hat.

---

## 3. Der entscheidende Gedanke

> Ein Feld darf nicht mehr automatisch alles gleichzeitig bedeuten.

In v0.3 wird **Raum** von **Funktion** getrennt:

- Ein Boardfeld ist zuerst ein **Platz im Raum** (Koordinate, Nachbarschaft)
- Funktion (Ressourcentyp, Upgrade, Spezialstatus) ist eine **zweite Schicht**
- Wie Kampfkraft aus dem Board abgeleitet wird, ist **bewusst offen** (siehe Abschnitt 7)

---

## 4. Hex-Board Grundlagen

### 4.1 Begriffliche Klarstellung: Seitenlänge, nicht Radius

> **Korrektur gegenüber erstem Entwurf:** In diesem Dokument wird die Variable s
> als **Seitenlänge** des regulären Hexagons verwendet, nicht als axialer Radius
> im Cube-Koordinatensystem. Die Formel lautet:

```
Felder(s) = 3 · s · (s − 1) + 1
```

Im Axial-/Cube-Koordinatensystem gilt stattdessen:

```
Felder(r) = 3 · r² + 3 · r + 1   (r = axialer Radius)
```

Beide Formeln sind konsistent, aber die Variable bedeutet Unterschiedliches:

| Seitenlänge s | Axialer Radius r | Felder |
|---------------|------------------|--------|
| 2             | 1                | 7      |
| 3             | 2                | 19     |
| 4             | 3                | 37     |
| 5             | 4                | 61     |
| 6             | 5                | 91     |

**In diesem Dokument werden Boards ab sofort als „Seitenlänge X" bezeichnet.**
„37er Board = Seitenlänge 4", „61er Board = Seitenlänge 5".
Skripte, die axialen Radius verwenden, müssen r = s − 1 rechnen.

45 Felder ist kein reguläres Hexboard und wird nicht als Standard übernommen.

### 4.2 Board-Eigenschaften (vorläufig — per Analyse-Skript zu verifizieren)

> **Hinweis:** Die Werte für Startdistanz und Rush-Erstkontakt sind Schätzwerte.
> Sie hängen davon ab, wo genau die Startpositionen gesetzt werden (Ecken,
> Kanten, gegenüberliegend). **Verbindliche Werte liefert erst das Analyse-Skript.**
>
> Vorläufige Erwartung bei gegenüberliegenden Eckpositionen:
> maximale Board-Distanz ≈ 2 · (s − 1)
>
> - Seitenlänge 4: max. Distanz ≈ **6**
> - Seitenlänge 5: max. Distanz ≈ **8**

**37er Board (Seitenlänge 4):**

| Eigenschaft               | Wert (vorläufig)                 |
|---------------------------|----------------------------------|
| Gesamtfelder              | 37                               |
| Randfelder (äußerste Reihe) | 18                             |
| Innenfelder               | 19                               |
| Ø Nachbarn (Innen)        | 6,0                              |
| Ø Nachbarn (Rand)         | ~3,8                             |
| Startdistanz (gegenüber)  | **ca. 6 — per Skript zu prüfen** |
| Rush-Erstkontakt (min)    | **ca. Runde 3 — per Skript zu prüfen** |
| Felder ≤3 Schritte Start  | per Skript zu berechnen          |

**61er Board (Seitenlänge 5):**

| Eigenschaft               | Wert (vorläufig)                 |
|---------------------------|----------------------------------|
| Gesamtfelder              | 61                               |
| Randfelder                | 20                               |
| Innenfelder               | 41                               |
| Ø Nachbarn (Innen)        | 6,0                              |
| Ø Nachbarn (Rand)         | ~3,8                             |
| Startdistanz (gegenüber)  | **ca. 8 — per Skript zu prüfen** |
| Rush-Erstkontakt (min)    | **ca. Runde 4 — per Skript zu prüfen** |
| Felder ≤3 Schritte Start  | per Skript zu berechnen          |

### 4.3 Interpretation

Das 37er Board ist groß genug, damit kein sofortiges 8-Feld-Rennen entsteht,
aber klein genug für schnelle Iterationen. Das 61er Board gibt mehr Flanken,
mehr Ausweichbewegung und mehr Aufbauzeit. Alle strategischen Aussagen über
Kontaktpunkte, Breitenoptionen und Rush-Szenarien werden erst durch das
Analyse-Skript belegt.

---

## 5. Startlogik v0.3

v0.2-Start: Dorf + Holz + Stein + Korn → zu weit entwickelt.

v0.3-Start: **Dorf/Core + 1 Holzfeld**

Warum:

- Bauen kostet 2 Holz + 1 Korn → ohne Holz sofort Softlock
- Korn produziert das Dorf (Core) → Versorgung gesichert
- Stein und weitere Typen entstehen durch Bauoptionen oder Testvariablen
- Dieser Start simuliert den echten Anfang, nicht das Mittelspiel

**Baugeschwindigkeit ab Start (deterministisches Modell — 1 Res/Feld/Runde):**

> Dieses Modell nimmt an, dass jedes Feld jede Runde sicher 1 Ressource produziert.
> Das entspricht **nicht** der v0.2-Würfelregel (W6, Ertrag nur bei bestimmten
> Ergebnissen). Es ist ein deterministisches Referenzmodell für Worst-/Best-Case.

| Runde | Holz | Korn | Aktion        |
|-------|------|------|---------------|
| 1     | 1    | 1    | kein Bau      |
| 2     | 2    | 2    | Bau möglich ✓ |

Ab Runde 2 kann im deterministischen Modell gebaut werden.

---

## 6. Ressourcenlimit-Hypothesen

> **Wichtiger Hinweis:** Die folgende Analyse gilt für ein **deterministisches
> Produktionsmodell** (jedes Feld produziert sicher 1 Ressource/Runde).
>
> Die v0.2-Regel ist anders: Felder produzieren auf W6-Wurf, nicht sicher.
> Nach v0.2-Regelwerk produziert 1 normales Feld im Erwartungswert **1/6
> Ressource pro Runde** (nur bei einer 6: +1 extra; ansonsten je nach Leserart
> der Regeln). Die exakte Produktionsregel für v0.3 ist noch offen.
>
> Die folgenden Argumente sind deshalb als **Hypothesen für das deterministisches
> Modell** zu verstehen, nicht als bewiesene Aussagen über v0.2 oder v0.3.

**Hypothese:** Bei deterministischer Produktion (1 Res/Feld/Runde) ist die
Überfluss-Regel (>5 → -1) ab etwa 6 Feldern wirkungslos, weil der Netto-
Zuwachs pro Runde dauerhaft positiv bleibt.

| Felder | Produktion/R (det.) | Netto nach Überfluss |
|--------|---------------------|----------------------|
| 2      | 2                   | 1                    |
| 4      | 4                   | 3 → Stacking         |
| 6      | 6                   | 5 → Stacking         |
| 10     | 10                  | 9 → Stacking         |

Bei stochastischer Produktion (W6) sind die Werte deutlich niedriger und
müssen per Simulation berechnet werden.

**Mögliche Limitansätze — alle als Testkandidaten, keine Empfehlung:**

### Testkandidat A — Hartes Cap

```
max(Ressource) = 8  oder  max = 10
```

- Einfach zu implementieren
- Skaliert nicht mit Boardgröße

### Testkandidat B — Diminishing Returns

```
Ertrag_effektiv = n · (1 / (1 + n/k))   [k = 6 als Startwert]
```

| Felder | Eff. Produktion (det.) |
|--------|------------------------|
| 4      | 2,4                    |
| 8      | 3,4                    |
| 12     | 4,0                    |
| 20     | 4,6                    |

Produktion wächst, aber gegen eine asymptotische Grenze (~k/2 bei großem n).

### Testkandidat C — Upkeep (Korn-Unterhalt)

```
Upkeep = floor(Felder / 3) Korn pro Runde
```

| Felder | Korn-Upkeep |
|--------|-------------|
| 3      | 1           |
| 6      | 2           |
| 9      | 3           |
| 15     | 5           |

Korn wird Limitressource. Thematisch kohärent mit Dorf/Core als Versorgungsanker.

**Welcher Testkandidat zuerst getestet wird, entscheidet der Designprozess nach
dem Board-Analyse-Skript — nicht dieses Dokument.**

---

## 7. Kampfwürfel-Hypothesen

### Problem v0.2

Formel: 1W6 pro eigenes Feld. Das erzeugt näherungsweise bei einem Feldvorteil
von +2 bereits eine Siegwahrscheinlichkeit von ~75–92 % (approximativ, diskrete
Simulation ausstehend).

### Testkandidaten (keine Empfehlung, bewusst offen)

**Testkandidat 1: Nur Frontfelder würfeln**

Frontfelder = Felder, die an ein neutrales oder gegnerisches Feld grenzen.

- Innere Felder geben Produktion, nicht Kampfpower
- Frontgröße ist räumlich begrenzt
- Potenzielle Wirkung: Compound-Effekt strukturell abschwächen
- Ob das ausreicht, zeigt erst der Boardtest

**Testkandidat 2: √n Würfel**

```
Würfel = sqrt(Felder)   →   E[Summe] = 3,5 · sqrt(n)
```

| Felder | Würfel | E[Summe] |
|--------|--------|----------|
| 4      | 2,00   | 7,0      |
| 9      | 3,00   | 10,5     |
| 16     | 4,00   | 14,0     |
| 25     | 5,00   | 17,5     |
| 37     | 6,08   | 21,3     |

Skaliert logarithmisch statt linear. Ob das Spielgefühl befriedigend ist,
lässt sich nur im Playtest beurteilen.

**Testkandidat 3: v0.2-Formel beibehalten, Feldübernahme entschärfen**

Kampfwürfel bleiben alle eigenen Felder, aber Feldübernahme-Schwelle wird
angepasst (höherer Vorsprung nötig, gestufter Effekt). Einfachste Variante.

**Welcher Testkandidat zuerst läuft, entscheidet sich nach dem Analyse-Skript.**

---

## 8. Siegbedingungen auf Hex-Board (Hypothesen)

### Imperium-Sieg (Feldanteil)

| Schwelle | 37er Board | 61er Board |
|----------|------------|------------|
| 50 %     | 19 Felder  | 31 Felder  |
| 60 %     | 23 Felder  | 37 Felder  |
| 70 %     | 26 Felder  | 43 Felder  |
| 80 %     | 30 Felder  | 49 Felder  |

Welche Schwelle sinnvoll ist, hängt von der tatsächlichen Spiellänge ab —
**noch nicht entschieden.**

### Distanz-Sieg

Gegner-Dorf erreichen. Ermöglicht Rush-Strategien ohne Feldmehrheit.
Startdistanz und Pfadlänge: per Analyse-Skript zu berechnen.

### Ausdauer-Sieg

Alle Ressourcentypen des Gegners auf 0 — nur sinnvoll, wenn Upkeep aktiv.
**Noch nicht entschieden.**

---

## 9. Offene Balanceparameter (bewusst offen)

Diese Punkte werden erst nach dem Board-Analyse-Skript und ersten Testrunden
entschieden:

- Kampfwürfel-Formel (alle Felder / Frontfelder / √n / v0.2 mit Anpassung)
- Feldübernahme: sofort oder gestuft?
- Upgrade: nur Produktion oder auch Schutz/Verteidigung?
- Feldtyp beim Bauen: freie Wahl oder 2×W3 wähle 1?
- Siegschwelle: 50 % / 60 % / Distanz?
- Ressourcenlimit: Hard Cap / Diminishing Returns / Upkeep?
- Produktionsregel: deterministisch oder W6-basiert?

---

## 10. Nächster technischer Schritt

Ein Analyse-Skript erstellen (`analysis/hex_board_analysis.py`), das:

1. Hex-Boards mit 37 und 61 Feldern generiert (axialer Radius r = s − 1)
2. Nachbarschaften für alle Koordinaten berechnet
3. Startpositionen setzt (gegenüberliegende Ecken, exakt definiert)
4. Baubare Felder pro Runde simuliert (räumlich: Ausdehnung von Start)
5. Rush-Distanzen und Erstkontaktpunkte berechnet
6. Breitenoptionen (verfügbare Bauoptionen pro Runde) zählt
7. Erste Kontaktpunkte zwischen den Fronten bestimmt

Die Werte in diesem Dokument (Startdistanz, Rush-Runde, Feldabdeckung) werden
dann durch Skript-Ausgaben ersetzt oder bestätigt.

---

## 11. Zusammenfassung des Schnitts

| Aspekt             | v0.2                          | v0.3                                  |
|--------------------|-------------------------------|---------------------------------------|
| Board              | 8-Feld-Liste                  | Hex-Grid (SL 4 Test / SL 5 Ziel)      |
| Start              | Dorf + Holz + Stein + Korn    | Dorf/Core + Holzfeld                  |
| Baulogik           | Feld an Liste anhängen        | räumlich: grenzt an eigenes Feld      |
| Kampfwürfel        | alle eigenen Felder           | **Testkandidat: Frontfelder / √n**    |
| Ressourcenlimit    | Überfluss >5 → -1             | **Testkandidat: Cap / DR / Upkeep**   |
| Snowball           | stark (Näherung bestätigt)    | strukturell zu adressieren            |
| Status             | Conflict Prototype ✓          | Board Baseline (nächster Schritt)     |

v0.2 beweist die Konfliktmechanik.  
v0.3 baut den Raum, in dem diese Mechanik sinnvoll werden kann.  
Dieses Dokument formuliert Hypothesen — keine Entscheidungen.
