---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED
phase: open
date: 2026-08-13
tags: [observability, documentation]
---

# TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED

## Title
`docs/guides/observability.md`'s stated import boundary ("`src/observability/` must never import
from `src/engine/`, `src/domains/`, `src/systems/`") is contradicted by `event_shapers.py`'s real
imports, and no existing architecture test enforces the doc's stated rule

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found incidentally during `TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS`'s
Document-Update phase, while correcting `docs/guides/observability.md`'s stale description of
`event_extractor.py` vs. `event_shapers.py` as the live event-derivation path.

`docs/guides/observability.md:185` states: **"Architecture boundary: `src/observability/` must
never import from `src/engine/`, `src/domains/`, or `src/systems/`."**

Direct read of `src/observability/event_shapers.py`'s import block confirms 3 real, unconditional,
top-level imports that appear to violate this stated rule:
- `src/observability/event_shapers.py:25` — `from src.domains.world_emergence.schema import
  WorldEventCategory`
- `src/observability/event_shapers.py:34` — `from src.domains.commitment.abandonment import
  AbandonmentEvaluator, AbandonmentCategory`
- `src/observability/event_shapers.py:35` — `from src.systems.strategic_systems.intelligence
  import _MAX_CONSECUTIVE_REJECTIONS`

Confirmed the existing architecture-boundary tests do **not** catch this: ran
`tests/architecture/test_phase19_observability_boundaries.py` and
`tests/architecture/test_phase18_import_boundaries.py` — both pass (3/3), but neither test asserts
the specific rule the doc states. `test_phase19_observability_boundaries.py`'s
`test_hot_path_does_not_import_heavy_analyzers` checks a narrower, different rule (hot-path modules
must not import heavy analyzer submodules like `observability.anomaly`/`observability.cognition`/
`observability.reporting`) — it says nothing about `src/engine/`, `src/domains/`, or
`src/systems/`. No other test found (via the same sweep) enforces the doc's stated blanket rule.

This means one of two things is true, and this ticket's job is to determine which:
1. The doc is stale/wrong — the real, intentional rule is narrower than stated (e.g. only certain
   `src/observability/` submodules are hot-path-restricted, and `event_shapers.py` was always meant
   to import from `src/domains/`/`src/systems/` for its push-shaper derivation logic) — in which
   case the doc needs correcting, not the code.
2. The doc is correct and `event_shapers.py`'s imports are a genuine, real architecture-boundary
   violation introduced at some point during the push-shaper migration epic (`TCK-20260806-PUSH-
   CUTOVER-COMBAT-ECONOMY-FACTION` and its siblings) — in which case either the imports need to be
   refactored out (e.g. via dependency injection / a narrower shared module) or the doc's rule
   needs an explicit, documented exception with rationale.

## Scope
- Determine, with git-blame/history evidence, when and why `event_shapers.py` first imported from
  `src/domains/`/`src/systems/` — was this a deliberate, reviewed decision (check the relevant
  push-shaper migration tickets' own Architecture-Verify passes) or an unnoticed drift?
- Determine the doc's own original intent — check `docs/architecture/
  observability_behavior_profiling_boundary.md` (the doc `test_phase19_observability_boundaries.py`
  actually validates) for whether it states the same or a different boundary rule than
  `docs/guides/observability.md:185`.
- Resolve the discrepancy: either correct `docs/guides/observability.md`'s stated rule to match
  reality (if the imports are legitimate), or file/implement a real architecture fix (if they're
  not) — do not silently leave the doc and the code disagreeing.
- If a real code fix is warranted, that likely exceeds hotfix tier — reassess tier at Investigate
  time and escalate to standard if a genuine refactor is needed.

## Out of Scope
- Any other claim in `docs/guides/observability.md` beyond this one import-boundary line — the rest
  of the doc was already reviewed and corrected by `TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-
  STALENESS`'s Document-Update phase.
- Re-auditing every other `src/observability/` file for the same potential violation — this ticket
  is scoped to the one concrete finding (`event_shapers.py`'s 3 imports); if Investigate finds more,
  handle within this ticket's own scope since it's the same root question, but don't proactively
  expand before that.

## Acceptance Criteria
- [ ] Root cause determined: is `docs/guides/observability.md:185`'s stated rule stale/wrong, or is
      `event_shapers.py`'s import genuinely a violation — with real evidence (git history, other
      docs, existing test intent), not assumed
- [ ] Resolved consistently: either the doc is corrected to state the real rule, or the code is
      fixed to comply with a real rule, or an explicit documented exception is added — not left
      contradicting itself
- [ ] If a real architecture test gap exists (no test enforces whatever the true rule turns out to
      be), a decision is made and recorded on whether to add one (may be out of this ticket's own
      scope if it requires new test infrastructure — file a further follow-up if so, don't leave it
      silently unstated)

## Related Tickets
- TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS (the ticket whose Document-Update phase
  found this while correcting an unrelated staleness in the same doc)

## Related Docs
- docs/guides/observability.md (line 185, the stated rule)
- docs/architecture/observability_behavior_profiling_boundary.md (the doc the existing test
  actually validates — check whether it states a matching or different rule)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/observability/event_shapers.py (lines 25, 34, 35 — the 3 flagged imports)
- tests/architecture/test_phase19_observability_boundaries.py
- tests/architecture/test_phase18_import_boundaries.py

## Assumptions / Open Questions
- Whether this is a doc-staleness issue (hotfix-appropriate) or a real architecture violation
  requiring a code refactor (likely standard-tier) is not yet known — Investigate must determine
  this before Plan/Implement proceeds, and the tier should be reassessed accordingly rather than
  forced into hotfix if a real refactor turns out to be needed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
