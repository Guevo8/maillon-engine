
Utility Scoring Overview

Zweck

Dieses Dokument beschreibt die Utility-Scoring-Logik der modernen Maillon-Bots.

Die Utility-Bots sind keine reinen If/Else-Bots. Sie erzeugen alle legalen normalen Aktionen, bewerten jede Aktion quantitativ und wählen anschließend die beste Aktion anhand eines vergleichbaren Scores.

Ziel der Utility-Logik ist nicht nur Gegner-KI, sondern auch Messbarkeit:

- Welche Aktion ist in einem Spielzustand attraktiv?
- Warum wurde Build statt Raid gewählt?
- Wann wird Defense sinnvoll?
- Wann wird Wait als Sparaktion akzeptiert?
- Welche Bot-Persönlichkeit verschiebt welche Priorität?
- Welche Spielmechaniken dominieren die Entscheidung?

Die Utility-Scoring-Logik ist damit ein zentrales Analysewerkzeug für Maillon.

---

Grundprinzip

Der normale Utility-Bot arbeitet in vier Schritten:

1. Alle legalen normalen Kandidaten-Aktionen erzeugen.
2. Jede Aktion lokal bewerten.
3. Den lokalen Score durch strategischen Spielkontext anpassen.
4. Den angepassten Score mit dem Personality-Gewicht multiplizieren.

Vereinfachtes Modell:

adjusted_raw = local_raw * strategic_multiplier + strategic_bonus
total_score  = adjusted_raw * personality_category_weight

Der Bot wählt die Aktion mit dem höchsten "total_score".

Wichtig: "strategic_bonus" ist kein reiner Multiplikator. Dadurch können bestimmte Aktionen in Finish-, Rückstands- oder Anti-Stall-Situationen deutlich stärker werden, auch wenn ihr lokaler Rohwert nicht maximal ist.

---

Normale Action-Kandidaten

Die Utility-Logik erzeugt normale Kandidaten aus diesen Aktionstypen:

Aktion| Kategorie| Bedeutung
"build"| "expansion"| Neues Feld bauen / Boardkontrolle erweitern
"raid"| "aggression"| Gegnerisches Feld angreifen / übernehmen
"fortify"| "defense"| Eigenes Feld gegen Raid schützen
"field_upgrade"| "development"| Feldproduktion verbessern
"core_upgrade"| "development"| Core-Level / Caps verbessern
"rebuild"| "economy"| Ressourcentyp eines eigenen Feldes ändern
"wait"| "fallback"| Aktion sparen / Ressource aufbauen

Tunnelaktionen werden nicht vom normalen Utility-Scoring direkt bewertet. Sie laufen über den separaten Utility-Tunneler-Overlay.

---

Utility Categories

Jede Aktion wird einer strategischen Kategorie zugeordnet:

build         -> expansion
raid          -> aggression
fortify       -> defense
field_upgrade -> development
core_upgrade  -> development
rebuild       -> economy
wait          -> fallback

Diese Kategorie entscheidet, welches Personality-Gewicht auf den Score angewendet wird.

---

Personality Weights

Die Utility-Bots nutzen unterschiedliche Persönlichkeiten.

Aktuelle Utility-Personas:

rusher
economist
fortifier
balancer
aggro_turtle
opportunist

Daraus entstehen Policies wie:

utility_rusher
utility_economist
utility_fortifier
utility_balancer
utility_aggro_turtle
utility_opportunist

Jede Personality hat pro Spielphase eigene Gewichte:

early
mid
late

Beispielhafte Bedeutung:

Personality| Schwerpunkt
"rusher"| Expansion + Aggression
"economist"| Economy + Development
"fortifier"| Defense + Stabilisierung
"balancer"| Ausgewogene Entscheidung
"aggro_turtle"| Defense + kontrollierte Aggression
"opportunist"| aggressive Chancenverwertung

Die Personality-Gewichte verändern nicht die Legalität einer Aktion. Sie verändern nur, wie stark eine strategische Kategorie im Verhältnis zu anderen Kategorien bewertet wird.

---

Lokale Score-Funktionen

Jede normale Aktion hat eine eigene lokale Bewertungsfunktion.

"score_build"

Bewertet ein mögliches neues Feld.

Wichtige Faktoren:

- Ressourcenbedarf für den Feldtyp
- eigene Nachbarn
- gegnerische Nachbarn
- Nähe zum gegnerischen Core
- Board-Fill-Pressure
- Feldtyp-Wert
- aktuelle Baukosten

Interpretation:

Build wird attraktiver, wenn:
- der Ressourcentyp gebraucht wird,
- das Feld gut angebunden ist,
- es Druck Richtung Gegner erzeugt,
- das Board sich füllt,
- der Build bezahlbar ist.

"score_raid"

Bewertet einen Angriff auf ein gegnerisches Feld.

Wichtige Faktoren:

- Wert des Zielfelds
- Level des Zielfelds
- Nähe zum gegnerischen Core
- gegnerischer Fortschritt
- contested_count
- Raid-Shield
- Kornkosten

Interpretation:

Raid wird attraktiver, wenn:
- das Zielfeld wertvoll ist,
- es nahe am gegnerischen Core liegt,
- der Gegner verwundbar ist,
- der Raid nicht zu teuer ist,
- kein hoher Shield-Wert blockiert.

"score_fortify"

Bewertet defensive Absicherung.

Wichtige Faktoren:

- gegnerische Nachbarn
- contested_count
- Feldtyp-Wert
- Nähe zum eigenen Core
- vorhandener Shield-Wert
- Kornkosten

Interpretation:

Fortify ist vor allem an Frontfeldern sinnvoll.
Abseits der Front wird Fortify stark abgewertet.

