---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL
phase: done
date: 2026-07-07T16:31:09Z
tags: [simulation-quality, world, observability]
---

# TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL

## Title
Emit a `building_sabotaged` observability event and score it under the existing WORLD pillar

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2.6 (formally recorded in
`TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC`'s new §7.5 of
`docs/simulation_quality/quality_scoring_contract.md`) found that `building_sabotage` — pipeline
phase 15, `src/engine/sabotage.py::BuildingSabotageSystem.resolve()` ("Law: Entities can damage town
infrastructure (LEG-RPG-001/006). Sabotaged buildings lose functionality, impacting regional
services.") — is a live, non-dead mechanic exercised by real corpus content
(`urban_political`'s resolved world spec and `data/content/world_modules/trading_company_hub.yaml`
both reference sabotage-relevant buildings), but is invisible to every SimQ pillar: it mutates
`building_updates` (hp_delta, functional_set) directly in durable state without emitting any
`ObservabilityEventEnvelope`/`SimulationEvent`.

This is the one genuine, evidence-backed gap the epic's pillar-completeness research found — not
grounds for an 11th pillar (see `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC`), but a real narrow gap:
closing it requires two pieces of work, not one, because there is currently no event for a scorer to
hook into:

1. **Emit a new event** (e.g. `building_sabotaged`) from `BuildingSabotageSystem.resolve()`.
2. **Add a scoring rule** consuming that event under the existing **WORLD** pillar — the contract's
   WORLD pillar question ("Is the world itself alive... regions transforming... or is the world a
   static backdrop entities move through without consequence?") squarely covers infrastructure
   damage as a "world consequence" signal. `FACTION` is a plausible secondary owner given
   `urban_political`'s faction-conflict framing, but WORLD is the decided primary per the contract's
   §7.3 conflict-detection rule (no existing pillar currently claims building-state events) — this
   was already decided during epic scoping and is not to be re-litigated here.

This is the lowest-priority ticket in the epic and lands last, after
`TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC` for citation.

## Scope
1. Add a new event type (e.g. `building_sabotaged`) and emit it from
   `BuildingSabotageSystem.resolve()` in `src/engine/sabotage.py` at the point where a sabotage
   intent is successfully resolved against a building (the existing `building_updates` mutation
   site) — follow the existing `ObservabilityEventEnvelope`/`SimulationEvent` emission pattern used
   by other engine-phase systems (survey a comparable phase's emission call as the pattern to
   mirror, e.g. another WORLD-pillar-scored event type per the contract §5).
2. Register the new event type in whatever central event-type registry/enum the observability system
   uses (mirror how other event types are registered — do not invent a parallel mechanism).
3. Add a new scoring rule to `src/simulation_quality/scorers/world_dynamics.py` (the WORLD pillar
   scorer) consuming `building_sabotaged`, per the contract's §7.2 "Adding a Scoring Rule to an
   Existing Pillar" protocol:
   - Add the rule's delta key and default value to `config/simulation_quality/scoring_weights.yaml`
     under the WORLD pillar section
   - Add the conditional logic to `world_dynamics.py` using `self.weights["<new_rule_key>"]` — no
     numeric literals in scorer code
   - Add the tag to WORLD's tag documentation in the contract's §5
   - Add a row to the contract's §6 Scenario Registry for the new scenario
   - Add the event_type to WORLD's "Event types scored" list in the contract's §5
4. Add a unit test for the new scoring rule (inject a `ScoringWeights` fixture, per §7.2 step 5 —
   not production config values).
5. Run a real calibration comparison in `urban_political` (the one world confirmed to exercise
   sabotage-relevant content per investigation.md §2.6's grep evidence) — before/after this change —
   to confirm the new event/signal actually fires, and document honestly whatever the resulting
   WORLD grade impact is (it may be a no-op if no sabotage actually occurs in that world's default
   calibration run; that is an acceptable, honestly-documented outcome, not a required grade change).

## Out of Scope
- Creating an 11th top-level pillar — explicit scope guard; this is a WORLD-pillar rule addition
  only, per the decision already made in epic scoping and recorded in
  `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC`.
- Adding the scoring rule to FACTION instead of (or in addition to) WORLD, even though
  investigation.md §2.6 notes FACTION as a plausible secondary owner — WORLD is the decided primary
  per the §7.3 conflict-detection rule; do not re-litigate this in this ticket.
- Any change to `BuildingSabotageSystem.resolve()`'s existing mutation logic (hp_delta,
  functional_set) beyond adding the event emission — this ticket adds observability, it does not
  change sabotage mechanics.
- Authoring new sabotage-relevant content in any world beyond what already exists in
  `urban_political`/`trading_company_hub.yaml`.

## Acceptance Criteria
- [x] `BuildingSabotageSystem.resolve()` emits a `building_sabotaged` (or equivalently named) event
      on successful sabotage resolution, registered in the observability event-type system
- [x] A new WORLD-pillar scoring rule in `world_dynamics.py` consumes this event, with its delta
      value sourced from `scoring_weights.yaml` (no numeric literals in scorer code)
- [x] `quality_scoring_contract.md` §5 (WORLD's event list and tags) and §6 (Scenario Registry) are
      updated per the §7.2 protocol
- [x] A unit test exists for the new scoring rule, using an injected `ScoringWeights` fixture
- [x] A real before/after calibration comparison in `urban_political` confirms the event fires (or
      honestly documents that it does not under default calibration conditions), with the resulting
      WORLD grade impact documented either way
- [x] `make evaluate --dry-run` confirms 0 regressions on the rest of the corpus

## Related Tickets
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC (parent epic; this is the lowest-priority child, lands last)
- TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC — hard dependency; this ticket cites that ticket's new
  §7.5 subsection of `quality_scoring_contract.md` as its evidence source and must land after it

## Related Docs
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2.6 (the full finding: live
  mechanic, no event emission, WORLD-pillar recommendation, FACTION as rejected secondary owner)
- `docs/simulation_quality/quality_scoring_contract.md` §5 (WORLD pillar definition), §7.2 (Adding a
  Scoring Rule to an Existing Pillar — the exact protocol this ticket follows), §7.3 (Conflict
  Detection Rules — the basis for choosing WORLD over FACTION)
- `docs/engine/authoritative_pipeline.md` — "The 31 Phases of Refinement," phase 15
  (`building_sabotage`)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` (see Related Docs)

## Related Code Areas
- `src/engine/sabotage.py` — `BuildingSabotageSystem.resolve()`
- `src/simulation_quality/scorers/world_dynamics.py` — WORLD pillar scorer
- `config/simulation_quality/scoring_weights.yaml` — WORLD pillar section
- `docs/simulation_quality/quality_scoring_contract.md` — §5, §6
- `data/worlds/urban_political/` — the one world confirmed to exercise sabotage-relevant content

## Assumptions / Open Questions
- Assumes `urban_political`'s default calibration run actually triggers a sabotage resolution at
  least once within its normal tick range — this must be live-verified per Scope item 5, not
  assumed; if it does not, the acceptance criteria's before/after comparison should honestly report
  a null result rather than forcing an artificial trigger.
- Assumes the observability event-type registration mechanism this ticket needs to hook into follows
  the same pattern as other engine-phase event emissions — if `src/engine/sabotage.py`'s call site
  turns out to require a different mechanism (e.g. no direct access to an event emitter at that point
  in the pipeline), this may require a small refactor beyond a single emission call; if so, document
  it as an implementation finding rather than silently expanding scope without noting it.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL/plan.md`'s 10
steps, with no deviations.

- **Step 1** — Added a new `building_sabotaged` diff block to `EventExtractor.extract()`
  (`src/observability/event_extractor.py`), placed as a sibling loop after the existing
  `world_updates` loop (not the ticket's literal Scope wording of emitting from
  `BuildingSabotageSystem.resolve()` — `sabotage.py` has no event-emitter access at its call site,
  matching every other WORLD-pillar sibling event's post-hoc extraction pattern, per
  investigation.md's confirmed finding). Discriminator is `hp_delta < 0` on
  `update.building_updates`, which is exclusive to `BuildingSabotageSystem.resolve()` (confirmed:
  `town_resolution.py` only sets `functional_set`, `conservation.py` never touches `hp_delta`).
  Region attribution uses `SpatialQueryService.get_building_region(current_state, b_id)` via a
  local import inside the new block, matching the identical local-import convention used by
  `town_resolution.py` and `sabotage.py` for the same lookup (no existing `src.engine` import block
  to extend at module level, so a local import was used rather than introducing a new module-level
  `src.observability` → `src.engine` coupling point).
- **Step 2** — Added `"building_sabotaged"` to `WorldDynamicsScorer.EVENT_TYPES` and a new
  `if et == "building_sabotaged":` branch in `score()` (`src/simulation_quality/scorers/world_dynamics.py`),
  reading `self.weights["infrastructure_damaged"]` — no numeric literals in scorer code.
- **Step 3** — Added `infrastructure_damaged: 1.0` to the `WORLD:` section of
  `config/simulation_quality/scoring_weights.yaml`, positive delta matching `hazard_active`'s
  "real world consequence" framing (not a damage=bad framing — WORLD's degenerate tags describe
  absence of activity, not damage).
- **Steps 4-5** — Updated `docs/simulation_quality/quality_scoring_contract.md` §5 (WORLD DYNAMICS
  event list + signal table row) and §6 (new `SQ-23` Scenario Registry row).
- **Step 6** — Added a `building_sabotaged` row to `docs/simulation_quality/event_type_coverage.md`
  §1.1 (0 calibration hits, classified `scored` not `no_engine_path` — genuine emission path exists,
  just no live SABOTAGE-intent producer) and incremented the Summary `scored` count 81→82.
- **Step 7** — Added tests: `TestBuildingSabotaged` (3 tests) in
  `tests/unit/observability/test_event_extractor_world_dynamics.py`; `TestBuildingSabotage` (2 tests)
  in `tests/simulation_quality/test_world_dynamics_scorer.py`; `TestBuildingSabotageOwnership`
  (2 tests) in `tests/simulation_quality/test_faction_scorer.py`; `test_sq23_world_owns_building_sabotaged`
  in `tests/simulation_quality/test_scenario_coverage.py`.
- **Step 8** — Ran a real before/after calibration comparison in `urban_political` (seed 42, 500t)
  via `git stash`/`stash pop` around the three implementation files. Before: WORLD norm=+0.3725,
  events=134, overall_grade=S, overall_score=2.0356. After: WORLD norm=+0.3725, events=134,
  overall_grade=S, overall_score=2.0356 — byte-identical pillar breakdown. `building_sabotaged` hit
  count: 0 in both runs (confirmed via `quality_report.json`/`quality_scores.jsonl`). This is the
  expected, pre-authorized outcome per investigation.md's repo-wide grep evidence: no
  strategic/goal-selection/quest-reward code anywhere in `src/` currently sets
  `task_upd.work_kind_set="SABOTAGE"` or `payload_set["action"]="SABOTAGE"`.
- **Step 9** — Added parity ledger entry `WORLD-111` to `docs/parity_ledger/world_dynamics.yaml`
  (P2, `status: verified`, real `test_path`), after the existing `WORLD-110` entry. Did not reuse
  `WORLD-088`/`WORLD-089` (confirmed pre-existing, cover unrelated mutation-level facts).
- **Step 10** — Full scoped regression: `pytest tests/simulation_quality/ tests/unit/observability/
  -m "not slow"` → 1178 passed, 6 skipped, 0 failures. `make evaluate` (dry-run corpus diff against
  grade anchors) → 710 pillars checked, 0 regressions, 0 missing.

No deviations from the plan.

## Test Summary
Scoped sweep (Step 7's exact command list) — 203 passed, 2 xfailed, 0 failures:
```
pytest tests/unit/observability/test_event_extractor_world_dynamics.py \
  tests/unit/observability/test_event_extractor_world.py \
  tests/unit/observability/test_event_extractor_simq.py \
  tests/simulation_quality/test_world_dynamics_scorer.py \
  tests/simulation_quality/test_faction_scorer.py \
  tests/simulation_quality/test_weights.py \
  tests/simulation_quality/test_quality_hub_integration.py \
  tests/simulation_quality/test_quality_hub_event_translation.py \
  tests/simulation_quality/test_scenario_coverage.py \
  tests/simulation_quality/test_kernel_simq_integration.py \
  tests/integration/pipeline/test_strategic_cadence.py \
  tests/integrity/test_logic_guards.py \
  tests/unit/world/test_building_sabotage.py \
  tests/simulation_quality/test_performance.py
```
`tests/integrity/test_logic_guards.py` passed unchanged, confirming the fix landed in
`event_extractor.py`/`world_dynamics.py`, not `pipeline.py`.

Full scoped regression (Step 10): `pytest tests/simulation_quality/ tests/unit/observability/ -m
"not slow"` → 1178 passed, 6 skipped, 26 deselected, 0 failures.

`make evaluate` (dry-run) → 710 pillars checked across all calibrated worlds, 0 regressions,
0 missing.

Live before/after calibration (`urban_political` seed42 500t) — see Implementation Notes Step 8:
WORLD grade/score byte-identical before and after; `building_sabotaged` calibration_hits = 0 in
both runs (expected null result, not a bug).

## Files Changed
- `src/observability/event_extractor.py` — new `building_sabotaged` diff block
- `src/simulation_quality/scorers/world_dynamics.py` — new `EVENT_TYPES` entry + scoring branch
- `config/simulation_quality/scoring_weights.yaml` — new `infrastructure_damaged: 1.0` WORLD key
- `docs/simulation_quality/quality_scoring_contract.md` — §5 event list + signal table row, §6 SQ-23 row
- `docs/simulation_quality/event_type_coverage.md` — new coverage row + Summary count update
- `docs/parity_ledger/world_dynamics.yaml` — new `WORLD-111` entry
- `tests/unit/observability/test_event_extractor_world_dynamics.py` — `TestBuildingSabotaged` (3 tests)
- `tests/simulation_quality/test_world_dynamics_scorer.py` — `TestBuildingSabotage` (2 tests)
- `tests/simulation_quality/test_faction_scorer.py` — `TestBuildingSabotageOwnership` (2 tests)
- `tests/simulation_quality/test_scenario_coverage.py` — `test_sq23_world_owns_building_sabotaged`

## Completion Summary
All 6 acceptance criteria met. `building_sabotaged` is emitted by `EventExtractor.extract()`
(diffing `update.building_updates` for `hp_delta < 0`, the exclusive signature of
`BuildingSabotageSystem.resolve()`) and scored by `WorldDynamicsScorer` under the WORLD pillar
via a new `infrastructure_damaged` weight (no numeric literals in scorer code). Contract §5/§6,
`event_type_coverage.md`, and parity ledger (`WORLD-111`) are all updated. A real before/after
`urban_political` calibration confirms the event's engine path is genuine but currently unreached
(0 hits, byte-identical WORLD grade before/after) — an honestly-documented, pre-authorized null
result per investigation.md's repo-wide grep evidence that no SABOTAGE-intent producer exists
anywhere in `src/` yet. Full scoped regression and `make evaluate --dry-run` both show 0
regressions.
