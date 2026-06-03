# Maillon v0.6 Tunnel Session Freeze Summary

Stand: 03-06-2026  
Branch: `v0.6-tunnel-prototype`  
Vorheriger Smoke-Tag: `v0.6-tunnel-probe-smoke`  
Freeze-Art: technischer Zwischen-Freeze, kein finales Balancing.

---

## 1. Kurzfazit

In dieser Session wurde das Tunnelsystem von einer Designidee zu einem technisch lauffähigen v0.6-Prototyp ausgebaut.

Der Stand ist jetzt:

```text
Tunnel-State existiert.
Tunnel-Actions existieren.
Collapse/Repair existieren.
Main-Action-Pipeline kennt Tunnelaktionen.
Runtime-Matrix misst Tunnelmetriken.
Ein erster tunnel-aware Bot `tunnel_probe` erzeugt echte Tunnelaktionen.
Smoke- und Regressionstests laufen.
```

Wichtig: `tunnel_probe` ist bewusst nur ein Stress-/Mechanik-Bot. Er ist nicht als balancierter Spielbot eingefroren.

---

## 2. Erreichte Hauptziele dieser Session

### 2.1 Tunnel-State eingeführt

Der GameState wurde um ein unterirdisches Netzwerkmodell erweitert.

Relevante Konzepte:

```text
has_tunnel_entrance
collapsed
tunnel_edges
```

Interpretation:

```text
Oberflächenfelder bleiben normale Spielfelder.
Tunnel sind ein separates physisches Graph-Netz.
Tunnelkanten sind nicht owned.
Zugriff auf Tunnel erfolgt über eigene aktive Tunneleingänge.
```

---

### 2.2 Tunnel Pressure und Collapse definiert

Druckregel:

```text
Tunnel pressure = Anzahl inzidenter Tunnelkanten an einem Feld.
Collapse threshold = 4.
```

Collapse-Entscheidung:

```text
Collapse wird simultan geprüft.
Alle Felder mit pressure >= 4 kollabieren gemeinsam.
Erst danach werden inzidente Tunnelkanten entfernt.
```

Collapsed State:

```text
collapsed = True
owner = None
field_type = None
level = 0
raid_shield = 0
has_tunnel_entrance = False
```

Designentscheidung:

```text
Collapsed ist kein normales neutrales Feld.
Collapsed kann nur über repair_build wieder spielbar werden.
```

---

### 2.3 Tunnelaktionen implementiert

Aktueller isolierter Tunnel-Action-Satz:

```text
tunnel_entrance
tunnel_extend
tunnel_raid
repair_build
```

Kurzlogik:

```text
tunnel_entrance: sichtbaren Zugang auf eigenem aktivem Feld bauen.
tunnel_extend: Tunnelkante von erreichbarem Tunnelknoten aus erweitern.
tunnel_raid: gegnerisches Nicht-Core-Feld über Tunnel übernehmen, Shield umgehen.
repair_build: collapsed Feld reparieren, übernehmen und neu bebauen.
```

---

### 2.4 Main-Action-Pipeline integriert

Die bestehenden normalen Aktionen bleiben erhalten:

```text
build
raid
rebuild
field_upgrade
core_upgrade
fortify
wait
```

Zusätzlich kennt das Main-Action-Modell jetzt:

```text
tunnel_entrance
tunnel_extend
tunnel_raid
repair_build
```

Wichtig: Die Tunnelaktionen werden intern an das isolierte Tunnelmodul delegiert. Das hält die neue Logik modular und reduziert Risiko für alte v0.5-Aktionen.

---

### 2.5 Runtime-Matrix erweitert

`analysis/runtime_matrix.py` wurde um Tunnelmetriken erweitert.

Neue relevante Matrixspalten:

```text
tunnel_entrance
tunnel_extend
tunnel_raid
repair_build
tunnel_raid_takeovers
shield_bypassed
collapsed_fields_total
collapsed_fields_final
tunnel_edges_final
tunnel_nodes_final
network_components_final
largest_tunnel_component
fields_with_tunnel_entrance
max_tunnel_pressure_final
avg_tunnel_pressure_final_x100
p_tunnel_entrance / e_tunnel_entrance
p_tunnel_extend / e_tunnel_extend
p_tunnel_raid / e_tunnel_raid
p_repair_build / e_repair_build
```

Bestätigter Kompatibilitätsstand:

```text
Alte Bots erzeugen weiterhin Tunnelwerte 0.
Das ist korrekt, solange sie nicht tunnel-aware sind.
```

---

### 2.6 tunnel_probe Bot erstellt

Neue Bot-Policy:

```text
tunnel_probe
```

Zweck:

