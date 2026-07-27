from core.spieler import Spieler
from core.nachbar import Nachbar
from core.phasen import ertrag, aktionen_phase, ueberfluss_check, omen_marker, mondrunde
from core.storage import speichern, laden


def sieg_check(spieler, nachbar):
    if len(spieler.felder) >= 8:
        print("\n\U0001f3c6 Imperium-Sieg! Du besitzt 8 Felder.")
        return True

    if (
        spieler.ressourcen["Holz"] == 0
        and spieler.ressourcen["Stein"] == 0
        and spieler.ressourcen["Korn"] == 0
    ):
        print("\n\U0001f3c6 Ausdauer-Sieg! Holz, Stein und Korn sind gleichzeitig auf 0.")
        return True

    if len(nachbar.felder) >= 8:
        print("\n\U0001f480 Niederlage! Der Nachbar hat 8 Felder erreicht.")
        return True

    return False


def neues_oder_laden():
    print("=== Maillon Pocket v0.2 ===")
    print("[1] Neues Spiel")
    print("[2] Spiel laden")
    wahl = input("Auswahl: ")

    if wahl == "2":
        geladen = laden()
        if geladen is not None:
            return geladen

    print("\U0001f331 Neues Spiel gestartet.")
    return Spieler(), Nachbar()


def rundenloop(spieler, nachbar):
    while True:
        nachbar.runde = spieler.runde

        print("\n" + "=" * 40)
        print(f"Runde {spieler.runde}")
        print("=" * 40)

        spieler.status()
        nachbar.status()

        omen_marker(spieler.runde)

        ertrag(spieler)

        aktionen_phase(spieler, nachbar)

        if sieg_check(spieler, nachbar):
            speichern(spieler, nachbar)
            break

        ertrag(nachbar)

        nachbar.zug_ausfuehren()

        if sieg_check(spieler, nachbar):
            speichern(spieler, nachbar)
            break

        ueberfluss_check(spieler)
        ueberfluss_check(nachbar)

        mondrunde(spieler, nachbar, spieler.runde)

        if sieg_check(spieler, nachbar):
            speichern(spieler, nachbar)
            break

        # Runde erst hochz\u00e4hlen, dann speichern
        spieler.runde += 1
        nachbar.runde = spieler.runde
        speichern(spieler, nachbar)


def main():
    ergebnis = neues_oder_laden()
    spieler, nachbar = ergebnis

    if sieg_check(spieler, nachbar):
        speichern(spieler, nachbar)
        return

    rundenloop(spieler, nachbar)


if __name__ == "__main__":
    main()
