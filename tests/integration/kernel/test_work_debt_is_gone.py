"""Deferred work is gone (TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE, Phase B).

Replaces the guard `test_work_debt_stays_empty_in_production.py`, which showed that nothing ever increased `state.work_debt`. This commit
removes the producers of deferred and periodic work: the scheduler's periodic, deferred (`DRAIN_DEBT`) and opportunistic branches,
`PeriodicDefinition`, the executor's `DRAIN_DEBT` handling, `SimulationDomainLogic.drain_debt`, the four policy fields that only those
branches read, the worker-result system fields and the kernel's merge of system results. Later commits remove the state fields and the
signal; the checks for those are added with them.
"""
from __future__ import annotations

import dataclasses

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.governance import RuntimeMode
from src.core.work import WorkClass
from src.core.worker_protocol import WorkerResult
from src.engine import executor, scheduler
from src.engine.domain_logic import SimulationDomainLogic
from src.engine.kernel import Kernel
from src.engine.policy import GovernorPolicy
from src.perf.scenarios import build_idle_state
from src.platform.rng import DeterministicRNG


def test_the_removed_names_are_gone():
    assert not hasattr(scheduler, "PeriodicDefinition")
    assert not hasattr(SimulationDomainLogic, "drain_debt")
    assert "DRAIN_DEBT" not in open(executor.__file__).read()
    assert not {"work_debt_update", "subsystem_id"} & set(WorkerResult.__dataclass_fields__)
    removed = {"allow_opportunistic", "allow_non_authoritative_periodic", "diagnostic_verbosity", "metrics_detail"}
    assert not removed & {f.name for f in dataclasses.fields(GovernorPolicy)}


def test_the_scheduler_takes_no_periodic_definitions():
    with pytest.raises(TypeError):
        scheduler.DeterministicScheduler(periodic_defs=[])  # type: ignore[call-arg]


@pytest.mark.parametrize("mode", [RuntimeMode.NORMAL, RuntimeMode.SURVIVAL])
def test_a_run_produces_only_critical_entity_work_and_never_drops_work(mode):
    profile = RuntimeProfile(
        name="no_deferred_work", hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=0,
        max_queue_depth=500, max_replay_buffer_kb=4096, max_observability_budget_percent=10.0, max_tick_budget_ms=100000.0,
    )
    kernel = Kernel(profile, build_idle_state(entity_count=20), DeterministicRNG(7), flags={"no_frame_pacing": True, "no_replay": True})
    try:
        kernel._status.current_mode = mode
        for _ in range(3):
            kernel.tick_once()
            assert {item.work_class for item in kernel._current_work_items} <= {WorkClass.CRITICAL}
        assert kernel.status.total_dropped_work == 0
    finally:
        kernel.shutdown()


def test_the_state_and_update_fields_are_gone():
    """C2: `work_debt` and `periodic_due_ticks` left `AuthoritativeState`, and `work_debt_updates` / `periodic_updates` left `StateUpdate`."""
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate
    from src.engine.checkpoint import CanonicalStateHasher

    assert not {"work_debt", "periodic_due_ticks"} & set(AuthoritativeState.__dataclass_fields__)
    assert not {"work_debt_updates", "periodic_updates"} & set(StateUpdate.__dataclass_fields__)
    with pytest.raises(TypeError):
        AuthoritativeState(tick=0, seed=1, work_debt={})  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        StateUpdate(work_debt_updates={})  # type: ignore[call-arg]
    assert not {"work_debt", "periodic_due_ticks"} & set(CanonicalStateHasher.to_canonical_data(AuthoritativeState(tick=0, seed=1)))


def test_the_signal_the_thresholds_and_the_reporting_are_gone():
    """C3: no `work_debt_total` signal, no `max_work_debt` profile field, no debt metric, and the certification measurement point lost its key."""
    from src.certification.models import MeasurementPoint
    from src.config.profiles import PROD_DEFAULT, PROD_SMALL, RuntimeProfile
    from src.core.governance import PressureSignals
    from src.engine.observability import RuntimeSnapshot
    from src.observability.prometheus_collector import PrometheusMetricsCollector

    assert "work_debt_total" not in PressureSignals.__dataclass_fields__
    assert "work_debt_total" not in RuntimeSnapshot.__dataclass_fields__
    assert "work_debt" not in MeasurementPoint.__dataclass_fields__
    assert "max_work_debt" not in RuntimeProfile.model_fields
    assert not hasattr(PROD_SMALL, "max_work_debt") and not hasattr(PROD_DEFAULT, "max_work_debt")

    class _Manager:
        def get_metrics_snapshot(self):
            return {"tick": 1, "work_debt_total": 5}  # a stale snapshot key must not resurrect the metric

    metric_names = {family.name for family in PrometheusMetricsCollector(_Manager()).collect()}
    assert metric_names, "the collector produced no metric at all, so the absence check proves nothing"
    assert "sim_work_debt_total" not in metric_names


def test_the_certification_result_schema_was_bumped_for_the_removed_key():
    from src.certification import models

    assert "certification_result.v2" in open(models.__file__).read()
