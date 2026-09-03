import pytest
from dataclasses import replace
from src.core.state import EntityState, LifecycleComponent, AuthoritativeState, CombatComponent, LifeStage, RegionState
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate, InventoryUpdate, LifecycleUpdate
from src.systems.lifecycle import LifecycleSystem
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder, build_parent_bond_updates_for_birth
from src.core.enums import EntityRole, Faction
from src.core.models.social import SocialBond, RelationshipRole
from src.domains.world_emergence.schema import WorldEventCategory

def test_aging_per_tick():
    """Verify that entities age by 1 tick every generation."""
    ent = (V2EntityBuilder(1)
           .location(0.0, 0.0)
           .lifecycle(age_ticks=50)
           .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})
    
    update = StateUpdate()
    next_state = ApplyPath.apply_generation(state, update, 101, 101)
    
    assert next_state.entities[1].lifecycle.age_ticks == 51

def test_death_by_old_age():
    """Verify that reaching max age triggers death."""
    # Note: V2EntityBuilder doesn't have max_age_ticks setter, we use replace for now
    ent = (V2EntityBuilder(1)
           .location(0.0, 0.0)
           .lifecycle(age_ticks=1000)
           .build())
    ent = replace(ent, lifecycle=replace(ent.lifecycle, max_age_ticks=1000))
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})
    
    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)
    
    ent_upd = refined.entity_updates[1]
    assert ent_upd.active is False
    assert ent_upd.lifecycle.death_reason_set == "OLD_AGE"
    assert ent_upd.lifecycle.is_permadeath_set is True

def test_combat_death_classification():
    """Verify that a KILL outcome is classified as a lifecycle death."""
    ent = (V2EntityBuilder(1)
           .location(0.0, 0.0)
           .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})
    
    # Simulate a KILL outcome from combat
    kill_upd = CombatUpdate(outcome_kind="KILL", is_lethal=True)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=kill_upd)})
    
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    ent_upd = refined.entity_updates[1]
    assert ent_upd.active is False
    assert ent_upd.lifecycle.death_reason_set == "COMBAT"

def test_permadeath_death_classification():
    """A PERMADEATH outcome (a rebirth-eligible Hero at generation cap, src/engine/combat.py)
    must deactivate the entity the same as a KILL outcome -- regression for a real bug where
    resolve_lifecycle only checked outcome_kind=="KILL", leaving a "permanently dead" Hero
    active=True and still acting."""
    ent = (V2EntityBuilder(1)
           .location(0.0, 0.0)
           .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent})

    permadeath_upd = CombatUpdate(outcome_kind="PERMADEATH", is_lethal=True)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=permadeath_upd)})

    refined = LifecycleSystem.resolve_lifecycle(state, update)

    ent_upd = refined.entity_updates[1]
    assert ent_upd.active is False
    assert ent_upd.lifecycle.death_reason_set == "COMBAT"
    assert ent_upd.lifecycle.is_permadeath_set is True

def test_succession_and_heirloom_transfer():
    """Verify that heirlooms are transferred to the heir upon death."""
    # Build parent with heir and heirlooms
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .build())
    parent_life = LifecycleComponent(
        age_ticks=100, max_age_ticks=100, 
        heir_entity_id=2, 
        heirlooms=["Excalibur"]
    )
    parent = replace(parent, lifecycle=parent_life)
    
    heir = (V2EntityBuilder(2)
            .location(1.0, 1.0)
            .build())
    
    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: heir})
    
    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)
    
    # Heir should receive the item via transaction
    heir_upd = refined.entity_updates[2]
    assert len(heir_upd.resource_transfers) > 0
    transfer = heir_upd.resource_transfers[0]
    assert any(stack.item_id == "Excalibur" for stack in transfer.items_add)

    # Logic ID: STRAT-142

    # Logic ID: SOC-042

    # Logic ID: SOC-042

def test_manual_heir_entity_id_transfers_even_if_heir_inactive():
    """The pre-existing manual-heir-transfer liveness check only tests existence, not
    .lifecycle.active -- default-heir selection's stricter filter must not have tightened
    this pre-existing behavior."""
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .build())
    parent_life = LifecycleComponent(
        age_ticks=100, max_age_ticks=100,
        heir_entity_id=2,
        heirlooms=["Excalibur"]
    )
    parent = replace(parent, lifecycle=parent_life)

    heir = (V2EntityBuilder(2)
            .location(1.0, 1.0)
            .lifecycle(active=False)
            .build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: heir})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    heir_upd = refined.entity_updates[2]
    assert len(heir_upd.resource_transfers) > 0
    transfer = heir_upd.resource_transfers[0]
    assert any(stack.item_id == "Excalibur" for stack in transfer.items_add)

