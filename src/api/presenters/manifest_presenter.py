from __future__ import annotations
from typing import Any, Dict, Optional
from src.core.state import AuthoritativeState
from src.content.repository import CatalogRepository
from src.api.presenters.state_presenter import StatePresenter

# Fixed independently of CatalogRepository._version (src/content/repository.py:226, :632-634) --
# that field versions the catalog's own internal schema/loader contract, a different concept from
# this route's response-shape contract. Bump this manually only when the manifest response's own
# field set/shape changes; dictionary_version (catalog.fingerprint) already carries content-only
# changes, per AC #3.
MANIFEST_PROTOCOL_VERSION = "1.0.0"


class ManifestPresenter:
    @staticmethod
    def present_manifest(state: Optional[AuthoritativeState], catalog: CatalogRepository) -> Dict[str, Any]:
        entity_kinds = {
            def_id: (d.display_name or d.id) for def_id, d in catalog.entity_archetypes.items()
        }
        building_types = {
            def_id: (d.display_name or d.id) for def_id, d in catalog.buildings.items()
        }

        terrain_types: Dict[str, str] = {}
        if state is not None:
            code_map = StatePresenter.terrain_code_map(state)  # {raw_terrain_str: int_code}
            for raw_terrain, code in code_map.items():
                terrain_types[str(code)] = ManifestPresenter._terrain_display_name(raw_terrain, catalog)

        return {
            "protocol_version": MANIFEST_PROTOCOL_VERSION,
            "dictionary_version": catalog.fingerprint,
            "terrain_types": terrain_types,
            "entity_kinds": entity_kinds,
            "building_types": building_types,
            # location_types intentionally omitted -- see docs/engine/contracts/frontend.md §2A and
            # investigation.md's Risks section: no LocationDefinition/CatalogRepository.locations
            # registry exists anywhere in src/content/schema.py; building one is out of this
            # ticket's scope (Out of Scope: "Building any new location-type registry beyond the
            # minimal decision documented above, if dropping the field is chosen instead").
        }

    @staticmethod
    def _terrain_display_name(raw_terrain: str, catalog: CatalogRepository) -> str:
        definition = catalog.terrain.get(raw_terrain.lower())
        if definition is not None:
            return definition.display_name or definition.id
        # Uncataloged default (e.g. "PLAIN"/"GRASS" from src/worldbuilding/compiler.py:205 and
        # recipe.py:16) -- same fallback precedent as present_static's b.kind.title() /
        # n.kind.title() (state_presenter.py:205, :218).
        return raw_terrain.title()
