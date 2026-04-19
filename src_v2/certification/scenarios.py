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