def test_default_heir_selected_from_strongest_bond():
    """When heir_entity_id is None, a default heir is selected from the deceased's live bonds."""
    bond = SocialBond(target_id=2, familiarity=0.8, sentiment=0.5, last_interaction_tick=10)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={2: bond})
              .build())
    parent_life = LifecycleComponent(
        age_ticks=100, max_age_ticks=100,
        heir_entity_id=None,
        heirlooms=["Excalibur"]
    )
    parent = replace(parent, lifecycle=parent_life)

    heir = (V2EntityBuilder(2)
            .location(1.0, 1.0)
            .build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: heir})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    assert refined.entity_updates[1].lifecycle.heir_entity_id_set == 2

    heir_upd = refined.entity_updates[2]
    assert len(heir_upd.resource_transfers) > 0
    transfer = heir_upd.resource_transfers[0]
    assert any(stack.item_id == "Excalibur" for stack in transfer.items_add)

def test_default_heir_prefers_strongest_bond_among_multiple_candidates():
    """The higher-scoring candidate (familiarity=0.9,sentiment=0.0 -> 0.74) is selected over
    a lower-scoring one (familiarity=0.2,sentiment=1.0 -> 0.52)."""
    bond_a = SocialBond(target_id=2, familiarity=0.9, sentiment=0.0, last_interaction_tick=10)
    bond_b = SocialBond(target_id=3, familiarity=0.2, sentiment=1.0, last_interaction_tick=10)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={2: bond_a, 3: bond_b})
              .build())
    parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent = replace(parent, lifecycle=parent_life)

    candidate_a = (V2EntityBuilder(2).location(1.0, 1.0).build())
    candidate_b = (V2EntityBuilder(3).location(2.0, 2.0).build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: candidate_a, 3: candidate_b})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    assert refined.entity_updates[1].lifecycle.heir_entity_id_set == 2

def test_default_heir_zero_bonds_no_heir_assigned():
    """Zero bonds -> no heir assigned, no exception raised."""
    parent = (V2EntityBuilder(1).location(0.0, 0.0).build())
    parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent = replace(parent, lifecycle=parent_life)

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    assert refined.entity_updates[1].lifecycle.heir_entity_id_set is None
    for ent_upd in refined.entity_updates.values():
        assert len(ent_upd.resource_transfers) == 0

def test_default_heir_all_bonded_targets_dead_or_missing_no_heir_assigned():
    """Every bonded target is either present-but-inactive or absent entirely -> no heir assigned."""
    bond_dead = SocialBond(target_id=2, familiarity=0.9, sentiment=0.9, last_interaction_tick=10)
    bond_missing = SocialBond(target_id=3, familiarity=0.9, sentiment=0.9, last_interaction_tick=10)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={2: bond_dead, 3: bond_missing})
              .build())
    parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent = replace(parent, lifecycle=parent_life)

    dead_candidate = (V2EntityBuilder(2)
                       .location(1.0, 1.0)
                       .lifecycle(active=False)
                       .build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: dead_candidate})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    assert refined.entity_updates[1].lifecycle.heir_entity_id_set is None

def test_default_heir_selection_deterministic_across_repeated_calls():
    """Reversed bond-dict insertion order must not change the selected heir."""
    bond_a = SocialBond(target_id=2, familiarity=0.9, sentiment=0.0, last_interaction_tick=10)
    bond_b = SocialBond(target_id=3, familiarity=0.2, sentiment=1.0, last_interaction_tick=10)

    def build_and_run(bonds):
        parent = (V2EntityBuilder(1)
                  .location(0.0, 0.0)
                  .social(bonds=bonds)
                  .build())
        parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
        parent = replace(parent, lifecycle=parent_life)
        candidate_a = (V2EntityBuilder(2).location(1.0, 1.0).build())
        candidate_b = (V2EntityBuilder(3).location(2.0, 2.0).build())
        state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: candidate_a, 3: candidate_b})
        refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
        return refined.entity_updates[1].lifecycle.heir_entity_id_set

    heir_forward = build_and_run({2: bond_a, 3: bond_b})
    heir_reversed = build_and_run({3: bond_b, 2: bond_a})

    assert heir_forward == heir_reversed == 2

