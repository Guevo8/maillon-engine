from core.spieler import Spieler
from core.phasen import ertrag, aktionen_phase, ueberfluss_check, mondrunde_marker
from core.storage import speichern, laden


def sieg_check(spieler):
    if len(spieler.felder) >= 8:
        print("\n🏆 Imperium-Sieg! Du besitzt 8 Felder.")
        return True

    if (
        spieler.ressourcen["Holz"] == 0
        and spieler.ressourcen["Stein"] == 0
        and spieler.ressourcen["Korn"] == 0
    ):
        print("\n🏆 Ausdauer-Sieg! Holz, Stein und Korn sind gleichzeitig auf 0.")
        return True

    return False


def neues_oder_laden():
    print("=== Maillon Pocket Solo v0.1 ===")
    print("[1] Neues Spiel")
    print("[2] Spiel laden")
    wahl = input("Auswahl: ")

    if wahl == "2":
        spieler = laden()
        if spieler is not None:
            return spieler

    print("🌱 Neues Spiel gestartet.")
    return Spieler()


def rundenloop(spieler):
    while True:
        print("\n" + "=" * 40)
        print(f"Runde {spieler.runde}")
        print("=" * 40)

        spieler.status()

        ertrag(spieler)
        aktionen_phase(spieler)
        ueberfluss_check(spieler)
        mondrunde_marker(spieler.runde)

        if sieg_check(spieler):
            speichern(spieler)
            break

        speichern(spieler)
        spieler.runde += 1


def main():
    spieler = neues_oder_laden()
    rundenloop(spieler)


if __name__ == "__main__":
    main()
