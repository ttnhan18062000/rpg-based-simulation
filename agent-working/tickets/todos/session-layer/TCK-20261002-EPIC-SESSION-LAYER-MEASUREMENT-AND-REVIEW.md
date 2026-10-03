---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW
phase: open
date: 2026-10-02
tags: [ai, process-improvement, agent-monitoring]
---

# TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW

## Title
Epic D — Session-layer measurement and evidence review: does the owner repeat fewer instructions, and which advisory rules earn hardening

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P3

## Request Summary

The point of the session layer is **fewer repeated owner instructions, not fewer owner decisions**. Without
measurement we cannot tell whether Epics A to C worked, which advisory rules recur, or whether deferred items
(auto-wake, a message inbox, hard blocking of message classes, the authority digest pin) are worth building.

This epic adds the **minimum measurement** the review needs (M6a), a report-only analytics and roster check
(M6b), and the first-month **evidence review** (M7). M7 depends on four weeks of real data after Epics A and B
land, so this is a **time-gated epic**: it cannot close earlier, and it is not a candidate for `implement-epic`
until the data window has elapsed.

Binding plan: `docs/plans/agent_infrastructure/session_layer_working_process.md` (sections 11, 12.2).

## Scope

- **M6a — minimum measurement.**
  - A `session_role` field on monitoring events and runs, **read from the resolved per-session binding
    record** (Epic A), separate from `agent`, so a session resumed outside the launcher is still attributed
    (or recorded `unresolved`). `SESSION_ROLE` is only an input to that resolution.
  - The **headline metric: manual orchestration actions per completed batch**, counting categories of
    *repeated* instruction (role reminder, routing correction, manual wake, worktree correction, boundary
    reminder, handover recovery) and **not** genuine owner decisions, design feedback or new requirements.
    The tagging method (prompt-submit hook sampling, or a one-line owner tally per batch) is decided from
    Epic A's M0 result; a raw user-prompt count is explicitly not the metric.
  - **Batch latency as three measures**: implementation latency (dispatch to PR green), finalization latency
    (PR green to finalized) and batch cycle time (dispatch to finalized), with batch status derived from PR
    and ticket artifacts and **no batch registry**.
- **M6b — analytics and roster check (report-only).** Misroutes, bounces, idle stall, handoff latency,
  `role_boundary` warnings, `/clear` count and tokens re-read; and the roster check: stale role citations,
  roles with no handover, worktrees with no role, unknown session names, orphaned instances with their
  in-flight work, one session holding two seats, an unstaffed seat with no named holder.
- **M7 — first-month evidence review.** Four weeks after M6a data exists for Epics A and B: harden or retire
  advisory rules on measured recurrence; decide the deferred items (inbox, auto-wake, hard message blocking,
  the authority digest pin) on evidence; simplify or remove unused configuration; propose retiring seats
  that did not act for two retros.

## Out of Scope

- Building any deferred item (each becomes its own ticket if M7 justifies it).
- Any blocking gate over monitoring data (advisory and report-only until measured, per the repo's standing
  preference).
- Changes to the retro report's existing sections beyond adding these measures.
- Identity, registry and launcher (A); routing and guardrails (B); hygiene tooling (C).

## Acceptance Criteria

1. Monitoring events and runs carry `session_role` from the resolved binding record; a session resumed
   outside the launcher is attributed correctly or marked `unresolved`; `agent` vocabulary is untouched (the
   `vocabulary_drift` ratchet does not move).
2. The headline metric is defined with its category list and tagging method, computed for at least one real
   completed batch, and **demonstrably excludes** a legitimate owner decision (a seeded example).
3. The three batch latencies are computed from artifacts for a real batch, and a batch with a green PR and no
   Finalize shows as *not done*.
4. The analytics and roster check run report-only and exit 0; a seeded orphaned instance and a session
   holding two seats are reported.
5. **M7:** a written review at least four weeks after M6a data begins, covering for each advisory rule its
   recurrence and a harden / keep / retire decision, and an explicit decision on each deferred item, with the
   evidence cited.

## Related Tickets

- Depends on Epics A and B: `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (binding record),
  `TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY` (`role_boundary` events).
- Sibling: `TCK-20261002-EPIC-SESSION-LAYER-OPERATIONS` (C).
- Parent of child tickets to be created by the agent-working planner.
- Prior art: the monitoring anomaly-detection epic (report-only ratchets) and
  `TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION` (do not gate on historical debt).

## Related Docs

- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding)
- `docs/agent-monitoring/schema.md`
- `docs/agent-monitoring/README.md`

## Related Stored Artifacts
None.

## Related Code Areas
`tools/agent-monitoring/` (event writers, retro generator); the per-session binding record; `docs/agent-monitoring/`.

## Assumptions / Open Questions

- Whether a prompt-submit hook payload allows tagging repeated instructions, or the owner tally is used, is an
  M0 result in Epic A.
- The four-week window starts when Epics A and B are both landed and `session_role` data exists; the epic
  stays open until M7 reports.

## Implementation Notes

Child tickets are created later by the agent-working planner. Suggested, non-binding: M6a `session_role`
field; M6a headline metric and tagging; M6a batch latencies; M6b analytics; M6b roster check; M7 review.
**Time-gated:** do not route this epic through `implement-epic` before the data window has elapsed.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)