def test_default_heir_tie_break_deterministic():
    """Score ties break on highest last_interaction_tick, then lowest target_id."""
    bond_older = SocialBond(target_id=2, familiarity=0.5, sentiment=0.5, last_interaction_tick=5)
    bond_newer = SocialBond(target_id=3, familiarity=0.5, sentiment=0.5, last_interaction_tick=50)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={2: bond_older, 3: bond_newer})
              .build())
    parent_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent = replace(parent, lifecycle=parent_life)
    candidate_a = (V2EntityBuilder(2).location(1.0, 1.0).build())
    candidate_b = (V2EntityBuilder(3).location(2.0, 2.0).build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: candidate_a, 3: candidate_b})
    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
    assert refined.entity_updates[1].lifecycle.heir_entity_id_set == 3

    bond_low_id = SocialBond(target_id=2, familiarity=0.5, sentiment=0.5, last_interaction_tick=10)
    bond_high_id = SocialBond(target_id=3, familiarity=0.5, sentiment=0.5, last_interaction_tick=10)
    parent2 = (V2EntityBuilder(4)
               .location(0.0, 0.0)
               .social(bonds={2: bond_low_id, 3: bond_high_id})
               .build())
    parent2_life = LifecycleComponent(age_ticks=100, max_age_ticks=100, heir_entity_id=None)
    parent2 = replace(parent2, lifecycle=parent2_life)
    state2 = AuthoritativeState(tick=100, seed=42, entities={4: parent2, 2: candidate_a, 3: candidate_b})
    refined2 = LifecycleSystem.resolve_lifecycle(state2, StateUpdate())
    assert refined2.entity_updates[4].lifecycle.heir_entity_id_set == 2

def test_default_heir_does_not_override_manual_heir_entity_id():
    """A manually-set heir_entity_id must win even when a higher-scoring bonded candidate exists."""
    bond_high = SocialBond(target_id=3, familiarity=1.0, sentiment=1.0, last_interaction_tick=999)
    parent = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .social(bonds={3: bond_high})
              .build())
    parent_life = LifecycleComponent(
        age_ticks=100, max_age_ticks=100,
        heir_entity_id=2,
        heirlooms=["Excalibur"]
    )
    parent = replace(parent, lifecycle=parent_life)

    heir = (V2EntityBuilder(2).location(1.0, 1.0).build())
    other_candidate = (V2EntityBuilder(3).location(2.0, 2.0).build())

    state = AuthoritativeState(tick=100, seed=42, entities={1: parent, 2: heir, 3: other_candidate})

    update = StateUpdate()
    refined = LifecycleSystem.resolve_lifecycle(state, update)

    heir_upd = refined.entity_updates[2]
    assert len(heir_upd.resource_transfers) > 0
    transfer = heir_upd.resource_transfers[0]
    assert any(stack.item_id == "Excalibur" for stack in transfer.items_add)

    assert 3 not in refined.entity_updates or len(refined.entity_updates[3].resource_transfers) == 0

    life_upd = refined.entity_updates[1].lifecycle
    assert life_upd.heir_entity_id_set in (None, 2)

def test_life_stage_flips_at_age_boundary():
    """TCK-20260824-LIFE-STAGE-TRANSITIONS: age_ticks=6999 must not transition; age_ticks=7000
    (the boundary, inclusive per get_age_bracket()'s numeric law) must transition to ELDER."""
    below_boundary = (V2EntityBuilder(1)
                       .location(0.0, 0.0)
                       .identity(life_stage=LifeStage.ADULT)
                       .lifecycle(age_ticks=6999, max_age_ticks=100000)
                       .build())
    state_below = AuthoritativeState(tick=100, seed=42, entities={1: below_boundary})
    refined_below = LifecycleSystem.resolve_lifecycle(state_below, StateUpdate())
    ent_upd_below = refined_below.entity_updates.get(1)
    assert ent_upd_below is None or ent_upd_below.identity is None or ent_upd_below.identity.life_stage_set is None

    at_boundary = (V2EntityBuilder(1)
                   .location(0.0, 0.0)
                   .identity(life_stage=LifeStage.ADULT)
                   .lifecycle(age_ticks=7000, max_age_ticks=100000)
                   .build())
    state_at = AuthoritativeState(tick=100, seed=42, entities={1: at_boundary})
    refined_at = LifecycleSystem.resolve_lifecycle(state_at, StateUpdate())
    ent_upd_at = refined_at.entity_updates[1]
    assert ent_upd_at.identity.life_stage_set == LifeStage.ELDER


