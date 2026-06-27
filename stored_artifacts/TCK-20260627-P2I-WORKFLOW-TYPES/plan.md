# Plan — TCK-20260627-P2I-WORKFLOW-TYPES

## Goal

Replace `dict[str, Any]` / `Dict[str, Any]` return annotations on all 7 `Workflow.run()` methods in `src/lab/workflows.py` with specific TypedDicts defined in a new `src/lab/results.py`.

## Files Changed

1. `src/lab/results.py` — new module, defines all TypedDicts
2. `src/lab/workflows.py` — update 7 `run()` return annotations + add import

## Step 1 — Create `src/lab/results.py`

Define:

```python
# Shared
class BlockedWorkflowResult(TypedDict):
    status: Literal["BLOCKED"]
    reason: str

# 1. GenerateSimulationSetupWorkflow
class GenerateSimulationSetupResult(TypedDict):
    world_spec_id: str
    scenario_spec_id: str
    experiment_spec_id: str
    validation_passed: bool
    budget_status: str

# 2. PrepareSimulationExecutionWorkflow
class PrepareReadyResult(TypedDict):
    status: Literal["READY"]
    command_script_path: str
    output_path: str
PrepareSimulationExecutionResult = Union[BlockedWorkflowResult, PrepareReadyResult]

# 3. RegisterSimulationResultWorkflow
class RegisterReadyResult(TypedDict):
    status: Literal["READY"]
    classification: str
    lab_run_id: str
    report_path: str
RegisterSimulationResultResult = Union[BlockedWorkflowResult, RegisterReadyResult]

# 4. CompactSimulationDataWorkflow
class CompactReadyResult(TypedDict):
    status: Literal["READY"]
    report_path: str
CompactSimulationDataResult = Union[BlockedWorkflowResult, CompactReadyResult]

# 5. InvestigateSimulationResultWorkflow
class InvestigateReadyResult(TypedDict):
    status: Literal["READY"]
    report_path: str
InvestigateSimulationResultResult = Union[BlockedWorkflowResult, InvestigateReadyResult]

# 6. ProposeSimulationEnhancementsWorkflow
class ProposeReadyResult(TypedDict):
    status: Literal["READY"]
    report_path: str
ProposeSimulationEnhancementsResult = Union[BlockedWorkflowResult, ProposeReadyResult]

# 7. UpdateSimulationKnowledgeWorkflow
class UpdateSimulationKnowledgeResult(TypedDict):
    status: Literal["SYNCED", "NO_INSIGHTS"]
    report_path: str
    synced_count: int
```

## Step 2 — Update `src/lab/workflows.py`

Add import at top:
```python
from src.lab.results import (
    GenerateSimulationSetupResult,
    PrepareSimulationExecutionResult,
    RegisterSimulationResultResult,
    CompactSimulationDataResult,
    InvestigateSimulationResultResult,
    ProposeSimulationEnhancementsResult,
    UpdateSimulationKnowledgeResult,
)
```

Replace 7 `run()` return type annotations:
- L88: `-> Dict[str, Any]` → `-> GenerateSimulationSetupResult`
- L597: `-> Dict[str, Any]` → `-> PrepareSimulationExecutionResult`
- L871: `-> dict[str, Any]` → `-> RegisterSimulationResultResult`
- L1120: `-> dict[str, Any]` → `-> CompactSimulationDataResult`
- L1575: `-> dict[str, Any]` → `-> InvestigateSimulationResultResult`
- L2065: `-> dict[str, Any]` → `-> ProposeSimulationEnhancementsResult`
- L2326: `-> dict[str, Any]` → `-> UpdateSimulationKnowledgeResult`

## Out of Scope

- Helper private methods (`_validate_world`, `_check_duplication`, etc.) — not `run()` methods.
- Caller behavior changes — TypedDicts are backward-compatible with dict-style access.
- `patches.py merge()` — separate ticket TCK-20260627-P2J-PATCHES-TYPE.

## Status

APPROVED — no unresolved questions.
