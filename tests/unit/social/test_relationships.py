"""
Social relationship and reputation tests.
- RPG-0056: social_reputation_vs_meaning
"""
import pytest
from src.core.state import AuthoritativeState
from src.core.models.social import RelationshipRole
from src.core.updates import EntityUpdate, SocialUpdate, SocialBondUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.systems.social_systems.relationships import RelationshipService

def test_relationship_familiarity_gain():
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Increase familiarity with entity 99
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(familiarity_delta={99: 0.1})
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    assert social.familiarity_history[99] == 0.1

def test_relationship_trust_evidence():
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Increase trust with entity 99
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(trust_delta={99: 0.5})
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    assert social.trust_history[99] == 0.5

def test_relationship_debt_and_fear():
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Increase debt and fear with entity 99
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(debt_delta={99: 0.3}, fear_delta={99: 0.2})
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    assert social.debt_history[99] == 0.3
    assert social.fear_history[99] == 0.2

def test_public_reputation_impact():
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Perform heroic deed
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(heroism_delta=0.5)
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    assert social.heroism_score == 0.5
    assert social.public_reputation == 1.5 # Base 1.0 + 0.5

def test_relationship_salience_pruning():
    from src.systems.social_systems.relationships import RelationshipService
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
    
    # Add two entities: one salient, one not
    update = EntityUpdate(
        entity_id=1,
        social=SocialUpdate(
            salience_delta={10: 0.1, 20: 0.01},
            trust_delta={10: 0.5, 20: 0.5}
        )
    )
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    social = new_state.entities[1].social
    
    # Prune
    pruned_social = RelationshipService.prune_low_salience(social, threshold=0.05)
    
    assert 10 in pruned_social.trust_history
    assert 20 not in pruned_social.trust_history
    assert 10 in pruned_social.salience_history
    assert 20 not in pruned_social.salience_history


def test_social_bond_role_set_via_authoritative_update_only():
    """
    Logic ID: SOC-217/SOC-247. role can only be set through SocialBondUpdate.role_set
    -> RelationshipService.process_update(), the sole authoritative apply path.
    """
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, role_set=RelationshipRole.RIVAL)]
    )
    new_social = RelationshipService.process_update(entity.social, update)

    assert new_social.bonds[99].role == RelationshipRole.RIVAL


def test_process_update_role_set_none_preserves_existing_role():
    """
    A None role_set is a no-op for role -- it leaves the existing bond's role
    untouched, exactly like last_interaction_tick_set. Logic ID: SOC-247.
    """
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    first_update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, role_set=RelationshipRole.FRIEND)]
    )
    social_after_first = RelationshipService.process_update(entity.social, first_update)
    assert social_after_first.bonds[99].role == RelationshipRole.FRIEND

    second_update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, familiarity_delta=0.1)]
    )
    social_after_second = RelationshipService.process_update(social_after_first, second_update)

    assert social_after_second.bonds[99].role == RelationshipRole.FRIEND
    assert social_after_second.bonds[99].familiarity == pytest.approx(0.1)


def test_public_reputation_locality_differs_by_region_after_region_scoped_event():
    """
    TCK-20260904-REPUTATION-LOCALITY-SCOPE (AC #2): a region-scoped reputation-affecting
    event updates SocialComponent.regional_reputation[region_id] independently of the
    retained global scalar. Two reads at different regions diverge after only one region
    receives an event; the untouched region and the global scalar keep their defaults.
    """
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    update = SocialUpdate(regional_reputation_delta={"region_a": 0.5})
    new_social = RelationshipService.process_update(entity.social, update)

    assert new_social.regional_reputation["region_a"] == pytest.approx(0.5)
    assert new_social.regional_reputation.get("region_b", 0.0) == 0.0
    assert new_social.regional_reputation["region_a"] != new_social.regional_reputation.get("region_b", 0.0)
    # The retained global scalar is unaffected by a region-scoped delta.
    assert new_social.public_reputation == 1.0