def test_life_stage_transition_is_monotonic_forward_only():
    """An already-ADULT entity at age_ticks=0 (a construction-time bookkeeping default, not a
    literal newborn fact) must NOT be demoted to CHILD. A CHILD entity correctly promotes to
    ADULT at 3000 and to ELDER at 7000."""
    already_adult = (V2EntityBuilder(1)
                      .location(0.0, 0.0)
                      .identity(life_stage=LifeStage.ADULT)
                      .lifecycle(age_ticks=0, max_age_ticks=100000)
                      .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: already_adult})
    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
    ent_upd = refined.entity_updates.get(1)
    assert ent_upd is None or ent_upd.identity is None or ent_upd.identity.life_stage_set is None

    child = (V2EntityBuilder(2)
             .location(0.0, 0.0)
             .identity(life_stage=LifeStage.CHILD)
             .lifecycle(age_ticks=0, max_age_ticks=100000)
             .build())

    state_child_at_0 = AuthoritativeState(tick=100, seed=42, entities={2: child})
    refined_at_0 = LifecycleSystem.resolve_lifecycle(state_child_at_0, StateUpdate())
    ent_upd_at_0 = refined_at_0.entity_updates.get(2)
    assert ent_upd_at_0 is None or ent_upd_at_0.identity is None or ent_upd_at_0.identity.life_stage_set is None

    child_at_3000 = replace(child, lifecycle=replace(child.lifecycle, age_ticks=3000))
    state_at_3000 = AuthoritativeState(tick=100, seed=42, entities={2: child_at_3000})
    refined_at_3000 = LifecycleSystem.resolve_lifecycle(state_at_3000, StateUpdate())
    assert refined_at_3000.entity_updates[2].identity.life_stage_set == LifeStage.ADULT

    child_at_7000 = replace(child, lifecycle=replace(child.lifecycle, age_ticks=7000))
    state_at_7000 = AuthoritativeState(tick=100, seed=42, entities={2: child_at_7000})
    refined_at_7000 = LifecycleSystem.resolve_lifecycle(state_at_7000, StateUpdate())
    assert refined_at_7000.entity_updates[2].identity.life_stage_set == LifeStage.ELDER


def test_coming_of_age_fires_exactly_once_on_child_to_adult_transition():
    """A CITIZEN CHILD crossing the CHILD->ADULT boundary gets exactly one EntityUpdate with
    both life_stage_set == ADULT and role_set in {SHOPKEEPER, WORKER, GUARD} from a single
    resolve_lifecycle() call (TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE)."""
    child = (V2EntityBuilder(1)
             .location(0.0, 0.0)
             .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.CHILD)
             .lifecycle(age_ticks=3000, max_age_ticks=100000,
                        parent_a_entity_id=10, parent_b_entity_id=11, birth_tick=1)
             .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: child})

    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())

    assert len(refined.entity_updates) == 1
    ent_upd = refined.entity_updates[1]
    assert ent_upd.identity.life_stage_set == LifeStage.ADULT
    assert ent_upd.identity.role_set in (EntityRole.SHOPKEEPER, EntityRole.WORKER, EntityRole.GUARD)


def test_coming_of_age_does_not_fire_for_already_adult_or_elder_entities():
    """Re-derivation on a later tick must not re-fire the roll: an entity already ADULT (or
    ELDER) at the start of the tick produces no role_set write from this mechanism."""
    already_adult = (V2EntityBuilder(1)
                      .location(0.0, 0.0)
                      .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.ADULT)
                      .lifecycle(age_ticks=3000, max_age_ticks=100000)
                      .build())
    state_adult = AuthoritativeState(tick=100, seed=42, entities={1: already_adult})
    refined_adult = LifecycleSystem.resolve_lifecycle(state_adult, StateUpdate())
    ent_upd_adult = refined_adult.entity_updates.get(1)
    assert ent_upd_adult is None or ent_upd_adult.identity is None or ent_upd_adult.identity.role_set is None

    already_elder = (V2EntityBuilder(2)
                      .location(0.0, 0.0)
                      .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.ELDER)
                      .lifecycle(age_ticks=7000, max_age_ticks=100000)
                      .build())
    state_elder = AuthoritativeState(tick=100, seed=42, entities={2: already_elder})
    refined_elder = LifecycleSystem.resolve_lifecycle(state_elder, StateUpdate())
    ent_upd_elder = refined_elder.entity_updates.get(2)
    assert ent_upd_elder is None or ent_upd_elder.identity is None or ent_upd_elder.identity.role_set is None


def test_coming_of_age_role_set_uses_authoritative_identity_patch_path():
    """The role_set value is only ever committed through the authoritative apply pipeline
    (ApplyPath.apply_generation), never a direct-mutation shortcut."""
    child = (V2EntityBuilder(1)
             .location(0.0, 0.0)
             .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.CHILD)
             .lifecycle(age_ticks=3000, max_age_ticks=100000,
                        parent_a_entity_id=10, parent_b_entity_id=11, birth_tick=1)
             .build())
    baseline_identity = child.identity
    state = AuthoritativeState(tick=100, seed=42, entities={1: child})

    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
    next_state = ApplyPath.apply_generation(state, refined, 101, 101)

    new_identity = next_state.entities[1].identity
    assert new_identity.role in (EntityRole.SHOPKEEPER, EntityRole.WORKER, EntityRole.GUARD)
    assert new_identity.life_stage == LifeStage.ADULT
    # Baseline entity/component object is untouched -- no direct mutation occurred.
    assert state.entities[1].identity is baseline_identity
    assert baseline_identity.role == EntityRole.CITIZEN


