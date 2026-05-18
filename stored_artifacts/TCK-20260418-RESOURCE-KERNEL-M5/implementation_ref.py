from __future__ import annotations

from typing import TYPE_CHECKING
from src.core.governance import RuntimeMode, PressureSignals
from src.engine.policy import GovernorPolicy

if TYPE_CHECKING:
    from src.config.profiles import RuntimeProfile
    from src.engine.runtime_status import RuntimeStatus


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
        status: RuntimeStatus
    ) -> GovernorPolicy:
        """
        Determine the next operational mode and return the derived policy.
        Implements Escalation (Immediate) and Recovery (Gated).
        """
        # 1. Capture signals
        status.record_signals(signals)
        
        # 2. Determine raw indicated mode based on thresholds
        indicated_mode = self._get_indicated_mode(profile, signals)
        
        # 3. Transition Logic
        current_mode = status.current_mode
        
        if indicated_mode > current_mode:
            # Escalation Rule: Immediate
            status.reset_dwell(indicated_mode)
        elif indicated_mode < current_mode:
            # Recovery Rule: Gated by Low-Watermark and Dwell Time
            if self._can_recover(profile, signals, status):
                # Transition down only one level at a time for stability
                status.reset_dwell(RuntimeMode(current_mode - 1))
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
        """
        # SURVIVAL (3): Critical overload
        if signals.work_debt_total >= profile.max_work_debt:
            return RuntimeMode.SURVIVAL
        if signals.tick_compute_ms >= profile.max_tick_budget_ms * 1.5:
            return RuntimeMode.SURVIVAL
        
        # DEGRADED (2): High pressure
        if signals.work_debt_total >= profile.max_work_debt * 0.5:
            return RuntimeMode.DEGRADED
        if signals.tick_compute_ms >= profile.max_tick_budget_ms:
            return RuntimeMode.DEGRADED
        if signals.queue_utilization >= 0.9:
            return RuntimeMode.DEGRADED
            
        # CONSTRAINED (1): Early pressure
        if signals.tick_compute_ms >= profile.max_tick_budget_ms * 0.7:
            return RuntimeMode.CONSTRAINED
        if signals.queue_utilization >= 0.7:
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
        # Signals must be significantly below the thresholds of the *current* mode's triggers
        # to prevent rapid oscillation back and forth.
        
        recovery_limit_debt = profile.max_work_debt * self._recovery_watermark
        recovery_limit_ms = profile.max_tick_budget_ms * self._recovery_watermark
        recovery_limit_queue = 0.7 * self._recovery_watermark # 0.7 is constrained threshold
        
        if signals.work_debt_total > recovery_limit_debt:
            return False
        if signals.tick_compute_ms > recovery_limit_ms:
            return False
        if signals.queue_utilization > recovery_limit_queue:
            return False
            
        return True
