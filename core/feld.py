import random


class Feld:
    def __init__(self, typ, spezial=False, aktiv_ab_runde=1):
        self.typ = typ
        self.spezial = spezial
        self.aktiv_ab_runde = aktiv_ab_runde

    def wuerfle_ertrag(self, aktuelle_runde):
        if self.typ == "Dorf":
            return None

        if self.aktiv_ab_runde > aktuelle_runde:
            return None

        wurf = random.randint(1, 6)
        print(f"🎲 Feld {self.typ}: Wurf {wurf}")

        if wurf != 6:
            return None

        menge = 2 if self.spezial else 1
        return self.typ, menge

    def als_dict(self):
        return {
            "typ": self.typ,
            "spezial": self.spezial,
            "aktiv_ab_runde": self.aktiv_ab_runde,
        }

    @classmethod
    def aus_dict(cls, daten):
        return cls(
            typ=daten["typ"],
            spezial=daten.get("spezial", False),
            aktiv_ab_runde=daten.get("aktiv_ab_runde", 1),
        )
