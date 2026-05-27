from core.feld import Feld


class Spieler:
    def __init__(self):
        self.ressourcen = {
            "Holz": 2,
            "Stein": 1,
            "Korn": 1,
        }
        self.felder = [
            Feld("Dorf", aktiv_ab_runde=1),
            Feld("Holz", aktiv_ab_runde=1),
            Feld("Stein", aktiv_ab_runde=1),
            Feld("Korn", aktiv_ab_runde=1),
        ]
        self.runde = 1

    def status(self):
        print("\n📊 Status")
        print(f"Runde: {self.runde}")
        print("\nRessourcen:")
        for name, menge in self.ressourcen.items():
            print(f" - {name}: {menge}")

        print("\nFelder:")
        for index, feld in enumerate(self.felder, start=1):
            spezial_text = "Spezial" if feld.spezial else "Normal"
            aktiv_text = "aktiv" if feld.aktiv_ab_runde <= self.runde else f"aktiv ab Runde {feld.aktiv_ab_runde}"
            print(f" {index}. {feld.typ} | {spezial_text} | {aktiv_text}")

    def als_dict(self):
        return {
            "ressourcen": self.ressourcen,
            "felder": [feld.als_dict() for feld in self.felder],
            "runde": self.runde,
        }

    @classmethod
    def aus_dict(cls, daten):
        spieler = cls()
        spieler.ressourcen = daten.get(
            "ressourcen",
            {"Holz": 2, "Stein": 1, "Korn": 1},
        )
        spieler.felder = [Feld.aus_dict(feld_daten) for feld_daten in daten.get("felder", [])]
        spieler.runde = daten.get("runde", 1)

        if not spieler.felder:
            spieler.felder = [
                Feld("Dorf", aktiv_ab_runde=1),
                Feld("Holz", aktiv_ab_runde=1),
                Feld("Stein", aktiv_ab_runde=1),
                Feld("Korn", aktiv_ab_runde=1),
            ]

        return spieler
