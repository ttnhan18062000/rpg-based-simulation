---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260524-LAB-REQUEST-CONTEXT
phase: done
date: 2026-05-24
tags: [lab, request, context]
---

# TCK-20260524-LAB-REQUEST-CONTEXT

## Title

Implement Input Request Model and Context Pack Builder (M94-M95)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement validated Pydantic input request schemas for workflows (`generic` vs `specific` modes) and build a token-conserving `ContextPackBuilder` that aggregates high-level summaries/indexes without importing large raw telemetry files.

## Scope

- Implement Pydantic `WorkflowRequest` model with mode-specific validations (mode, workflow name, constraints, user_goal required for generic).
- Implement `ContextPackBuilder` in `src/lab/context.py`:
  - Support `build_generation_context_pack` and `build_investigation_context_pack`.
  - Extract index-level information (worlds, scenarios, experiments) without parsing raw reports.
  - Exclude heavy files like `simulation_events.jsonl` by default.
  - Implement rules and known issues extraction with tags/domains.
  - Format output both as JSON (`context_pack.json`) and Markdown (`context_pack.md`).
- Implement unit tests in:
  - `tests/unit/lab_agent/test_workflow_request_model.py`
  - `tests/unit/lab_agent/test_context_pack_builder.py`

## Out of Scope

- Core workflow execution logic (M96 - M102).
- CLI implementation.

## Acceptance Criteria

- `WorkflowRequest` correctly validates input options, requiring `user_goal` for generic mode.
- `ContextPackBuilder` aggregates indexes and filters known issues, respecting item limits.
- Raw simulation logs are strictly excluded by default to conserve context budgets.
- All request and context unit tests pass perfectly (100% success rate).

## Related Tickets

- `TCK-20260524-WORKFLOW-REGISTRY` (Done)

## Related Docs

- `lab_phase14.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/request.py`
- `src/lab/context.py`
- `tests/unit/lab_agent/test_workflow_request_model.py`
- `tests/unit/lab_agent/test_context_pack_builder.py`

## Assumptions / Open Questions

- We assume standard index files (`world_index.json`, `scenario_index.json`, `experiment_index.json`) exist in the environment or can be mocked during testing.

## Implementation Notes

- Ensure model fields use proper type definitions and optional filters are case-insensitive.

## Test Summary

- Automated unit tests implemented:
  - `tests/unit/lab_agent/test_workflow_request_model.py` (7 tests passing)
  - `tests/unit/lab_agent/test_context_pack_builder.py` (4 tests passing)
- 100% success rate on both test suites.

## Files Changed

- `src/lab/__init__.py`
- `src/lab/request.py`
- `src/lab/context.py`
- `tests/unit/lab_agent/test_workflow_request_model.py`
- `tests/unit/lab_agent/test_context_pack_builder.py`

## Completion Summary

- Implemented `WorkflowRequest` Pydantic model enforcing mode specific inputs and constraints verification.
- Implemented `ContextPackBuilder` ensuring token-efficient context packaging using a **Summary First, Index Second, Evidence Third** hierarchy.
- Confirmed that heavy telemetry logs (like `simulation_events.jsonl`) are strictly ignored in context packs, while metadata summaries/scorecards are correctly compiled.
- Confirmed that missing indexes produce safe warning logs rather than crashing the builder.

