---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST
date: 2026-09-06
---

# Investigation: TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST

## Current Behavior
- `tools/simq_long_run_observation.py:86`: `--ticks` default is `5000` (confirmed unchanged).
- `src/core/calendar.py:13`: `TICKS_PER_FANTASY_YEAR = 288,000` (confirmed).
- `src/domains/demographics/cohort.py:19-20`: `YOUNG_ADULT_BOUNDARY_TICKS = 12 * TICKS_PER_FANTASY_YEAR`
  = 3,456,000; `ADULT_ELDER_BOUNDARY_TICKS = 60 * TICKS_PER_FANTASY_YEAR` = 17,280,000 (confirmed).
  `compute_elder_attribute_update()` (cohort.py:89) applies elder-tier attribute modifiers once
  `get_age_bracket(age_ticks) == "elder"`.
- `tools/simq_long_run_observation.py`'s `DEFAULT_WORLDS` list (`wilderness_survival`,
  `resource_dense_basin`, `crowded_frontier`, `hero_guild_routing`, `dungeon_crawl`,
  `urban_political`) — none of these is the `frontier_village_core`/`hero_adventurers` combination
  the ticket text cites; that combination is a `world_module` composition named in the M9 epic doc's
  own item-4 scoping prose (`rpg_m9_corpus_test_coverage_epic.md:145,182-183`), not an existing
  registered `simq_long_run_observation.py` world or a corpus-registry entry — no such world exists
  today under that exact name.

