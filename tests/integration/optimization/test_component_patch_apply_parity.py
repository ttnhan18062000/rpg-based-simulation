# Compliance IDs: PERF-015
import pytest
from src.core.state import (
    AuthoritativeState, EntityState, NavigationComponent, CombatComponent,
    BiologicalComponent, LifecycleComponent, StaminaComponent, StrategicComponent,
    AttributeComponent, IdentityComponent, InventoryComponent, LifeStage
)
from src.core.self_model import SelfModelBundle, KnowledgeModelComponent, KnowledgeFact, UnknownFact
from src.core.updates import (
    StateUpdate, EntityUpdate, NavigationUpdate, CombatUpdate, AttributeUpdate, IdentityUpdate
)
from src.engine.cadence import SystemCadence
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.patches import extract_patches, NavigationPatch, CombatPatch, AttributePatch, IdentityPatch, SelfModelPatch

def test_component_patch_apply_parity():
    # Setup rich multi-domain entity state
    entities = {}
    for i in range(1, 11):
        entities[i] = EntityState(
            id=i,
            kind="HERO",
            navigation=NavigationComponent(position=(float(i * 10), float(i * 10))),
            combat=CombatComponent(hp=100, max_hp=100, alive=True, atk=15, def_stat=5, speed=1, readiness=100.0),
            biological=BiologicalComponent(),
            lifecycle=LifecycleComponent(age_ticks=50, max_age_ticks=2000, active=True),
            stamina=StaminaComponent(current=100.0, max_stamina=100.0),
            attributes=AttributeComponent(strength=10, agility=10),
            identity=IdentityComponent(role="WARRIOR", evolution_level=1),
            inventory=InventoryComponent(),
            strategic=StrategicComponent()
        )
    
    state = AuthoritativeState(tick=10, seed=12345, world_time=5000, entities=entities)
    
    # Construct complex update across multiple components
    e_upds = {
        1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(50.0, 50.0))),
        3: EntityUpdate(entity_id=3, attributes=AttributeUpdate(strength_delta=5)),
        4: EntityUpdate(entity_id=4, identity=IdentityUpdate(role_set="PALADIN"))
    }
    
    update = StateUpdate(entity_updates=e_upds, force_full_scan=True)
    
    # Verify patch extraction
    patches1 = extract_patches(1, e_upds[1])
    assert any(isinstance(p, NavigationPatch) for p in patches1)
    
    # Refine through pipeline
    refined_upd = AuthoritativeApplyPipeline.refine(state, update)
    
    # Authoritative systems (like combat resolution) attach combat updates to the refined update
    refined_e_upds = dict(refined_upd.entity_updates)
    combat_upd = EntityUpdate(entity_id=2, combat=CombatUpdate(hp_delta=-25), readiness_delta=15.0)
    patches2 = extract_patches(2, combat_upd)
    assert any(isinstance(p, CombatPatch) for p in patches2)
    refined_e_upds[2] = combat_upd
    refined_upd = refined_upd.replace(entity_updates=refined_e_upds)
    
    # Apply through ApplyPath
    new_state = ApplyPath.apply_generation(state, refined_upd, next_tick=11, cadence=SystemCadence())
    
    # Assert correct component transformations
    assert new_state.tick == 11
    assert new_state.entities[1].navigation.position == (10.0, 11.0)
    assert new_state.entities[2].combat.hp == 75
    assert new_state.entities[2].combat.readiness == 100.0 # 100 + 15 clamped to 100.0
    assert new_state.entities[3].attributes.strength == 15
    assert new_state.entities[4].identity.role == "PALADIN"


def test_life_stage_set_survives_full_apply_pipeline():
    """TCK-20260824-LIFE-STAGE-TRANSITIONS: mirrors the existing role_set -> 'PALADIN' pattern
    above, but for IdentityUpdate.life_stage_set, run through the full ApplyPath.apply_generation()
    pipeline (not just IdentityPatch.apply() in isolation) to catch a replace()-kwarg-omission bug."""
    entity = EntityState(id=1, kind="HERO", identity=IdentityComponent(life_stage=LifeStage.ADULT))
    state = AuthoritativeState(tick=1, seed=1, world_time=100, entities={1: entity})

    e_upd = EntityUpdate(entity_id=1, identity=IdentityUpdate(life_stage_set=LifeStage.ELDER))
    update = StateUpdate(entity_updates={1: e_upd}, force_full_scan=True)

    new_state = ApplyPath.apply_generation(state, update, next_tick=2, cadence=SystemCadence())

    assert new_state.entities[1].identity.life_stage == LifeStage.ELDER


