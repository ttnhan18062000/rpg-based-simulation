"""
Unit tests for entity initialization fixes (TCK-20260619-P0-ENTITY-INIT).

Verifies:
1. PersonalityComponent traits are seeded with non-zero variance across entities
2. class_id is assigned by role (HERO → WARRIOR/MAGE/ROGUE)
3. Seeding is deterministic: same world seed → same personality vectors
"""
from __future__ import annotations

import pytest
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.compiler import WorldCompiler


_SEED = 42

_MULTI_ROLE_SPEC = {
    "schema_version": "worldspec.v1",
    "world_id": "init_test_world",
    "name": "Init Test World",
    "topology": {"width": 50, "height": 50, "coordinate_system": "grid"},
    "regions": [
        {"id": "town", "type": "town", "bounds": [0, 0, 20, 20], "terrain": "GRASS"},
        {"id": "wilds", "type": "wilderness", "bounds": [25, 25, 45, 45], "terrain": "FOREST"},
    ],
    "factions": [
        {"id": "hero_guild", "type": "hero"},
        {"id": "townsfolk", "type": "civilian"},
        {"id": "monsters", "type": "hostile"},
    ],
    "entities": [
        {"id": "heroes", "count": 6, "role": "hero", "faction": "hero_guild", "spawn_region": "town"},
        {"id": "citizens", "count": 4, "role": "citizen", "faction": "townsfolk", "spawn_region": "town"},
        {"id": "horde", "count": 3, "role": "monster", "faction": "monsters", "spawn_region": "wilds"},
    ],
    "resources": [],
    "buildings": [],
    "quest_definitions": [],
}


def _compile(seed: int = _SEED):
    spec = WorldSpec.model_validate(_MULTI_ROLE_SPEC)
    state, _ = WorldCompiler.compile(spec, seed=seed)
    return state


def test_entity_personality_variance_at_spawn():
    """No two entities should share the same (bravery, greed, industry, sociability) tuple."""
    state = _compile()
    tuples = set()
    for ent in state.entities.values():
        p = ent.identity.personality
        trait_tuple = (p.bravery, p.greed, p.industry, p.sociability)
        # Every trait must be in [0.0, 1.0)
        assert all(0.0 <= v < 1.0 for v in trait_tuple), f"Trait out of range: {trait_tuple}"
        tuples.add(trait_tuple)
    assert len(tuples) == len(state.entities), (
        f"Duplicate personality vectors found: {len(state.entities)} entities, "
        f"only {len(tuples)} distinct tuples"
    )


def test_class_id_non_novice_for_hero_role():
    """HERO-role entities must receive a class from {WARRIOR, MAGE, ROGUE}."""
    state = _compile()
    hero_classes = set()
    citizen_classes = set()

    for ent in state.entities.values():
        role = ent.identity.role
        cid = ent.identity.class_id
        from src.core.enums import EntityRole
        if role == EntityRole.HERO.value:
            hero_classes.add(cid)
        elif role == EntityRole.CITIZEN.value:
            citizen_classes.add(cid)

    assert hero_classes, "No HERO entities found — test world must include hero population"
    assert hero_classes <= {"WARRIOR", "MAGE", "ROGUE"}, (
        f"HERO entities received unexpected class_ids: {hero_classes}"
    )
    # With 6 heroes, we should see multiple classes from the pool of 3
    assert len(hero_classes) > 1, (
        f"All 6 hero entities got the same class_id={hero_classes} — "
        "class assignment is not varying across the pool"
    )


def test_personality_seeding_is_deterministic():
    """Compiling the same world twice with the same seed produces identical personality vectors."""
    state_a = _compile(seed=_SEED)
    state_b = _compile(seed=_SEED)

    for eid in state_a.entities:
        pa = state_a.entities[eid].identity.personality
        pb = state_b.entities[eid].identity.personality
        assert pa == pb, (
            f"Entity {eid} personality mismatch: {pa} vs {pb} (non-deterministic seeding)"
        )


def test_different_seeds_produce_different_personalities():
    """Different world seeds must produce different personality distributions."""
    state_42 = _compile(seed=42)
    state_137 = _compile(seed=137)

    same_count = 0
    for eid in state_42.entities:
        if eid in state_137.entities:
            pa = state_42.entities[eid].identity.personality
            pb = state_137.entities[eid].identity.personality
            if pa == pb:
                same_count += 1

    total = len(state_42.entities)
    assert same_count < total, (
        "All entities have identical personalities across seeds 42 and 137 — "
        "seed isolation is broken"
    )
