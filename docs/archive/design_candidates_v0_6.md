# Maillon v0.6 Design Candidates

## Status

Dieses Dokument ist ein theoretischer Freeze für spätere Erweiterungen.

Es beschreibt Ideen, die nicht direkt in v0.5 eingebaut werden sollen.

Priorität:

1. v0.5 dokumentieren
2. Personality-Bots aktivieren
3. Personality-Matrix testen
4. Danach v0.6 entscheiden

## Candidate A: Underground / Tunnel Layer

### Kurzidee

Ein zweiter strategischer Layer unterhalb der bestehenden Felder.

Die Oberwelt bleibt das sichtbare Hauptspiel. Der Untergrund erlaubt Umgehung, Sabotage, Unterhöhlung und neue Frontlogik.

### Designziel

Das Spiel soll nicht nur aus direkter Oberflächen-Expansion bestehen.

Tunnel sollen:

- Fortify indirekt kontern
- Frontlinien aufbrechen
- neue Angriffswege schaffen
- defensive Monostrategien schwächen
- langfristige Planung belohnen

### Mögliche Grundstruktur

Jedes Feld kann zusätzlich einen Untergrundstatus haben.

Beispiel:

```text
surface_owner
surface_type
surface_level
raid_shield

underground_owner
tunnel_level
undermined
damaged
repair_required
```

### Minimalversion v0.6a

Nur eine kleine erste Version:

- Feld kann `tunnel=True` besitzen.
- Tunnelbau kostet Ressourcen.
- Tunnel erlaubt bestimmte Raid-/Bypass-Aktionen.
- Keine Feldzerstörung.
- Keine neue Win Condition.
- Keine verdeckte Information.

Ziel:

Erst prüfen, ob Tunnel als zweite Bewegungsebene Spaß macht.

### Erweiterung v0.6b: Unterhöhlung

Unterhöhlung ist eine Sabotageaktion gegen Oberflächenfelder.

Mögliche Effekte:

- Produktion gestoppt
- Feld temporär deaktiviert
- Fortify teilweise ignoriert
- Reparatur erforderlich

### Erweiterung v0.6c: Reparatur

Neue Aktion:

```text
repair
```

Zweck:

- Unterhöhlung entfernen
- Feldproduktion wiederherstellen
- zerstörte/gesperrte Felder stabilisieren

### Erweiterung v0.6d: Feldzerstörung / schrumpfende Karte

Sehr spätes Modul.

Mögliche Regel:

- stark unterhöhlte Felder können zerstört werden
- zerstörte Felder zählen nicht mehr als normale Felder
- Boardgröße / Win Threshold muss dynamisch neu berechnet werden

Risiko:

Sehr hohe Komplexität. Nur nach stabiler v0.6a/v0.6b testen.

### Bewertung Underground

Strategischer Wert: sehr hoch  
Komplexität: sehr hoch  
Balancing-Risiko: hoch  
Empfehlung: als v0.6-Hauptmodul vormerken, aber klein starten.

## Candidate B: Weather / Event Layer

### Kurzidee

Rundenbasierte Wetter- oder Ereigniszustände verändern Kosten, Produktion oder Aktionsqualität.

Beispiele:

- Regen: Raid wird teurer
- Frost: Build wird teurer
- Hitze: Kornproduktion sinkt
- Hagel: Fortify/Rebuild wird erschwert
- Klarer Himmel: keine Änderung

### Designziel

Wetter soll Varianz erzeugen und Planung erschweren.

### Risiko

Zufällige Wettereffekte können Balancing-Daten verrauschen.

Dann ist schwer zu erkennen:

- War der Bot schlecht?
- War das Wetter unfair?
- War die Regel schlecht?
- War der Seed ungünstig?

### Mindestanforderung

Wenn Wetter eingebaut wird, braucht es:

- deterministischen Seed
- Wetterlog im Run-Log
- Wetterspalte im Runtime-Report
- Option zum Deaktivieren
- Matrixläufe mit und ohne Wetter

### Empfohlene Minimalversion

Nicht direkt Aktionen verbieten. Nicht direkt Kosten verdoppeln.

Besser:

```text
Regen: Raidkosten +1
Frost: Buildkosten +1
Hitze: Kornproduktion -1
Hagel: Fortifykosten +1
Klar: keine Änderung
```

### Bewertung Weather

Strategischer Wert: mittel bis hoch  
Komplexität: mittel  
Balancing-Risiko: mittel bis hoch  
Empfehlung: optionales Szenario-/Eventsystem, nicht v0.6-Hauptmodul.

## Vergleich: Underground vs. Weather

Underground:

- echte zweite Strategieebene
- hoher Tiefgang
- hohe Komplexität
- besser als Hauptmodul geeignet

Weather:

- mehr Varianz
- einfacher einzubauen
- kann Balancing verfälschen
- besser als optionaler Modus geeignet

## Vorläufige Entscheidung

Für v0.6 priorisieren:

```text
1. Underground / Tunnel Layer theoretisch weiter ausarbeiten
2. Minimalversion v0.6a planen
3. Wetter nur als späteren optionalen Event-Layer vormerken
```

## Freeze-Notiz

Dieses Dokument ist ein Design-Freeze, kein Implementierungsauftrag.

Vor Umsetzung müssen zuerst erfüllt sein:

- Personality-Bots aktiv
- Personality-Matrix vorhanden
- Utility-Bot stabil genug
- v0.5-Systemstand dokumentiert
