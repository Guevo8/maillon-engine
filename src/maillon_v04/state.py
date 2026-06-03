from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.maillon_v04.board import Coord, HexBoard


ActorId = Literal["player", "enemy"]
ResourceName = Literal["Holz", "Stein", "Korn"]
FieldType = Literal["Core", "Holz", "Stein", "Korn"]
TunnelEdge = tuple[Coord, Coord]


RESOURCE_NAMES: tuple[ResourceName, ...] = ("Holz", "Stein", "Korn")


@dataclass
class CellState:
    """
    Zustand eines einzelnen Hex-Feldes.

    owner:
        player, enemy oder None.

    field_type:
        Core, Holz, Stein, Korn oder None.

    level:
        Produktions-/Ausbaustufe.
        Für v0.4/v0.5 sind Level 1 und 2 relevant.
        Core Level 2 bedeutet aktuell: Caps wurden erhöht.
        Für v0.6 gilt: collapsed Felder haben level 0.

    active_from_round:
        Runde, ab der das Feld wieder aktiv ist.
        Wird bei Build, Rebuild, Raid-Instabilität und später Repair relevant.

    contested_count:
        Wie oft dieses Feld per Raid umkämpft wurde.
        Dient für Front-Hotspots und Cooldown.

    raid_shield:
        Befestigung / Raid-Schutz eines Nicht-Core-Feldes.
        Jeder gegnerische Raid entfernt zuerst eine Schutzstufe.

    has_tunnel_entrance:
        Sichtbarer Tunneleingang auf der Oberfläche.
        Gibt später Zugang zum verbundenen Tunnelnetz.

    collapsed:
        Kaputter Sonderzustand.
        Collapsed Felder sind nicht normale neutrale Felder und werden später
        nur per repair_build wieder nutzbar gemacht.
    """

    owner: ActorId | None = None
    field_type: FieldType | None = None
    level: int = 1
    active_from_round: int = 1
    contested_count: int = 0
    raid_shield: int = 0
    has_tunnel_entrance: bool = False
    collapsed: bool = False

    @property
    def is_empty(self) -> bool:
        return self.owner is None and self.field_type is None and not self.collapsed

    @property
    def is_core(self) -> bool:
        return self.field_type == "Core"


@dataclass
class ActorState:
    """
    Ressourcen- und Cap-Zustand eines Akteurs.
    """

    resources: dict[ResourceName, int]
    caps: dict[ResourceName, int]

    @classmethod
    def create_default(cls) -> "ActorState":
        return cls(
            resources={
                "Holz": 2,
                "Stein": 0,
                "Korn": 3,
            },
            caps={
                "Holz": 6,
                "Stein": 6,
                "Korn": 6,
            },
        )


@dataclass
class GameState:
    """
    Vollständiger Spielzustand für Maillon.

    Dieses Modul enthält bewusst keine Aktionslogik.
    Regeln, Kosten und Aktionen kommen später in rules.py/actions.py.
    """

    board: HexBoard
    round_index: int
    cells: dict[Coord, CellState]
    player_core: Coord
    enemy_core: Coord
    actors: dict[ActorId, ActorState]
    tunnel_edges: set[TunnelEdge] = field(default_factory=set)

    def actor_state(self, actor: ActorId) -> ActorState:
        return self.actors[actor]

    def cell(self, coord: Coord) -> CellState:
        if coord not in self.cells:
            raise ValueError(f"coord is not on board: {coord}")

        return self.cells[coord]

    def is_active(self, coord: Coord) -> bool:
        return self.cell(coord).active_from_round <= self.round_index

    def owned_cells(self, actor: ActorId) -> list[Coord]:
        return sorted(
            coord
            for coord, cell in self.cells.items()
            if cell.owner == actor
        )

    def active_owned_cells(self, actor: ActorId) -> list[Coord]:
        return sorted(
            coord
            for coord in self.owned_cells(actor)
            if self.is_active(coord)
        )

    def neutral_cells(self) -> list[Coord]:
        return sorted(
            coord
            for coord, cell in self.cells.items()
            if cell.owner is None and not cell.collapsed
        )

    def opponent(self, actor: ActorId) -> ActorId:
        return "enemy" if actor == "player" else "player"

    def controlled_count(self, actor: ActorId) -> int:
        return len(self.owned_cells(actor))

    def non_core_controlled_count(self, actor: ActorId) -> int:
        return sum(
            1
            for coord in self.owned_cells(actor)
            if not self.cell(coord).is_core
        )

    def clone(self) -> "GameState":
        return GameState(
            board=self.board,
            round_index=self.round_index,
            cells={
                coord: CellState(
                    owner=cell.owner,
                    field_type=cell.field_type,
                    level=cell.level,
                    active_from_round=cell.active_from_round,
                    contested_count=cell.contested_count,
                    raid_shield=cell.raid_shield,
                    has_tunnel_entrance=cell.has_tunnel_entrance,
                    collapsed=cell.collapsed,
                )
                for coord, cell in self.cells.items()
            },
            player_core=self.player_core,
            enemy_core=self.enemy_core,
            actors={
                actor: ActorState(
                    resources=dict(actor_state.resources),
                    caps=dict(actor_state.caps),
                )
                for actor, actor_state in self.actors.items()
            },
            tunnel_edges=set(self.tunnel_edges),
        )


def create_initial_state(side_length: int = 5) -> GameState:
    """
    Erstellt den v0.4/v0.5-Startzustand.

    Default:
        side_length 5 = 61 Felder.

    Start:
        player Core links,
        enemy Core rechts,
        je ein Holzfeld einen Schritt Richtung Mitte.
    """

    board = HexBoard.create(side_length)
    player_core, enemy_core = board.opposite_edge_cores()

    r = board.radius

    player_start_wood = (-r + 1, 0)
    enemy_start_wood = (r - 1, 0)

    cells = {coord: CellState() for coord in board.cells}

    cells[player_core] = CellState(
        owner="player",
        field_type="Core",
        level=1,
        active_from_round=1,
    )
    cells[enemy_core] = CellState(
        owner="enemy",
        field_type="Core",
        level=1,
        active_from_round=1,
    )

    cells[player_start_wood] = CellState(
        owner="player",
        field_type="Holz",
        level=1,
        active_from_round=1,
    )
    cells[enemy_start_wood] = CellState(
        owner="enemy",
        field_type="Holz",
        level=1,
        active_from_round=1,
    )

    return GameState(
        board=board,
        round_index=1,
        cells=cells,
        player_core=player_core,
        enemy_core=enemy_core,
        actors={
            "player": ActorState.create_default(),
            "enemy": ActorState.create_default(),
        },
    )
