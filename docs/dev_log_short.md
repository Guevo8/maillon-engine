# Maillon — kurzer Entwicklungslog bis v0.4

Stand: 02-06-2026  
Status: kompakte Chronologie, keine vollständige Arbeitsdokumentation.

## Zweck

Dieses Dokument fasst den Entwicklungsweg stark verdichtet zusammen. Es ersetzt weder Regelwerk noch Analysebefunde.

- Aktueller Regelkern: `docs/maillon_v0_4_rules.md`
- Analysebefunde: `docs/analysis_findings_v0_4.md`
- Offene Designfragen: `docs/design_notes_v0_4.md`

## Projektstatus-Modell

```text
v0.1/v0.2 = historische Runtime
v0.3      = Board-Baseline-Hypothese
v0.4      = analysierter Prototypkern
```

## v0.1 — Solo Resource Executor

v0.1 war die erste lauffähige Terminal-Version.

Bestätigt:

- Python-Terminal-Loop.
- Ressourcen Holz, Stein, Korn.
- Bauen.
- Upgrade.
- Aussetzen.
- Überfluss-Check.
- einfache Siegbedingungen.
- JSON Save/Load.

Bedeutung:

```text
Maillon funktioniert grundsätzlich als kleines Terminalspiel.
```

## v0.2 — Conflict Prototype

v0.2 ergänzte den Gegner/Nachbarn und machte das Spiel konflikthaft.

Bestätigt:

- regelbasierter Gegner.
- Raid.
- Mondrunde.
- Feldübernahme.
- Save/Load mit erweitertem Spielstand.

Problem:

- 8 Felder sind zu eng.
- Start mit Dorf + Holz + Stein + Korn ist zu weit entwickelt.
- Besitz, Produktion, Kampfwert und Siegfortschritt liegen zu stark auf derselben Feldliste.

Bedeutung:

```text
Konflikt funktioniert, aber der Raum ist zu eng.
```

## v0.3 — Board-Baseline-Hypothese

v0.3 formulierte den räumlichen Schnitt.

Kernideen:

- Hex-Board statt 8-Feld-Liste.
- 37 Felder als Testboard.
- 61 Felder als strategischer Zieltest.
- Core + Start-Holz statt vollständig entwickeltem Start.
- Boardposition und Feldfunktion trennen.
- räumliches Bauen über Nachbarschaft.

Bedeutung:

```text
v0.3 schafft die Hypothese für Raum, Front und Expansion.
```

## v0.4 — Analysephase

v0.4 konkretisierte die v0.3-Hypothese mit deterministischen Simulationen.

Entwickelte Analysebausteine:

- Hex-Board-Simulation.
- Bot-Policies.
- Ressourcen-Caps.
- Direct Takeover.
- Raid-Kosten nach Support.
- Rebuild/Umbau.
- Field Upgrade.
- Core Upgrade.
- Tiered Cost Scaling.
- Feld-Instabilität nach Raid.
- Action-Log.
- Hotspot-Analyse.

## Wichtigste Erkenntnisse aus v0.4

### Direct Takeover funktioniert

Direkter Besitzerwechsel ist verständlich und erzeugt klare Konsequenz.

### Raid braucht Frontbremse

Ohne Feld-Instabilität erzeugt direkter Raid zu starkes Pingpong.

### Ressourcen cappen früh

Holz, Stein und Korn laufen früh in Cap-Druck. Es braucht sinnvolle Sinks und Kostenkurven.

### Rebuild ist sinnvoll

Umbau gibt Holz nach der Expansion eine zweite strategische Funktion.

### Tiered Cost Scaling verbessert das Midgame

Build und Field Upgrade werden mit Reichsgröße teurer. Das erzeugt bessere Midgame-Entscheidungen.

### Feld-Instabilität ist zentral

Eroberte Felder werden nicht sofort wieder voll nutzbar. Dadurch sinkt Raid-Pingpong deutlich.

### 3 Aktionen werden möglich

Mit Feld-Instabilität wird eine 3-Aktionen-Struktur zu einem ernsthaften Kandidaten für den Terminal-Prototyp.

### Hotspots sind echte Frontzonen

Action-Log und Hotspot-Analyse zeigen, dass Front-Stalls vor allem an wiederkehrenden Streitfeldern entstehen.

## Arbeitsmethode

Der v0.4-Stand entstand durch eine einfache, aber wirksame Schleife:

```text
Hypothese
→ Regelpatch
→ Simulation
→ Messwerte
→ Interpretation
→ nächste Hypothese
```

Diese Methode bleibt für weitere Balancing-Schritte sinnvoll.

## Nächster Schritt

v0.4 sollte als Prototypkern dokumentiert und danach in eine neue Terminal-Runtime überführt werden.

Priorität:

1. Regeln und Analysebefunde festhalten.
2. Analyseartefakte versionieren.
3. Terminal-Prototyp vorbereiten.
4. Danach neue Designvarianten einzeln testen.
