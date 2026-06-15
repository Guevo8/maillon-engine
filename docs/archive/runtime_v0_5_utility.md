# Maillon v0.5 Utility Runtime

## Status

Branch/Tag-Stand:

- Branch: `v0.5-utility-bot`
- Freeze-Tag: `v0.5-utility-tuned2d`

Dieser Stand enthält den bisher stabilsten v0.5-Prototypen mit:

- Terminal-Spielkern
- Run-Logging
- Runtime-Matrix
- Utility Decision Probe
- Fortify/Raid-Shield
- Fortify-Breaker
- Rusher-Finish-Fix
- Utility-Balancer tuned2d

## Kernsystem

Maillon ist ein rundenbasiertes Strategie-Prototypsystem auf einem axialen Hex-/Grid-Board.

Aktive Ressourcen:

- `Holz`
- `Stein`
- `Korn`

Aktive Aktionen:

- `build`
- `raid`
- `fortify`
- `rebuild`
- `field_upgrade`
- `core_upgrade`
- `wait`

Aktive Siegbedingungen:

- `territory`
- `domination`
- `full_board_majority`

## Fortify / Raid-Shield

`Fortify` nutzt Korn als defensiven Sink.

Felder können Raid-Schutz erhalten. Raids reduzieren zunächst Schutz, bevor ein Feld übernommen wird.

Aktuelle Kostenlogik:

- Schutzstufe 1: 2 Korn
- Schutzstufe 2: 4 Korn
- Schutzstufe 3: 6 Korn

## Fortify-Breaker

Angrenzende Angreiferfelder erhöhen den Schaden gegen Raid-Shields.

Aktuelle Kurve:

- 1 angrenzendes Angreiferfeld: 1 Shield Damage
- 2 angrenzende Angreiferfelder: 1 Shield Damage
- 3 angrenzende Angreiferfelder: 2 Shield Damage
- 4+ angrenzende Angreiferfelder: 3 Shield Damage

Designziel:

- Fortify bleibt relevant.
- Fortify darf keine Endlos-Stalls erzeugen.
- Räumliche Umklammerung soll strategisch zählen.

## Rusher-Finish-Fix

Der Rusher hatte vorher Endgame-Stalls erzeugt, weil er Holz durch Rebuild-Oszillation verbrannt hat.

Fix:

- Wenn neutrale Felder offen sind,
- Build grundsätzlich sinnvoll ist,
- aber Holz aktuell nicht reicht,
- und Holzproduktion vorhanden ist,

spielt der Rusher kein destruktives Rebuild, sondern spart für Build.

## Utility-Balancer tuned2d

`tuned2d` ergänzt das Utility-Scoring um strategischen Kontext:

- Strategic pressure layer
- Wait/Rebuild-Unterdrückung bei Rückstand
- Save-for-build-Logik
- bessere Expansion-/Raid-Priorität
- Rebuild-Cap in Drucklagen
- klarerer Finish-Druck

Wichtiger gelöster Problemfall vor tuned2d:

```text
37 rusher_vs_utility_balancer
none R121
16/16/5
chosen_action:rebuild: 145
behind_action:rebuild: 129
```

Nach tuned2d:

```text
37 rusher_vs_utility_balancer
player territory R27
23/9/5
chosen_action:rebuild: 2
```

## Analysewerkzeuge

Aktive Analysewerkzeuge:

```text
analysis/runtime_matrix.py
analysis/utility_decision_probe.py
```

Wichtige Reports:

```text
analysis/reports/runtime_matrix_v0_5_baseline.csv
analysis/reports/runtime_matrix_v0_5_utility_tuned2d.csv
analysis/reports/utility_decision_probe_v0_5_tuned2d_summary.txt
```

## Bewertung

v0.5 ist kein finales Balancing, aber ein belastbarer Systemstand.

Stärken:

- spielbarer Terminal-Prototyp
- reproduzierbare Runs
- Bot-vs-Bot-Matrix
- Entscheidungsanalyse für Utility-Bots
- klare Freeze-Tags
- nachvollziehbarer Regel-/Bot-Testzyklus

Offene Punkte:

- Utility-Balancer ist besser, aber nicht final.
- Personality-Bots sind vorbereitet, aber noch nicht aktiv integriert.
- Fortify bleibt stark und muss bei neuen Mechaniken erneut geprüft werden.
- 61er Board erzeugt deutlich andere Dynamik als 37er Board.

## Nächster v0.5-Schritt

Personality-Bots aktivieren:

- `utility_rusher`
- `utility_economist`
- `utility_fortifier`
- `utility_aggro_turtle`
- `utility_opportunist`

Danach:

- Runtime-Matrix mit Personality-Bots
- Personality-Balance prüfen
- erst danach v0.6-Mechaniken starten
