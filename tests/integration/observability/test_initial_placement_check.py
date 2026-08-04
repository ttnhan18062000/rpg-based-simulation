"""
Integration tests for TCK-20260716-PLACELEGAL-HARDLAW: Kernel._run_initial_placement_check().

New Kernel construction fixture file (per test_plan.md item 6/7's own noted contingency) —
tests/integration/kernel/test_kernel_boundaries.py's fixtures build a clean, collision-free
AuthoritativeState and do not need a colliding one, so a dedicated file keeps that suite unchanged.
"""
import gc
import json
import pytest
from unittest.mock import MagicMock

from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.event_recorder import EventRecorder
from src.observability.cognition.decision_trace_writer import DecisionTraceWriter
from src.observability.hard_law_monitor import HardLawMonitor, HardLawViolationError


@pytest.fixture
def mock_profile():
    return RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=10,
        max_replay_buffer_kb=100,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=16.6
    )


@pytest.fixture
def mock_rng():
    rng = MagicMock(spec=DeterministicRNG)
    rng.next_int.return_value = 42
    rng.get_state.return_value = None
    rng.get_int.return_value = 4242
    return rng


@pytest.fixture(autouse=True)
def _reset_observability_mode():
    yield
    ObservabilityConfig.set_override_mode(None)


def _colliding_state() -> AuthoritativeState:
    e1 = V2EntityBuilder(1).location(5.0, 5.0).combat(alive=True).build()
    e2 = V2EntityBuilder(2).location(5.0, 5.0).combat(alive=True).build()
    return AuthoritativeState(tick=0, seed=42, entities={1: e1, 2: e2})


def test_kernel_init_calls_check_initial_placement_once(monkeypatch, mock_profile, mock_rng):
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    call_count = {"n": 0}
    original = HardLawMonitor.check_initial_placement

    def _spy(state):
        call_count["n"] += 1
        return original(state)

    monkeypatch.setattr(HardLawMonitor, "check_initial_placement", _spy)

    kernel = Kernel(profile=mock_profile, state=_colliding_state(), rng=mock_rng)
    try:
        assert call_count["n"] == 1

        spawn_violations = [v for v in kernel.status.hard_law_violations if v.law_id == "LAW-SPAWN-OCCUPANCY"]
        assert len(spawn_violations) == 1

        v_path = kernel._artifact_repo.resolve_path(kernel._run_id, "violations")
        with open(v_path, "r", encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        spawn_records = [r for r in records if r["law_id"] == "LAW-SPAWN-OCCUPANCY"]
        assert len(spawn_records) == 1
        assert spawn_records[0]["tick"] == 0

        # Advancing ticks must not re-trigger the one-time init check.
        kernel.tick_once()
        assert call_count["n"] == 1
    finally:
        kernel.shutdown(timeout_s=1.0)


def test_check_initial_placement_mode_gating_matches_precedent(mock_profile, mock_rng):
    # OFF: check is skipped entirely — no artifact repo, nothing recorded.
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    kernel = Kernel(profile=mock_profile, state=_colliding_state(), rng=mock_rng)
    try:
        assert kernel._artifact_repo is None
        assert not hasattr(kernel.status, "hard_law_violations")
    finally:
        kernel.shutdown(timeout_s=1.0)

    # DEBUG / CERTIFICATION: construction raises HardLawViolationError (fail-fast).
    # __init__ never returns on this path, so there is no kernel handle to call
    # shutdown() through — the EventRecorder and DecisionTraceWriter it already
    # started (pre-existing to this ticket: __init__ has no exception-safe
    # teardown for anything raised after their construction) must be reclaimed
    # via gc instead.
    for fail_fast_mode in (ObservabilityMode.DEBUG, ObservabilityMode.CERTIFICATION):
        ObservabilityConfig.set_override_mode(fail_fast_mode)
        try:
            with pytest.raises(HardLawViolationError) as exc_info:
                Kernel(profile=mock_profile, state=_colliding_state(), rng=mock_rng)
            assert "LAW-SPAWN-OCCUPANCY" in str(exc_info.value)
        finally:
            for obj in gc.get_objects():
                if isinstance(obj, EventRecorder) and getattr(obj, "_worker", None) is not None:
                    obj.shutdown()
                elif isinstance(obj, DecisionTraceWriter) and getattr(obj, "_worker", None) is not None:
                    obj.close()

    # LIGHT and LONG_RUN: construction succeeds without raising; violation is
    # still recorded onto status (LONG_RUN deliberately inherits the existing
    # fall-through gap — neither logs nor raises, per Resolved Decision 2).
    for non_fail_fast_mode in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
        ObservabilityConfig.set_override_mode(non_fail_fast_mode)
        kernel = Kernel(profile=mock_profile, state=_colliding_state(), rng=mock_rng)
        try:
            spawn_violations = [v for v in kernel.status.hard_law_violations if v.law_id == "LAW-SPAWN-OCCUPANCY"]
            assert len(spawn_violations) == 1
        finally:
            kernel.shutdown(timeout_s=1.0)
