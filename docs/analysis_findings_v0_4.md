# Maillon v0.4 — Analysebefunde

Stand: 02-06-2026  
Status: Befunddokument zur deterministischen v0.4-Analyse.

## Zweck

Dieses Dokument hält fest, welche Designentscheidungen durch die v0.4-Analysen gestützt werden. Es ersetzt nicht das Regelwerk, sondern erklärt, warum der aktuelle Prototypkern sinnvoll ist.

Regelwerk: `docs/maillon_v0_4_rules.md`  
Analysewerkzeuge: `analysis/`

## Ausgangspunkt

v0.3 formulierte die Board-Baseline-Hypothese:

- 8 Felder sind zu eng.
- Maillon braucht ein räumliches Hex-Board.
- Boardposition und Feldfunktion müssen getrennt werden.
- Ressourcenlimit, Feldübernahme, Raid, Upgrades und Siegbedingungen müssen neu geprüft werden.

v0.4 ist die analysierte Antwort auf diese Hypothesen.

## 1. Direct Takeover bleibt als Kern sinnvoll

Die Analyse hat gezeigt, dass direkte Feldübernahme grundsätzlich funktioniert:

```text
Raid erfolgreich → owner wechselt sofort
```

Diese Regel ist klar, leicht verständlich und erzeugt sofortige Konsequenz. Eine gestufte Übernahme wurde vorerst nicht benötigt.

Wichtig ist aber: Direct Takeover braucht eine Gegenkraft gegen sofortiges Pingpong. Diese Gegenkraft ist in v0.4 die Feld-Instabilität.

## 2. Nur direkte Raids erzeugen Pingpong

Frühe Testläufe ohne ausreichende Frontbremse erzeugten extrem hohe Raid- und Takeover-Zahlen. In manchen Matchups entstanden 250 bis 300+ Takeovers.

Befund:

```text
Direkte Übernahme allein ist zu volatil.
Direkte Übernahme + Instabilität ist deutlich stabiler.
```

## 3. Ressourcen cappen früh

Die Cap-Verlaufsauswertung zeigte:

- Korn cappt häufig sehr früh.
- Stein und Holz folgen oft bereits im Early-/Midgame.
- Holz erzeugt langfristig die größten Waste-Werte, ist aber nicht das einzige Cap-Problem.

Daraus folgt:

```text
Das System braucht nicht nur mehr Cap, sondern bessere Sinks und Kostenkurven.
```

## 4. Rebuild ist ein sinnvoller Holz-Sink

Umbau/Rebuild wurde als Aktion ergänzt:

```text
2 Holz → eigenes aktives Nicht-Core-Feld ändert Ressourcentyp
```

Befund:

- Rebuild gibt Holz auch nach der Expansion eine Funktion.
- Rebuild unterstützt Ressourcensteuerung.
- Rebuild ist besonders wichtig, wenn Holzfelder später weniger direkte Expansion ermöglichen.

Rebuild ersetzt aber nicht die Notwendigkeit von Kostensteigerung oder Frontlogik.

## 5. Tiered Cost Scaling verbessert das Midgame

Build und Field Upgrade wurden mit tiered costs versehen.

Build-Kosten:

```text
2 / 3 / 5 / 8 / 12 Holz
```

Field-Upgrade-Kosten:

```text
3 / 4 / 6 / 8 / 12 Stein
```

Befund:

- Expansion wird nicht endlos billig.
- Midgame-Entscheidungen werden relevanter.
- Ressourcen werden stärker verbraucht.
- Einige zuvor offene Matchups werden entscheidbarer.

Grenze:

- Tiered costs lösen nicht allein das Front-Pingpong.
- Große Boards können weiterhin Longgame-Waste erzeugen.

## 6. Feld-Instabilität ist ein Schlüsselpatch

Nach jedem erfolgreichen Raid:

```text
contested_count += 1
cooldown = min(3, contested_count)
active_from_round = current_round + cooldown
```

Während Cooldown:

- keine Produktion,
- kein Build-Origin,
- kein Raid-Origin,
- nicht erneut raidbar.

Befund:

- Raid-Pingpong sinkt deutlich.
- Frontfelder werden zu echten Streitpunkten.
- 3 Aktionen pro Zug werden dadurch überhaupt erst plausibel.
- Die Regel erhält Direct Takeover, bremst aber sofortige Durchbruchsketten.

## 7. 3 Aktionen werden zum ernsthaften Kandidaten

Vor Feld-Instabilität wären 3 Aktionen pro Zug wahrscheinlich zu explosiv gewesen.

Nach Feld-Instabilität zeigte die Analyse:

- 37er Board + 3 Aktionen eignet sich als schneller Stress-/Speed-Test.
- 61er Board + 3 Aktionen wirkt wie ein ernsthafter Prototyp-Kandidat.
- Viele Spiele enden in plausiblen Rundenbereichen.

Vorläufige Bewertung:

```text
2 Aktionen = konservativer Vergleich
3 Aktionen = Kandidat für Terminal-Prototyp
```

## 8. `cap_aware_vs_rusher` ist ein Stressfall

Der Fall `61 / cap_aware_vs_rusher / 3 Aktionen` erzeugte sehr hohe Raid-Zahlen und lange Front-Stalls.

Action-Log-Auswertung:

```text
player/cap_aware: 163 Takeovers
enemy/rusher:     159 Takeovers
```

Das ist fast symmetrisch. Beide Seiten stecken in einer Frontmaschine, statt dass eine Seite klar dominiert.

Interpretation:

```text
cap_aware_balanced ist kein normaler Referenzgegner.
cap_aware_balanced ist ein Cap-/Front-Stall-Stressbot.
```

## 9. Hotspot-Analyse bestätigt Frontzonen

Die Hotspot-Analyse zeigte chronisch umkämpfte Felder.

Top-Hotspots im Stressfall:

```text
(0, -1): 23 Takeovers
(-1, 0): 22 Takeovers
(3, 0):  20 Takeovers
(1, -2): 19 Takeovers
(-2, 3): 18 Takeovers
(2, -3): 18 Takeovers
```

Befund:

- Der Stall entsteht nicht überall gleichmäßig.
- Er entsteht an wiederkehrenden Front-Hotspots.
- Cooldown 3 bremst, verhindert extreme Hotspot-Zyklen aber nicht vollständig.

Dieser Befund spricht für spätere Regeln wie Stabilisieren, Reparieren oder stärkere Erschöpfung chronischer Streitfelder.

## 10. Aktueller Gesamtbefund

v0.4 ist als Prototypkern tragfähig:

- Hex-Board 37/61 funktioniert als Teststruktur.
- Direct Takeover bleibt verständlich und wirksam.
- Raid-Kosten nach Support erzeugen Stellungsspiel.
- Rebuild gibt Holz eine zweite Funktion.
- Tiered costs verbessern Midgame-Druck.
- Feld-Instabilität reduziert Raid-Pingpong stark.
- 3 Aktionen sind mit Instabilität ein ernsthafter Kandidat.
- Action-Log und Hotspot-Auswertung machen Frontprobleme sichtbar.

## Offene Befunde

Noch nicht final entschieden:

- Core Level 3 / Cap 18.
- Raid +1 Holz als zusätzliche Logistikkosten.
- Repair/Stabilisieren chronisch umkämpfter Felder.
- Utility-Scoring-Bot als bessere Referenz-Policy.
- finale Siegbedingungen neben 60 Prozent Gebietskontrolle.
- tatsächliches Spielgefühl im Terminal-Prototyp.
