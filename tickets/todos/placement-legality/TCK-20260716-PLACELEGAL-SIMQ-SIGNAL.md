---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260716-PLACELEGAL-SIMQ-SIGNAL
phase: open
date: 2026-07-16
tags: [simulation-quality, observability, world]
---

# TCK-20260716-PLACELEGAL-SIMQ-SIGNAL

## Title
Route the new spawn-occupancy hard-law violation into SimQ's WORLD DYNAMICS pillar as a frequency-scored signal

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`src/simulation_quality/quality_hub.py`'s `_translate_invariant()` is an already-shipped `law_id`-prefix dispatcher routing `HardLawMonitor` violations into SimQ scored events — it already routes `COMBAT`-prefixed violations to `combat_hard_law_violation`, scored by `CombatScorer`. `TCK-20260716-PLACELEGAL-HARDLAW` (this folder) adds a new law (working name `LAW-SPAWN-OCCUPANCY`) with no existing dispatcher branch. This ticket adds that branch and its scoring, following the exact precedent of the existing `building_sabotaged` row (`WorldDynamicsScorer`, `docs/simulation_quality/quality_scoring_contract.md` SQ-23): a system outside SimQ produces an event, WORLD DYNAMICS scores its frequency as a gradient.

This follows a real, already-established project precedent rather than inventing new SimQ scope: SimQ's own prior investigation (`stored_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2.2) explicitly excluded *determinism* from SimQ's scope — *"does not score correctness — that is `hard_law_monitor`; determinism/replay is a correctness property, not a health gradient."* Placement legality (is this one position walkable, yes/no) is a correctness property in exactly the same sense — a binary fact about one instant, not itself a gradient. What SimQ scores here is not "was this placement legal" (that's `HardLawMonitor`'s job, done in the parent ticket) but "how often does this violation class occur" — a frequency signal, same shape as `building_sabotaged`.

## Scope
- `src/simulation_quality/quality_hub.py::_translate_invariant()`: add a new branch matching the new law's `law_id` prefix (e.g. `LAW-SPAWN-OCCUPANCY`, confirmed against the parent ticket's final naming), routing to a new event type (e.g. `spawn_occupancy_violation`) — mirroring the existing `COMBAT*` branch's shape exactly.
- `src/simulation_quality/scorers/world_dynamics.py::WorldDynamicsScorer`: add the new event type to `EVENT_TYPES`, and add scoring logic matching the `building_sabotaged` row's shape (`worth_dynamics.py:175-176`) — a negative/penalized signal, since this event only ever represents a correctness violation (unlike some WORLD signals that have a healthy range, this one is unconditionally bad — zero occurrences is the correct target).
- `docs/simulation_quality/quality_scoring_contract.md`: add one new signal row to the `WORLD DYNAMICS` pillar table, matching the exact shape/column format of the existing `building_sabotaged` row (SQ-23).
- Confirm no re-anchor risk: run SimQ's existing anchor/grade-check tooling (`make evaluate --dry-run` or equivalent, per the `obs-isolation` folder's precedent for this exact check) against the current corpus before and after the change — the new signal should only fire on worlds/runs that already exhibit the reproduced seed-42 collision (a small, known subset), so existing anchor grades for unaffected runs must not shift.

## Out of Scope
- Anything in `HardLawMonitor` itself, or the call-site wiring in `Kernel.__init__` — entirely owned by `TCK-20260716-PLACELEGAL-HARDLAW` (this ticket only consumes the `law_id` that ticket produces).
- Any change to `EconomyScorer`'s existing, already-fully-wired `CONSERVATION` branch (`conservation_law_violated`/`conservation_law_verified`) — a separate, unrelated, already-complete piece of `_translate_invariant()`, not touched here.
- A new SimQ pillar or a standalone determinism-scoring mechanism — explicitly rejected per the Request Summary's precedent citation; this is a WORLD DYNAMICS frequency signal, not a new correctness-scoring system.
- Historical/retroactive re-scoring of past runs' existing `hard_law_violations.jsonl` records that predate this signal's addition.

## Acceptance Criteria
- `_translate_invariant()` correctly routes the new law's violations to the new event type; unit test covers both branches (violation present → event emitted; no violation → no event), mirroring existing `COMBAT*` branch test coverage.
- `WorldDynamicsScorer.EVENT_TYPES` includes the new event type; scoring logic produces a real, non-zero grade delta when the event fires, matching the `building_sabotaged` row's negative-signal shape.
- `docs/simulation_quality/quality_scoring_contract.md` WORLD DYNAMICS table has a new row for this signal, in the same format as SQ-23.
- Anchor/grade-stability check: existing anchor runs (unaffected by the seed-42 collision) show no grade change after this signal is added; affected runs show a real, expected grade delta.
- Depends on `TCK-20260716-PLACELEGAL-HARDLAW` being DONE first — the new `law_id` must exist and be producing real violations before this ticket's dispatcher branch has anything to route.

## Related Tickets
TCK-20260716-PLACELEGAL-HARDLAW (must complete first — see `SEQUENCE.md` in this folder)

## Related Docs
docs/plans/idea_placement_legality_check.md (originating investigation), docs/simulation_quality/quality_scoring_contract.md (WORLD DYNAMICS pillar table, SQ-23 precedent row), stored_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md (§2.2, the determinism-exclusion precedent this ticket's scope is built on)

## Related Stored Artifacts
none yet

## Related Code Areas
src/simulation_quality/quality_hub.py (`_translate_invariant`), src/simulation_quality/scorers/world_dynamics.py (`WorldDynamicsScorer`, `EVENT_TYPES`), docs/simulation_quality/quality_scoring_contract.md

## Assumptions / Open Questions
- Exact event-type name (`spawn_occupancy_violation` working name) and scoring weight — not calibrated; follow the same calibration discipline as other WORLD DYNAMICS signals (`tools/calibrate_simq.py` if a real weight-tuning pass is warranted, or a reasonable default matching `building_sabotaged`'s magnitude if the signal is expected to be rare).
- Whether this signal needs a positive/"no violations this run" counterpart event (mirroring `CONSERVATION`'s paired `_violated`/`_verified` events) or whether absence-of-event is sufficient (matching `building_sabotaged`, which has no positive counterpart) — default to no positive counterpart unless Investigate finds a concrete scoring reason to add one.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
