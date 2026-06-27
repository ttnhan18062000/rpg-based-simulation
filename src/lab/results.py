"""
Typed return models for all 7 lab Workflow.run() methods.

TypedDicts are used (not dataclasses) so that existing callers using
dict-style key access (result["status"], result.get("reason", "")) remain
valid without modification.  Literal-tagged status fields allow mypy to
narrow discriminated Union results in caller code.
"""
from __future__ import annotations

from typing import Union

try:
    from typing import Literal, TypedDict
except ImportError:  # Python < 3.8
    from typing_extensions import Literal, TypedDict  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Shared: BLOCKED result (returned by workflows 2–6 on precondition failure)
# ---------------------------------------------------------------------------

class BlockedWorkflowResult(TypedDict):
    """Returned when a workflow cannot proceed due to missing preconditions."""
    status: Literal["BLOCKED"]
    reason: str


# ---------------------------------------------------------------------------
# 1. GenerateSimulationSetupWorkflow — never returns BLOCKED
# ---------------------------------------------------------------------------

class GenerateSimulationSetupResult(TypedDict):
    """Result from GenerateSimulationSetupWorkflow.run()."""
    world_spec_id: str
    scenario_spec_id: str
    experiment_spec_id: str
    validation_passed: bool
    budget_status: str


# ---------------------------------------------------------------------------
# 2. PrepareSimulationExecutionWorkflow
# ---------------------------------------------------------------------------

class PrepareReadyResult(TypedDict):
    """Success branch of PrepareSimulationExecutionWorkflow.run()."""
    status: Literal["READY"]
    command_script_path: str
    output_path: str


PrepareSimulationExecutionResult = Union[BlockedWorkflowResult, PrepareReadyResult]


# ---------------------------------------------------------------------------
# 3. RegisterSimulationResultWorkflow
# ---------------------------------------------------------------------------

class RegisterReadyResult(TypedDict):
    """Success branch of RegisterSimulationResultWorkflow.run()."""
    status: Literal["READY"]
    classification: str
    lab_run_id: str
    report_path: str


RegisterSimulationResultResult = Union[BlockedWorkflowResult, RegisterReadyResult]


# ---------------------------------------------------------------------------
# 4. CompactSimulationDataWorkflow
# ---------------------------------------------------------------------------

class CompactReadyResult(TypedDict):
    """Success branch of CompactSimulationDataWorkflow.run()."""
    status: Literal["READY"]
    report_path: str


CompactSimulationDataResult = Union[BlockedWorkflowResult, CompactReadyResult]


# ---------------------------------------------------------------------------
# 5. InvestigateSimulationResultWorkflow
# ---------------------------------------------------------------------------

class InvestigateReadyResult(TypedDict):
    """Success branch of InvestigateSimulationResultWorkflow.run()."""
    status: Literal["READY"]
    report_path: str


InvestigateSimulationResultResult = Union[BlockedWorkflowResult, InvestigateReadyResult]


# ---------------------------------------------------------------------------
# 6. ProposeSimulationEnhancementsWorkflow
# ---------------------------------------------------------------------------

class ProposeReadyResult(TypedDict):
    """Success branch of ProposeSimulationEnhancementsWorkflow.run()."""
    status: Literal["READY"]
    report_path: str


ProposeSimulationEnhancementsResult = Union[BlockedWorkflowResult, ProposeReadyResult]


# ---------------------------------------------------------------------------
# 7. UpdateSimulationKnowledgeWorkflow — never returns BLOCKED (raises instead)
# ---------------------------------------------------------------------------

class UpdateSimulationKnowledgeResult(TypedDict):
    """Result from UpdateSimulationKnowledgeWorkflow.run().

    status is 'SYNCED' when at least one item was stored,
    'NO_INSIGHTS' when nothing was available to sync.
    """
    status: Literal["SYNCED", "NO_INSIGHTS"]
    report_path: str
    synced_count: int
