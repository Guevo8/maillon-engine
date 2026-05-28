import random

from core.feld import Feld


class Nachbar:
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
        print("\n\U0001f441\ufe0f  Nachbar-Status")
        print(f"  Felder: {len(self.felder)} / 8")
        for name, menge in self.ressourcen.items():
            print(f"  {name}: {menge}")
        felder_bis_sieg = 8 - len(self.felder)
        if felder_bis_sieg <= 3:
            print(f"  \u26a0\ufe0f  Warnung: Noch {felder_bis_sieg} Felder bis Nachbar-Sieg!")

    def kann_bauen(self):
        return (
            self.ressourcen["Holz"] >= 2
            and self.ressourcen["Korn"] >= 1
            and len(self.felder) < 8
        )

    def _waehlt_feldtyp(self, optionen):
        prioritaet = ["Holz", "Stein", "Korn"]
        feld_zaehler = {"Holz": 0, "Stein": 0, "Korn": 0}
        for feld in self.felder:
            if feld.typ in feld_zaehler:
                feld_zaehler[feld.typ] += 1

        beste_option = None
        bester_zaehler = None
        for typ in prioritaet:
            if typ in optionen:
                if bester_zaehler is None or feld_zaehler[typ] < bester_zaehler:
                    beste_option = typ
                    bester_zaehler = feld_zaehler[typ]
        return beste_option

    def bauen(self):
        if not self.kann_bauen():
            return False

        self.ressourcen["Holz"] -= 2
        self.ressourcen["Korn"] -= 1

        wurf1 = random.randint(1, 3)
        wurf2 = random.randint(1, 3)

        typen_tabelle = {1: "Korn", 2: "Holz", 3: "Stein"}
        option1 = typen_tabelle[wurf1]
        option2 = typen_tabelle[wurf2]

        optionen = {option1, option2}
        gewaehlter_typ = self._waehlt_feldtyp(optionen)

        neues_feld = Feld(gewaehlter_typ, spezial=False, aktiv_ab_runde=self.runde + 1)
        self.felder.append(neues_feld)

        print(
            f"\U0001f3d7\ufe0f  Nachbar baut: {gewaehlter_typ}-Feld "
            f"(W\u00fcrfe: {option1}/{option2}). "
            f"Aktiv ab Runde {self.runde + 1}."
        )
        return True

    def aussetzen(self):
        wurf = random.randint(1, 4)
        print(f"\U0001f3b2 Nachbar setzt aus (Wurf: {wurf})")

        if wurf == 1:
            self.ressourcen["Korn"] += 1
            print("  \U0001f33e Nachbar +1 Korn")
        elif wurf == 2:
            self.ressourcen["Holz"] += 1
            print("  \U0001fab5 Nachbar +1 Holz")
        elif wurf == 3:
            self.ressourcen["Stein"] += 1
            print("  \U0001faa8 Nachbar +1 Stein")
        else:
            prioritaet = ["Holz", "Stein", "Korn"]
            ziel = min(prioritaet, key=lambda r: self.ressourcen[r])
            self.ressourcen[ziel] += 2
            print(f"  \u2728 Nachbar +2 {ziel}")

    def zug_ausfuehren(self):
        print("\n--- Nachbar-Zug ---")
        if self.kann_bauen():
            self.bauen()
        else:
            self.aussetzen()

    def als_dict(self):
        return {
            "ressourcen": self.ressourcen,
            "felder": [feld.als_dict() for feld in self.felder],
            "runde": self.runde,
        }

    @classmethod
    def aus_dict(cls, daten):
        nachbar = cls()
        nachbar.ressourcen = daten.get(
            "ressourcen",
            {"Holz": 2, "Stein": 1, "Korn": 1},
        )
        nachbar.felder = [Feld.aus_dict(fd) for fd in daten.get("felder", [])]
        nachbar.runde = daten.get("runde", 1)

        if not nachbar.felder:
            nachbar.felder = [
                Feld("Dorf", aktiv_ab_runde=1),
                Feld("Holz", aktiv_ab_runde=1),
                Feld("Stein", aktiv_ab_runde=1),
                Feld("Korn", aktiv_ab_runde=1),
            ]

        return nachbar
