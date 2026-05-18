from __future__ import annotations

from typing import TYPE_CHECKING
from src_legacy.core.governance import RuntimeMode, PressureSignals
from src_legacy.engine.policy import GovernorPolicy

if TYPE_CHECKING:
    from src_legacy.config.profiles import RuntimeProfile
    from src_legacy.engine.runtime_status import RuntimeStatus


class ResourceGovernor:
    """
    Authoritative safety-control layer for the simulation engine.
    Responsibility: Evaluate pressure signals vs profile limits and
    transition through deterministic operational modes.

    Law: Must follow Milestone B Runtime Signals Contract.
    Proof: Verified by mb_test_matrix.md and test_milestone_b_closure.py.
    """

    def __init__(self) -> None:
        """Initialize the governor. Constants are now profile-driven."""
        pass

    def evaluate(
        self, 
        profile: RuntimeProfile, 
        signals: PressureSignals, 
        status: RuntimeStatus,
        current_tick: int
    ) -> GovernorPolicy:
        """
        Determine the next operational mode and return the derived policy.
        Implements Escalation (Immediate) and Recovery (Gated by Dwell + Confidence).
        """
        # Indicated mode based on input signals
        indicated_mode = self._get_indicated_mode(profile, signals)
        current_mode = status.current_mode
        
        if indicated_mode > current_mode:
            # Escalation Rule: Immediate
            status.reset_dwell(indicated_mode, current_tick)
        elif indicated_mode < current_mode:
            # Recovery Rule: Gated by Low-Watermark and Dwell Time
            if self._can_recover(profile, signals, status):
                # Law: Monotonic recovery (one level at a time)
                next_mode = RuntimeMode(current_mode - 1)
                status.reset_dwell(next_mode, current_tick)
            else:
                status.increment_dwell()
        else:
            # Stability: Continue dwelling
            status.increment_dwell()
            
        return GovernorPolicy.from_mode(status.current_mode)

    def _get_indicated_mode(
        self, 
        profile: RuntimeProfile, 
        signals: PressureSignals
    ) -> RuntimeMode:
        # 1. SURVIVAL (3): Critical overload
        if signals.work_debt_total >= profile.max_work_debt:
            return RuntimeMode.SURVIVAL
        if signals.tick_compute_ms >= profile.max_tick_budget_ms * 1.5:
            return RuntimeMode.SURVIVAL
        if signals.memory_estimate_mb >= profile.max_ram_mb:
            return RuntimeMode.SURVIVAL
            
        # 2. DEGRADED (2): High pressure
        if signals.work_debt_total >= profile.max_work_debt * 0.5:
            return RuntimeMode.DEGRADED
        if signals.tick_compute_ms >= profile.max_tick_budget_ms:
            return RuntimeMode.DEGRADED
        if signals.worker_utilization >= 0.9 or signals.queue_utilization >= 0.9:
            return RuntimeMode.DEGRADED
        if profile.max_replay_buffer_kb > 0 and signals.replay_backlog_kb >= profile.max_replay_buffer_kb * 0.9:
            return RuntimeMode.DEGRADED
            
        # 3. CONSTRAINED (1): Early pressure
        if signals.tick_compute_ms >= profile.max_tick_budget_ms * 0.7:
            return RuntimeMode.CONSTRAINED
        if signals.worker_utilization >= 0.7 or signals.queue_utilization >= 0.7:
            return RuntimeMode.CONSTRAINED
        if signals.memory_estimate_mb >= profile.max_ram_mb * profile.degradation_threshold_ram:
            return RuntimeMode.CONSTRAINED
            
        return RuntimeMode.NORMAL

    def _can_recover(
        self, 
        profile: RuntimeProfile, 
        signals: PressureSignals, 
        status: RuntimeStatus
    ) -> bool:
        """
        Check if the system is stable enough to de-escalate.
        Law: Dwell Time + Confidence Window + Low Watermark.
        """
        # 1. Dwell Time Check (Profile Driven)
        if status.mode_dwell_ticks < profile.dwell_time_ticks:
            return False
            
        # 2. Confidence Window Check
        # Check if the last N samples are all below recovery thresholds
        window_size = profile.confidence_window_ticks
        history = status.get_recent_history(window_size)
        
        # If we don't even have enough samples yet, stay safe
        if len(history) < window_size:
            return False
            
        watermark = profile.recovery_watermark
        
        # Law: All samples in the window must be below the recovery limits
        for sample in history:
            # Thresholds derived from escalation points * watermark
            recovery_limit_ms = (profile.max_tick_budget_ms * 0.7) * watermark
            recovery_limit_capacity = 0.7 * watermark
            recovery_limit_ram = (profile.max_ram_mb * profile.degradation_threshold_ram) * watermark
            recovery_limit_debt = (profile.max_work_debt * 0.5) * watermark
            
            # Note: We check avg_compute for stability
            if sample.tick_compute_ms_avg > recovery_limit_ms:
                return False
            if sample.worker_utilization > recovery_limit_capacity or sample.queue_utilization > recovery_limit_capacity:
                return False
            if sample.memory_estimate_mb > recovery_limit_ram:
                return False
            if sample.work_debt_total > recovery_limit_debt:
                return False
                
        return True
