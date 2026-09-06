---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-ENTITY-EVOLVED-EVENT-GAP
phase: done
date: 2026-09-06
tags: [simulation-quality]
---

# TCK-20260906-ENTITY-EVOLVED-EVENT-GAP

## Title
Add a real entity_evolved observability event for the already-shipped XP-only evolution path

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 2 of 8. `docs/brainstorm/
rpg_expected_schemas.html`'s "Expected Events" section found this gap independent of any of M9's own
32 tracked ideas: no `entity_evolved` event exists today, even for the already-shipped XP-only
evolution path. Confirmed still real, 2026-09-06 — zero real code hits for `entity_evolved` anywhere
in `src/`.

## Scope
- Confirm the real XP-only evolution code path (likely in `src/domains/progression/` or
  `src/systems/lifecycle_systems/`, confirm exact location during Investigate).
- Add a real `entity_evolved` observability event, emitted on the actual evolution transition, mirroring
  the shape/conventions of this codebase's other 90 real event types in `src/observability/
  event_extractor.py`.
- Register the new event with SimQ per the standard M7-established pattern (a real signal rule, or an
  explicit written reason it's excluded) — cross-reference
  `docs/simulation_quality/event_type_coverage.md` rather than duplicating that audit.

## Out of Scope
- Building any new evolution mechanic — the XP-only path already exists and ships; this ticket only
  adds observability for it.
- Any other item from M9's scope.

## Acceptance Criteria
- [x] A real `entity_evolved` event fires on the actual XP-only evolution transition, confirmed via a
      test.
- [x] The event is registered with SimQ (a real signal rule, or an explicit written exclusion reason
      recorded in `event_type_coverage.md`).

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)

## Related Docs
- `docs/brainstorm/rpg_expected_schemas.html` — "Expected Events" section
- `docs/simulation_quality/event_type_coverage.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/observability/event_extractor.py`
- `src/domains/progression/`

## Assumptions / Open Questions
- The exact real code location of the XP-only evolution transition is not confirmed here — real work
  for this ticket's own Investigate phase.

## Implementation Notes
Real finding during Investigate: the live default event path for PROGRESSION events is
`src/observability/event_shapers.py::ProgressionShaper` (push-based, `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`
default ON), not `event_extractor.py` directly — that file is only the flag-gated rollback path.
Added `entity_evolved` to both, matching the existing `xp_granted`/`level_up` dual-path convention.
`EvolutionSystem` (`src/engine/evolution.py`) always writes `EntityUpdate.kind_set` (unchanged when
no evolution occurs), and `kind_set` lives on `EntityUpdate` itself, not `IdentityUpdate` like the
other 6 ProgressionShaper events — the detection is `kind_set != prior_ent.kind`, not a bare
non-None check (would false-fire every tick otherwise). Registered a new `species_evolution`
scoring rule (+10) on `ProgressionScorer` — PROGRESSION's own Question already names "evolving
their playstyle" as part of what this pillar tracks. Amended the now-stale `PROG-117` parity entry
("All 7 PROGRESSION event types...") and added new entry `PROG-125`, both via
`tools/parity_ledger_writer.py::write_entry()`. Updated `docs/brainstorm/rpg_expected_schemas.html`'s
idea-50 row to reflect the real shipped payload shape (`previous_kind`/`new_kind`, not the
originally-proposed `from_kind`/`to_kind`) — idea 50's own material-gated alternate branch remains
confirmed unshipped, out of this ticket's scope. Disclosed honestly (not fabricated): no shipped
calibration profile is confirmed to have an entity reach level 10 within existing tick budgets, so
this event is not yet observed in any real corpus run — recorded as an open gap in
`event_type_coverage.md`, matching `route_new_query`'s own precedent from the M9 batch's ticket 1.

## Test Summary
- `tests/unit/observability/test_event_shapers_progression.py` (2 new tests: pass/fail path),
  `tests/unit/observability/test_event_extractor_simq.py` (2 new tests: pass/fail path),
  `tests/simulation_quality/test_progression_scorer.py` (1 new test), and
  `tests/unit/progression/test_evolution.py` (1 new test — the real end-to-end proof: the actual
  `EvolutionSystem.evaluate()` output wired into the real `ProgressionShaper`, not a hand-built mock).
- Broader regression: `tests/unit/observability/ tests/simulation_quality/ tests/unit/progression/`
  — 1650 passed, 86 skipped, 0 failed.
- `tools/parity_index.py build`/`health` — status `ok`, 2175 entries.

## Files Changed
- `src/observability/event_shapers.py`
- `src/observability/event_extractor.py`
- `src/simulation_quality/scorers/progression.py`
- `config/simulation_quality/scoring_weights.yaml`
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/simulation_quality/event_type_coverage.md`
- `docs/brainstorm/rpg_expected_schemas.html`
- `docs/parity_ledger/progression.yaml`
- `tests/unit/observability/test_event_shapers_progression.py`
- `tests/unit/observability/test_event_extractor_simq.py`
- `tests/simulation_quality/test_progression_scorer.py`
- `tests/unit/progression/test_evolution.py`

## Completion Summary
Closed the standalone `entity_evolved` observability gap for the already-shipped XP-only species
evolution path. Wired into both the real live push-based `ProgressionShaper` and the flag-gated
`event_extractor.py` rollback path, correctly diffing the always-present `kind_set` field against
the prior tick's kind rather than a bare non-None check. Registered a new `species_evolution` SimQ
scoring rule on PROGRESSION. Found and fixed a stale parity entry (`PROG-117`) along the way.
Honestly disclosed that no shipped calibration corpus is yet confirmed to exercise this event —
correct wiring proven via the real `EvolutionSystem` production code path, not a fabricated corpus
claim.
