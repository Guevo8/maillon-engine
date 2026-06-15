
Maillon v0.7.1 — Utility Calibration & Opening Probes

Zweck

v0.7.1 ist kein Buff-/Nerf-Schritt.

v0.7.1 ist ein Kalibrierungs- und Validierungsschritt.

Ziel ist, die Utility-Bot-Logik als Messinstrument zu schärfen und gezielt zu prüfen, welche Grundstrategien im aktuellen Regelwerk stark, schwach, dominant oder nur scheinbar stark sind.

---

Ausgangslage v0.7

Maillon v0.7 integriert den "utility_tunneler" in den Main-Branch.

Bisheriger Stand:

Utility-Tunneler integriert.
Smoke-Tests bestanden.
Decision-Probe erzeugt.
Runtime-Matrix kann utility_tunneler auswerten.
Dokumentation für v0.7-Freeze vorhanden.
Generierte CSV-Reports werden nicht als Source-of-Truth behandelt.

Wichtig:

v0.7 ist ein Validierungsstand.
v0.7 ist kein Balance-Freeze.

---

Bisherige Kernerkenntnisse

Die bisherigen Messungen zeigen:

Der Utility-Tunneler ist technisch integriert.
Der Bot läuft stabil in der Runtime-Matrix.
Tunnelaktionen werden gezählt.
Finale Tunnelmetriken werden erfasst.
Der Utility-Tunneler ist nicht offensichtlich OP.
Der Utility-Tunneler verliert gegen bestehende Vergleichsbots.

Besonders wichtig:

Nicht-Mirror-Matchups mit Utility-Tunneler: 12
Utility-Tunneler-Siege: 0

Interpretation:

Der aktuelle Utility-Tunneler ist nicht dominant.
Er ist eher konservativ oder strategisch noch nicht konkurrenzfähig.

Aber:

Das beweist nicht, dass Tunnel als Mechanik grundsätzlich schwach sind.

Der aktuelle Utility-Tunneler ist kein Tunnel-All-In-Exploit-Sucher, sondern ein vorsichtiger Utility-Bot mit Tunneloption.

---

Methodische Korrektur

Nicht aus den Daten ableiten:

Tunnel sind schwach.
Tunnel sind fair.
Tunnel müssen gebufft werden.
Utility-Bot muss einfach stärker werden.

Besser ableiten:

Die aktuelle konservative Tunnel-Entscheidungslogik konvertiert Tunneloptionen noch nicht zuverlässig in Siege.

Daraus folgt:

Vor Gewichtsänderungen müssen die wichtigsten Grundstrategien isoliert geprüft werden.

---

Ziel von v0.7.1

v0.7.1 soll beantworten:

Kann das Utility-Scoring-System die wichtigsten Entscheidungstypen sichtbar unterscheiden und bewerten?

Relevante Entscheidungstypen:

Entscheidungstyp| Aktion / Mechanik
Expansion| "build"
Aggression| "raid"
Defense| "fortify"
Economy| "rebuild", Ressourcentypen
Development| "field_upgrade", "core_upgrade"
Fallback / Tempo| "wait"
Tunnel-Infrastruktur| "tunnel_entrance", "tunnel_extend"
Tunnel-Offense| "tunnel_raid"
Tunnel-Recovery| "repair_build"

---

Warum nicht sofort Utility-Tunneler tunen?

Direktes Tuning wäre zu früh, weil mehrere Ursachen möglich sind:

Tunnel-Scoring zu konservativ.
Normale Utility-Baseline zu dominant.
Rush-/Raid-Meta zu stark.
Resource-Spam zu effizient.
Expansion zu wichtig.
Wait-/Fallback-Verhalten verzerrt.
Tunnelmechanik zu langsam.
Tunnel-Follow-up fehlt.

Wenn man jetzt nur Gewichte verändert, optimiert man möglicherweise gegen ein unklar vermessenes Meta-Problem.

Deshalb:

Erst Kalibrierung.
Dann Tuning.

---

v0.7.1 Arbeitsprinzip

v0.7.1 nutzt drei Ebenen:

1. Dokumentation der Scoring-Logik
2. Opening-/Exploit-Probes
3. Vergleich gegen Utility-Bots

Nicht Ziel:

perfekte KI
Minimax
Machine Learning
vollständige Spielbaum-Suche

Ziel:

kleine, deterministische, erklärbare Testinstrumente

---

Probe-Strategien

1. "opening_resource_spammer"

Hypothese:

2-3 Holzfelder sichern,
danach 2-3 Kornfelder sichern,
anschließend Ressourcen möglichst sofort in Build/Raid umsetzen.

