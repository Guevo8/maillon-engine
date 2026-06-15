# Maillon v0.7 — Utility-Tunneler Validation Build

## Status

Maillon v0.7 integriert den `utility_tunneler`-Bot in den Main-Branch.

Der Stand erweitert den bisherigen Tunnel-Prototyp um eine erklärbare Bot-Entscheidungsebene:

- Tunnelaktionen werden über Feature-Scoring bewertet.
- Der Bot kann zwischen normalen Utility-Aktionen und Tunnelaktionen abwägen.
- Opportunity-Cost gegen den besten normalen Utility-Zug ist Teil der Entscheidungslogik.
- Analyse-/Probe-Werkzeuge erzeugen CSV-Daten zur späteren Validierung.

## Lokale Validierung

Folgende Smoke-/Regression-Blöcke wurden nach dem Merge erfolgreich ausgeführt:

- `analysis.utility_tunneler_smoke`
- `analysis.main_action_regression_smoke`
- `analysis.tunnel_action_smoke_suite`
- `analysis.runtime_matrix_compat_smoke`
- `analysis.utility_tunneler_decision_probe`

Die Decision-Probe erzeugte:

- `analysis/reports/utility_tunneler_decision_probe_v0_7.csv`
- 13.401 Zeilen

## Wichtiges Ergebnis

Der Merge ist technisch stabil genug für einen v0.7-Zwischenstand.

Noch nicht final validiert ist die strategische Qualität des Bots. Die nächste Auswertung muss zeigen, ob der Utility-Tunneler Tunnelaktionen in plausiblen Situationen wählt oder ob die Scoring-/Opportunity-Cost-Logik zu konservativ, zu aggressiv oder unklar ist.

## Bekannte Hinweise

- `runtime_matrix_compat_smoke` trägt im Terminal-Header noch die Bezeichnung `v0.6`. Das ist wahrscheinlich ein kosmetischer Versionslabel-Rest und sollte später bereinigt werden.
- Raw-CSV-Reports sollten nur committed werden, wenn sie deterministisch erzeugt werden oder bewusst als Analyseartefakte versioniert werden sollen.
- Für Portfolio-Zwecke ist eine kompakte Markdown-Auswertung wertvoller als eine große Rohdaten-CSV.

## Nächster Meilenstein

Eine kurze CSV/MD-Auswertung erstellen:

- Wie oft werden Tunnelaktionen gewählt?
- Welche Tunnelaktion wird am häufigsten gewählt?
- In welchen Matchups und Boardgrößen passiert das?
- Ignoriert der Bot Tunneloptionen trotz guter Lage?
- Gibt es Score-Anomalien oder auffällige Opportunity-Cost-Blockaden?

Danach Entscheidung:

A) Bot-Scoring verfeinern, falls die Entscheidungen unplausibel sind.  
B) Godot-Port vorbereiten, falls die Entscheidungen brauchbar sind.
