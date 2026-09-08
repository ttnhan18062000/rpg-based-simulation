"""Tests for AdventureRouteScorer Belief Institution bias branch (TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING)."""

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
from src.domains.belief_institution.model import BeliefInstitution


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


def _institution(belief_strength: float, origin_event_id: str = "ev_1", clan_id: str = "clan_1") -> BeliefInstitution:
    return BeliefInstitution(
        origin_event_id=origin_event_id,
        clan_id=clan_id,
        adherent_entity_ids=(1,),
        belief_strength=belief_strength,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_belief_institution_raises_quest_opportunity_score_when_present():
    entity = _build_entity()
    route = _route(RouteFamily.QUEST_OPPORTUNITY)
    inst = _institution(0.7)

    baseline = AdventureRouteScorer.score(entity, route)
    with_belief = AdventureRouteScorer.score(entity, route, belief_institutions=(inst,))

    assert with_belief.personality_bias > baseline.personality_bias
    assert with_belief.score > baseline.score
    # No event_fidelity supplied -> defaults to 1.0 (fully accurate), same as omitted.
    assert with_belief.personality_bias - baseline.personality_bias == round(0.7 * 1.0 * 0.30, 4)


def test_belief_institution_no_effect_when_route_family_unmapped():
    entity = _build_entity()
    route = _route(RouteFamily.ASK_INFORMATION)
    inst = _institution(0.9)

    baseline = AdventureRouteScorer.score(entity, route)
    with_belief = AdventureRouteScorer.score(entity, route, belief_institutions=(inst,))

    assert with_belief.personality_bias == baseline.personality_bias
    assert with_belief.score == baseline.score


def test_belief_institution_empty_tuple_is_identical_to_omitted_default():
    entity = _build_entity()
    route = _route(RouteFamily.QUEST_OPPORTUNITY)

    default_call = AdventureRouteScorer.score(entity, route)
    explicit_empty = AdventureRouteScorer.score(entity, route, belief_institutions=())

    assert default_call.score == explicit_empty.score
    assert default_call.personality_bias == explicit_empty.personality_bias


def test_belief_institution_scaled_by_event_fidelity():
    """A belief formed around a heavily-decayed-fidelity event carries less weight."""
    entity = _build_entity()
    route = _route(RouteFamily.QUEST_OPPORTUNITY)
    inst = _institution(0.8, origin_event_id="ev_decayed")

    full_fidelity = AdventureRouteScorer.score(
        entity, route, belief_institutions=(inst,), event_fidelity={"ev_decayed": 1.0}
    )
    decayed_fidelity = AdventureRouteScorer.score(
        entity, route, belief_institutions=(inst,), event_fidelity={"ev_decayed": 0.25}
    )
    missing_fidelity_entry = AdventureRouteScorer.score(
        entity, route, belief_institutions=(inst,), event_fidelity={}
    )

    assert decayed_fidelity.personality_bias < full_fidelity.personality_bias
    assert decayed_fidelity.personality_bias == round(0.8 * 0.25 * 0.30, 4)
    # A missing entry_id defaults to 1.0 (fully accurate), matching FidelityState's own default.
    assert missing_fidelity_entry.personality_bias == full_fidelity.personality_bias


def test_belief_institution_uses_strongest_of_multiple_memberships_not_sum():
    """An entity in >1 belief institution gets the strongest signal, not a stacked sum."""
    entity = _build_entity()
    route = _route(RouteFamily.QUEST_OPPORTUNITY)
    weak = _institution(0.2, origin_event_id="ev_a", clan_id="clan_a")
    strong = _institution(0.9, origin_event_id="ev_b", clan_id="clan_b")

    baseline = AdventureRouteScorer.score(entity, route)
    both = AdventureRouteScorer.score(entity, route, belief_institutions=(weak, strong))
    strong_only = AdventureRouteScorer.score(entity, route, belief_institutions=(strong,))

    assert both.personality_bias == strong_only.personality_bias
    assert both.personality_bias - baseline.personality_bias == round(0.9 * 0.30, 4)


def test_belief_institution_and_legend_fact_are_additive():
    from src.domains.fame.legend import LegendFact

    entity = _build_entity()
    route = _route(RouteFamily.QUEST_OPPORTUNITY)
    inst = _institution(0.5)
    fact = LegendFact(subject_id="1", fame=0.6)

    belief_only = AdventureRouteScorer.score(entity, route, belief_institutions=(inst,))
    both = AdventureRouteScorer.score(entity, route, belief_institutions=(inst,), legend_fact=fact)

    assert both.personality_bias > belief_only.personality_bias
    assert round(both.personality_bias - belief_only.personality_bias, 4) == round(0.6 * 0.30, 4)
