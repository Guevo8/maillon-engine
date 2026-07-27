import json
import os

from core.spieler import Spieler
from core.nachbar import Nachbar

SAVE_PATH = os.path.join("data", "savegame.json")


def speichern(spieler, nachbar):
    os.makedirs("data", exist_ok=True)

    daten = {
        "version": "0.2",
        "spieler": spieler.als_dict(),
        "nachbar": nachbar.als_dict(),
    }

    with open(SAVE_PATH, "w", encoding="utf-8") as datei:
        json.dump(daten, datei, ensure_ascii=False, indent=2)

    print("\U0001f4be Spiel gespeichert.")


def laden():
    if not os.path.exists(SAVE_PATH):
        print("\u26a0\ufe0f Kein Spielstand gefunden.")
        return None

    with open(SAVE_PATH, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    # v0.1-Save: kein "version"-Key
    if "version" not in daten:
        spieler = Spieler.aus_dict(daten)
        nachbar = Nachbar()
        nachbar.runde = spieler.runde
        print("\U0001f4c2 v0.1-Spielstand geladen. Neuer Nachbar erzeugt.")
        return spieler, nachbar

    # Robustheit: .get() sch\u00fctzt vor halbkorruptem v0.2-Save
    spieler = Spieler.aus_dict(daten.get("spieler", daten))
    nachbar = Nachbar.aus_dict(daten.get("nachbar", {}))
    print("\U0001f4c2 Spielstand geladen.")
    return spieler, nachbar