Prüffrage:

Ist frühe Ressourcen- und Action-Economy stärker als differenzierte Utility-Entscheidungen?

Mögliche Logik:

Early:
- Holz priorisieren, bis Build-Nachschub stabil ist.
- Korn priorisieren, sobald Raid-Potenzial absehbar ist.
- Stein nur minimal oder situativ.

Mid:
- Build, wenn möglich.
- Raid, wenn sinnvoll und bezahlbar.
- Keine komplexen Tunnel.
- Kein übermäßiges Fortify.

Nutzen:

Prüft, ob das Grundspiel durch einfache Ressourcen-Tempo-Strategie dominiert wird.

---

2. "pure_rush_probe"

Hypothese:

Frühe Aggression schlägt Aufbau, wenn Raid-Kosten und Takeover-Tempo zu stark sind.

Prüffrage:

Ist Raid/Takeover im aktuellen Regelwerk zu effizient?

Mögliche Logik:

1. Raid, wenn möglich.
2. Build nur, wenn kein Raid möglich ist.
3. Korn bevorzugt bauen.
4. Fortify/Rebuild/Upgrade fast ignorieren.
5. Ziel: Territory oder Domination so früh wie möglich.

Nutzen:

Prüft, ob Rush die Meta bricht.

---

3. "greedy_expander_probe"

Hypothese:

Board-Control über neutrale Felder ist stärker als Kampf.

Prüffrage:

Ist reines Expandieren bis zur Territory-Schwelle dominant?

Mögliche Logik:

1. Build, wenn möglich.
2. Neutrale Felder priorisieren.
3. Richtung Territory-Schwelle spielen.
4. Raid nur, wenn Expansion blockiert ist.
5. Fortify/Rebuild/Upgrade niedrig priorisieren.

Nutzen:

Prüft, ob Build/Expansion im aktuellen System zu stark ist.

---

4. "tunnel_all_in_probe"

Hypothese:

Tunnel können OP sein, wenn man sie erzwingt.

Prüffrage:

Ist die Tunnelmechanik gefährlich, wenn der Bot nicht konservativ auf normale Utility-Baseline zurückfällt?

Mögliche Logik:

1. Tunnel-Eingang so früh wie möglich.
2. Tunnel erweitern, wenn möglich.
3. Tunnel-Raid sofort nutzen, wenn verfügbar.
4. Normale Aktionen nur als Fallback.
5. Repair nur bei echtem Collapse-/Recovery-Wert.

Nutzen:

Prüft die Mechanik selbst, nicht nur den vorsichtigen Utility-Tunneler.

---

5. "anti_tunnel_guard" spätere Probe

Diese Probe ist erst sinnvoll, wenn Tunnel-All-In gefährlich wird.

Hypothese:

Starke Tunnel brauchen Counterplay.

Prüffrage:

Kann ein Gegner Tunnel-Offense erkennen und sinnvoll beantworten?

Mögliche Logik:

1. Felder mit Tunnelbedrohung sichern.
2. Fortify priorisieren, wenn Tunnel-Raid droht.
3. Druck auf Tunnelzugänge erzeugen.
4. Repair-/Collapse-Situationen ausnutzen.

Nutzen:

Prüft Counterplay.

---

Empfohlene Reihenfolge

Nicht alle Probes gleichzeitig bauen.

Empfohlen:

Phase 1:
- opening_resource_spammer
- tunnel_all_in_probe

Phase 2:
- pure_rush_probe
- greedy_expander_probe

Phase 3:
- anti_tunnel_guard, nur falls nötig

Begründung:

opening_resource_spammer prüft die Economy-/Tempo-Grundthese.
tunnel_all_in_probe prüft die Tunnelmechanik direkt.

Diese beiden liefern den größten Erkenntnisgewinn mit dem kleinsten zusätzlichen Bot-Aufwand.

---

Erwartete Ergebnisdeutung

Fall A: "opening_resource_spammer" dominiert

Dann liegt das Problem wahrscheinlich bei:

Ressourcenproduktion
Baukosten
Aktionen pro Turn
Build-Tempo
Korn-/Holz-Verhältnis
Waste-/Cap-Mechanik

Dann sollte nicht zuerst Tunnel getuned werden.

---

Fall B: "pure_rush_probe" dominiert

Dann liegt das Problem wahrscheinlich bei:

Raid-Kosten
Takeover-Wert
Shield-Wirkung
Fortify-Counterplay
Tempo bis Territory / Domination

Dann sollte Combat/Defense geprüft werden.

---

Fall C: "greedy_expander_probe" dominiert

Dann liegt das Problem wahrscheinlich bei:

