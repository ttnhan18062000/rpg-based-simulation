"""Tests for BeliefInstitution/BeliefInstitutionCarryForward round-trip (idea 63, AC2)."""

from src.domains.belief_institution.model import BeliefInstitution, BeliefInstitutionCarryForward


def test_belief_institution_round_trip_serialization():
    inst = BeliefInstitution(
        origin_event_id="0:1:entity_death:hero_1",
        clan_id="clan_a",
        adherent_entity_ids=(1, 2, 3),
        belief_strength=0.85,
    )
    d = inst.to_dict()
    restored = BeliefInstitution.from_dict(d)
    assert restored == inst


def test_belief_institution_carry_forward_round_trip_serialization():
    inst = BeliefInstitution(
        origin_event_id="0:1:entity_death:hero_1",
        clan_id="clan_a",
        adherent_entity_ids=(1, 2),
        belief_strength=0.5,
    )
    cf = BeliefInstitutionCarryForward(key="clan_a:0:1:entity_death:hero_1", institution=inst, derived_episode=3)
    d = cf.to_dict()
    restored = BeliefInstitutionCarryForward.from_dict(d)
    assert restored == cf


def test_belief_institution_default_belief_strength_is_zero():
    inst = BeliefInstitution(origin_event_id="e1", clan_id="c1", adherent_entity_ids=())
    assert inst.belief_strength == 0.0
