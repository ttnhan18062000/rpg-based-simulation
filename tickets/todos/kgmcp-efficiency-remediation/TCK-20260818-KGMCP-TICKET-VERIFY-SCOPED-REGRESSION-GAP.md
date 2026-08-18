---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP
phase: open
date: 2026-08-18
tags: [testing, process-improvement, mcp]
---

# TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP

## Title
Close the Verify-phase test-scoping gap that let a KGMCP ticket ship with two pre-existing tests broken

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD` legitimately changed
`tools/retrieval_cache.py` (new table, schema version bump 2->3) per its own accepted plan.md
design decision (DD1). Its Verify/Finalize phase ran its own new tests and reported success, but
did not catch that the change broke two *pre-existing* tests elsewhere in the suite
(`tests/tools/test_knowledge_gateway_cache.py::test_no_junction_table_or_new_sqlite_table_
introduced_by_this_ticket`, `tests/tools/test_knowledge_gateway_redaction.py::
TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`) —
both hardcoded point-in-time snapshot values from earlier, closed tickets that this ticket's own
design legitimately superseded. The gap only surfaced when the real GitHub Actions "API / tools /
logging" job failed after merge, requiring `TCK-20260818-HOTFIX-KGMCP-STALE-SCOPE-GUARD-TESTS` as
a separate follow-up hotfix. This ticket closes the process gap so the next ticket that touches a
shared, widely-depended-on module doesn't repeat it.

## Scope
- Investigate how the CACHE-ATTRIBUTION ticket's Test/Verify phase scoped its test run — did it
  run only its own new test files, or a broader directory, and if broader, why did it still miss
  these two? (Check whether `tests/tools/test_knowledge_gateway_cache.py` and
  `tests/tools/test_knowledge_gateway_redaction.py` were even included in whatever command ran.)
- Identify the general pattern: a ticket's Verify phase needs to run the full test directory for
  any module it modifies (not just files it directly edited or added), including tests that only
  *reference* the module's public constants/schema (as both broken tests did, via `import ... as
  rc` / `re_mod`) — grep-based or import-graph-based test discovery, not just "tests in the same
  folder as the ticket's new tests."
- Propose and implement a concrete mechanism (a gate check, a Verify-phase instruction update in
  the relevant workflow/agent prompt, or a lightweight pre-Finalize test-impact-scan script) that
  would have caught this specific case, and prove it by reproducing the exact failure mode: revert
  `tools/retrieval_cache.py`'s schema-version constant to a stale test value in a throwaway branch
  or local sandbox and confirm the new mechanism flags it before Finalize.
- This is a pipeline/process fix, not a KGMCP fix — but it's scoped under the KGMCP epic because
  it was discovered by, and is being fixed in response to, real KGMCP-ticket damage.

## Out of Scope
- Any change to `tools/retrieval_cache.py` itself — that module is not touched by this ticket.
- Rewriting the whole Verify/Test phase pipeline — scope the fix narrowly to closing this specific
  class of gap (shared-module test-impact scoping), not a general pipeline redesign.
- Retroactively re-verifying every other already-closed ticket for the same class of gap — that's
  a separate, larger audit a human reviewer can scope later if this ticket's finding suggests it's
  widespread.

## Acceptance Criteria
- [ ] Root cause identified: exactly what test-scoping decision (or its absence) let the two
      broken tests through the CACHE-ATTRIBUTION ticket's own Verify/Finalize phase.
- [ ] A concrete, working mechanism lands that would have caught this specific case.
- [ ] The mechanism is proven against a reproduction of the exact real failure mode (not just
      asserted to work in the abstract).
- [ ] The relevant workflow/agent-prompt documentation is updated to describe the new mechanism,
      so future ticket implementers/verifiers actually use it.

## Related Tickets
- TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC (parent)
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD (introduced the gap)
- TCK-20260818-HOTFIX-KGMCP-STALE-SCOPE-GUARD-TESTS (the resulting hotfix this ticket aims to make
  unnecessary for future tickets)

## Related Docs
- `docs/testing/test_taxonomy.md`
- Relevant workflow/agent prompt files for the Test/Verify phases (identify exact paths during
  investigation — likely `.claude/agents/test-scoper.md` and/or
  `.claude/workflows/implement-ticket.js`'s Test/Verify phase steps).

## Related Stored Artifacts
(To be created during implementation.)

## Related Code Areas
- `.claude/agents/test-scoper.md`
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- Open: whether the right fix is a documentation/prompt change (relying on agent discipline) or a
  scripted gate check (structural, not relying on discipline) — given this project's stated
  preference for structural guards over instructions alone (see the CACHE-ATTRIBUTION ticket's
  own self-contamination guard, made "structural, not incidental"), prefer a scripted check if one
  is feasible within scope; fall back to a documentation fix only if investigation shows a general
  script isn't practical.

## Implementation Notes
(Fill in during implementation.)

## Test Summary
(Fill in during implementation.)

## Files Changed
(Fill in during implementation.)

## Completion Summary
(Fill in when done.)