def test_new_maturity_field_survives_apply_generation_round_trip():
    """TCK-20260831-CREATURE-TERRITORY-LIFECYCLE: mirrors
    test_life_stage_set_survives_full_apply_pipeline's pattern for the new
    IdentityUpdate.territory_maturity_delta field, run through the full
    ApplyPath.apply_generation() pipeline (not just IdentityPatch.apply() in isolation) to
    catch a replace()-kwarg-omission bug."""
    entity = EntityState(id=1, kind="goblin_warrior", identity=IdentityComponent(territory_maturity=0.0))
    state = AuthoritativeState(tick=1, seed=1, world_time=100, entities={1: entity})

    e_upd = EntityUpdate(entity_id=1, identity=IdentityUpdate(territory_maturity_delta=5.0))
    update = StateUpdate(entity_updates={1: e_upd}, force_full_scan=True)

    new_state = ApplyPath.apply_generation(state, update, next_tick=2, cadence=SystemCadence())

    assert new_state.entities[1].identity.territory_maturity == 5.0


def test_natural_creature_spawn_commits_through_authoritative_apply_path():
    """TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH: a parentless natural-creature
    offspring built via EntityGenerator.spawn_natural_creature_offspring() and appended to
    StateUpdate.entities_add must survive a full ApplyPath.apply_generation() round-trip,
    including its birth-record fields and short-maturation-clock age_ticks."""
    from src.systems.world_systems.generator import EntityGenerator

    state = AuthoritativeState(tick=60, seed=42, world_time=100, entities={})

    generator = EntityGenerator(seed=42)
    offspring = generator.spawn_natural_creature_offspring(
        (10.0, 20.0), state=state, kind="goblin_warrior", difficulty_tier=1, birth_tick=60,
    )

    update = StateUpdate(entities_add=[offspring], force_full_scan=True)
    new_state = ApplyPath.apply_generation(state, update, next_tick=61, cadence=SystemCadence())

    result_entity = new_state.entities[offspring.id]
    assert result_entity.kind == "goblin_warrior"
    assert result_entity.lifecycle.parent_a_entity_id is None
    assert result_entity.lifecycle.parent_b_entity_id is None
    assert result_entity.lifecycle.birth_tick == 60
    assert result_entity.lifecycle.age_ticks == 3000 - 30
    assert result_entity.identity.life_stage == LifeStage.CHILD


def test_magical_demonic_entity_spawn_commits_through_authoritative_apply_path():
    """TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH: a parentless magical/demonic entity
    built via EntityGenerator.spawn_magical_demonic_entity() and appended to
    StateUpdate.entities_add must survive a full ApplyPath.apply_generation() round-trip,
    including its birth-record fields and full-ADULT life stage (no maturation clock)."""
    from src.systems.world_systems.generator import EntityGenerator

    state = AuthoritativeState(tick=5000, seed=42, world_time=100, entities={})

    generator = EntityGenerator(seed=42)
    entity = generator.spawn_magical_demonic_entity(
        (10.0, 20.0), state=state, difficulty_tier=4, birth_tick=5000,
    )

    update = StateUpdate(entities_add=[entity], force_full_scan=True)
    new_state = ApplyPath.apply_generation(state, update, next_tick=5001, cadence=SystemCadence())

    result_entity = new_state.entities[entity.id]
    assert result_entity.kind == "magical_demonic_entity"
    assert result_entity.lifecycle.parent_a_entity_id is None
    assert result_entity.lifecycle.parent_b_entity_id is None
    assert result_entity.lifecycle.birth_tick == 5000
    assert result_entity.lifecycle.birth_city_id is None
    assert result_entity.identity.life_stage == LifeStage.ADULT


def test_self_model_patch_apply_parity_durable_materialization():
    """
    TCK-20260703-SIMQ-UPLIFT3-BRANCH-B (supplementary fix): direct regression guard for
    Finding 5 — EntityUpdate.self_model_bundle_set must durably materialize into
    entity.self_model end-to-end through ApplyPath.apply_generation(), via the new
    SelfModelPatch (src/engine/patches.py).
    """
    entity = EntityState(id=1, kind="HERO", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    state = AuthoritativeState(tick=1, seed=1, world_time=100, entities={1: entity})

    bundle = SelfModelBundle(
        knowledge=KnowledgeModelComponent(
            facts={"coal_ore": KnowledgeFact(subject="coal_ore", fact_type="material_source", details={"source": "old_mine"})},
            unknowns={"iron_ore": UnknownFact(subject="iron_ore", reason="never_queried")},
        )
    )

    e_upd = EntityUpdate(entity_id=1, self_model_bundle_set=bundle)

    # Patch-extraction sanity check
    patches = extract_patches(1, e_upd)
    assert any(isinstance(p, SelfModelPatch) for p in patches)

    update = StateUpdate(entity_updates={1: e_upd}, force_full_scan=True)
    new_state = ApplyPath.apply_generation(state, update, next_tick=2, cadence=SystemCadence())

    result_entity = new_state.entities[1]
    assert result_entity.self_model == bundle  # full equality, not just not-None
    assert result_entity.self_model.knowledge.facts["coal_ore"].details == {"source": "old_mine"}
    assert result_entity.self_model.knowledge.unknowns["iron_ore"].reason == "never_queried"
