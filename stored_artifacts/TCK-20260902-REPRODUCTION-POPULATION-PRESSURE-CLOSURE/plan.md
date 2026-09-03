---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE
artifact_type: plan
tags: [lifecycle, world]
---

# Implementation Plan — TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE

## Summary

Close the individual-birth → aggregate-cohort feedback loop by adding a new **additive** delta
field, `WorldUpdate.population_young_births_delta`, that each of the two eligible reproduction
paths (natural-creature, humanoid) sets to `+1` per birth inside its own already-flag-gated
branch, and that the authoritative apply path layers on top of the region's resolved `young`
cohort bracket (creating the bracket if absent) — never a whole-dict resync. This sits alongside,
not inside, `WorldUpdate.population_cohorts_set` (which stays whole-dict-replace, used only by
`DemographicCycleService`'s own 200-tick cycle and by migration), so a same-tick collision between
the aggregate cycle's own recompute and this ticket's nudge cannot clobber either signal — the
`_set` field wins as a base and the `_delta` field adds on top of it, both correctly summed across
multiple births in one call via `WorldUpdate.merge()`. Two pre-existing bugs are fixed as
prerequisite plumbing: (1) `WorldDynamicsSystem.resolve_dynamics()` silently drops
`camp_state_update.world_updates`/`calamity_update.world_updates` today (confirmed at
`src/engine/world_dynamics.py:174-182` — only `entities_add`/`camp_updates`/`maturity_set`/
`last_calamity_tick_set` are cherry-picked from those two services), which is fixed by folding
them in via the same per-region merge idiom the file already uses for `ThreatService` at lines
149-152; (2) the missing-`young`-bracket case is resolved by materializing a fresh
`PopulationCohort(bracket="young", count=<delta>)` with dataclass defaults, mirroring the
migration code's own "new bracket in target" precedent (`src/domains/demographics/cohort.py:288-290`).
The magical/demonic path is confirmed **excluded** from the nudge, per its own already-shipped,
already-verified `WORLD-121` rationale ("a calamity-driven spawn is a world-threat escalation
event, not a settlement/camp demographic signal" — `docs/parity_ledger/world_dynamics.yaml:1737-1741`):
since that path deliberately never *reads* the population-pressure signal either, symmetry argues
it should not *write* it. `WORLD-120`/`WORLD-122`'s now-false "never writes population_cohorts"
claims are corrected; `WORLD-121`'s claim remains substantively true but gains an explicit
addendum recording that this ticket evaluated and confirmed the exclusion, rather than leaving it
an implicit omission.

## Steps

### Step 1 — Add the additive nudge field to `WorldUpdate`
**Files:** `src/core/updates.py`
**Change:** Add `population_young_births_delta: int = 0` to the `WorldUpdate` dataclass, next to
the existing `population_cohorts_set: Optional[Dict[str, Any]] = None` field (currently at
`src/core/updates.py:827`, confirmed by direct read). In `WorldUpdate.merge()` (currently at
`src/core/updates.py:834-859`, confirmed by direct read), add
`population_young_births_delta=self.population_young_births_delta + other.population_young_births_delta`
to the `replace(...)` call — the exact same additive-delta pattern already used in this same
dataclass for `trauma_delta`, `retaliation_pressure_delta`, `influence_delta`,
`service_availability_delta`, and `siege_progress_delta` (all summed at merge time, confirmed at
`src/core/updates.py:843,845,847,855,858`). This is a genuinely new field, not a repurposing of
`population_cohorts_set` — `population_cohorts_set` merge semantics ("prefer other, non-None",
confirmed at `src/core/updates.py:854`) are left completely untouched, so `DemographicCycleService`'s
own 200-tick whole-dict rebuild and `_check_migration`'s emigration rewrite keep working exactly
as before.
**Other writers to this dataclass/field considered:** `WorldUpdate.population_cohorts_set` is
written by `DemographicCycleService.process_demographics()` and `_check_migration()`
(`src/domains/demographics/cohort.py`), and by `TransformationService`/`ThreatService`/
`CalamityPressurePropagator` for their own unrelated fields on the same class. None of these
writers touch `population_young_births_delta` — it is a brand-new field only the three
reproduction-path steps below will ever set, so there is no existing writer to reconcile against.
**Do NOT touch:** `population_cohorts_set`'s type, default, or merge semantics; any other field on
`WorldUpdate`.
**Verify:** No existing test regresses (`tests/unit/world/test_world_dynamics.py`,
`tests/unit/world/test_demographics.py`). This field's additive behavior is exercised end-to-end
by New Test `test_two_simultaneous_births_same_region_same_call_both_nudge` (Step 7) and
`test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update` (Step 10).

### Step 2 — Fix the dropped `world_updates` fold-in bug in `WorldDynamicsSystem.resolve_dynamics()`
**Files:** `src/engine/world_dynamics.py`
**Change:** At `src/engine/world_dynamics.py:174-182` (confirmed by direct read), the
`update = update.replace(...)` call cherry-picks only `maturity_set`, `last_calamity_tick_set`,
`entities_add` (correctly includes both `camp_state_update.entities_add` and
`calamity_update.entities_add`), `nodes_add`, `camp_updates`, `next_node_id_set`,
`next_entity_id_set` — it never reads `camp_state_update.world_updates` or
`calamity_update.world_updates`. Fix by folding both into `update.world_updates` using the exact
per-region merge-or-set idiom this same file already uses for `ThreatService` at
`src/engine/world_dynamics.py:149-152` (`if r_id in update.world_updates: update.world_updates[r_id]
= update.world_updates[r_id].merge(w_upd) else: update.world_updates[r_id] = w_upd`), applied once
for each of `camp_state_update.world_updates.items()` and `calamity_update.world_updates.items()`.
Confirmed safe to mutate the dict in place either before or after the `update.replace(...)` call
on line 174: `StateUpdate.replace()` is `dataclasses.replace(self, **kwargs)`
(`src/core/updates.py:1219-1220`, confirmed by direct read), which does not copy the
`world_updates` dict object when it is not among the passed kwargs — the new `update` instance
shares the same dict reference, so in-place mutation is safe on either side of the reassignment.
Do not route this through `.merge()` on the whole `camp_state_update`/`calamity_update`
`StateUpdate` objects (unlike `demo_update`/`seasonal_update`/`territory_update`/`repro_update` at
lines 184-207) — that would double-count `entities_add`/`camp_updates`/`maturity_set`/
`last_calamity_tick_set`, which the explicit `update.replace(...)` call already folds in from
those same two objects.
**Other writers to `update.world_updates` in this function considered:** `ThreatService` (lines
145-152, same merge-or-set idiom, unaffected), `demo_update`/`seasonal_update`/`territory_update`/
`repro_update` (lines 184-207, each folded in via `StateUpdate.merge()`, which already correctly
per-region-merges `world_updates` via `WorldUpdate.merge()` at `src/core/updates.py:1091-1092`,
unaffected by this change since `camp_state_update`/`calamity_update` are handled separately, not
via `.merge()`), and the `TransformationService` region-kind-shift block at lines 209-216 (writes
into a `refined_world_updates` copy taken *after* this fix point, so it correctly sees the folded-in
values).
**Do NOT touch:** the existing `ThreatService` merge block (145-152); the `entities_add`/
`camp_updates`/`maturity_set`/`last_calamity_tick_set` handling already in the `update.replace(...)`
call; the `demo_update`/`seasonal_update`/`territory_update`/`repro_update` merge sequence at
184-207; `TransformationService`'s block at 209-216.
**Verify:** `test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update` (New Test,
Step 10) plus full regression pass of `tests/unit/world/test_camp_lifecycle.py`,
`tests/unit/world/test_calamity_raid.py`, `tests/unit/world/test_calamity_pressure_propagator.py`,
`tests/unit/world/test_creature_territory_lifecycle.py`, `tests/unit/world/test_world_dynamics.py`,
`tests/unit/world/test_spawn_cadence.py`, `tests/unit/core/test_system_cadence.py` (all listed in
test_plan.md's Regression Surface as sharing this merge sequence).

### Step 3 — Apply the delta in the authoritative apply path
**Files:** `src/engine/apply_plan.py`
**Change:** At `src/engine/apply_plan.py:124` (confirmed by direct read: `pop_cohorts =
r_upd.population_cohorts_set if r_upd.population_cohorts_set is not None else
reg.population_cohorts`), after this line resolves the base cohort dict (whichever of
`DemographicCycleService`'s fresh set or the prior region state it is), layer
`r_upd.population_young_births_delta` on top by incrementing (or creating) the `young` bracket:
if `r_upd.population_young_births_delta` is non-zero, build a new dict
`pop_cohorts = {**pop_cohorts}`, then if `"young"` is present, replace it with
`dataclasses.replace(existing, count=existing.count + delta)` (reusing the already-imported
`replace` from `src.engine.apply` at line 112); if absent, insert
`PopulationCohort(bracket="young", count=delta)` (dataclass defaults for `birth_rate`/
`mortality_rate`/`migration_threshold`, imported from `src.domains.demographics.cohort` —
confirmed field shape and defaults at `src/domains/demographics/cohort.py:39-43`). This resolves
Risk #3 (a region with `population_cohorts == {}` legitimately materializes a fresh `young`
bracket on its first birth rather than silently dropping the signal, consistent with idea 38's
"coarse nudge closes the loop" framing — dropping it would leave the gap this ticket exists to
close). This is applied strictly *after* `pop_cohorts` is resolved from `population_cohorts_set`
(the whole-dict-replace field), so a same-tick collision between `DemographicCycleService`'s own
200-tick rebuild (which sets `population_cohorts_set`) and a reproduction path's nudge (which only
ever sets `population_young_births_delta`, never `population_cohorts_set`) cannot clobber either —
the aggregate cycle's fresh dict becomes the base, and the nudge's delta is added on top of it in
the same apply pass. This resolves Risk #2.
**Other writers to `pop_cohorts`/`new_regions[r_id]` in this function considered:** this is the
single site in `apply_plan.py` that resolves `population_cohorts` for a region (confirmed: only
one `population_cohorts` reference in the file, at line 124/139); no other line in `apply_plan.py`
touches it. The surrounding `replace(reg, ...)` call at 136-140 already threads `pop_cohorts`
through alongside every other resolved field for that region — extending what `pop_cohorts` itself
evaluates to does not change that call's shape.
**Do NOT touch:** `hazard_level_set`/`suppression_set`/`calamity_intensity_set`/`trauma_score_set`/
etc. resolution logic on the surrounding lines (113-123); the `siege_state`/`service_availability`
resolution (125-135); the `"regions" in cols` gating (line 79, 108) — `population_young_births_delta`
being non-zero on a `WorldUpdate` already implies `update.world_updates` is non-empty, which already
triggers `cols.add("regions")`, so no new gating condition is needed.
**Verify:** New Test `test_birth_in_region_missing_young_cohort` and
`test_birth_nudge_does_not_recompute_other_brackets` (Step 6); exercised transitively by every
Step 4/5 test.

### Step 4 — Wire the nudge into the natural-creature path
**Files:** `src/world/camp.py`
**Change:** In `CampService.process_camps()`, block "4. Natural-Creature Reproduction"
(`src/world/camp.py:85-104`, confirmed by direct read), after a successful
`generator.spawn_natural_creature_offspring(...)` call (line 97-103) and only when `region is not
None` (the region can legitimately be `None` per `LegalityServiceV2.get_region_for_position`
returning nothing — in that case there is no region to attribute the nudge to, so it is skipped,
not defaulted to some other region), accumulate a `WorldUpdate(region_id=region.id,
population_young_births_delta=1)` into a new local `world_updates: Dict[str, WorldUpdate] = {}`
dict declared at the top of `process_camps()` alongside `camp_updates`/`entities_add` (line 26-27).
Because a single `process_camps()` call iterates multiple camps and more than one eligible camp
can land in the same region on the same tick, use the same merge-or-set idiom as Step 2
(`if region.id in world_updates: world_updates[region.id] = world_updates[region.id].merge(nudge)
else: world_updates[region.id] = nudge`) — this is required, not optional, because
`population_young_births_delta` only sums correctly through `WorldUpdate.merge()`; a naive
`world_updates[region.id] = nudge` overwrite would silently drop the first camp's nudge. Change
the return statement at line 106 from `StateUpdate(camp_updates=camp_updates,
entities_add=entities_add)` to also pass `world_updates=world_updates`.
**Other writers to this function's return value considered:** `resolve_camp_clearing()` (lines
108-130) is a separate static method on the same class with its own independent `StateUpdate`
return — unaffected. `process_camps()` itself already builds `camp_updates`/`entities_add`
incrementally across the same camp loop (lines 26-27, 43, 62, 79-83) — the new `world_updates`
dict follows the identical accumulate-then-return shape, so it composes with the existing pattern
rather than introducing a new one.
**Do NOT touch:** blocks 1-3 (maturity evolution, camp-based spawning, raid trigger, lines 30-83);
`resolve_camp_clearing()`; the eligibility gate itself (lines 89-95, already reuses
`compute_regional_scarcity`/`migration_threshold` verbatim — this step only adds what happens
*after* a birth is decided, never touches eligibility).
**Verify:** New Test `test_natural_creature_birth_nudges_young_cohort_by_one` and
`test_two_simultaneous_births_same_region_same_call_both_nudge` (both in
`tests/unit/world/test_natural_creature_reproduction.py`).

### Step 5 — Wire the nudge into the humanoid path
**Files:** `src/world/reproduction_humanoid.py`
**Change:** In `HumanoidReproductionService.process_reproduction()`, after `region` is resolved at
line 67 and the eligibility gate at lines 68-72 (confirmed by direct read), and only when `region
is not None` (same skip-when-unregioned rule as Step 4 — `SpatialQueryService.get_region_at` can
also return `None`), add `world_updates={region.id: WorldUpdate(region_id=region.id,
population_young_births_delta=1)}` to the `pair_update` `StateUpdate` constructed at lines 94-101.
No new accumulation logic is needed here (unlike Step 4): the function already accumulates
per-pair results via `result = result.merge(pair_update).merge(bond_update)` inside the `for a in
candidates:` loop (line 108, confirmed by direct read) — since `StateUpdate.merge()` →
`merge_many()` already per-region-merges `world_updates` using `WorldUpdate.merge()`
(`src/core/updates.py:1091-1092`, confirmed by direct read), and `population_young_births_delta`
now sums additively (Step 1), multiple pairs birthing in the same region in the same call
correctly accumulate through the existing `.merge()` call with zero new code beyond adding the
`world_updates=` kwarg. Import `WorldUpdate` from `src.core.updates` (already imported as
`StateUpdate` at line 9 — add `WorldUpdate` to that import).
**Other writers to `pair_update`/`result` considered:** `bond_update` (lines 102-107) writes only
`entity_updates`, no overlap with `world_updates`. No other writer touches `result` in this
function.
**Do NOT touch:** the eligibility gate (68-72); the cooldown/bond-write logic (94-107); the
candidate-pairing loop structure (35-65).
**Verify:** New Test `test_humanoid_birth_nudges_young_cohort_by_one`
(`tests/unit/world/test_reproduction_humanoid_cadence.py`).

### Step 6 — Confirm and document magical/demonic exclusion
**Files:** `src/world/calamity.py`
**Change:** No behavioral code change to `CalamityService.process_world_dynamics()`'s "3.
Magical/Demonic Reproduction" branch (`src/world/calamity.py:60-69`). Resolve investigation.md
Risk #4 (open question: does this path participate) as **excluded**, with evidence: the
already-shipped `WORLD-121` parity entry states this path "does not reference
`compute_regional_scarcity()`/`migration_threshold`/`PopulationCohort` at all... a calamity-driven
spawn is a world-threat escalation event, not a settlement/camp demographic signal"
(`docs/parity_ledger/world_dynamics.yaml:1737-1741`, confirmed by direct read). Since this path
already deliberately never *reads* the population-pressure signal, symmetry with its own shipped
rationale argues it should not *write* to it either — the exclusion is a confirmation of existing
design intent, not a new judgment call. Add a one-line comment directly above the "3.
Magical/Demonic Reproduction" branch citing this ticket and the rationale, so the exclusion reads
as an evaluated decision in the code, not a silent gap.
**Other writers considered:** N/A — no code path is added or changed here; this step is a
documented no-op plus a regression-guard test.
**Do NOT touch:** the branch's spawn logic itself (lines 60-69); the `should_spawn`/
`target_region` trigger it reuses (lines 34-58).
**Verify:** New Test `test_magical_demonic_birth_nudge_decision`
(`tests/unit/world/test_calamity_magical_demonic_reproduction.py`) — asserts the returned
`StateUpdate.world_updates == {}` after a successful magical/demonic spawn, explicitly, so the
exclusion is a hard regression gate rather than an absence of coverage.

### Step 7 — Retarget the three existing "does not write population_cohorts" guard tests
**Files:** `tests/unit/world/test_natural_creature_reproduction.py`,
`tests/unit/world/test_calamity_magical_demonic_reproduction.py`,
`tests/unit/world/test_reproduction_humanoid_cadence.py`
**Change:** Per test_plan.md's Anti-Drift Test Guards, do not delete
`test_natural_creature_reproduction_does_not_write_population_cohorts` (line 140) or
`test_no_population_cohorts_write_in_humanoid_reproduction_path` (line 99) — rewrite them in place
to assert the new additive `+1` behavior (New Tests 1/2 from Step 4/5 above satisfy this; these
can be the same test renamed, or the old test renamed to assert `+1` directly — keep same file
location so the diff is easy to review). `test_magical_demonic_reproduction_does_not_write_population_cohorts`
(line 98) is retained largely as-is per Step 6 (still asserts `world_updates == {}`), just
re-anchored to the explicit-exclusion rationale rather than a "not implemented yet" placeholder.
Also add the additive assertions from test_plan.md's New Tests 4/5/6
(`test_two_simultaneous_births_same_region_same_call_both_nudge`,
`test_birth_nudge_does_not_recompute_other_brackets`, `test_birth_in_region_missing_young_cohort`)
to `tests/unit/world/test_natural_creature_reproduction.py` (natural-creature is the path where
same-call multi-birth accumulation is exercised, per Step 4). Do not touch
`test_flag_off_by_default_does_not_spawn_*` tests beyond adding a `world_updates == {}` assertion
if not already covered, per test_plan.md's Anti-Drift Test Guards.
**Do NOT touch:** `test_natural_creature_reproduction_does_not_reference_genetics`,
`test_magical_demonic_reproduction_does_not_reference_genetics`, the humanoid path's
no-marriage-contract source-inspection guard — all must pass unmodified.
**Verify:** the retargeted/new tests themselves; full pass of all three files.

### Step 8 — Add the pressure-model mirrored-births test (AC#3)
**Files:** `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py`
**Change:** Add `test_repeated_births_increase_population_density_signal`, mirroring
`test_repeated_deaths_increase_danger_pressure`'s shape: seed a small-`count`/small-`area` region
(not `count=2000`/`100x100` like the AC#4-pattern integration test — investigation.md flags that a
single +1 nudge is a ~0.05% density change against that fixture's scale and would not produce an
assertable delta), apply N nudge-produced `WorldUpdate`s (using
`population_young_births_delta`, applied via the Step 3 apply-path logic — either by driving
`ApplyPath`/`apply_plan.py` directly or by hand-constructing the resulting `population_cohorts`
dict the same way the apply path would, whichever matches this test file's existing convention),
then call `RegionalPressureModel.evaluate()` with harvest aggregates and assert
`demand_multiplier`/`res_intensity` increases measurably relative to a zero-births baseline with
identical harvest activity. Do not scale the fixture up to make the existing `count=2000` pattern
"work more easily" — that is exactly the anti-drift smell investigation.md warns against (making
the test pass by recomputing to a nicer number rather than proving the real +1-scale mechanism).
**Do NOT touch:** `RegionalPressureModel.evaluate()`'s formula itself
(`src/domains/world_emergence/models.py:104-118`) or `compute_population_density()`
(`src/domains/demographics/cohort.py:122-146`) — both are unchanged by this ticket; only their
input (`population_cohorts` counts) gains a new mutation source.
**Verify:** the new test itself; no regression in the rest of `test_phase8_regional_pressure_model.py`.

### Step 9 — Add the integration end-to-end test (AC#4)
**Files:** `tests/integration/scenarios/test_demographics.py`
**Change:** Add `test_population_pressure_region_responds_to_real_births`, mirroring
`test_high_population_region_higher_resource_demand`'s pattern: drive at least the humanoid path
end-to-end through the actual `HumanoidReproductionService.process_reproduction()` call (chosen
because, per investigation.md, it is the only one of the two participating paths operating on real
entity pairs rather than a per-camp anchor, so it best exercises the full pipeline realistically),
applied via the real authoritative apply path (`ApplyPath.apply_generation()` or equivalent,
matching this test file's existing convention), and assert both the region's post-apply
`population_cohorts["young"].count` and the subsequent `RegionalPressureModel.evaluate()` output
move as expected. Optionally also exercise the natural-creature path in the same test if the
fixture setup (a mature camp) is not significantly more complex than the humanoid setup.
**Do NOT touch:** `DemographicCycleService.process_demographics()`'s own cycle — this test proves
the *nudge* responds, not the 200-tick aggregate cycle, which already has its own coverage in
`tests/unit/world/test_demographics.py`.
**Verify:** the new test itself; no regression in `tests/integration/scenarios/test_demographics.py`.

### Step 10 — Add architecture-guard regression tests
**Files:** `tests/unit/world/test_world_dynamics.py` (and one of the three reproduction-path test
files for the source-inspection guard)
**Change:** Add `test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update` per
test_plan.md New Test #12 — drives `WorldDynamicsSystem.resolve_dynamics()` (not
`CampService.process_camps()` alone) with the natural-creature flag ON and conditions producing a
birth, asserts the *final* returned `StateUpdate.world_updates` contains the region's
`population_cohorts_set`/`population_young_births_delta` nudge — this is the regression guard for
Step 2's fix specifically, since a `CampService`-level-only test would pass even if the
world_dynamics-level drop bug reappeared. Add
`test_reproduction_paths_never_mutate_region_directly` per New Test #11 — `inspect.getsource()` on
each of the three `process_*` methods, asserting no direct attribute assignment onto a
`RegionState`/`region.population_cohorts` object.
**Do NOT touch:** any non-reproduction-related tests in `test_world_dynamics.py`.
**Verify:** the two new tests themselves.

### Step 11 — Update the Mechanics Bible
**Files:** `docs/mechanics/05_world_evolution.md`
**Change:** Three corrections to now-false sentences (all confirmed present by direct read):
(a) lines 300-302 ("This path only *reads* `compute_regional_scarcity()`/`migration_threshold` —
it never writes `population_cohorts_set`...") — replace with a statement that the path now nudges
`population_cohorts["young"].count` by `+1` per birth via `population_young_births_delta`, additive
only, citing this ticket. (b) lines 331-336 ("This path writes no `population_cohorts_set` under
any circumstance.") — replace with an explicit statement that this ticket evaluated whether this
path should participate and confirmed exclusion, citing the `WORLD-121` rationale (calamity-driven
spawn is a world-threat escalation event, not a settlement/camp demographic signal) rather than
leaving the sentence as an unexamined default. (c) lines 399-403 ("Does not yet close the
population-pressure feedback loop... it never writes `population_cohorts_set`... that closure is a
separate, later mechanic") — replace with the same `+1`-nudge statement as (a), removing the
forward reference since the closure has now landed. Add a new subsection under §5 ("Demographic
Cohort Cycle"), most naturally directly after "Population Density Demand Signal (E52D)" (currently
ending at line 229-230), titled something like "Individual-Birth Population-Pressure Nudge (idea
38)", documenting: the nudge is coarse and additive-only, explicitly not a resync (per idea 38's
revision-25 decision); it is implemented via `WorldUpdate.population_young_births_delta`, summed
independently of and applied after `population_cohorts_set`; which two of the three reproduction
paths participate (natural-creature, humanoid) and which is excluded (magical/demonic, with the
`WORLD-121` rationale cited); and the missing-`young`-bracket resolution (a fresh bracket is
materialized with dataclass defaults, never silently dropped).
**Do NOT touch:** `docs/world/demographics_contract.md` or
`docs/world/ecology_and_calamity_contract.md` — both describe the density/`demand_multiplier`
formula itself, which this ticket does not change, only adds a new input-mutation source to
(confirmed by investigation.md's own conclusion after reading both). Do not touch the "Birth/Death
Law" (153-158) or "Migration Law" (207-208) subsections' own text — this ticket does not change
either mechanism.
**Verify:** `tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage` (static
doc-coverage check against this investigation's "Docs Requiring Update" bullets).

### Step 12 — Update the parity ledger
**Files:** `docs/parity_ledger/world_dynamics.yaml` (via `tools/parity_ledger_writer.py` — never a
raw edit, per project convention and the prior parity-updater full-file-rewrite-risk lesson)
**Change:** (a) `WORLD-120` (natural-creature, currently states "This path reads but never writes
population_cohorts" at line 1710, confirmed by direct read) — update `text` to describe the
`population_young_births_delta` nudge and update `v2_evidence`/`test_path` to cite
`test_natural_creature_birth_nudges_young_cohort_by_one`. (b) `WORLD-122` (humanoid, currently
states "reads but never writes population_cohorts" at lines 1781-1783, confirmed by direct read)
— same correction, citing `test_humanoid_birth_nudges_young_cohort_by_one`, and remove the forward
reference to this ticket ("the aggregate population-pressure feedback loop closure is a separate,
later ticket") since it has now landed. (c) `WORLD-121` (magical/demonic, currently states "This
path reads and writes no population_cohorts" at lines 1740-1741, confirmed by direct read) — the
core claim stays true; append a sentence recording that this ticket (cite ticket ID) evaluated
whether this path should participate in the nudge and confirmed exclusion, with the same rationale
as Step 11(b), so the omission reads as a confirmed decision, not a stale gap. (d) Add a new entry
(next available id in `world_dynamics.yaml`, `priority: P1` since it is the AC-critical closure
mechanism) documenting the nudge mechanism itself — `WorldUpdate.population_young_births_delta`,
additive-only, applied in `apply_plan.py` after `population_cohorts_set` resolution, participating
paths natural-creature/humanoid only — with `test_path` citing
`test_repeated_births_increase_population_density_signal` (Step 8) and
`test_population_pressure_region_responds_to_real_births` (Step 9), and cross-referencing
`WORLD-120`/`WORLD-121`/`WORLD-122`/`WORLD-DEMO-005`/`WORLD-DEMO-006`.
**Do NOT touch:** `WORLD-DEMO-005`'s or `WORLD-DEMO-006`'s own `text` — both describe mechanisms
this ticket does not change (the density→pressure formula itself, and world-assembly-time cohort
seeding respectively); reference them from the new entry instead of editing them.
**Verify:** `tests/tools/test_parity_index_baseline.py`, `tests/tools/test_parity_ledger_writer.py`,
`tests/tools/test_parity_ledger_schema.py`, `tests/tools/test_parity_updater_static.py` (the
latter's hardcoded `next_available_id` baseline for `world_dynamics.yaml` will drift and need
updating, same documented pattern as the humanoid ticket's own fix).

## Scope Guards

- Do not change `DemographicCycleService.process_demographics()`'s own birth/death math
  (`src/domains/demographics/cohort.py:337-419`) or `_check_migration()` (`223-321`) — the nudge is
  strictly additive on top of, never a reimplementation of, the 200-tick cycle.
- Do not implement a full resync/recount of `population_cohorts` against actual named entities —
  explicitly rejected by the idea-38 card.
- Do not build a single shared "scan `entities_add` for births" hook — birth markers
  (`parent_a_entity_id`/`parent_b_entity_id`, `LifecycleComponent.birth_tick`) cannot reliably
  distinguish reproduction-path births from ordinary `spawn_monster()`/`spawn_goblin()` garrison
  spawns after the fact (confirmed: neither calls `.birth_record()`). Wire the nudge inside each
  path's own existing flag-gated branch, as done in Steps 4/5/6.
- Do not introduce a new feature flag — reuse each path's existing flag
  (`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, `ENABLE_REPRODUCTION_HUMANOID_PATH`; the
  magical/demonic path's `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` is not touched since that path
  is excluded).
- Do not change `RegionalPressureModel.evaluate()`'s formula (`src/domains/world_emergence/models.py:104-118`)
  or `compute_population_density()` (`src/domains/demographics/cohort.py:122-146`) — only their
  input gains a new mutation source.
- Do not edit `docs/world/demographics_contract.md` or `docs/world/ecology_and_calamity_contract.md`.
- Do not edit `WORLD-DEMO-005` or `WORLD-DEMO-006`'s existing `text` fields.
- Do not touch the pre-existing `EntityGenerator._last_id` id-collision quirk flagged as an
  out-of-scope known-gap in the humanoid ticket's own Completion Summary.
- Do not change `SystemCadence.reproduction_humanoid` (200 ticks), `CAMP_SPAWN_INTERVAL` (30), or
  `DemographicCycleService.COHORT_INTERVAL` (200) — the cadence coincidence between humanoid
  reproduction and the demographic cycle is handled by the additive-delta design (Step 1/3), not by
  changing either cadence.
- Do not delete the three existing `test_*_does_not_write_population_cohorts` guard tests — retarget
  them (Step 7).

## Dependency Map

- Step 1 (new field) — no dependencies. Must land before Steps 3, 4, 5.
- Step 2 (fold-in fix) — no dependencies (independent pre-existing bug). Should land before Steps
  4/5's end-to-end behavior is meaningful, and before Step 10.
- Step 3 (apply-path delta logic) — depends on Step 1.
- Step 4 (natural-creature wiring) — depends on Steps 1, 2, 3.
- Step 5 (humanoid wiring) — depends on Steps 1, 2, 3.
- Step 6 (magical/demonic exclusion decision + test) — depends on Step 1 conceptually; no code
  dependency on Steps 2-5.
- Step 7 (retarget guard tests) — depends on Steps 4, 5, 6.
- Step 8 (pressure-model test) — depends on Steps 1, 3.
- Step 9 (integration test) — depends on Steps 1-6 (full pipeline).
- Step 10 (architecture-guard tests) — depends on Steps 2, 4, 5.
- Step 11 (mechanics doc) — depends on the decisions locked in Steps 4, 5, 6 (content must match
  final code).
- Step 12 (parity ledger) — depends on Steps 4, 5, 6, 11.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC#1 — successful birth increments `population_cohorts["young"].count` by exactly +1 via typed `WorldUpdate` through the authoritative apply path | Steps 1, 2, 3, 4, 5, 6 | `test_natural_creature_birth_nudges_young_cohort_by_one`, `test_humanoid_birth_nudges_young_cohort_by_one`, `test_magical_demonic_birth_nudge_decision` |
| AC#2 — no full resync/recount; additive-only, exactly +1 not a recomputed total | Steps 1, 3, 4, 5 | `test_two_simultaneous_births_same_region_same_call_both_nudge`, `test_birth_nudge_does_not_recompute_other_brackets`, `test_birth_in_region_missing_young_cohort` |
| AC#3 — `RegionalPressureModel.evaluate()`'s `demand_multiplier` measurably responds to births | Step 8 | `test_repeated_births_increase_population_density_signal` |
| AC#4 — new integration test proves a pressured region responds to real births | Step 9 | `test_population_pressure_region_responds_to_real_births` |
| AC#5 — reproduction paths' repeatable-births capability not "shipped" until this ticket lands atomically with the three path tickets | N/A — process/Finalize-time confirmation, not code | Noted in Completion Summary; already satisfied (the three path tickets are DONE prerequisites per ticket's Related Tickets) |
| AC#6 — `docs/mechanics/05_world_evolution.md` documents the nudge as coarse/additive-only; `docs/parity_ledger/world_dynamics.yaml` gains/updates an entry | Steps 11, 12 | `tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage`; `tests/tools/test_parity_ledger_schema.py`, `tests/tools/test_parity_ledger_writer.py` |

## Anti-Drift Notes

- The single highest-value diff to check: any nudge-building code that reads
  `state.regions[region_id].population_cohorts` fresh instead of accumulating through
  `WorldUpdate.merge()`'s additive `population_young_births_delta` will silently lose a sibling
  birth's nudge the moment two births land on the same region in the same call. Step 4's local
  `world_updates` dict in `camp.py` and Step 5's reliance on `reproduction_humanoid.py`'s existing
  `result.merge(pair_update)` loop are both designed specifically to avoid this trap — do not
  replace either with a direct `state.regions[...].population_cohorts` read-and-copy.
- `population_cohorts_set` (whole-dict-replace) and `population_young_births_delta` (additive) are
  deliberately two different fields with two different merge semantics on the same `WorldUpdate`
  dataclass — do not collapse them into one field or make the nudge write through
  `population_cohorts_set`, which would reintroduce the exact same-tick clobbering risk (Risk #2)
  this design avoids.
- The magical/demonic exclusion (Step 6) is a confirmed decision with cited evidence
  (`WORLD-121`'s own shipped rationale), not an oversight — a reviewer should not "fix" it by
  adding the nudge to `calamity.py` without first re-opening that rationale.
- Step 2's fix touches shared plumbing (`WorldDynamicsSystem.resolve_dynamics()`'s merge sequence)
  used by every system in the `cadence.world_dynamics` block, not just the reproduction paths —
  the full regression surface listed in test_plan.md (`test_camp_lifecycle.py`,
  `test_calamity_raid.py`, `test_calamity_pressure_propagator.py`,
  `test_creature_territory_lifecycle.py`, `test_world_dynamics.py`, `test_spawn_cadence.py`,
  `test_system_cadence.py`) must all still pass — this is not a scoped-down check.
- A region can have `population_cohorts == {}` legitimately (per `WORLD-DEMO-006`/idea 43's
  compiler, zero declared population seeds nothing) — Step 3's fresh-bracket creation must not
  raise or silently no-op in that case; both natural-creature's and humanoid's own eligibility
  gates already treat an empty/unseeded region as *eligible* (not suppressed), so births can and
  will occur there, and the nudge must handle it.

## Unresolved Questions

None. All architectural risks flagged in investigation.md (dropped `world_updates`, same-tick merge
collision, missing `young` bracket, magical/demonic participation) are resolved above with direct
code citations; none require a human decision beyond what this plan already settles.

## Deviations

- **Step 3 citation correction (architecture-review finding, applied at Implement time):** this
  plan's Step 3 and Summary cited `src/domains/demographics/cohort.py`'s migration "new bracket in
  target" branch (`replace(cohort, count=emigrant_count)`, cohort.py:288-290) as the precedent for
  materializing a fresh `PopulationCohort` with dataclass defaults when the `young` bracket is
  absent. That citation was inaccurate: the migration code at that line actually copies the
  *emigrating* cohort's own `birth_rate`/`mortality_rate`/`migration_threshold` via `replace()` — it
  does not use dataclass defaults. The plan's actually-specified behavior
  (`PopulationCohort(bracket="young", count=delta)` using dataclass defaults) was correct and was
  implemented exactly as specified — only the citation was wrong. The correct matching precedent,
  used in the implemented code's comment instead, is `src/worldbuilding/compiler.py`'s
  `_seed_population_cohorts()` (lines 186-224), whose own docstring states seeded cohorts "leave
  birth_rate/mortality_rate at their PopulationCohort dataclass defaults." No behavior changed as a
  result of this correction — it is a documentation/citation fix only.
