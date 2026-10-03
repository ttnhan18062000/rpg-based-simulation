---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260831-POPULATION-COHORT-SEEDING
phase: done
date: 2026-08-31
tags: [world]
---

# TCK-20260831-POPULATION-COHORT-SEEDING

## Title
Seed population_cohorts at world-compile time

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This is the highest-leverage item in M2, cited by 5 later ideas (32, 38, 43, 65), and also the highest-uncertainty item in the whole 65-idea roadmap — the guard it activates has never fired against real data. WorldCompiler.compile() never passes population_cohorts= when constructing RegionState, so DemographicCycleService's real, unit-tested birth/death/migration logic — wired live into the tick pipeline every 200 ticks — has literally never run against compiler-produced data; every existing test hand-constructs RegionState bypassing the compiler.

## Scope
- Modify WorldCompiler.compile() (src/worldbuilding/compiler.py:245-254) to pass population_cohorts= when constructing RegionState, using direct constructor assignment (the same precedent already used for influence and owner_faction_id), not the tick-time WorldUpdate.population_cohorts_set merge path.
- Author and explicitly document a fixed young/adult/elder distribution ratio (no existing anchor in code or docs anywhere) to seed cohort counts from a region's declared population, against today's real age-bracket boundaries (`<3000`/`<7000`/`≥7000` ticks) — do not silently assume these tick values are permanent (see Temporal-axis caution below).
- If constructing PopulationCohort instances requires setting `birth_rate`/`mortality_rate` (rather than relying on their existing dataclass defaults untouched), explicitly state in Implementation Notes what real-world meaning (if any) is intended for the seeded values — do not let a compile-time seed value quietly imply a fantasy-calendar meaning nobody has decided (see Temporal-axis caution below). If defaults are left untouched, say so explicitly instead of leaving it implicit.
- Verify DemographicCycleService.process_demographics() proceeds past the `if not region.population_cohorts: continue` guard (src/domains/demographics/cohort.py:349) on compiler-produced state at tick=200.
- Preserve determinism: compiling the same WorldSpec+seed twice must produce byte-identical population_cohorts.
- Ensure a region with zero PopulationSpec entries still compiles without crashing and the guard correctly no-ops.

## Out of Scope
- entity age_ticks always defaulting to 0 because the compiler's builder chain never calls .lifecycle(age_ticks=...) — a separate atlas finding, not part of this ticket.
- Downstream consumers of population_cohorts (ideas 32, 38, 65) — this ticket only seeds the field.
- Actually migrating age representation to fantasy-year units, or redefining birth_rate/mortality_rate to a calendar-independent unit (e.g. births/year) — both are accepted-but-not-yet-implemented future decisions per `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`, owned by a dedicated future calendar-migration ticket, not this one. This ticket only needs to avoid quietly baking in an assumption about either — documenting the gap is sufficient, resolving it is not required here.

## Acceptance Criteria
- [x] After WorldCompiler.compile() on a WorldSpec with a PopulationSpec targeting a region, RegionState.population_cohorts is non-empty (young/adult/elder keys) with counts summing to the region's declared population per a documented, explicitly-authored fixed distribution ratio.
- [x] Calling DemographicCycleService.process_demographics on a compiler-produced (not hand-built) AuthoritativeState at tick=200 proceeds past the guard and returns a real StateUpdate.
- [x] Compiling the same WorldSpec+seed twice produces byte-identical population_cohorts (determinism preserved).
- [x] A region with zero PopulationSpec entries still compiles without crashing and the guard correctly no-ops.
- [x] Implementation Notes explicitly states whether seeded PopulationCohort instances leave `birth_rate`/`mortality_rate` at their existing per-200-tick-cycle defaults untouched, or set new values — either way, the real-world (calendar) meaning intended is stated explicitly, not left implicit, per the cadence-duration-conflation finding below.

## Related Tickets
- TCK-20260619-E52A-COHORT-MODEL
- TCK-20260619-E52B-MIGRATION
- TCK-20260619-E52C-AGE-ADVANCEMENT
- TCK-20260619-E52D-DENSITY-SIGNAL
- TCK-20260523-WORLD-COMPILER
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY

## Related Docs
- docs/brainstorm/rpg_expected_schemas.html
- docs/plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md (Temporal-axis caution + cadence-coupled rate finding on idea 43, added 2026-08-31)
- docs/plans/rpg_design_roadmap/rpg_design_roadmap.md ("§9.3/§9.4 conflicts — code-verified" entry, added 2026-08-31)

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldbuilding/compiler.py
- src/domains/demographics/cohort.py
- src/core/state.py
- src/engine/world_dynamics.py
- src/engine/apply_plan.py
- src/worldbuilding/schema.py
- src/core/builder.py
- tests/unit/world/test_demographics.py
- tests/unit/worldbuilding/test_world_compiler.py

## Assumptions / Open Questions
- The young/adult/elder distribution ratio is an open design decision with zero existing anchor — must be explicitly authored and documented, not treated as obvious.
- This is the first time DemographicCycleService's logic will ever run against real compiled-world data — corpus/integration-level testing should be required, not just unit tests.
- Real class name is PopulationCohort (docs/brainstorm/rpg_expected_schemas.html), not 'CohortState' as some docs call it.
- **Temporal-axis caution (`TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`, decided):** the current tick-based age-bracket thresholds (`<3000`/`<7000`/`≥7000`) produce only a 4.17-day maximum lifespan under the now-settled 2,400-ticks/day calendar authority. Migrating age representation to fantasy-year units is an accepted-but-not-yet-implemented future decision. This ticket seeds population *counts* into the existing buckets, not the buckets themselves, so it is not blocked — but must not treat these specific tick values as permanent or build anything that would need non-trivial rework once that migration lands. Balancing/resolving the actual numbers is explicitly not required of this ticket; documenting the assumption is.
- **Cadence-coupled rate finding (code-verified 2026-08-31):** `PopulationCohort.birth_rate`/`mortality_rate` are defined and coded as "per 200-tick cycle" — the rate's real-world meaning is tied directly to `DemographicCycleService`'s evaluation cadence (`COHORT_INTERVAL=200`), not a calendar-independent duration unit (e.g. births/year). Since this ticket is the one that will next touch these exact fields, seed values chosen now inherit that ambiguity — state the intended real-world meaning explicitly when choosing seed numbers, or flag it as a known gap for the future calendar-authority migration ticket to resolve. Checked across all 16 M2 ideas: idea 43 (this ticket) is the *only* one with real exposure to the temporal-axis findings — no other M2 batch ticket needs this treatment.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260831-POPULATION-COHORT-SEEDING/plan.md`
(all 7 steps), with one test-fixture-level adjustment noted below and one tooling
workaround noted below.

**Step 1-3 (compiler.py):**
- Added a pre-aggregation pass in `WorldCompiler.compile()` immediately before the
  existing region-construction loop (`src/worldbuilding/compiler.py`), summing
  `PopulationSpec.count` by `spawn_region` across `spec.entities` into
  `region_declared_population: Dict[str, int]`.
- Added a module-level pure helper `_seed_population_cohorts(declared_population: int) ->
  Dict[str, PopulationCohort]`, placed before the `WorldCompiler` class, splitting a
  declared population into young/adult/elder counts using a fixed **30/50/20** ratio
  (`_YOUNG_ADULT_ELDER_RATIO`) via largest-remainder (Hamilton apportionment) rounding
  with fixed tie-break priority `["young", "adult", "elder"]` (`_BRACKET_PRIORITY`).
  Returns `{}` for `declared_population <= 0`.
- Wired the result into the existing `RegionState(...)` constructor call via a new
  `population_cohorts=_seed_population_cohorts(region_declared_population.get(r_spec.id,
  0))` kwarg — direct constructor assignment, matching the `influence`/`owner_faction_id`
  precedent on the adjacent lines. Did not route through
  `WorldUpdate.population_cohorts_set` / `apply_plan.py`.
- Added `from src.domains.demographics.cohort import PopulationCohort` at module level;
  confirmed no circular import (cohort.py's `src.core.state`/`src.core.updates`
  references are all under `TYPE_CHECKING`).

**AC 5 — `birth_rate`/`mortality_rate` decision (explicit statement):** Seeded
`PopulationCohort` instances leave `birth_rate=0.02` and `mortality_rate=0.01` at their
existing dataclass defaults, **untouched**. These remain exactly what they already meant
before this ticket — a fraction of `count` applied per `DemographicCycleService`'s
200-tick evaluation cadence (`COHORT_INTERVAL=200`), expressed in ticks, not any
calendar-independent unit (e.g. births/year). This ticket only supplies the initial
`count` values those existing rates apply to; it does not add, remove, or reinterpret
their real-world meaning. Recalibrating them to a calendar-independent unit remains an
accepted-but-not-yet-implemented future decision owned by
`TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`, not this ticket.
`PopulationCohort`'s dataclass definition itself (`src/domains/demographics/cohort.py`)
was **not touched at all** — confirmed via `git diff` showing zero changes to that file.

**Zero-`PopulationSpec` regions:** `_seed_population_cohorts(0) == {}` (empty dict, not
three zero-count cohorts), which `DemographicCycleService`'s existing guard
(`if not region.population_cohorts: continue`, `cohort.py:349`) already no-ops on
correctly via plain dict-truthiness — no new guard/defensive code was needed, confirmed
by test.

**Step 4-5 (tests):** Added 4 new tests exactly as specified in the ticket/plan's test
plan — see Test Summary below. One deviation from the plan's literal wording: plan
Step 5 said to reuse "the same spec-construction helpers already used in this file
[`tests/integration/scenarios/test_demographics.py`] for WORLD-DEMO-002/WORLD-DEMO-005."
On inspection, that file has no `WorldSpec`-construction helpers at all — its existing
tests (`test_cohort_migrates_on_scarcity`, `test_high_population_region_higher_resource_demand`,
etc.) all hand-build `RegionState`/`AuthoritativeState` directly via a local `_make_region`/
`_make_state` helper, never `WorldCompiler`/`WorldSpec`. This is itself the exact gap the
ticket exists to close, so there was nothing to reuse; I added a new local helper
`_build_population_seeding_world_spec()` in that file, modeled on
`create_base_valid_spec()` from `tests/unit/worldbuilding/test_world_compiler.py`, and
imported `WorldCompiler`/`WorldSpec` into the integration test file for the first time.
Recorded in `staging_artifacts/.../plan.md`'s Deviations section.

**Post-Test-phase regression fix (real regression, root-caused and fixed — not routed
around):** The Test phase's full regression sweep surfaced a real, pre-existing bug in
`RegionState.to_canonical_dict()` (`src/core/state.py`, originally introduced by
`TCK-20260619-E52A-COHORT-MODEL`): its `"population_cohorts": dict(sorted(...))` line
passed raw `PopulationCohort` dataclass instances straight through without serializing
them. This was always latent — `population_cohorts` was always `{}` in every compiled
world before this ticket, so `CanonicalStateHasher.to_canonical_data()` →
`json.dumps()` (`src/engine/checkpoint.py`) never actually touched a real
`PopulationCohort` instance. This ticket is exactly the first thing to seed
`population_cohorts` with real, non-empty data at compile time, so it is what first
exposed the bug: `CanonicalStateHasher.get_hash()` (called by `kernel.tick_once()` and
`kernel.shutdown()` on every real run) raised `TypeError: Object of type
PopulationCohort is not JSON serializable` on any world with seeded cohorts, breaking
30 tests (6 of them in `tests/integration/lab/`, where the exception was silently
swallowed into a `status="FAILED"` lab run result rather than surfacing as a raised
exception).

Fix (serialization-only, minimal, matching the existing per-nested-dataclass
convention already used by `SiegeState.to_canonical_dict()` on the adjacent line):
1. Added `PopulationCohort.to_canonical_dict(self) -> dict` (`src/domains/demographics/cohort.py`)
   returning its 5 fields (`bracket`, `count`, `birth_rate`, `mortality_rate`,
   `migration_threshold`) as a plain dict. No other change to `PopulationCohort` — its
   dataclass definition (fields, defaults, `frozen=True, slots=True`) and every other
   function in `cohort.py` (`get_age_bracket`, `DemographicCycleService`, migration
   helpers) are untouched, confirmed via `git diff` showing only the new method added.
2. Updated `RegionState.to_canonical_dict()` (`src/core/state.py`) to call
   `.to_canonical_dict()` on each `PopulationCohort` value:
   `{k: v.to_canonical_dict() for k, v in sorted(self.population_cohorts.items())}`.
3. Added a regression test,
   `tests/unit/worldbuilding/test_world_compiler.py::test_canonical_state_hasher_serializes_seeded_population_cohorts`,
   reusing the same `create_base_valid_spec()` + `WorldCompiler.compile()` pattern as
   the ticket's own `test_compiler_seeds_population_cohorts_from_spec` (real
   compiler-produced state, not a hand-built fixture). Asserts
   `CanonicalStateHasher.get_hash()` succeeds twice with an identical hash
   (determinism) and that the resulting canonical dict for each cohort matches the
   expected 5-field shape.

Verification: `tests/unit/worldbuilding/test_world_compiler.py`,
`tests/integration/scenarios/test_demographics.py`, and `tests/integration/lab/` all
pass (60 passed, 0 failed). The same broader sweep the Test phase ran
(`tests/unit/worldbuilding/ tests/unit/world/ tests/integration/scenarios/
tests/unit/worldassembly/ tests/integration/worldbuilding/
tests/integration/worldassembly/ tests/certification/ tests/integration/lab/
tests/unit/api/ tests/tools/ tests/unit/rendering/ -m "not slow"`) was re-run from a
fresh baseline (confirmed 30 failed + 1 error before the fix, matching the Test
phase's reported count exactly) — see Test Summary below for the after-fix count.
One pre-existing unrelated leftover artifact (`data/mutation_labs/test_mutlab_run/`
from a prior interrupted test run) had to be removed between runs to avoid a spurious
`FileExistsError` in `test_mutation_lab_orchestrator_end_to_end` — not a product of
this fix, a test-isolation artifact from re-running the same integration test twice
without its own cleanup firing (the test's `FileExistsError` guard exists to catch
concurrent lab runs, and correctly fired here on a leftover dir).

Also: the integration test's `PopulationSpec.count` needed to be 1000 (not a small demo
number like 50) — at small totals, `int(births - deaths)` truncation (`cohort.py:358`)
produces `net == 0` for every bracket, so the guard would pass but produce no real
`StateUpdate`, defeating the test's purpose. 1000 seeds young=300/adult=500/elder=200,
each comfortably above the ~100-count threshold where net birth/death first becomes
nonzero at these rates. Region bounds were sized to 60x60 to avoid triggering the
unrelated LAW-SPAWN-OCCUPANCY collision-reroll path under entity-spawn oversubscription.

**Step 6 (parity ledger):** Added `WORLD-DEMO-006` to `docs/parity_ledger/world_dynamics.yaml`.
**Tooling deviation:** `tools/parity_ledger_writer.py`'s `_ID_PATTERN`
(`^[A-Z]+-[0-9]{3}$`, itself mirroring `docs/parity_ledger/schema.json`'s own declared
`id` pattern) rejects multi-segment IDs like `WORLD-DEMO-006` — confirmed by direct
regex test that it also rejects all 5 pre-existing sibling entries already in this exact
shard (`WORLD-DEMO-001`..`005`). This is a pre-existing tool/schema bug, not something
introduced by this ticket, and not something in this ticket's scope to fix. Rather than
either (a) inventing an off-convention ID that would break traceability with the 5
established sibling entries, or (b) blocking the ticket on an unrelated tool defect, I
manually reproduced `write_entry()`'s exact validated read-modify-write-and-rebuild logic
(hand-checking every other `validate_entry()` rule: `status=verified` requires
non-empty `v2_evidence`+`test_path`, both present) and then ran the required separate,
visible `python3 tools/parity_index.py build` Bash call per `.claude/agents/parity-updater.md`'s
convention for the retro co-occurrence metric. `git diff --stat` on the ledger file shows
a clean 19-line pure-append, no reformatting of existing entries. **Recommend a follow-up
ticket to fix `_ID_PATTERN` in `tools/parity_ledger_writer.py` and the `id.pattern` in
`docs/parity_ledger/schema.json` to accept the established multi-segment convention
(e.g. `^[A-Z]+(-[A-Z]+)*-[0-9]{3}$`).**

**Step 7 (docs):** Added a new "§1a. Compile-Time Seeding" subsection to
`docs/world/demographics_contract.md`, between the existing §1 (PopulationCohort Model)
and §2 (Birth/Death Cycle) — §1-§5's existing content was not rewritten, only appended
to/around. Also added the `WORLD-DEMO-006` row to §6's parity table and
`src/worldbuilding/compiler.py`/the two new test files to §7's source-files table.
Updated the doc's `last_verified` frontmatter date and its `Tickets:` header line to
include this ticket. Did **not** touch `docs/mechanics/05_world_evolution.md` — since
`birth_rate`/`mortality_rate` defaults are unchanged, that chapter's existing
formula/cadence documentation stays accurate as-is, per the plan's explicit reasoning.

Ran `make knowledge-index-update` (docs changed) and `graphify update .` (src/tests
changed) after all edits.

## Test Summary

All 4 new tests specified in `staging_artifacts/.../test_plan.md` were written and pass,
plus full regression on the affected suites:

- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_seeds_population_cohorts_from_spec`
  — non-empty young/adult/elder keys, counts sum to declared population from 2
  `PopulationSpec` entries sharing one `spawn_region` (aggregation, not pass-through),
  and asserts `birth_rate==0.02`/`mortality_rate==0.01` (AC 5 guard).
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_population_cohorts_sum_exact_at_small_totals`
  — exact-sum property at `declared_population` = 1, 2, 7, 1000.
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_zero_population_spec_region_no_crash_and_cohorts_empty`
  — zero-`PopulationSpec` region compiles without crash, `population_cohorts == {}`.
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_population_cohorts_deterministic_same_seed`
  — same `WorldSpec`+seed compiled twice: `report1["state_hash"] == report2["state_hash"]`
  plus direct per-region `population_cohorts` dict equality (state_hash itself does not
  cover `population_cohorts`, so the direct dict-equality assertion is the
  ticket-load-bearing determinism check).
- `tests/integration/scenarios/test_demographics.py::test_demographic_cycle_proceeds_past_guard_on_compiler_produced_state_at_tick_200`
  — the ticket's headline AC: compiles a real `WorldSpec` via `WorldCompiler.compile()`
  (never a hand-built `RegionState`), calls `DemographicCycleService.process_demographics(...,
  tick=200)` directly, asserts `not result.is_noop()` and that the populated region
  produced a real `WorldUpdate`/`WorldEvent`.
- `tests/integration/scenarios/test_demographics.py::test_compiler_zero_population_region_guard_noop_via_full_tick_pipeline`
  (optional, plan marked belt-and-suspenders) — zero-`PopulationSpec` region compiled by
  `WorldCompiler` produces no `WorldUpdate`/`WorldEvent` for itself at tick=200.

Full regression run:
`.venv/bin/python3 -m pytest tests/unit/worldbuilding/ tests/unit/world/test_demographics.py tests/integration/scenarios/test_demographics.py -q`
→ **215 passed**, 0 failed. This includes the full existing
`tests/unit/worldbuilding/test_world_compiler.py` (47 tests, all pre-existing tests
unmodified) and `tests/unit/world/test_demographics.py` (unmodified) regression suites
named in the assignment, confirming no non-interference with entity placement/count,
terrain, or the existing hand-built-state demographic tests.

**Post-Test-phase regression fix — verification (2026-09-01):**

- `.venv/bin/python3 -m pytest tests/unit/worldbuilding/test_world_compiler.py
  tests/integration/scenarios/test_demographics.py tests/integration/lab/ -m "not slow"
  -q` → **60 passed**, 0 failed (includes the new
  `test_canonical_state_hasher_serializes_seeded_population_cohorts` regression test
  and all 6 previously-failing `tests/integration/lab/` tests, now passing).
- Broader sweep — same command the Test phase ran:
  `tests/unit/worldbuilding/ tests/unit/world/ tests/integration/scenarios/
  tests/unit/worldassembly/ tests/integration/worldbuilding/
  tests/integration/worldassembly/ tests/certification/ tests/integration/lab/
  tests/unit/api/ tests/tools/ tests/unit/rendering/ -m "not slow"`:
  - **Before fix** (re-run fresh from a clean baseline to confirm): **30 failed**, 3492
    passed, 14 skipped, 89 deselected, 1 xfailed, **1 error** — exact match to the Test
    phase's reported count.
  - **After fix**: **2 failed**, 3521 passed, 14 skipped, 89 deselected, 1 xfailed, 0
    errors.
  - Net: 28 failures + 1 error resolved by this fix (29 of 31 total baseline
    failure items).
  - The 2 remaining failures are both pre-existing and unrelated to this fix:
    1. `tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`
       — expected `docs/REGISTRY.yaml` drift from this ticket's own doc edit
       (`docs/world/demographics_contract.md`'s `last_verified` field); self-resolves
       at Finalize's automatic `docs/REGISTRY.yaml` regen, per the project's standard
       ticket-close flow.
    2. `tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x`
       — already failing in the pre-fix baseline too (present in both the Test
       phase's original 30 and this run's re-confirmed 30). Root cause confirmed by
       traceback: `TimeoutError: Test execution exceeded the resource time limit`
       raised by `tests/conftest.py`'s per-test resource-time-limit signal handler —
       has nothing to do with `population_cohorts`/`CanonicalStateHasher` (the
       traceback passes through `HardLawMonitor.check_occupancy`, not
       `to_canonical_dict`). The test is explicitly marked
       `@pytest.mark.extra_slow` and its own docstring documents it as designed to run
       only in the dedicated "Slow regression" CI job (600s budget, ~128.8s measured
       runtime) — `-m "not slow"` alone does not exclude `extra_slow`, so it executes
       in this sandboxed sweep and hits the sandbox's own tighter per-test wall-clock
       limit. Not in scope for this fix; not caused by this fix.
  - One local test-isolation artifact (`data/mutation_labs/test_mutlab_run/`, left
    over from an earlier interrupted run of the same suite) had to be removed between
    sweep runs to avoid a spurious `FileExistsError` in
    `test_mutation_lab_orchestrator_end_to_end` — unrelated to the fix itself, a
    pre-existing test-isolation gap in that orchestrator test (it correctly detects
    and refuses to overwrite an existing lab dir; the leftover dir was mine from an
    earlier run in this same session).
- Confirmed via `git diff -- src/domains/demographics/cohort.py`: the only change to
  that file is the additive `to_canonical_dict()` method — `PopulationCohort`'s 5
  field definitions, defaults, `frozen=True, slots=True` status, and every other
  function in the file (`get_age_bracket`, `compute_elder_attribute_update`,
  `compute_population_density`, `compute_regional_scarcity`,
  `find_adjacent_regions`, `_check_migration`, `DemographicCycleService`) are
  byte-for-byte unchanged.

## Files Changed

- `src/worldbuilding/compiler.py` — pre-aggregation pass, `_seed_population_cohorts()`
  helper, `RegionState(...)` constructor wiring, new `PopulationCohort` import.
- `src/domains/demographics/cohort.py` — added `PopulationCohort.to_canonical_dict()`
  (post-Test-phase regression fix; dataclass fields/other functions untouched).
- `src/core/state.py` — `RegionState.to_canonical_dict()` now calls
  `.to_canonical_dict()` on each `PopulationCohort` value instead of passing it through
  raw (post-Test-phase regression fix).
- `tests/unit/worldbuilding/test_world_compiler.py` — 4 new tests (see Test Summary),
  1 new import line, plus 1 new regression test
  (`test_canonical_state_hasher_serializes_seeded_population_cohorts`) and a
  `CanonicalStateHasher` import (post-Test-phase regression fix).
- `tests/integration/scenarios/test_demographics.py` — 2 new tests, `WorldCompiler`/
  `WorldSpec` imports, new `_build_population_seeding_world_spec()` helper.
- `docs/parity_ledger/world_dynamics.yaml` — new `WORLD-DEMO-006` entry (pure append).
- `docs/world/demographics_contract.md` — new "§1a. Compile-Time Seeding" subsection;
  updated §6 parity table, §7 source-files table, frontmatter `last_verified`, and
  `Tickets:` header line.
- `staging_artifacts/TCK-20260831-POPULATION-COHORT-SEEDING/investigation.md` — created
  in this run's own Investigate phase (pre-existing when implementation began).
- `staging_artifacts/TCK-20260831-POPULATION-COHORT-SEEDING/plan.md` — created in this
  run's own Plan phase, architecture-review-verified (pre-existing when implementation
  began; a Deviations section was appended per the notes above).
- `staging_artifacts/TCK-20260831-POPULATION-COHORT-SEEDING/test_plan.md` — created in
  this run's own Plan phase (pre-existing when implementation began).
- `tickets/inprogress/TCK-20260831-POPULATION-COHORT-SEEDING.md` — this file: Status,
  Acceptance Criteria checkboxes, Implementation Notes, Test Summary, Files Changed,
  Completion Summary.

Not changed (verified via `git diff` showing zero diff):
`src/domains/demographics/cohort.py` (`PopulationCohort` dataclass itself, `get_age_bracket()`,
`DemographicCycleService.process_demographics()`/`_check_migration()` logic — all untouched
per the plan's Scope Guards), `docs/mechanics/05_world_evolution.md`.

## Completion Summary

Implemented compile-time seeding of `RegionState.population_cohorts`:
`WorldCompiler.compile()` now sums declared population per region from
`WorldSpec.entities` (`PopulationSpec.count` by `spawn_region`) and splits it
young/adult/elder via a fixed, documented 30/50/20 ratio with exact-sum largest-remainder
rounding, wired into the existing `RegionState(...)` constructor call (not the tick-time
`WorldUpdate.population_cohorts_set` path). This activates `DemographicCycleService`'s
birth/death/migration logic — previously dead code against compiler-produced state,
confirmed to now proceed past its guard and return a real `StateUpdate` at tick=200
against real compiled state, verified by a new integration test. `PopulationCohort`'s
dataclass (fields, defaults, frozen/slots status) was left completely untouched;
`birth_rate`/`mortality_rate` stay at their existing 0.02/0.01 per-200-tick-cycle
defaults, with that decision and its real-world meaning stated explicitly per AC 5. All
4 required tests plus 2 optional/belt-and-suspenders tests were added and pass, along
with 215 total tests across the affected regression suites. Parity ledger entry
`WORLD-DEMO-006` and a new "Compile-Time Seeding" doc subsection were added; a
pre-existing, unrelated bug in `tools/parity_ledger_writer.py`'s ID-pattern validation
(rejects the established multi-segment `WORLD-DEMO-XXX` convention already used by 5
sibling entries) was worked around by hand-reproducing the writer's validated write
path rather than either breaking ID convention or blocking on it — flagged for a
follow-up ticket.

**Post-Test-phase regression fix:** The Test phase's full regression sweep surfaced a
real, pre-existing bug this ticket was the first to expose: `RegionState.to_canonical_dict()`
(`src/core/state.py`) passed raw `PopulationCohort` instances through to `json.dumps()`
unserialized, because `population_cohorts` had always been empty in every prior
compiled world. Fixed by adding `PopulationCohort.to_canonical_dict()`
(`src/domains/demographics/cohort.py`, additive only — no other change to that file)
and updating `RegionState.to_canonical_dict()` to call it per-cohort. Added a
regression test proving `CanonicalStateHasher.get_hash()` now succeeds and is
deterministic against real compiler-produced state with seeded cohorts. Re-ran the
Test phase's exact broader sweep: 30 failed/1 error before the fix (matching the Test
phase's report) → 2 failed after, both pre-existing and unrelated (a REGISTRY.yaml
drift that self-resolves at Finalize, and an already-failing, unrelated
`extra_slow`-marked timeout test). All 6 `tests/integration/lab/` failures are
resolved.