```text
technischer Nachweis, dass Bots Tunnelaktionen erzeugen können.
Stress-Test für Runtime-Metriken.
Kein finaler Balance-Bot.
```

Bestätigt:

```text
tunnel_probe erzeugt tunnel_entrance.
tunnel_probe erzeugt tunnel_extend.
tunnel_probe erzeugt tunnel_raid.
tunnel_probe kann repair_build / Collapse-Kontexte auslösen.
Runtime-Matrix zählt diese Aktionen korrekt.
```

Beobachtete Schwäche:

```text
tunnel_probe vernachlässigt Oberfläche.
Surface-Control bricht zu früh weg.
Gegen normale Bots droht frühe Domination.
```

Designlesart:

```text
Tunnel muss eine strategische Zusatzebene sein,
nicht Ersatz für Surface-Control.
```

---

## 3. Wichtigste aktuelle Dateien

### 3.1 Core-Spielstruktur

```text
src/maillon_v04/board.py
src/maillon_v04/state.py
src/maillon_v04/rules.py
src/maillon_v04/actions.py
src/maillon_v04/engine.py
```

Bedeutung:

```text
board.py    -> Hex-Board / Koordinaten / Nachbarschaften
state.py    -> GameState, CellState, Ressourcen, Tunnel-State
rules.py    -> Kosten, Caps, Produktion, Raid-/Build-Regeln
actions.py  -> zentrale Main-Action-Pipeline inkl. Tunnel-Dispatch
engine.py   -> Rundenablauf, Bot-vs-Bot, Produktions-/Action-Fluss
```

---

### 3.2 Tunnelmodule

```text
src/maillon_v04/tunnels.py
src/maillon_v04/tunnel_collapse.py
src/maillon_v04/tunnel_rules.py
src/maillon_v04/tunnel_actions.py
```

Bedeutung:

```text
tunnels.py          -> Tunnelgraph, Kanten, Pressure, Erreichbarkeit, Komponenten
tunnel_collapse.py -> simultaner Collapse, collapsed field state, Edge-Removal
tunnel_rules.py    -> Tunnelkosten und parametrisierbare Konstanten
tunnel_actions.py  -> isolierte Tunnelaktionen und Target-Validierung
```

---

### 3.3 Botdateien

```text
src/maillon_v04/bot.py
src/maillon_v04/bot_utility.py
src/maillon_v04/bot_personality.py
src/maillon_v04/bot_tunnel_probe.py
```

Bedeutung:

```text
bot.py               -> BotPolicy-Dispatch, klassische Bots, utility dispatch
bot_utility.py       -> Utility-Scoring-Botlogik
bot_personality.py   -> Personality-Parameter / Utility-Personas
bot_tunnel_probe.py  -> erster tunnel-aware Stress-/Probe-Bot
```

Aktuelle wichtige Bot-Policy:

```text
tunnel_probe
```

---

## 4. Wichtigste Analyse- und Testskripte

### 4.1 Tunnel-Smoke und Regression

```text
analysis/tunnel_action_smoke_suite.py
analysis/tunnel_extend_collapse_probe.py
analysis/main_action_regression_smoke.py
analysis/runtime_matrix_compat_smoke.py
```

Bedeutung:

```text
tunnel_action_smoke_suite.py      -> prüft tunnel_entrance, tunnel_extend, collapse, tunnel_raid, repair_build
tunnel_extend_collapse_probe.py   -> gezielter Collapse-Test über tunnel_extend
main_action_regression_smoke.py   -> prüft alte Aktionen nach Tunnelintegration
runtime_matrix_compat_smoke.py    -> prüft alte Runtime-Matrix + Tunnelspalten 0 bei alten Bots
```

---

### 4.2 Runtime und Reports

```text
analysis/runtime_matrix.py
analysis/personality_report.py
analysis/stall_diagnostic.py
analysis/utility_decision_probe.py
```

Bedeutung:

```text
runtime_matrix.py        -> zentrale Bot-vs-Bot-Matrix, jetzt inkl. Tunnelmetriken
personality_report.py    -> aggregiert Bot-/Policy-Performance
stall_diagnostic.py      -> untersucht Max-Round-Stalls und Churn-Fälle
utility_decision_probe.py -> analysiert Utility-Bot-Entscheidungen
```

---

## 5. Wichtigste Dokumentationsdateien

### 5.1 Aktuelle v0.6 Tunnel-Dokumentation

```text
analysis/reports/tunnel_action_smoke_suite_v0_6.md
analysis/reports/v0_6_tunnel_probe_freeze_notes.md
analysis/reports/v0_6_tunnel_session_freeze_summary.md
```

