"""
tests/unit/domains/adventure/test_eligibility_cognition_profile.py

TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY — cognition-profile-driven adventure
eligibility. Migrated by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (plan.md Step 5 item 2):
_resolve_cognition_profile_id/_supports_adventure_routing relocated from the deleted
AdventureDecisionPhase.apply() into src.ai.goals.adventure_scorer, exercised directly here
against a caller-supplied cache dict rather than through apply()'s own per-call cache.
Covers: non-hero-role inclusion, hero-role-but-ineligible-profile exclusion, the real-corpus
cognition_profile_id-missing fallback, and per-call catalog-lookup caching.
"""

from __future__ import annotations

import pytest

from src.ai.goals.adventure_scorer import _supports_adventure_routing
from src.core.builder import V2EntityBuilder


def test_eligibility_resolves_via_cognition_profile_not_role():
    """A non-HERO-role entity (CITIZEN=3) with an explicit cognition_profile_id resolving to
    supports_adventure_routing=True is included -- proving eligibility is now profile-driven,
    not role-driven."""
    b = V2EntityBuilder(1)
    b.identity(role=3, properties={"cognition_profile_id": "practical_humanoid"})  # CITIZEN
    entity = b.build()

    assert _supports_adventure_routing(entity, {}) is True


def test_hero_role_with_ineligible_profile_excluded():
    """A HERO-role entity whose cognition_profile_id is explicitly overridden to
    instinctive_animal (supports_adventure_routing=False) is excluded -- the negative case named
    explicitly in the ticket's AC. Uses an explicit Tier-1 override rather than relying on any
    fallback tier, since the Tier-3 fallback for role_id-absent HERO entities always resolves to
    practical_humanoid/True, which would make this test pass for the wrong reason otherwise."""
    b = V2EntityBuilder(1)
    b.identity(role=0, properties={"cognition_profile_id": "instinctive_animal"})  # HERO
    entity = b.build()

    assert _supports_adventure_routing(entity, {}) is False


def test_cognition_profile_id_missing_does_not_crash():
    """A HERO-role entity with no cognition_profile_id key and an explicitly-None role_id in
    identity.properties (matching WorldEntitySpawner._spawn_legacy_guard's real output shape,
    the confirmed real-corpus gap in investigation.md Risk 1) resolves deterministically via the
    Tier-3 EntityRole.HERO -> 'hero' role default fallback (practical_humanoid, eligible) instead
    of raising KeyError/AttributeError or silently defaulting to ineligible."""
    b = V2EntityBuilder(1)
    b.identity(role=0, properties={"role_id": None})  # HERO, no cognition_profile_id key
    entity = b.build()

    assert _supports_adventure_routing(entity, {}) is True


def test_cognition_profile_id_resolution_is_cached_not_reloaded_per_hero(monkeypatch):
    """The catalog lookup used to resolve CognitionProfileDefinition is invoked at most once per
    distinct cognition_profile_id encountered while sharing one cache dict across calls, not
    once per hero -- closes the ticket's AC bullet on cheap/cached per-tick resolution."""
    import src.ai.goals.adventure_scorer as scorer_module

    class _FakeProfile:
        supports_adventure_routing = True

    call_count = {"n": 0}

    def _counting_getter(profile_id):
        call_count["n"] += 1
        return _FakeProfile()

    monkeypatch.setattr(scorer_module, "get_cognition_profile_definition", _counting_getter)

    entities = []
    for i in range(1, 6):
        b = V2EntityBuilder(i)
        b.identity(role=3, properties={"cognition_profile_id": "practical_humanoid"})
        entities.append(b.build())

    cache: dict = {}
    for entity in entities:
        _supports_adventure_routing(entity, cache)

    assert call_count["n"] == 1, (
        f"expected exactly 1 catalog lookup for 5 heroes sharing one cognition_profile_id, "
        f"got {call_count['n']}"
    )
