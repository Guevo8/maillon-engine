"""Maillon v0.6 tunnel default configuration.

This module is the single source of truth for tunnel-related default
constants. It intentionally has no dependency on GameState, ResourceName
or rule modules, so it can be imported safely from tunnel modules.
"""

from __future__ import annotations

from typing import Final


# Collapse
DEFAULT_COLLAPSE_THRESHOLD: Final[int] = 4


# Action costs
DEFAULT_TUNNEL_ENTRANCE_HOLZ: Final[int] = 1
DEFAULT_TUNNEL_ENTRANCE_STEIN: Final[int] = 2

DEFAULT_TUNNEL_EXTEND_HOLZ: Final[int] = 1
DEFAULT_TUNNEL_EXTEND_STEIN: Final[int] = 1

DEFAULT_TUNNEL_RAID_KORN: Final[int] = 3

DEFAULT_REPAIR_BUILD_HOLZ: Final[int] = 2
DEFAULT_REPAIR_BUILD_STEIN: Final[int] = 2
