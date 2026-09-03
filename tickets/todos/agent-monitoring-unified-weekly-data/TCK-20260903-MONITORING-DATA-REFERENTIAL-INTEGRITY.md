---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY
phase: open
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality, schema]
---

# TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY

## Title
Build referential-integrity verification across `runs`/`events`/`tools`
(`events.run_id → runs.run_id`, `tools.(run_id, seq) → events.(run_id, seq)`), cross-ISO-week-
boundary aware

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 6 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`, directly implementing the requester's
explicit instruction: *"verify if they are linked between (like foreign keys)"*.
`docs/agent-monitoring/schema.md` already documents this FK model in prose (confirmed via direct
read this session): `events.jsonl` is "One record per agent call within a workflow run. FK: `run_id →
runs.run_id`" (line 126, field table line 144); `tools.jsonl` is "Joined to events by `run_id` +
`seq`" (line 342), with `run_id` documented as "FK → runs.jsonl" (line 366) and `seq` as
"FK → events.seq" (line 367). **This contract has never been automated/verified — it is prose only.**
This ticket makes it a real, tested check.

**The single most important correctness requirement for this ticket, confirmed by direct
investigation this session:** a `run_id`'s `events`/`tools` rows can legitimately land in a
**different** week folder than its own `runs.jsonl` row, or than each other — whenever a run/session
crosses an ISO-week boundary. `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` already confirms
pause/resume-across-a-boundary is a real, previously-encountered scenario for this exact `(run_id,
seq)` join. A referential-integrity checker that assumes same-week-folder locality will produce false
positives on entirely legitimate data — the checker must load and join across **all** week folders
for a given `run_id`, never scope its lookup to one folder.

**Documented, schema-sanctioned exceptions the checker must NOT flag** (per `schema.md`'s own text,
confirmed this session):
- Retrieval-event shadow rows: `run_id` prefix `RETRIEVAL-EVENT-<slug>` intentionally has no matching
  `runs.jsonl` row (schema.md lines 325-335) — excluded from the `events.run_id → runs.run_id` check.
- `tools.jsonl` rows with `run_id: null` — tool calls made outside an active workflow run (interactive
  session use), not an FK violation (schema.md line 366).
- `context-packet-wrapper` shadow rows with negative `seq` (`seq <= 0`, schema.md lines 145, 310) —
  deliberately disjoint from the monotonic `seq` range, excluded from the
  `tools.(run_id, seq) → events.(run_id, seq)` check.

## Scope
- Build `tools/agent-monitoring/verify_referential_integrity.py` (new script, or a new function
  added to `validate.py` alongside its existing `compute_drift_report()`-style functions —
  implementer's choice, document which and why) that:
  - Loads all week folders' `runs`/`events`/`tools` files (reusing the dual-mode/glob loading pattern
    children 1-3 establish for the new layout, not a fourth independent loader).
  - For every `events` row (excluding `RETRIEVAL-EVENT-<slug>` `run_id`s), confirms its `run_id` has
    a matching `runs` row anywhere across all week folders.
  - For every `tools` row with a non-null `run_id` and `seq >= 1` (excluding `run_id: null` and
    `seq <= 0` shadow rows), confirms a matching `events` row exists at that exact `(run_id, seq)`
    anywhere across all week folders.
  - Produces a structured report (violation counts + concrete examples: `run_id`/`seq`/week-folder of
    each orphan), matching `validate.py`'s existing report-function output style.
- New pytest suite covering, at minimum: (a) same-week-only join (baseline correctness), (b) a
  `run_id` whose `events`/`tools` rows legitimately span 2+ week folders — must NOT be flagged, (c) a
  genuinely orphaned `tools` row with no matching `events` row anywhere — MUST be flagged, (d) a
  genuinely orphaned `events` row with no matching `runs` row anywhere — MUST be flagged, (e) each of
  the 3 documented exception shapes above — must NOT be flagged.
- Run the tool against the real, post-migration corpus and capture the real report in this ticket's
  Test Summary. If it finds real violations, they must be reported and explicitly triaged in
  Implementation Notes (accepted-as-known-legacy-noise vs. a real bug needing its own follow-up) —
  never silently suppressed or worked around to make the check report clean.

## Out of Scope
- Building a general-purpose relational/SQL referential-integrity engine — only these 2 specific FK
  relationships, matching the epic's own Out of Scope boundary.
- Wiring this check into `done_checker_static.py` as a new blocking DoD gate, or into CI, unless the
  real-corpus run above finds it needs to be — if it's added as a gate, that's a deliberate decision
  to record explicitly, not an assumed default.
- Repairing any orphan this check finds — this ticket verifies and reports, it does not fix upstream
  data-quality bugs beyond what children 1/3/4's own bug fixes already cover.
- Any change to the 3 per-line record schemas.

## Acceptance Criteria
- [ ] All 5 test scenarios in Scope pass, each a testable assertion.
- [ ] **Explicit cross-week-join test** (scenario b above) passes — this is the key architectural
      risk this ticket exists to cover; a same-week-only implementation must fail this test.
- [ ] The tool runs successfully against the real post-migration corpus and its output (clean, or
      explicitly triaged violations) is captured in Test Summary.
- [ ] The tool's report format is documented (either in the script's own docstring or a doc file) well
      enough for a future consumer (dashboard, gate check, or manual audit) to parse it.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — hard prerequisite: needs real migrated multi-week
  data to test against)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE, -CONSUMERS-GATES-DASHBOARD, -CODEX-REMIGRATION
  (children 3-5 — independent, file-disjoint, parallelizable with this ticket once child 2 lands)
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION — confirms the cross-week-boundary `(run_id,
  seq)` scenario this ticket's core correctness requirement is built around.
- TCK-20260729-SHADOW-PACKET-CALL-SITE — established the negative-`seq` shadow-row exception this
  ticket must not flag.

## Related Docs
- `docs/agent-monitoring/schema.md` lines 126, 144, 342, 366-367 (the FK contract this ticket
  automates), lines 325-335 (the `RETRIEVAL-EVENT-<slug>` exception), lines 145, 310
  (the shadow-`seq` exception).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/validate.py` (existing report-function style/precedent to match)
- `tools/agent-monitoring/verify_referential_integrity.py` (new, exact filename implementer's choice)

## Assumptions / Open Questions
- Assumes child 2 has landed.
- Whether this becomes a new standalone script or a new function in `validate.py` is left to the
  implementer's judgment — document the choice and why.
- Whether any real violations found against the live corpus warrant their own follow-up
  hotfix/investigation ticket is a decision to make at implementation time based on what the real run
  actually finds, not pre-decided here.
- `layer: observability` matches this repo's established pattern; `schema` tag reflects this ticket's
  focus on the record-join/schema-contract dimension, matching the prior epic's migration child's use
  of the same tag for a related shape-contract concern.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
