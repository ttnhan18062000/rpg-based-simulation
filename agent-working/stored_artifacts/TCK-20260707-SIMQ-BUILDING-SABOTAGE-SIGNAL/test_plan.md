---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL
artifact_type: test_plan
tags: [simulation-quality, world, observability]
---

# Test Plan — TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL

## Regression Surface

### Unit — event extraction
- `tests/unit/observability/test_event_extractor_world_dynamics.py` — must keep passing; this is
  the file the new `building_sabotaged` extraction test belongs in (mirrors its `_state`/`_update`/
  `_world_upd` `MagicMock` fixture style, same file family as `region_trauma_delta` coverage).
- `tests/unit/observability/test_event_extractor_world.py` — adjacent WORLD-diff extraction
  coverage; confirm no cross-talk from the new `building_updates` block.
- `tests/unit/observability/test_event_extractor_simq.py` — general extractor/SimQ interplay
  regression.

### Unit — scorer
- `tests/simulation_quality/test_world_dynamics_scorer.py` — must keep passing; add the new
  `TestBuildingSabotage` class here (same file, same `scorer`/`_ctx`/`_env` fixtures as
  `TestEcologyOwnership`/`TestRegion`/`TestStructureAndHazard`).
- `tests/simulation_quality/test_faction_scorer.py` — regression guard that `FactionScorer` was
  **not** touched (§7.3 no-dual-ownership; Out of Scope explicitly forbids a FACTION rule for this
  event).
- `tests/simulation_quality/test_weights.py` — confirms `ScoringWeights` still loads/validates after
  the new `WORLD:` key is added to `scoring_weights.yaml`.

### Integration
- `tests/simulation_quality/test_quality_hub_integration.py` — `SCORER_REGISTRY` auto-build from
  `EVENT_TYPES`, routing, accumulator update, persistence, error isolation, disable mechanism.
- `tests/simulation_quality/test_quality_hub_event_translation.py` — confirms the direct-emission
  path (no `_TRANSLATE_SIMPLE`/`_TRANSLATE_CONDITIONAL` entry needed, since `building_sabotaged`
  will be contract vocabulary directly) doesn't collide with existing translation table entries.
- `tests/simulation_quality/test_scenario_coverage.py` — all §6 Scenario Registry rows must still
  each have passing coverage; if a new scenario row is added per §7.2 step 4, this file needs a new
  test case for it.
- `tests/simulation_quality/test_kernel_simq_integration.py` — end-to-end `Kernel.tick_once()` →
  `EventExtractor` → `QualityHub` wiring; confirms the new extraction block doesn't break the live
  loop.
- `tests/integration/pipeline/test_strategic_cadence.py` — references `BuildingSabotageSystem`
  cadence wiring; must stay green since phase wiring is untouched.

### Architecture / integrity guards
- `tests/integrity/test_logic_guards.py` — asserts `BuildingSabotageSystem.resolve` call-site
  ordering in `src/engine/pipeline.py` via source-position checks. This ticket must not touch
  `pipeline.py`; re-run to confirm the guard is unaffected.
- `tests/unit/world/test_building_sabotage.py` — **not** part of this ticket's subsystem (tests the
  dead `src/town/sabotage.py::SabotageAction` legacy path) — run only to confirm it is untouched,
  do not treat its content as coverage for this change.

### Performance
- `tests/simulation_quality/test_performance.py` — `scorer.score()` must stay < 0.1ms/event with the
  new branch added; `QualityReport.build()` must stay < 50ms.

## New Tests Required

Per Acceptance Criteria:

