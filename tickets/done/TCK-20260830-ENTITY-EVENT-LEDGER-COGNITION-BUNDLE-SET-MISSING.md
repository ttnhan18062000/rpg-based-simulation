---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260830-ENTITY-EVENT-LEDGER-COGNITION-BUNDLE-SET-MISSING
phase: open
date: 2026-08-30
tags: [observability]
---

# TCK-20260830-ENTITY-EVENT-LEDGER-COGNITION-BUNDLE-SET-MISSING

## Title
Add `docs/event_ledger/entity.yaml` Coverage for `EntityUpdate.cognition_bundle_set`

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`tests/tools/test_entity_event_ledger.py::test_entity_ledger_covers_every_entity_update_field`
fails: `EntityUpdate.cognition_bundle_set` (added to `src/core/updates.py:655`) has no
corresponding entry in `docs/event_ledger/entity.yaml`. Found while verifying no hard errors were
introduced by merging `origin/main` into `m1-quick-wins` (2026-08-30) — this gap predates the
merge (the field and its 3 real write sites — `src/domains/memory/phase.py`,
`src/engine/quests.py`'s ESCORT-quest reputation wiring, `src/engine/pipeline_phases/hardening.py`
— were added earlier in the M1 batch, most recently by
`TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING`) and was not caught by that ticket's own scoped
Test-phase run.

## Scope
- Investigate what real observability event(s), if any, `cognition_bundle_set` writes produce
  (check `src/observability/event_extractor.py` for any diff block reading
  `entity.cognition`/`CognitionModel` changes) across its 3 real write sites.
- Add a `docs/event_ledger/entity.yaml` entry (`mutation_source: "EntityUpdate.cognition_bundle_set"`)
  following the file's existing entry format (see `ENTITY-019`/`ENTITY-020` for the closest
  precedent shape — a `status: observed` or `status: silent` entry as the evidence actually
  supports, not assumed).
- If genuinely no event is emitted for this field's mutation (a real observability gap, not just
  missing documentation), disclose that distinctly rather than writing a `status: observed` entry
  that isn't true.

## Out of Scope
- Wiring a new observability event if one doesn't already exist — that's a separate scope decision
  from documenting current (possibly silent) behavior.
- Any other `EntityUpdate` field's ledger coverage.

## Acceptance Criteria
- `test_entity_ledger_covers_every_entity_update_field` passes.
- The new entry's `status`/`event_types`/`evidence` accurately reflects real, verified behavior
  (real event-extractor code read, not assumed).

## Related Docs
- docs/event_ledger/entity.yaml
- tests/tools/test_entity_event_ledger.py

## Related Code Areas
- src/core/updates.py (EntityUpdate.cognition_bundle_set)
- src/domains/memory/phase.py
- src/engine/quests.py
- src/engine/pipeline_phases/hardening.py
- src/observability/event_extractor.py

## Assumptions / Open Questions
Resolved: no observability event exists for cognition_bundle_set mutations (verified: 0 grep
matches for "cognition_bundle_set", ".cognition\b", or "CognitionModel" in
src/observability/event_extractor.py). Genuinely silent, not just undocumented.

## Implementation Notes
Added `docs/event_ledger/entity.yaml` entry ENTITY-021, `status: silent`, citing the 3 real
production write sites (src/domains/memory/phase.py:51, src/engine/quests.py:249,
src/engine/pipeline_phases/hardening.py:106) and the confirmed-zero grep evidence. Did not wire a
new observability event — out of scope per the ticket's own boundary; disclosed as a stated,
genuine gap rather than fixed.

## Test Summary
tests/tools/test_entity_event_ledger.py: 3 passed.

## Files Changed
docs/event_ledger/entity.yaml

## Completion Summary
Fixed while confirming PR #90's CI was fully green after the origin/main merge — this was the
sole remaining real (non-environment) CI failure in the "API / tools / logging" job.
