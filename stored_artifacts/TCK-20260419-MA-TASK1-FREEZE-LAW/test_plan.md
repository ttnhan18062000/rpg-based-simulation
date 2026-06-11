---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260419-MA-TASK1-FREEZE-LAW
artifact_type: test_plan
tags: [ma, task1, freeze, law]
---

# Test Plan: Milestone A Law Set Freeze

## Objective
Verify that the Milestone A law set is accurately documented, consistent across files, and covers all requirements specified in the implementation roadmap.

## Manual Verification
1. **Consistency Check**: Cross-reference `docs/engine/runtime_completion_contract_ma.md` with:
    - `src/engine/kernel.py`
    - `src/engine/apply.py`
    - `src/engine/checkpoint.py`
    - `src/engine/scheduler.py`
    Ensure that the "laws" described in the doc are the ones being implemented/pinned in the code.
2. **Completeness Check**: Verify that all items in the "Task 1 Checklist" from `resource_implementation_v3_milestone_a.md` are covered:
    - Freeze exact tick execution law
    - Freeze exact phase ownership
    - Freeze exact apply-path law
    - Freeze exact work-order law
    - Freeze exact checkpoint law
    - Freeze no-placeholder rule for baseline runtime
    - Freeze explicit non-goals

## Automated Verification
1. **Doc Integrity**: Run existing doc integrity tests (if any) to see if they need updates.
    - `tests/docs/test_doc_integrity.py` (if it exists)
2. **Linting**: Ensure that the new markdown files are valid.
