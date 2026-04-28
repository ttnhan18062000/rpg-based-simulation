from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from src.certification.models import ScenarioExpectations
from src.core.state import AuthoritativeState, EntityState, ItemStack


class PressureInjector:
    """Helper to inject pathological state or work into the simulation."""
    
    @staticmethod
    def inject_entities(state: AuthoritativeState, count: int) -> AuthoritativeState:
        """Inject a large number of entities to stress memory."""
        new_entities = state.entities.copy()
        current_max_id = max(new_entities.keys()) if new_entities else 0
        
        for i in range(1, count + 1):
            eid = current_max_id + i
            new_entities[eid] = EntityState(
                id=eid,
                kind="PRESSURE_TARGET",
                position=(0.0, 0.0),
                readiness=100.0
            )
        
        # We must return a new state as it's frozen (well, AuthoritativeState is dataclass)
        # Re-using the dictionary but creating a new state object.
        from dataclasses import replace
        return replace(state, entities=new_entities)

    @staticmethod
    def inject_work_debt(state: AuthoritativeState, system: str, amount: int) -> AuthoritativeState:
        """Inject work debt to stress the governor."""
        new_debt = state.work_debt.copy()
        new_debt[system] = new_debt.get(system, 0) + amount
        from dataclasses import replace
        return replace(state, work_debt=new_debt)


