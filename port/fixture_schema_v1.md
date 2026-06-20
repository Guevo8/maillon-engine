# Maillon Godot Fixture Schema v1

## Zweck

Die Fixtures bilden den festgelegten Python-Referenzstand für den Godot-Port ab.

Sie werden deterministisch durch `tools/export_godot_fixtures.py` erzeugt.

Standard-Ausgabeziel:

    port/fixtures/

## Grundstruktur

Ein Fixture besitzt folgende Felder:

    {
      "schema_version": 1,
      "fixture_id": "string",
      "base_state": {
        "kind": "initial",
        "side_length": 5
      },
      "overrides": {},
      "query": {},
      "expected": {}
    }

## base_state

`base_state` definiert den Ausgangszustand.

Schema v1 unterstützt:

    {
      "kind": "initial",
      "side_length": 5
    }

Der Zustand wird mit `create_initial_state(side_length)` erzeugt.

## overrides

`overrides` enthält ausschließlich Abweichungen vom Initialzustand.

Mögliche Felder:

    {
      "round_index": 1,
      "cells": [],
      "actors": {},
      "tunnel_edges": []
    }

### Zellzustand

    {
      "coord": [0, 0],
      "owner": "player",
      "field_type": "Holz",
      "level": 1,
      "active_from_round": 1,
      "contested_count": 0,
      "raid_shield": 0,
      "has_tunnel_entrance": false,
      "collapsed": false
    }

### Akteurszustand

    {
      "player": {
        "resources": {
          "Holz": 2,
          "Stein": 0,
          "Korn": 3
        },
        "caps": {
          "Holz": 6,
          "Stein": 6,
          "Korn": 6
        }
      }
    }

## Query-Typen

Schema v1 kennt vier Query-Typen.

### surface_legal_actions

Query:

    {
      "type": "surface_legal_actions",
      "actor": "player"
    }

Erwartetes Ergebnis:

    {
      "actions": []
    }

Die Aktionsliste enthält ausschließlich die legalen Oberflächenaktionen und ist innerhalb dieses Scopes vollständig und kanonisch sortiert.

Tunnelaktionen gehören nicht zum Fixture-Scope v1 und werden in einer späteren Port-Stufe ergänzt.

### apply_action

Query:

    {
      "type": "apply_action",
      "apply_production_before": false,
      "action": {
        "actor": "player",
        "action_type": "build",
        "target": [-2, 0],
        "field_type": "Korn"
      }
    }

Erwartete Felder:

    {
      "ok": true,
      "winner": null,
      "round_index": 1,
      "actors": {},
      "cell_changes": [],
      "tunnel_edges": [],
      "collapsed": []
    }

Bei `apply_production_before: true` enthält das Ergebnis zusätzlich:

    {
      "production_waste": {}
    }

### bot_decision

Query:

    {
      "type": "bot_decision",
      "actor": "enemy",
      "policy": "phase_player"
    }

Erwartetes Ergebnis:

    {
      "action": {}
    }

### phase_order

Query:

    {
      "type": "phase_order",
      "round_index": 2
    }

Erwartetes Ergebnis:

    {
      "first": "enemy",
      "second": "player"
    }

## Koordinaten

Axiale Hex-Koordinaten werden als zweielementige Arrays gespeichert:

    [q, r]

Beispiel:

    [-2, 1]

## Kanonische Aktionssortierung

Aktionen werden sortiert nach:

1. Aktionstyp
2. `source.q`
3. `source.r`
4. `target.q`
5. `target.r`
6. Feldtyp

Reihenfolge der Oberflächenaktionen:

1. `build`
2. `raid`
3. `fortify`
4. `rebuild`
5. `field_upgrade`
6. `core_upgrade`
7. `wait`

Reihenfolge der Feldtypen:

1. `Holz`
2. `Stein`
3. `Korn`

## Determinismus

Der Export verwendet:

- UTF-8
- eingerücktes JSON
- alphabetisch sortierte JSON-Schlüssel
- kanonisch sortierte Koordinaten
- kanonisch sortierte Aktionen
- keine Timestamps
- keine Zufallswerte
- keine systemabhängigen Pfade innerhalb der Fixtures

Wiederholte Exporte desselben Referenzstands müssen byteidentische Fixture-Dateien erzeugen.
