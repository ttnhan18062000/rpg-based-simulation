import pytest
from src.core.state import AuthoritativeState
from src.engine.apply import ApplyPath
from src.certification.scenarios import build_scenario_state
from src.engine.executor import LocalSequentialExecutor
from src.platform.rng import DeterministicRNG
from src.config.loader import ConfigLoader
from src.engine.pipeline import AuthoritativeApplyPipeline

def test_combat_progression_rewards():
    """
    Verifies that killing a monster grants XP and Gold, and spawns a corpse.
    """
    state = build_scenario_state("COMBAT_ARENA_PROGRESSION")
    from dataclasses import replace
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(base_seed=42)
    profile = ConfigLoader.load_profile()
    
    # 1. First Tick (Attack)
    from src.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:1:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=1, payload={"action": "ATTACK", "target_id": 2}, work_class=WorkClass.CRITICAL)
    ]
    
    results = executor.execute(work, state, rng, profile)
    
    # Apply results through pipeline
    from src.core.updates import StateUpdate
    entity_updates = {res.entity_id: res.update for res in results}
    state_up = StateUpdate(entity_updates=entity_updates)
    
    refined = AuthoritativeApplyPipeline.refine(state, state_up)
    new_state = ApplyPath.apply_generation(state, refined)
    
    # Verify Hero (ID 1) rewards
    hero = new_state.entities[1]
    assert hero.inventory.gold > 0
    # Base rewards: 10 XP. 
    assert hero.identity.evolution_points >= 10
    
    # Verify Monster (ID 2) state
    monster = new_state.entities[2]
    assert not monster.combat.alive
    assert monster.combat.hp == 0
    
    # Verify Corpse (ID 1000002)
    assert 1000002 in new_state.corpses

def test_hero_mortality_rebirth():
    """
    Verifies that a hero death increments generation (rebirth).
    """
    state = build_scenario_state("COMBAT_ARENA_MORTALITY")
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(base_seed=42)
    profile = ConfigLoader.load_profile()
    
    from src.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:3:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=3, payload={"action": "ATTACK", "target_id": 4}, work_class=WorkClass.CRITICAL)
    ]
    
    results = executor.execute(work, state, rng, profile)
    
    from src.core.updates import StateUpdate
    entity_updates = {res.entity_id: res.update for res in results}
    state_up = StateUpdate(entity_updates=entity_updates)
    
    refined = AuthoritativeApplyPipeline.refine(state, state_up)
    new_state = ApplyPath.apply_generation(state, refined)
    
    # Verify Hero (ID 4) state
    hero = new_state.entities[4]
    assert not hero.combat.alive
    # generation was 3, should now be 4
    assert hero.lifecycle.generation == 4

def test_hero_permadeath():
    """
    Verifies that at generation 4, death results in permadeath.
    """
    from src.core.state import EntityState, LifecycleComponent, CombatComponent
    from dataclasses import replace
    
    state = build_scenario_state("COMBAT_ARENA_MORTALITY")
    # Set hero to generation 4
    hero = state.entities[4]
    state = replace(state, entities={**state.entities, 4: replace(hero, lifecycle=replace(hero.lifecycle, generation=4))})
    
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(base_seed=42)
    profile = ConfigLoader.load_profile()
    
    from src.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:3:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=3, payload={"action": "ATTACK", "target_id": 4}, work_class=WorkClass.CRITICAL)
    ]
    
    results = executor.execute(work, state, rng, profile)
    
    from src.core.updates import StateUpdate
    entity_updates = {res.entity_id: res.update for res in results}
    state_up = StateUpdate(entity_updates=entity_updates)
    
    refined = AuthoritativeApplyPipeline.refine(state, state_up)
    new_state = ApplyPath.apply_generation(state, refined)
    
    # Verify Hero (ID 4) permadeath
    hero = new_state.entities[4]
    assert hero.lifecycle.is_permadeath

def test_tactical_modifiers():
    """
    Verifies High Ground and Flanking bonuses.
    """
    state = build_scenario_state("COMBAT_ARENA_TACTICAL")
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(base_seed=42)
    profile = ConfigLoader.load_profile()

    from src.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:5:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=5, payload={"action": "ATTACK", "target_id": 7}, work_class=WorkClass.CRITICAL)
    ]

    results = executor.execute(work, state, rng, profile)
    
    from src.core.updates import StateUpdate
    entity_updates = {res.entity_id: res.update for res in results}
    state_up = StateUpdate(entity_updates=entity_updates)
    
    refined = AuthoritativeApplyPipeline.refine(state, state_up)
    
    monster_up = refined.entity_updates[7]
    # Base damage is ~4. With bonuses it should be higher.
    assert monster_up.combat.damage_taken > 4

