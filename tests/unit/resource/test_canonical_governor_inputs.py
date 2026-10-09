"""How the governors read the cost inputs under the Canonical contract (PERF-D1; TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY, step 3)."""
from __future__ import annotations

import math

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.governance import PressureSignals, RuntimeMode
from src.engine import work_units
from src.engine.governor import ResourceGovernor
from src.engine.phase_governor import PhaseBudgetGovernor, ScanPolicy
from src.engine.runtime_status import RuntimeStatus
from src.engine.signal_source import CanonicalSignalSource, HostReadings
from src.perf.scenarios import build_idle_state


def _profile(budget: float = 100.0, dwell: int = 3, window: int = 3, workers: int = 0, depth: int = 100) -> RuntimeProfile:
    return RuntimeProfile(
        name="canonical_governor", hardware_class=HardwareClass.CLASS_B, max_ram_mb=1024, max_cpu_percent=90.0, max_worker_count=workers,
        max_queue_depth=depth, max_replay_buffer_kb=64, max_observability_budget_percent=5.0, max_tick_budget_ms=budget,
        dwell_time_ticks=dwell, confidence_window_ticks=window, signal_contract="canonical",
    )


@pytest.mark.parametrize("cost", [0.0, 50.0, 69.9, 70.0, 99.9, 100.0, 149.9, 150.0, 400.0])
def test_a_modelled_cost_decides_like_the_same_measured_cost(cost):
    """Equal ratios, equal decisions: the thresholds keep their millisecond meaning (owner decision Q-B)."""
    profile, governor = _profile(), ResourceGovernor()
    measured = governor._get_indicated_mode(profile, PressureSignals(tick_compute_ms=cost))
    modelled = governor._get_indicated_mode(profile, PressureSignals(tick_compute_ms=0.0, tick_cost=cost))
    assert measured == modelled


def test_an_explicit_tick_budget_replaces_the_profile_budget():
    governor = ResourceGovernor()
    signals = PressureSignals(tick_cost=80.0, tick_budget=50.0)  # 80 >= 1.5 * 50
    assert governor._get_indicated_mode(_profile(budget=100.0), signals) is RuntimeMode.SURVIVAL
    assert governor._get_indicated_mode(_profile(budget=100.0), PressureSignals(tick_cost=80.0)) is RuntimeMode.CONSTRAINED


def test_recovery_reads_the_rolling_average_of_the_modelled_cost():
    profile, governor, status = _profile(dwell=1, window=2), ResourceGovernor(), RuntimeStatus()
    status.current_mode = RuntimeMode.DEGRADED
    for _ in range(3):  # measured time says "overloaded", the model says "light": recovery follows the model
        status.record_signals(PressureSignals(tick_compute_ms=500.0, tick_cost=10.0))
    status.mode_dwell_ticks = 5
    assert governor._can_recover(profile, status.signal_history[-1], status)
    status = RuntimeStatus()
    status.current_mode = RuntimeMode.DEGRADED
    for _ in range(3):  # and the other way round
        status.record_signals(PressureSignals(tick_compute_ms=1.0, tick_cost=500.0))
    status.mode_dwell_ticks = 5
    assert not governor._can_recover(profile, status.signal_history[-1], status)


def test_memory_and_replay_backlog_are_not_canonical_inputs():
    state, profile = build_idle_state(entity_count=5), _profile()
    host = HostReadings({"worker_utilization": 1.0, "queue_utilization": 1.0, "active_workers": 9},
                        {"backlog_kb": 10**9}, {"rss_mb": 1.0e7}, {})
    signals = CanonicalSignalSource().tick_start_signals(state=state, profile=profile, status=RuntimeStatus(), host=host)
    assert (signals.memory_estimate_mb, signals.replay_backlog_kb, signals.active_workers) == (0.0, 0, 0)
    assert ResourceGovernor()._get_indicated_mode(profile, signals) is RuntimeMode.NORMAL


