# Compliance IDs: INFRA-118, INFRA-214, INFRA-215
"""
ScenarioRuntimeService — controllable execution wrapper around the Kernel.

Owns the Kernel lifecycle for a single scenario run. Exposes start/pause/resume/
step/abort so test harnesses and future REST layers can drive tick progression
without embedding kernel construction details.

E31B additions:
  - ObjectiveEvaluator: pure static evaluator for victory_conditions.
  - Stall detector on ScenarioRuntimeService: fires STALLED after STALL_THRESHOLD
    consecutive ticks with zero kernel events.
  - _evaluate_after_tick() wired into both _run_loop() and step().

Out of scope (see sibling tickets):
  E31C — checkpoint / restore
  E31D — REST API
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.scenarios.schema import SimulationScenarioDefinition
    from src.core.state import AuthoritativeState
    from src.observability.event_recorder import EventRecorder

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

STALL_THRESHOLD: int = 50
"""Number of consecutive zero-event ticks before the stall detector fires STALLED."""


class ScenarioObjectiveState(str, Enum):
    """Execution-level state of a running scenario."""

    RUNNING = "RUNNING"
    OBJECTIVE_MET = "OBJECTIVE_MET"
    OBJECTIVE_FAILED = "OBJECTIVE_FAILED"
    STALLED = "STALLED"
    ABORTED = "ABORTED"


class ObjectiveEvaluator:
    """Pure static evaluator for scenario victory_conditions.

    Reads world state — never mutates it. Accepts conditions as a list of
    ``VictoryCondition`` objects or plain dicts (for test convenience); both
    provide ``.kind`` / ``.value`` attributes or ``["kind"]`` / ``["value"]``
    keys respectively.

    Evaluation order: conditions are tested in list order; first match wins.
    If ``conditions`` is ``None`` or empty, returns ``RUNNING`` immediately.
    """

    @staticmethod
    def evaluate(
        state: "AuthoritativeState",
        conditions: "list | None",
    ) -> ScenarioObjectiveState:
        """Evaluate ``conditions`` against ``state`` and return the resulting state.

        Args:
            state: Current ``AuthoritativeState`` snapshot (read-only).
            conditions: List of ``VictoryCondition`` objects or dicts, or ``None``.

        Returns:
            ``OBJECTIVE_MET``, ``OBJECTIVE_FAILED``, or ``RUNNING``.
        """
        if not conditions:
            return ScenarioObjectiveState.RUNNING

        for cond in conditions:
            if isinstance(cond, dict):
                kind = cond.get("kind")
                value = cond.get("value")
            else:
                kind = getattr(cond, "kind", None)
                value = getattr(cond, "value", None)

            if kind == "tick_limit" and value is not None and state.tick >= value:
                return ScenarioObjectiveState.OBJECTIVE_MET

            if kind == "entity_count" and value is not None:
                alive = sum(
                    1 for e in state.entities.values() if e.combat.alive
                )
                if alive < value:
                    return ScenarioObjectiveState.OBJECTIVE_FAILED

        return ScenarioObjectiveState.RUNNING


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

    __slots__ = (
        "_spec",
        "_kernel",
        "_state",
        "_tick",
        "_paused",
        "_stall_counter",
        "_last_event_tick",
        "_initial_state",
        "_scenario_event_recorder",
    )

    def __init__(
        self,
        spec: "SimulationScenarioDefinition",
        initial_state: Optional["AuthoritativeState"] = None,
        scenario_event_recorder: Optional["EventRecorder"] = None,
    ) -> None:
        """
        `scenario_event_recorder` is a narrow, scenario-bookkeeping-only side channel —
        it only ever receives `scenario_objective_completed`/`progressed`/`stalled`
        (TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY). It is NOT the real
        per-tick kernel event stream (combat, cooperation, hard-law, etc.) — that lives on
        the `Kernel` this service builds internally, as its own separate `event_recorder`
        property (`Kernel.event_recorder`, fed by `EventExtractor.extract()` every tick).
        The two are unrelated objects that happened to share a name; do not assume this
        parameter carries the full stream.
        """
        self._spec = spec
        self._kernel = None
        self._initial_state = initial_state
        self._scenario_event_recorder = scenario_event_recorder
        self._state: ScenarioObjectiveState = ScenarioObjectiveState.RUNNING
        self._tick: int = 0
        self._paused: bool = False
        self._stall_counter: int = 0
        self._last_event_tick: int = 0

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
        Raises RuntimeError if already in a terminal state (ABORTED, OBJECTIVE_MET,
        OBJECTIVE_FAILED, or STALLED).
        """
        if self._state == ScenarioObjectiveState.ABORTED:
            raise RuntimeError("Cannot step an aborted ScenarioRuntimeService.")
        _OBJECTIVE_TERMINAL = (
            ScenarioObjectiveState.OBJECTIVE_MET,
            ScenarioObjectiveState.OBJECTIVE_FAILED,
            ScenarioObjectiveState.STALLED,
        )
        if self._state in _OBJECTIVE_TERMINAL:
            raise RuntimeError(
                f"Cannot step a scenario in terminal state: {self._state}."
            )
        if self._kernel is None:
            self._kernel = self._build_kernel()
        if self._paused:
            # step() overrides pause for a single tick
            pass
        self._kernel.tick_once()
        self._tick += 1
        self._evaluate_after_tick()

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

    @property
    def final_state(self) -> Optional["AuthoritativeState"]:
        """Return the kernel's AuthoritativeState after a terminal episode.

        Returns None if the kernel has not been started yet (episode not begun).
        Available in all objective states including ABORTED — callers should
        check objective_state before relying on the contents.
        """
        if self._kernel is None:
            return None
        return self._kernel.state

    @property
    def run_id(self) -> Optional[str]:
        """The underlying Kernel's run_id, or None if not yet started."""
        if self._kernel is None:
            return None
        return getattr(self._kernel, "_run_id", None)

    def flush_pending_grief_triggers(self) -> None:
        """Drain any Kernel-queued grief trigger detected on the episode's final tick, before
        final_state is read. No-op if the kernel was never built or nothing is queued."""
        if self._kernel is not None:
            self._kernel.drain_pending_triggers_at_teardown()

    # ── internal ───────────────────────────────────────────────────────────────

    def _run_loop(self, tick_limit: int) -> None:
        """Run tick_once() until tick_limit is reached or paused/aborted/terminal."""
        while (
            self._tick < tick_limit
            and not self._paused
            and self._state == ScenarioObjectiveState.RUNNING
        ):
            self._kernel.tick_once()
            self._tick += 1
            self._evaluate_after_tick()

    def _evaluate_after_tick(self) -> None:
        """Evaluate objective conditions and the stall detector after each tick.

        Called immediately after ``tick_once()`` and ``self._tick += 1`` in both
        ``_run_loop()`` and ``step()``.  Mutates ``self._state`` if a terminal
        condition is reached and sets ``self._paused = True`` to break
        ``_run_loop()``.  Does **not** call ``kernel.shutdown()`` — callers use
        ``abort()`` for cleanup (which calls shutdown idempotently).

        Evaluation order (per investigation.md §Stall Detector):
          1. Objective conditions — OBJECTIVE_MET / OBJECTIVE_FAILED take priority.
          2. Stall detector — STALLED only fires when no objective condition fired.
        """
        # 1. Objective evaluation (takes priority over stall)
        conditions = self._spec.victory_conditions
        if conditions:
            result = ObjectiveEvaluator.evaluate(
                self._kernel.state,
                list(conditions),
            )
            if result != ScenarioObjectiveState.RUNNING:
                self._state = result
                self._paused = True
                if self._scenario_event_recorder is not None:
                    from src.observability.events import SimulationEvent
                    self._scenario_event_recorder.record(SimulationEvent(
                        event_type="scenario_objective_completed",
                        event_category="infrastructure",
                        tick=self._tick,
                        entity_id=None,
                        severity="INFO",
                        source_system="scenario_runtime",
                        message="",
                        payload={
                            "scenario_id": getattr(self._spec, "id", ""),
                            "outcome": result.name,
                        },
                    ))
                return
            # scenario_objective_progressed: fires every tick while objective is still RUNNING
            # to signal forward progress (intermediate signal distinct from scenario_objective_completed)
            if self._scenario_event_recorder is not None and self._tick > 0:
                from src.observability.events import SimulationEvent
                self._scenario_event_recorder.record(SimulationEvent(
                    event_type="scenario_objective_progressed",
                    event_category="infrastructure",
                    tick=self._tick,
                    entity_id=None,
                    severity="INFO",
                    source_system="scenario_runtime",
                    message="",
                    payload={
                        "scenario_id": getattr(self._spec, "id", ""),
                        "progress_fraction": self._tick / max(1, getattr(self._spec, "tick_limit", 500)),
                        "tick": self._tick,
                    },
                ))

        # 2. Stall detector
        # _current_tick_event_count is set by kernel.tick_once() to the count of
        # SimulationEvent objects generated in that tick (kernel.py line 764).
        # Any event > 0 resets the counter; zero events increment it.
        # Simplification: all event kinds count — no filtering by category.
        # Defensive int cast: in tests, mock kernels may expose a MagicMock attribute
        # rather than a real int; int() normalises it safely.
        try:
            event_count = int(getattr(self._kernel, "_current_tick_event_count", 0))
        except (TypeError, ValueError):
            event_count = 0
        if event_count > 0:
            self._stall_counter = 0
            self._last_event_tick = self._tick
        else:
            self._stall_counter += 1
            if self._stall_counter > STALL_THRESHOLD:
                self._state = ScenarioObjectiveState.STALLED
                self._paused = True
                if self._scenario_event_recorder is not None:
                    from src.observability.events import SimulationEvent
                    self._scenario_event_recorder.record(SimulationEvent(
                        event_type="scenario_stalled",
                        event_category="infrastructure",
                        tick=self._tick,
                        entity_id=None,
                        severity="WARNING",
                        source_system="scenario_runtime",
                        message="",
                        payload={
                            "scenario_id": getattr(self._spec, "id", ""),
                            "stall_counter": self._stall_counter,
                            "last_event_tick": self._last_event_tick,
                        },
                    ))

    def _build_kernel(self):
        """Construct a minimal Kernel for this scenario spec.

        If ``self._initial_state`` was provided at construction time, it is used
        as the kernel's starting ``AuthoritativeState`` and its ``seed`` is also
        forwarded to ``DeterministicRNG`` so that both state and RNG agree on the
        episode seed (required for determinism — INFRA-101/102).
        """
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
        if self._initial_state is not None:
            state = self._initial_state
            rng = DeterministicRNG(base_seed=self._initial_state.seed)
        else:
            state = AuthoritativeState(tick=0, seed=0)
            rng = DeterministicRNG(base_seed=0)
        return Kernel(profile, state, rng, flags={"no_replay": True})


# E31C: re-export so callers can do `from src.engine.scenario_runtime import ScenarioCheckpointer`
from src.engine.scenario_checkpoint import ScenarioCheckpointer  # noqa: E402, F401
