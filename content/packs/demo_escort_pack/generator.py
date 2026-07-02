"""
content/packs/demo_escort_pack/generator.py
───────────────────────────────────────────────────────────────────────────────
Demo feature pack: adds the ESCORT_DIGNITARY route type to the adventure_routing
domain without modifying any file under src/engine/ or src/domains/.

Registered at load time by FeaturePackLoader via manifest.yaml extension_point.
"""

from __future__ import annotations

from typing import Any


class EscortDignitaryGenerator:
    """Route generator for the ESCORT_DIGNITARY adventure route type.

    Demonstrates the extension pattern: a pack can add new route families by
    registering a generator class in the adventure_routing FeatureRegistry.
    The engine retrieves this class at tick time via registry.lookup("ESCORT_DIGNITARY").
    """

    REGISTRY_KEY = "ESCORT_DIGNITARY"

    @classmethod
    def generate(cls, context: Any) -> dict[str, Any]:
        """Produce a route option payload for escorting a dignitary.

        Parameters
        ----------
        context:
            Tick context (entity state, world state).  Typed loosely so the
            demo pack does not import from src/domains/ directly.

        Returns
        -------
        dict
            Minimal route option payload consumed by the engine's route scorer.
        """
        return {
            "family": cls.REGISTRY_KEY,
            "score": 0.6,
            "confidence": 0.7,
            "expected_benefit": 0.8,
            "expected_risk": 0.4,
            "reason": "Escort dignitary to safety",
        }
