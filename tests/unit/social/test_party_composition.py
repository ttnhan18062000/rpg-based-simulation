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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid: int, kind: str = "hero", bravery: float = 0.5, sociability: float = 0.5):
    from src.core.builder import V2EntityBuilder
    entity = (
        V2EntityBuilder(eid)
        .kind(kind)
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
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
