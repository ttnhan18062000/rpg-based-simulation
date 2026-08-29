---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY
artifact_type: test_plan
tags: [temporal, determinism, world]
---

# Test Plan — TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY

No `src/` code changes are in scope for this ticket (see `plan.md`'s "What this ticket does NOT do") — there
is no behavior to unit- or integration-test. Verification is documentation-consistency and evidence-integrity
checking instead:

## Normal flow

- Every citation in `investigation.md` (file:line references for `state.py`, `legality.py`, `apply.py`,
  `raid.py`, `cohort.py`) is re-verified against the actual repo state at close time — not just trusted from
  when the investigation was written — in case an unrelated concurrent change shifted line numbers or values.
- `docs/REGISTRY.yaml` regenerated (`tools/generate_registry.py`) after this ticket's frontmatter is added,
  same as any other new doc/ticket, and the drift check (`tests/tools/test_generate_registry.py`) passes.

## Edge cases

- If a concurrent session's work has changed one of the cited files (e.g. `move_cost`'s default) between
  investigation and close, the investigation's numbers are re-derived, not left stale — a wrong "real number"
  in a decision record is worse than an admitted gap.

## Failure modes

- If the plan owner defers all four decisions in `plan.md` rather than accepting/redirecting them, this
  ticket does not silently close as done — it either stays `INPROGRESS`/`BLOCKED` with the deferral recorded
  in Open Questions, or moves to `tickets/done/` only with an explicit "deferred, no decision made yet" note
  in its Completion Summary, never presented as if a decision happened when it didn't.

## Regression-prone paths

- None — this ticket touches no shared runtime code path. The regression risk is purely documentation
  (another doc contradicting this decision record after it's written) — mitigated by recording the outcome
  in `rpg_design_roadmap.md`'s single "Temporal axis" section rather than scattering it, consistent with this
  session's existing pattern for the codex-review reconciliation.

## Architecture tests

- Not applicable — no durable state, no authoritative mutation path, no read-only decision logic touches
  live state in this ticket. (Documentation/decision-record ticket only.)