def test_coming_of_age_no_birth_record_exclusion_tracked_or_stubbed():
    """A synthetic construction-default CHILD (no .birth_record() call at all -- birth_tick=0,
    both parent ids None) is excluded from the roll. A Humanoid-path-style CHILD with real
    parent ids and birth_tick=0 is NOT excluded (the false-exclusion regression this ticket's
    investigation identified as a live risk: birth_tick==0 alone is not a safe signal)."""
    no_birth_record_child = (V2EntityBuilder(1)
                              .location(0.0, 0.0)
                              .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.CHILD)
                              .lifecycle(age_ticks=3000, max_age_ticks=100000)
                              .build())
    state_no_record = AuthoritativeState(tick=100, seed=42, entities={1: no_birth_record_child})
    refined_no_record = LifecycleSystem.resolve_lifecycle(state_no_record, StateUpdate())
    ent_upd_no_record = refined_no_record.entity_updates[1]
    assert ent_upd_no_record.identity.life_stage_set == LifeStage.ADULT
    assert ent_upd_no_record.identity.role_set is None

    tick_zero_humanoid_child = (V2EntityBuilder(2)
                                 .location(0.0, 0.0)
                                 .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.CHILD)
                                 .lifecycle(age_ticks=3000, max_age_ticks=100000,
                                            parent_a_entity_id=10, parent_b_entity_id=11, birth_tick=0)
                                 .build())
    state_tick_zero = AuthoritativeState(tick=100, seed=42, entities={2: tick_zero_humanoid_child})
    refined_tick_zero = LifecycleSystem.resolve_lifecycle(state_tick_zero, StateUpdate())
    ent_upd_tick_zero = refined_tick_zero.entity_updates[2]
    assert ent_upd_tick_zero.identity.role_set in (EntityRole.SHOPKEEPER, EntityRole.WORKER, EntityRole.GUARD)


def test_coming_of_age_monster_role_child_role_untouched_on_transition():
    """Regression for the architecture-review finding (2026-09-02): a MONSTER-role CHILD built
    the same way spawn_natural_creature_offspring() does -- parentless but with a real nonzero
    birth_tick -- is NOT excluded by is_excluded_no_birth_record() alone. Only the
    entity.identity.role == EntityRole.CITIZEN gate (plan.md Decision 5) prevents this branch
    from overwriting role_set on an incoherent MONSTER_HORDE-faction entity."""
    monster_child = (V2EntityBuilder(1)
                      .location(0.0, 0.0)
                      .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, life_stage=LifeStage.CHILD)
                      .lifecycle(age_ticks=3000, max_age_ticks=100000,
                                 parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=50)
                      .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: monster_child})

    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
    ent_upd = refined.entity_updates[1]
    assert ent_upd.identity.life_stage_set == LifeStage.ADULT
    assert ent_upd.identity.role_set is None

    next_state = ApplyPath.apply_generation(state, refined, 101, 101)
    assert next_state.entities[1].identity.role == EntityRole.MONSTER


def test_sole_shopkeeper_death_emits_vacancy_event():
    """TCK-20260903-ECONOMIC-VACANCY-SIGNAL: killing the sole living SHOPKEEPER in a region
    through resolve_lifecycle produces a PRODUCTION_ROLE_VACATED WorldEvent in the returned
    StateUpdate.world_events_add, carrying vacated_role and region_id."""
    dying = (V2EntityBuilder(1)
             .location(10.0, 10.0)
             .identity(role=EntityRole.SHOPKEEPER)
             .lifecycle(age_ticks=1000, max_age_ticks=1000)
             .build())
    region = RegionState(id="region_01", name="Test Region", bounds=(0, 0, 100, 100))
    state = AuthoritativeState(tick=100, seed=42, entities={1: dying}, regions={"region_01": region})

    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())

    assert len(refined.world_events_add) == 1
    event = refined.world_events_add[0]
    assert event.category == WorldEventCategory.PRODUCTION_ROLE_VACATED
    assert event.region_id == "region_01"
    assert event.subject == "1"
    assert event.payload == {"vacated_role": float(int(EntityRole.SHOPKEEPER))}


