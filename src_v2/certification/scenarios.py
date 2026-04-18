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
    """M9 Law: Scenario-bound pass/fail criteria and sampling intervals."""
    if scenario_id == "IDLE_CLEAN":
        return ScenarioExpectations(
            required_governor_modes=["NORMAL"],
            requires_recovery=False,
            requires_semantic_equivalence=True,
            sampling_interval_ticks=10
        )
    elif scenario_id == "RAM_PRESSURE":
        return ScenarioExpectations(
            required_governor_modes=["NORMAL", "DEGRADED"],
            requires_recovery=True,
            requires_semantic_equivalence=False, # We expect some shedding if configured
            max_recovery_ticks=100,
            sampling_interval_ticks=5
        )
    elif scenario_id == "DET_EQUIV":
        return ScenarioExpectations(
            required_governor_modes=["NORMAL"],
            requires_recovery=False,
            requires_semantic_equivalence=True,
            sampling_interval_ticks=1
        )
    else:
        return ScenarioExpectations() # Default safe
