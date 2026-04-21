from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from src_v2.certification.models import ScenarioExpectations
from src_v2.core.state import AuthoritativeState, EntityState


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


class GameplayInjector:
    """Helper to inject real gameplay scenarios into the simulation."""

    @staticmethod
    def build_movement_test(state: AuthoritativeState, distance: int = 20) -> AuthoritativeState:
        """Setup an entity moving in a straight line."""
        from src_v2.core.state import EntityState
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
        from src_v2.core.state import EntityState, ResourceNodeState, InteractionComponent, InventoryComponent
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
        from src_v2.core.state import (
            EntityState, ResourceNodeState, InteractionComponent, 
            InventoryComponent, IdentityComponent
        )
        from src_v2.core.strategic import StrategicComponent, BlockerState, LeadState
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
                known_recipes={"craft_steel_sword"}, # Set for recipes
                navigation_target=(0.0, 0.0)
            ),
            strategic=StrategicComponent(
                leads={
                    "lead_ore": LeadState(id="lead_ore", kind="location", subject="iron_ore", detail="1.0,0.0")
                }
            ),
            inventory=InventoryComponent(max_slots=10, gold=100, items=["wood", "iron_ore"])
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
    
    return base_state


def get_scenario_expectations(scenario_id: str) -> ScenarioExpectations:
    """M10 Law: Scenario-bound pass/fail criteria and sampling intervals."""
    from src_v2.certification.models import FailureKind
    
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
    elif scenario_id in ("MVM_PATH_20", "RES_HARVEST_3", "INTEG_RESOURCE_LOOP"):
        return ScenarioExpectations(
            required_governor_modes=["NORMAL"],
            requires_recovery=False,
            requires_semantic_equivalence=True, # STRICT LAW: Gameplay must be deterministic
            required_sampling_interval_ticks=2,
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
