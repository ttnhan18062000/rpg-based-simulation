---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-INPUT-SITES
phase: done
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-INPUT-SITES

## Title
Port the 5 input-class bash sites to runCommand

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child of `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`. Depends on: TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES.

## Scope
Input sites compute values handed to agents or gates; failure is visible to the receiving agent so plain `runCommand` is enough, except the parity-ledger `git status` that feeds a gate, which waits for the attested route.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. The input rows (except the parity-ledger status) no longer call bash().
2. Markers parsed as `{exit_code, stdout}` as in the create-tickets pilot.
3. Existing pinned tests pass or are updated with the same assertions.

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
Ported 6 sites via `sh`: input rows 19, 22, 26, 27 (arch static checks, expected test dirs, expected parity subsystems, next ledger id) and the two plain-runcommand control rows 13 and 33 (frontmatter-FAIL classification, docs-changed check), which the epic split had not assigned to a child. Row 28 (parity-ledger git status) stays for the attested-gates child as the classification says. Native runtime now returns INVALID_ARGS before any work when `args.start_ts` or `args.execution_id_suffix` is missing (design review notes 1 and 3); `startTs` prefers `args.start_ts`. Legacy runtime unchanged: both args are optional there.

## Test Summary
1058 passed, 10 skipped, 1 xfailed across all tests referencing implement-ticket; new test pins the INVALID_ARGS gate ahead of any work. One pin (startTs line) updated to the new expression.

## Files Changed
- `.claude/workflows/implement-ticket.js`
- `tests/tools/test_implement_ticket_bash_site_classification.py`, `tests/tools/test_step0_ts_orchestrator.py`
- `stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.jsonl`

## Completion Summary
6 more sites ported (29 of 38 total); 9 gate/attested sites remain for ATTESTED-GATE-SITES. Native INVALID_ARGS gate added.
