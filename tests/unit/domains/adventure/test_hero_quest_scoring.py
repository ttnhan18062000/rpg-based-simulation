"""
tests/unit/domains/adventure/test_hero_quest_scoring.py

TCK-20260619-E23D-HERO-MATCHING — HERO Capability Matching for Quest Routes.
Verifies that HERO entities with matching capability traits score QUEST_OPPORTUNITY
routes above GATHER_RESOURCE, and that non-HERO entities are unaffected.
"""

from __future__ import annotations

import pytest
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.models.quests import QuestOpportunity, QuestOpportunityStatus
from src.core.state import CombatComponent, BiologicalComponent
from src.core.self_model import (
    SelfModelBundle,
    SelfAwarenessComponent,
    NeedInterpretationComponent,
    KnowledgeModelComponent,
)
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption
from src.domains.adventure.scoring import AdventureRouteScorer


# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_entity(role: EntityRole, traits: set[str] | None = None):
    """Build a minimal entity with the given role and capability traits."""
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(role=role, traits=traits or set())
    awareness = SelfAwarenessComponent(perceived_condition={"health": 1.0}, perceived_weaknesses=())
    needs = NeedInterpretationComponent(active_needs={}, dominant_need=None)
    km = KnowledgeModelComponent(unknowns={})
    b.replace_self_model(SelfModelBundle(self_awareness=awareness, needs=needs, knowledge=km))
    return b.build()


def _quest_route(quest_id: str | None = "q1", benefit: float = 0.5) -> AdventureRouteOption:
    return AdventureRouteOption(
        family=RouteFamily.QUEST_OPPORTUNITY,
        score=0.0,
        confidence=0.8,
        expected_benefit=benefit,
        expected_risk=0.1,
        quest_id=quest_id,
    )


def _gather_route(benefit: float = 0.5) -> AdventureRouteOption:
    return AdventureRouteOption(
        family=RouteFamily.GATHER_RESOURCE,
        score=0.0,
        confidence=0.8,
        expected_benefit=benefit,
        expected_risk=0.1,
    )


def _make_registry(objective_chain: tuple[str, ...], quest_id: str = "q1") -> dict:
    opp = QuestOpportunity(
        id=quest_id,
        kind="resource_crisis",
        trigger_condition="test",
        objective_chain=objective_chain,
        reward_spec={"gold": 50, "xp": 100},
        faction_source=None,
        expiry_ticks=100,
        source_event_id=None,
        status=QuestOpportunityStatus.OFFERED,
    )
    return {quest_id: opp}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_hero_entity_scores_quest_above_harvesting():
    """AC1: HERO with matching capability scores QUEST_OPPORTUNITY above GATHER_RESOURCE."""
    hero = _build_entity(EntityRole.HERO, traits={"combat"})
    registry = _make_registry(("combat:threat:1",))
    quest = _quest_route(benefit=0.5)
    gather = _gather_route(benefit=0.5)

    scored_quest = AdventureRouteScorer.score(hero, quest, quest_registry=registry)
    scored_gather = AdventureRouteScorer.score(hero, gather)

    assert scored_quest.score > scored_gather.score, (
        f"HERO quest score {scored_quest.score} should exceed gather score {scored_gather.score}"
    )


def test_non_hero_entity_unaffected():
    """AC2: Non-HERO entity scores quest route <= equivalent GATHER_RESOURCE route."""
    npc = _build_entity(EntityRole.SHOPKEEPER, traits={"combat"})
    registry = _make_registry(("combat:threat:1",))
    quest = _quest_route(benefit=0.5)
    gather = _gather_route(benefit=0.5)

    scored_quest = AdventureRouteScorer.score(npc, quest, quest_registry=registry)
    scored_gather = AdventureRouteScorer.score(npc, gather)

    assert scored_quest.score <= scored_gather.score, (
        f"Non-HERO quest score {scored_quest.score} should be <= gather score {scored_gather.score}"
    )


