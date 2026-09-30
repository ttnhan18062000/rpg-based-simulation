"""Shared scenario helper: compile -> stage -> run -> observe, with an optional control arm.

Level contract: docs/testing/test_taxonomy.md section 5. A scenario claims **occurrence and effect**; where
the claim needs one, run the same scenario twice differing only in the precondition under test
(`run_with_control`) so a pass cannot come from something unrelated to the mechanism.

The helper owns no gameplay knowledge: it neither knows a mechanic nor mutates state outside the kernel's
own tick. Staging callables receive a state and return the staged state.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from src.config.profiles import PROD_SMALL, RuntimeProfile
from src.core.state import AuthoritativeState
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

DEFAULT_SEED = 42
DEFAULT_FLAGS: Dict[str, Any] = {"no_frame_pacing": True}

Stage = Callable[[AuthoritativeState], AuthoritativeState]
Observe = Callable[[AuthoritativeState], Any]


@dataclass(frozen=True)
class ScenarioRun:
    """One executed scenario: what was staged, what the kernel produced, what was observed."""

    seed: int
    ticks: int
    observed: Any
    final_state: AuthoritativeState
    final_hash: str


@dataclass(frozen=True)
class ControlledRun:
    """Treatment and control arms of one scenario, run with the same seed, profile and ticks."""

    treatment: ScenarioRun
    control: ScenarioRun


def compile_world(world_id: str, seed: int = DEFAULT_SEED, worlds_dir: str = os.path.join("data", "worlds")) -> AuthoritativeState:
    """Compile a declared world into a fresh authoritative state (one world per test)."""
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec, context = WorldRepository(worlds_dir).load_world_with_context(world_id)
    state, _report = WorldCompiler.compile(spec, seed, context=context)
    return state


def run_scenario(
    state: AuthoritativeState,
    *,
    ticks: int,
    observe: Observe,
    stage: Optional[Stage] = None,
    seed: int = DEFAULT_SEED,
    profile: RuntimeProfile = PROD_SMALL,
    flags: Optional[Dict[str, Any]] = None,
) -> ScenarioRun:
    """Stage `state`, advance the real kernel `ticks` ticks, then observe the final authoritative state."""
    if ticks < 0:
        raise ValueError("ticks must be >= 0")
    staged = stage(state) if stage is not None else state
    kernel = Kernel(profile=profile, state=staged, rng=DeterministicRNG(seed),
                    flags=dict(DEFAULT_FLAGS if flags is None else flags))
    try:
        for _ in range(ticks):
            kernel.tick_once()
        final_state = kernel._state
        return ScenarioRun(seed=seed, ticks=ticks, observed=observe(final_state), final_state=final_state,
                           final_hash=CanonicalStateHasher.get_hash(final_state))
    finally:
        kernel.shutdown()


def run_with_control(
    build_state: Callable[[], AuthoritativeState],
    *,
    ticks: int,
    observe: Observe,
    stage_treatment: Stage,
    stage_control: Optional[Stage] = None,
    seed: int = DEFAULT_SEED,
    profile: RuntimeProfile = PROD_SMALL,
    flags: Optional[Dict[str, Any]] = None,
) -> ControlledRun:
    """Run the scenario twice from fresh states: once with the treatment staged, once with the control.

    `build_state` is called per arm, so the arms share nothing. `stage_control=None` runs the control
    unstaged (the mechanism's precondition absent)."""
    common = dict(ticks=ticks, observe=observe, seed=seed, profile=profile, flags=flags)
    return ControlledRun(
        treatment=run_scenario(build_state(), stage=stage_treatment, **common),
        control=run_scenario(build_state(), stage=stage_control, **common),
    )
