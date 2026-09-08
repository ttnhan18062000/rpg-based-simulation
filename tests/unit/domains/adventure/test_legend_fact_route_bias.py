"""Tests for AdventureRouteScorer Living Legend bias branch (TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING)."""

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.self_model import (
    KnowledgeModelComponent,
    NeedInterpretationComponent,
    SelfAwarenessComponent,
    SelfModelBundle,
)
from src.core.state import BiologicalComponent, CombatComponent
from src.domains.adventure.schema import AdventureRouteOption, RouteFamily
from src.domains.adventure.scoring import AdventureRouteScorer
from src.domains.fame.legend import LegendFact


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_entity() -> object:
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(role=EntityRole.HERO, traits=set())
    b.replace_self_model(SelfModelBundle(
        self_awareness=SelfAwarenessComponent(perceived_condition={"health": 1.0}, perceived_weaknesses=()),
        needs=NeedInterpretationComponent(active_needs={}, dominant_need=None),
        knowledge=KnowledgeModelComponent(unknowns={}),
    ))
    return b.build()


def _route(family: RouteFamily, benefit: float = 0.5) -> AdventureRouteOption:
    return AdventureRouteOption(
        family=family,
        score=0.0,
        confidence=0.8,
        expected_benefit=benefit,
        expected_risk=0.1,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_legend_fact_raises_quest_opportunity_score_when_present():
    entity = _build_entity()
    route = _route(RouteFamily.QUEST_OPPORTUNITY)
    fact = LegendFact(subject_id="1", fame=0.7)

    baseline = AdventureRouteScorer.score(entity, route)
    with_legend = AdventureRouteScorer.score(entity, route, legend_fact=fact)

    assert with_legend.personality_bias > baseline.personality_bias
    assert with_legend.score > baseline.score
    assert with_legend.personality_bias - baseline.personality_bias == round(0.7 * 0.30, 4)


def test_legend_fact_no_effect_when_route_family_unmapped():
    entity = _build_entity()
    route = _route(RouteFamily.ASK_INFORMATION)
    fact = LegendFact(subject_id="1", fame=0.9)

    baseline = AdventureRouteScorer.score(entity, route)
    with_legend = AdventureRouteScorer.score(entity, route, legend_fact=fact)

    assert with_legend.personality_bias == baseline.personality_bias
    assert with_legend.score == baseline.score


def test_legend_fact_none_is_identical_to_omitted_default():
    entity = _build_entity()
    route = _route(RouteFamily.QUEST_OPPORTUNITY)

    default_call = AdventureRouteScorer.score(entity, route)
    explicit_none = AdventureRouteScorer.score(entity, route, legend_fact=None)

    assert default_call.score == explicit_none.score
    assert default_call.personality_bias == explicit_none.personality_bias


def test_legend_fact_and_culture_drift_are_additive():
    from src.domains.culture.model import CultureState

    entity = _build_entity()
    route = _route(RouteFamily.QUEST_OPPORTUNITY)
    fact = LegendFact(subject_id="1", fame=0.6)

    legend_only = AdventureRouteScorer.score(entity, route, legend_fact=fact)
    # QUEST_OPPORTUNITY has no Culture Drift tag mapping (_CULTURE_DRIFT_TAGS_BY_FAMILY), so a
    # culture_state alone must not change the score -- this proves the two branches are
    # independent code paths rather than accidentally sharing state.
    culture = CultureState(fatalism=0.9, hero_veneration=0.9, resource_scarcity_memory=0.9, faction_conflict_exposure=0.9)
    legend_and_culture = AdventureRouteScorer.score(entity, route, legend_fact=fact, culture_state=culture)

    assert legend_and_culture.personality_bias == legend_only.personality_bias