## Correction 1 — no duplicate ownership, confirmed
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s "Temporal axis" section (line 367) and its
"Known open items" section (line 272-279) both name this exact finding — "the long-run observation
tool's default 5000-tick run is now confirmed far more inadequate than originally described" — as an
open, unowned gap, explicitly pointing at M9 as the milestone that should close it ("M9 should add
daily/seasonal/annual/lifespan/multi-generation scenario horizons, not rely on one fixed tick
count"). No dedicated fix ticket exists elsewhere. This M9 child ticket is the correct, non-duplicate
owner.

## Correction 2 — the underlying mechanics are already well-tested at the real boundaries; the real
## gap is narrower than "no run has ever observed these transitions"
Confirmed via direct read, three real, already-passing test files already exercise all 3 age-tier
mechanics through the real production `LifecycleSystem.resolve_lifecycle()` (or the relevant pure
function) at the REAL fantasy-year-scaled boundary values (3,456,000 / 17,280,000), by hand-setting
`age_ticks` rather than running an emergent multi-million-tick simulation:
- `tests/unit/progression/test_lifecycle.py::test_life_stage_flips_at_age_boundary` and
  `test_life_stage_transition_is_monotonic_forward_only` — `identity.life_stage` flips CHILD->ADULT
  at exactly 3,456,000 and ADULT->ELDER at exactly 17,280,000, through the real
  `LifecycleSystem.resolve_lifecycle()` call.
- `tests/unit/strategic/test_coming_of_age_archetype_choice.py` — the Coming-of-Age roll (idea 34)
  fires through the same real `resolve_lifecycle()` path at `age_ticks=3456000`.
- `tests/unit/world/test_demographics.py` — `compute_elder_attribute_update()` coverage.

So the claim "no calibration run using this tool's default has ever been capable of observing any
age-bracket transition at all" is true specifically of `simq_long_run_observation.py`'s own
long-run-Kernel-driven observation tier — it is NOT true of this codebase's test coverage in
general. This is a real, disclosed correction to the ticket's own framing, not a silent scope
narrowing: the mechanics are correct and already unit-tested; what's missing is a SimQ
corpus-tier exercise of them (the M9 epic's own actual question — "does a real SimQ corpus world
exist to exercise this idea" — distinct from "is there a unit test for the pure function").

## Correction 3 — `archetype_locked` does not exist; idea 34's real observable is a one-shot `role_set`
Confirmed via grep: zero hits for `archetype_locked` anywhere in `src/`, `tests/`, or either the M9
epic doc or the design-merit-scorecard's own idea-34 entry ("Coming of Age"). The real mechanism
(`tickets/done/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE.md`, `src/ai/coming_of_age.py`):
`choose_archetype()` is invoked exactly once inside `LifecycleSystem.resolve_lifecycle()` at the
CHILD->ADULT `life_stage` transition, producing one `IdentityUpdate`/`role_set` (only for
`entity.identity.role == EntityRole.CITIZEN`). The correct assertable proxy is: `identity.role`
changes to a real occupation via `role_set` exactly once at the transition tick, and does not fire
again on a later re-check. The ticket's own "archetype_locked flips false->true" text has no basis
in real code — corrected here rather than fabricating a field.

## Correction 4 — the `get_age_bracket()`/`LifeStage` overlap question is already resolved
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (line 774-782): `TCK-20260824-LIFE-STAGE-TRANSITIONS`
(DONE) already settled this — `get_age_bracket()` (cohort-level aggregate demographics,
`cohort.py`) and `LifeStage`/`LifeStageService.get_stage_for_age()` (per-entity strategic cognition,
`src/ai/life_stage.py`) are two deliberately separate vocabularies for two genuinely different
consumers, not merged. Verified directly that `life_stage.py`'s own duplicated literals were
correctly updated by the fantasy-year migration (both files now use the identical 3,456,000/
17,280,000 boundaries) — `tests/unit/strategic/test_life_stage_transitions.py::
test_get_stage_for_age_matches_get_age_bracket_numeric_boundaries` already regression-guards this
alignment. No new code needed; this ticket's own AC3 is satisfied by citing this existing,
already-verified resolution.

## Practicality of a real 17,280,000-tick corpus run
Not practical within this project's normal test/calibration budget. Existing calibration
convention runs top out at hundreds to a few thousand ticks (`tests/simulation_quality/`'s own
profiles; `simq_long_run_observation.py`'s own doc-string calls itself an "additive, periodic
observation tier," not a fast-tier fixture, at a 5000-tick scale). A real, emergent 17.28M-tick
Kernel run is roughly 3-4 orders of magnitude beyond any existing test's scale and would make any
test suite invocation impractically slow. Per this ticket's own Assumptions section, this is
flagged honestly rather than forced: the SimQ corpus-tier proof below uses this codebase's own
established "deterministic hand-scripted proof" precedent (`tests/simulation_quality/
test_grade_regression.py::test_information_intent_execution_fires_through_kernel_tick_once`, M7's
`route_new_query_isolated_calibration.py`, and this same M9 batch's ticket-1 precedent) — a small,
multi-entity, hand-seeded `AuthoritativeState` with entities placed at/near the real thresholds,
run through a handful of real `Kernel.tick_once()` calls, rather than an emergent multi-million-tick
run.

## Docs Requiring Update
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`: mark the 5000-tick finding (line ~272-279,
  ~367) as addressed by this ticket, with the 4 corrections above noted.
- No `docs/mechanics/`/`docs/engine/` chapter changes — this ticket adds tooling + tests only, no
  law/formula change.

## Parity Ledger Overlap
- `docs/parity_ledger/world_dynamics.yaml::WORLD-DEMO-003` (get_age_bracket/elder thresholds) and
  `docs/parity_ledger/combat_movement.yaml::COMB-313` (LifeStage/get_age_bracket duplication
  decision) already document the underlying mechanics correctly — unaffected by this ticket, which
  adds no production behavior change to either.
- No new parity entry needed for the tool default/guard change (`tools/` is not `src/`, and the
  Definition of Done's parity-update trigger is `src/` behavior changes) or for the new corpus test
  (test-only, no behavior change).

## Prior Work
- `tests/unit/progression/test_lifecycle.py`, `tests/unit/strategic/test_life_stage_transitions.py`,
  `tests/unit/strategic/test_coming_of_age_archetype_choice.py`, `tests/unit/world/
  test_demographics.py` — real, passing, boundary-accurate precedent for all 3 mechanics.
- `tests/simulation_quality/test_grade_regression.py::
  test_information_intent_execution_fires_through_kernel_tick_once` — the deterministic
  hand-scripted-scenario-through-real-Kernel precedent this ticket's own corpus proof follows.

## Risks and Open Questions
None outstanding.

## Anti-Drift Hazards
- Do not raise `simq_long_run_observation.py`'s default to anything near 17,280,000 — this would
  make every ordinary invocation of the tool impractically slow; a guard/warning is the correct fix,
  not a huge default bump.
- Do not invent an `archetype_locked` field — assert on `identity.role`/`role_set` instead, matching
  the real shipped mechanism.
- Do not duplicate the existing pure-function unit tests (test_lifecycle.py etc.) — this ticket's own
  new test's value is specifically the SimQ corpus-tier framing (a multi-entity scenario, not a
  single hand-built entity), not re-proving what's already proven.
