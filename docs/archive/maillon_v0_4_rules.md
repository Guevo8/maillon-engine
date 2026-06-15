# Maillon v0.4 — Analysierter Prototypkern

Stand: 02-06-2026  
Status: analysierter Regelkern / Grundlage für den nächsten Terminal-Prototyp.

## Einordnung

Maillon v0.4 konkretisiert die v0.3-Board-Hypothese durch deterministische Simulationen.

```text
v0.1/v0.2 = historische Runtime
v0.3      = Board-Baseline-Hypothese
v0.4      = analysierter Prototypkern
```

v0.1/v0.2 bleiben als lauffähige historische Terminal-Runtime erhalten. v0.3 bleibt die Board-Baseline. v0.4 beschreibt den aktuell bevorzugten Regelkern für die nächste spielbare Terminal-Version.

## Board

Maillon verwendet ein reguläres Hex-Board.

Aktuelle Testgrößen:

| Board | Bedeutung |
|---|---|
| 37 Felder | Schnelltest / kleines Testboard |
| 61 Felder | Haupttest / strategischer Zielraum |

Das Board beschreibt Raum, Nachbarschaft, Fronten, Baurichtung und Raid-Reichweite. Der Boardplatz legt den Ressourcentyp nicht automatisch fest.

## Akteure

Aktueller Kern:

```text
player
enemy
```

Der ältere Begriff `Nachbar` bleibt historisch relevant, sollte im neuen Boardmodell aber nicht mit Hex-Nachbarschaft verwechselt werden.

## Ressourcen

Es gibt drei Hauptressourcen:

| Ressource | Funktion |
|---|---|
| Holz | Expansion und Umbau |
| Korn | Raid / Angriff |
| Stein | Feld-Upgrades und Core-Ausbau |

Startressourcen im Analysemodell:

| Ressource | Startwert |
|---|---:|
| Holz | 2 |
| Stein | 0 |
| Korn | 3 |

## Ressourcen-Caps

Basis-Cap:

| Ressource | Cap |
|---|---:|
| Holz | 6 |
| Stein | 6 |
| Korn | 6 |

Core Level 2 erhöht alle Caps um +6:

| Ressource | Neues Cap |
|---|---:|
| Holz | 12 |
| Stein | 12 |
| Korn | 12 |

Core Level 3 ist vorgemerkt, aber noch nicht Teil der v0.4-Baseline.

## Produktion

Aktuelles deterministisches Analysemodell:

| Feld | Level 1 | Level 2 |
|---|---:|---:|
| Holzfeld | +1 Holz / Runde | +2 Holz / Runde |
| Kornfeld | +1 Korn / Runde | +2 Korn / Runde |
| Steinfeld | +1 Stein / Runde | +2 Stein / Runde |
| Core | +1 Korn / Runde | Cap-Erhöhung durch Core Upgrade |

Felder produzieren nur, wenn sie aktiv sind.

## Aktive und instabile Felder

Jedes Feld kann durch `active_from_round` zeitlich blockiert sein.

Ein nicht aktives Feld:

- produziert nicht,
- kann nicht als Build-Origin dienen,
- kann nicht als Raid-Origin dienen,
- ist nicht erneut raidbar, bis es wieder aktiv ist.

## Aktionen

### Build

Build erzeugt ein neues eigenes Feld auf einem angrenzenden neutralen Feld.

Bedingungen:

- Ziel liegt innerhalb des Boards.
- Ziel ist neutral.
- Ziel grenzt an mindestens ein eigenes aktives Feld.

Build kostet Holz. Die Kosten steigen nach Entwicklungsstufe.

Tier-Berechnung:

```text
tier = eigene kontrollierte Nicht-Core-Felder // 5
```

Build-Kosten:

| Tier | Holz-Kosten |
|---:|---:|
| 0 | 2 |
| 1 | 3 |
| 2 | 5 |
| 3 | 8 |
| 4+ | 12 |

Das neue Feld wird ab der nächsten Runde aktiv.

### Raid

