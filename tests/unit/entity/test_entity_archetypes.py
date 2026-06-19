"""
Unit tests for HERO archetype class coverage (TCK-20260619-E11A-HERO-AUTHORING).

Verifies that 6 HERO-role entities compiled from an inline worldspec.v1 at seed=42
collectively cover all three tier-1 hero classes: WARRIOR, MAGE, ROGUE.
"""
from __future__ import annotations

from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.compiler import WorldCompiler
from src.core.enums import EntityRole


_SEED = 42

_HERO_ARCHETYPE_SPEC = {
    "schema_version": "worldspec.v1",
    "world_id": "archetype_test_world",
    "name": "Archetype Test World",
    "topology": {"width": 50, "height": 50, "coordinate_system": "grid"},
    "regions": [
        {"id": "town", "type": "town", "bounds": [0, 0, 20, 20], "terrain": "GRASS"},
    ],
    "factions": [
        {"id": "hero_guild", "type": "hero"},
    ],
    "entities": [
        {"id": "heroes", "count": 6, "role": "hero", "faction": "hero_guild", "spawn_region": "town"},
    ],
    "resources": [],
    "buildings": [],
    "quest_definitions": [],
}


def test_hero_archetypes_cover_combat_mage_rogue():
    """6 HERO entities at seed=42 must collectively include WARRIOR, MAGE, and ROGUE."""
    spec = WorldSpec.model_validate(_HERO_ARCHETYPE_SPEC)
    state, _ = WorldCompiler.compile(spec, seed=_SEED)

    hero_classes = {
        ent.identity.class_id
        for ent in state.entities.values()
        if ent.identity.role == EntityRole.HERO.value
    }

    assert "WARRIOR" in hero_classes, f"No WARRIOR found in hero classes: {hero_classes}"
    assert "MAGE" in hero_classes, f"No MAGE found in hero classes: {hero_classes}"
    assert "ROGUE" in hero_classes, f"No ROGUE found in hero classes: {hero_classes}"
    assert hero_classes <= {"WARRIOR", "MAGE", "ROGUE"}, (
        f"HERO entities received unexpected class_ids: {hero_classes}"
    )
