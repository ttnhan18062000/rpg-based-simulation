# Compliance IDs: INFRA-216
from __future__ import annotations

from typing import Optional

from src.engine.scenario_runtime import ScenarioRuntimeService

_registry: dict[str, ScenarioRuntimeService] = {}


def register(scenario_id: str, svc: ScenarioRuntimeService) -> None:
    """Register a live ScenarioRuntimeService under a scenario ID."""
    _registry[scenario_id] = svc


def get(scenario_id: str) -> Optional[ScenarioRuntimeService]:
    """Return the registered service, or None if not found."""
    return _registry.get(scenario_id)


def unregister(scenario_id: str) -> None:
    """Remove a scenario ID from the registry (call on abort/completion)."""
    _registry.pop(scenario_id, None)
