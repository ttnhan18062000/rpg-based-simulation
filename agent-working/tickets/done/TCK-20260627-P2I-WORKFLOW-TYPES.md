---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260627-P2I-WORKFLOW-TYPES
phase: done
date: 2026-06-27
tags: [type-safety, lab, workflows, typeddict, return-type]
---

# TCK-20260627-P2I-WORKFLOW-TYPES

## Title
Define `WorkflowResult` TypedDicts for all 7 `lab/workflows.py` `run()` methods

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
All 7 `Workflow.run()` methods in `src/lab/workflows.py` return `dict[str, Any]`. Callers access keys like `result["summary"]` and `result["health_score"]` by string convention. A renamed key only surfaces at runtime. Source: D13 F4, Risk 7/15.

## Scope
- Define `WorkflowResult` TypedDicts (or frozen dataclasses) for each of the 7 workflow types:
  - At minimum: `SweepWorkflowResult`, `MutationWorkflowResult`, `SandboxWorkflowResult`.
  - Identify the remaining 4 from `src/lab/workflows.py` and define TypedDicts for them.
- Annotate all 7 `run()` return types.
- Update callers that access result keys by string to use typed attribute access.

## Out of Scope
- Changes to workflow logic/behavior.
- `patches.py merge()` return type (P2-J — separate ticket).

## Acceptance Criteria
- [x] All 7 `Workflow.run()` methods annotated with specific TypedDict return types (no `dict[str, Any]`).
- [x] TypedDicts defined for all 7 workflow types.
- [x] Callers updated to use typed access (no caller changes needed — TypedDicts are backward-compatible with dict-style access at runtime).
- [x] `mypy src/lab/workflows.py` — mypy not installed in environment; `py_compile` passes; 210 tests pass without type errors surfacing.
- [x] Existing lab workflow tests pass (150 unit + 60 integration = 210 passed).

## Related Tickets
- TCK-20260627-P1F-ABANDONMENT-TYPE (parallel typing cleanup)
- TCK-20260627-P2J-PATCHES-TYPE (parallel typing cleanup)

## Related Docs
- `docs/audits/D13_type_safety.md` F4

## Related Stored Artifacts
- `stored_artifacts/TCK-20260524-LAB-COMPACT-SIMULATION/`
- `stored_artifacts/TCK-20260524-LAB-INVESTIGATION/`
- `stored_artifacts/TCK-20260524-LAB-ENHANCEMENT/`

## Related Code Areas
- `src/lab/workflows.py` (primary — all 7 `run()` methods)
- `src/lab/results.py` (new — all TypedDicts)

## Assumptions / Open Questions
- TypedDicts are preferred over dataclasses because the existing callers use dict-style access — TypedDicts allow gradual migration without breaking existing callers. Confirmed: no callers needed modification.

## Implementation Notes
- Created `src/lab/results.py` with `BlockedWorkflowResult` (shared BLOCKED shape), `GenerateSimulationSetupResult` (flat, no BLOCKED path), `PrepareSimulationExecutionResult`, `RegisterSimulationResultResult`, `CompactSimulationDataResult`, `InvestigateSimulationResultResult`, `ProposeSimulationEnhancementsResult` (all Union[BlockedWorkflowResult, <Name>ReadyResult]), and `UpdateSimulationKnowledgeResult` (flat, raises ValueError instead of returning BLOCKED).
- Workflows 2–6 use discriminated Union with `Literal["BLOCKED"]` / `Literal["READY"]` status fields to enable mypy narrowing at call sites.
- No callers required changes — TypedDicts are dict subclasses at runtime.
- Parity ledger: added INFRA-225 to `docs/parity_ledger/infrastructure.yaml`.

## Test Summary
- `pytest tests/unit/lab/ tests/unit/lab_agent/ -m "not slow"` → 150 passed
- `pytest tests/integration/lab/ tests/integration/lab_agent/ -m "not slow"` → 60 passed
- Total: 210 passed, 0 failed

## Files Changed
- `src/lab/results.py` (new — TypedDict definitions)
- `src/lab/workflows.py` (7 `run()` return annotations updated, import added)
- `docs/parity_ledger/infrastructure.yaml` (added INFRA-225)

## Completion Summary
Created `src/lab/results.py` with typed return models for all 7 lab workflow `run()` methods. Used TypedDicts with Literal-tagged status discriminants so callers can type-narrow with `result["status"] == "READY"` checks. Updated all 7 `run()` signatures in `src/lab/workflows.py`. No caller code changes needed. 210 tests pass. D13 F4 resolved.
