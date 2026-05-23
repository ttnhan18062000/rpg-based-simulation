import logging
from typing import Optional
from src.lab.schema import ExperimentSpec
from src.worldbuilding.schema import WorldSpec

logger = logging.getLogger(__name__)

class BudgetBlockedError(Exception):
    """Exception raised when an experiment is blocked by budget guardrails."""
    pass

class BudgetWarningError(Exception):
    """Exception raised when an experiment triggers budget warnings and requires confirmation."""
    pass

class BudgetEstimation:
    """Estimates of resource consumption before running a laboratory experiment."""
    def __init__(
        self,
        run_count: int,
        total_ticks: int,
        expected_entity_count: int,
        expected_event_volume: int,
        expected_artifact_mb: float,
        expected_runtime_minutes: float
    ):
        self.run_count = run_count
        self.total_ticks = total_ticks
        self.expected_entity_count = expected_entity_count
        self.expected_event_volume = expected_event_volume
        self.expected_artifact_mb = expected_artifact_mb
        self.expected_runtime_minutes = expected_runtime_minutes

class BudgetCheckResult:
    """Result of validating budget estimates against limits."""
    def __init__(self, status: str, warnings: list[str], blocked_reasons: list[str]):
        self.status = status  # "OK", "WARNING", "BLOCKED"
        self.warnings = warnings
        self.blocked_reasons = blocked_reasons

    @property
    def is_ok(self) -> bool:
        return self.status == "OK"

    @property
    def is_warning(self) -> bool:
        return self.status == "WARNING"

    @property
    def is_blocked(self) -> bool:
        return self.status == "BLOCKED"

class LabBudgetGuardrails:
    """
    Estimates and validates resource, runtime, and storage requirements
    for laboratory matrix sweeps before execution.
    """
    def __init__(self, profile: str = "local_dev"):
        self.profile = profile

    def estimate(self, experiment_spec: ExperimentSpec, world_spec: WorldSpec) -> BudgetEstimation:
        """Calculates budget estimations based on specs."""
        run_count = len(experiment_spec.run.seeds) * experiment_spec.run.repeat_count
        total_ticks = run_count * experiment_spec.run.ticks
        
        expected_entity_count = sum(e.count for e in world_spec.entities)
        resource_count = len(world_spec.resources)
        
        obs_mode = experiment_spec.observability.mode
        if obs_mode in ["MINIMAL", "LIGHTWEIGHT"]:
            event_multiplier = 0.05
        elif obs_mode == "STANDARD":
            event_multiplier = 0.2
        else:  # LONG_RUN
            event_multiplier = 0.5
            
        expected_event_volume = int(total_ticks * expected_entity_count * event_multiplier)
        
        # Base size formula: (entities * ticks * 0.0001) + (resources * ticks * 0.00005)
        base_size = (expected_entity_count * total_ticks * 0.0001) + (resource_count * total_ticks * 0.00005)
        if obs_mode == "LONG_RUN":
            base_size *= 2.0
        expected_artifact_mb = round(max(0.001, base_size), 3)
        
        expected_runtime_minutes = round(total_ticks * 0.0005 + run_count * 0.05, 2)
        
        return BudgetEstimation(
            run_count=run_count,
            total_ticks=total_ticks,
            expected_entity_count=expected_entity_count,
            expected_event_volume=expected_event_volume,
            expected_artifact_mb=expected_artifact_mb,
            expected_runtime_minutes=expected_runtime_minutes
        )

    def check(self, estimate: BudgetEstimation, experiment_spec: ExperimentSpec) -> BudgetCheckResult:
        """Validates estimations against profile-based and custom constraints."""
        warnings = []
        blocked_reasons = []
        
        budgets = experiment_spec.budgets
        
        # Profile specific limits
        if self.profile == "CI":
            limit_max_runs = 20
            limit_max_ticks = 5000
            limit_max_artifact_mb = 100.0
        else:  # local_dev
            limit_max_runs = 100
            limit_max_ticks = 100000
            limit_max_artifact_mb = 2000.0

        # 1. Runs check
        if estimate.run_count > limit_max_runs:
            blocked_reasons.append(
                f"Run count ({estimate.run_count}) exceeds limit ({limit_max_runs}) under '{self.profile}' profile."
            )
        elif self.profile != "CI" and estimate.run_count > 50:
            warnings.append(f"Run count ({estimate.run_count}) is high.")
            
        if hasattr(budgets, "max_runs") and budgets.max_runs is not None:
            if estimate.run_count > budgets.max_runs:
                warnings.append(f"Run count ({estimate.run_count}) exceeds experiment budget of {budgets.max_runs}.")

        # 2. Total Ticks check
        if estimate.total_ticks > limit_max_ticks:
            blocked_reasons.append(
                f"Total ticks ({estimate.total_ticks}) exceeds limit ({limit_max_ticks}) under '{self.profile}' profile."
            )
        elif self.profile != "CI" and estimate.total_ticks > 50000:
            warnings.append(f"Total ticks ({estimate.total_ticks}) is high.")
            
        if hasattr(budgets, "max_total_ticks") and budgets.max_total_ticks is not None:
            if estimate.total_ticks > budgets.max_total_ticks:
                warnings.append(f"Total ticks ({estimate.total_ticks}) exceeds experiment budget of {budgets.max_total_ticks}.")

        # 3. Artifact Size check
        if estimate.expected_artifact_mb > limit_max_artifact_mb:
            blocked_reasons.append(
                f"Expected artifact size ({estimate.expected_artifact_mb:.2f} MB) exceeds limit ({limit_max_artifact_mb} MB) under '{self.profile}' profile."
            )
        elif self.profile != "CI" and estimate.expected_artifact_mb > (limit_max_artifact_mb / 2):
            warnings.append(f"Expected artifact size ({estimate.expected_artifact_mb:.2f} MB) is high.")
            
        if budgets.max_total_artifact_mb is not None:
            if estimate.expected_artifact_mb > budgets.max_total_artifact_mb:
                warnings.append(
                    f"Expected artifact size ({estimate.expected_artifact_mb:.2f} MB) exceeds experiment budget of {budgets.max_total_artifact_mb} MB."
                )

        # 4. Runtime check
        if budgets.max_runtime_minutes is not None:
            if estimate.expected_runtime_minutes > budgets.max_runtime_minutes:
                warnings.append(
                    f"Expected runtime ({estimate.expected_runtime_minutes:.2f} minutes) exceeds experiment budget of {budgets.max_runtime_minutes} minutes."
                )

        if blocked_reasons:
            status = "BLOCKED"
        elif warnings:
            status = "WARNING"
        else:
            status = "OK"
            
        return BudgetCheckResult(status=status, warnings=warnings, blocked_reasons=blocked_reasons)
