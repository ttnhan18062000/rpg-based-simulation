"""The pinned governor pins what the host's speed could change, at the source: the Kernel feeds it zeroed signals, so neither the mode nor the per-phase budgets can
read a clock (TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR). Before it, ``PinnedNormalGovernor`` pinned the
mode only, and ``PhaseBudgetGovernor`` still switched the scan policy and the movement and strategic budgets at absolute per-phase costs of 10 and 15 ms."""
from __future__ import annotations

import itertools
import time

import pytest

from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.phase_governor import PhaseBudgetGovernor
from src.engine.policy import ScanPolicy
from src.observability.reporting.artifact_repository import RunManifest
from src.observability.reporting.run_determinism import NonAuditRunError, require_host_independent_runs, run_is_host_independent
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world

TICKS = 12


def _budgets_seen(monkeypatch, governor, flags=None):
    """Run a few ticks of a real world while every clock read advances 20 ms (so every phase costs over 15 ms) and return the budgets the governor chose."""
    seen = []
    original = PhaseBudgetGovernor.evaluate

    def spy(profile, signals, current_mode, current_tick, opt_profile=None):
        out = original(profile, signals, current_mode, current_tick, opt_profile)
        if signals is not None:  # the kernel's per-tick call; other callers pass no signals
            seen.append((out, signals))
        return out

    monkeypatch.setattr(PhaseBudgetGovernor, "evaluate", staticmethod(spy))
    ticker = itertools.count(0, 20_000_000)
    monkeypatch.setattr(time, "perf_counter_ns", lambda: next(ticker))
    state = compile_world("frontier_living_world", 42)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True, **(flags or {})},
                    executor=LocalSequentialExecutor(), governor=governor)
    for _ in range(TICKS):
        kernel.tick_once()
    kernel.shutdown()
    return seen, kernel


def test_the_pinned_governor_keeps_the_normal_budgets_whatever_the_phases_cost(monkeypatch):
    seen, _ = _budgets_seen(monkeypatch, PinnedNormalGovernor())
    assert len(seen) >= TICKS - 1
    first = seen[0][0]
    assert all(b == first for b, _ in seen)  # the same budgets on every tick, whatever the (fake) clock says
    assert all(not sig.phase_costs_ms and sig.tick_compute_ms == 0.0 for _, sig in seen)  # because the governor saw no timings


def test_positive_control_an_unpinned_run_under_the_same_clock_does_switch_its_budgets(monkeypatch):
    from src.engine.governor import ResourceGovernor

    seen, _ = _budgets_seen(monkeypatch, ResourceGovernor())
    budgets = [b for b, _ in seen]
    assert any(b != budgets[0] for b in budgets) or any(sig.phase_costs_ms for _, sig in seen), "the fake clock did not put any phase under pressure"


def test_the_kernel_zeroes_the_signals_for_audit_mode_and_for_a_pinning_governor_only(monkeypatch):
    from src.engine.governor import ResourceGovernor

    state = compile_world("urban_political", 42)

    def build(governor, flags):
        return Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True, **flags}, executor=LocalSequentialExecutor(), governor=governor)

    results = {}
    for name, governor, flags in (("pinned", PinnedNormalGovernor(), {}), ("audit", ResourceGovernor(), {"audit_mode": True}), ("live", ResourceGovernor(), {})):
        kernel = build(governor, flags)
        results[name] = kernel._signals_zeroed
        kernel.shutdown()
    assert results == {"pinned": True, "audit": True, "live": False}


def test_a_run_manifest_records_audit_mode_and_zeroed_signals_as_typed_fields():
    base = dict(run_id="r", scenario_name="s", scenario_type="t", seed=1, observability_mode="m", started_at="now", ticks_requested=1)
    assert RunManifest(**base).signals_zeroed is None and RunManifest(**base).audit_mode is None  # an older manifest says nothing
    m = RunManifest(**base, audit_mode=True, signals_zeroed=True)
    assert run_is_host_independent(m.model_dump()) is True
    assert RunManifest.model_validate_json(m.model_dump_json()).signals_zeroed is True


def test_a_tool_that_compares_runs_refuses_a_run_not_recorded_as_host_independent():
    require_host_independent_runs({"a": {"signals_zeroed": True}, "b": {"signals_zeroed": True}})
    with pytest.raises(NonAuditRunError) as exc:
        require_host_independent_runs({"a": {"signals_zeroed": True}, "b": {"signals_zeroed": False}, "c": {}})
    assert "b" in str(exc.value) and "c" in str(exc.value) and "'a'" not in str(exc.value)
