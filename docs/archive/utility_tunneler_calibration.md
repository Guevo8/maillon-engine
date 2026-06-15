
Utility Tunneler Calibration

Zweck

Dieses Dokument beschreibt den "utility_tunneler" als Tunnel-Overlay über dem normalen Utility-Bot.

Der "utility_tunneler" ist kein Tunnel-All-In-Bot. Er ist ein konservativer Utility-Bot, der Tunnelaktionen nur dann nimmt, wenn sie im Vergleich zur besten normalen Utility-Aktion ausreichend attraktiv sind.

Ziel ist nicht, den Bot blind stärker zu machen. Ziel ist, die Tunnelentscheidung mathematisch nachvollziehbar und als Messinstrument nutzbar zu machen.

---

Grundidee

Der Utility-Tunneler arbeitet mit zwei parallelen Bewertungsräumen:

1. Normale Utility-Baseline
   Build, Raid, Fortify, Upgrade, Rebuild, Wait

2. Tunnel-Feature-Score
   tunnel_entrance, tunnel_extend, tunnel_raid, repair_build, wait

Der Bot nimmt eine Tunnelaktion nur, wenn:

best_tunnel_score >= normal_baseline - opportunity_cost_tolerance

Aktuell:

opportunity_cost_tolerance = 0.10

Beide Werte liegen im normalisierten 0-1-Raum.

---

Entscheidungsablauf

1. Erzeuge alle legalen Tunnelkandidaten.
2. Berechne die beste normale Utility-Aktion als Baseline.
3. Normalisiere die Baseline auf 0-1.
4. Bewerte jeden Tunnelkandidaten über Tunnel-Features.
5. Sortiere die Tunnelkandidaten.
6. Vergleiche den besten Tunnelkandidaten gegen die normale Baseline.
7. Wähle Tunnel, wenn Opportunity-Cost klein genug ist.
8. Sonst Fallback auf normale Utility-Aktion.

---

Mermaid Flowchart

flowchart TD
    A[choose_utility_tunneler_action]
    --> B[generate_tunnel_candidates\nTunnel Entrance, Extend, Raid, Repair, Wait]

    A --> C[_get_normal_baseline\nbeste normale Utility-Aktion\nnormalisiert 0-1]

    B --> D[score_tunnel_candidate\nFeature-Scoring pro Tunnelaktion]
    D --> E[resource_fit]
    D --> F[tunnel_access_gain]
    D --> G[enemy_tunnel_threat]
    D --> H[own_tunnel_pressure]
    D --> I[collapse_risk]
    D --> J[raid_value / repair_value]
    D --> K[territory_pressure]

    E --> L[tunnel_score 0-1]
    F --> L
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L

    C --> M{tunnel_score >= normal_baseline - 0.10?}
    L --> M

    M -->|Ja| N[beste Tunnelaktion wählen]
    M -->|Nein| O[Fallback:\nbeste normale Utility-Aktion]

    style A fill:#e3f2fd
    style D fill:#fff3e0
    style M fill:#f3e5f5

---

Tunnelaktionen

Aktion| Funktion
"tunnel_entrance"| Einstieg in das Tunnelnetz auf einem Feld
"tunnel_extend"| Erweiterung des Tunnelnetzes von einem Knoten zu einem neuen Ziel
"tunnel_raid"| Angriff über Tunnelzugang, inklusive Shield-Bypass-Potenzial
"repair_build"| Wiederaufbau / Reparatur im Tunnelkontext
"wait"| Fallback-Kandidat innerhalb des Tunnelkandidatenraums

---

Tunnel Features

Jede Tunnelaktion wird über mehrere Features bewertet.

Feature| Bedeutung
"resource_fit"| Wie gut kann sich der Actor die Aktion leisten?
"tunnel_access_gain"| Wie stark verbessert die Aktion das Tunnelnetz?
"enemy_tunnel_threat"| Wie stark stehen eigene Felder unter Tunnel-/Pressure-Bedrohung?
"own_tunnel_pressure"| Erhöht die Aktion eigenen Tunnel-Pressure / Collapse-Gefahr?
"collapse_risk"| Risiko eigener Collapses
"raid_value"| Wert eines Tunnel-Raids
"repair_value"| Wert einer Repair-/Rebuild-Aktion
"territory_pressure"| Globale Siegdrucksituation

