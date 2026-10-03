# Workflow Tuning Follow-ups — Implementation Sequence

Two tickets filed 2026-07-05 from the "build now" recommendations of
`TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION` (`tickets/done/`). Both modify
`.claude/workflows/implement-ticket.js`, but in disjoint regions (a new gate inserted between
Test/Parity and Verify vs. the existing Parity phase's own agent-call condition), so there is no
ordering dependency between them.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260705-WORKFLOW-SECURITY-GATE | No preference either way — listed first only because it was Candidate 2 in the source investigation |
| 2 | TCK-20260705-WORKFLOW-PARITY-SKIP | Independent of ticket 1; can be done first, last, or in parallel |

## Dependency Notes

- No hard dependency between these two tickets — pick whichever order suits available time/interest.
- Both touch `implement-ticket.js`, but in different phases (a new gate between Test/Parity/Verify vs.
  the existing Parity phase's own skip condition) — confirm no line overlap during Investigate for
  whichever is implemented second, the same discipline used for the sibling
  `tag-taxonomy-followups`/`TCK-20260705-TAG-SKILL-SUGGEST` vs. `TCK-20260705-TAG-REGISTRY-QUERY` pair.
- Both require updating `docs/ai/workflows.md`, `docs/ai/system_overview.md`, and
  `docs/ai/ticket-lifecycle.md` if the phase list changes — if both land in the same session, reconcile
  these doc updates together rather than each ticket independently re-deriving the current phase count.
- Two candidates from the same investigation were explicitly **not** ticketed here, per the
  investigation's own recommendation: auto-invoking a suggested skill during Implement (Candidate 1,
  deferred — needs a skill-invocation primitive first) and skipping the Test phase for docs-only
  tickets (Candidate 4, rejected — directly falsified by this session's own evidence). Do not
  resurrect either as a ticket without new justification.