class ArenaInjector:
    """Helper to inject multi-team combat scenarios into the simulation."""

    @staticmethod
    def build_team_battle(state: AuthoritativeState, team_size: int = 5) -> AuthoritativeState:
        """Setup a balanced team battle on opposite sides of a 20x20 area."""
        from src.systems.generator import EntityGenerator
        from dataclasses import replace
        
        generator = EntityGenerator(state.seed)
        new_entities = dict(state.entities)
        
        from src.core.strategic import ContractState, ContractKind, ContractStatus
        
        # 1. Spawn Team A (Heroes) at Western boundary
        hero_leader_id = None
        for i in range(team_size):
            hero = generator.spawn_hero(pos=(2.0, float(5 + i * 2)), state=state)
            if i == 0:
                hero_leader_id = hero.id
            elif hero_leader_id:
                # Add contract with leader
                contract = ContractState(
                    id=f"team_a_contract_{hero.id}",
                    kind=ContractKind.PROTECTION,
                    source_id=hero_leader_id,
                    target_id=hero.id,
                    status=ContractStatus.ACTIVE
                )
                hero = replace(hero, strategic=replace(hero.strategic, contracts={contract.id: contract}))
                # Update leader's state too
                leader = new_entities[hero_leader_id]
                new_entities[hero_leader_id] = replace(leader, strategic=replace(leader.strategic, contracts={**leader.strategic.contracts, contract.id: contract}))
            
            new_entities[hero.id] = hero
            state = replace(state, entities=new_entities)
            
        # 2. Spawn Team B (Monsters) at Eastern boundary
        monster_leader_id = None
        for i in range(team_size):
            monster = generator.spawn_monster(pos=(18.0, float(5 + i * 2)), state=state)
            if i == 0:
                monster_leader_id = monster.id
            elif monster_leader_id:
                # Add contract with leader
                contract = ContractState(
                    id=f"team_b_contract_{monster.id}",
                    kind=ContractKind.PROTECTION,
                    source_id=monster_leader_id,
                    target_id=monster.id,
                    status=ContractStatus.ACTIVE
                )
                monster = replace(monster, strategic=replace(monster.strategic, contracts={contract.id: contract}))
                # Update leader's state too
                leader = new_entities[monster_leader_id]
                new_entities[monster_leader_id] = replace(leader, strategic=replace(leader.strategic, contracts={**leader.strategic.contracts, contract.id: contract}))
                
            new_entities[monster.id] = monster
            state = replace(state, entities=new_entities)
            
        return state

    @staticmethod
    def build_progression_test(state: AuthoritativeState) -> AuthoritativeState:
        """Setup a hero vs monster fight to verify XP, Gold, and Mortality."""
        from src.core.state import EntityState, IdentityComponent, CombatComponent, LifecycleComponent, InventoryComponent
        from dataclasses import replace
        
        from src.core.enums import Faction
        
        # 1. Hero (Attacker)
        hero = EntityState(
            id=1, kind="HERO", position=(5.0, 5.0), readiness=100.0,
            identity=IdentityComponent(evolution_level=1, evolution_points=0, faction=Faction.HERO_GUILD),
            combat=CombatComponent(hp=100, max_hp=100, atk=50, def_stat=10, alive=True),
            lifecycle=LifecycleComponent(generation=1),
            inventory=InventoryComponent(max_slots=10, gold=0)
        )
        
        # 2. Monster (Victim)
        monster = EntityState(
            id=2, kind="MONSTER", position=(6.0, 5.0), readiness=0.0,
            identity=IdentityComponent(evolution_level=1, evolution_points=0, faction=Faction.MONSTER_HORDE),
            combat=CombatComponent(hp=10, max_hp=10, atk=5, def_stat=5, alive=True),
            lifecycle=LifecycleComponent(generation=1),
            inventory=InventoryComponent(max_slots=10, items=[ItemStack("MONSTER_TOOTH", 1)])
        )
        
        new_entities = dict(state.entities)
        new_entities[1] = hero
        new_entities[2] = monster
        
        # Inject the attack intent into the hero
        new_entities[1] = replace(hero, properties={"work_kind": "ENTITY_ACT", "payload": {"action": "ATTACK", "target_id": 2}})
        
        return replace(state, entities=new_entities)

    @staticmethod
    def build_mortality_test(state: AuthoritativeState) -> AuthoritativeState:
        """Setup a hero dying to verify rebirth/permadeath."""
        from src.core.state import EntityState, IdentityComponent, CombatComponent, LifecycleComponent
        from src.core.enums import Faction
        from dataclasses import replace
        
        # 1. Boss (Attacker)
        boss = EntityState(
            id=3, kind="MONSTER", position=(10.0, 10.0), readiness=100.0,
            identity=IdentityComponent(evolution_level=10, faction=Faction.MONSTER_HORDE),
            combat=CombatComponent(hp=1000, max_hp=1000, atk=500, def_stat=100, alive=True)
        )
        
        # 2. Hero (Victim)
        hero = EntityState(
            id=4, kind="HERO", position=(11.0, 10.0), readiness=0.0,
            identity=IdentityComponent(evolution_level=1, faction=Faction.HERO_GUILD),
            combat=CombatComponent(hp=5, max_hp=5, atk=1, def_stat=1, alive=True),
            lifecycle=LifecycleComponent(generation=3) # One away from permadeath
        )
        
        new_entities = dict(state.entities)
        new_entities[3] = boss
        new_entities[4] = hero
        
        # Boss attacks hero
        new_entities[3] = replace(boss, properties={"work_kind": "ENTITY_ACT", "payload": {"action": "ATTACK", "target_id": 4}})
        
        return replace(state, entities=new_entities)

    @staticmethod
    def build_tactical_test(state: AuthoritativeState) -> AuthoritativeState:
        """Setup a flanking scenario for tactical bonus verification."""
        from src.core.state import EntityState, IdentityComponent, CombatComponent
        from src.core.enums import Faction
        from dataclasses import replace
        
        # 1. Attacker 1 (North)
        hero1 = EntityState(
            id=5, kind="HERO", position=(10.0, 9.0), readiness=100.0,
            identity=IdentityComponent(faction=Faction.HERO_GUILD),
            combat=CombatComponent(hp=100, atk=10, def_stat=10, alive=True)
        )
        
        # 2. Attacker 2 (South)
        hero2 = EntityState(
            id=6, kind="HERO", position=(10.0, 11.0), readiness=100.0,
            identity=IdentityComponent(faction=Faction.HERO_GUILD),
            combat=CombatComponent(hp=100, atk=10, def_stat=10, alive=True)
        )
        
        # 3. Monster (Target in the middle at 10,10)
        monster = EntityState(
            id=7, kind="MONSTER", position=(10.0, 10.0), readiness=0.0,
            identity=IdentityComponent(faction=Faction.MONSTER_HORDE),
            combat=CombatComponent(hp=50, atk=5, def_stat=5, alive=True)
        )
        
        new_entities = dict(state.entities)
        new_entities[5] = hero1
        new_entities[6] = hero2
        new_entities[7] = monster
        
        # Terrain: Add a MOUNTAIN at (10,9) for Hero 1 high ground
        new_terrain = dict(state.terrain)
        new_terrain[(10, 9)] = "MOUNTAIN"
        
        return replace(state, entities=new_entities, terrain=new_terrain)

    @staticmethod
    def build_social_test(state: AuthoritativeState) -> AuthoritativeState:
        """Setup a synergy scenario for social bond verification."""
        from src.core.state import EntityState, IdentityComponent, CombatComponent, SocialComponent, SocialBond
        from src.core.enums import Faction
        from dataclasses import replace
        
        # 1. Attacker (Hero 1)
        hero1 = EntityState(
            id=8, kind="HERO", position=(20.0, 20.0), readiness=100.0,
            identity=IdentityComponent(faction=Faction.HERO_GUILD),
            combat=CombatComponent(hp=100, atk=10, def_stat=10, alive=True),
            social=SocialComponent(bonds={9: SocialBond(target_id=9, familiarity=0.8)})
        )
        
        # 2. Ally (Hero 2) - adjacent to Hero 1
        hero2 = EntityState(
            id=9, kind="HERO", position=(21.0, 20.0), readiness=100.0,
            identity=IdentityComponent(faction=Faction.HERO_GUILD),
            combat=CombatComponent(hp=100, atk=10, def_stat=10, alive=True)
        )
        
        # 3. Monster (Target)
        monster = EntityState(
            id=10, kind="MONSTER", position=(20.0, 21.0), readiness=0.0,
            identity=IdentityComponent(faction=Faction.MONSTER_HORDE),
            combat=CombatComponent(hp=50, atk=5, def_stat=5, alive=True)
        )
        
        new_entities = dict(state.entities)
        new_entities[8] = hero1
        new_entities[9] = hero2
        new_entities[10] = monster
        return replace(state, entities=new_entities)

    @staticmethod
    def build_quest_battle(state: AuthoritativeState) -> AuthoritativeState:
        """Setup a hero with a HUNT quest against a specific monster kind."""
        from src.core.state import (
            EntityState, IdentityComponent, CombatComponent, 
            InventoryComponent, LifecycleComponent
        )
        from src.core.quests import QuestState, QuestStatus, QuestKind, RewardState
        from src.core.strategic import StrategicComponent
        from src.core.enums import Faction, EntityRole
        from dataclasses import replace
        
        # 1. Hero (Quester)
        hero = EntityState(
            id=11, kind="HERO", position=(5.0, 5.0), readiness=100.0,
            identity=IdentityComponent(evolution_level=1, faction=Faction.HERO_GUILD),
            combat=CombatComponent(hp=100, max_hp=100, atk=50, def_stat=10, alive=True),
            lifecycle=LifecycleComponent(generation=1),
            inventory=InventoryComponent(max_slots=10, gold=0),
            strategic=StrategicComponent(
                projects={
                    "test_hunt": QuestState(
                        id="test_hunt",
                        kind="quest",
                        quest_kind=QuestKind.HUNT,
                        quest_status=QuestStatus.ACTIVE,
                        goal_value=1.0,
                        current_value=0.0,
                        reward=RewardState(xp=100, gold=50),
                        metadata={"target_kind": "GOBLIN"}
                    )
                }
            )
        )
        
        # 2. Monster (Target)
        goblin = EntityState(
            id=12, kind="GOBLIN", position=(6.0, 5.0), readiness=0.0,
            identity=IdentityComponent(evolution_level=1, faction=Faction.MONSTER_HORDE, role=EntityRole.MONSTER),
            combat=CombatComponent(hp=10, max_hp=10, atk=5, def_stat=5, alive=True),
            lifecycle=LifecycleComponent(generation=1)
        )
        
        from src.core.state import TaskComponent
        new_entities = dict(state.entities)
        new_entities[11] = hero
        new_entities[12] = goblin
        
        # Hero attacks goblin (Inject authoritative intent)
        new_entities[11] = replace(hero, 
            task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 12})
        )
        
        return replace(state, entities=new_entities)

    @staticmethod
    def build_regional_control_test(state: AuthoritativeState) -> AuthoritativeState:
        """Setup regional control test: Hero vs Monster in a named region."""
        from src.core.state import (
            EntityState, IdentityComponent, CombatComponent, 
            InventoryComponent, LifecycleComponent, RegionState, TaskComponent
        )
        from src.core.enums import Faction, EntityRole
        from dataclasses import replace
        
        # 1. Define Region
        region = RegionState(
            id="test_wilderness",
            name="Test Wilderness",
            bounds=(0, 0, 100, 100),
            influence=-45.0, # Close to conquest threshold (-50.0)
            owner_faction_id=None
        )
        
        # 2. Hero (Strong enough to kill)
        hero = EntityState(
            id=13, kind="HERO", position=(50.0, 50.0), readiness=100.0,
            identity=IdentityComponent(evolution_level=5, faction=Faction.HERO_GUILD, role=EntityRole.HERO),
            combat=CombatComponent(hp=100, max_hp=100, atk=100, def_stat=20, speed=10, alive=True),
            lifecycle=LifecycleComponent(generation=1),
            inventory=InventoryComponent(max_slots=10, gold=100)
        )
        
        # 3. Monster (Weak)
        monster = EntityState(
            id=14, kind="GOBLIN", position=(51.0, 50.0), readiness=0.0,
            identity=IdentityComponent(evolution_level=1, faction=Faction.MONSTER_HORDE, role=EntityRole.MONSTER),
            combat=CombatComponent(hp=1, max_hp=1, atk=1, def_stat=1, alive=True),
            lifecycle=LifecycleComponent(generation=1)
        )
        
        new_entities = dict(state.entities)
        new_entities[13] = hero
        new_entities[14] = monster
        
        # Hero attacks monster
        new_entities[13] = replace(hero, 
            task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 14})
        )
        
        new_regions = dict(state.regions)
        new_regions["test_wilderness"] = region
        
        return replace(state, entities=new_entities, regions=new_regions, tick=99)


    @staticmethod
    def register_all():
        """Register all authoritative test scenarios."""
        from src.platform.scenarios import ScenarioRegistry
        ScenarioRegistry.register("COMBAT_ARENA_SOCIAL", ArenaInjector.build_social_test)
        ScenarioRegistry.register("COMBAT_ARENA_QUESTS", ArenaInjector.build_quest_battle)
        ScenarioRegistry.register("COMBAT_ARENA_REGIONAL", ArenaInjector.build_regional_control_test)


