from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from src.api.engine_manager import V2EngineManager

if TYPE_CHECKING:
    from src.simulation_quality.quality_hub import QualityHub
    from src.simulation_quality.persistence import QualityPersistence

_engine_manager: Optional[V2EngineManager] = None
_quality_hub: Optional["QualityHub"] = None
_quality_persistence: Optional["QualityPersistence"] = None

def set_engine_manager(manager: V2EngineManager):
    global _engine_manager
    _engine_manager = manager

def get_engine_manager() -> V2EngineManager:
    if _engine_manager is None:
        raise RuntimeError("V2EngineManager not initialized.")
    return _engine_manager

def set_quality_hub(hub: "QualityHub") -> None:
    global _quality_hub
    _quality_hub = hub

def get_quality_hub() -> Optional["QualityHub"]:
    return _quality_hub

def set_quality_persistence(persistence: "QualityPersistence") -> None:
    global _quality_persistence
    _quality_persistence = persistence

def get_quality_persistence() -> Optional["QualityPersistence"]:
    return _quality_persistence
