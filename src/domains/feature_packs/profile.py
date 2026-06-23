"""
src/domains/feature_packs/profile.py
───────────────────────────────────────────────────────────────────────────────
RuntimeProfile — selects which feature packs are active for a simulation run.

Stored in SimulationScenarioDefinition.runtime_profile (optional).
When None, the implicit profile is RuntimeProfile(active_pack_names=["base"]).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RuntimeProfile(BaseModel):
    """Selects which feature packs are active for a given simulation run.

    Fields
    ------
    active_pack_names:
        Pack names to activate, in declaration order. CompatibilityResolver
        resolves these into a deterministic load order at scenario init.
        "base" is always implicitly included even if omitted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    active_pack_names: list[str] = Field(default_factory=list)
