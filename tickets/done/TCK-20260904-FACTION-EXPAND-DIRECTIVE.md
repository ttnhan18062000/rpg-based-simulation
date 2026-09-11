---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260904-FACTION-EXPAND-DIRECTIVE
phase: done
date: 2026-09-04
tags: [faction, grand-strategy]
---

# TCK-20260904-FACTION-EXPAND-DIRECTIVE

## Title
National EXPAND_TERRITORY faction directive (ideas 51+52)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Ideas 51 (EXPAND directive) + 52 (population-pressure wiring), consolidated per the epic doc's own confirmation that idea 52 is pure wiring on top of idea 51's directive, not a separate mechanism. Adds a 4th directive kind, EXPAND_TERRITORY, to `FactionDecisionPhase.execute()` (`src/engine/faction_decision.py`), mirroring the existing DEFEND_BORDER/TRADE_ROUTE/COMMISSION_QUEST if/elif pattern, invoked inside `AuthoritativeApplyPipeline.refine()` right after 'blacksmith' and before 'faction_awareness'. Deliberately narrows target resolution to today's state model (faction-less regions via `RegionState.owner_faction_id`) rather than blocking on idea 35 (City ownership, still design-only) or Camp/Nest-as-conquest-target (not yet landed).

## Scope
- Add `EXPAND_TERRITORY` as a new directive-kind constant in `src/engine/faction_constants.py` (alongside DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST) and a new branch in `FactionDecisionPhase.execute()` (`src/engine/faction_decision.py`) that emits it as a transient `FactionDirective`, matching the existing if/elif directive-emission pattern.
- Target resolution for EXPAND_TERRITORY is scoped narrowly to today's state model: target any faction-less region via the existing `RegionState.owner_faction_id` field (Optional[int] = None) — do NOT attempt City-ownership-aware or Camp/Nest-as-conquest-target resolution; state this narrowing explicitly as a deliberate scope decision in `plan.md`, not an oversight.
- Wire the population-pressure/cohort signal (`src/domains/demographics/cohort.py` — `compute_population_density`/`compute_regional_scarcity`) as the real trigger condition feeding `FactionDecisionPhase`'s EXPAND_TERRITORY branch, per idea 52's population-cohort-signal framing.
- Wire the resulting directive through to `CampService` as its final consumption point (population-cohort/pressure signal -> FactionDecisionPhase -> CampService), scoped as real multi-file integration across 3 phases, not a one-line hookup.
- Directives remain transient scratch (FAC-003 parity rule) — EXPAND_TERRITORY must NOT be persisted in `AuthoritativeState`/`StateUpdate`, matching the existing DEFEND_BORDER/TRADE_ROUTE/COMMISSION_QUEST pattern.
- Update `docs/parity_ledger/faction.yaml`'s FAC-003 entry to include the 4th directive kind, and extend its test_path (`tests/unit/domains/faction/test_faction_decision_phase.py`) accordingly.