def test_regional_reputation_delta_clamped_to_public_reputation_range():
    """Regional reputation clamps to [0.0, 2.0], matching public_reputation's own clamp."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    over_update = SocialUpdate(regional_reputation_delta={"region_a": 5.0})
    over_social = RelationshipService.process_update(entity.social, over_update)
    assert over_social.regional_reputation["region_a"] == pytest.approx(2.0)

    under_update = SocialUpdate(regional_reputation_delta={"region_a": -5.0})
    under_social = RelationshipService.process_update(over_social, under_update)
    assert under_social.regional_reputation["region_a"] == pytest.approx(0.0)


def test_regional_reputation_delta_merges_by_summing_per_region():
    """SocialUpdate.merge() sums regional_reputation_delta by key, mirroring
    place_attachment_delta's existing merge rule."""
    first = SocialUpdate(regional_reputation_delta={"region_a": 0.2})
    second = SocialUpdate(regional_reputation_delta={"region_a": 0.1, "region_b": 0.3})

    merged = first.merge(second)

    assert merged.regional_reputation_delta["region_a"] == pytest.approx(0.3)
    assert merged.regional_reputation_delta["region_b"] == pytest.approx(0.3)
    # Existing composition rules for reputation_set/heroism_delta/notoriety_delta unchanged.
    reputation_merge = SocialUpdate(reputation_set=1.2).merge(SocialUpdate(reputation_set=1.8))
    assert reputation_merge.reputation_set == 1.8
    heroism_merge = SocialUpdate(heroism_delta=0.1).merge(SocialUpdate(heroism_delta=0.2))
    assert heroism_merge.heroism_delta == pytest.approx(0.3)


def test_heroism_and_notoriety_deltas_apply_identically_to_birth_seeded_reputation():
    """TCK-20260904-INHERITED-REPUTATION-SEED (AC4): a birth-seeded public_reputation value
    (simulated here via V2EntityBuilder's construction-time seed, standing in for
    birth_record()'s own seed write) moves by the exact same heroism_delta/notoriety_delta
    amount as the SocialComponent class default -- proving process_update() has no
    floor/ceiling/persistence special-cased to birth-seed origin, and that this ticket adds
    zero new decay logic to RelationshipService.process_update()."""
    birth_seeded = V2EntityBuilder(entity_id=1).identity(role=0).social(public_reputation=0.6).build()
    default_seeded = V2EntityBuilder(entity_id=2).identity(role=0).build()
    assert default_seeded.social.public_reputation == 1.0

    heroism_update = SocialUpdate(heroism_delta=0.2)
    birth_seeded_after = RelationshipService.process_update(birth_seeded.social, heroism_update)
    default_after = RelationshipService.process_update(default_seeded.social, heroism_update)

    assert birth_seeded_after.public_reputation == pytest.approx(0.8)
    assert default_after.public_reputation == pytest.approx(1.2)
    assert (birth_seeded_after.public_reputation - birth_seeded.social.public_reputation) == pytest.approx(
        default_after.public_reputation - default_seeded.social.public_reputation
    )

    notoriety_update = SocialUpdate(notoriety_delta=0.15)
    birth_seeded_notoriety = RelationshipService.process_update(birth_seeded_after, notoriety_update)
    default_notoriety = RelationshipService.process_update(default_after, notoriety_update)

    assert (birth_seeded_notoriety.public_reputation - birth_seeded_after.public_reputation) == pytest.approx(
        default_notoriety.public_reputation - default_after.public_reputation
    )


def test_sustained_positive_sentiment_derives_role_to_friend():
    """TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH (SOC-248): a real sentiment_delta crossing
    the FRIEND_SENTIMENT_THRESHOLD (0.8) through the authoritative apply-path -- not an
    explicit role_set -- derives role to FRIEND. This is the real, live production trigger
    (fires wherever sentiment_delta already flows today: contracts.py, combat.py,
    appraisal.py), unlike role_set which has zero real (non-test) callers."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, sentiment_delta=0.85)]
    )
    new_social = RelationshipService.process_update(entity.social, update)

    assert new_social.bonds[99].sentiment == pytest.approx(0.85)
    assert new_social.bonds[99].role == RelationshipRole.FRIEND


def test_sustained_negative_sentiment_derives_role_to_rival():
    """SOC-248: the mirror-negative case, reusing appraisal.py's own real TOTAL_DISTRUST
    bound (bond.sentiment < -0.8) as RIVAL_SENTIMENT_THRESHOLD."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, sentiment_delta=-0.85)]
    )
    new_social = RelationshipService.process_update(entity.social, update)

    assert new_social.bonds[99].sentiment == pytest.approx(-0.85)
    assert new_social.bonds[99].role == RelationshipRole.RIVAL


