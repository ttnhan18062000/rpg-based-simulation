---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-PHASE-TIER-MATRIX-WORKFLOW-VERSION-STALE
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-HOTFIX-PHASE-TIER-MATRIX-WORKFLOW-VERSION-STALE

## Title
Fix `test_phase_tier_matrix_reads_real_implement_ticket_yaml`'s stale `workflow_version == 1`
assertion

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Part of a large batch of tickets fixing real, pre-existing failures found while auditing (1) the
16 test directories added by commit `29d78798` ("Simulation quality #20", 2026-08-14) that were
never wired into any CI job, and (2) the "Integration"/"API / tools / logging" CI jobs, which were
still failing after an earlier batch this session. This one:
`tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py::test_phase_tier_matrix_reads_real_implement_ticket_yaml`
asserted `matrix.workflow_version == 1`.

Root cause (confirmed via investigation): `agent-orchestration/workflows/implement-ticket.yaml`'s
`workflow_version` was legitimately bumped 1 → 2 by a later, unrelated ticket in the same squashed
commit batch (`TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY`, which added the
`continuation_policy` block). `matrix.py::load_supported_matrix()` correctly reads the real yaml
and returns `workflow_version=2`; only the test's hardcoded literal was never updated, since this
directory was never wired into CI and so the drift went uncaught.

## Scope
- Update the single hardcoded literal in
  `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py:24` from `== 1` to `== 2`.

## Out of Scope
- The 3 sibling `agent_codex_runtime_shadow` failures in this same batch caused by a real,
  separate contract-version-conflation bug (own standard-tier ticket).
- Any other ticket in this batch.

## Acceptance Criteria
- [ ] `test_phase_tier_matrix_reads_real_implement_ticket_yaml` passes.
- [ ] No other test in the file regresses.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py`

## Implementation Notes
Changed `assert matrix.workflow_version == 1` to `== 2`, matching the real, current
`agent-orchestration/workflows/implement-ticket.yaml`'s `workflow_version: 2`.

## Test Summary
- `pytest tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py -q`: 11 passed.

## Files Changed
- `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py` — line 24, `== 1` → `== 2`.

## Completion Summary
Fixed the stale test literal: `workflow_version` was legitimately bumped by an unrelated ticket in
the same original squash commit; the test's hardcoded expectation was never updated because this
directory was never wired into CI. No production code change.