1. **`test_building_sabotaged_emitted_on_negative_hp_delta`**
   - Category: unit (extraction)
   - Verifies: `EventExtractor.extract()` produces a `SimulationEvent(event_type="building_sabotaged", ...)`
     when `update.building_updates` contains a `BuildingUpdate` with `hp_delta < 0`, with payload
     carrying `building_id` and the resolved `region_id` (via `SpatialQueryService.get_building_region`
     — mock or stub at the state level per the file's existing `MagicMock` convention).
   - Location: `tests/unit/observability/test_event_extractor_world_dynamics.py`

2. **`test_building_sabotaged_not_emitted_on_functional_only_update`**
   - Category: unit (extraction, negative/edge case)
   - Verifies: a `BuildingUpdate` with only `functional_set=False` and `hp_delta=0` (the
     `town_resolution.py` insolvency path) does **not** emit `building_sabotaged` — proves the
     `hp_delta < 0` discriminator correctly excludes the non-sabotage writer of `building_updates`.
   - Location: `tests/unit/observability/test_event_extractor_world_dynamics.py`

3. **`test_building_sabotaged_scored_by_world_dynamics`**
   - Category: unit (scorer, positive signal — §11.1 "Positive signal")
   - Verifies: `WorldDynamicsScorer.score()` returns a `ScoreRecord` with
     `delta == scoring_weights["<new_rule_key>"]` and the correct tag for a `building_sabotaged`
     envelope; `pillar == PillarId.WORLD`.
   - Location: `tests/simulation_quality/test_world_dynamics_scorer.py` (new `TestBuildingSabotage`
     class, mirrors `TestStructureAndHazard`)

4. **`test_building_sabotaged_not_scored_by_faction`**
   - Category: unit (scorer, null return — §11.1 "Null return" + §7.3 conflict guard)
   - Verifies: `FactionScorer.score()` returns `None` for a `building_sabotaged` envelope, and
     `"building_sabotaged" not in FactionScorer.EVENT_TYPES` — proves the Out-of-Scope FACTION
     exclusion holds.
   - Location: `tests/simulation_quality/test_faction_scorer.py` (or as a standalone assertion in the
     new `TestBuildingSabotage` class in `test_world_dynamics_scorer.py`, matching the existing
     `TestEcologyOwnership.test_ecology_not_in_economy_scorer` pattern)

5. **`test_building_sabotaged_registered_in_scorer_registry`**
   - Category: unit (registration/tag assignment — §11.1 "Tag assignment")
   - Verifies: `"building_sabotaged" in WorldDynamicsScorer.EVENT_TYPES` (mirrors
     `TestEcologyOwnership.test_ecology_owned_by_world_scorer`).
   - Location: `tests/simulation_quality/test_world_dynamics_scorer.py`

6. **Scenario coverage row** (if a new §6 entry is added per §7.2 step 4)
   - Category: integration (scenario coverage)
   - Verifies: the new scenario's event_type reaches `WorldDynamicsScorer` with correct pillar and
     polarity, per the file's existing `test_sq*` pattern.
   - Location: `tests/simulation_quality/test_scenario_coverage.py`

7. **Calibration comparison** (AC item 5 — not a pytest unit test, a documented artifact)
   - Category: manual/scripted calibration run, not part of the automated suite
   - Verifies: `python3 tools/calibrate_simq.py --name urban_political --seed 42 --ticks <T>` before
     and after the change; inspect `quality_scores.jsonl`/`quality_report.json` for
     `building_sabotaged` hit count and WORLD grade delta. Per the investigation's Risk #1, the
     realistic expected outcome is **zero hits** (no code path in `src/` currently produces a
     `SABOTAGE` intent) — document this honestly per Scope item 5, backed by the repo-wide grep
     evidence already gathered in `investigation.md`, not as an unexplained null result.

## Scoped Pytest Commands

```bash
# Extraction-layer unit tests
python3 -m pytest tests/unit/observability/test_event_extractor_world_dynamics.py \
  tests/unit/observability/test_event_extractor_world.py \
  tests/unit/observability/test_event_extractor_simq.py -v

# Scorer-layer unit tests (WORLD + conflict guards)
python3 -m pytest tests/simulation_quality/test_world_dynamics_scorer.py \
  tests/simulation_quality/test_faction_scorer.py \
  tests/simulation_quality/test_weights.py -v

# SimQ integration + scenario coverage + hub wiring
python3 -m pytest tests/simulation_quality/test_quality_hub_integration.py \
  tests/simulation_quality/test_quality_hub_event_translation.py \
  tests/simulation_quality/test_scenario_coverage.py \
  tests/simulation_quality/test_kernel_simq_integration.py -v

# Pipeline wiring / architecture guards (must stay green, unmodified)
python3 -m pytest tests/integrity/test_logic_guards.py \
  tests/integration/pipeline/test_strategic_cadence.py \
  tests/unit/world/test_building_sabotage.py -v

# Performance budget
python3 -m pytest tests/simulation_quality/test_performance.py -v

# Full SimQ domain sweep before claiming completion (not the whole repo suite)
python3 -m pytest tests/simulation_quality/ tests/unit/observability/ -m "not slow"

# Corpus regression per AC item 6 — never re-run the full engine suite for this
make evaluate --dry-run
```

## Anti-Drift Test Guards

- `test_building_sabotaged_not_scored_by_faction` (New Test 4) directly guards against the
  Out-of-Scope violation of adding a secondary FACTION rule — this is the single highest-value
  anti-drift test in this ticket given the ticket text itself flags FACTION as a "plausible"
  temptation.
- `test_building_sabotaged_not_emitted_on_functional_only_update` (New Test 2) guards against a
  broader-than-intended `building_updates` diff that would also fire on the unrelated
  `town_resolution.py` insolvency path (`functional_set=False`, no `hp_delta`) — silently conflating
  two unrelated building-state-change causes into one signal would be a correctness regression, not
  just a scope issue.
- `tests/integrity/test_logic_guards.py` guards against accidentally touching
  `src/engine/pipeline.py`'s phase ordering or call sites while implementing the emission fix —
  since the correct fix site is `event_extractor.py`, not `pipeline.py`, this test should require no
  changes; any diff to it during implementation is a signal the change landed in the wrong layer.
- Re-run `tests/simulation_quality/test_faction_scorer.py` in full (not just the one new negative
  test) to confirm no accidental cross-import or shared-state leakage between `WorldDynamicsScorer`
  and `FactionScorer` was introduced.
- `make evaluate --dry-run` (AC item 6) is the corpus-wide anti-drift guard — it must show 0
  regressions across all calibrated scenarios (not just `urban_political`), catching any unintended
  WORLD-grade shift in `dungeon_crawl`, `sandbox_world`, or other anchored worlds from the new
  scoring branch.