Build-Effizienz
Territory-Schwelle
Board-Fill-Dynamik
Neutrale-Felder-Wert

Dann sollte Expansion geprüft werden.

---

Fall D: "tunnel_all_in_probe" dominiert

Dann sind Tunnel potenziell gefährlich.

Dann prüfen:

Tunnelkosten
Tunnel-Extend-Tempo
Tunnel-Raid-Wert
Shield-Bypass
Collapse-Risiko
Counterplay

---

Fall E: "tunnel_all_in_probe" verliert deutlich

Dann ist die Tunnelmechanik wahrscheinlich:

zu langsam
zu teuer
zu riskant
zu wenig payoff-stark
oder ohne ausreichendes Follow-up

Dann kann Utility-Tunneler-Tuning sinnvoll werden.

---

Runtime-Matrix für v0.7.1

Geplante Matrix:

python -m analysis.runtime_matrix \
  --side-lengths 4 5 \
  --policies opening_resource_spammer tunnel_all_in_probe pure_rush_probe greedy_expander_probe utility_balancer utility_tunneler rusher phase_player \
  --max-rounds 80 \
  --actions-per-turn 3 \
  --out analysis/reports/runtime_matrix_v0_7_1_calibration.csv

Hinweis:

Die CSV sollte lokales Analyseartefakt bleiben.
Eine kompakte Markdown-Auswertung ist wertvoller als Rohdaten im Repo.

---

Auswertungskriterien

Für jede Probe relevant:

Winrate
Win reason
Final round
Controlled fields
Neutral fields
Build count
Raid count
Fortify count
Wait count
Tunnel entrance count
Tunnel extend count
Tunnel raid count
Waste nach Ressource
Final shield stats
Final tunnel stats

Besonders wichtig:

Gewinnt eine Probe schnell?
Gewinnt sie unabhängig von Sitzposition?
Gewinnt sie auf side_length 4 und 5?
Gewinnt sie über denselben Win reason?
Erzeugt sie auffällige Action-Muster?
Hat der Gegner sichtbares Counterplay?

---

Dokumentationsregeln

Für v0.7.1 gelten diese Regeln:

Keine großen Rohdaten als primäre Projekterklärung.
Keine nicht-deterministischen Artefakte committen.
CSV nur committen, wenn bewusst als deterministisches Referenzartefakt markiert.
Primär Markdown-Summary committen.
Keine Gewichte ändern, ohne vorher Hypothese + Testfrage zu notieren.

---

Minimale Definition of Done

v0.7.1 ist ausreichend abgeschlossen, wenn:

1. Mindestens zwei Probe-Strategien existieren.
2. Runtime-Matrix gegen Utility-Bots läuft.
3. Ergebnisse als Markdown ausgewertet sind.
4. Es klar ist, ob zuerst Economy, Rush, Expansion oder Tunnel geprüft/getuned werden muss.

Optional:

5. Utility-Tunneler-Entscheidungen werden gegen Probe-Strategien erklärt.
6. Wait-Fälle werden gesondert geprüft.
7. Tunnel-Raid-Follow-up wird als eigene Frage dokumentiert.

---

Nicht-Ziele für v0.7.1

Kein Godot-Port.
Kein UI-Fokus.
Kein vollständiges Balancing.
Kein Minimax.
Kein Machine Learning.
Kein großer Bot-Zoo.
Keine massiven Tunnel-Buffs.
Keine Regeländerungen ohne vorherige Probe.

---

Entscheidung nach v0.7.1

Nach v0.7.1 gibt es drei mögliche Wege.

Weg A: Core-Meta zuerst

Wenn Resource/Rush/Expansion dominant ist:

Core-Economy und Combat-Meta prüfen.
Utility-Tunneler bleibt vorerst unverändert.

Weg B: Tunnelmechanik zuerst

Wenn Tunnel-All-In gefährlich oder extrem schwach ist:

Tunnelkosten, Collapse, Raid-Wert und Counterplay prüfen.

Weg C: Utility-Kalibrierung zuerst

Wenn Probe-Strategien plausibel funktionieren, aber Utility-Bots schlecht reagieren:

Utility-Gewichte / strategic_pressure / Fallback-Logik kalibrieren.

---

Leitgedanke

v0.7.1 soll nicht beweisen, dass ein Bot stark ist.

v0.7.1 soll beweisen, dass Maillon strategische Grundmuster sichtbar messen kann.

Der zentrale Satz:

Maillon braucht keine perfekte KI, sondern eine erklärbare Entscheidungslogik, die Spielmechaniken sichtbar, vergleichbar und kalibrierbar macht.

