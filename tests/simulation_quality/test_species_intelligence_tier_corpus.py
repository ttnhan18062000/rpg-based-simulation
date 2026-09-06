"""Idea 14 (Species Classification) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS).

CORRECTION, found during Investigate: `intelligence_tier` is NOT read by coming-of-age or a
"Progression-Planner eligibility" gate -- confirmed via grep, its only real `src/` consumer is
`RoleModelImitationService.compute_imitation_fidelity()` (src/strategy/role_model_imitation.py),
a pure imitation-fidelity multiplier (1.0 for high tier, 0.5 for low tier), unrelated to Coming of
Age. The content-level rule itself is real: every real species with `tool_user` in
`natural_traits` has `intelligence_tier == "high"` (a one-directional implication, not a full
biconditional -- `dragonkin`/other magic-sensitive species are real, schema-disclosed exceptions
that reach "high" tier without `tool_user`, per `SpeciesDefinition.intelligence_tier`'s own field
docstring allowing "explicitly justified exceptions").
"""
from __future__ import annotations

import yaml

from src.core.builder import V2EntityBuilder
from src.strategy.role_model_imitation import RoleModelImitationService

SPECIES_PATH = "data/content/living/species.yaml"


def test_every_tool_user_species_is_high_intelligence_tier():
    species = yaml.safe_load(open(SPECIES_PATH))
    assert species, "expected real species content"

    for s in species:
        if "tool_user" in s.get("natural_traits", []):
            assert s["intelligence_tier"] == "high", (
                f"{s['id']} has tool_user but intelligence_tier={s['intelligence_tier']!r}"
            )


def test_imitation_fidelity_is_high_for_high_tier_species():
    entity = V2EntityBuilder(1).location(0.0, 0.0).identity(properties={"species_id": "human"}).build()
    fidelity = RoleModelImitationService.compute_imitation_fidelity(entity)
    assert fidelity == RoleModelImitationService.HIGH_TIER_FIDELITY


def test_imitation_fidelity_is_low_for_low_tier_species():
    entity = V2EntityBuilder(1).location(0.0, 0.0).identity(properties={"species_id": "wolf"}).build()
    fidelity = RoleModelImitationService.compute_imitation_fidelity(entity)
    assert fidelity == RoleModelImitationService.LOW_TIER_FIDELITY
