---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260801-PROVIDER-COVERAGE-TEST-STALE
phase: done
date: 2026-08-01
tags: [ai, agent-monitoring, testing]
---

# TCK-20260801-PROVIDER-COVERAGE-TEST-STALE

## Title
Repair stale real-corpus provider coverage expectation

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
Update the guardrail test whose zero-provider expectation became stale when
TCK-20260730-CLAUDE-EXECUTION-IDENTITY correctly began recording provider identity.

## Scope
- Assert provider coverage is populated without pinning a mutable corpus count.

## Out of Scope
- Any monitoring corpus rewrite or Codex provider record.

## Acceptance Criteria
- [x] The focused guardrail test passes with the legitimate Claude identity record.

## Related Tickets
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY
- TCK-20260731-CODEX-PILOT-EXECUTOR

## Related Docs
- docs/ai/monitoring_writer_decision.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/agent_codex_pilot_guardrails/test_concurrent_claim.py

## Assumptions / Open Questions
None.

## Implementation Notes
Implemented in the shared worktree before this traceability ticket was filed.

## Test Summary
`.venv/bin/python -m pytest -q tests/agent_codex_pilot_guardrails/test_concurrent_claim.py`
→ 5 passed.

## Files Changed
- `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py`

## Completion Summary
Replaced the obsolete exact-zero real-corpus provider assertion with a populated-coverage
assertion (`>= 1`). This remains tolerant of later legitimate identity-bearing workflow records
while proving the guardrail sees the Claude record that invalidated the original expectation.
