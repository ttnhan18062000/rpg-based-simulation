---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260903-ECONOMIC-VACANCY-SIGNAL
phase: done
date: 2026-09-03
tags: [economy, lifecycle]
---

# TCK-20260903-ECONOMIC-VACANCY-SIGNAL

## Title
The Empty Chair — economic-vacancy signal on sole-occupant production role death

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 64 — "The Empty Chair": emit a readable economic-vacancy signal when the sole occupant of a production-relevant role dies, so consuming economy systems can detect the gap. This is the real remaining half of idea 64 after heir-assignment split cleanly to TCK-20260824-DEFAULT-HEIR-ASSIGNMENT (idea 10, confirmed DONE, entirely resource/inheritance, no production overlap). Investigation found EntityRole (src/core/enums.py) has no unique/singular production role concept — production today is entity-agnostic (BlacksmithSystem: proximity+materials/gold only; TownResolutionSystem: BuildingState.functional driven by faction-level maintenance solvency, never entity occupancy) — so this ticket must first define what "occupies" a production role before a vacancy signal is meaningful, then emit and wire a typed EconomicVacancyEvent-equivalent through the authoritative apply path.

## Scope
- Define what constitutes a "sole occupant/holder of a defined production-relevant role" (Plan-phase design decision, not pre-decided).
- On that occupant's death (PP-33, lifecycle.py), commit a typed vacancy signal (EconomicVacancyEvent-equivalent, following EconomyHealthMonitor's SimulationEvent-based alert pattern) through the authoritative apply path, carrying vacated_role and a location identifier.
- Use region_id as the location identifier (interim substitute for the schema doc's location_place_id, which depends on unbuilt idea 66).
- Wire the signal to be readable by at least one consumer (PP-07 BlacksmithSystem or PP-20 TownResolutionSystem).
- Vacancy remains detectable (not auto-resolved) across ticks if unfilled.
- Regression test: single-production-entity town, entity killed, N ticks advanced, measurable production-throughput delta vs. same-seed control.

## Out of Scope
- Any apprenticeship/recovery/auto-refill mechanism (explicitly flagged as scope creep in docs/brainstorm/codex/2026-08-27-core-rpg-new-idea-portfolio.md Candidate J) — vacancy SIGNAL only.
- filled_by_entity_id resolution logic (apprentice promotion vs import vs stays-vacant) — explicitly open in the schema doc, not decided here.
- Personal resource/inheritance handling — already covered by TCK-20260824-DEFAULT-HEIR-ASSIGNMENT (confirmed DONE).
- location_place_id / idea 66 Place-model integration — use region_id instead.
- A new headcount-gap detector duplicating OccupationChangeGoalScorer (TCK-20260824-OCCUPATION-CHANGE-TRIGGER) — review during design, do not fork a second parallel detector.

## Acceptance Criteria
- [x] The death (PP-33) of the sole occupant/holder of a defined production-relevant role commits a typed EconomicVacancyEvent-equivalent through the authoritative apply path, carrying vacated_role and the vacating entity/region_id.
- [x] The emitted signal is actually readable by at least one consuming system (PP-07 or PP-20), proven by a test that reads it from state/events, not just constructs it in isolation.
- [x] The vacancy remains detectable (not auto-resolved) if left unfilled across a subsequent tick.
- [x] **AC4 (REVISED during Plan/Review — see Assumptions / Open Questions and Implementation Notes below):** a regression scenario (single-production-entity town, entity killed, N ticks advanced) shows a measurable **vacancy-detection-signal** delta vs. a same-seed control run. (Originally worded "production-throughput delta"; revised because `BlacksmithSystem.enforce` is confirmed entity-agnostic and gating it would break `TOWN-017`'s verified P0 parity entry — see rationale below.)
- [x] Plan phase produces an explicit, documented definition of what "occupies" a production-relevant role (EntityRole has none today) before implementation begins, recorded in plan.md.

## Related Tickets
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
- TCK-20260824-OCCUPATION-CHANGE-TRIGGER

## Related Docs
- docs/audits/D19_domain_phase_inventory.md
- docs/brainstorm/rpg_expected_schemas.html
- docs/brainstorm/codex/2026-08-27-core-rpg-new-idea-portfolio.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/lifecycle_systems/lifecycle.py
- src/engine/blacksmith.py
- src/engine/town_resolution.py
- src/ai/goals/occupation_change_scorer.py
- src/economy/health_monitor.py
- src/core/enums.py
- tests/unit/economy/test_economy_health_monitor.py
- tests/unit/economy/test_economy_alerts.py
- tests/unit/strategic/test_occupation_change_scorer.py
- tests/integration/strategic/test_occupation_change_reachability.py
- tests/unit/progression/test_lifecycle.py

## Assumptions / Open Questions
- What counts as an "occupied production role" is undefined in the current codebase (no unique/singular production role on EntityRole) — a real Plan-phase design decision, bigger than "add one event class"; must not be silently resolved. **Resolved in plan.md's "Occupancy Definition" section**: an entity is the only *living* (`lifecycle.active and combat.alive`) entity in its *region* whose `identity.role` is in `{SHOPKEEPER, WORKER}`.
- location_place_id depends on unbuilt idea 66's Place model — confirm idea 66's landing status, or proceed with region_id as the recommended interim substitute. **Resolved**: idea 66's Place model is confirmed not merged into this branch; `region_id` used throughout, as planned.
- filled_by_entity_id resolution strategy is an explicitly open design question in docs/brainstorm/rpg_expected_schemas.html, not decided by this ticket. **Confirmed still out of scope**: no `filled_by_entity_id`/apprentice-promotion/auto-refill logic exists anywhere in the diff.
- **AC4 revision (deviation, documented per plan.md's "AC4 revision rationale" section, same class as Coming-of-Age's role-gate addition and Clan-Lifecycle's asset_ids inertness note)**: the ticket's original AC4 ("measurable production-throughput delta") was revised during Plan/Review to "measurable vacancy-detection-signal delta." `BlacksmithSystem.enforce` (`src/engine/blacksmith.py`) is confirmed fully entity-agnostic — any qualifying entity can craft regardless of the vacancy signal — so a literal crafted-item-count delta is not something this design produces, and gating `BlacksmithSystem` on the signal to manufacture one would both violate this ticket's own out-of-scope guard against recovery/refill mechanics and break `TOWN-017`'s verified P0 parity entry (`docs/parity_ledger/town_resource.yaml`). The delivered regression test (`test_single_production_entity_town_regression_vacancy_detection_delta`, `tests/integration/economy/test_economic_vacancy_signal.py`) instead measures the delta this design honestly produces: the vacancy-detection signal (Step 2 emission at PP-33 → Step 3 consumption at PP-20) is present and counting in the treatment run (entity killed) and absent (0) in the control run (entity survives), across the same seed and same N ticks.
- **`tests_v2/parity/test_town_resolution_parity.py` (cited by plan.md Step 3's Verify section and by `TOWN-017`'s existing `test_path`) does not exist in this worktree** — confirmed via `find`/`git log -- tests_v2`, no `tests_v2/` directory has ever existed in this branch's history. This appears to be a stale reference predating this worktree, unrelated to this ticket's own changes, and `TOWN-017`'s entry is left untouched per the plan's explicit scope guard. As a substitute regression guard, `tests/unit/resource/test_resource_v2_boundary.py::test_blacksmith_craft_refactor` and the other `TownResolutionSystem`-exercising suites (`tests/unit/world/test_building_interaction_contract.py`, `tests/unit/core/test_interaction_recovery.py`, `tests/integration/pipeline/test_strategic_cadence.py`, `tests/integrity/test_logic_guards.py`) were run instead and confirmed passing unchanged — see Test Summary.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260903-ECONOMIC-VACANCY-SIGNAL/plan.md` (post-review
revision), no deviations from the plan's steps:

1. **`WorldEventCategory.PRODUCTION_ROLE_VACATED`** added as one new additive enum member in
   `src/domains/world_emergence/schema.py`, following the existing grouped-comment style.
2. **`EconomicVacancyService.check_and_emit(state, recent_deaths) -> StateUpdate`** — new file
   `src/economy/vacancy.py`, mirroring `FactionInfluenceService.process_influence_shift`'s exact
   staticmethod shape. Module-level `_PRODUCTION_RELEVANT_ROLES = (SHOPKEEPER, WORKER)` constant
   (new, not reused from `OccupationChangeGoalScorer`'s `_CANDIDATE_ROLES`, which also includes
   GUARD). Scans `recent_deaths` for a production-relevant role whose region (via
   `LegalityServiceV2.get_region_for_position`) has zero other living holders of that role, where
   "living" is filtered on **both** `other.lifecycle.active` and `other.combat.alive` — deliberately
   stricter than `OccupationChangeGoalScorer`'s `combat.alive`-only filter, because `combat.alive_set`
   is never written for OLD_AGE deaths (only KILL/HAZARD outcomes write it), so an old-age corpse's
   `combat.alive` stays `True` forever and would be miscounted as a live occupant under a
   `combat.alive`-only filter. Covered directly by
   `tests/unit/economy/test_vacancy.py::test_old_age_death_of_prior_occupant_does_not_mask_vacancy`.
3. **Call site** — `LifecycleSystem.resolve_lifecycle` (`src/systems/lifecycle_systems/lifecycle.py`),
   inside the existing `if recent_deaths:` aggregate block, alongside (not inside) the existing
   `FactionInfluenceService` calls. Added `vac_update = EconomicVacancyService.check_and_emit(...)`
   and a new `world_events_add=list(update.world_events_add) + list(vac_update.world_events_add)`
   keyword to the block's existing `replace(update, ...)` call — additive only, the block's three
   existing fields (`world_updates`, `entities_add`, `entities_remove`) are untouched. Not inlined
   into the per-entity death loop, matching the block's existing local-vs-aggregate-logic separation.
4. **`TownResolutionSystem.resolve`** (`src/engine/town_resolution.py`, PP-20) wired as consumer:
   reads `state.recent_world_events` (previous tick's applied, one-tick-lagged window — same law as
   `FactionAwarenessService.compute_tension_updates`) immediately after the early-exit checks, before
   the entity loop, and additively increments
   `metric_counters["economic_vacancy_detected_region_<region_id>"]` per matching
   `PRODUCTION_ROLE_VACATED` event. Added `metric_counters=new_metric_counters` to the function's
   final `replace(update, ...)` call. Does **not** touch `BuildingState.functional` or gate
   `BlacksmithSystem.enforce` — confirmed via direct read that `TOWN-017`
   (`docs/parity_ledger/town_resource.yaml`) is `priority: P0`, so gating crafting on this signal
   would have broken a P0-protected verified entry.
5. **Tests** — new `tests/unit/economy/test_vacancy.py` (7 tests, direct
   `EconomicVacancyService.check_and_emit` unit coverage including the old-age-staleness regression),
   3 new tests added to `tests/unit/progression/test_lifecycle.py`
   (`test_sole_shopkeeper_death_emits_vacancy_event`,
   `test_non_sole_occupant_death_does_not_emit_vacancy_event`,
   `test_role_and_region_scope_of_sole_occupant_check`, all driven through
   `LifecycleSystem.resolve_lifecycle` per plan.md's Step 2 Verify section), and new
   `tests/integration/economy/test_economic_vacancy_signal.py` (4 tests: real apply-path commit test
   via `ApplyPath.apply_generation`, consumer-readability test against
   `TownResolutionSystem.resolve`, a genuinely count-based `WORLD_EVENT_WINDOW=500` boundary test
   constructing the merged event list directly at both the still-in-window and just-evicted
   boundaries — not a 501-tick loop proxy — and the AC4-revised vacancy-detection-delta regression
   scenario).
6. **Parity ledger** — new `TOWN-193` entry in `docs/parity_ledger/town_resource.yaml`, written via
   `tools/parity_ledger_writer.py` (never hand-edited). Re-grepped the file immediately before
   writing and confirmed `TOWN-192` was still the highest id (the plan's cited "next free id" was
   re-verified, not trusted blindly). `TOWN-017` and its neighbors are byte-identical to before.
7. **Doc update** — `docs/audits/D19_domain_phase_inventory.md`'s PP-20 and PP-33 rows updated with a
   short description of the new emission/consumption behavior, per plan.md Step 6. PP-07's row
   (`BlacksmithSystem`) left untouched, since its behavior is unchanged by this ticket.
8. **AC4 revision** — the ticket's own AC4 checkbox text and the "Assumptions / Open Questions"
   section above were updated to record the AC4 revision explicitly (measured
   vacancy-detection-signal delta, not production-throughput delta), matching this session's
   established pattern for documenting mid-plan AC revisions.

**One deviation from the plan's literal Verify text, not from its implementation steps**: plan.md
Step 3's Verify section and `TOWN-017`'s own existing `test_path` both cite
`tests_v2/parity/test_town_resolution_parity.py`, which does not exist anywhere in this worktree's
history (`git log --all -- tests_v2` returns nothing). This predates this ticket and is unrelated to
its changes. Substituted the real `TownResolutionSystem`/blacksmith-exercising test files that do
exist in this repo as the regression guard instead (see Test Summary) — all pass unchanged,
confirming `TOWN-017` crafting stays entity-agnostic. Recorded in the "Assumptions / Open Questions"
section above rather than silently substituted.

## Test Summary

All new and regression-scoped tests pass. Ran with
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest`:

- New tests (11): `tests/unit/economy/test_vacancy.py` (7), plus 4 in
  `tests/integration/economy/test_economic_vacancy_signal.py` — all PASS.
- Plan/test_plan.md's scoped regression command (84 tests):
  `tests/unit/progression/test_lifecycle.py` (34, incl. 3 new),
  `tests/unit/economy/` (7 new + 27 pre-existing across `test_economy_alerts.py`,
  `test_economy_health_monitor.py`, `test_gold_sink.py`),
  `tests/unit/strategic/test_occupation_change_scorer.py` (6),
  `tests/integration/strategic/test_occupation_change_reachability.py` (1),
  `tests/integration/economy/` (4) — all 84 PASS, 0 failures.
- `tests_v2/parity/test_town_resolution_parity.py` (plan-cited path) does not exist in this
  worktree (see Assumptions / Open Questions) — substituted real `TownResolutionSystem`/blacksmith
  regression coverage: `tests/unit/world/test_building_interaction_contract.py`,
  `tests/unit/resource/test_resource_v2_boundary.py` (incl. `test_blacksmith_craft_refactor`),
  `tests/unit/core/test_interaction_recovery.py`, `tests/integration/pipeline/test_strategic_cadence.py`
  (incl. `test_town_resolution_cadence_gating`), `tests/integrity/test_logic_guards.py` — 27 passed,
  2 xfailed (pre-existing, unrelated xfails), 0 failures.
- Total: 122 tests run across all scoped suites, 0 failures.

## Files Changed

- `src/domains/world_emergence/schema.py` — added `WorldEventCategory.PRODUCTION_ROLE_VACATED`.
- `src/economy/vacancy.py` — new file, `EconomicVacancyService.check_and_emit`.
- `src/systems/lifecycle_systems/lifecycle.py` — call site in `resolve_lifecycle`'s
  `if recent_deaths:` aggregate block.
- `src/engine/town_resolution.py` — PP-20 consumer wiring in `TownResolutionSystem.resolve`.
- `tests/unit/economy/test_vacancy.py` — new file, 7 unit tests.
- `tests/unit/progression/test_lifecycle.py` — 3 new tests
  (`test_sole_shopkeeper_death_emits_vacancy_event`,
  `test_non_sole_occupant_death_does_not_emit_vacancy_event`,
  `test_role_and_region_scope_of_sole_occupant_check`) plus new imports (`RegionState`,
  `WorldEventCategory`).
- `tests/integration/economy/__init__.py` — new (package init for new test directory).
- `tests/integration/economy/test_economic_vacancy_signal.py` — new file, 4 integration tests.
- `docs/parity_ledger/town_resource.yaml` — new `TOWN-193` entry (written via
  `tools/parity_ledger_writer.py`).
- `docs/audits/D19_domain_phase_inventory.md` — PP-20 and PP-33 row descriptions updated.
- `tickets/inprogress/TCK-20260903-ECONOMIC-VACANCY-SIGNAL.md` — this file (AC4 revision, status,
  implementation notes, test summary, files changed, completion summary).
- `staging_artifacts/TCK-20260903-ECONOMIC-VACANCY-SIGNAL/plan.md`,
  `staging_artifacts/TCK-20260903-ECONOMIC-VACANCY-SIGNAL/investigation.md`,
  `staging_artifacts/TCK-20260903-ECONOMIC-VACANCY-SIGNAL/test_plan.md` — pre-existing from
  Investigate/Plan phases of this run (already carried `status: historical` frontmatter at the start
  of this Implement run; not modified further by the implementer).

## Completion Summary

Implemented "The Empty Chair" economic-vacancy signal (idea 64) exactly per the reviewed plan: a new
`PRODUCTION_ROLE_VACATED` `WorldEventCategory`, a new stateless `EconomicVacancyService` that detects
a region losing its sole living SHOPKEEPER/WORKER on death (using a `lifecycle.active`-and-
`combat.alive` filter, deliberately stricter than `OccupationChangeGoalScorer`'s
`combat.alive`-only filter, to avoid missing OLD_AGE deaths), called from
`LifecycleSystem.resolve_lifecycle`'s aggregate death block and committed through the real
authoritative apply path (`world_events_add` → `recent_world_events`). `TownResolutionSystem`
(PP-20) reads the signal back one-tick-lagged and increments a per-region metric counter, without
gating `BlacksmithSystem.enforce`'s crafting behavior, preserving `TOWN-017`'s P0 parity entry.
AC4 was formally revised from "production-throughput delta" to "vacancy-detection-signal delta"
during Plan/Review since the design deliberately keeps crafting entity-agnostic; this revision is
recorded above. 11 new unit/integration tests plus 3 new tests colocated in the existing lifecycle
test suite all pass, along with the full test_plan.md regression surface (122 tests total, 0
failures). New `TOWN-193` parity ledger entry added via the sanctioned writer tool; D19 audit
inventory rows updated for PP-20/PP-33.
