# Maillon Pocket v0.2 — Regelwerk

## Ziel von v0.2

v0.2 macht aus dem Solo-Ressourcen-Executor ein Duell.
Spieler und Nachbar bauen gleichzeitig ein 8-Feld-Maillon auf.
Wer 8 Felder erreicht, gewinnt. Wer es dem Gegner erlaubt — verliert.

---

## Nachbar

Der Nachbar ist keine KI. Er ist eine Bedrohungsuhr.

Startet mit: Holz 2, Stein 1, Korn 1 | Felder: Dorf, Holz, Stein, Korn

### Nachbar-Zug (nach Spieler-Aktionen)

Wenn Holz >= 2 und Korn >= 1 und Felder < 8 → baut ein Feld.  
Sonst → setzt aus (W4).

Der Nachbar baut automatisch den Typ, von dem er die wenigsten Felder hat.  
Bei Gleichstand: Holz vor Stein vor Korn.

---

## Bauen (v0.2)

Kosten: 2 Holz + 1 Korn.

Spieler würfelt 2x W3 und wählt einen der beiden Typen:

- 1 = Korn
- 2 = Holz
- 3 = Stein

Das neue Feld ist ab der nächsten Runde aktiv.

---

## Upgrade

Kosten: 3 Stein.  
Effekt: Feld produziert bei einer 6 → +2 statt +1.

Nur aktive Felder dürfen upgegradet werden.  
Dorf darf nie upgegradet werden.  
Jedes Feld nur einmal.

---

## Raid

Kosten: 1 Aktion, keine Ressourcen.

Ablauf:
- Spieler würfelt 1W6 pro eigenem Feld + +2 Initiative-Bonus.
- Nachbar würfelt 1W6 pro eigenem Feld.
- Höhere Summe gewinnt. Bei Gleichstand gewinnt der Nachbar.

Spieler-Sieg: Spieler nimmt 2 Ressourcen eines gewählten Typs.  
Ab Runde 5 + Vorsprung >= 5: zusätzlich Feldübernahme.

Spieler-Niederlage: Nachbar nimmt 1 Ressource.  
Ab Runde 5 + Vorsprung >= 5: zusätzlich Feldübernahme.

---

## Omen & Mondrunde

Omen: Runde 3, 7, 11, 15 — Hinweis, keine Wirkung.  
Mondrunde: Runde 4, 8, 12, 16 — echter Konflikt.

Ablauf Mondrunde:
- Beide würfeln 1W6 pro Feld. Kein Initiative-Bonus.
- Bei Gleichstand: nichts.
- Gewinner nimmt 1 Ressource. Bei Vorsprung >= 5: zusätzlich Feldübernahme.

---

## Sieg & Niederlage

Spieler-Sieg (Imperium): 8 eigene Felder.  
Spieler-Sieg (Ausdauer): Holz = 0 UND Stein = 0 UND Korn = 0.  
Spieler-Niederlage: Nachbar erreicht 8 Felder.

---

## Nicht in v0.2

Nachbar-Profile, Sabotage, Stagnation, Heilige Felder,
Fokus-Token, Hex-Alterung, Named Combos, Wonder,
VP-System, Backend, GUI, KI.
