# Maillon v0.6 Terminal Tunnel Playtest Report

Stand: 04-06-2026  
Branch: `v0.6-tunnel-prototype`  
Playtest block: `7N.1`  
Scope: Manual terminal playtest after tunnel UI integration and tunnel rule tightening.

---

## 1. Kurzfazit

Der manuelle Terminal-Playtest bestätigt, dass das v0.6-Tunnelsystem im echten Spielablauf funktioniert.

Bestätigt wurden:

```text
- dynamisches Terminalmenü
- Status/Karte kombiniert
- Tunnelmarker auf der Karte
- Tunneleingang als `tu`
- Untergrabung als `u`
- Tunnel Pressure sichtbar
- Tunnel Extend auf besetzte Felder
- keine neutralen Extend-Ziele mehr
- Tunnel Raid
- Collapse
- Repair Build
- gemeinsamer Netzwerkzugang
```

Der Stand ist damit spielbar genug, um das Tunnelsystem als technischen Prototypen zu dokumentieren.

---

## 2. Wichtigster Playtest-Befund

Die Kernmechanik funktioniert:

```text
Wer Zugang zum Tunnelnetz hat, kann das bestehende Tunnelnetz nutzen.
```

Das wurde im Playtest praktisch sichtbar und entspricht der gewünschten Designlogik.

Diese Regel ist keine Nebensache, sondern eine zentrale Tunnelentscheidung:

```text
Tunnelkanten sind nicht owned.
Zugang entsteht über eigene aktive Tunneleingänge.
Ein verbundenes Tunnelnetz kann strategisch von beiden Seiten genutzt werden,
wenn Zugang besteht.
```

Das ist für spätere Botlogik sehr wichtig, weil ein Bot nicht nur eigene Tunnel bauen darf, sondern auch bewerten muss:

```text
- Kann ich ein bestehendes Netz anzapfen?
- Nutzt der Gegner mein Netz gegen mich?
- Ist ein neuer Eingang ein Zugriffspunkt oder ein Risiko?
- Wann lohnt sich ein Tunnel-Raid über ein bestehendes Netz?
- Wann ist ein Tunnelnetz gefährlicher als nützlich?
```

---

## 3. Bestätigte UI-Funktionen

### 3.1 Dynamisches Hauptmenü

Das Hauptmenü zeigt nur verfügbare Gruppen:

```text
Build / Expand
Attack / Raid
Develop / Upgrade
Tunnel
Status / Karte
Zug beenden
Partie abbrechen
```

Wenn keine Tunnelaktion möglich ist, erscheint keine Tunnelgruppe. Wenn Tunnelaktionen möglich sind, erscheint die Gruppe mit Anzahl.

Beispiel:

```text
Möglich: Build 0 | Attack 0 | Develop 5 | Tunnel 6
Tunnel: Entrance 3 | Extend 3 | Raid 0 | Repair 0
```

Das reduziert Menürauschen deutlich und verhindert, dass die Spieleroberfläche durch zu viele Einzelaktionen überladen wird.

### 3.2 Status und Karte

`Status / Karte` funktioniert als kombinierte Ansicht.

Angezeigt werden:

```text
- Runde
- Boardgröße
- Sieger
- kontrollierte Felder
- Ressourcen
- Tunnelübersicht
- Karte
- Legende
```

### 3.3 Tunnelmarker

Die Karte zeigt Tunnelzustände direkt im Board-Token:

```text
u    = untergraben
tu   = Tunneleingang + untergraben
XX   = collapsed
```

Beispiele aus dem Playtest:

```text
PHtu
PKu
ESu
EStu
```

Die Regel `T => U` ist damit visuell umgesetzt: Ein Tunneleingang wird nicht isoliert als `t`, sondern als `tu` dargestellt.

---

## 4. Bestätigte Regeländerungen aus 7M.7

### 4.1 Tunneleingang zählt als Untergrabung

Nach dem Bau eines Tunneleingangs steigt `under` und `max_pressure`.

Beispiel:

```text
Tunnel: edges=0 | under=2 | entrances=2 | collapsed=0 | max_pressure=1
```

Das bestätigt:

```text
Tunneleingang erzeugt Pressure.
Tunneleingang ist automatisch untergraben.
```

### 4.2 Neutrale Extend-Ziele sind geblockt

Nach 7M.7 wurden im Tunnel-Extend-Menü keine neutralen Felder mehr als gültige Ziele angeboten.

Das ist wichtig, weil Tunnel sonst eine zweite Expansionsmechanik durch leeres Land geworden wären.

Aktuelle Regel:

```text
tunnel_extend darf nur auf besetzte, nicht-collapsed, nicht-Core-Felder gehen.
```

