# Investigation — TCK-20260627-P2I-WORKFLOW-TYPES

## Finding Summary

**Source:** D13 F4 — `src/lab/workflows.py`, all 7 `Workflow.run()` methods return `dict[str, Any]`.

## The 7 Workflow Classes and Their run() Return Shapes

| # | Class | Line | Return shape |
|---|---|---|---|
| 1 | `GenerateSimulationSetupWorkflow` | 88 | `{world_spec_id, scenario_spec_id, experiment_spec_id, validation_passed, budget_status}` — no BLOCKED path |
| 2 | `PrepareSimulationExecutionWorkflow` | 597 | BLOCKED → `{status:"BLOCKED", reason}` / READY → `{status:"READY", command_script_path, output_path}` |
| 3 | `RegisterSimulationResultWorkflow` | 871 | BLOCKED → `{status:"BLOCKED", reason}` / READY → `{status:"READY", classification, lab_run_id, report_path}` |
| 4 | `CompactSimulationDataWorkflow` | 1120 | BLOCKED → `{status:"BLOCKED", reason}` / READY → `{status:"READY", report_path}` |
| 5 | `InvestigateSimulationResultWorkflow` | 1575 | BLOCKED → `{status:"BLOCKED", reason}` / READY → `{status:"READY", report_path}` |
| 6 | `ProposeSimulationEnhancementsWorkflow` | 2065 | BLOCKED → `{status:"BLOCKED", reason}` / READY → `{status:"READY", report_path}` |
| 7 | `UpdateSimulationKnowledgeWorkflow` | 2326 | `{status:"SYNCED"\|"NO_INSIGHTS", report_path, synced_count}` — raises ValueError, never returns BLOCKED |

## Callers

- `tests/unit/lab_agent/test_agent_guardrails.py` — accesses `result["status"]` (dict-key style, TypedDict-compatible)
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py` — accesses `result["status"]`, `result.get("reason", "")` (TypedDict-compatible, no change needed)
- `src/lab/mutation_orchestrator.py` line 253 — accesses an *internal* variant dict, NOT a workflow result — no change needed

## Design Decision

**TypedDicts in `src/lab/results.py`** — chosen because:
1. Callers already use `result["key"]` dict-style access; TypedDicts are backward-compatible (they are dict subclasses at runtime).
2. No caller needs to be modified.
3. Discriminated Union (Literal status field) enables mypy narrowing in `if result["status"] == "READY":` branches.

Pattern used for workflows 2–6:
```
Union[BlockedWorkflowResult, <Workflow>ReadyResult]
```

Pattern for workflow 1 (never blocked): flat TypedDict.
Pattern for workflow 7 (never blocked, unique status values): flat TypedDict with `Literal["SYNCED", "NO_INSIGHTS"]` status.

## No Circular Import Risk

`results.py` imports only from `typing` — no imports from `src.lab.*` — safe as a dependency.

## Files to Change

1. `src/lab/results.py` — **new** — defines all TypedDicts
2. `src/lab/workflows.py` — annotate 7 `run()` signatures; add import from `results`