"score_field_upgrade"

Bewertet Ausbau eines eigenen Feldes.

Wichtige Faktoren:

- Feldtyp
- Level
- Stein-Druck
- contested_count
- Stein-Kosten

"score_core_upgrade"

Bewertet Core-Upgrade.

Wichtige Faktoren:

- durchschnittlicher Ressourcendruck
- Anzahl kontrollierter Nicht-Core-Felder
- Stein-Kosten

"score_rebuild"

Bewertet Umwandlung eines Feldtyps.

Wichtige Faktoren:

- neuer Ressourcenbedarf
- alter Ressourcendruck
- contested_count
- Holz-Kosten

"score_wait"

Wait ist Fallback. Der lokale Score ist niedrig. Wait kann aber durch strategische Regeln sinnvoll werden, wenn der Bot bewusst für einen späteren Build sparen soll.

---

Strategische Kontext-Schicht

Nach der lokalen Bewertung wird "apply_strategic_pressure" angewendet.

Diese Schicht bewertet nicht mehr nur das einzelne Ziel, sondern die globale Spielsituation.

Wichtige Kontextfragen:

Bin ich nah am 60%-Sieg?
Ist der Gegner nah am 60%-Sieg?
Liege ich zurück?
Liege ich weit zurück?
Gibt es viele neutrale Felder?
Ist ein Finish-Fenster erreicht?
Droht ein Stall?
Soll Holz für den nächsten Build gespart werden?

Typische Effekte

Situation| Wirkung
Actor nah am Territory-Sieg| Build/Raid hoch, passive Aktionen runter
Gegner nah am Territory-Sieg| Build/Raid als Interrupt hoch, Wait/Rebuild/Fortify runter
Actor liegt zurück| Build/Raid hoch, Turtle-Aktionen runter
Viele neutrale Felder| Build stark hoch
Finish Window| Build wird stark priorisiert
Stall Window| Build gegen Raid-Churn/Stall hoch
Holz knapp, Build möglich in Zukunft| Rebuild runter, Wait kann sinnvoll werden

Diese Schicht verhindert typische Bot-Probleme:

- zu viel Turtling
- sinnlose Rebuild-Schleifen
- zu spätes Expandieren
- passives Verhalten bei gegnerischem Siegdruck
- Raid-Churn ohne Board-Fortschritt

---

Auswahl der besten Aktion

Die finale Auswahl läuft über:

generate_candidate_actions
-> score_candidate_actions
-> score_action pro Aktion
-> UtilityScore
-> Sortierung
-> choose_best_utility_action

Sortierung:

1. Höchster "total_score"
2. Action-Priority als Tiebreaker
3. deterministische Koordinatenreihenfolge

Dadurch bleibt das Verhalten reproduzierbar.

---

Mermaid Flowchart

flowchart TD
    A[generate_candidate_actions\nalle legalen normalen Aktionen]
    --> B[score_candidate_actions]

    B --> C[score_action\nbewertet jede Aktion]

    C --> D[category_for_action\nexpansion, aggression, defense, economy, development, fallback]
    C --> E[score_xxx lokal\nscore_build, score_raid, score_fortify, upgrades, rebuild, wait]

    E --> F[apply_strategic_pressure\nSiegdruck, Rückstand, neutrale Felder, Anti-Stall]
    D --> G[get_weights_for_state\nPersonality + Phase]

    F --> H[adjusted_raw]
    G --> I[category_weight]

    H --> J[total_score = adjusted_raw × category_weight]
    I --> J

    J --> K[UtilityScore\nraw_score, weight, total_score, reasons]
    K --> L[sortieren nach total_score\n+ Action-Priority + Koordinaten]
    L --> M[choose_best_utility_action]
    M --> N[Aktion ausführen]

    style C fill:#e3f2fd
    style F fill:#f3e5f5
    style K fill:#e8f5e9

---

Warum diese Architektur wertvoll ist

Die Utility-Scoring-Logik trennt sauber:

Lokale Aktionsqualität
Personality-Gewichtung
Globale Spielsituation
Deterministische Auswahl
Erklärbare Gründe

Dadurch wird der Bot nicht nur spielbar, sondern analysierbar.

Der wichtigste Projektwert:

Maillon enthält eine erklärbare, gewichtete Bot-Entscheidungslogik zur Validierung von Spielmechaniken und Strategieprofilen.

---

Aktuelle Limitationen

Die Utility-Scoring-Logik ist bewusst kein Minimax und kein Machine Learning.

Aktueller Charakter:

Greedy + Scoring + strategischer Kontext

Das bedeutet:

- keine echte Mehrzug-Vorausschau,
- keine vollständige Spielbaum-Suche,
- keine optimale mathematische Lösung,
- manuell kalibrierte Gewichtungen,
- gute Erklärbarkeit, aber keine perfekte Spielstärke.

Das ist für den aktuellen Projektstand sinnvoll, weil Maillon zuerst ein nachvollziehbares Validierungs- und Balancing-System braucht, bevor komplexere KI-Verfahren relevant werden.

---

Offene Validierungsfragen

Für die nächste Kalibrierung sind besonders wichtig:

- Erkennt der Bot frühe Expansion korrekt?
- Reagiert der Bot angemessen auf Rush?
- Wird Fortify nur an sinnvollen Frontfeldern genutzt?
- Wird Rebuild wirklich als Economy-Werkzeug genutzt oder nur als Fallback?
- Ist Wait ein bewusstes Sparen oder ein Symptom fehlender Optionen?
- Verdrängen Build/Raid zu stark andere Entscheidungstypen?
- Sind die Personality-Unterschiede sichtbar genug?
- Sind die Ergebnisse reproduzierbar und erklärbar?

