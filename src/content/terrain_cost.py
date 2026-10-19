"""What a terrain declares in content: the cost of a step onto it (D72, owner ruling 2026-10-14), and whether it gives cover and whether it is high ground.

Each terrain in content (`data/content/world/terrain.yaml`) declares `move_cost_multiplier`, `gives_cover` and `high_ground`; this module is the one place code reads them. There is no table of
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
from src.content.schema import TerrainDefinition

# The terrain a compiled map is filled with before any region paints it: a catalog id (the `plain` entry), never a literal in the compiler.
DEFAULT_TERRAIN_ID = "plain"

_terrain_cache: Optional[Dict[str, TerrainDefinition]] = None


class UnknownTerrainError(ValueError):
    """A terrain id that is not in the content catalog (so it has no declared move cost)."""


def _load_default_terrain() -> Dict[str, TerrainDefinition]:
    repo = CatalogRepository(ContentPathConfig().content_root)
    repo.load_all()
    return _terrain_of(repo)


def _terrain_of(repo: CatalogRepository) -> Dict[str, TerrainDefinition]:
    return dict(repo.terrain.items())


def _terrain() -> Mapping[str, TerrainDefinition]:
    global _terrain_cache
    if _terrain_cache is None:
        _terrain_cache = _load_default_terrain()
    return _terrain_cache


def configure_terrain_costs(repo: CatalogRepository) -> None:
    """Install the terrain of `repo` (a test catalog). Pair with `reset_terrain_costs()` in teardown."""
    global _terrain_cache
    _terrain_cache = _terrain_of(repo)


def reset_terrain_costs() -> None:
    """Clear the cache so the next lookup reads the default content catalog."""
    global _terrain_cache
    _terrain_cache = None


def _definition(terrain_id: str) -> TerrainDefinition:
    terrain = _terrain()
    try:
        return terrain[terrain_id]
    except KeyError:
        raise UnknownTerrainError(f"terrain {terrain_id!r} is not in the content catalog (known: {sorted(terrain)}); declare it in data/content/world/terrain.yaml") from None


def terrain_cost(terrain_id: str) -> float:
    """The declared move cost of the terrain with this catalog id."""
    return float(_definition(terrain_id).move_cost_multiplier)


def terrain_gives_cover(terrain_id: str) -> bool:
    """Whether the terrain with this catalog id is declared to give cover."""
    return bool(_definition(terrain_id).gives_cover)


def terrain_is_high_ground(terrain_id: str) -> bool:
    """Whether the terrain with this catalog id is declared high ground."""
    return bool(_definition(terrain_id).high_ground)


def validate_terrain_ids(terrain_ids: Iterable[str]) -> None:
    """Raise `UnknownTerrainError` naming every id in `terrain_ids` the catalog does not know (the compile-time content check)."""
    terrain = _terrain()
    unknown = sorted({t for t in terrain_ids if t not in terrain})
    if unknown:
        raise UnknownTerrainError(f"terrain ids not in the content catalog: {unknown} (known: {sorted(terrain)}); declare each in data/content/world/terrain.yaml with a move_cost_multiplier")
