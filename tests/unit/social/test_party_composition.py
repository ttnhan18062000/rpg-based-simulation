# Compliance IDs: SOC-231, SOC-232
"""
Tests for PartyCompositionScorer and FORM_PARTY route generation.
Ticket: TCK-20260628-E41F-PARTY-SCORER
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.systems.social_systems.party_composition import PartyCompositionScorer, PartyRole
from src.core.enums import EntityRole, Faction
from src.core.models.social import SocialBond, RelationshipRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(
    eid: int, kind: str = "hero", bravery: float = 0.5, sociability: float = 0.5,
    trust_history: dict = None, bonds: dict = None, nemesis_ids: set = None,
):
    from src.core.builder import V2EntityBuilder
    entity = (
        V2EntityBuilder(eid)
        .kind(kind)
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
        .social(trust_history=trust_history or {}, bonds=bonds or {}, nemesis_ids=nemesis_ids or set())
        .build()
    )
    p = replace(entity.identity.personality, bravery=bravery, sociability=sociability)
    return replace(entity, identity=replace(entity.identity, personality=p))


# ---------------------------------------------------------------------------
# PartyRole inference (SOC-231)
# ---------------------------------------------------------------------------

def test_infer_guard_is_tank():
    e = _entity(1, kind="guard", bravery=0.7)
    assert PartyCompositionScorer.infer_party_role(e) == PartyRole.TANK


def test_infer_mage_is_healer():
    e = _entity(2, kind="mage", bravery=0.3)
    assert PartyCompositionScorer.infer_party_role(e) == PartyRole.HEALER


def test_infer_hero_brave_is_tank():
    e = _entity(3, kind="hero", bravery=0.8)
    assert PartyCompositionScorer.infer_party_role(e) == PartyRole.TANK


def test_infer_hero_low_bravery_is_dps():
    e = _entity(4, kind="hero", bravery=0.3)
    assert PartyCompositionScorer.infer_party_role(e) == PartyRole.DPS


def test_infer_worker_is_support():
    e = _entity(5, kind="worker", bravery=0.2)
    assert PartyCompositionScorer.infer_party_role(e) == PartyRole.SUPPORT


# ---------------------------------------------------------------------------
# Role diversity score (SOC-231)
# ---------------------------------------------------------------------------

def test_role_diversity_single_entity():
    e = _entity(1, kind="guard")
    assert PartyCompositionScorer.score_role_diversity([e]) == pytest.approx(0.25)  # 1/4 roles


def test_role_diversity_all_four_roles():
    entities = [
        _entity(1, kind="guard", bravery=0.8),    # TANK
        _entity(2, kind="mage"),                   # HEALER
        _entity(3, kind="hero", bravery=0.3),      # DPS
        _entity(4, kind="worker"),                  # SUPPORT
    ]
    assert PartyCompositionScorer.score_role_diversity(entities) == pytest.approx(1.0)


def test_role_diversity_all_same_role():
    entities = [_entity(i, kind="guard", bravery=0.8) for i in range(4)]
    assert PartyCompositionScorer.score_role_diversity(entities) == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# OCEAN compatibility score (SOC-232)
# ---------------------------------------------------------------------------

def test_ocean_compat_single_entity_is_neutral():
    e = _entity(1, bravery=0.5, sociability=0.5)
    assert PartyCompositionScorer.score_ocean_compatibility([e]) == pytest.approx(0.5)


def test_ocean_compat_identical_entities_is_zero():
    entities = [_entity(i, bravery=0.5, sociability=0.5) for i in range(4)]
    assert PartyCompositionScorer.score_ocean_compatibility(entities) == pytest.approx(0.0)


def test_ocean_compat_maximum_variance():
    # Two entities: one at 0.0 bravery, one at 1.0 — maximum variance
    entities = [
        _entity(1, bravery=0.0, sociability=0.0),
        _entity(2, bravery=1.0, sociability=1.0),
    ]
    score = PartyCompositionScorer.score_ocean_compatibility(entities)
    assert score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Combined score
# ---------------------------------------------------------------------------

def test_score_empty_returns_zero():
    assert PartyCompositionScorer.score([]) == 0.0


def test_score_balanced_party_higher_than_homogeneous():
    balanced = [
        _entity(1, kind="guard", bravery=0.9, sociability=0.2),    # TANK
        _entity(2, kind="mage", bravery=0.1, sociability=0.8),     # HEALER
        _entity(3, kind="hero", bravery=0.3, sociability=0.4),     # DPS
        _entity(4, kind="worker", bravery=0.2, sociability=0.6),   # SUPPORT
    ]
    homogeneous = [_entity(i, kind="guard", bravery=0.7, sociability=0.5) for i in range(4)]
    assert PartyCompositionScorer.score(balanced) > PartyCompositionScorer.score(homogeneous)


# ---------------------------------------------------------------------------
# Trust/bonds-aware scoring (SOC-244, TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY)
# ---------------------------------------------------------------------------

def test_party_composition_score_reflects_candidate_trust_history():
    pool = [_entity(2, kind="guard"), _entity(3, kind="mage")]
    actor_low = _entity(1, kind="hero", trust_history={2: -0.8})
    actor_high = _entity(1, kind="hero", trust_history={2: 0.8})
    assert PartyCompositionScorer.score(pool, actor=actor_low) != PartyCompositionScorer.score(
        pool, actor=actor_high
    )


def test_party_composition_score_unchanged_when_actor_omitted():
    balanced = [
        _entity(1, kind="guard", bravery=0.9, sociability=0.2),
        _entity(2, kind="mage", bravery=0.1, sociability=0.8),
        _entity(3, kind="hero", bravery=0.3, sociability=0.4),
        _entity(4, kind="worker", bravery=0.2, sociability=0.6),
    ]
    homogeneous = [_entity(i, kind="guard", bravery=0.7, sociability=0.5) for i in range(4)]

    for pool in (balanced, homogeneous):
        role_div = PartyCompositionScorer.score_role_diversity(pool)
        ocean_compat = PartyCompositionScorer.score_ocean_compatibility(pool)
        expected = round(
            PartyCompositionScorer.ROLE_DIVERSITY_WEIGHT * role_div
            + PartyCompositionScorer.OCEAN_COMPAT_WEIGHT * ocean_compat,
            4,
        )
        assert PartyCompositionScorer.score(pool) == expected


def test_party_composition_score_prioritizes_bond_sentiment_over_trust_history():
    candidate = _entity(2, kind="guard")
    actor = _entity(
        1, kind="hero",
        trust_history={2: -0.9},
        bonds={2: SocialBond(target_id=2, sentiment=0.9)},
    )
    assert PartyCompositionScorer.score_trust_bonds(actor, [candidate]) == pytest.approx(0.9)


def test_party_composition_trust_lookup_does_not_mutate_social_state():
    actor = _entity(1, kind="hero", trust_history={2: 0.5})
    candidate = _entity(2, kind="guard")
    actor_social_before = actor.social
    candidate_social_before = candidate.social

    PartyCompositionScorer.score([candidate], actor=actor)

    assert actor.social is actor_social_before
    assert candidate.social is candidate_social_before


def test_party_composition_trust_lookup_defaults_safely_for_unknown_candidate():
    actor = _entity(1, kind="hero")
    candidate = _entity(2, kind="guard")
    assert PartyCompositionScorer.score_trust_bonds(actor, [candidate]) == 0.0


# ---------------------------------------------------------------------------
# FORM_PARTY route generation
# ---------------------------------------------------------------------------

def test_form_party_route_generated_when_sociable_and_candidates_exist():
    from src.domains.adventure.generator import AdventureRouteGenerator
    from src.domains.adventure.schema import RouteFamily

    actor = _entity(1, kind="worker", sociability=0.7)
    candidate = _entity(2, kind="guard", bravery=0.8)

    class _FakeState:
        entities = {1: actor, 2: candidate}

    routes = AdventureRouteGenerator.generate(actor, state=_FakeState())
    families = {r.family for r in routes}
    assert RouteFamily.FORM_PARTY in families, "FORM_PARTY route should be generated for sociable entity"


def test_form_party_route_not_generated_when_low_sociability():
    from src.domains.adventure.generator import AdventureRouteGenerator
    from src.domains.adventure.schema import RouteFamily

    actor = _entity(1, kind="worker", sociability=0.1)  # below 0.2 threshold
    candidate = _entity(2, kind="guard", bravery=0.8)

    class _FakeState:
        entities = {1: actor, 2: candidate}

    routes = AdventureRouteGenerator.generate(actor, state=_FakeState())
    families = {r.family for r in routes}
    assert RouteFamily.FORM_PARTY not in families


def test_form_party_benefit_reflects_composition_score():
    from src.domains.adventure.generator import AdventureRouteGenerator
    from src.domains.adventure.schema import RouteFamily

    actor = _entity(1, kind="worker", sociability=0.8)
    diverse_candidates = [
        _entity(2, kind="guard", bravery=0.9),
        _entity(3, kind="mage", bravery=0.1),
    ]

    class _FakeState:
        entities = {e.id: e for e in [actor] + diverse_candidates}

    routes = AdventureRouteGenerator.generate(actor, state=_FakeState())
    fp = next((r for r in routes if r.family == RouteFamily.FORM_PARTY), None)
    assert fp is not None
    assert fp.expected_benefit >= 0.3, "FORM_PARTY expected_benefit should be ≥ 0.3"


def test_form_party_route_benefit_and_confidence_differ_with_candidate_trust():
    from src.domains.adventure.generator import AdventureRouteGenerator
    from src.domains.adventure.schema import RouteFamily

    candidate = _entity(2, kind="guard", bravery=0.8)

    actor_low = _entity(1, kind="worker", sociability=0.7, trust_history={2: -0.9})
    actor_high = _entity(1, kind="worker", sociability=0.7, trust_history={2: 0.9})

    class _FakeStateLow:
        entities = {1: actor_low, 2: candidate}

    class _FakeStateHigh:
        entities = {1: actor_high, 2: candidate}

    routes_low = AdventureRouteGenerator.generate(actor_low, state=_FakeStateLow())
    routes_high = AdventureRouteGenerator.generate(actor_high, state=_FakeStateHigh())

    fp_low = next(r for r in routes_low if r.family == RouteFamily.FORM_PARTY)
    fp_high = next(r for r in routes_high if r.family == RouteFamily.FORM_PARTY)

    assert fp_low.expected_benefit != fp_high.expected_benefit
    assert fp_low.confidence != fp_high.confidence


# ---------------------------------------------------------------------------
# Role-affinity scoring (SOC-247, TCK-20260824-RELATIONSHIP-ROLE-FIELD)
# ---------------------------------------------------------------------------


def test_party_composition_score_reflects_candidate_role():
    pool = [_entity(2, kind="guard"), _entity(3, kind="mage")]

    def _actor(role):
        return _entity(
            1, kind="hero",
            bonds={2: SocialBond(target_id=2, sentiment=0.2, role=role)},
        )

    score_friend = PartyCompositionScorer.score(pool, actor=_actor(RelationshipRole.FRIEND))
    score_neutral = PartyCompositionScorer.score(pool, actor=_actor(RelationshipRole.NEUTRAL))
    score_rival = PartyCompositionScorer.score(pool, actor=_actor(RelationshipRole.RIVAL))

    assert score_friend > score_neutral > score_rival


def test_party_composition_score_role_term_is_zero_for_all_neutral_pool():
    pool = [_entity(2, kind="guard"), _entity(3, kind="mage")]
    actor = _entity(
        1, kind="hero",
        bonds={
            2: SocialBond(target_id=2, role=RelationshipRole.NEUTRAL),
            3: SocialBond(target_id=3, role=RelationshipRole.NEUTRAL),
        },
    )
    assert PartyCompositionScorer.score_role_affinity(actor, pool) == 0.0


def test_party_composition_score_role_term_requires_actor():
    pool = [_entity(2, kind="guard"), _entity(3, kind="mage")]
    actor = _entity(
        1, kind="hero",
        bonds={2: SocialBond(target_id=2, sentiment=0.2, role=RelationshipRole.FRIEND)},
    )

    score_with_actor = PartyCompositionScorer.score(pool, actor=actor)
    score_without_actor = PartyCompositionScorer.score(pool)

    role_div = PartyCompositionScorer.score_role_diversity(pool)
    ocean_compat = PartyCompositionScorer.score_ocean_compatibility(pool)
    base_score = round(
        PartyCompositionScorer.ROLE_DIVERSITY_WEIGHT * role_div
        + PartyCompositionScorer.OCEAN_COMPAT_WEIGHT * ocean_compat,
        4,
    )

    assert score_without_actor == base_score
    assert score_with_actor != score_without_actor


# ---------------------------------------------------------------------------
# nemesis_ids / RelationshipRole precedence (TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE)
# ---------------------------------------------------------------------------

def test_candidate_role_value_nemesis_overrides_stale_friend_bond():
    """A candidate who is both a confirmed nemesis (grudge-promoted) and still tagged
    FRIEND on the bond must score as a nemesis (-1.0), not a friend (+1.0) -- nemesis_ids
    is the stronger, harm-history-backed signal."""
    candidate = _entity(2, kind="guard")
    actor = _entity(
        1, kind="hero",
        bonds={2: SocialBond(target_id=2, sentiment=0.5, role=RelationshipRole.FRIEND)},
        nemesis_ids={2},
    )
    assert PartyCompositionScorer._candidate_role_value(actor, candidate) == -1.0


def test_candidate_role_value_nemesis_without_bond():
    """A nemesis with no bond record at all still scores -1.0, not the no-bond default 0.0."""
    candidate = _entity(2, kind="guard")
    actor = _entity(1, kind="hero", nemesis_ids={2})
    assert PartyCompositionScorer._candidate_role_value(actor, candidate) == -1.0


def test_candidate_role_value_non_conflicting_cases_unchanged():
    """Non-conflicting cases (FRIEND alone, RIVAL alone, NEUTRAL, no bond) are unaffected
    by the nemesis_ids precedence check."""
    candidate = _entity(2, kind="guard")

    friend_actor = _entity(1, bonds={2: SocialBond(target_id=2, role=RelationshipRole.FRIEND)})
    assert PartyCompositionScorer._candidate_role_value(friend_actor, candidate) == 1.0

    rival_actor = _entity(1, bonds={2: SocialBond(target_id=2, role=RelationshipRole.RIVAL)})
    assert PartyCompositionScorer._candidate_role_value(rival_actor, candidate) == -1.0

    neutral_actor = _entity(1, bonds={2: SocialBond(target_id=2, role=RelationshipRole.NEUTRAL)})
    assert PartyCompositionScorer._candidate_role_value(neutral_actor, candidate) == 0.0

    no_bond_actor = _entity(1)
    assert PartyCompositionScorer._candidate_role_value(no_bond_actor, candidate) == 0.0


def test_party_composition_score_lower_for_nemesis_with_friend_bond_than_true_friend():
    """End-to-end via score(): a nemesis-with-stale-FRIEND-bond actor scores lower than an
    actor with a genuine FRIEND bond toward the same candidate pool shape."""
    pool = [_entity(2, kind="guard"), _entity(3, kind="mage")]

    true_friend_actor = _entity(
        1, bonds={2: SocialBond(target_id=2, sentiment=0.5, role=RelationshipRole.FRIEND)},
    )
    nemesis_with_friend_tag_actor = _entity(
        1, bonds={2: SocialBond(target_id=2, sentiment=0.5, role=RelationshipRole.FRIEND)},
        nemesis_ids={2},
    )

    score_true_friend = PartyCompositionScorer.score(pool, actor=true_friend_actor)
    score_nemesis = PartyCompositionScorer.score(pool, actor=nemesis_with_friend_tag_actor)

    assert score_nemesis < score_true_friend


def test_form_party_route_blocked_by_canonical_nemesis_ids_without_strategic_blocker():
    """FORM_PARTY's own nemesis-block check must fire from the canonical nemesis_ids field
    alone, even with zero matching strategic.blockers entries (the gap this ticket closes --
    previously only the strategic-blocker proxy was checked)."""
    from src.domains.adventure.generator import AdventureRouteGenerator
    from src.domains.adventure.schema import RouteFamily
    from src.core.state import AuthoritativeState

    nemesis_candidate = _entity(2, kind="guard")
    entity = _entity(1, kind="hero", sociability=0.8, nemesis_ids={2})
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity, 2: nemesis_candidate})

    routes = AdventureRouteGenerator.generate(entity, state=state, opportunities=())
    form_party = next((r for r in routes if r.family == RouteFamily.FORM_PARTY), None)

    assert form_party is not None
    assert "nemesis_block" in form_party.blockers
