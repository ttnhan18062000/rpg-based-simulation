# Compliance IDs: PERF-017, INFRA-204
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from src.config.profiles import RuntimeProfile
    from src.config.optimization_profiles import OptimizationProfile
    from src.core.governance import PressureSignals
    from src.engine.runtime_status import RuntimeStatus

from src.core.governance import RuntimeMode


class ScanPolicy(Enum):
    FULL = auto()
    THROTTLED = auto()
    EXACT_DIRTY = auto()


@dataclass(frozen=True, slots=True)
class PhaseBudgets:
    """
    Explicit per-phase budgets and scan policies emitted by the Adaptive Phase Budget Governor.
    Milestone 17 Law: Controls granular sub-phase budgets under system pressure.
    """
    scan_policy: ScanPolicy = ScanPolicy.FULL
    candidate_budget: int = 1000
    strategic_budget: int = 50
    movement_budget: int = 1000
    background_sweep_interval: int = 1
    compaction_level: str = "NORMAL"  # NORMAL, AGGRESSIVE, NONE


class PhaseBudgetGovernor:
    """
    Adaptive Phase Budget Governor (Milestone 17).
    Monitors recent per-phase compute costs (p95 latency, tick cost, work debt)
    and dynamically throttles candidate budgets, scan policies, and background sweep intervals.
    """

    @staticmethod
    def evaluate(
        profile: RuntimeProfile | None,
        signals: PressureSignals | None,
        current_mode: RuntimeMode,
        current_tick: int,
        opt_profile: OptimizationProfile | None = None,
    ) -> PhaseBudgets:
        """
        Determine dynamic phase budgets based on operational mode and real-time phase pressure signals.
        """
        # Baseline defaults according to current mode
        if current_mode == RuntimeMode.NORMAL:
            base_policy = ScanPolicy.FULL
            cand_b = 1000
            strat_b = 50
            move_b = 1000
            sweep_int = 1
            comp_lvl = "NORMAL"
        elif current_mode == RuntimeMode.CONSTRAINED:
            base_policy = ScanPolicy.THROTTLED
            cand_b = 500
            strat_b = 25
            move_b = 500
            sweep_int = 3
            comp_lvl = "NORMAL"
        elif current_mode == RuntimeMode.DEGRADED:
            base_policy = ScanPolicy.EXACT_DIRTY
            cand_b = 200
            strat_b = 10
            move_b = 200
            sweep_int = 5
            comp_lvl = "AGGRESSIVE"
        elif current_mode == RuntimeMode.SURVIVAL:
            base_policy = ScanPolicy.EXACT_DIRTY
            cand_b = 50
            strat_b = 5
            move_b = 50
            sweep_int = 10
            comp_lvl = "AGGRESSIVE"
        else:
            base_policy = ScanPolicy.FULL
            cand_b = 1000
            strat_b = 50
            move_b = 1000
            sweep_int = 1
            comp_lvl = "NORMAL"

        if opt_profile:
            cand_b = opt_profile.movement_budget
            move_b = opt_profile.movement_budget
            strat_b = opt_profile.strategic_budget
            sweep_int = opt_profile.background_sweep_interval
            comp_lvl = opt_profile.compaction_level.value if hasattr(opt_profile.compaction_level, "value") else str(opt_profile.compaction_level)

        if not signals:
            return PhaseBudgets(
                scan_policy=base_policy,
                candidate_budget=cand_b,
                strategic_budget=strat_b,
                movement_budget=move_b,
                background_sweep_interval=sweep_int,
                compaction_level=comp_lvl,
            )

        # Real-time Phase Pressure Override
        phase_costs = signals.phase_costs_ms or {}

        # 1. Locomotion phase pressure (Action & Movement Routing)
        loco_ms = phase_costs.get("locomotion", 0.0)
        max_tick_ms = profile.max_tick_budget_ms if profile else 0.0
        if loco_ms > 15.0 or (max_tick_ms > 0 and loco_ms > max_tick_ms * 0.5):
            # Severe locomotion pressure
            if not opt_profile or opt_profile.phase_skip_policy != "NEVER_SKIP":
                base_policy = ScanPolicy.EXACT_DIRTY
                move_b = min(move_b, 100)
        elif loco_ms > 10.0 or (max_tick_ms > 0 and loco_ms > max_tick_ms * 0.3):
            # Moderate locomotion pressure
            if not opt_profile or opt_profile.phase_skip_policy != "NEVER_SKIP":
                if base_policy == ScanPolicy.FULL:
                    base_policy = ScanPolicy.THROTTLED
                move_b = min(move_b, 400)

        # 2. Final Integrity phase pressure (Strategic Intelligence & Lifecycle)
        integ_ms = phase_costs.get("final_integrity", 0.0)
        if integ_ms > 15.0 or (max_tick_ms > 0 and integ_ms > max_tick_ms * 0.5):
            if not opt_profile or opt_profile.phase_skip_policy != "NEVER_SKIP":
                strat_b = min(strat_b, 8)
                sweep_int = max(sweep_int, 8)
        elif integ_ms > 10.0 or (max_tick_ms > 0 and integ_ms > max_tick_ms * 0.3):
            if not opt_profile or opt_profile.phase_skip_policy != "NEVER_SKIP":
                strat_b = min(strat_b, 20)
                sweep_int = max(sweep_int, 4)

        # 3. Overall Tick Budget or Work Debt Pressure
        max_debt = profile.max_work_debt if profile else 0
        if (max_tick_ms > 0 and signals.tick_compute_ms > max_tick_ms * 0.8) or (max_debt > 0 and signals.work_debt_total > max_debt * 0.7):
            if not opt_profile or opt_profile.compaction_level != "NONE":
                comp_lvl = "AGGRESSIVE"

        return PhaseBudgets(
            scan_policy=base_policy,
            candidate_budget=cand_b,
            strategic_budget=strat_b,
            movement_budget=move_b,
            background_sweep_interval=sweep_int,
            compaction_level=comp_lvl,
        )
