"""
Singleton accessors for PerceptionGate and MotivationPressureResolver.

Provides lazy-initialised module singletons for use in the tactical engine.
Configurable for tests via configure_behavior_consumers / reset_behavior_consumers.
"""

from __future__ import annotations

from typing import Dict, Optional, Any

_perception_gate = None
_pressure_resolver = None
_catalog = None


def configure_behavior_consumers(catalog: Any) -> None:
    """Inject a pre-loaded catalog for tests or custom environments."""
    global _catalog, _perception_gate, _pressure_resolver
    from src.world.perception.gate import PerceptionGate
    from src.world.motivation.pressure_resolver import MotivationPressureResolver
    _catalog = catalog
    _perception_gate = PerceptionGate(catalog)
    _pressure_resolver = MotivationPressureResolver(catalog)


def reset_behavior_consumers() -> None:
    """Reset singletons (for test isolation)."""
    global _catalog, _perception_gate, _pressure_resolver
    _catalog = _perception_gate = _pressure_resolver = None


def get_perception_gate():
    """Return the module-level PerceptionGate, auto-initialising if needed."""
    global _perception_gate
    if _perception_gate is None:
        _auto_init()
    return _perception_gate


def get_pressure_resolver():
    """Return the module-level MotivationPressureResolver, auto-initialising if needed."""
    global _pressure_resolver
    if _pressure_resolver is None:
        _auto_init()
    return _pressure_resolver


def get_cognition_profile_definition(profile_id: str):
    """Return the named CognitionProfileDefinition via the warmed catalog singleton."""
    global _catalog
    if _catalog is None:
        _auto_init()
    return _catalog.get_cognition_profile(profile_id)


def get_role_definition(role_id: str):
    """Return the named RoleDefinition via the warmed catalog singleton."""
    global _catalog
    if _catalog is None:
        _auto_init()
    return _catalog.get_role(role_id)


def _auto_init() -> None:
    """Load default catalog and initialise consumers."""
    global _catalog, _perception_gate, _pressure_resolver
    from src.content.repository import CatalogRepository
    from src.world.perception.gate import PerceptionGate
    from src.world.motivation.pressure_resolver import MotivationPressureResolver
    _catalog = CatalogRepository("data/content")
    _catalog.load_all()
    _perception_gate = PerceptionGate(_catalog)
    _pressure_resolver = MotivationPressureResolver(_catalog)


def get_entity_signals(entity: Any) -> Dict[str, str]:
    """
    Derive the natural signals emitted by an entity for perception checks.

    Signal keys match PerceptionGate's _SENSE_TO_SIGNAL values.
    Reads from entity.identity.properties with sensible defaults.
    """
    props: Dict[str, str] = {}
    if hasattr(entity, "identity") and hasattr(entity.identity, "properties"):
        props = entity.identity.properties or {}
    return {
        "visibility": props.get("visibility_signal", "medium"),
        "noise": props.get("noise_signal", "low"),
        "scent": props.get("scent_signal", "low"),
        "magic_signal": props.get("magic_signal", "none"),
        "life_signal": props.get("life_signal", "low"),
        "vibration": props.get("vibration_signal", "low"),
        "social_signal": props.get("social_signal", "none"),
    }
