# Maillon v0.6 Terminal Tunnel Playtest Report

Stand: 04-06-2026  
Branch: `v0.6-tunnel-prototype`  
Playtest block: `7N.1`  
Scope: Manual terminal playtest after tunnel UI integration and tunnel rule tightening.

---

## 1. Kurzfazit

Der manuelle Terminal-Playtest bestätigt, dass das v0.6-Tunnelsystem im echten Spielablauf funktioniert.

Bestätigt wurden:

```text
- dynamisches Terminalmenü
- Status/Karte kombiniert
- Tunnelmarker auf der Karte
- Tunneleingang als `tu`
- Untergrabung als `u`
- Tunnel Pressure sichtbar
- Tunnel Extend auf besetzte Felder
- keine neutralen Extend-Ziele mehr
- Tunnel Raid
- Collapse
- Repair Build
- gemeinsamer Netzwerkzugang
```

Der Stand ist damit spielbar genug, um das Tunnelsystem als technischen Prototypen zu dokumentieren.

---

## 2. Wichtigster Playtest-Befund

Die Kernmechanik funktioniert:

```text
Wer Zugang zum Tunnelnetz hat, kann das bestehende Tunnelnetz nutzen.
```

Das wurde im Playtest praktisch sichtbar.

Diese Regel ist nicht nur ein Nebeneffekt, sondern eine gewollte Designentscheidung:

```text
Tunnelkanten sind nicht owned.
Zugang entsteht über eigene aktive Tunneleingänge.
Ein verbundenes Tunnelnetz kann strategisch von beiden Seiten genutzt werden,
wenn Zugang besteht.
```

Das ist für spätere Botlogik sehr wichtig, weil ein Bot nicht nur eigene Tunnel bauen muss, sondern