def test_social_synergy():
    """
    Verifies Social Synergy (+10%) for adjacent bonded allies.
    """
    from dataclasses import replace
    state = build_scenario_state("COMBAT_ARENA_SOCIAL")
    state = replace(state, tick=7) # Use unique tick to avoid spatial cache collision
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(base_seed=42)
    profile = ConfigLoader.load_profile()

    from src.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:8:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=8, payload={"action": "ATTACK", "target_id": 10}, work_class=WorkClass.CRITICAL)
    ]

    results = executor.execute(work, state, rng, profile)
    
    from src.core.updates import StateUpdate
    entity_updates = {res.entity_id: res.update for res in results}
    state_up = StateUpdate(entity_updates=entity_updates)
    
    refined = AuthoritativeApplyPipeline.refine(state, state_up)
    
    monster_up = refined.entity_updates[10]
    assert monster_up.combat.damage_taken > 4

def test_attrition_and_status():
    """
    Verifies Shatter damage, Exhaustion penalties, and Starvation decay.
    """
    from src.core.state import BiologicalComponent, CombatComponent, EntityState, IdentityComponent
    from src.core.enums import Faction
    from dataclasses import replace
    
    # 1. Test Shatter (1.5x damage vs Frozen)
    from src.core.builder import V2EntityBuilder
    attacker = (V2EntityBuilder(11)
        .kind("HERO")
        .at((0,0))
        .readiness(100.0)
        .with_identity(faction=Faction.HERO_GUILD)
        .with_combat(hp=100, atk=10, def_stat=10, alive=True)
        .build())
    target = (V2EntityBuilder(12)
        .kind("HERO")
        .at((1,0))
        .with_identity(faction=Faction.MONSTER_HORDE)
        .with_combat(hp=100, atk=10, def_stat=5, alive=True)
        .with_property("status_frozen", True)
        .build())
    
    from src.engine.combat import CombatResolutionSystem
    state = AuthoritativeState(tick=1, seed=42, entities={11: attacker, 12: target})
    res = CombatResolutionSystem.resolve_attack(attacker, target, state)
    assert res.damage_taken > 4 # Shatter applied
    
    # 2. Test Exhaustion Atk Penalty (0.8x)
    exhausted_attacker = replace(attacker, biological=replace(attacker.biological, sleep_debt=85.0))
    normal_target = replace(target, identity=replace(target.identity, properties={}))
    
    res = CombatResolutionSystem.resolve_attack(exhausted_attacker, normal_target, state)
    assert res.damage_taken <= 4 # Exhaustion penalty (0.8x of 5 = 4)

def test_quest_lifecycle():
    """
    Verifies that HUNT quests advance when killing enemies, and that rewards are granted.
    """
    from src.core.state import AuthoritativeState, EntityState, StrategicComponent, CombatComponent, IdentityComponent, InventoryComponent
    from src.core.quests import QuestState, QuestKind, QuestStatus, RewardState
    from src.engine.domain_logic import SimulationDomainLogic
    from src.core.updates import StateUpdate
    
    # Setup Quest
    quest = QuestState(
        id="q1",
        kind="quest",
        quest_kind=QuestKind.HUNT,
        quest_status=QuestStatus.ACTIVE,
        goal_value=1.0,
        current_value=0.0,
        reward=RewardState(xp=100, gold=50),
        metadata={"target_kind": "MONSTER"}
    )
    
    # Setup Hero
    from dataclasses import replace
    from src.core.builder import V2EntityBuilder
    hero = (V2EntityBuilder(1)
        .kind("HERO")
        .at((0,0))
        .readiness(100.0)
        .with_strategic(projects={"q1": quest})
        .with_combat(hp=100, atk=100, def_stat=10, alive=True)
        .with_identity(evolution_points=0)
        .with_inventory(gold=0)
        .build()
    )
    
    # Setup Monster (target)
    from src.core.enums import EntityRole, Faction
    monster = (V2EntityBuilder(2)
        .kind("MONSTER")
        .at((1,0))
        .with_identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
        .with_combat(hp=10, max_hp=10, atk=5, def_stat=0, alive=True)
        .build()
    )
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster})
    
    # Execute Attack
    updates_dict = SimulationDomainLogic.execute_action(
        entity=hero,
        payload={"action": "ATTACK", "target_id": 2},
        current_tick=1,
        neighbor_view=[(2, monster)],
        context=state
    )
    # Ensure task is in proposal for kernel re-execution
    from src.core.updates import TaskUpdate
    if 1 in updates_dict:
        updates_dict[1] = replace(updates_dict[1], task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2}))
    
    # Apply Updates
    state_up = StateUpdate(entity_updates=updates_dict)
    
    refined = AuthoritativeApplyPipeline.refine(state, state_up)
    new_state = ApplyPath.apply_generation(state, refined)
    
    new_hero = new_state.entities[1]
    
    # Assert status is REWARDED
    updated_quest = new_hero.strategic.projects["q1"]
    assert updated_quest.quest_status == QuestStatus.REWARDED
    
    # Rewards should be applied
    # XP: 100 (Quest) + 10 (Combat) = 110. Level 1->2 costs 100.
    # Total points = 110, Level up consumed 100, remaining = 10.
    assert new_hero.identity.evolution_level == 2
    assert new_hero.identity.evolution_points == 10
    # Gold: 50 (Quest) + 5 (Combat) = 55
    assert new_hero.inventory.gold == 55