def test_non_sole_occupant_death_does_not_emit_vacancy_event():
    """A region with two living SHOPKEEPERs -- killing one via resolve_lifecycle must NOT emit
    the vacancy event (negative case guarding against a naive "any production-role death"
    implementation that ignores the sole-occupant condition)."""
    dying = (V2EntityBuilder(1)
             .location(10.0, 10.0)
             .identity(role=EntityRole.SHOPKEEPER)
             .lifecycle(age_ticks=1000, max_age_ticks=1000)
             .build())
    surviving_peer = (V2EntityBuilder(2)
                       .location(20.0, 20.0)
                       .identity(role=EntityRole.SHOPKEEPER)
                       .build())
    region = RegionState(id="region_01", name="Test Region", bounds=(0, 0, 100, 100))
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: dying, 2: surviving_peer},
        regions={"region_01": region},
    )

    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())

    assert refined.world_events_add == []


def test_role_and_region_scope_of_sole_occupant_check():
    """Two regions, each with exactly one SHOPKEEPER: killing the one in region_01 via
    resolve_lifecycle emits a vacancy event scoped to region_01 only -- guards against a
    "global role count" misinterpretation of the occupancy check."""
    dying_a = (V2EntityBuilder(1)
               .location(10.0, 10.0)
               .identity(role=EntityRole.SHOPKEEPER)
               .lifecycle(age_ticks=1000, max_age_ticks=1000)
               .build())
    shopkeeper_b = (V2EntityBuilder(2)
                     .location(200.0, 200.0)
                     .identity(role=EntityRole.SHOPKEEPER)
                     .build())
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: dying_a, 2: shopkeeper_b},
        regions={
            "region_01": RegionState(id="region_01", name="Region A", bounds=(0, 0, 100, 100)),
            "region_02": RegionState(id="region_02", name="Region B", bounds=(150, 150, 250, 250)),
        },
    )

    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())

    assert len(refined.world_events_add) == 1
    assert refined.world_events_add[0].region_id == "region_01"
    assert refined.world_events_add[0].subject == "1"


def test_near_death_hardening_logic():
    """Directly test the hardening logic in the pipeline."""
    from src.engine.pipeline import AuthoritativeApplyPipeline
    
    hero = (V2EntityBuilder(1)
            .kind("HERO")
            .location(0.0, 0.0)
            .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100)
            .build())
            
    attacker = (V2EntityBuilder(2)
                .kind("MONSTER")
                .location(1.0, 0.0)
                .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
                .combat(atk=105)
                .combat(readiness=100.0)
                .build())
    
    state = AuthoritativeState(tick=100, seed=42, entities={1: hero, 2: attacker})
    
    # Simulate an attack that would leave hero at low HP
    from src.core.updates import TaskUpdate
    task_upd = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 1})
    update = StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, task=task_upd)})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Hero should have a combat update with max_hp_delta
    hero_upd = refined.entity_updates[1]
    assert hero_upd.combat is not None
    assert hero_upd.combat.max_hp_delta == 5


def test_lifecycle_component_canonical_dict_round_trip_includes_birth_fields():
    """Birth-record fields must serialize deterministically, including the parentless
    (natural-creature/magical) case where parent ids and birth_city_id are None."""
    lifecycle = LifecycleComponent(
        parent_a_entity_id=10,
        parent_b_entity_id=20,
        birth_tick=42,
        birth_city_id=7,
        reproduction_cooldowns={20: 100, 10: 200},
    )
    canonical = lifecycle.to_canonical_dict()
    assert canonical["parent_a_entity_id"] == 10
    assert canonical["parent_b_entity_id"] == 20
    assert canonical["birth_tick"] == 42
    assert canonical["birth_city_id"] == 7
    assert canonical["reproduction_cooldowns"] == {10: 200, 20: 100}
    assert list(canonical["reproduction_cooldowns"].keys()) == [10, 20]

    parentless = LifecycleComponent()
    parentless_canonical = parentless.to_canonical_dict()
    assert parentless_canonical["parent_a_entity_id"] is None
    assert parentless_canonical["parent_b_entity_id"] is None
    assert parentless_canonical["birth_city_id"] is None
    assert parentless_canonical["birth_tick"] == 0
    assert parentless_canonical["reproduction_cooldowns"] == {}


