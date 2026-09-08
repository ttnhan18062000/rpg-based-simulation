"""
tests/unit/engine/test_campaign_bridge_fields_state_hash_coverage.py

TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE

Regression coverage: CanonicalStateHasher.to_canonical_data() must include the 6
AuthoritativeState fields the Dormant Mechanism Closure epic added
(region_loyalty_pressure, region_culture_states, entity_legend_facts,
information_source_profiles, entity_belief_institutions, event_fidelity). Confirmed via
direct reproduction (before this ticket's fix) that two states differing ONLY in one of
these 6 fields produced identical hashes -- a real determinism-verification gap, not a
benign omission: these fields feed into AdventureRouteScorer.score()'s personality_bias,
but personality_bias's own contribution is not guaranteed to flip any entity's resulting
decision/state on the same tick it changes (a small bias delta can leave the same route
family selected), so a real divergence in one of these fields could silently escape
detection at a certification/replay checkpoint that relies on final_state_hash.
"""
from __future__ import annotations

from src.core.state import AuthoritativeState
from src.domains.belief_institution.model import BeliefInstitution
from src.domains.culture.model import CultureState
from src.domains.fame.legend import LegendFact
from src.domains.information.schema import InformationSourceProfile
from src.engine.checkpoint import CanonicalStateHasher


def _base_state() -> AuthoritativeState:
    return AuthoritativeState(tick=0, seed=42, entities={})


def test_identical_states_still_hash_identically():
    h1 = CanonicalStateHasher.get_hash(_base_state())
    h2 = CanonicalStateHasher.get_hash(_base_state())
    assert h1 == h2


def test_region_loyalty_pressure_difference_changes_hash():
    baseline = CanonicalStateHasher.get_hash(_base_state())
    diverged = CanonicalStateHasher.get_hash(
        AuthoritativeState(tick=0, seed=42, entities={}, region_loyalty_pressure={"r1": 5.0})
    )
    assert baseline != diverged


def test_region_culture_states_difference_changes_hash():
    baseline = CanonicalStateHasher.get_hash(_base_state())
    diverged = CanonicalStateHasher.get_hash(
        AuthoritativeState(
            tick=0, seed=42, entities={},
            region_culture_states={"r1": CultureState(fatalism=0.5)},
        )
    )
    assert baseline != diverged


def test_entity_legend_facts_difference_changes_hash():
    baseline = CanonicalStateHasher.get_hash(_base_state())
    diverged = CanonicalStateHasher.get_hash(
        AuthoritativeState(
            tick=0, seed=42, entities={},
            entity_legend_facts={"1": LegendFact(subject_id="1", fame=0.9)},
        )
    )
    assert baseline != diverged


def test_information_source_profiles_difference_changes_hash():
    baseline = CanonicalStateHasher.get_hash(_base_state())
    diverged = CanonicalStateHasher.get_hash(
        AuthoritativeState(
            tick=0, seed=42, entities={},
            information_source_profiles=[
                InformationSourceProfile(
                    source_id="s1", source_kind="guide",
                    knowledge_scopes=("x",), accuracy=0.5, freshness=0.5,
                )
            ],
        )
    )
    assert baseline != diverged


def test_information_source_profiles_hash_is_insertion_order_independent():
    """The field is a List[InformationSourceProfile] with no natural key -- the canonical
    hash must sort it internally so two semantically-identical-but-differently-ordered
    lists still produce the same hash (matching every other collection's own sorted()
    discipline in to_canonical_data())."""
    p1 = InformationSourceProfile(
        source_id="s1", source_kind="guide", knowledge_scopes=("x",),
        accuracy=0.5, freshness=0.5,
    )
    p2 = InformationSourceProfile(
        source_id="s2", source_kind="guild", knowledge_scopes=("y",),
        accuracy=0.6, freshness=0.6,
    )
    state_a = AuthoritativeState(
        tick=0, seed=42, entities={}, information_source_profiles=[p1, p2]
    )
    state_b = AuthoritativeState(
        tick=0, seed=42, entities={}, information_source_profiles=[p2, p1]
    )
    assert CanonicalStateHasher.get_hash(state_a) == CanonicalStateHasher.get_hash(state_b)


def test_entity_belief_institutions_difference_changes_hash():
    baseline = CanonicalStateHasher.get_hash(_base_state())
    diverged = CanonicalStateHasher.get_hash(
        AuthoritativeState(
            tick=0, seed=42, entities={},
            entity_belief_institutions={
                1: (
                    BeliefInstitution(
                        origin_event_id="e1", clan_id="c1",
                        adherent_entity_ids=(1, 2), belief_strength=0.7,
                    ),
                )
            },
        )
    )
    assert baseline != diverged


def test_event_fidelity_difference_changes_hash():
    baseline = CanonicalStateHasher.get_hash(_base_state())
    diverged = CanonicalStateHasher.get_hash(
        AuthoritativeState(tick=0, seed=42, entities={}, event_fidelity={"e1": 0.5})
    )
    assert baseline != diverged