Bedeutung:

```text
tunnel_action_smoke_suite_v0_6.md
-> dokumentiert Coverage der Tunnel-Smoke-Suite.

v0_6_tunnel_probe_freeze_notes.md
-> dokumentiert den ersten technischen Freeze des tunnel_probe-Standes.

v0_6_tunnel_session_freeze_summary.md
-> diese Übersicht; ordnet Session-Ergebnisse, relevante Dateien und nächsten Arbeitsstand.
```

---

### 5.2 Wichtige v0.5 Vorarbeit

```text
analysis/reports/v0_5_balance_freeze_notes.md
analysis/reports/personality_report_v0_5_summary.csv
analysis/reports/personality_report_v0_5.md
```

Bedeutung:

```text
v0_5_balance_freeze_notes.md
-> letzter sinnvoller Balance-Freeze vor v0.6-Tunnelarbeit.

personality_report_v0_5_summary.csv / .md
-> Grundlage der Personality-Bot-Bewertung.
```

Hinweis: Viele ältere `runtime_matrix_v0_5_*` und `stall_diagnostics_*` Dateien sind historische Analyseartefakte. Sie sind nützlich, aber nicht alle gehören dauerhaft in den aktiven Arbeitsfokus.

---

## 6. Aktueller Git-Stand

Aktueller relevanter Verlauf:

```text
583c746 Add v0.6 tunnel probe freeze notes
20a2309 Add tunnel probe bot policy
0923cae Assert tunnel metrics in runtime compat smoke
07ab5d8 Add tunnel metrics to runtime matrix
```

Aktueller relevanter Tag:

```text
v0.6-tunnel-probe-smoke
```

Interpretation:

```text
Der Tag markiert den ersten funktionierenden tunnel_probe-Smoke.
Die Freeze-Notizen liegen danach als Dokumentationscommit auf dem Branch.
```

Wenn ein neuer finaler Freeze nach dieser Summary gewünscht ist, kann ein weiterer Tag gesetzt werden, z.B.:

```text
v0.6-tunnel-session-freeze
```

---

## 7. Was ist eingefroren?

Eingefroren als technisch funktionsfähig:

```text
Tunnel-State
Tunnelgraph
Tunnel Pressure
Simultan-Collapse
Tunnelactions
Repair-Build
Main-Action-Integration
Runtime-Matrix-Tunnelmetriken
tunnel_probe-Smoke
```

Nicht eingefroren als final/balanced:

```text
Tunnelkosten
Collapse threshold
repair_build cost
tunnel_probe Verhalten
utility_tunneler Verhalten
Bot-Balancing allgemein
UI/Terminal-Darstellung
Fog of War / Hidden Tunnel System
Szenario-JSON-Parametrisierung
```

---

## 8. Empfohlene nächste Schritte

### 8.1 Nicht direkt tun

Nicht sofort `tunnel_probe` balancen. Der Bot erfüllt seine Aufgabe als Stress-/Mechanik-Probe.

### 8.2 Nächster sinnvoller Designschritt

```text
7L.2 utility_tunneler Design-Plan
```

Ziel:

```text
Einen echten balancierbaren Tunnel-Bot konzipieren,
der Surface-Control zuerst stabilisiert und Tunnel dann als strategisches Werkzeug nutzt.
```

Mögliche Leitplanken:

```text
- erst ab Mindestanzahl eigener Non-Core-Felder tunneln
- erst mindestens 1-2 Holz/Stein-Felder sichern
- tunnel_entrance nicht vor Surface-Basis
- tunnel_extend nicht endlos spammen
- tunnel_raid als Conversion-Tool gegen geschützte Ziele
- repair_build nur als Recovery / Value-Repair
- Collapse nicht zufällig selbst auslösen, außer bewusst als Opfer-/Pressure-Spielzug
```

### 8.3 Später

```text
Terminal-UI erweitern
Run-Logging für Tunnelereignisse verfeinern
Szenario-JSON für Tunnelkosten und Collapse threshold
Fog-of-war / hidden tunnel design separat prüfen
```

---

## 9. Praktischer Arbeitsanker

Für die nächste Session relevant zuerst öffnen:

```text
analysis/reports/v0_6_tunnel_session_freeze_summary.md
analysis/reports/v0_6_tunnel_probe_freeze_notes.md
src/maillon_v04/bot_tunnel_probe.py
src/maillon_v04/tunnel_actions.py
analysis/runtime_matrix.py
```

Danach nur bei Bedarf tiefer in:

```text
src/maillon_v04/tunnels.py
src/maillon_v04/tunnel_collapse.py
src/maillon_v04/actions.py
src/maillon_v04/bot.py
```