class GameplayInjector:
    """Helper to inject real gameplay scenarios into the simulation."""

    @staticmethod
    def build_movement_test(state: AuthoritativeState, distance: int = 20) -> AuthoritativeState:
        """Setup an entity moving in a straight line."""
        from src.core.state import EntityState
        from dataclasses import replace
        
        new_entities = dict(state.entities)
        new_entities[1] = EntityState(
            id=1, kind="actor", position=(0.0, 0.0), readiness=100.0,
            properties={"work_kind": "ENTITY_MOVE", "payload": {"target_position": (0.0, float(distance))}}
        )
        return replace(state, entities=new_entities)

    @staticmethod
    def build_harvest_test(state: AuthoritativeState, required_ticks: int = 3) -> AuthoritativeState:
        """Setup an entity harvesting a resource node."""
        from src.core.state import EntityState, ResourceNodeState, InteractionComponent, InventoryComponent
        from dataclasses import replace
        
        node = ResourceNodeState(
            id=100, kind="herb", position=(0.0, 1.0), yields_item="herb",
            remaining_charges=1, max_charges=1, required_ticks=required_ticks
        )
        
        actor = EntityState(
            id=1, kind="actor", position=(0.0, 1.0), readiness=100.0,
            interaction=InteractionComponent(target_node_id=100, progress=0),
            inventory=InventoryComponent(max_slots=10)
        )
        
        new_nodes = dict(state.resource_nodes)
        new_nodes[100] = node
        
        new_entities = dict(state.entities)
        new_entities[1] = actor
        
        return replace(state, entities=new_entities, resource_nodes=new_nodes)

    @staticmethod
    def build_integrated_loop(state: AuthoritativeState) -> AuthoritativeState:
        """
        Autonomous Progression Loop: 
        1. Entity at Town (0,0) wants to craft a sword.
        2. Blacksmith fails (missing iron_ore).
        3. Strategic AI generates blocker and lead for iron_ore at (1,0).
        4. Entity moves to (1,0), harvests, and returns.
        """
        from src.core.state import (
            EntityState, ResourceNodeState, InteractionComponent, 
            InventoryComponent, IdentityComponent, NavigationComponent
        )
        from src.core.strategic import StrategicComponent, BlockerState, LeadState
        from dataclasses import replace
        
        # 1. Resource Node at (1.0, 0.0)
        node = ResourceNodeState(
            id=101, kind="ORE_VEIN", position=(1.0, 0.0), 
            yields_item="iron_ore", remaining_charges=5, max_charges=5, required_ticks=2
        )
        
        # 2. Hero at Town (0.0, 0.0) with Craft Intent but no materials
        actor = EntityState(
            id=1, kind="hero", position=(0.0, 0.0), readiness=100.0,
            identity=IdentityComponent(
                craft_target="craft_steel_sword",
                known_recipes={"craft_steel_sword"} # Set for recipes
            ),
            navigation=NavigationComponent(target=(0.0, 0.0)),
            strategic=StrategicComponent(
                leads={
                    "lead_ore": LeadState(id="lead_ore", kind="location", subject="iron_ore", detail="1.0,0.0")
                }
            ),
            inventory=InventoryComponent(
                max_slots=10, 
                gold=100, 
                items=[ItemStack("wood", 1), ItemStack("iron_ore", 1)]
            )
        )
        
        new_nodes = dict(state.resource_nodes)
        new_nodes[101] = node
        
        new_entities = dict(state.entities)
        new_entities[1] = actor
        
        return replace(state, 
            entities=new_entities, 
            resource_nodes=new_nodes,
            town_tiles={(0,0)},
            building_tiles={(0,0): "blacksmith"}
        )


