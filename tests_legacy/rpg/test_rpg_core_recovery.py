import pytest
from src_legacy.core.state import AuthoritativeState
from src_legacy.engine.apply import ApplyPath
from src_legacy.certification.scenarios import build_scenario_state
from src_legacy.engine.executor import LocalSequentialExecutor
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config.loader import ConfigLoader

def test_combat_progression_rewards():
    """
    Verifies that killing a monster grants XP and Gold, and spawns a corpse.
    """
    state = build_scenario_state("COMBAT_ARENA_PROGRESSION")
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(42)
    profile = ConfigLoader.load_profile()
    
    # Hero (ID 1) should attack Monster (ID 2)
    # Monster has 10 HP. Hero has 50 ATK.
    # Damage calculation: atk * (atk / (atk + def*2 + 1))
    # 50 * (50 / (50 + 5*2 + 1)) = 50 * (50 / 61) = 50 * 0.819 = 40 damage.
    # Monster should die in 1 tick.
    
    # 1. First Tick (Attack)
    # We need to build WorkItems. In a real system, the kernel does this.
    # For a unit test, we'll simulate the execution.
    from src_legacy.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:1:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=1, payload={"action": "ATTACK", "target_id": 2}, work_class=WorkClass.CRITICAL)
    ]
    
    results = executor.execute(work, state, rng, profile)
    
    # We expect 2 results: one for attacker, one for defender
    assert len(results) == 2
    
    # Apply results
    from src_legacy.core.updates import StateUpdate
    entity_updates = {res.entity_id: res.update for res in results}
    state_up = StateUpdate(entity_updates=entity_updates)
    
    new_state = ApplyPath.apply_generation(state, state_up)
    
    # Verify Hero (ID 1) rewards
    hero = new_state.entities[1]
    assert hero.inventory.gold > 0
    assert hero.identity.evolution_points > 0
    
    # Verify Monster (ID 2) state
    monster = new_state.entities[2]
    assert not monster.combat.alive
    assert monster.combat.hp == 0
    
    # Verify Corpse (ID 1000002)
    assert 1000002 in new_state.corpses
    corpse = new_state.corpses[1000002]
    assert corpse.original_entity_id == 2
    assert "MONSTER_TOOTH" in [item.item_id for item in corpse.items]

def test_hero_mortality_rebirth():
    """
    Verifies that a hero death increments generation (rebirth).
    """
    state = build_scenario_state("COMBAT_ARENA_MORTALITY")
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(42)
    profile = ConfigLoader.load_profile()
    
    # Boss (ID 3) attacks Hero (ID 4)
    # Hero has 5 HP. Boss has 500 ATK. Hero dies instantly.
    
    from src_legacy.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:3:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=3, payload={"action": "ATTACK", "target_id": 4}, work_class=WorkClass.CRITICAL)
    ]
    
    results = executor.execute(work, state, rng, profile)
    
    from src_legacy.core.updates import StateUpdate
    entity_updates = {res.entity_id: res.update for res in results}
    state_up = StateUpdate(entity_updates=entity_updates)
    
    new_state = ApplyPath.apply_generation(state, state_up)
    
    # Verify Hero (ID 4) state
    hero = new_state.entities[4]
    assert not hero.combat.alive
    # generation was 3, should now be 4
    assert hero.lifecycle.generation == 4
    
    # Verify Corpse spawned
    assert 1000004 in new_state.corpses

def test_hero_permadeath():
    """
    Verifies that at generation 4, death results in permadeath.
    """
    from src_legacy.core.state import EntityState, LifecycleComponent, CombatComponent
    from dataclasses import replace
    
    state = build_scenario_state("COMBAT_ARENA_MORTALITY")
    # Set hero to generation 4
    hero = state.entities[4]
    state = replace(state, entities={**state.entities, 4: replace(hero, lifecycle=replace(hero.lifecycle, generation=4))})
    
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(42)
    profile = ConfigLoader.load_profile()
    
    from src_legacy.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:3:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=3, payload={"action": "ATTACK", "target_id": 4}, work_class=WorkClass.CRITICAL)
    ]
    
    results = executor.execute(work, state, rng, profile)
    
    from src_legacy.core.updates import StateUpdate
    entity_updates = {res.entity_id: res.update for res in results}
    state_up = StateUpdate(entity_updates=entity_updates)
    
    new_state = ApplyPath.apply_generation(state, state_up)
    
    # Verify Hero (ID 4) permadeath
    hero = new_state.entities[4]
    assert hero.lifecycle.is_permadeath

