# Maillon v0.6 Tunnel Config Freeze Notes

Stand: 05-06-2026  
Branch: `v0.6-tunnel-prototype`  
Block: `7O.4`  
Scope: Freeze notes after tunnel default configuration centralization.

---

## 1. Kurzfazit

Die Tunnelparameter wurden zentral vorbereitet, ohne das Spielverhalten zu ändern.

Neu eingeführt wurde:

```text
src/maillon_v04/tunnel_config.py
```

Dieses Modul bündelt die Default-Werte für Tunnelkosten und Collapse-Schwelle.

---

## 2. Zentralisierte Defaults

Aktuelle Default-Werte:

```text
DEFAULT_COLLAPSE_THRESHOLD = 4

DEFAULT_TUNNEL_ENTRANCE_HOLZ = 1
DEFAULT_TUNNEL_ENTRANCE_STEIN = 2

DEFAULT_TUNNEL_EXTEND_HOLZ = 1
DEFAULT_TUNNEL_EXTEND_STEIN = 1

DEFAULT_TUNNEL_RAID_KORN = 3

DEFAULT_REPAIR_BUILD_HOLZ = 2
DEFAULT_REPAIR_BUILD_STEIN = 2
```

Spielwerte wurden nicht verändert.

---

## 3. Betroffene Dateien

Geändert wurden:

```text
src/maillon_v04/tunnel_config.py
src/maillon_v04/tunnels.py
src/maillon_v04/tunnel_rules.py
analysis/main_action_regression_smoke.py
analysis/tunnel_action_smoke_suite.py
```

Zweck:

```text
- tunnel_config.py als zentrale Default-Quelle
- tunnels.py liest Collapse/Raid-Konstanten aus tunnel_config.py
- tunnel_rules.py baut Kosten-Dicts aus tunnel_config.py
- Smoke-Tests wurden an die v0.6-Tunnelregeln angepasst
```

---

## 4. Regressionsergebnis

Bestätigt:

```text
- Tunnelkosten unverändert
- Collapse Threshold unverändert
- Runtime-Matrix-Kompatibilität weiterhin OK
- Main Action Regression Smoke an v0.6-Regeln angepasst
- Tunnel Action Smoke Suite an v0.6-Regeln angepasst
```

Die Runtime-Matrix bestätigt weiterhin:

```text
Tunnelaktionen sind in das Action-Modell integriert,
aber alte Bot-Pools nutzen sie nicht unbeabsichtigt.
```

---

## 5. Warum dieser Schritt wichtig ist

Der spätere `utility_tunneler` hängt stark an:

```text
- Tunnel Entrance Cost
- Tunnel Extend Cost
- Tunnel Raid Cost
- Repair Build Cost
- Collapse Threshold
```

Durch die Zentralisierung sind spätere Balance-Änderungen besser kontrollierbar und erzeugen weniger noisy diffs.

---

## 6. Aktueller Freeze-Status

Der Stand nach 7O ist:

```text
Tunnelmechanik spielbar.
Terminal-UI funktionsfähig.
Collapse und Repair Build bewiesen.
Tunnelparameter zentral vorbereitet.
Regression aktualisiert.
```

Damit ist der Weg frei für:

```text
7P utility_tunneler Design-Plan
```

---

## 7. Nicht gelöst in 7O

Noch offen:

```text
- Utility-Tunneler-Entscheidungslogik
- Bot-Bewertung von Tunnelrisiko
- Bot-Bewertung gemeinsamer Tunnelnetzwerke
- Kostenbalancing
- Szenario-/JSON-Parameter
- bessere Terminal-Navigation für Tunnel-Extend
```

Diese Punkte gehören in spätere Blöcke.