def test_hero_full_match_scores_higher_than_no_match():
    """Full capability match (1.0) yields higher benefit than no match (0.0)."""
    registry = _make_registry(("combat:threat:1",))

    hero_match = _build_entity(EntityRole.HERO, traits={"combat"})
    hero_no_match = _build_entity(EntityRole.HERO, traits={"social"})

    route = _quest_route(benefit=0.5)
    scored_match = AdventureRouteScorer.score(hero_match, route, quest_registry=registry)
    scored_no_match = AdventureRouteScorer.score(hero_no_match, route, quest_registry=registry)

    assert scored_match.score > scored_no_match.score, (
        f"Full-match score {scored_match.score} should exceed no-match score {scored_no_match.score}"
    )


def test_hero_partial_match_intermediate_score():
    """Partial match (0.5) yields a score between full-match and no-match."""
    # Quest requires both combat AND magic
    registry = _make_registry(("combat:threat:1", "magic:debuff:1"))

    hero_full = _build_entity(EntityRole.HERO, traits={"combat", "magic"})
    hero_partial = _build_entity(EntityRole.HERO, traits={"combat"})        # 1 of 2
    hero_none = _build_entity(EntityRole.HERO, traits={"social"})

    route = _quest_route(benefit=0.5)
    scored_full = AdventureRouteScorer.score(hero_full, route, quest_registry=registry)
    scored_partial = AdventureRouteScorer.score(hero_partial, route, quest_registry=registry)
    scored_none = AdventureRouteScorer.score(hero_none, route, quest_registry=registry)

    assert scored_full.score > scored_partial.score > scored_none.score, (
        f"Expected full {scored_full.score} > partial {scored_partial.score} > none {scored_none.score}"
    )


def test_quest_opportunity_missing_registry_entry_uses_no_match():
    """HERO with quest_id not in registry falls back to capability_match=0.0 (no crash)."""
    hero = _build_entity(EntityRole.HERO, traits={"combat"})
    registry = {}  # empty — quest not registered

    route = _quest_route(quest_id="unknown_quest", benefit=0.5)
    scored = AdventureRouteScorer.score(hero, route, quest_registry=registry)

    # benefit = 0.5 * (1.0 + 0.0) = 0.5, same as no-match
    hero_no_match = _build_entity(EntityRole.HERO, traits={"social"})
    scored_no_match = AdventureRouteScorer.score(
        hero_no_match, _quest_route(quest_id="unknown_quest", benefit=0.5), quest_registry=registry
    )
    assert scored.score == scored_no_match.score


def test_quest_opportunity_none_quest_id_uses_no_match():
    """QUEST_OPPORTUNITY route with quest_id=None does not crash; scores as no-match."""
    hero = _build_entity(EntityRole.HERO, traits={"combat"})
    registry = _make_registry(("combat:threat:1",))

    route = _quest_route(quest_id=None, benefit=0.5)
    scored = AdventureRouteScorer.score(hero, route, quest_registry=registry)

    # Should not raise; capability_match=0.0 → benefit *= 1.0
    assert scored.score >= 0.0


def test_non_hero_quest_opportunity_uses_half_benefit():
    """Non-HERO entity receives benefit * 0.5 for QUEST_OPPORTUNITY routes."""
    npc = _build_entity(EntityRole.MONSTER, traits={"combat"})
    registry = _make_registry(("combat:threat:1",))

    route = _quest_route(benefit=1.0)
    scored = AdventureRouteScorer.score(npc, route, quest_registry=registry)

    # benefit = 1.0 * 0.5 = 0.5 (before risk/urgency adjustments)
    assert scored.benefit_score == pytest.approx(0.5, abs=1e-4)


def test_no_regression_existing_families_unaffected():
    """Existing route families are not changed by the QUEST_OPPORTUNITY branch."""
    hero = _build_entity(EntityRole.HERO, traits={"combat"})
    gather = _gather_route(benefit=0.5)

    # Without quest_registry, scorer should work exactly as before (no crash)
    scored = AdventureRouteScorer.score(hero, gather)
    assert scored.score >= 0.0
    assert scored.benefit_score == pytest.approx(0.5, abs=1e-4)
