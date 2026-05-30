"""
src/domains/memory/spatial_update.py
───────────────────────────────────────────────────────────────────────────────
Phase 13 — SpatialMemoryUpdateService

UpdatesVisited regions records, safety/danger path rankings, and resource observations
inside SpatialMemory.
"""

from __future__ import annotations
from dataclasses import replace
from typing import Dict, Any

from src.core.state import EntityState
from src.core.cognition import (
    SpatialMemory,
    RegionVisitMemory,
    RouteMemory,
    ResourceSiteMemory,
    FailedSearchMemory
)

class SpatialMemoryUpdateService:
    """Updates SpatialMemory container states from events and movement."""

    @staticmethod
    def update_region_visit(spatial: SpatialMemory, region_id: str) -> SpatialMemory:
        visited = dict(spatial.visited_regions)
        if region_id in visited:
            old = visited[region_id]
            visited[region_id] = RegionVisitMemory(
                region_id=region_id,
                visit_count=old.visit_count + 1,
                familiarity=min(1.0, old.familiarity + 0.15),
                is_dangerous=old.is_dangerous
            )
        else:
            visited[region_id] = RegionVisitMemory(
                region_id=region_id,
                visit_count=1,
                familiarity=0.2
            )
        return replace(spatial, visited_regions=visited)

    @staticmethod
    def mark_region_danger(spatial: SpatialMemory, region_id: str, is_dangerous: bool = True) -> SpatialMemory:
        visited = dict(spatial.visited_regions)
        if region_id in visited:
            old = visited[region_id]
            visited[region_id] = RegionVisitMemory(
                region_id=region_id,
                visit_count=old.visit_count,
                familiarity=old.familiarity,
                is_dangerous=is_dangerous
            )
        else:
            visited[region_id] = RegionVisitMemory(
                region_id=region_id,
                visit_count=0,
                familiarity=0.0,
                is_dangerous=is_dangerous
            )
        return replace(spatial, visited_regions=visited)

    @staticmethod
    def record_resource_site(spatial: SpatialMemory, site_id: str, kind: str, pos: tuple[float, float]) -> SpatialMemory:
        sites = dict(spatial.known_resource_sites)
        sites[site_id] = ResourceSiteMemory(
            site_id=site_id,
            resource_kind=kind,
            position=pos
        )
        return replace(spatial, known_resource_sites=sites)
