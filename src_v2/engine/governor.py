from __future__ import annotations

from typing import TYPE_CHECKING
from src_v2.core.governance import RuntimeMode, PressureSignals
from src_v2.engine.policy import GovernorPolicy

if TYPE_CHECKING:
    from src_v2.config.profiles import RuntimeProfile
    from src_v2.engine.runtime_status import RuntimeStatus


class ResourceGovernor:
    """
    Authoritative safety-control layer for the simulation engine.
    Responsibility: Evaluate pressure signals vs profile limits and
    transition through deterministic operational modes.
    """

    def __init__(
        self, 
        dwell_time: int = 10, 
        recovery_watermark: float = 0.8
    ) -> None:
        self._dwell_time = dwell_time
        self._recovery_watermark = recovery_watermark

    def evaluate(
        self, 
        profile: RuntimeProfile, 
        signals: PressureSignals, 
        status: RuntimeStatus,
        current_tick: int
    ) -> GovernorPolicy:
        """
        Determine the next operational mode and return the derived policy.
        Implements Escalation (Immediate) and Recovery (Gated).
        """
        # Indicated mode based on input signals
        indicated_mode = self._get_indicated_mode(profile, signals)
        
        # 3. Transition Logic
        current_mode = status.current_mode
        
        if indicated_mode > current_mode:
            # Escalation Rule: Immediate
            status.reset_dwell(indicated_mode, current_tick)
        elif indicated_mode < current_mode:
            # Recovery Rule: Gated by Low-Watermark and Dwell Time
            if self._can_recover(profile, signals, status):
                # Transition down only one level at a time for stability
                parent_mode = RuntimeMode(current_mode - 1)
                status.reset_dwell(parent_mode, current_tick)
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
        """
        Map pressure signals to the indicated severity level.
        M7 Law: Evaluate relative to profile limits.
        """
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
        Requirements:
        1. All signals below recovery threshold (Low-Watermark).
        2. Minimum dwell time satisfied.
        """
        # 1. Dwell Time Check
        if status.mode_dwell_ticks < self._dwell_time:
            return False
            
        # 2. Low-Watermark Check
        # Signals must be below current mode's thresholds * watermark
        # Example: to recover from CONSTRAINED (0.7ms), signals must be < 0.56ms (0.7 * 0.8)
        
        watermark = self._recovery_watermark
        
        # Thresholds derived from NORMAL trigger points (CONSTRAINED triggers)
        # Note: We use the *lowest* escalation threshold as the recovery baseline.
        recovery_limit_ms = (profile.max_tick_budget_ms * 0.7) * watermark
        recovery_limit_capacity = 0.7 * watermark
        recovery_limit_ram = (profile.max_ram_mb * profile.degradation_threshold_ram) * watermark
        
        # Work debt recovery is usually faster, 80% of current mode's trigger
        recovery_limit_debt = (profile.max_work_debt * 0.5) * watermark
        
        if signals.tick_compute_ms > recovery_limit_ms:
            return False
        if signals.worker_utilization > recovery_limit_capacity or signals.queue_utilization > recovery_limit_capacity:
            return False
        if signals.memory_estimate_mb > recovery_limit_ram:
            return False
        if signals.work_debt_total > recovery_limit_debt:
            return False
            
        return True
