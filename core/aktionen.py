import random

from core.feld import Feld


def bauen(spieler):
    if len(spieler.felder) >= 8:
        print("❌ Du hast bereits 8 Felder. Mehr Felder sind in v0.1 nicht erlaubt.")
        return False

    if spieler.ressourcen["Holz"] < 2 or spieler.ressourcen["Korn"] < 1:
        print("⚠️ Nicht genug Ressourcen. Bauen kostet 2 Holz und 1 Korn.")
        return False

    spieler.ressourcen["Holz"] -= 2
    spieler.ressourcen["Korn"] -= 1

    wurf = random.randint(1, 3)
    if wurf == 1:
        typ = "Korn"
    elif wurf == 2:
        typ = "Holz"
    else:
        typ = "Stein"

    neues_feld = Feld(typ, spezial=False, aktiv_ab_runde=spieler.runde + 1)
    spieler.felder.append(neues_feld)

    print(f"🏗️ Neues Feld gebaut: {typ}. Es wird ab Runde {spieler.runde + 1} aktiv.")
    return True


def upgrade(spieler):
    upgradebare_felder = [
        (index, feld)
        for index, feld in enumerate(spieler.felder, start=1)
        if feld.typ != "Dorf" and not feld.spezial
    ]

    if not upgradebare_felder:
        print("❌ Keine upgradebaren Felder vorhanden.")
        return False

    if spieler.ressourcen["Stein"] < 3:
        print("⚠️ Nicht genug Stein. Upgrade kostet 3 Stein.")
        return False

    print("\n--- Upgrade-Menü ---")
    for index, feld in upgradebare_felder:
        aktiv_text = "aktiv" if feld.aktiv_ab_runde <= spieler.runde else f"aktiv ab Runde {feld.aktiv_ab_runde}"
        print(f"{index}. {feld.typ} | {aktiv_text}")
    print("0. Zurück")

    wahl = input("Welches Feld soll Spezial werden? ")

    if not wahl.isdigit():
        print("❌ Ungültige Eingabe.")
        return False

    feld_index = int(wahl)

    if feld_index == 0:
        return False

    erlaubte_indices = [index for index, _ in upgradebare_felder]
    if feld_index not in erlaubte_indices:
        print("❌ Dieses Feld kann nicht upgegradet werden.")
        return False

    spieler.ressourcen["Stein"] -= 3
    spieler.felder[feld_index - 1].spezial = True
    print(f"⬆️ Feld {feld_index} ({spieler.felder[feld_index - 1].typ}) ist jetzt Spezial.")
    return True


def aussetzen(spieler):
    wurf = random.randint(1, 4)
    print(f"🎲 Aussetzen-Wurf: {wurf}")

    if wurf == 1:
        spieler.ressourcen["Korn"] += 1
        print("🌾 +1 Korn")
    elif wurf == 2:
        spieler.ressourcen["Holz"] += 1
        print("🪵 +1 Holz")
    elif wurf == 3:
        spieler.ressourcen["Stein"] += 1
        print("🪨 +1 Stein")
    else:
        print("Wähle eine Ressource für +2:")
        print("1. Holz")
        print("2. Stein")
        print("3. Korn")
        wahl = input("Ressource: ")

        if wahl == "1":
            spieler.ressourcen["Holz"] += 2
            print("🪵 +2 Holz")
        elif wahl == "2":
            spieler.ressourcen["Stein"] += 2
            print("🪨 +2 Stein")
        elif wahl == "3":
            spieler.ressourcen["Korn"] += 2
            print("🌾 +2 Korn")
        else:
            print("❌ Ungültige Eingabe. Standard: +2 Korn.")
            spieler.ressourcen["Korn"] += 2

    return True
