"""Standalone ON-flag population-floor guard for `hero_guild_routing`
(TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY, plan.md Step 4).

`test_corpus_diversity.py::test_population_stability` tests every corpus world, including
`hero_guild_routing`, with `Kernel(flags={"no_frame_pacing": True})` only -- it never reads a
world's profile `feature_flags:` block, so it exercises `hero_guild_routing` with
`ENABLE_ADVENTURE_ROUTING` at its default OFF state, not the ON state this world's own profile
(`config/simulation_quality/profiles/hero_guild_routing.yaml`) sets from first compile. That
generic guard stays untouched and world-agnostic (OQ-1 resolution, plan.md Step 3) -- it is the
baseline survival-mechanic regression guard every corpus world gets, not proof of this world's
ON-flag population floor.

This module is the authoritative check for that floor: it applies the profile's
`ENABLE_ADVENTURE_ROUTING=ON` override onto the compiled `AuthoritativeState.feature_flags`
before constructing the `Kernel` -- mirroring `tools/calibrate_simq.py::_run_engine`'s own
profile-activation mechanism (lines ~205-226) -- so the floor assertion below runs against the
world's true ON-flag condition, not a silent retest of OFF under a new name.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.worldassembly

REPO_ROOT = Path(__file__).resolve().parents[3]
WORLDS_ROOT = REPO_ROOT / "data" / "worlds"
PROFILE_PATH = (
    REPO_ROOT / "config" / "simulation_quality" / "profiles" / "hero_guild_routing.yaml"
)


@pytest.mark.slow
def test_hero_guild_routing_population_stability_adventure_routing_on() -> None:
    """>=60% alive floor through 500 ticks at seed 42, ENABLE_ADVENTURE_ROUTING genuinely ON."""
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from src.config.profiles import PROD_SMALL
    from src.domains.optimization.feature_flags import FeatureMode

    seed = 42
    repo = WorldRepository(str(WORLDS_ROOT))
    spec = repo.load_world("hero_guild_routing")
    state, report = WorldCompiler.compile(spec, seed)
    starting = report["entity_count"]
    floor = 0.6 * starting

    raw_profile = yaml.safe_load(PROFILE_PATH.read_text()) or {}
    profile_flags = {str(k): str(v) for k, v in (raw_profile.get("feature_flags") or {}).items()}
    assert profile_flags.get("ENABLE_ADVENTURE_ROUTING") == "ON", (
        "hero_guild_routing.yaml no longer sets ENABLE_ADVENTURE_ROUTING: ON -- this test's "
        "premise (proving the ON-flag floor) no longer holds against the profile on disk."
    )
    existing_flags = dict(state.feature_flags or {})
    existing_flags["ENABLE_ADVENTURE_ROUTING"] = FeatureMode.ON
    state = dataclasses.replace(state, feature_flags=existing_flags)

    rng = DeterministicRNG(seed)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True})
    try:
        for tick in range(1, 501):
            kernel.tick_once()
            if tick % 50 == 0:
                alive = sum(1 for e in kernel._state.entities.values() if e.combat.alive)
                assert alive >= floor, (
                    f"hero_guild_routing: population collapsed at tick {tick} under "
                    f"ENABLE_ADVENTURE_ROUTING=ON -- alive={alive}/{starting} "
                    f"({alive / starting:.1%}), floor is 60% ({floor:.1f})"
                )
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
