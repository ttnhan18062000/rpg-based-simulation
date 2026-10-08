"""
src/content/common_knowledge_seed.py
───────────────────────────────────────────────────────────────────────────────
KNOW-04: a subject may start with declared common knowledge about a recognisable kind (the seeding half).

The catalog declares, next to a species, what everyone commonly believes about it (``SpeciesDefinition.common_knowledge``).
Every subject is seeded once at spawn with one low-confidence ``KnowledgeFact`` per DECLARED species, recorded in its own
``KnowledgeModelComponent.facts`` with provenance ``source_id == "common_knowledge"``. It is a belief, not the kind's real
strength: it is declared folk belief, never derived from stats. Decision logic only reads it (``src.cognition.common_knowledge``);
only KNOW-02's declared processes may change it later.

Seeding is world-wide on purpose: knowledge must not depend on which world a subject was compiled into.

This module sits in the content pipeline layer so the world compiler, the entity spawner and the archetype factory can seed a
subject without importing the cognition or engine layers (TCK-20261008-CORE-STRATEGIC-IMPORTS-AI-GOALS-FOR-A-TYPE-HINT, the
registry layer order). The catalog the engine has warmed is reached through a provider the engine installs
(``install_warm_catalog_provider``); with no provider installed the default catalog is loaded here once.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from src.content.repository import CatalogRepository
from src.core.self_model import KnowledgeFact, KnowledgeModelComponent, SelfModelBundle

FACT_KEY_PREFIX = "danger."
COMMON_KNOWLEDGE_SOURCE_ID = "common_knowledge"
DANGER_FACT_TYPE = "danger_rating"
COMMON_KNOWLEDGE_CERTAINTY = 0.3   # a weak prior: experience and trusted reports are meant to outweigh it

_warm_catalog_provider: Optional[Callable[[], Any]] = None
_fallback_catalog: Any = None


def install_warm_catalog_provider(provider: Callable[[], Any]) -> None:
    """Install the function that returns the warmed catalog (the engine's behavior consumers do, at import)."""
    global _warm_catalog_provider
    _warm_catalog_provider = provider


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


def _warmed_catalog() -> Any:
    """The warmed catalog through the installed provider, else the default catalog loaded once here."""
    global _fallback_catalog
    if _warm_catalog_provider is not None:
        return _warm_catalog_provider()
    if _fallback_catalog is None:
        _fallback_catalog = CatalogRepository("data/content")
        _fallback_catalog.load_all()
    return _fallback_catalog


def default_self_model() -> SelfModelBundle:
    """The self-model a new subject starts with: empty except for the common knowledge from the warmed catalog.

    World-wide, not per world: knowledge must not depend on which world the subject was compiled into."""
    return SelfModelBundle(knowledge=seeded_knowledge(_warmed_catalog()))
