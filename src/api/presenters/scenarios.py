# Compliance IDs: INFRA-134, INFRA-135, INFRA-136, INFRA-216, API-001
from __future__ import annotations

from typing import Any, Dict

from src.engine.scenario_runtime import ScenarioRuntimeService


class ScenarioPresenter:
    """
    Shapes ScenarioRuntimeService state into API-safe dicts.
    M12 Law: MUST NOT mutate authoritative state.
    VERIFIED v2: INFRA-134, INFRA-135, INFRA-136
    """

    @staticmethod
    def present_status(svc: ScenarioRuntimeService) -> Dict[str, Any]:
        return {
            "tick": svc.tick,
            "objective_state": svc.objective_state.value,
            "alive_entity_count": svc.alive_entity_count,
            "key_metrics": {},
        }

    @staticmethod
    def present_checkpoint(path: str, tick: int) -> Dict[str, Any]:
        return {
            "path": path,
            "tick": tick,
        }

    @staticmethod
    def present_restore(svc: ScenarioRuntimeService) -> Dict[str, Any]:
        return {
            "tick": svc.tick,
            "objective_state": svc.objective_state.value,
        }
