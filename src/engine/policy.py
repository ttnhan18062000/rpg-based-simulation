from __future__ import annotations

from dataclasses import dataclass, field
from src.core.governance import RuntimeMode
from src.engine.cadence import SystemCadence
from src.engine.phase_governor import PhaseBudgets, PhaseBudgetGovernor, ScanPolicy


@dataclass(frozen=True, slots=True)
class GovernorPolicy:
    """
    Explicit decisions emitted by the Resource Governor for system consumption.
    M5 Law: Subsystems respond to these flags, not to raw pressure enums.
    """
    allow_opportunistic: bool = True
    allow_non_authoritative_periodic: bool = True
    lod_enabled: bool = True
    diagnostic_verbosity: str = "FULL"  # "FULL", "MINIMAL", "ERROR", "MUTED"
    metrics_detail: str = "HIGH"        # "HIGH", "LOW", "MUTED"
    
    # M8 Adaptive Concurrency
    concurrency_limit: float = 1.0     # 0.0 to 1.0 multiplier of active pool
    
    # M6 Replay Policy
    replay_allowed: bool = True
    replay_richness: str = "FULL"       # "FULL", "MINIMAL", "OFF"
    allow_subsystem_traces: bool = True
    mode: RuntimeMode = RuntimeMode.NORMAL
    system_cadence: SystemCadence = field(default_factory=lambda: SystemCadence(strategic_intelligence=1))
    
    # Milestone 17 Adaptive Phase Budgets
    phase_budgets: PhaseBudgets = field(default_factory=PhaseBudgets)

    @property
    def scan_policy(self) -> ScanPolicy:
        return self.phase_budgets.scan_policy

    @property
    def candidate_budget(self) -> int:
        return self.phase_budgets.candidate_budget

    @property
    def strategic_budget(self) -> int:
        return self.phase_budgets.strategic_budget

    @property
    def movement_budget(self) -> int:
        return self.phase_budgets.movement_budget

    @property
    def background_sweep_interval(self) -> int:
        return self.phase_budgets.background_sweep_interval

    @property
    def compaction_level(self) -> str:
        return self.phase_budgets.compaction_level

    @classmethod
    def from_mode(cls, mode: RuntimeMode) -> GovernorPolicy:
        """
        Policy Waterfall according to Milestone 5/6 Degradation Matrix.

        `concurrency_limit` goes DOWN as `mode` escalates (1.0 / 1.0 / 0.5 / 0.25
        for NORMAL / CONSTRAINED / DEGRADED / SURVIVAL below) — this is not a typo
        and should not be "fixed" to scale the other way. Naively, more pressure
        might suggest more parallel workers to clear a backlog faster. But by the
        time concurrency is throttled, every other lever has already shrunk the
        scheduled batch for this tick: PhaseBudgetGovernor.evaluate() (phase_governor.py)
        cuts candidate/strategic/movement budgets and tightens scan_policy as `mode`
        escalates; SystemCadence gates re-evaluation frequency per subsystem
        (cadence.py:should_run); and DeterministicScheduler.select_work()
        (scheduler.py) filters candidates through LOD (LODService.should_execute,
        lod.py) and cadence gating before dispatch. A smaller worker pool applied to
        an already-smaller batch reduces thread/IPC contention instead of adding
        scheduling noise to an already-stressed system. See
        docs/engine/contracts/bounded_concurrency_contract.md §5.1 for the full
        write-up.
        """
        budgets = PhaseBudgetGovernor.evaluate(None, None, mode, 0)
        if mode == RuntimeMode.NORMAL:
            return cls(
                allow_opportunistic=True,
                allow_non_authoritative_periodic=True,
                diagnostic_verbosity="FULL",
                metrics_detail="HIGH",
                concurrency_limit=1.0,
                replay_allowed=True,
                replay_richness="FULL",
                allow_subsystem_traces=True,
                mode=RuntimeMode.NORMAL,
                system_cadence=SystemCadence(
                    strategic_intelligence=10,
                    world_dynamics=50,
                    town_resolution=20,
                    social_propagation=30,
                    concern_evaluation=10
                ),
                phase_budgets=budgets,
            )
        
        if mode == RuntimeMode.CONSTRAINED:
            return cls(
                allow_opportunistic=True,
                allow_non_authoritative_periodic=True,
                diagnostic_verbosity="MINIMAL",
                metrics_detail="HIGH",
                concurrency_limit=1.0,
                replay_allowed=True,
                replay_richness="FULL",
                allow_subsystem_traces=False, # Drop internal traces first
                mode=RuntimeMode.CONSTRAINED,
                system_cadence=SystemCadence(
                    strategic_intelligence=20,
                    world_dynamics=100,
                    town_resolution=40,
                    social_propagation=60,
                    concern_evaluation=20
                ),
                phase_budgets=budgets,
            )
            
        if mode == RuntimeMode.DEGRADED:
            return cls(
                allow_opportunistic=False,
                allow_non_authoritative_periodic=True,
                diagnostic_verbosity="ERROR",
                metrics_detail="LOW",
                concurrency_limit=0.5,
                replay_allowed=True,
                replay_richness="MINIMAL",
                allow_subsystem_traces=False,
                mode=RuntimeMode.DEGRADED,
                system_cadence=SystemCadence(
                    strategic_intelligence=50,
                    world_dynamics=250,
                    town_resolution=100,
                    social_propagation=150,
                    concern_evaluation=50
                ),
                phase_budgets=budgets,
            )
            
        if mode == RuntimeMode.SURVIVAL:
            return cls(
                allow_opportunistic=False,
                allow_non_authoritative_periodic=False,
                diagnostic_verbosity="MUTED",
                metrics_detail="MUTED",
                concurrency_limit=0.25,
                replay_allowed=False,
                replay_richness="OFF",
                allow_subsystem_traces=False,
                mode=RuntimeMode.SURVIVAL,
                system_cadence=SystemCadence(
                    strategic_intelligence=100,
                    world_dynamics=500,
                    town_resolution=200,
                    social_propagation=300,
                    concern_evaluation=100
                ),
                phase_budgets=budgets,
            )
            
        return cls(phase_budgets=budgets)