---

Aktuelle Gewichtungslogik

Die Tunnelaktionen haben eigene Gewichtungen.

"tunnel_entrance"

Fokus:

resource_fit
tunnel_access_gain
enemy_tunnel_threat
collapse_risk
territory_pressure

Interpretation:

Ein Tunnel-Eingang soll attraktiv sein, wenn er bezahlbar ist, Zugang erzeugt und in einer relevanten Board-Situation passiert.

"tunnel_extend"

Fokus:

resource_fit
tunnel_access_gain
enemy_tunnel_threat
own_tunnel_pressure
collapse_risk
territory_pressure

Interpretation:

Tunnel-Erweiterung soll Netzwerkwert erzeugen, aber nicht blind Pressure und Collapse-Risiko erhöhen.

"tunnel_raid"

Fokus:

resource_fit
enemy_tunnel_threat
raid_value
territory_pressure

Interpretation:

Tunnel-Raid soll vor allem dann attraktiv sein, wenn das Ziel wertvoll ist und der Raid taktisch oder strategisch relevant ist.

"repair_build"

Fokus:

resource_fit
tunnel_access_gain
repair_value
territory_pressure

Interpretation:

Repair-Build soll nicht als generischer Build-Ersatz dienen, sondern nur bei echtem Wiederaufbau-/Netzwerkwert relevant werden.

---

Opportunity-Cost-Prinzip

Der wichtigste Designpunkt ist die Opportunity-Cost-Schwelle.

Der Bot fragt nicht nur:

Ist diese Tunnelaktion gut?

Sondern:

Ist diese Tunnelaktion gut genug, um auf die beste normale Aktion zu verzichten?

Das verhindert Tunnelspam.

Gleichzeitig kann diese Regel den Bot zu konservativ machen, wenn Tunnelaktionen langfristigen Wert erzeugen, der im aktuellen Einzelschritt noch nicht sichtbar genug ist.

---

Was die bisherigen v0.7-Daten zeigen

Die bisherigen Outcome- und Decision-Probes deuten auf Folgendes:

Integration funktioniert.
Der Utility-Tunneler ist nicht offensichtlich OP.
Der Bot nutzt Tunnelaktionen, aber verliert gegen bestehende Vergleichsbots.
Tunnel-Entrance wird sichtbar genutzt.
Tunnel-Extend wird selten gewählt.
Tunnel-Raid kommt vor, konvertiert aber nicht zuverlässig in Siege.
Repair-Build ist aktuell praktisch nicht relevant.

Diese Daten beweisen nicht, dass Tunnel grundsätzlich schwach sind.

Sie zeigen:

Die aktuelle konservative Utility-Tunneler-Entscheidung gewinnt noch nicht gegen die vorhandene Tempo-/Expansion-/Raid-Meta.

---

Wichtige methodische Grenze

Der Utility-Tunneler ist aktuell kein Exploit-Sucher.

Er beantwortet die Frage:

Wann würde ein vorsichtiger Utility-Bot eine Tunneloption gegenüber einer normalen Aktion bevorzugen?

Er beantwortet noch nicht zuverlässig:

Sind Tunnel als Mechanik potenziell OP, wenn man sie erzwingt?

Dafür braucht es eigene Probe-Strategien wie:

tunnel_all_in_probe
pure_rush_probe
opening_resource_spammer

---

Aktuelle Stärken

- Klare Trennung von normalem Utility-Bot und Tunnel-Overlay.
- Tunnelaktionen werden legalitäts- und kostenbasiert erzeugt.
- Feature-Scoring ist erklärbar.
- Opportunity-Cost ist explizit.
- Scores liegen im normalisierten 0-1-Raum.
- Runtime-Matrix zählt Tunnelaktionen und finale Tunnelmetriken.
- Gute Basis für reproduzierbare Kalibrierung.

---

Aktuelle Schwächen / offene Punkte

1. Langfristiger Tunnelwert ist schwer sichtbar

"tunnel_entrance" und "tunnel_extend" erzeugen oft Infrastrukturwert. Dieser Wert zahlt sich möglicherweise erst später aus.

Greedy-Scoring kann diesen Zukunftswert unterschätzen.

2. Tunnel-Raid-Follow-up fehlt

Ein Tunnel-Raid kann taktisch gut sein, aber der Bot braucht danach eventuell Folgeprioritäten:

