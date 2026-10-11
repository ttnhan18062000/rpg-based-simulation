"""Plant cover on wild land (owner row 59): a biome names the cover kind its open land carries, and the assembly places its patches.

A region whose catalog biome declares ``grazing_cover`` gets patches of that resource kind, a number set by the kind's own density per
1,000 tiles of the region's bounds, rounded per region and at least 1. A patch is an ordinary resource node (it regrows and is eaten through
the same ecology and harvest paths as any node); this module only decides how many exist and where they are declared. Placement inside the
region is the compiler's, from the node's seeded stream.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from src.worldbuilding.schema import ResourceNodeSpec

if TYPE_CHECKING:
    from src.content.repository import CatalogRepository
    from src.worldbuilding.schema import RegionSpec

TILES_PER_DENSITY_UNIT = 1000.0  # the declared density is per this many tiles of a region's bounds


def patch_count(bounds: Tuple[int, int, int, int], density_per_1000_tiles: int) -> int:
    """Patches for a region of these bounds: its tile count scaled by the kind's density, rounded, at least 1."""
    min_x, min_y, max_x, max_y = bounds
    tiles = (max_x - min_x + 1) * (max_y - min_y + 1)
    return max(1, round(tiles / TILES_PER_DENSITY_UNIT * density_per_1000_tiles))


def region_cover_kind(repo: "CatalogRepository", region_id: str) -> Optional[str]:
    """The cover resource kind of the region's catalog biome, or None when its biome declares none (or the region is not in the catalog)."""
    region_def = repo.get_region(region_id)
    if region_def is None and "_" in region_id:
        region_def = repo.get_region(region_id.split("_", 1)[1])
    biome = repo.get_biome(region_def.biome) if region_def is not None and region_def.biome else None
    return biome.grazing_cover if biome is not None else None


def cover_patch_specs(repo: "CatalogRepository", regions: Dict[str, "RegionSpec"]) -> List[ResourceNodeSpec]:
    """The patch nodes for every region whose biome carries cover, in region order (deterministic)."""
    specs: List[ResourceNodeSpec] = []
    for region_id, region in regions.items():
        kind = region_cover_kind(repo, region_id)
        kind_def = repo.get_resource(kind) if kind else None
        if kind_def is None or kind_def.density_per_1000_tiles is None:
            continue
        regen = kind_def.regen_per_check
        for i in range(patch_count(region.bounds, kind_def.density_per_1000_tiles)):
            fields = {"id": f"cover__{region_id}__{i}", "resource_type": kind, "count": kind_def.default_charges, "region": region_id}
            if regen is not None:
                fields["regen_rate"] = regen
            specs.append(ResourceNodeSpec(**fields))
    return specs
