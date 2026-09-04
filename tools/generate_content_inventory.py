#!/usr/bin/env python3
"""Generate config/content_inventory.json from real data/content/ counts.

TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH: docs/audits/D07_content_depth.md's own numeric
tables are hand-counted and had drifted silently for ~7 weeks (some categories off by 3-5x) before
this ticket's own real re-count found it. This generator is the fix -- mirrors
tools/generate_corpus_registry.py's own "generated, never hand-transcribed" precedent for a
different (content-catalog) audience. Re-run via `make content-inventory` whenever D07 needs a
real refresh; the qualitative Gap Risk scoring/narrative in D07 stays human-authored, only the raw
counts are generated here.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import yaml

OUTPUT_PATH = Path("config/content_inventory.json")

# category -> real source file, per D07_content_depth.md's own Layer table structure
_SINGLE_FILE_CATEGORIES: dict[str, str] = {
    "Traits": "data/content/foundation/traits.yaml",
    "Themes": "data/content/foundation/themes.yaml",
    "Roles": "data/content/social/roles.yaml",
    "Materials": "data/content/foundation/materials.yaml",
    "Attributes": "data/content/foundation/attributes.yaml",
    "Relationship axes": "data/content/foundation/relationship_axes.yaml",
    "Elements": "data/content/foundation/elements.yaml",
    "Stat profiles": "data/content/entities/stat_profiles.yaml",
    "Entity archetypes": "data/content/entities/entity_archetypes.yaml",
    "Populations": "data/content/entities/populations.yaml",
    "Species": "data/content/living/species.yaml",
    "Combat profiles": "data/content/entities/combat_profiles.yaml",
    "Skill profiles": "data/content/entities/skill_profiles.yaml",
    "Inventory profiles": "data/content/entities/inventory_profiles.yaml",
    "Body models": "data/content/living/body_models.yaml",
    "Cognition profiles": "data/content/living/cognition_profiles.yaml",
    "Drive profiles": "data/content/living/drive_profiles.yaml",
    "Need profiles": "data/content/living/need_profiles.yaml",
    "Sense profiles": "data/content/living/sense_profiles.yaml",
    "Items": "data/content/world/items.yaml",
    "Runtime regions": "data/content/world/runtime_regions.yaml",
    "Biomes": "data/content/world/biomes.yaml",
    "Resources": "data/content/world/resources.yaml",
    "Buildings": "data/content/world/buildings.yaml",
    "Ecologies": "data/content/world/ecologies.yaml",
    "Terrain": "data/content/world/terrain.yaml",
    "Services": "data/content/world/services.yaml",
    "Recipes": "data/content/world/recipes.yaml",
    "Factions": "data/content/social/factions.yaml",
    "Faction relationships": "data/content/social/faction_relationships.yaml",
    "Perspectives": "data/content/social/perspectives.yaml",
}


def _count_entries(path: str) -> int:
    data = yaml.safe_load(Path(path).read_text())
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return len(value)
        return len(data)
    return 0


def _count_scenarios() -> int:
    total = 0
    for path in sorted(glob.glob("data/content/simulation_scenarios/*.yaml")):
        data = yaml.safe_load(Path(path).read_text())
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    total += len(value)
                    break
        elif isinstance(data, list):
            total += len(data)
    return total


def generate() -> dict:
    counts: dict[str, int] = {}
    for category, path in sorted(_SINGLE_FILE_CATEGORIES.items()):
        counts[category] = _count_entries(path)

    counts["Simulation scenarios"] = _count_scenarios()
    counts["World modules"] = len(glob.glob("data/content/world_modules/*.yaml"))
    counts["World compositions"] = len(glob.glob("data/content/world_compositions/*.yaml"))
    counts["World compositions (generated)"] = len(
        glob.glob("data/content/world_compositions/generated/*.yaml")
    )
    return counts


def main() -> None:
    counts = generate()
    OUTPUT_PATH.write_text(json.dumps(counts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    total = sum(v for k, v in counts.items() if k != "World compositions (generated)")
    print(f"Wrote {len(counts)} categories to {OUTPUT_PATH} (real entry total: {total})")


if __name__ == "__main__":
    main()
