from core.aktionen import bauen, upgrade, aussetzen, aktionen_phase
from core import konflikt


def ertrag(akteur):
    label = "Nachbar" if akteur.__class__.__name__ == "Nachbar" else "Spieler"
    print(f"\n=== Ertrag ({label}) ===")
    gesamt_ertrag = {"Holz": 0, "Stein": 0, "Korn": 0}

    for feld in akteur.felder:
        ergebnis = feld.wuerfle_ertrag(akteur.runde)
        if ergebnis is None:
            continue

        rohstoff, menge = ergebnis
        akteur.ressourcen[rohstoff] += menge
        gesamt_ertrag[rohstoff] += menge
        print(f"  \u2705 {feld.typ}-Feld erzeugt +{menge} {rohstoff}.")

    if all(menge == 0 for menge in gesamt_ertrag.values()):
        print("  Kein Ertrag in dieser Runde.")

    return gesamt_ertrag


def ueberfluss_check(akteur):
    label = "Nachbar" if akteur.__class__.__name__ == "Nachbar" else "Spieler"
    print(f"\n=== \u00dcberfluss-Check ({label}) ===")
    hatte_ueberfluss = False

    for rohstoff, bestand in list(akteur.ressourcen.items()):
        if bestand > 5:
            neuer_bestand = max(5, bestand - 1)
            akteur.ressourcen[rohstoff] = neuer_bestand
            hatte_ueberfluss = True
            print(f"  \u26a0\ufe0f {rohstoff}: {bestand} > 5. \u00dcberfluss verf\u00e4llt auf {neuer_bestand}.")

    if not hatte_ueberfluss:
        print("  Kein \u00dcberfluss.")


def omen_marker(runde):
    if runde % 4 == 3:
        print("\n\U0001f318 Omen: Die Mondrunde naht. Bereite dich vor.")


def mondrunde(spieler, nachbar, runde):
    if runde % 4 == 0:
        konflikt.mondrunde_konflikt(spieler, nachbar)
