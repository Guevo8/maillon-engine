# Maillon v0.4 — Design Notes

Stand: 02-06-2026  
Status: offene Designfragen und spätere Kandidaten nach v0.4-Analyse.

## Zweck

Dieses Dokument sammelt offene Designoptionen. Es ist kein Regel-Freeze. Der aktuelle Regelkern steht in `docs/maillon_v0_4_rules.md`; die Analysebefunde stehen in `docs/analysis_findings_v0_4.md`.

## Aktueller Fokus

v0.4 ist stabil genug, um als Grundlage für den nächsten Terminal-Prototyp zu dienen.

Die nächsten Designfragen sollten nicht alle gleichzeitig umgesetzt werden. Jede größere Änderung muss einzeln testbar bleiben.

## 1. Terminal-Prototyp

Nächster Hauptschritt:

```text
v0.4-Regeln in eine spielbare Terminal-Runtime übertragen.
```

Benötigte Kernmodule:

- BoardState.
- Ressourcenstand.
- Legal Actions.
- Aktionsmenüs.
- Spielerentscheidung.
- einfacher Gegnerbot.
- Save/Load später wieder anbinden.

Das Terminal-Interface sollte keine komplette Editorlogik erzwingen. Zuerst reicht ein klarer Spielablauf.

## 2. Legal-Action-Menüs

Empfohlene Menüstruktur:

```text
1 Build
2 Raid
3 Rebuild
4 Field Upgrade
5 Core Upgrade
6 Status
7 End Turn
```

Wichtig: Das Terminal zeigt zuerst nur gültige Aktionslisten, nicht das gesamte Board.

Beispiel:

```text
Raid-Ziele:
[1] (0, -1) Kornfeld, Kosten 2 Korn
[2] (1, -2) Holzfeld, Kosten 1 Korn
```

Damit entsteht bereits eine natürliche Action-Vision, ohne echte Fog-of-War-Regel.

## 3. Sichtmodell / Fog of War

Für die aktuelle Analysephase ist Sichtmodell zweitrangig. Die Simulation kennt den vollständigen GameState.

Für den Terminal-Prototyp gilt vorerst:

```text
Spieler sieht Status und gültige Aktionen.
```

Echte Fog-of-War-Mechaniken bleiben später möglich, sollten aber nicht vor dem ersten v0.4-Terminal-Prototyp eingebaut werden.

## 4. Utility-Scoring-Bot

Die aktuellen Bot-Policies sind feste Entscheidungsmodelle. Ein Utility-Bot wäre ein nächster Analysefortschritt.

Grundidee:

```text
Alle legalen Aktionen bekommen Punkte.
Die Aktion mit dem besten Score wird gewählt.
```

Mögliche Bewertungsfaktoren:

- Nähe zur 60%-Siegschwelle.
- Ressourcencap-Druck.
- günstige Raidkosten.
- neue Build-Optionen.
- Hotspot-Vermeidung.
- Upgrade-Wert.
- Rebuild gegen Ressourcenmangel.

Status: sinnvoll, aber nicht notwendig vor dem ersten Terminal-Prototyp.

## 5. Core Level 3

Core Level 3 ist vorgemerkt.

Mögliche Regel:

```text
Core Level 2 → Level 3
Kosten: 8 Stein
Caps: 12 → 18
```

Nutzen:

- reduziert Longgame-Waste.
- ermöglicht höhere tiered costs.
- gibt Stein im Mid-/Lategame mehr Funktion.

Risiko:

- kann Cap-Druck zu stark entschärfen.
- kann Spiele verlängern.

Empfehlung: erst nach Terminal- oder Utility-Bot-Tests prüfen.

## 6. Raid +1 Holz

Mögliche Variante:

```text
Raid kostet Korn nach Support + 1 Holz
```

Interpretation:

- Korn = Angriff / Versorgung.
- Holz = Logistik / Kriegsmaterial.

Nutzen:

- gibt Holz im Krieg eine weitere Funktion.
- bremst Raid-Spam.

Risiko:

- kann Rusher zu stark schwächen.
- kann Expansion und Krieg dieselbe Ressource zu stark belasten.

Status: interessante Balancing-Variante, aber nicht Teil der v0.4-Baseline.

## 7. Repair / Stabilisieren

Hotspot-Analyse zeigte, dass manche Felder extrem oft erobert werden.

Mögliche spätere Aktion:

```text
Stabilisieren
Kosten: Holz oder Stein
Effekt: contested_count senken oder active_from_round früher machen
```

Varianten:

```text
2 Holz → cooldown um 1 reduzieren
2 Stein → contested_count um 1 reduzieren
```

Nutzen:

- macht Front-Hotspots strategisch bearbeitbar.
- gibt Holz/Stein zusätzliche Sinks.
- passt thematisch zu Befestigung, Reparatur und Kontrolle.

Risiko:

- zusätzliche Komplexität.
- sollte erst nach Terminal-Playtest entschieden werden.

## 8. Erschöpfte Felder

Alternative oder Ergänzung zu Repair:

```text
Wenn contested_count >= X:
Feld gilt als exhausted/ruined.
```

Mögliche Effekte:

- produziert temporär nicht.
- produziert dauerhaft -1.
- muss stabilisiert werden.
- kann nicht sofort weiter geraidet werden.

Status: starkes Konzept, aber aktuell zu früh für Baseline.

## 9. Siegbedingungen

Aktuell verwendet die Analyse 60 Prozent Gebietskontrolle.

Spätere Kandidaten:

- 60 Prozent Gebietskontrolle.
- Core-Rush / gegnerischen Core erreichen.
- Punktsystem nach Feldern, Upgrades und Stabilität.
- Ausdauer-/Ressourcen-Sieg nur bei Upkeep-System.

Empfehlung: 60 Prozent bleibt vorerst Mess- und Testsiegbedingung.

## 10. Editor-Perspektive

Langfristig soll Maillon von datengetriebenen Regeln profitieren.

Editor-relevante spätere Datenbereiche:

- Boardgröße.
- Startpositionen.
- Ressourcen-Caps.
- Build-Kostenkurve.
- Raid-Kostenmodell.
- Cooldown-Regeln.
- Bot-Policies.
- Siegbedingungen.
- Szenario-Parameter.

Wichtig: Der Editor ist Folgeprojekt, nicht Voraussetzung für den Terminal-Prototyp.

## Priorität

Empfohlene Reihenfolge:

1. v0.4-Regeln dokumentieren.
2. Analyseartefakte sauber versionieren.
3. Terminal-Prototyp vorbereiten.
4. Utility-Bot oder Action-Log-gestützte Gegnerdiagnose.
5. Core Level 3 / Repair / Raid +1 Holz einzeln testen.
6. Erst danach Editor-Konzept konkretisieren.