def build_scenario_state(scenario_id: str) -> AuthoritativeState:
    """Factory to build the initial state for a specific scenario."""
    base_state = AuthoritativeState(tick=0, seed=42)
    
    if scenario_id == "MVM_PATH_20":
        return GameplayInjector.build_movement_test(base_state, 20)
    elif scenario_id == "RES_HARVEST_3":
        return GameplayInjector.build_harvest_test(base_state, 3)
    elif scenario_id == "INTEG_RESOURCE_LOOP":
        return GameplayInjector.build_integrated_loop(base_state)
    elif scenario_id == "COMBAT_ARENA_5V5":
        return ArenaInjector.build_team_battle(base_state, 5)
    elif scenario_id == "COMBAT_ARENA_STRESS_50V50":
        return ArenaInjector.build_team_battle(base_state, 50)
    elif scenario_id == "COMBAT_ARENA_PROGRESSION":
        return ArenaInjector.build_progression_test(base_state)
    elif scenario_id == "COMBAT_ARENA_MORTALITY":
        return ArenaInjector.build_mortality_test(base_state)
    elif scenario_id == "COMBAT_ARENA_TACTICAL":
        return ArenaInjector.build_tactical_test(base_state)
    elif scenario_id == "COMBAT_ARENA_SOCIAL":
        return ArenaInjector.build_social_test(base_state)
    elif scenario_id == "COMBAT_ARENA_QUESTS":
        return ArenaInjector.build_quest_battle(base_state)
    
    elif scenario_id == "COMBAT_ARENA_REGIONAL":
        return ArenaInjector.build_regional_control_test(base_state)
    
    return base_state