def test_mid_band_sentiment_change_does_not_derive_a_role():
    """SOC-248: a real sentiment_delta that does not cross either extreme leaves role at
    its NEUTRAL default -- this is not a tautology, since a naive implementation could
    derive role on every bond_update regardless of magnitude."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, sentiment_delta=0.3)]
    )
    new_social = RelationshipService.process_update(entity.social, update)

    assert new_social.bonds[99].sentiment == pytest.approx(0.3)
    assert new_social.bonds[99].role == RelationshipRole.NEUTRAL


def test_derived_friend_role_is_not_demoted_by_a_later_mid_band_sentiment_update():
    """SOC-248: once derived (not just explicitly role_set), a promotion is sticky against
    a later sentiment_delta that lands back in the mid-band -- a regression-catching
    assertion that a naive "always re-derive from current sentiment" implementation would
    fail (it would silently reset role to NEUTRAL on the second update below)."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    first_update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, sentiment_delta=0.9)]
    )
    social_after_first = RelationshipService.process_update(entity.social, first_update)
    assert social_after_first.bonds[99].role == RelationshipRole.FRIEND

    second_update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, sentiment_delta=-0.3)]
    )
    social_after_second = RelationshipService.process_update(social_after_first, second_update)

    assert social_after_second.bonds[99].sentiment == pytest.approx(0.6)
    assert social_after_second.bonds[99].role == RelationshipRole.FRIEND


def test_extreme_negative_sentiment_can_flip_an_existing_friend_role_to_rival():
    """SOC-248: unlike nemesis_ids' own one-way-only promotion, a role derivation is not
    one-way across the FRIEND/RIVAL boundary itself -- a real, extreme sentiment reversal
    (e.g. a betrayal) can flip an existing FRIEND bond to RIVAL, since both are derived from
    the same live sentiment signal, not independently latched flags."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    first_update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, sentiment_delta=0.9)]
    )
    social_after_first = RelationshipService.process_update(entity.social, first_update)
    assert social_after_first.bonds[99].role == RelationshipRole.FRIEND

    second_update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, sentiment_delta=-1.8)]
    )
    social_after_second = RelationshipService.process_update(social_after_first, second_update)

    assert social_after_second.bonds[99].sentiment == pytest.approx(-0.9)
    assert social_after_second.bonds[99].role == RelationshipRole.RIVAL


def test_explicit_role_set_overrides_a_contradicting_derived_sentiment():
    """SOC-248: an explicit role_set still takes priority over the sentiment-derivation
    even when they'd disagree -- role_set remains a real, honored override, not dead
    scaffolding replaced outright by the new derivation."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, sentiment_delta=0.9, role_set=RelationshipRole.RIVAL)]
    )
    new_social = RelationshipService.process_update(entity.social, update)

    assert new_social.bonds[99].sentiment == pytest.approx(0.9)
    assert new_social.bonds[99].role == RelationshipRole.RIVAL


def test_zero_sentiment_delta_bond_update_does_not_touch_role():
    """SOC-248: a bond_update with sentiment_delta left at its 0.0 default (e.g. a pure
    familiarity or last_interaction_tick touch) must not evaluate role derivation at all --
    this is TCK-20260824-RELATIONSHIP-ROLE-FIELD's own established
    test_process_update_role_set_none_preserves_existing_role guarantee, re-asserted here
    directly against the new derivation code path added by this ticket."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()

    first_update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, sentiment_delta=0.9)]
    )
    social_after_first = RelationshipService.process_update(entity.social, first_update)
    assert social_after_first.bonds[99].role == RelationshipRole.FRIEND

    second_update = SocialUpdate(
        bond_updates=[SocialBondUpdate(target_id=99, familiarity_delta=0.1)]
    )
    social_after_second = RelationshipService.process_update(social_after_first, second_update)

    assert social_after_second.bonds[99].role == RelationshipRole.FRIEND
    assert social_after_second.bonds[99].familiarity == pytest.approx(0.1)
