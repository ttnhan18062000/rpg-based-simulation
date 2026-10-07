"""
src/cognition/common_knowledge.py
───────────────────────────────────────────────────────────────────────────────
KNOW-04: a subject may start with declared common knowledge about a recognisable kind.

The catalog declares, next to a species, what everyone commonly believes about it (``SpeciesDefinition.common_knowledge``).
Every subject is seeded once at spawn with one low-confidence ``KnowledgeFact`` per DECLARED species, recorded in its own
``KnowledgeModelComponent.facts`` with provenance ``source_id == "common_knowledge"``. It is a belief, not the kind's real
strength: it is declared folk belief, never derived from stats. Decision logic only reads it; only KNOW-02's declared
processes may change it later.

Seeding is world-wide on purpose: knowledge must not depend on which world a subject was compiled into.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from src.cognition.capability_estimate import (
    COMMON_KNOWLEDGE_CERTAINTY,
    COMMON_KNOWLEDGE_DANGER,
    CapabilityContext,
    CapabilityEstimateService,
)
from src.core.self_model import KnowledgeFact, KnowledgeModelComponent, SelfModelBundle
from src.engine import behavior_consumers

FACT_KEY_PREFIX = "danger."
COMMON_KNOWLEDGE_SOURCE_ID = "common_knowledge"
DANGER_FACT_TYPE = "danger_rating"


def danger_fact_key(species_id: str) -> str:
    """The key a species' danger fact lives under in ``KnowledgeModelComponent.facts``."""
    return f"{FACT_KEY_PREFIX}{species_id}"


def common_knowledge_facts(catalog: Any, certainty: float) -> Dict[str, KnowledgeFact]:
    """One danger fact per species the catalog declares common knowledge for, in sorted order."""
    facts: Dict[str, KnowledgeFact] = {}
    for species_id in sorted(catalog.species):
        declared = catalog.species[species_id].common_knowledge
        if declared is None:
            continue
        facts[danger_fact_key(species_id)] = KnowledgeFact(
            subject=species_id,
            fact_type=DANGER_FACT_TYPE,
            details={"danger_level": declared.danger},
            certainty=certainty,
            source_id=COMMON_KNOWLEDGE_SOURCE_ID,
            recorded_tick=0,
        )
    return facts


def seeded_knowledge(catalog: Optional[Any]) -> KnowledgeModelComponent:
    """The knowledge component a new subject starts with."""
    if catalog is None:
        return KnowledgeModelComponent()
    return KnowledgeModelComponent(facts=common_knowledge_facts(catalog, COMMON_KNOWLEDGE_CERTAINTY))


def _recognised_kind(hostile: Any) -> str:
    """What an observer recognises the hostile as: its species, else (for a hand-built entity) its kind."""
    return str((hostile.identity.properties or {}).get("species_id") or hostile.kind)


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


def default_self_model() -> SelfModelBundle:
    """The self-model a new subject starts with: empty except for the common knowledge from the warmed catalog.

    World-wide, not per world: knowledge must not depend on which world the subject was compiled into."""
    if behavior_consumers._catalog is None:
        behavior_consumers._auto_init()
    return SelfModelBundle(knowledge=seeded_knowledge(behavior_consumers._catalog))
