"""What it costs to step onto a terrain (D72, owner ruling 2026-10-14).

Each terrain in content (`data/content/world/terrain.yaml`) declares `move_cost_multiplier`; this module is the one place code reads it. There is no table of
terrain names in code (D56) and no silent default: a terrain id the catalog does not know raises `UnknownTerrainError` (at compile, for the whole map, and at
lookup for a single tile). A tile carries a catalog id exactly (`plain`, not `PLAIN`), so the match is exact.

The costs come from the loaded content catalog, held as a process-level cache like `get_faction_semantics_service`. It holds content, never world state, so two
worlds compiled in one process read the same declared costs and cannot read each other's; `configure_terrain_costs` installs a small catalog for a test and
`reset_terrain_costs` clears it.
"""
from __future__ import annotations

from typing import Dict, Iterable, Mapping, Optional

from src.content.paths import ContentPathConfig
from src.content.repository import CatalogRepository

# The terrain a compiled map is filled with before any region paints it: a catalog id (the `plain` entry), never a literal in the compiler.
DEFAULT_TERRAIN_ID = "plain"

_costs_cache: Optional[Dict[str, float]] = None


class UnknownTerrainError(ValueError):
    """A terrain id that is not in the content catalog (so it has no declared move cost)."""


def _load_default_costs() -> Dict[str, float]:
    repo = CatalogRepository(ContentPathConfig().content_root)
    repo.load_all()
    return _costs_of(repo)


def _costs_of(repo: CatalogRepository) -> Dict[str, float]:
    return {terrain_id: float(definition.move_cost_multiplier) for terrain_id, definition in repo.terrain.items()}


def _costs() -> Mapping[str, float]:
    global _costs_cache
    if _costs_cache is None:
        _costs_cache = _load_default_costs()
    return _costs_cache


def configure_terrain_costs(repo: CatalogRepository) -> None:
    """Install the costs of `repo` (a test catalog). Pair with `reset_terrain_costs()` in teardown."""
    global _costs_cache
    _costs_cache = _costs_of(repo)


def reset_terrain_costs() -> None:
    """Clear the cache so the next lookup reads the default content catalog."""
    global _costs_cache
    _costs_cache = None


def terrain_cost(terrain_id: str) -> float:
    """The declared move cost of the terrain with this catalog id."""
    costs = _costs()
    try:
        return costs[terrain_id]
    except KeyError:
        raise UnknownTerrainError(f"terrain {terrain_id!r} is not in the content catalog (known: {sorted(costs)}); a terrain needs a declared move_cost_multiplier") from None


def validate_terrain_ids(terrain_ids: Iterable[str]) -> None:
    """Raise `UnknownTerrainError` naming every id in `terrain_ids` the catalog does not know (the compile-time content check)."""
    costs = _costs()
    unknown = sorted({t for t in terrain_ids if t not in costs})
    if unknown:
        raise UnknownTerrainError(f"terrain ids not in the content catalog: {unknown} (known: {sorted(costs)}); declare each in data/content/world/terrain.yaml with a move_cost_multiplier")