def test_tactical_modifiers():
    """
    Verifies High Ground and Flanking bonuses.
    """
    state = build_scenario_state("COMBAT_ARENA_TACTICAL")
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(42)
    profile = ConfigLoader.load_profile()

    # Hero 1 (ID 5) attacks Monster (ID 7)
    # Hero 1 is at (10,9) [MOUNTAIN], Monster at (10,10) [PLAIN].
    # Hero 2 is at (10,11), flanking the monster with Hero 1.
    
    from src_legacy.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:5:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=5, payload={"action": "ATTACK", "target_id": 7}, work_class=WorkClass.CRITICAL)
    ]

    results = executor.execute(work, state, rng, profile)
    
    # Hero 1 has 10 ATK. Monster has 5 DEF.
    # Base Atk: 10
    # High Ground: +20% (1.2)
    # Flanking: +15% (1.15)
    # Total Atk Mult: 1.35? No, modifiers are additive usually.
    # atk_mult = 1.0 + 0.2 + 0.15 = 1.35
    # Adjusted Atk = 10 * 1.35 = 13.5
    # Monster Def: 5
    # Damage: 13.5 * (13.5 / (13.5 + 5*2 + 1)) = 13.5 * (13.5 / 24.5) = 13.5 * 0.551 = 7.43 -> 7 damage.
    
    # Without bonuses: 10 * (10 / (10 + 10 + 1)) = 10 * (10/21) = 4.76 -> 4 damage.
    
    entity_updates = {res.entity_id: res.update for res in results}
    monster_up = entity_updates[7]
    assert monster_up.combat.damage_taken > 4
    assert monster_up.combat.damage_taken == 7

def test_social_synergy():
    """
    Verifies Social Synergy (+10%) for adjacent bonded allies.
    """
    state = build_scenario_state("COMBAT_ARENA_SOCIAL")
    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(42)
    profile = ConfigLoader.load_profile()

    # Hero 1 (ID 8) attacks Monster (ID 10)
    # Hero 2 (ID 9) is adjacent to Hero 1 and has high bond.
    
    from src_legacy.core.work import WorkItem, WorkClass
    work = [
        WorkItem(work_id="1:8:ENTITY_ACT", work_kind="ENTITY_ACT", owner_id=8, payload={"action": "ATTACK", "target_id": 10}, work_class=WorkClass.CRITICAL)
    ]

    results = executor.execute(work, state, rng, profile)
    
    # Hero 1 has 10 ATK. Monster has 5 DEF.
    # Base Atk: 10
    # Social Synergy: +10% (1.1)
    # Adjusted Atk = 10 * 1.1 = 11.0
    # Monster Def: 5
    # Damage: 11.0 * (11.0 / (11.0 + 5*2 + 1)) = 11.0 * (11.0 / 22.0) = 11.0 * 0.5 = 5.5 -> 5 damage.
    
    # Without bonuses: 10 * (10 / (10 + 10 + 1)) = 4.76 -> 4 damage.
    
    entity_updates = {res.entity_id: res.update for res in results}
    monster_up = entity_updates[10]
    assert monster_up.combat.damage_taken > 4
    assert monster_up.combat.damage_taken == 5

def test_attrition_and_status():
    """
    Verifies Shatter damage, Exhaustion penalties, and Starvation decay.
    """
    from src_legacy.core.state import BiologicalComponent, CombatComponent, EntityState
    from dataclasses import replace
    
    # 1. Test Shatter (1.5x damage vs Frozen)
    attacker = EntityState(id=11, kind="HERO", position=(0,0), combat=CombatComponent(hp=100, atk=10, def_stat=10, alive=True))
    # Target is Frozen
    target = EntityState(id=12, kind="HERO", position=(1,0), combat=CombatComponent(hp=100, atk=10, def_stat=5, alive=True),
                         properties={"status_frozen": True})
    
    from src_legacy.engine.combat import CombatResolutionSystem
    # Base Atk: 10. Shatter: 1.5x -> 15.0. Target Def: 5.
    # Damage: 15 * (15 / (15 + 10 + 1)) = 15 * (15/26) = 8.65 -> 8 damage.
    # Without Shatter: 10 * (10/21) = 4 damage.
    
    # We need a context for resolve_attack
    state = AuthoritativeState(tick=1, seed=42, entities={11: attacker, 12: target})
    res = CombatResolutionSystem.resolve_attack(attacker, target, state)
    assert res.damage_taken == 8
    
    # 2. Test Exhaustion Atk Penalty (0.8x)
    # Attacker is Exhausted (sleep_debt > 80)
    exhausted_attacker = replace(attacker, biological=BiologicalComponent(sleep_debt=85.0))
    # Normal target
    normal_target = replace(target, properties={})
    
    # Base Atk: 10. Exhaustion: 0.8x -> 8.0. Target Def: 5.
    # Damage: 8 * (8 / (8 + 10 + 1)) = 8 * (8/19) = 3.36 -> 3 damage.
    # Without Exhaustion: 10 * (10/21) = 4 damage.
    
    res = CombatResolutionSystem.resolve_attack(exhausted_attacker, normal_target, state)
    assert res.damage_taken == 3
    
    # 3. Test Starvation & Readiness Penalty in apply_generation
    # Entity at 100 hunger and 85 sleep debt
    hungry_entity = EntityState(id=13, kind="HERO", position=(0,0), 
                                biological=BiologicalComponent(hunger=100.0, sleep_debt=85.0),
                                combat=CombatComponent(hp=10, max_hp=10, alive=True),
                                readiness=0.0)
    
    prior_state = AuthoritativeState(tick=1, seed=42, entities={13: hungry_entity})
    from src_legacy.core.updates import StateUpdate
    update = StateUpdate()
    
    new_state = ApplyPath.apply_generation(prior_state, update)
    
    # Verify Hunger/Sleep increments (though they are already at limit)
    # Verify HP decay (10 -> 5)
    # Verify Readiness gain (0 -> 5.0 instead of 10.0)
    ent = new_state.entities[13]
    assert ent.combat.hp == 5
    assert ent.readiness == 5.0

