---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP
phase: done
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP

## Title
Re-run the static gates orchestrator-side after a native run returns

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
The attestation design found agent-reported gate results forgeable. Add the unforgeable backstop: after a native implement-ticket run returns, the top-level session (which has a shell) re-runs `done_checker_static.py` and the validators before commit; document it in the implement-ticket skill and `docs/guides/delivery_process.md`. CI remains the second backstop.

## Out of Scope
- Any other workflow script; sites owned by a sibling child.

## Acceptance Criteria
1. A documented, runnable post-native-run check (one command) that exits non-zero on any gate failure.
2. The implement-ticket skill instructs running it before commit.
3. Test that the check fails on a ticket with a missing working_log row.

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT (parent epic)
- TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN (outcome: adopt for gates only, plus backstop)

## Related Docs
- `docs/guides/delivery_process.md`
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
New `tools/gate_checks/post_native_run_check.py --ticket-id T`: read-only wrapper that re-runs done_checker_static, validate_frontmatter and ticket_field_values, prints PASS/FAIL per check and exits 1 on any failure. Documented in `docs/guides/delivery_process.md` (new subsection) and in the implement-ticket skill (one paragraph). Legacy and hand-executed paths are unaffected.

## Test Summary
4 new tests in tests/tools/test_post_native_run_check.py (missing ticket; done ticket with no working_log row fails and names done_checker_static; CLI exit code; passes for a real closed ticket). 631 passed in the related skill/orphan/doc/frontmatter selection.

## Files Changed
- `tools/gate_checks/post_native_run_check.py`
- `tests/tools/test_post_native_run_check.py`
- `docs/guides/delivery_process.md`, `.claude/skills/implement-ticket/SKILL.md`

## Completion Summary
The unforgeable post-native-run re-run exists and is documented; the attested-gates child can now rely on it.
