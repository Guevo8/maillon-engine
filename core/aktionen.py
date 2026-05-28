import random

from core.feld import Feld


def _terminalzustand_erreicht(spieler, nachbar):
    if len(spieler.felder) >= 8:
        return True
    if len(nachbar.felder) >= 8:
        return True
    if (
        spieler.ressourcen["Holz"] == 0
        and spieler.ressourcen["Stein"] == 0
        and spieler.ressourcen["Korn"] == 0
    ):
        return True
    return False


def bauen(spieler):
    if len(spieler.felder) >= 8:
        print("\u274c Du hast bereits 8 Felder. Mehr Felder sind nicht erlaubt.")
        return False

    if spieler.ressourcen["Holz"] < 2 or spieler.ressourcen["Korn"] < 1:
        print("\u26a0\ufe0f Nicht genug Ressourcen. Bauen kostet 2 Holz und 1 Korn.")
        return False

    spieler.ressourcen["Holz"] -= 2
    spieler.ressourcen["Korn"] -= 1

    typen_tabelle = {1: "Korn", 2: "Holz", 3: "Stein"}
    wurf1 = random.randint(1, 3)
    wurf2 = random.randint(1, 3)
    option1 = typen_tabelle[wurf1]
    option2 = typen_tabelle[wurf2]

    if option1 == option2:
        typ = option1
        print(f"\U0001f3b2 Beide W\u00fcrfe ergeben {typ}. Es wird {typ} gebaut.")
    else:
        print(f"\nDu hast diese Bauoptionen:")
        print(f"1. {option1}")
        print(f"2. {option2}")
        wahl = input("Welche Option willst du bauen? (1/2): ").strip()
        if wahl == "2":
            typ = option2
        else:
            typ = option1

    neues_feld = Feld(typ, spezial=False, aktiv_ab_runde=spieler.runde + 1)
    spieler.felder.append(neues_feld)

    print(f"\U0001f3d7\ufe0f Neues Feld gebaut: {typ}. Es wird ab Runde {spieler.runde + 1} aktiv.")
    return True


def upgrade(spieler):
    upgradebare_felder = [
        (index, feld)
        for index, feld in enumerate(spieler.felder, start=1)
        if feld.typ != "Dorf"
        and not feld.spezial
        and feld.aktiv_ab_runde <= spieler.runde
    ]

    if not upgradebare_felder:
        print("\u274c Keine upgradebaren Felder vorhanden.")
        return False

    if spieler.ressourcen["Stein"] < 3:
        print("\u26a0\ufe0f Nicht genug Stein. Upgrade kostet 3 Stein.")
        return False

    print("\n--- Upgrade-Men\u00fc ---")
    for index, feld in upgradebare_felder:
        print(f"{index}. {feld.typ} | aktiv")
    print("0. Zur\u00fcck")

    wahl = input("Welches Feld soll Spezial werden? ")

    if not wahl.isdigit():
        print("\u274c Ung\u00fcltige Eingabe.")
        return False

    feld_index = int(wahl)

    if feld_index == 0:
        return False

    erlaubte_indices = [index for index, _ in upgradebare_felder]
    if feld_index not in erlaubte_indices:
        print("\u274c Dieses Feld kann nicht upgegradet werden.")
        return False

    spieler.ressourcen["Stein"] -= 3
    spieler.felder[feld_index - 1].spezial = True
    print(f"\u2b06\ufe0f Feld {feld_index} ({spieler.felder[feld_index - 1].typ}) ist jetzt Spezial.")
    return True


def aussetzen(spieler):
    wurf = random.randint(1, 4)
    print(f"\U0001f3b2 Aussetzen-Wurf: {wurf}")

    if wurf == 1:
        spieler.ressourcen["Korn"] += 1
        print("\U0001f33e +1 Korn")
    elif wurf == 2:
        spieler.ressourcen["Holz"] += 1
        print("\U0001fab5 +1 Holz")
    elif wurf == 3:
        spieler.ressourcen["Stein"] += 1
        print("\U0001faa8 +1 Stein")
    else:
        print("W\u00e4hle eine Ressource f\u00fcr +2:")
        print("1. Holz")
        print("2. Stein")
        print("3. Korn")
        wahl = input("Ressource: ")

        if wahl == "1":
            spieler.ressourcen["Holz"] += 2
            print("\U0001fab5 +2 Holz")
        elif wahl == "2":
            spieler.ressourcen["Stein"] += 2
            print("\U0001faa8 +2 Stein")
        elif wahl == "3":
            spieler.ressourcen["Korn"] += 2
            print("\U0001f33e +2 Korn")
        else:
            print("\u274c Ung\u00fcltige Eingabe. Standard: +2 Korn.")
            spieler.ressourcen["Korn"] += 2

    return True


def aktionen_phase(spieler, nachbar):
    from core import konflikt

    print("\n=== Phase 2: Aktionen ===")
    verbleibende_aktionen = 2

    while verbleibende_aktionen > 0:
        print(f"\nVerbleibende Aktionen: {verbleibende_aktionen}")
        print("[1] Bauen")
        print("[2] Upgrade")
        print("[3] Aussetzen (verbraucht beide Aktionen)")
        print("[4] Raid")
        print("[5] Status anzeigen")
        wahl = input("W\u00e4hle eine Aktion: ")

        if wahl == "1":
            if bauen(spieler):
                verbleibende_aktionen -= 1
                if _terminalzustand_erreicht(spieler, nachbar):
                    return
        elif wahl == "2":
            if upgrade(spieler):
                verbleibende_aktionen -= 1
                if _terminalzustand_erreicht(spieler, nachbar):
                    return
        elif wahl == "3":
            aussetzen(spieler)
            verbleibende_aktionen = 0
            if _terminalzustand_erreicht(spieler, nachbar):
                return
        elif wahl == "4":
            konflikt.raid(spieler, nachbar)
            verbleibende_aktionen -= 1
            if _terminalzustand_erreicht(spieler, nachbar):
                return
        elif wahl == "5":
            spieler.status()
            nachbar.status()
        else:
            print("\u274c Ung\u00fcltige Eingabe.")
