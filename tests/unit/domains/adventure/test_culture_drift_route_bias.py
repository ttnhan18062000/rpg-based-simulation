"""Tests for AdventureRouteScorer Culture Drift bias branch (TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE)."""

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
from src.domains.culture.model import CultureState


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

def test_culture_drift_raises_recover_score_when_fatalism_high():
    entity = _build_entity()
    route = _route(RouteFamily.RECOVER)
    culture = CultureState(fatalism=0.8)

    baseline = AdventureRouteScorer.score(entity, route)
    with_culture = AdventureRouteScorer.score(entity, route, culture_state=culture)

    assert with_culture.personality_bias > baseline.personality_bias
    assert with_culture.score > baseline.score


def test_culture_drift_no_effect_when_all_axes_below_activation_threshold():
    entity = _build_entity()
    route = _route(RouteFamily.RECOVER)
    culture = CultureState(fatalism=0.1)

    baseline = AdventureRouteScorer.score(entity, route)
    with_culture = AdventureRouteScorer.score(entity, route, culture_state=culture)

    assert with_culture.personality_bias == baseline.personality_bias
    assert with_culture.score == baseline.score


def test_culture_drift_no_effect_when_route_family_unmapped():
    entity = _build_entity()
    route = _route(RouteFamily.ASK_INFORMATION)
    culture = CultureState(fatalism=0.9, hero_veneration=0.9, resource_scarcity_memory=0.9, faction_conflict_exposure=0.9)

    baseline = AdventureRouteScorer.score(entity, route)
    with_culture = AdventureRouteScorer.score(entity, route, culture_state=culture)

    assert with_culture.personality_bias == baseline.personality_bias
    assert with_culture.score == baseline.score


def test_culture_drift_none_is_identical_to_omitted_default():
    entity = _build_entity()
    route = _route(RouteFamily.RECOVER)

    default_call = AdventureRouteScorer.score(entity, route)
    explicit_none = AdventureRouteScorer.score(entity, route, culture_state=None)

    assert default_call.score == explicit_none.score
    assert default_call.personality_bias == explicit_none.personality_bias