def test_canonical_dict_round_trip_includes_genetic_profile():
    """TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE: genetic_profile must serialize
    deterministically via to_canonical_dict(), including the unset (None) case."""
    from src.systems.lifecycle_systems.genetics import GeneticProfile

    profile = GeneticProfile(strength_mult=1.2, agility_mult=0.9, intelligence_mult=1.1,
                              wisdom_mult=1.0, constitution_mult=0.85, charisma_mult=1.05)
    lifecycle = LifecycleComponent(genetic_profile=profile)
    canonical = lifecycle.to_canonical_dict()
    assert canonical["genetic_profile"] == {
        "strength_mult": 1.2, "agility_mult": 0.9, "intelligence_mult": 1.1,
        "wisdom_mult": 1.0, "constitution_mult": 0.85, "charisma_mult": 1.05,
    }

    unset = LifecycleComponent()
    assert unset.to_canonical_dict()["genetic_profile"] is None


def test_lifecycle_update_merges_birth_fields():
    """New *_set fields participate in is_noop() and merge() with last-non-None-wins
    semantics, matching heir_entity_id_set's existing behavior; reproduction_cooldowns_add
    merges per-key so two same-tick writers updating different partners don't clobber
    each other."""
    assert LifecycleUpdate().is_noop()
    assert not LifecycleUpdate(parent_a_entity_id_set=1).is_noop()
    assert not LifecycleUpdate(birth_tick_set=5).is_noop()
    assert not LifecycleUpdate(reproduction_cooldowns_add={1: 100}).is_noop()

    base = LifecycleUpdate(parent_a_entity_id_set=1, birth_tick_set=5, reproduction_cooldowns_add={10: 100})
    other = LifecycleUpdate(parent_a_entity_id_set=2, parent_b_entity_id_set=3, reproduction_cooldowns_add={20: 200})
    merged = base.merge(other)

    assert merged.parent_a_entity_id_set == 2  # last-non-None-wins
    assert merged.parent_b_entity_id_set == 3
    assert merged.birth_tick_set == 5  # untouched by `other`
    assert merged.reproduction_cooldowns_add == {10: 100, 20: 200}  # per-key union


def test_lifecycle_patch_apply_writes_birth_fields_through_authoritative_path():
    """Birth-record fields are written only via LifecycleUpdate applied through
    ApplyPath.apply_generation (the authoritative apply path) -- never direct mutation."""
    parent = (V2EntityBuilder(1).location(0.0, 0.0).build())
    baseline_lifecycle = parent.lifecycle
    state = AuthoritativeState(tick=100, seed=42, entities={1: parent})

    life_upd = LifecycleUpdate(
        parent_a_entity_id_set=5,
        parent_b_entity_id_set=6,
        birth_tick_set=100,
        birth_city_id_set=3,
        reproduction_cooldowns_add={5: 150},
    )
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, lifecycle=life_upd)})

    next_state = ApplyPath.apply_generation(state, update, 101, 101)

    new_lifecycle = next_state.entities[1].lifecycle
    assert new_lifecycle.parent_a_entity_id == 5
    assert new_lifecycle.parent_b_entity_id == 6
    assert new_lifecycle.birth_tick == 100
    assert new_lifecycle.birth_city_id == 3
    assert new_lifecycle.reproduction_cooldowns == {5: 150}

    # Baseline entity/component object is untouched -- no direct mutation occurred.
    assert state.entities[1].lifecycle is baseline_lifecycle
    assert baseline_lifecycle.parent_a_entity_id is None


def test_builder_birth_record_path_two_parent_case():
    """birth_record() populates all new Lifecycle fields exactly as passed for a two-parent
    birth."""
    child = (V2EntityBuilder(99)
             .location(0.0, 0.0)
             .birth_record(parent_a_entity_id=1, parent_b_entity_id=2, birth_tick=10, birth_city_id=4)
             .build())

    assert child.lifecycle.parent_a_entity_id == 1
    assert child.lifecycle.parent_b_entity_id == 2
    assert child.lifecycle.birth_tick == 10
    assert child.lifecycle.birth_city_id == 4


def test_builder_birth_record_path_parentless_case():
    """A parentless spawn (natural-creature/magical path) must build cleanly with both
    parent fields left None."""
    creature = (V2EntityBuilder(100)
                .location(0.0, 0.0)
                .birth_record(birth_tick=10)
                .build())

    assert creature.lifecycle.parent_a_entity_id is None
    assert creature.lifecycle.parent_b_entity_id is None
    assert creature.lifecycle.birth_tick == 10
    assert creature.lifecycle.birth_city_id is None
    assert creature.social.bonds == {}