- erobertes Feld halten,
- Druck fortsetzen,
- Nachbarfelder sichern,
- Shield-/Fortify-Situation bewerten,
- nicht in Wait oder normale ineffiziente Aktionen zurückfallen.

3. "repair_build" ist noch kein aktiver Faktor

Wenn "repair_build" dauerhaft 0 bleibt, ist entweder die Mechanik selten relevant oder der Bot erkennt sie nicht sinnvoll.

4. Tunnel-Features sind additiv

Aktuell werden Features additiv gewichtet.

Mögliche Interaktionen fehlen noch:

guter raid_value + guter Follow-up-Zugang
hoher territory_pressure + tunnel_raid
enemy_tunnel_threat + repair_build

Diese Interaktionen sollten erst nach weiteren Tests ergänzt werden.

5. Namen können missverständlich sein

"enemy_tunnel_threat" sollte dokumentarisch vorsichtig gelesen werden:

Bedrohung eigener Felder durch bestehende Tunnel-/Pressure-Struktur.

Nicht einfach:

Der Gegner hat viele Tunnel.

---

Kalibrierungsfragen

Vor jedem Tuning sollten diese Fragen beantwortet werden:

Tunnel Entrance

- Wird ein Eingang gebaut, bevor er sinnvoll nutzbar ist?
- Wird ein Eingang zu spät gebaut?
- Werden Eingänge auf Feldern mit echtem Netzwerk-/Raumwert bevorzugt?
- Baut der Bot Eingänge, ohne später zu extenden?

Tunnel Extend

- Wird Extend nur selten gewählt, weil es wirklich schlecht ist?
- Oder fehlt Zukunftswert im Score?
- Entstehen Sackgassen?
- Entstehen Wege zu relevanten Raid-Zielen?
- Wird Collapse-Risiko angemessen bestraft?

Tunnel Raid

- Wird Tunnel-Raid nur bei guten Zielen gewählt?
- Bypasst er Shield sinnvoll?
- Führt ein Tunnel-Raid zu konkretem Boardvorteil?
- Fehlt nach Tunnel-Raid ein Follow-up?
- Ist Tunnel-Raid zu selten, zu schwach oder nur gegen bestimmte Gegner sinnvoll?

Repair Build

- Gibt es realistische Repair-Situationen?
- Ist Repair zu teuer?
- Ist Repair als Aktion zu spät verfügbar?
- Erkennt der Bot Repair-Wert überhaupt?

Fallback

- Fällt der Bot zu oft auf normale Utility-Aktionen zurück?
- Ist das korrekt oder überkonservativ?
- Ist "OPPORTUNITY_COST_TOLERANCE = 0.10" zu streng?
- Muss die Baseline je Action-Typ anders interpretiert werden?

---

Dokumentierte Nicht-Ziele

Aktuell nicht direkt tun:

Keine blinden Tunnel-Buffs.
Keine Tunnel-Kostenänderung ohne Probe.
Keine OP-/Balance-Aussage nur aus Utility-Tunneler-Niederlagen.
Kein komplexes Minimax einbauen.
Keine ML-Kalibrierung.

Aktuelles Ziel:

Utility-Tunneler als erklärbares Messinstrument stabilisieren.

---

Nächste sinnvolle Tests

1. "tunnel_all_in_probe"

Prüft:

Sind Tunnel gefährlich, wenn man sie erzwingt?

2. "pure_rush_probe"

Prüft:

Ist frühe Aggression grundsätzlich dominant?

3. "opening_resource_spammer"

Prüft:

Ist frühes Ressourcen-/Build-/Raid-Spamming stärker als alle differenzierten Strategien?

4. "utility_tunneler_vs_probe_matrix"

Prüft:

Kann der Utility-Tunneler gegen klar definierte Extremstrategien bestehen?

---

Zielbild

Der Utility-Tunneler soll langfristig nicht einfach stärker werden.

Er soll verständlich beantworten:

Wann lohnt sich Tunnel-Infrastruktur?
Wann lohnt sich Tunnel-Offense?
Wann ist die normale Utility-Aktion besser?
Wann ist Tunnel zu langsam?
Wann ist Tunnel zu riskant?
Wann kippt Tunnel in OP?

Damit wird der Bot zu einem echten Validierungswerkzeug für die Tunnelmechanik.

