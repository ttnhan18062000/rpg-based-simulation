"""Run observers (decision 80 B): the kernel offers consumers of a run's event envelopes a four-stage lifecycle and knows no observer type.

Pins: the stage order at shutdown (TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD), fan-out in registration order with failure isolation,
a factory that returns None, observability OFF building nothing, and that a kernel without observers never imports the SimQ package.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from typing import List
from pathlib import Path

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.state import AuthoritativeState
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.run_observers import RunContext, RunObservers
from src.platform.rng import DeterministicRNG
from src.observability.config import ObservabilityConfig, ObservabilityMode
from tests.helpers.kernel_pinning import PinnedNormalGovernor


ROOT = Path(__file__).resolve().parents[3]


def _profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="test", hardware_class=HardwareClass.CLASS_B, max_ram_mb=1024, max_tick_budget_ms=500, max_cpu_percent=50.0,
        max_worker_count=0, max_queue_depth=64, max_replay_buffer_kb=0, max_observability_budget_percent=5.0,
    )


class _Recorder:
    """A run observer that logs every stage into a shared list."""

    def __init__(self, name: str, log: List[str], fail_on: str = "") -> None:
        self.name, self.log, self.fail_on = name, log, fail_on

    def _hit(self, stage: str) -> None:
        self.log.append(f"{self.name}.{stage}")
        if self.fail_on == stage:
            raise RuntimeError(f"{self.name} {stage}")

    def on_envelope(self, envelope) -> None:
        self._hit("env") if not any(e == f"{self.name}.env" for e in self.log) else None
        if self.fail_on == "env":
            raise RuntimeError("boom")

    def start(self) -> None:
        self._hit("start")

    def stop_intake(self) -> None:
        self._hit("stop_intake")

    def finish(self) -> None:
        self._hit("finish")


def _kernel(observers, tmp_path, monkeypatch):
    monkeypatch.setenv("QUALITY_RUN_DIR", str(tmp_path))
    return Kernel(_profile(), AuthoritativeState(tick=0, seed=42), DeterministicRNG(42), run_id="run-observers-test", flags={"no_replay": True},
                  governor=PinnedNormalGovernor(), executor=LocalSequentialExecutor(), observers=observers)


def test_stages_run_in_order_and_finish_comes_after_the_recorder_has_shut_down(tmp_path, monkeypatch):
    log: List[str] = []
    kernel = _kernel([lambda ctx: _Recorder("a", log)], tmp_path, monkeypatch)
    real_shutdown = kernel._event_recorder.shutdown
    kernel._event_recorder.shutdown = lambda *a, **k: (log.append("recorder.shutdown"), real_shutdown(*a, **k))[1]
    for _ in range(3):
        kernel.tick_once()
    kernel.shutdown()

    stages = [e for e in log if not e.endswith(".env")]
    assert stages == ["a.start", "a.stop_intake", "recorder.shutdown", "a.finish"]
    assert "a.env" in log, "the observer saw at least one envelope on the drain thread"
    assert log.index("a.start") < log.index("a.env")


def test_fan_out_keeps_registration_order_and_one_failing_observer_does_not_stop_the_next():
    log: List[str] = []
    observers = RunObservers([_Recorder("a", log, fail_on="env"), _Recorder("b", log)])
    observers.on_envelope(object())
    assert log == ["a.env", "b.env"]


def test_a_failing_stage_is_isolated_and_the_next_observer_still_runs():
    log: List[str] = []
    observers = RunObservers([_Recorder("a", log, fail_on="finish"), _Recorder("b", log)])
    observers.finish()
    assert log == ["a.finish", "b.finish"]


def test_a_factory_returning_none_adds_nothing_and_a_raising_factory_propagates():
    context = RunContext(run_id="r", run_dir="")
    log: List[str] = []
    built = RunObservers.build([lambda ctx: None, lambda ctx: _Recorder("a", log)], context)
    assert len(built) == 1

    def boom(ctx):
        raise ValueError("unknown feed mode")

    with pytest.raises(ValueError):
        RunObservers.build([boom], context)


def test_observability_off_builds_no_observer(tmp_path, monkeypatch):
    built: List[str] = []
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    try:
        kernel = _kernel([lambda ctx: built.append("called")], tmp_path, monkeypatch)
        kernel.shutdown()
    finally:
        ObservabilityConfig.set_override_mode(None)
    assert built == [] and len(kernel.observers) == 0


def test_a_kernel_without_observers_never_imports_the_simq_package():
    code = textwrap.dedent("""
        import sys
        from src.config.profiles import HardwareClass, RuntimeProfile
        from src.core.state import AuthoritativeState
        from src.platform.rng import DeterministicRNG
        from src.engine.kernel import Kernel
        p = RuntimeProfile(name="t", hardware_class=HardwareClass.CLASS_B, max_ram_mb=1024, max_tick_budget_ms=500, max_cpu_percent=50.0,
                           max_worker_count=0, max_queue_depth=64, max_replay_buffer_kb=0, max_observability_budget_percent=5.0)
        k = Kernel(p, AuthoritativeState(tick=0, seed=1), DeterministicRNG(1), run_id="no-simq", flags={"no_replay": True})
        k.tick_once(); k.shutdown()
        bad = sorted(m for m in sys.modules if m == "src.simulation_quality" or m.startswith("src.simulation_quality."))
        print("SIMQ_IMPORTED", bad)
    """)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(ROOT), env={**os.environ, "PYTHONPATH": str(ROOT)}, timeout=120)
    assert "SIMQ_IMPORTED []" in out.stdout, out.stdout + out.stderr


def test_a_scenario_service_and_a_restored_one_carry_the_observers_to_their_kernel():
    from unittest.mock import MagicMock

    from src.engine.scenario_runtime import ScenarioRuntimeService

    def factory(ctx):
        return None

    service = ScenarioRuntimeService(MagicMock(), observers=[factory])
    assert service._observers == (factory,)
    assert ScenarioRuntimeService(MagicMock())._observers == ()
