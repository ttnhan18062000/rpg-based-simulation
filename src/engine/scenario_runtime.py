# Compliance IDs: INFRA-118
"""
ScenarioRuntimeService — controllable execution wrapper around the Kernel.

Owns the Kernel lifecycle for a single scenario run. Exposes start/pause/resume/
step/abort so test harnesses and future REST layers can drive tick progression
without embedding kernel construction details.

Out of scope (see sibling tickets):
  E31B — ScenarioObjectiveFSM (victory condition evaluation)
  E31C — checkpoint / restore
  E31D — REST API
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.scenarios.schema import SimulationScenarioDefinition


class ScenarioObjectiveState(str, Enum):
    """Execution-level state of a running scenario."""

    RUNNING = "RUNNING"
    OBJECTIVE_MET = "OBJECTIVE_MET"
    OBJECTIVE_FAILED = "OBJECTIVE_FAILED"
    STALLED = "STALLED"
    ABORTED = "ABORTED"


class ScenarioRuntimeService:
    """
    Owns a Kernel for the duration of one scenario run.

    The tick loop is synchronous — no threads. pause()/resume() are cooperative:
    the caller drives tick progression by calling start()/resume() which run the
    loop until completion, or step() which advances exactly one tick.

    Usage::

        spec = SimulationScenarioDefinition(...)
        svc = ScenarioRuntimeService(spec)
        svc.start(tick_limit=100)           # runs 100 ticks
        assert svc.objective_state == ScenarioObjectiveState.RUNNING

        svc2 = ScenarioRuntimeService(spec)
        svc2.step()                          # tick 1
        svc2.pause()
        svc2.resume(tick_limit=50)           # ticks 2–50
        svc2.abort()
    """

    __slots__ = ("_spec", "_kernel", "_state", "_tick", "_paused")

    def __init__(self, spec: SimulationScenarioDefinition) -> None:
        self._spec = spec
        self._kernel = None
        self._state: ScenarioObjectiveState = ScenarioObjectiveState.RUNNING
        self._tick: int = 0
        self._paused: bool = False

    # ── public API ─────────────────────────────────────────────────────────────

    def start(self, tick_limit: int = 500) -> None:
        """Build kernel and run the tick loop up to *tick_limit* ticks.

        Idempotent if called while paused — resumes from current tick instead.
        Raises RuntimeError if already aborted.
        """
        if self._state == ScenarioObjectiveState.ABORTED:
            raise RuntimeError("Cannot start an aborted ScenarioRuntimeService.")
        if self._kernel is None:
            self._kernel = self._build_kernel()
        self._paused = False
        self._run_loop(tick_limit)

    def pause(self) -> None:
        """Signal the tick loop to halt after the current tick.

        Has no effect if already paused or not running.
        """
        self._paused = True

    def resume(self, tick_limit: int = 500) -> None:
        """Clear the pause flag and continue the tick loop up to *tick_limit* total ticks.

        Raises RuntimeError if the kernel has not been started or has been aborted.
        """
        if self._kernel is None:
            raise RuntimeError("Cannot resume: service has not been started.")
        if self._state == ScenarioObjectiveState.ABORTED:
            raise RuntimeError("Cannot resume an aborted ScenarioRuntimeService.")
        self._paused = False
        self._run_loop(tick_limit)

    def step(self) -> None:
        """Advance exactly one tick.

        Builds the kernel on first call if not already started.
        Raises RuntimeError if aborted.
        """
        if self._state == ScenarioObjectiveState.ABORTED:
            raise RuntimeError("Cannot step an aborted ScenarioRuntimeService.")
        if self._kernel is None:
            self._kernel = self._build_kernel()
        if self._paused:
            # step() overrides pause for a single tick
            pass
        self._kernel.tick_once()
        self._tick += 1

    def abort(self) -> None:
        """Shutdown the kernel and mark the scenario as ABORTED.

        Safe to call multiple times (idempotent after first call).
        """
        self._state = ScenarioObjectiveState.ABORTED
        self._paused = True
        if self._kernel is not None:
            self._kernel.shutdown()

    # ── properties ─────────────────────────────────────────────────────────────

    @property
    def tick(self) -> int:
        """Current completed tick count."""
        return self._tick

    @property
    def objective_state(self) -> ScenarioObjectiveState:
        """Current execution-level objective state.

        Evaluation of victory/failure conditions is handled by E31B
        (ScenarioObjectiveFSM). This property reflects the value set by
        abort() or externally via the FSM hook.
        """
        return self._state

    @property
    def alive_entity_count(self) -> int:
        """Number of entities currently in the authoritative state.

        Returns 0 if the kernel has not been started.
        """
        if self._kernel is None:
            return 0
        return len(self._kernel.state.entities)

    # ── internal ───────────────────────────────────────────────────────────────

    def _run_loop(self, tick_limit: int) -> None:
        """Run tick_once() until tick_limit is reached or paused/aborted."""
        while (
            self._tick < tick_limit
            and not self._paused
            and self._state == ScenarioObjectiveState.RUNNING
        ):
            self._kernel.tick_once()
            self._tick += 1

    def _build_kernel(self):
        """Construct a minimal Kernel for this scenario spec."""
        from src.config.profiles import RuntimeProfile, HardwareClass
        from src.core.state import AuthoritativeState
        from src.platform.rng import DeterministicRNG
        from src.engine.kernel import Kernel

        profile = RuntimeProfile(
            name=self._spec.id,
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=512,
            max_cpu_percent=100.0,
            max_worker_count=0,
            max_queue_depth=1000,
            max_replay_buffer_kb=64,
            max_observability_budget_percent=5.0,
            max_tick_budget_ms=200.0,
        )
        state = AuthoritativeState(tick=0, seed=0)
        rng = DeterministicRNG(base_seed=0)
        return Kernel(profile, state, rng, flags={"no_replay": True})
