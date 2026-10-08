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
from src.engine.work_units import (
    WORK_MODEL_STATUS,
    WORK_MODEL_VERSION,
    count_demand,
    queue_utilization_proxy,
    tick_cost_ref_ms,
    worker_utilization_proxy,
)

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


@dataclass(frozen=True, slots=True)
class MeasuredCosts:
    """This tick's measured cost in milliseconds and its per-phase breakdown. Telemetry under CANONICAL; the governors' input under LIVE."""

    final_compute_ms: float
    phase_costs: Mapping[str, float]


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
        profile: RuntimeProfile,
        status: RuntimeStatus,
        measured: MeasuredCosts,
        host: HostReadings,
    ) -> PressureSignals:
        """Signals recorded into the status history at the end of a tick: this tick's measured cost and phase costs."""
        return PressureSignals(
            work_debt_total=sum(state.work_debt.values()),
            tick_compute_ms=measured.final_compute_ms,
            worker_utilization=host.worker_stats["worker_utilization"],
            queue_utilization=host.worker_stats["queue_utilization"],
            memory_estimate_mb=host.platform_signals["rss_mb"],
            replay_backlog_kb=host.replay_stats["backlog_kb"],
            active_workers=host.worker_stats["active_workers"],
            dropped_work_delta=status.dropped_work_delta,
            phase_costs_ms=dict(measured.phase_costs),
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


class CanonicalSignalSource(LiveSignalSource):
    """The CANONICAL contract: cost inputs are modelled from deterministic demand counts, never read from a clock or the host.

    ``tick_cost`` is ``WORK_MODEL_V1`` in reference-milliseconds, counted from the state about to be processed (pre-policy demand), so the mode
    cannot feed back into its own input. ``phase_cost`` is empty, so the governor's per-phase rules (locomotion, final_integrity) have nothing
    to read: neither has a pre-policy counter. Memory and replay backlog are not inputs (zero); queue and worker pressure are demand proxies.
    The measured tick cost still goes into the status history as telemetry in ``tick_compute_ms``, and nothing the governors read looks at it.
    """

    def tick_start_signals(
        self,
        *,
        state: AuthoritativeState,
        profile: RuntimeProfile,
        status: RuntimeStatus,
        host: HostReadings,
    ) -> PressureSignals:
        """Signals for the governor at the start of a tick, from the demand in ``state``."""
        return self._canonical(state, profile, status, host, MeasuredCosts(0.0, {}))

    def tick_end_signals(
        self,
        *,
        state: AuthoritativeState,
        profile: RuntimeProfile,
        status: RuntimeStatus,
        measured: MeasuredCosts,
        host: HostReadings,
    ) -> PressureSignals:
        """Signals recorded into the status history: modelled inputs for the governors plus the measured cost as telemetry."""
        return self._canonical(state, profile, status, host, measured)

    @staticmethod
    def _canonical(
        state: AuthoritativeState,
        profile: RuntimeProfile,
        status: RuntimeStatus,
        host: HostReadings,
        measured: MeasuredCosts,
    ) -> PressureSignals:
        demand = count_demand(state)
        return PressureSignals(
            work_debt_total=sum(state.work_debt.values()),
            tick_compute_ms=measured.final_compute_ms,
            worker_utilization=worker_utilization_proxy(demand.entities_active, profile.max_worker_count),
            queue_utilization=queue_utilization_proxy(demand.entities_active, profile.max_worker_count, profile.max_queue_depth),
            memory_estimate_mb=0.0,
            replay_backlog_kb=0,
            active_workers=0,
            dropped_work_delta=status.dropped_work_delta,
            phase_costs_ms=dict(measured.phase_costs),
            metrics=host.metrics.copy(),
            tick_cost=tick_cost_ref_ms(demand),
            phase_cost={},
        )


_LIVE = LiveSignalSource()
_ZEROED = ZeroedSignalSource()
_CANONICAL = CanonicalSignalSource()


def select_signal_source(profile: RuntimeProfile, audit_mode: bool) -> LiveSignalSource:
    """Precedence: ``audit_mode`` -> zeroed signals; else the profile's ``signal_contract``. A flag cannot override the profile's contract."""
    if audit_mode:
        return _ZEROED
    return _CANONICAL if profile.signal_contract is SignalContract.CANONICAL else _LIVE


def signal_contract_record(profile: RuntimeProfile, audit_mode: bool) -> Dict[str, str]:
    """What a run's manifest records about how its governor inputs were produced (readers tolerate the record's absence in older manifests)."""
    canonical = profile.signal_contract is SignalContract.CANONICAL
    return {
        "signal_contract": "CANONICAL" if canonical else "LIVE",
        "effective_source": "audit_zeroed" if audit_mode else ("canonical" if canonical else "live"),
        "work_model": WORK_MODEL_VERSION,
        "work_model_status": WORK_MODEL_STATUS,
    }