@pytest.mark.parametrize("entities,workers,depth", [(0, 2, 100), (1, 2, 100), (49, 4, 10), (5000, 2, 3), (10**6, 1, 1)])
def test_queue_and_worker_proxies_stay_in_the_unit_interval(entities, workers, depth):
    queue = work_units.queue_utilization_proxy(entities, workers, depth)
    worker = work_units.worker_utilization_proxy(entities, workers)
    assert 0.0 <= queue <= 1.0 and 0.0 <= worker <= 1.0


def test_proxies_report_zero_without_workers_and_one_at_saturation():
    assert work_units.queue_utilization_proxy(10**6, 0, 10) == 0.0
    assert work_units.worker_utilization_proxy(10**6, 0) == 0.0
    assert work_units.worker_utilization_proxy(2 * work_units.THREAD_CHUNK_CAP, 2) == 1.0
    assert work_units.queue_utilization_proxy(work_units.THREAD_CHUNK_CAP * 10, 2, 10) == 1.0
    assert work_units.worker_utilization_proxy(work_units.THREAD_CHUNK_CAP, 2) == 0.5


def test_the_canonical_source_gives_the_per_phase_rules_nothing_to_read():
    """Locomotion and final_integrity have no pre-policy counter, so under Canonical they never fire; under Live they do."""
    profile = _profile(budget=100.0)
    heavy = {"locomotion": 90.0, "final_integrity": 90.0}
    live = PhaseBudgetGovernor.evaluate(profile, PressureSignals(phase_costs_ms=heavy), RuntimeMode.NORMAL, 1)
    canonical = PhaseBudgetGovernor.evaluate(profile, PressureSignals(phase_costs_ms=heavy, phase_cost={}), RuntimeMode.NORMAL, 1)
    normal = PhaseBudgetGovernor.evaluate(profile, None, RuntimeMode.NORMAL, 1)
    assert live.scan_policy is ScanPolicy.EXACT_DIRTY and live.movement_budget == 100 and live.strategic_budget == 8
    assert canonical == normal


def test_the_tick_level_compaction_rule_reads_the_modelled_cost():
    profile = _profile(budget=100.0)
    hot = PhaseBudgetGovernor.evaluate(profile, PressureSignals(tick_compute_ms=0.0, tick_cost=85.0, phase_cost={}), RuntimeMode.NORMAL, 1)
    cool = PhaseBudgetGovernor.evaluate(profile, PressureSignals(tick_compute_ms=500.0, tick_cost=10.0, phase_cost={}), RuntimeMode.NORMAL, 1)
    assert hot.compaction_level == "AGGRESSIVE" and cool.compaction_level == "NORMAL"


@pytest.mark.parametrize("dwell,window", [(1, 1), (3, 3), (10, 5)])
@pytest.mark.parametrize("high,low", [(105.0, 95.0), (72.0, 40.0), (155.0, 60.0)])
def test_mode_transitions_stay_within_the_anti_thrash_bounds(dwell, window, high, low):
    """A modelled cost that sits on a threshold and flips every tick must not defeat the dwell, the confidence window or the watermark."""
    profile, governor, status = _profile(dwell=dwell, window=window), ResourceGovernor(), RuntimeStatus()
    ticks, modes, transitions = 60, [], []
    for tick in range(ticks):
        cost = high if tick % 2 == 0 else low
        signals = PressureSignals(tick_cost=cost)
        before = status.current_mode
        governor.evaluate(profile, signals, status, tick)
        status.record_signals(signals)
        modes.append(status.current_mode)
        if status.current_mode != before:
            transitions.append((tick, before, status.current_mode))
    de_escalations = [t for t in transitions if t[2] < t[1]]
    for tick, _, _ in de_escalations:
        previous = [t[0] for t in transitions if t[0] < tick]
        assert not previous or tick - previous[-1] >= dwell, "a de-escalation came sooner than the dwell time"
    assert len(transitions) <= math.ceil(ticks / dwell) + 2
    for i in range(len(modes) - 2 * (window + dwell)):
        span = modes[i:i + 2 * (window + dwell)]
        flips = sum(1 for a, b in zip(span, span[1:]) if a < b)
        assert flips <= 1, "the mode escalated twice inside one confidence window plus dwell time"