def test_builder_birth_record_seeds_child_social_bonds_toward_parents():
    """The two-parent case seeds the child's own SocialBonds toward each parent at the
    documented high familiarity/sentiment (0.8/0.8), role left at its NEUTRAL default."""
    child = (V2EntityBuilder(99)
             .location(0.0, 0.0)
             .birth_record(parent_a_entity_id=1, parent_b_entity_id=2, birth_tick=10)
             .build())

    assert set(child.social.bonds.keys()) == {1, 2}
    for parent_id in (1, 2):
        bond = child.social.bonds[parent_id]
        assert bond.target_id == parent_id
        assert bond.familiarity == 0.8
        assert bond.sentiment == 0.8
        assert bond.last_interaction_tick == 10
        assert bond.role == RelationshipRole.NEUTRAL


def test_parent_bond_updates_for_birth_apply_through_authoritative_path():
    """build_parent_bond_updates_for_birth() produces typed EntityUpdates that, applied
    through the normal authoritative apply path, land each existing parent's bond toward the
    new child at the same 0.8/0.8 seeded values as the child's own side."""
    parent_a = (V2EntityBuilder(1).location(0.0, 0.0).build())
    parent_b = (V2EntityBuilder(2).location(0.0, 0.0).build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: parent_a, 2: parent_b})

    updates = build_parent_bond_updates_for_birth([1, 2], child_entity_id=99, birth_tick=100)
    update = StateUpdate(entity_updates={u.entity_id: u for u in updates})

    next_state = ApplyPath.apply_generation(state, update, 101, 101)

    for parent_id in (1, 2):
        bond = next_state.entities[parent_id].social.bonds[99]
        assert bond.familiarity == 0.8
        assert bond.sentiment == 0.8
        assert bond.last_interaction_tick == 100


def test_no_marriage_precondition_in_birth_record_schema_or_apply_path():
    """Reproduction (idea 32) is explicitly decoupled from Marriage (idea 33) per the
    2026-08-29 build-order decision -- no marriage/contract precondition may gate the
    birth-record schema, its builder path, or its apply path."""
    import inspect
    from src.engine import patches as patches_module
    from src.core import builder as builder_module

    for source in (
        inspect.getsource(patches_module.LifecyclePatch),
        inspect.getsource(builder_module.V2EntityBuilder.lifecycle),
        inspect.getsource(builder_module.V2EntityBuilder.birth_record),
        inspect.getsource(builder_module.build_parent_bond_updates_for_birth),
    ):
        assert "Contract" not in source
        assert "marriage" not in source.lower()

    # Behavioral: birth_record() succeeds with zero contracts present anywhere in state.
    child = (V2EntityBuilder(99)
             .location(0.0, 0.0)
             .birth_record(parent_a_entity_id=1, parent_b_entity_id=2, birth_tick=10)
             .build())
    state = AuthoritativeState(tick=10, seed=42, entities={99: child})
    assert state.entities[99].strategic.contracts == {}


def test_dependent_field_round_trip():
    """TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS: dependent_entity_ids serializes
    deterministically via to_canonical_dict(), sorted like heirlooms, including the
    unset (empty-list) default case."""
    lifecycle = LifecycleComponent(dependent_entity_ids=[3, 1, 2])
    canonical = lifecycle.to_canonical_dict()
    assert canonical["dependent_entity_ids"] == [1, 2, 3]

    unset = LifecycleComponent()
    assert unset.to_canonical_dict()["dependent_entity_ids"] == []


def test_dependent_field_applied_via_authoritative_patch():
    """dependent_entity_ids is only ever set via LifecycleUpdate.dependent_entity_ids_add
    applied through ApplyPath.apply_generation (the authoritative apply path) -- never a
    direct mutation, mirroring heir_entity_id_set's own precedent."""
    entity = (V2EntityBuilder(1).location(0.0, 0.0).build())
    baseline_lifecycle = entity.lifecycle
    state = AuthoritativeState(tick=100, seed=42, entities={1: entity})

    assert LifecycleUpdate().is_noop()
    assert not LifecycleUpdate(dependent_entity_ids_add=[2]).is_noop()

    life_upd = LifecycleUpdate(dependent_entity_ids_add=[2])
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, lifecycle=life_upd)})

    next_state = ApplyPath.apply_generation(state, update, 101, 101)

    new_lifecycle = next_state.entities[1].lifecycle
    assert list(new_lifecycle.dependent_entity_ids) == [2]

    # Baseline entity/component object is untouched -- no direct mutation occurred.
    assert state.entities[1].lifecycle is baseline_lifecycle
    assert baseline_lifecycle.dependent_entity_ids == []

    # merge() unions dependent_entity_ids_add across same-tick writers, mirroring
    # heirlooms_add's own additive-list semantics.
    merged = LifecycleUpdate(dependent_entity_ids_add=[2]).merge(LifecycleUpdate(dependent_entity_ids_add=[3]))
    assert merged.dependent_entity_ids_add == [2, 3]
