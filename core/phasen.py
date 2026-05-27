from core.aktionen import bauen, upgrade, aussetzen


def ertrag(spieler):
    print("\n=== Phase 1: Ertrag ===")
    gesamt_ertrag = {
        "Holz": 0,
        "Stein": 0,
        "Korn": 0,
    }

    for feld in spieler.felder:
        ergebnis = feld.wuerfle_ertrag(spieler.runde)
        if ergebnis is None:
            continue

        rohstoff, menge = ergebnis
        spieler.ressourcen[rohstoff] += menge
        gesamt_ertrag[rohstoff] += menge
        print(f"✅ {feld.typ}-Feld erzeugt +{menge} {rohstoff}.")

    if all(menge == 0 for menge in gesamt_ertrag.values()):
        print("Kein Ertrag in dieser Runde.")

    return gesamt_ertrag


def aktionen_phase(spieler):
    print("\n=== Phase 2: Aktionen ===")
    verbleibende_aktionen = 2

    while verbleibende_aktionen > 0:
        print(f"\nVerbleibende Aktionen: {verbleibende_aktionen}")
        print("[1] Bauen")
        print("[2] Upgrade")
        print("[3] Aussetzen (verbraucht beide Aktionen)")
        print("[4] Status anzeigen")
        wahl = input("Wähle eine Aktion: ")

        if wahl == "1":
            if bauen(spieler):
                verbleibende_aktionen -= 1
        elif wahl == "2":
            if upgrade(spieler):
                verbleibende_aktionen -= 1
        elif wahl == "3":
            aussetzen(spieler)
            verbleibende_aktionen = 0
        elif wahl == "4":
            spieler.status()
        else:
            print("❌ Ungültige Eingabe.")


def ueberfluss_check(spieler):
    print("\n=== Phase 3: Überfluss-Check ===")
    hatte_ueberfluss = False

    for rohstoff, bestand in list(spieler.ressourcen.items()):
        if bestand > 5:
            neuer_bestand = max(5, bestand - 1)
            spieler.ressourcen[rohstoff] = neuer_bestand
            hatte_ueberfluss = True
            print(f"⚠️ {rohstoff}: {bestand} > 5. Überfluss verfällt auf {neuer_bestand}.")

    if not hatte_ueberfluss:
        print("Kein Überfluss.")


def mondrunde_marker(runde):
    if runde % 4 == 0:
        print("\n🌙 Mondrunde — Solo v0.1: kein Konflikt. Ab v0.2 wird hier ein Nachbar simuliert.")