def test_regional_consequences():
    """
    Verifies that Regional Trauma and Local Scars persist and decay correctly.
    """
    from src_legacy.core.state import RegionState, LocalScarState
    from src_legacy.world.consequences import RegionalConsequenceService
    
    # 1. Setup state with a region and a scar
    region = RegionState(id="forest_a", name="Forest A", bounds=(0,0,100,100), kind="FOREST", trauma_score=5.0, stability=0.5)
    scar = LocalScarState(id=101, position=(5,5), kind="BATTLE_FIELD", severity=0.8, 
                          created_tick=10, source_event_id="death:1", recovery_rate=0.1)
    
    state = AuthoritativeState(tick=11, seed=42, regions={"forest_a": region}, local_scars={101: scar})
    
    # 2. Process recovery
    new_regions, new_scars = RegionalConsequenceService.process_recovery(state)
    
    # Trauma decays by 0.0005, Stability increases by 0.0001
    assert new_regions["forest_a"].trauma_score < 5.0
    assert new_regions["forest_a"].stability > 0.5
    
    # Scar severity decays by 0.1 (recovery_rate)
    assert new_scars[101].severity == pytest.approx(0.7)
    
    # 3. Test ApplyPath integration
    from src_legacy.core.updates import StateUpdate
    update = StateUpdate()
    new_state = ApplyPath.apply_generation(state, update)
    
    assert 101 in new_state.local_scars
    assert new_state.local_scars[101].severity == pytest.approx(0.7)
    
    # 4. Test adding a new scar via update
    new_scar = LocalScarState(id=102, position=(6,6), kind="RAID_DAMAGE", severity=0.5,
                              created_tick=11, source_event_id="raid:1", recovery_rate=0.01)
    update_with_scar = StateUpdate(scars_add_or_update=[new_scar])
    
    state_with_new_scar = ApplyPath.apply_generation(state, update_with_scar)
    assert 102 in state_with_new_scar.local_scars
    assert state_with_new_scar.local_scars[102].severity == 0.5

def test_quest_lifecycle():
    """
    Verifies that HUNT quests advance when killing enemies, and that rewards are granted.
    """
    from src_legacy.core.state import AuthoritativeState, EntityState, StrategicComponent, CombatComponent, IdentityComponent, InventoryComponent
    from src_legacy.core.quests import QuestState, QuestKind, QuestStatus, RewardState
    from src_legacy.engine.domain_logic import SimulationDomainLogic
    from src_legacy.engine.apply import ApplyPath
    from src_legacy.core.updates import StateUpdate
    from src_legacy.platform.rng import DeterministicRNG
    from src_legacy.config.loader import ConfigLoader
    
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
    hero = EntityState(
        id=1, 
        kind="HERO", 
        position=(0,0), 
        strategic=StrategicComponent(projects={"q1": quest}),
        combat=CombatComponent(hp=100, atk=100, def_stat=10, alive=True),
        identity=IdentityComponent(evolution_points=0),
        inventory=InventoryComponent(gold=0)
    )
    
    # Setup Monster (target)
    from src_legacy.core.enums import EntityRole
    monster = EntityState(
        id=2, 
        kind="MONSTER", 
        position=(1,0), 
        identity=IdentityComponent(role=EntityRole.MONSTER),
        combat=CombatComponent(hp=10, max_hp=10, atk=5, def_stat=0, alive=True)
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
    
    # Apply Updates
    state_up = StateUpdate(entity_updates=updates_dict)
    new_state = ApplyPath.apply_generation(state, state_up)
    
    new_hero = new_state.entities[1]
    
    # Quest should be rewarded
    updated_quest = new_hero.strategic.projects["q1"]
    assert updated_quest.quest_status == QuestStatus.REWARDED
    assert updated_quest.current_value == 1.0
    
    # Rewards should be applied (Quest rewards + base combat rewards)
    # XP: 100 (quest) + 10 (base) = 110. Level 1 -> 2 costs 100 XP. Remaining: 10
    # Gold: 50 (quest) + 5 (base) = 55
    assert new_hero.inventory.gold == 55
    assert new_hero.identity.evolution_level == 2
    assert new_hero.identity.evolution_points == 10

