from __future__ import annotations

from dataclasses import dataclass


Coord = tuple[int, int]

# Axiale Hex-Koordinaten: (q, r)
# Der dritte Cube-Wert ergibt sich implizit: s = -q - r
DIRECTIONS: tuple[Coord, ...] = (
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
)


@dataclass(frozen=True)
class HexBoard:
    """
    Reguläres Hex-Board für Maillon v0.4.

    side_length:
        Seitenlänge des Hexagons.
        side_length 4 = 37 Felder.
        side_length 5 = 61 Felder.

    radius:
        Axialer Radius.
        radius = side_length - 1.
    """

    side_length: int
    radius: int
    cells: tuple[Coord, ...]

    @classmethod
    def create(cls, side_length: int) -> "HexBoard":
        if side_length < 2:
            raise ValueError("side_length must be >= 2")

        radius = side_length - 1
        cells: list[Coord] = []

        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                s = -q - r

                if max(abs(q), abs(r), abs(s)) <= radius:
                    cells.append((q, r))

        return cls(
            side_length=side_length,
            radius=radius,
            cells=tuple(sorted(cells)),
        )

    @property
    def size(self) -> int:
        return len(self.cells)

    def contains(self, coord: Coord) -> bool:
        return coord in self.cells

    def neighbors(self, coord: Coord) -> tuple[Coord, ...]:
        if not self.contains(coord):
            raise ValueError(f"coord is not on board: {coord}")

        cell_set = set(self.cells)
        found: list[Coord] = []

        for dq, dr in DIRECTIONS:
            candidate = (coord[0] + dq, coord[1] + dr)

            if candidate in cell_set:
                found.append(candidate)

        return tuple(sorted(found))

    @staticmethod
    def distance(a: Coord, b: Coord) -> int:
        aq, ar = a
        bq, br = b

        # Axial -> Cube
        ax = aq
        az = ar
        ay = -ax - az

        bx = bq
        bz = br
        by = -bx - bz

        return max(
            abs(ax - bx),
            abs(ay - by),
            abs(az - bz),
        )

    def opposite_edge_cores(self) -> tuple[Coord, Coord]:
        """
        Standard-Startpunkte für 2 Spieler:
        gegenüberliegende Randpositionen auf der q-Achse.
        """

        return (-self.radius, 0), (self.radius, 0)
