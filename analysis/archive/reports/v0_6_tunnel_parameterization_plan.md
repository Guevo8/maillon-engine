# Maillon v0.6 Tunnel Parameterization Plan

Stand: 05-06-2026  
Branch: `v0.6-tunnel-prototype`  
Block: `7O.1`  
Scope: Vorbereitung der Tunnel-Parametrisierung nach Terminal-Playtest-Freeze.

---

## 1. Kurzfazit

Der Terminal-Playtest hat bewiesen, dass die Tunnelmechanik funktioniert. Der nächste sinnvolle Schritt ist nicht direkt `utility_tunneler`, sondern eine kleine technische Vorbereitung der Tunnelparameter.

Grund:

```text
Der spätere utility_tunneler hängt stark an Kosten, Pressure und Collapse-Schwelle.
Wenn diese Werte vorher sauber zentralisiert sind, wird Bot-Tuning kontrollierter.
```

Ziel von 7O.1 ist nur Vorbereitung und Dokumentation. Es werden noch keine Spielwerte verändert.

---

## 2. Aktuell hardcoded

Aktuelle Tunnelwerte:

```text
Tunnel Entrance Cost: 1 Holz + 2 Stein
Tunnel Extend Cost:   1 Holz + 1 Stein
Tunnel Raid Cost:     3 Korn
Repair Build Cost:    2 Holz + 2 Stein
Collapse Threshold:   4
```

Aktuelle Verteilung:

```text
src/maillon_v04/tunnel_rules.py
- TUNNEL_ENTRANCE_COSTS
- TUNNEL_EXTEND_COSTS
- REPAIR_BUILD_COSTS
- tunnel_entrance_cost()
- tunnel_extend_cost()
- tunnel_raid_cost()
- repair_build_cost()

src/maillon_v04/tunnels.py
- TUNNEL_RAID_KORN_COST
- COLLAPSE_THRESHOLD
```

Bewertung:

```text
Die Werte sind funktional, aber noch nicht sauber als einheitliches Tunnel-Regelset gekapselt.
```

---

## 3. Designentscheidung

Tunnelparameter sollen zentral vorbereitet werden, ohne das Spielverhalten zu ändern.

Für den nächsten Codeblock soll gelten:

```text
Keine Balanceänderung.
Keine neue Szenario-Logik.
Keine JSON-Pflicht.
Kein Zufall.
Kein Timestamp.
Keine noisy diffs.
```

---

## 4. Empfohlene technische Richtung

Empfohlen wird ein neues kleines Modul:

```text
src/maillon_v04/tunnel_config.py
```

Dieses Modul soll die Default-Werte bündeln:

```text
DEFAULT_TUNNEL_ENTRANCE_COSTS
DEFAULT_TUNNEL_EXTEND_COSTS
DEFAULT_TUNNEL_RAID_COSTS
DEFAULT_REPAIR_BUILD_COSTS
DEFAULT_COLLAPSE_THRESHOLD
```

Danach sollen bestehende Module diese Defaults nutzen.

Ziel:

```text
tunnels.py und tunnel_rules.py lesen aus derselben Quelle.
```

Noch nicht Ziel:

```text
Szenario-JSON vollständig einführen.
GameConfig vollständig umbauen.
Runtime-Matrix CLI mit Tunnelparametern erweitern.
```

---

## 5. Warum nicht sofort GameConfig?

`GameConfig` ist aktuell klein und steuert vor allem:

```text
side_length
actions_per_turn
bot_policy
max_rounds
```

Eine direkte Erweiterung um alle Tunnelparameter wäre möglich, aber für den nächsten Schritt größer als nötig.

Besser:

```text
1. Defaults zentralisieren.
2. Verhalten per Smoke-Test unverändert bestätigen.
3. Danach entscheiden, ob GameConfig oder Szenario-JSON folgen soll.
```

---

## 6. Vorgeschlagene Schrittfolge

### 7O.2 Default-Konfiguration zentralisieren

```text
- neues Modul tunnel_config.py
- bestehende Konstanten dorthin verschieben/kopieren
- tunnels.py und tunnel_rules.py darauf umstellen
- keine Werte ändern
```

### 7O.3 Regression prüfen

```text
- py_compile
- tunnel_action_smoke_suite.py
- main_action_regression_smoke.py
- runtime_matrix_compat_smoke.py
- kleiner Terminal-Check optional
```

### 7O.4 Freeze-Notiz

```text
- dokumentieren, dass Werte zentralisiert wurden
- bestätigen, dass Verhalten unverändert blieb
```

### 7P Danach

Erst danach:

```text
utility_tunneler Design-Plan
```

---

## 7. Erfolgsdefinition für 7O

7O ist erfolgreich, wenn:

```text
- Tunnelwerte zentral auffindbar sind.
- Alle bisherigen Smoke-Tests weiter laufen.
- Der Playtest-Stand nicht verändert wird.
- Späteres Bot-Tuning weniger noisy diffs erzeugt.
```

---

## 8. Nicht anfassen in 7O.1

Nicht ändern:

```text
Tunnelkosten
Collapse Threshold
Botlogik
Terminal-UI
Runtime-Matrix-Interpretation
```

7O.1 ist nur ein Vorbereitungs- und Planungscommit.