### 4.3 Core-Felder werden nicht als Tunnel-Eingang genutzt

Core-Sonderfälle bleiben dadurch vorerst ausgeschlossen.

Das reduziert Risiko bei:

```text
- Core-Stabilität
- Core-Zugriff
- Win-Condition-Sonderfällen
- Tunnel-Raid-Sonderfällen
```

---

## 5. Collapse und Repair Build bestätigt

Im Playtest wurde Collapse real ausgelöst.

Beispiel:

```text
player extends tunnel (0, -1)->(0, 0) ... collapsed=((0, 0),).
enemy repair-builds Holz at (0, 0) ...
```

Später wurde erneut Collapse ausgelöst:

```text
player extends tunnel (0, -1)->(0, 0) ... collapsed=((0, -1),).
enemy repair-builds Korn at (0, -1) ...
```

Damit sind bestätigt:

```text
- Pressure kann im echten Terminalspiel die Collapse-Schwelle erreichen.
- Collapse wird direkt nach Tunnelaktion ausgelöst.
- Collapse entfernt das Feld aus normaler Nutzung.
- Repair Build kann das Feld wieder spielbar machen.
- Der Spielablauf läuft danach weiter.
```

---

## 6. Gameplay-Lesart

Der Playtest zeigt: Tunnel funktionieren als strategische Zusatzebene.

Besonders sichtbar wurden:

```text
- Tunnel können geschützte Felder über Shield-Bypass bedrohen.
- Tunneleingänge sind gleichzeitig Chance und Risiko.
- Ein verbundenes Tunnelnetz kann vom Gegner mitgenutzt werden.
- Collapse kann gezielt oder indirekt entstehen.
- Repair Build erzeugt einen eigenen Recovery-/Rebuild-Pfad.
```

Die wichtigste Designlesart bleibt:

```text
Tunnel sind kein Ersatz für Surface-Control.
Tunnel sind eine zweite Konflikt- und Druckebene auf bestehenden Oberflächenfeldern.
```

---

## 7. Beobachtete Schwächen / offene UI-Punkte

Die Funktionalität ist bestätigt, aber die Navigation im Terminal ist noch schwer lesbar.

Besonders bei `tunnel_extend` können Listen schnell lang und kognitiv schwer werden.

Offene UI-Verbesserungen für später:

```text
- Tunnel-Extend-Ziele besser sortieren
- Collapse-Gefahr markieren
- Pressure 3 als Gefahr anzeigen
- gegnerische Ziele hervorheben
- eigene riskante Felder hervorheben
- eventuell Top-Ziele priorisieren
- eventuell Debug-Ansicht separat halten
```

Diese Punkte sind Interface-Fragen, keine Blocker für die Regelmechanik.

---

## 8. Aktuelle Bewertung

### Erfolgreich

```text
Tunnel-State funktioniert.
Tunnel-UI ist sichtbar.
Tunnelaktionen sind manuell ausführbar.
Neutrale Tunnelziele sind geblockt.
Tunneleingang zählt als Untergrabung.
Collapse funktioniert.
Repair Build funktioniert.
Gemeinsames Tunnelnetz funktioniert.
```

### Noch nicht final

```text
Terminal-Navigation im Tunnelnetz
Bot-Bewertung der Tunnelrisiken
Utility-Tunneler-Logik
Kostenbalancing
Szenario-/Config-Parametrisierung
Fog-of-war / hidden tunnel rules
```

---

## 9. Entscheidung nach Playtest

Der Playtest ist ausreichend für den aktuellen Block.

Es ist nicht nötig, jetzt weiter manuell Collapse zu erzwingen. Collapse wurde bereits bewiesen.

Nächster sinnvoller Schritt:

```text
7N.2 Playtest-Freeze / Dokumentationscommit prüfen
```

Danach sinnvoller Folgeblock:

```text
7O.1 Tunnel-Parameter vorbereiten
oder
7O.1 Utility-Tunneler Design-Plan
```

Empfohlene Reihenfolge:

```text
1. Playtest-Report committen
2. kleinen Freeze-Tag setzen
3. dann entscheiden:
   a) Tunnelparameter auslagern
   b) utility_tunneler designen
```

Tendenz:

```text
Erst minimale Parametrisierung der Tunnelkosten und Collapse-Schwelle,
danach utility_tunneler.
```

Begründung:

```text
Der utility_tunneler hängt stark an Kosten, Pressure und Collapse-Schwelle.
Wenn diese Werte vorher parametrisierbar sind, wird späteres Bot-Tuning sauberer
und erzeugt weniger noisy diffs.
```
