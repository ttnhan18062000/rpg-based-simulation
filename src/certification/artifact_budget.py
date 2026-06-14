"""
ArtifactBudgetRegistry — central write-time size governance for all generated artifacts.

INFRA-193: Per-artifact-type budget enforcement.
  - Unknown types return action="allow" (safe default).
  - fail_on_budget_violation=True  → action="reject", allowed=False.
  - fail_on_budget_violation=False → action="warn",   allowed=True.
  - soft_limit_mb exceeded (below max) → action="warn", allowed=True.
  - All violation events are logged by the caller (INFRA-060 compliance).

Default registry is a module-level singleton; reset_default_registry() is provided
for test isolation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass
class ArtifactBudget:
    """Declared size/retention policy for one artifact type."""

    artifact_type: str
    max_size_mb: float
    soft_limit_mb: Optional[float] = None          # None = no soft limit
    retention: str = "keep_latest_per_scenario"
    allow_full_state: bool = True
    compression: str = "none"
    fail_on_budget_violation: bool = False          # MUST default False


@dataclass
class BudgetCheckResult:
    """Result of a single artifact-type budget check."""

    allowed: bool
    action: str          # "allow" | "warn" | "compact" | "reject"
    reason: Optional[str] = None


class ArtifactBudgetViolationError(Exception):
    """
    Raised by the caller when fail_on_budget_violation=True and check()
    returns action="reject".  The registry's check() itself never raises.
    """

    def __init__(self, artifact_type: str, size_bytes: int, message: str = ""):
        self.artifact_type = artifact_type
        self.size_bytes = size_bytes
        super().__init__(
            message or f"Artifact budget violation: {artifact_type} ({size_bytes} bytes)"
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class ArtifactBudgetRegistry:
    """
    Registry of per-artifact-type size budgets.

    Thread-safe for read (check/get); register() should be called during
    initialization only.
    """

    def __init__(self) -> None:
        self._budgets: Dict[str, ArtifactBudget] = {}

    def register(self, budget: ArtifactBudget) -> None:
        """Register (or overwrite) a budget for the given artifact type."""
        self._budgets[budget.artifact_type] = budget

    def get(self, artifact_type: str) -> Optional[ArtifactBudget]:
        """Return the registered budget for *artifact_type*, or None."""
        return self._budgets.get(artifact_type)

    def check(self, artifact_type: str, estimated_size_bytes: int) -> BudgetCheckResult:
        """
        Check *estimated_size_bytes* against the registered budget.

        Decision tree (exact per plan):
          1. No budget registered → allow.
          2. estimated_mb > max_size_mb → reject (if fail_on_budget_violation)
             or warn (otherwise, write still proceeds).
          3. estimated_mb > soft_limit_mb → warn (write proceeds).
          4. Otherwise → allow.
        """
        estimated_mb = estimated_size_bytes / (1024 * 1024)
        budget = self.get(artifact_type)

        if budget is None:
            return BudgetCheckResult(allowed=True, action="allow", reason=None)

        if estimated_mb > budget.max_size_mb:
            if budget.fail_on_budget_violation:
                return BudgetCheckResult(
                    allowed=False,
                    action="reject",
                    reason=(
                        f"{artifact_type} estimated {estimated_mb:.2f} MB "
                        f"exceeds max {budget.max_size_mb} MB"
                    ),
                )
            else:
                return BudgetCheckResult(
                    allowed=True,
                    action="warn",
                    reason=(
                        f"{artifact_type} estimated {estimated_mb:.2f} MB "
                        f"exceeds max {budget.max_size_mb} MB (warn-only)"
                    ),
                )

        if budget.soft_limit_mb is not None and estimated_mb > budget.soft_limit_mb:
            return BudgetCheckResult(
                allowed=True,
                action="warn",
                reason=(
                    f"{artifact_type} estimated {estimated_mb:.2f} MB "
                    f"exceeds soft limit {budget.soft_limit_mb} MB"
                ),
            )

        return BudgetCheckResult(allowed=True, action="allow", reason=None)


# ---------------------------------------------------------------------------
# Default budgets
# ---------------------------------------------------------------------------

_DEFAULTS = [
    ArtifactBudget(
        artifact_type="certification_result",
        max_size_mb=2.0,
        soft_limit_mb=1.5,
        retention="keep_latest_per_scenario",
        allow_full_state=False,
        compression="optional",
        fail_on_budget_violation=False,
    ),
    ArtifactBudget(
        artifact_type="replay_chunk",
        max_size_mb=10.0,
        soft_limit_mb=8.0,
        retention="keep_latest_per_scenario",
        allow_full_state=False,
        compression="optional",
        fail_on_budget_violation=False,  # MUST be False — async thread path
    ),
    ArtifactBudget(
        artifact_type="behavior_report",
        max_size_mb=5.0,
        soft_limit_mb=None,
        retention="keep_latest_per_scenario",
        allow_full_state=False,
        compression="optional",
        fail_on_budget_violation=False,
    ),
    ArtifactBudget(
        artifact_type="proof_index",
        max_size_mb=1.0,
        soft_limit_mb=None,
        retention="keep_latest_per_scenario",
        allow_full_state=False,
        compression="optional",
        fail_on_budget_violation=False,
    ),
]

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_registry: Optional[ArtifactBudgetRegistry] = None


def get_default_registry() -> ArtifactBudgetRegistry:
    """
    Return the process-wide default ArtifactBudgetRegistry.

    Lazily initialized on first call; reset_default_registry() returns it to
    the uninitialized state so the next call re-creates it with fresh defaults.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = ArtifactBudgetRegistry()
        for budget in _DEFAULTS:
            _default_registry.register(budget)
    return _default_registry


def reset_default_registry() -> None:
    """
    Reset the singleton to None so the next get_default_registry() call
    re-initializes with fresh defaults.  Use in test teardown/setup only.
    """
    global _default_registry
    _default_registry = None
