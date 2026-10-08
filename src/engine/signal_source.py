# Compliance IDs: INFRA-005, RES-025
"""Where the governors' pressure signals come from (PERF-D1 signal contract).

The kernel builds ``PressureSignals`` twice per tick: at the start of tick N+1 for ``ResourceGovernor.evaluate`` and at the end of tick N for
``RuntimeStatus.record_signals``. ``LiveSignalSource`` is that construction, moved out of ``Kernel`` unchanged. ``ZeroedSignalSource`` is the
``audit_mode`` variant that deletes every pressure input at the start of the tick. A source reads what it is given and decides nothing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Mapping

from src.config.profiles import SignalContract
from src.core.governance import PressureSignals

if TYPE_CHECKING:
    from src.config.profiles import RuntimeProfile
    from src.core.state import AuthoritativeState
    from src.engine.runtime_status import RuntimeStatus


@dataclass(frozen=True, slots=True)
class HostReadings:
    """What the kernel read from the worker pool, the replay buffer and the platform collector for this tick, plus the tick's metrics."""

    worker_stats: Mapping[str, Any]
    replay_stats: Mapping[str, Any]
    platform_signals: Mapping[str, Any]
    metrics: Dict[str, float]


class LiveSignalSource:
    """Today's behaviour: cost inputs are measured milliseconds, memory and replay backlog come from the host."""

    def tick_start_signals(
        self,
        *,
        state: AuthoritativeState,
        profile: RuntimeProfile,
        status: RuntimeStatus,
        host: HostReadings,
    ) -> PressureSignals:
        """Signals for the governor at the start of a tick: last tick's measured cost, current host readings."""
        compute_ms = status.signal_history[-1].tick_compute_ms if status.signal_history else 0.0
        if state.tick <= 5:
            compute_ms = min(compute_ms, profile.max_tick_budget_ms * 0.5)
        return PressureSignals(
            work_debt_total=sum(state.work_debt.values()),
            tick_compute_ms=compute_ms,
            worker_utilization=host.worker_stats["worker_utilization"],
            queue_utilization=host.worker_stats["queue_utilization"],
            memory_estimate_mb=host.platform_signals["rss_mb"],
            replay_backlog_kb=host.replay_stats["backlog_kb"],
            active_workers=host.worker_stats["active_workers"],
            dropped_work_delta=status.dropped_work_delta,
            phase_costs_ms=(status.signal_history[-1].phase_costs_ms
                            if status.signal_history else {}),
            metrics=host.metrics.copy()
        )

    def tick_end_signals(
        self,
        *,
        state: AuthoritativeState,
        status: RuntimeStatus,
        final_compute_ms: float,
        phase_costs: Mapping[str, float],
        host: HostReadings,
    ) -> PressureSignals:
        """Signals recorded into the status history at the end of a tick: this tick's measured cost and phase costs."""
        return PressureSignals(
            work_debt_total=sum(state.work_debt.values()),
            tick_compute_ms=final_compute_ms,
            worker_utilization=host.worker_stats["worker_utilization"],
            queue_utilization=host.worker_stats["queue_utilization"],
            memory_estimate_mb=host.platform_signals["rss_mb"],
            replay_backlog_kb=host.replay_stats["backlog_kb"],
            active_workers=host.worker_stats["active_workers"],
            dropped_work_delta=status.dropped_work_delta,
            phase_costs_ms=dict(phase_costs),
            metrics=host.metrics.copy()
        )


class ZeroedSignalSource(LiveSignalSource):
    """``audit_mode``: every timing and resource input is zero at the start of the tick, so no run ever leaves ``NORMAL``."""

    def tick_start_signals(
        self,
        *,
        state: AuthoritativeState,
        profile: RuntimeProfile,
        status: RuntimeStatus,
        host: HostReadings,
    ) -> PressureSignals:
        """Every timing and resource input at zero; the work-debt total and the dropped-work delta are kept."""
        return PressureSignals(
            work_debt_total=sum(state.work_debt.values()),
            tick_compute_ms=0.0,
            worker_utilization=0.0,
            queue_utilization=0.0,
            memory_estimate_mb=0.0,
            replay_backlog_kb=0,
            active_workers=0,
            dropped_work_delta=status.dropped_work_delta,
            phase_costs_ms={},
            metrics=host.metrics.copy()
        )


_LIVE = LiveSignalSource()
_ZEROED = ZeroedSignalSource()


def select_signal_source(profile: RuntimeProfile, audit_mode: bool) -> LiveSignalSource:
    """Precedence: ``audit_mode`` -> zeroed signals; else the profile's ``signal_contract``. A flag cannot override the profile's contract."""
    if audit_mode:
        return _ZEROED
    if profile.signal_contract is SignalContract.CANONICAL:
        raise NotImplementedError("the CANONICAL signal contract has no source yet (arrives with step 3)")
    return _LIVE
