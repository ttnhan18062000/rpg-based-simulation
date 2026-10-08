"""
src/cognition/common_knowledge.py
───────────────────────────────────────────────────────────────────────────────
KNOW-04: a subject may start with declared common knowledge about a recognisable kind (the reading half).

The seeding (one low-confidence danger fact per declared species, provenance ``common_knowledge``) lives in
``src.content.common_knowledge_seed`` so the world compiler and spawner can seed without importing this layer; the names are
re-exported here. Decision logic only reads the facts: ``combat_capability_against`` turns the entity's own belief about a
hostile's species into a subjective chance (COMB-316). Only KNOW-02's declared processes may change a fact later.
"""
from __future__ import annotations

from typing import Any

from src.cognition.capability_estimate import (
    COMMON_KNOWLEDGE_DANGER,
    CapabilityContext,
    CapabilityEstimateService,
)
from src.content.common_knowledge_seed import (
    COMMON_KNOWLEDGE_CERTAINTY,
    COMMON_KNOWLEDGE_SOURCE_ID,
    DANGER_FACT_TYPE,
    FACT_KEY_PREFIX,
    common_knowledge_facts,
    danger_fact_key,
    default_self_model,
    seeded_knowledge,
)

__all__ = [
    "COMMON_KNOWLEDGE_CERTAINTY", "COMMON_KNOWLEDGE_SOURCE_ID", "DANGER_FACT_TYPE", "FACT_KEY_PREFIX", "UNRECOGNISED",
    "combat_capability_against", "common_knowledge_facts", "danger_fact_key", "default_self_model", "seeded_knowledge",
]

UNRECOGNISED = "unrecognised"


def _recognised_kind(hostile: Any) -> str:
    """What an observer recognises the hostile as: its species. With none the hostile is unrecognised and so uninformed;
    ``kind`` is the hidden population role and KNOW-04 forbids attaching a prior to it."""
    return str((hostile.identity.properties or {}).get("species_id") or UNRECOGNISED)


def combat_capability_against(entity: Any, hostile: Any) -> float:
    """The acting entity's subjective chance against `hostile` (COMB-316): ad hoc and read-only.

    The belief comes from the entity's own knowledge facts, keyed by the hostile's species; with none the estimate is neutral
    and recorded as uninformed."""
    kind = _recognised_kind(hostile)
    fact = entity.self_model.knowledge.facts.get(danger_fact_key(kind))
    beliefs = {}
    if fact is not None and fact.details.get("danger_level") in COMMON_KNOWLEDGE_DANGER:
        beliefs[kind] = {"danger_rating": COMMON_KNOWLEDGE_DANGER[fact.details["danger_level"]], "certainty": fact.certainty}
    component = CapabilityEstimateService.estimate(
        entity, context=CapabilityContext.for_combat(enemy_ids=[kind], enemy_data=beliefs))
    estimate = component.estimates.get(f"combat.enemy_type.{kind}")
    return estimate.estimate if estimate is not None else 0.0