def get_scenario_expectations(scenario_id: str) -> ScenarioExpectations:
    """M10 Law: Scenario-bound pass/fail criteria and sampling intervals."""
    from src.certification.models import FailureKind
    
    # 1. Clean Baselines
    if scenario_id in ("IDLE_CLEAN", "STEADY_STATE_NORMAL", "QUIET_TICK_STABILITY"):
        return ScenarioExpectations(
            required_governor_modes=["NORMAL"],
            requires_recovery=False,
            requires_semantic_equivalence=True,
            required_sampling_interval_ticks=10,
            allowed_failure_kinds=[FailureKind.NONE],
            reproducibility_required=True
        )
    
    # NEW: Gameplay Surface Scenarios (Milestone 5)
    elif scenario_id in (
        "MVM_PATH_20", "RES_HARVEST_3", "INTEG_RESOURCE_LOOP", 
        "COMBAT_ARENA_5V5", "COMBAT_ARENA_STRESS_50V50", 
        "COMBAT_ARENA_PROGRESSION", "COMBAT_ARENA_MORTALITY",
        "COMBAT_ARENA_QUESTS", "COMBAT_ARENA_REGIONAL"
    ):
        return ScenarioExpectations(
            required_governor_modes=["NORMAL"],
            requires_recovery=False,
            requires_semantic_equivalence=True, # STRICT LAW: Gameplay must be deterministic
            required_sampling_interval_ticks=1, # Sample every tick for progression tests
            allowed_failure_kinds=[FailureKind.NONE],
            reproducibility_required=True
        )

    # 2. Pressure & Degradation
    elif scenario_id in ("RAM_PRESSURE", "TICK_BUDGET_PRESSURE", "QUEUE_INFLIGHT_PRESSURE", "WORK_DEBT_BUILDUP"):
        return ScenarioExpectations(
            required_governor_modes=["NORMAL", "DEGRADED"],
            requires_recovery=True,
            requires_semantic_equivalence=False,
            max_recovery_ticks=100,
            recovery_time_limit_ticks=150,
            required_sampling_interval_ticks=5,
            allowed_failure_kinds=[FailureKind.NONE, FailureKind.FAILED_ENVELOPE, FailureKind.FAILED_RECOVERY_TIMEOUT]
        )
    elif scenario_id == "REPLAY_PRESSURE":
        return ScenarioExpectations(
            required_governor_modes=["NORMAL", "DEGRADED", "SURVIVAL"],
            requires_recovery=True,
            requires_semantic_equivalence=False,
            required_sampling_interval_ticks=5,
            allowed_failure_kinds=[FailureKind.NONE, FailureKind.FAILED_ENVELOPE, FailureKind.FAILED_REPLAY_PERSISTENCE, FailureKind.FAILED_RECOVERY_TIMEOUT]
        )
        
    # 3. Recovery Paths
    elif scenario_id == "DEGRADED_NORMAL_RECOVERY":
        return ScenarioExpectations(
            required_governor_modes=["NORMAL", "DEGRADED"],
            requires_recovery=True,
            requires_semantic_equivalence=False,
        )
    elif scenario_id == "SURVIVAL_NORMAL_RECOVERY":
        return ScenarioExpectations(
            required_governor_modes=["NORMAL", "DEGRADED", "SURVIVAL"],
            requires_recovery=True,
            requires_semantic_equivalence=False,
            max_recovery_ticks=150,
            recovery_time_limit_ticks=200
        )

    # 4. Lifecycle & Faults
    elif scenario_id == "STARTUP_VALIDATION":
        return ScenarioExpectations(
            required_governor_modes=["NORMAL"],
            expected_lifecycle_outcome="SUCCESS",
        )
    elif scenario_id == "REPLAY_OVERFLOW_SURVIVAL":
        return ScenarioExpectations(
            required_governor_modes=["SURVIVAL"],
            requires_recovery=False,
            requires_semantic_equivalence=False,
            expected_lifecycle_outcome="SUCCESS",
            allowed_failure_kinds=[FailureKind.NONE, FailureKind.FAILED_REPLAY_PERSISTENCE]
        )
    elif scenario_id == "SHUTDOWN_TIMEOUT_SURVIVAL":
        return ScenarioExpectations(
            expected_lifecycle_outcome="TIMEOUT",
            shutdown_timeout_s=0.0, # Force immediate timeout
            requires_semantic_equivalence=False,
            allowed_failure_kinds=[FailureKind.NONE, FailureKind.FAILED_LIFECYCLE]
        )
    elif scenario_id == "WORKER_FAILURE_FALLBACK":
        return ScenarioExpectations(
            required_governor_modes=["NORMAL"],
            allowed_failure_kinds=[FailureKind.NONE, FailureKind.FAILED_WORKER_PROPAGATION],
            requires_semantic_equivalence=True  # Should fallback deterministically
        )

    # 5. Equivalence (Milestone D closure)
    elif scenario_id in ("DET_EQUIV", "LOCAL_CONCURRENT_EQUIV"):
        return ScenarioExpectations(
            required_governor_modes=["NORMAL"],
            requires_recovery=False,
            requires_semantic_equivalence=True,
            required_sampling_interval_ticks=1,
            allowed_failure_kinds=[FailureKind.NONE],
            reproducibility_required=True
        )
    
    # Release verification scenarios
    elif scenario_id == "MISSING_SCENARIO_BLOCK":
        return ScenarioExpectations(
            allowed_failure_kinds=[FailureKind.FAILED_MISSING_SCENARIO]
        )
        
    else:
        return ScenarioExpectations() # Default safe
