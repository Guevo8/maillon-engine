import json
import os

from core.spieler import Spieler

SAVE_PATH = os.path.join("data", "savegame.json")


def speichern(spieler):
    os.makedirs("data", exist_ok=True)

    with open(SAVE_PATH, "w", encoding="utf-8") as datei:
        json.dump(spieler.als_dict(), datei, ensure_ascii=False, indent=2)

    print("💾 Spiel gespeichert.")


def laden():
    if not os.path.exists(SAVE_PATH):
        print("⚠️ Kein Spielstand gefunden.")
        return None

    with open(SAVE_PATH, "r", encoding="utf-8") as datei:
        daten = json.load(datei)

    spieler = Spieler.aus_dict(daten)
    print("📂 Spielstand geladen.")
    return spieler
