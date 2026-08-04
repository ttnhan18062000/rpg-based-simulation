"""Tests for tools/calibrate_simq.py's queue-drop / SURVIVAL-mode integrity guard
(TCK-20260702-OBSISO-ISOLATION-PROOF, Steps 7-12).

_run_engine() builds its own Kernel internally and immediately drives the tick
loop — there is no seam for a caller to mutate the Kernel's EventRecorder queue
between construction and the first tick. These tests monkeypatch
src.engine.kernel.Kernel with a subclass that runs a post-construction hook,
since _run_engine() does `from src.engine.kernel import Kernel` at call time
and picks up whatever the module attribute currently resolves to.
"""
from __future__ import annotations

import json
import os

import pytest

import tools.calibrate_simq as cal_mod
from src.simulation_quality.run_health import RunHealthRecord


def _force_small_queue(kernel, max_size: int) -> None:
    """Shrink an already-built Kernel's EventRecorder queue and stop its drain worker.

    Test-only lever (Key Decision #2, TCK-20260702-OBSISO-ISOLATION-PROOF) — mirrors
    tests/unit/observability/test_obs_backpressure.py::_set_queue_fill's existing
    precedent of mutating BoundedObservabilityQueue state directly rather than adding
    a production Kernel constructor flag/env override for queue size. Stopping the
    drain worker makes the forced state deterministic instead of racing its 10ms
    drain cadence.
    """
    kernel.event_recorder.queue.max_size = max_size
    kernel.event_recorder._worker.stop()


def _patch_kernel_with_hook(monkeypatch, post_construct_hook) -> None:
    """Monkeypatch src.engine.kernel.Kernel so _run_engine()'s internally-built
    Kernel instance runs post_construct_hook(kernel) immediately after __init__,
    before _run_engine() starts its tick loop.
    """
    import src.engine.kernel as kernel_mod

    real_kernel_cls = kernel_mod.Kernel

    class _HookedKernel(real_kernel_cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            post_construct_hook(self)

    monkeypatch.setattr(kernel_mod, "Kernel", _HookedKernel)


class TestQueueOverflowGuard:
    def test_calibrate_simq_fails_on_forced_queue_overflow(self, monkeypatch, tmp_path):
        """AC #3: a run that genuinely drops >=1 envelope must hard-fail rather than
        silently writing quality_report.json.

        ObservabilityController.evaluate() enters SURVIVAL exactly at fill>=1.00 —
        the identical condition BoundedObservabilityQueue.try_push() uses to decide
        it's full — so EventRecorder.record() always diverts to the counter-only
        SURVIVAL path before try_push() can ever see a full queue in a single-threaded
        caller. Overriding get_size() decouples the mode-controller's fill perception
        from the queue's real length, which is the only way to reach a genuine
        dropped_count>0 (as opposed to SURVIVAL mode-shed, the separate mechanism
        covered below) through the real record() call path.
        """

        def _hook(kernel):
            _force_small_queue(kernel, max_size=2)
            kernel.event_recorder.queue.get_size = lambda: 0

        _patch_kernel_with_hook(monkeypatch, _hook)

        cal_dir = str(tmp_path / "cal_out")
        os.makedirs(cal_dir, exist_ok=True)

        # "generic" (hero + staggered goblins, no engagement) is nearly inert —
        # 20 ticks produce ~1 event. sandbox_world's compiled scenario has active
        # factions/quests generating events every tick, which this test needs to
        # actually exceed a max_size=2 queue.
        with pytest.raises(cal_mod.CalibrationIntegrityError):
            cal_mod._run_engine("sandbox_world", seed=42, ticks=20, entity_count=10, cal_dir=cal_dir)

        sidecar_path = os.path.join(cal_dir, "quality_report.run_health.json")
        assert os.path.exists(sidecar_path), "RunHealthRecord sidecar must be written even on guard failure"
        record = RunHealthRecord.from_dict(json.loads(open(sidecar_path, encoding="utf-8").read()))
        assert record.guard_passed is False
        assert record.dropped_count > 0

    def test_calibrate_simq_succeeds_normally_with_zero_drops(self, tmp_path):
        """Anti-drift: the new guard must not change the existing exit-0-on-success
        contract when dropped_count == 0 and mode stays NORMAL throughout — every
        anchor-based calibration test depends on this."""
        cal_dir = str(tmp_path / "cal_out")
        os.makedirs(cal_dir, exist_ok=True)

        run_dir, elapsed, run_id = cal_mod._run_engine(
            "generic", seed=42, ticks=5, entity_count=4, cal_dir=cal_dir,
        )
        assert run_dir
        assert elapsed >= 0

        sidecar_path = os.path.join(cal_dir, "quality_report.run_health.json")
        assert os.path.exists(sidecar_path)
        record = RunHealthRecord.from_dict(json.loads(open(sidecar_path, encoding="utf-8").read()))
        assert record.guard_passed is True
        assert record.dropped_count == 0
        assert record.survival_triggered is False


class TestSurvivalModeGuard:
    def test_survival_mode_flags_run_instead_of_silently_grading(self, monkeypatch, tmp_path):
        """AC #4 / Scope: SURVIVAL (mode-shed, zero queue push) is a distinct loss
        mechanism from queue-drop (overflow-evict) — the guard must flag it
        independently, even when dropped_count stays 0.
        """

        def _hook(kernel):
            # No get_size() override here (unlike the overflow test above): real
            # fill must genuinely reach >=1.00 so ObservabilityController.evaluate()
            # enters SURVIVAL through its real code path.
            _force_small_queue(kernel, max_size=1)

        _patch_kernel_with_hook(monkeypatch, _hook)

        cal_dir = str(tmp_path / "cal_out")
        os.makedirs(cal_dir, exist_ok=True)

        # sandbox_world (see overflow test above) — "generic" is too inert to
        # reliably fill even a max_size=1 queue.
        with pytest.raises(cal_mod.CalibrationIntegrityError):
            cal_mod._run_engine("sandbox_world", seed=42, ticks=20, entity_count=10, cal_dir=cal_dir)

        sidecar_path = os.path.join(cal_dir, "quality_report.run_health.json")
        record = RunHealthRecord.from_dict(json.loads(open(sidecar_path, encoding="utf-8").read()))
        assert record.guard_passed is False
        assert record.survival_triggered is True
        assert record.pressure_mode_final == "SURVIVAL"
        assert record.dropped_count == 0, (
            "SURVIVAL preempts try_push() entirely once the queue is at capacity — "
            "dropped_count must stay 0, proving this is a distinct loss mechanism"
        )


class TestRunHealthRecordRoundTrip:
    def test_to_dict_from_dict_round_trip(self):
        record = RunHealthRecord(
            dropped_count=7,
            pressure_mode_final="DEGRADED",
            survival_triggered=True,
            guard_passed=False,
        )
        assert RunHealthRecord.from_dict(record.to_dict()) == record

    def test_round_trip_through_json_serialization(self):
        record = RunHealthRecord(
            dropped_count=0,
            pressure_mode_final="NORMAL",
            survival_triggered=False,
            guard_passed=True,
        )
        reconstituted = RunHealthRecord.from_dict(json.loads(json.dumps(record.to_dict())))
        assert reconstituted == record
