import random


def wuerfel_summe(akteur):
    wuerfe = [random.randint(1, 6) for _ in akteur.felder]
    print(f"  W\u00fcrfe ({len(wuerfe)} Felder): {wuerfe}")
    return sum(wuerfe)


def _ressource_mit_hoechstem_bestand(akteur):
    prioritaet = ["Holz", "Stein", "Korn"]
    return max(prioritaet, key=lambda r: akteur.ressourcen[r])


def ressource_stehlen(gewinner, verlierer, menge, ressource):
    verfuegbar = verlierer.ressourcen.get(ressource, 0)
    if verfuegbar == 0:
        for r in ["Holz", "Stein", "Korn"]:
            if verlierer.ressourcen[r] > 0:
                ressource = r
                verfuegbar = verlierer.ressourcen[r]
                break
        else:
            print("  Verlierer hat keine Ressourcen. Nichts gestohlen.")
            return

    gestohlen = min(menge, verfuegbar)
    verlierer.ressourcen[ressource] -= gestohlen
    gewinner.ressourcen[ressource] += gestohlen
    print(f"  \U0001f4b8 {gestohlen}x {ressource} gestohlen.")


def neuestes_nicht_dorf_feld_entnehmen(verlierer):
    for i in range(len(verlierer.felder) - 1, -1, -1):
        if verlierer.felder[i].typ != "Dorf":
            return verlierer.felder.pop(i)
    return None


def feld_uebernehmen(gewinner, verlierer, runde):
    feld = neuestes_nicht_dorf_feld_entnehmen(verlierer)
    if feld is None:
        print("  Kein \u00fcbernehmbares Feld beim Verlierer.")
        return

    feld.aktiv_ab_runde = max(feld.aktiv_ab_runde, runde + 1)
    gewinner.felder.append(feld)
    print(f"  \U0001f3f3\ufe0f  Feld \u00fcbernommen: {feld.typ} (aktiv ab Runde {feld.aktiv_ab_runde}).")


def raid(spieler, nachbar):
    print("\n\u2694\ufe0f  === RAID ===")

    print(f"Spieler w\u00fcrfelt ({len(spieler.felder)} Felder):")
    spieler_summe = wuerfel_summe(spieler) + 2
    print(f"  Spieler-Summe (inkl. +2 Initiative): {spieler_summe}")

    print(f"Nachbar w\u00fcrfelt ({len(nachbar.felder)} Felder):")
    nachbar_summe = wuerfel_summe(nachbar)
    print(f"  Nachbar-Summe: {nachbar_summe}")

    vorsprung = abs(spieler_summe - nachbar_summe)

    if spieler_summe > nachbar_summe:
        print(f"\u2705 Spieler gewinnt den Raid! (Vorsprung: {vorsprung})")

        print("Welche Ressource willst du stehlen?")
        print("1. Holz")
        print("2. Stein")
        print("3. Korn")
        wahl = input("Ressource (1-3): ").strip()
        ressource_map = {"1": "Holz", "2": "Stein", "3": "Korn"}
        gewaehlte_ressource = ressource_map.get(
            wahl, _ressource_mit_hoechstem_bestand(nachbar)
        )

        ressource_stehlen(spieler, nachbar, 2, gewaehlte_ressource)

        if vorsprung >= 5 and spieler.runde >= 5:
            print("  \U0001f4a5 Gro\u00dfer Sieg! Feld\u00fcbernahme:")
            feld_uebernehmen(spieler, nachbar, spieler.runde)

    else:
        print(f"\u274c Spieler verliert den Raid. (Vorsprung Nachbar: {vorsprung})")

        ressource = _ressource_mit_hoechstem_bestand(spieler)
        ressource_stehlen(nachbar, spieler, 1, ressource)

        if vorsprung >= 5 and spieler.runde >= 5:
            print("  \U0001f4a5 Vernichtende Niederlage! Nachbar \u00fcbernimmt ein Feld:")
            feld_uebernehmen(nachbar, spieler, spieler.runde)


def mondrunde_konflikt(spieler, nachbar):
    print("\n\U0001f319 === MONDRUNDE ===")

    print(f"Spieler w\u00fcrfelt ({len(spieler.felder)} Felder):")
    spieler_summe = wuerfel_summe(spieler)
    print(f"  Spieler-Summe: {spieler_summe}")

    print(f"Nachbar w\u00fcrfelt ({len(nachbar.felder)} Felder):")
    nachbar_summe = wuerfel_summe(nachbar)
    print(f"  Nachbar-Summe: {nachbar_summe}")

    vorsprung = abs(spieler_summe - nachbar_summe)

    if spieler_summe > nachbar_summe:
        print(f"\u2705 Spieler gewinnt die Mondrunde! (Vorsprung: {vorsprung})")
        ressource = _ressource_mit_hoechstem_bestand(nachbar)
        ressource_stehlen(spieler, nachbar, 1, ressource)

        if vorsprung >= 5:
            print("  \U0001f4a5 Dominanter Sieg! Feld\u00fcbernahme:")
            feld_uebernehmen(spieler, nachbar, spieler.runde)

    elif nachbar_summe > spieler_summe:
        print(f"\u274c Nachbar gewinnt die Mondrunde. (Vorsprung: {vorsprung})")
        ressource = _ressource_mit_hoechstem_bestand(spieler)
        ressource_stehlen(nachbar, spieler, 1, ressource)

        if vorsprung >= 5:
            print("  \U0001f4a5 Nachbar \u00fcbernimmt ein Feld:")
            feld_uebernehmen(nachbar, spieler, spieler.runde)

    else:
        print("  Gleichstand \u2014 nichts passiert.")
