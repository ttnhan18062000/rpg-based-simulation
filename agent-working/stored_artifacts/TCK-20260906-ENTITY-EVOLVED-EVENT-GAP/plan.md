---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260906-ENTITY-EVOLVED-EVENT-GAP
date: 2026-09-06
---

# Plan: TCK-20260906-ENTITY-EVOLVED-EVENT-GAP

## Ordered Steps
1. Add `entity_evolved` to `src/observability/event_shapers.py::ProgressionShaper.shape()` —
   read `e_upd.kind_set`, diff against `prior_ent.kind`, emit with `{previous_kind, new_kind}`
   payload. Update the class docstring's event-type list.
2. Add the mirror block to `src/observability/event_extractor.py`'s flag-gated rollback path,
   diffing `entity.kind` against `prior_ent.kind` on already-applied state.
3. Register with SimQ: add `entity_evolved` to `ProgressionScorer.EVENT_TYPES`
   (`src/simulation_quality/scorers/progression.py`) and a new `score()` branch using a new
   `species_evolution` weight (`config/simulation_quality/scoring_weights.yaml`).
4. Update `docs/simulation_quality/quality_scoring_contract.md` §5 PROGRESSION (event list + new
   signal row) and `docs/simulation_quality/event_type_coverage.md` (§1.1 row, `scored` count,
   changelog).
5. Update `docs/brainstorm/rpg_expected_schemas.html`'s idea-50 row and section-lede — the doc
   already named this exact gap; reflect the real shipped payload shape and that idea 50's own
   material-gated branch remains unshipped.
6. Tests: extend the 3 sibling test files (`test_event_shapers_progression.py`,
   `test_event_extractor_simq.py`, `test_progression_scorer.py`) with pass/fail-path coverage, plus
   one real end-to-end proof in `test_evolution.py` wiring the real `EvolutionSystem.evaluate()`
   output into the real `ProgressionShaper`.
7. Parity: amend `PROG-117` (now-stale "7 event types" claim) and add new entry `PROG-125`, both
   via `tools/parity_ledger_writer.py::write_entry()`.
8. Finalize: move ticket to `tickets/done/`, fill Implementation Notes/Completion Summary, append
   `working_log.csv`, regenerate `docs/REGISTRY.yaml`, record agent-monitoring coverage.

## Files to Change
- `src/observability/event_shapers.py` (ProgressionShaper)
- `src/observability/event_extractor.py` (rollback-path mirror)
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

## Explicit Scope Guards
- Do NOT build idea 50's material-gated alternate evolution path — out of scope, unshipped, a
  separate future ticket's concern.
- Do NOT attempt to prove real-corpus calibration reachability — disclose the gap instead (matches
  `route_new_query`'s own precedent from M9's own ticket 1 batch).
- Do NOT touch `EvolutionSystem` itself — this ticket adds observability only, the mechanic is
  already correct and already unit-tested.

## Dependency Map
Steps 1-2 (event emission) must land before step 3 (scoring) can meaningfully reference the event
type. Step 4-5 (docs) and step 7 (parity) can happen any time after steps 1-3's real behavior is
known. Step 6 (tests) is written alongside steps 1-3, not after.

## Acceptance Criteria Map
- AC1 ("A real `entity_evolved` event fires on the actual XP-only evolution transition, confirmed
  via a test") — steps 1, 2, 6 (specifically the real-`EvolutionSystem`-integration test).
- AC2 ("The event is registered with SimQ") — step 3, verified by `TestEntityEvolved` in
  `test_progression_scorer.py`.

## Deviations
None from the original ticket scope. One clarification found during Investigate not present in the
ticket's own text: the real live event path is `event_shapers.py::ProgressionShaper`, not
`event_extractor.py` directly (that file is the flag-gated rollback path) — both were updated for
full coverage regardless of flag state, matching the existing `xp_granted`/`level_up` dual-path
convention.

## Unresolved Questions
None.
