---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES
phase: done
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES

## Title
Port the 23 advisory and bookkeeping bash sites to args/runCommand and decide dispatch batching

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`. Depends on: none in this batch.

## Scope
Advisory (12) and bookkeeping (11) sites per classification.jsonl: `args` for start timestamp and execution id, `runCommand` otherwise, shadow-reviewer sites omitted. Includes the batching decision for 13 writeSidecar and 11 captureTs invocations (per-phase timestamps stamped by the existing monitoring agent, sidecar writes folded into the preceding agent) so the port does not add ~40 dispatches per run.

- Carried over from the parse-fix hotfix: take `start_ts` from `args` (today `scopeTs = await captureTs()` is a bash site pinned by tests), and decide the execution-id fallback: the clock-free `'fallback'` suffix means two runs of one ticket share an `execution_id` when the bash suffix fails and no `args.execution_id_suffix` is passed. Native path: return INVALID_ARGS when the arg is missing; legacy path: record the choice.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. The bookkeeping and advisory rows of classification.jsonl no longer call bash().
2. A recorded batching decision with measured or counted dispatches per full-tier run.
3. Monitoring run and event records for a legacy-path run are unchanged (pinned tests pass).

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT (parent epic)
- TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN (outcome: adopt for gates only, plus backstop)

## Related Docs
- `stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.md`
- `stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/`
- `stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- None beyond the parent epic's.

## Implementation Notes
Added `legacyBash`, `sh()` and `shOmit()` at the top of implement-ticket.js. Legacy runtime (bash present): every command runs through bash exactly as before. Native: `sh` dispatches an agent (create-tickets.js RUN_COMMAND pattern) and returns stdout; `shOmit` returns ''. 23 sites ported (rows stamped `ported_by` in classification.jsonl): 13 via `sh`, 10 via `shOmit` (clearSidecar, Scope-resume sidecar write, writeSidecar, captureTs, captureEpochMs, and the 5 deferred shadow-reviewer sites).
Batching decision (counted, not measured): natively the 13 writeSidecar + 11 captureTs dispatches per full-tier run are dropped (sidecar attribution from a dispatched agent's shell is not meaningful; per-event ts comes from the agents' reported ts). Remaining native dispatches from this class: resume seq offset, claim detection, execution id, ticket relocation, Files-Changed read, reindex, monitoring check and 3 advisories, about 8-10 per run. start_ts-from-args and the INVALID_ARGS decision for a missing execution_id_suffix are in the next child (INPUT-SITES). Classification test now compares unported rows to remaining bash( sites.

## Test Summary
1056 passed, 10 skipped, 1 xfailed across all tests referencing implement-ticket. Added node-run test of sh/shOmit under legacy (bash present) and native (bash absent) runtimes. Pin edits: 3 text pins renamed bash( to sh(/shOmit(; assertions unchanged.

## Files Changed
- `.claude/workflows/implement-ticket.js`
- `tests/tools/test_implement_ticket_bash_site_classification.py`, `test_shadow_reviewer_call_site.py`, `test_ticket_claim_detection.py`, `test_current_run_sidecar_orchestrator.py`
- `stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.jsonl`

## Completion Summary
23 of 38 bash sites ported behind a runtime-aware helper; 15 (gate, control, input) remain for sibling children. Legacy path unchanged.