## Out of Scope
- Camp/Nest as a conquest target for EXPAND_TERRITORY — deferred until `TCK-20260904-CAMP-NEST-CLASSIFICATION` and `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` land.
- City-ownership-aware target resolution (idea 35) — idea 35 remains design-only/not-in-code even after idea 66 landed (idea 66's own closing ticket says idea 35 "retains its own ticket for implementation," which does not yet exist); this ticket must not block on it and must not silently attempt a partial implementation of it.
- The material-possession predicate itself (`TCK-20260904-MATERIAL-POSSESSION-PREDICATE`) — this ticket may consume it if available but does not implement it.

## Acceptance Criteria
- [x] EXPAND_TERRITORY is added as a 4th directive constant and a new branch in `FactionDecisionPhase.execute()`, matching the existing DEFEND_BORDER/TRADE_ROUTE/COMMISSION_QUEST if/elif structure, invoked in the same pipeline position (after 'blacksmith', before 'faction_awareness' in `AuthoritativeApplyPipeline.refine()`).
- [x] Target resolution uses only `RegionState.owner_faction_id` (faction-less regions) — no Camp/Nest or City-ownership-aware logic is added.
- [x] A population-pressure/cohort signal from `src/domains/demographics/cohort.py` gates when EXPAND_TERRITORY is emitted, tested for both trigger and no-trigger cases.
- [x] The directive reaches `CampService` as a real, tested integration point (not a stub), covering the 3-phase path: cohort/pressure signal -> FactionDecisionPhase -> CampService.
- [x] EXPAND_TERRITORY directives are proven NOT persisted in `AuthoritativeState`/`StateUpdate` (transient-scratch test, matching FAC-003's existing verification approach).
- [x] `docs/parity_ledger/faction.yaml`'s FAC-003 entry text/v2_evidence/test_path are updated to include EXPAND_TERRITORY.

## Related Tickets
- TCK-20260904-MATERIAL-POSSESSION-PREDICATE
- TCK-20260904-CAMP-NEST-CLASSIFICATION
- TCK-20260904-CAMPSTATE-PLACE-BRIDGE
- TCK-20260619-E53Ab-DECISION-PHASE

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/brainstorm/rpg_feature_atlas.html (ideas 51, 52)
- docs/parity_ledger/faction.yaml (FAC-003)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/engine/faction_decision.py (FactionDecisionPhase.execute)
- src/engine/faction_constants.py (DEFEND_BORDER, TRADE_ROUTE, COMMISSION_QUEST)
- src/engine/pipeline.py (AuthoritativeApplyPipeline.refine, faction_decision inline block)
- src/domains/demographics/cohort.py (compute_population_density, compute_regional_scarcity)
- src/world/camp.py (CampService, final consumption point)
- src/core/state.py (RegionState.owner_faction_id)
- tests/unit/domains/faction/test_faction_decision_phase.py

## Assumptions / Open Questions
- Recommended sequencing (soft): idea 52's population-pressure-driven expansion should ideally be informed by material possession per idea 52's own card — recommend `TCK-20260904-MATERIAL-POSSESSION-PREDICATE` land before/alongside this ticket, but it is not a hard blocker; this ticket can proceed with population-pressure-only gating if the predicate isn't ready.
- Idea 35 (City ownership) remains design-only after idea 66 landed, and no implementation ticket exists for it yet — this ticket deliberately narrows EXPAND_TERRITORY's target resolution to avoid blocking on it, a scope decision that must be stated explicitly, not discovered as a gap later.
- Idea 52's "pure wiring" framing is confirmed accurate by the atlas's own audit but still spans 3 real phases/files (population signal, FactionDecisionPhase, CampService) — must be scoped and tested as real multi-file integration, not treated as a one-line hookup.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260904-FACTION-EXPAND-DIRECTIVE/plan.md`'s 9 steps
exactly, in the plan's suggested order (1 → 2 → 3 → 6 → 4 → 5 → 7 → 8 → 9). No deviations from
the plan.

- **Step 1**: `EXPAND_TERRITORY = "EXPAND_TERRITORY"` added to `src/engine/faction_constants.py`.
- **Step 2**: `src/engine/faction_decision.py` — imported `EXPAND_TERRITORY` and
  `compute_population_density`/`compute_regional_scarcity` from `src.domains.demographics.cohort`
  at module scope; added a 3rd independent `if fs.territory:` block inside `execute()`'s per-faction
  loop gating on `mean(compute_regional_scarcity(rid, state) for rid in fs.territory) > 0.7`, with
  `compute_population_density` folded into `priority` scaling only (`min(1.0, mean_scarcity +
  mean_density * 0.1)`), never the gate; added the new `_resolve_expand_territory_target(state, fs)`
  staticmethod that deterministically picks the lowest-id region with `owner_faction_id is None`
  and not already in `fs.territory`, via `sorted()` over a generator (never raw dict iteration).
  Updated the class docstring's "Decision rules" list and the `FactionDirective.directive_kind`
  inline comment to list the 4th value (small, in-spirit addition beyond the plan's literal text,
  since the plan's own Step 8 already documents this exact string elsewhere).
- **Step 3**: 9 new tests added to `tests/unit/domains/faction/test_faction_decision_phase.py`
  (test_plan items 1-6 plus 3 of the 5 required anti-drift guards: mutual-exclusivity
  non-interference, no-Camp/Nest/City-ownership scope-creep, recipe_materials non-hard-gate). The
  determinism guard (test_plan item 4) and signature-backward-compatibility guard are covered by
  tests already in this set / in the CampService and world_dynamics test files respectively.
- **Step 6**: `src/world/camp.py` — added `from dataclasses import replace`, a new
  `EXPAND_TERRITORY_MATURITY_BOOST = 1.0` class constant, a new trailing-optional
  `faction_directives: list | None = None` param on `process_camps()`, and a new "1b" branch
  (after Maturity Evolution, before Camp-based Spawning) that additively boosts a matching camp's
  `maturity_delta` via `dataclasses.replace()` on the existing `camp_updates[c_id]` entry — never a
  new mutation path. 3 new tests added to `tests/unit/world/test_camp_lifecycle.py`.
- **Step 4**: `src/engine/world_dynamics.py` — added the same trailing-optional
  `faction_directives` param to `resolve_dynamics()` and threaded it into the existing
  `CampService.process_camps(...)` call site. 1 new test added to `tests/unit/world/test_world_dynamics.py`.
- **Step 5**: `src/engine/pipeline.py:343` — threaded the pre-existing `faction_directives` local
  (computed at line 230) into the `resolve_dynamics(...)` call as `faction_directives=faction_directives`.
- **Step 7**: `docs/parity_ledger/faction.yaml` FAC-003 updated via
  `tools/parity_ledger_writer.py::write_entry` (not hand-edited) — `text`/`v2_evidence` now name all
  4 directive kinds and the CampService consumption path; `status`/`priority`/`test_path` unchanged
  per plan. Confirmed via `git diff --stat` that only FAC-003's fields changed (7 insertions, 2
  deletions) — no other entry in the shard was touched by the writer's full-file rewrite.
- **Step 8**: `docs/systems/faction_contract.md` — added `EXPAND_TERRITORY` to the
  `FactionDirective Schema` code comment, the "Directive Kinds" table (with a new note on its
  independence from the other three and its target-resolution scope), and the "Pipeline Position"
  diagram (noting the new `world_dynamics`-phase threading into `CampService`).
- **Step 9**: `docs/world/raid_boss_camp_contract.md` — added a new "Faction EXPAND_TERRITORY
  consumption" subsection under "Camp — `camp.py`", documenting the new branch, its interaction
  with the pre-existing raid-trigger overwrite, and its current real-content-inert status.

Real-content reachability (disclosed per plan Anti-Drift Notes): `CampService`'s EXPAND_TERRITORY
consumption branch is real, correct, and covered by direct unit tests, but has **zero observable
effect in any currently-compiled real world** — `state.camps` is `{}` for every real world today
(no content sets `creature_kind`), identical in kind to `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`'s
own disclosed "wired but inert" outcome. This is the accepted, correct scope for this ticket, not
a shortfall.

### Document-Update phase — independent verification and one disclosed scope-extending doc edit

Independently re-verified (per the doc-updater phase's own instructions) that `docs/parity_ledger/faction.yaml`
FAC-003, `docs/systems/faction_contract.md`, and `docs/world/raid_boss_camp_contract.md` (the 3 docs
flagged by `investigation.md`'s "Docs Requiring Update" section) are accurate and in exact semantic
parity with the shipped diff — cross-checked line-by-line against `git diff` for
`src/engine/faction_constants.py`, `src/engine/faction_decision.py`, `src/engine/world_dynamics.py`,
`src/engine/pipeline.py`, and `src/world/camp.py`, plus a live run of
`tests/unit/domains/faction/test_faction_decision_phase.py tests/unit/world/test_camp_lifecycle.py
tests/unit/world/test_world_dynamics.py` (50 passed). No corrections were needed to any of the 3
flagged docs.

Per the process note requiring disclosure of any doc edit beyond the injected flagged set: found and
fixed one additional stale doc not listed in `investigation.md`'s "Docs Requiring Update" —
`docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`. This is the epic doc's own Scope item 5
(ideas 51+52), which had no "Status update, 2026-09-04" annotation even though this ticket is the
5th of the epic's 8 scope items to ship a child ticket and the batch's own established pattern (5
prior sibling tickets in this batch — CAMP-NEST-CLASSIFICATION, CAMPSTATE-PLACE-BRIDGE,
LAIR-ENTITY-ANCHOR, SETTLEMENT-CULTURE-READ, MATERIAL-POSSESSION-PREDICATE) already added this
annotation to their own scope items on close. Added a status-update paragraph to item 5 summarizing
what shipped (gate condition, target-resolution scope, the 3-phase `CampService` threading, the
disclosed content-authoring-gap inertness) and explicitly naming the real, still-unticketed
follow-up work (`CampService` content-authoring bridge for Camp/Nest, a recipe-catalog namespace
bridge for item 4's `RecipeRegistry` naming collision, ~44 stale parity test-path citations) plus the
one already-filed follow-up ticket (`TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`, from item 3) — and
explicitly stated the epic is not complete (items 6, 7, 8 remain fully unticketed; item 1's
world-generation content-authoring half remains open). No other section of the epic doc was touched;
its frontmatter `status: active` is left unchanged since the epic genuinely is not done.

## Test Summary
13 new tests added across 3 files, all passing:
- `tests/unit/domains/faction/test_faction_decision_phase.py`: 9 new tests (11 pre-existing tests
  unmodified and still passing — 20 total in file).
- `tests/unit/world/test_camp_lifecycle.py`: 3 new tests (16 pre-existing tests unmodified and
  still passing — 19 total in file).
- `tests/unit/world/test_world_dynamics.py`: 1 new test (9 pre-existing tests unmodified and still
  passing — 10 total in file).

Scoped regression run (test_plan.md's full specified surface), all green, 0 failures:
```
pytest tests/unit/domains/faction/ tests/unit/world/test_demographics.py tests/unit/world/test_world_dynamics.py \
  tests/unit/world/test_camp_lifecycle.py tests/unit/world/test_natural_creature_reproduction.py \
  tests/integration/scenarios/test_demographics.py -q
=> 273 passed

pytest tests/unit/world/test_sovereignty_events.py tests/unit/world/test_creature_territory_lifecycle.py \
  tests/unit/world/test_reproduction_humanoid_cadence.py tests/integration/world/test_phase9_stability.py \
  tests/integration/scenarios/test_faction_campaign.py -q
=> 35 passed
```
Full test suite was not run (per CLAUDE.md scoping rule); the Test phase will run its own broader
pass.

## Files Changed
- `src/engine/faction_constants.py` — added `EXPAND_TERRITORY` constant.
- `src/engine/faction_decision.py` — new imports, new EXPAND_TERRITORY branch + gate helper,
  docstring/comment updates.
- `src/world/camp.py` — new `faction_directives` param, `EXPAND_TERRITORY_MATURITY_BOOST`
  constant, new consumption branch, new `dataclasses.replace` import.
- `src/engine/world_dynamics.py` — new `faction_directives` param on `resolve_dynamics()`, threaded
  into the `CampService.process_camps()` call site.
- `src/engine/pipeline.py` — threaded `faction_directives` into the `world_dynamics` phase call.
- `tests/unit/domains/faction/test_faction_decision_phase.py` — 9 new tests.
- `tests/unit/world/test_camp_lifecycle.py` — 3 new tests.
- `tests/unit/world/test_world_dynamics.py` — 1 new test.
- `docs/parity_ledger/faction.yaml` — FAC-003 entry updated (via `tools/parity_ledger_writer.py`).
- `docs/systems/faction_contract.md` — EXPAND_TERRITORY documented (schema, directive-kinds table,
  pipeline-position diagram).
- `docs/world/raid_boss_camp_contract.md` — new "Faction EXPAND_TERRITORY consumption" subsection.
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` — **added during the Document-Update
  phase, not flagged by `investigation.md`** — added a "Status update, 2026-09-04" annotation to
  Scope item 5 (ideas 51+52), matching the pattern already established by the 5 prior sibling
  tickets in this batch; disclosed per the Document-Update phase note above.
- `tickets/inprogress/TCK-20260904-FACTION-EXPAND-DIRECTIVE.md` — this file (status, AC checkboxes,
  Implementation Notes, Test Summary, Files Changed, Completion Summary).

Note: `staging_artifacts/TCK-20260904-FACTION-EXPAND-DIRECTIVE/plan.md`, `investigation.md`, and
`test_plan.md` already existed as APPROVED artifacts from prior planning rounds (2 rounds of
NEEDS_CHANGES on call-site enumeration, since fixed) before this implementation run started — they
were read but not rewritten during this run, so they are not listed as changed files here.

## Completion Summary
Added the 4th faction directive kind, `EXPAND_TERRITORY`, gated on mean regional scarcity (>0.7)
over a faction's territory, with population density folded into priority scaling only. Target
resolution deterministically picks the lowest-id faction-less region via `RegionState.owner_faction_id`
(no Camp/Nest or City-ownership logic). The directive is threaded, same-tick, from
`FactionDecisionPhase` through `WorldDynamicsSystem.resolve_dynamics()` into
`CampService.process_camps()`, where a matching directive additively boosts a camp's maturity growth
— both new parameters are backward-compatible trailing optionals, verified against all 16
`resolve_dynamics()` and 17 `process_camps()` real call sites. Directives remain transient scratch
per FAC-003 (never persisted). The CampService consumption path is real and tested but currently has
no observable effect in any real compiled world, since no world content sets `creature_kind` yet —
disclosed explicitly, not silently assumed. This closes the 6th and final ticket in the
m4-place-material-expansion batch.
