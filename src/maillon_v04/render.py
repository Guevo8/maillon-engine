from __future__ import annotations

from src.maillon_v04.board import Coord
from src.maillon_v04.state import GameState


def field_letter(field_type: str | None) -> str:
    if field_type == "Core":
        return "C"

    if field_type == "Holz":
        return "H"

    if field_type == "Stein":
        return "S"

    if field_type == "Korn":
        return "K"

    return "."


def cell_token(state: GameState, coord: Coord) -> str:
    cell = state.cell(coord)

    if cell.owner is None:
        return ".."

    owner = "P" if cell.owner == "player" else "E"
    field = field_letter(cell.field_type)

    token = owner + field

    # Instabile Felder werden klein geschrieben.
    # Beispiel: pK = Player-Kornfeld, aber aktuell instabil.
    if not state.is_active(coord):
        token = token.lower()

    return token


def render_board(state: GameState) -> str:
    """
    Gibt eine kompakte axiale Hex-Board-Ansicht zurück.

    Legende:
        P = Player
        E = Enemy
        C = Core
        H = Holz
        S = Stein
        K = Korn
        .. = neutral

    Kleinbuchstaben bedeuten:
        Feld ist aktuell instabil / nicht aktiv.
    """

    radius = state.board.radius
    lines: list[str] = []

    lines.append("BOARD")
    lines.append("-" * 72)

    for r in range(-radius, radius + 1):
        row_coords = [
            coord
            for coord in state.board.cells
            if coord[1] == r
        ]
        row_coords.sort(key=lambda coord: coord[0])

        indent = "  " * abs(r)
        tokens = "  ".join(cell_token(state, coord) for coord in row_coords)

        lines.append(f"r={r:>2} {indent}{tokens}")

    return "\n".join(lines)


def render_legend() -> str:
    lines = [
        "LEGENDE",
        "- P = Player, E = Enemy",
        "- C = Core, H = Holz, S = Stein, K = Korn",
        "- .. = neutral",
        "- Kleinbuchstaben, z. B. pK/eH = instabil / nicht aktiv",
    ]

    return "\n".join(lines)


def render_board_with_legend(state: GameState) -> str:
    return render_board(state) + "\n\n" + render_legend()