Raid übernimmt ein gegnerisches Nicht-Core-Feld direkt.

Bedingungen:

- Ziel gehört dem Gegner.
- Ziel ist kein Core.
- Ziel ist aktiv.
- Ziel grenzt an mindestens ein eigenes aktives Feld.

Raid kostet Korn nach Support:

| Eigene aktive Nachbarfelder am Ziel | Korn-Kosten |
|---:|---:|
| 1 | 3 |
| 2 | 2 |
| 3+ | 1 |

Bei erfolgreichem Raid:

- owner wechselt sofort,
- field_type bleibt erhalten,
- Upgrade-Status bleibt erhalten,
- das Feld wird instabil.

### Feld-Instabilität nach Raid

Jedes geraidete Feld speichert, wie oft es bereits umkämpft wurde.

```text
contested_count += 1
cooldown = min(3, contested_count)
active_from_round = current_round + cooldown
```

Diese Regel reduziert sofortiges Raid-Pingpong, ohne den direkten Besitzerwechsel aufzugeben.

### Rebuild / Umbau

Umbau ändert den Feldtyp eines eigenen aktiven Nicht-Core-Feldes.

Bedingungen:

- Ziel gehört dem Akteur.
- Ziel ist aktiv.
- Ziel ist Holz, Korn oder Stein.
- Ziel ist kein Core.

Kosten:

```text
2 Holz
```

Effekt:

- Feldtyp ändert sich zu Holz, Korn oder Stein.
- Upgrade-Level bleibt erhalten.
- Feld wird ab der nächsten Runde wieder aktiv.

### Field Upgrade

Field Upgrade verbessert ein eigenes aktives Nicht-Core-Feld von Level 1 auf Level 2.

Bedingungen:

- Ziel gehört dem Akteur.
- Ziel ist aktiv.
- Ziel ist kein Core.
- Ziel ist noch nicht upgraded.

Kosten steigen nach Entwicklungsstufe:

| Tier | Stein-Kosten |
|---:|---:|
| 0 | 3 |
| 1 | 4 |
| 2 | 6 |
| 3 | 8 |
| 4+ | 12 |

Effekt:

- Produktion steigt von +1 auf +2 pro Runde.

### Core Upgrade

Core Upgrade verbessert den Core von Level 1 auf Level 2.

Kosten:

```text
4 Stein
```

Effekt:

- Holz-Cap +6
- Stein-Cap +6
- Korn-Cap +6

Aktuell ist nur Level 2 aktiv. Level 3 bleibt spätere Option.

## Action Economy

Getestete Varianten:

| Aktionen pro Zug | Bewertung |
|---:|---|
| 2 | konservativer Baseline-Test |
| 3 | ernsthafter Kandidat für den Terminal-Prototyp |

Befund: 3 Aktionen sind erst nach Einführung der Feld-Instabilität plausibel, weil eroberte Felder nicht sofort als Durchbruchskette weitergenutzt werden können.

## Siegbedingung

Aktuelle Analyse-Siegbedingung:

```text
60 Prozent kontrollierte Felder
```

Für die Testboards bedeutet das:

| Board | 60%-Schwelle |
|---|---:|
| 37 Felder | 23 Felder |
| 61 Felder | 37 Felder |

Die 60%-Schwelle ist ein stabiler Messpunkt für Simulationen. Weitere Siegbedingungen bleiben offen.

## Bot-Policies im Analysemodell

Aktuelle Policies:

- `rusher`
- `expander`
- `upgrader`
- `balanced`
- `tempo_expander`
- `cap_aware_balanced`
- `phase_player`

Wichtig: `cap_aware_balanced` ist aktuell eher ein Stressbot als ein normaler Gegner. Er eignet sich, um Cap-Druck, Front-Stalls und Raid-Pingpong sichtbar zu machen.

## Status v0.4

v0.4 ist kein fertiges Spiel und keine finale Balance. v0.4 ist der aktuell analysierte Prototypkern, der als Grundlage für die nächste Terminal-Runtime dienen soll.
