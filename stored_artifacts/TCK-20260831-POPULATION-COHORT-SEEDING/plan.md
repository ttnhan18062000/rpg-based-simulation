---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260831-POPULATION-COHORT-SEEDING
artifact_type: plan
tags: [world]
---

# Implementation Plan — TCK-20260831-POPULATION-COHORT-SEEDING

## Summary

`WorldCompiler.compile()` never seeds `RegionState.population_cohorts`, so
`DemographicCycleService`'s live birth/death/migration logic has never run against
compiler-produced state. This plan adds a small, pure, RNG-free pre-aggregation pass
(sum `PopulationSpec.count` by `spawn_region`) inserted immediately before the existing
step-2 region-construction loop in `compile()`, a new pure helper
`_seed_population_cohorts(declared_population)` that splits the total into
`young`/`adult`/`elder` `PopulationCohort` instances using a fixed 30/50/20 ratio with
largest-remainder (Hamilton) rounding to guarantee an exact sum at any population size,
and wires the result into `RegionState(...)`'s existing constructor call via direct
keyword assignment — following the same precedent already used for `influence` and
`owner_faction_id`. Seeded cohorts leave `birth_rate`/`mortality_rate` at their dataclass
defaults (`0.02`/`0.01`) untouched. A region with no matching `PopulationSpec` entries
gets `population_cohorts={}`, which the existing guard at `cohort.py:349` already no-ops
on correctly — no new guard/defensive code needed. Docs and parity ledger are updated to
record the new compile-time seeding behavior.

## Steps

### Step 1 — Add pre-aggregation pass for declared population per region

**Files:** `src/worldbuilding/compiler.py`

**Change:** Immediately before the existing `# 2. Compile regions & terrain painting`
comment / `regions: Dict[str, RegionState] = {}` line (confirmed at
`compiler.py:209-211`), insert a new pre-pass that sums `PopulationSpec.count` by
`spawn_region` across `spec.entities`:

```python
# 1a. Aggregate declared population per region from spec.entities (PopulationSpec.count),
# summed by spawn_region. Must run before step 2 constructs RegionState, since RegionState
# is @dataclass(frozen=True, slots=True) (src/core/state.py:235) and cannot be
# field-mutated after construction. Multiple PopulationSpec entries may share one
# spawn_region (WorldSpec.validate_unique_identifiers only enforces uniqueness of
# PopulationSpec.id, not spawn_region — schema.py:277-282), so this must sum, not overwrite.
region_declared_population: Dict[str, int] = {}
for pop_spec in spec.entities:
    region_declared_population[pop_spec.spawn_region] = (
        region_declared_population.get(pop_spec.spawn_region, 0) + pop_spec.count
    )
```

`spec.entities: list[PopulationSpec]` is confirmed at `schema.py:236`; `PopulationSpec`
fields (`id`, `count`, `role`, `faction`, `spawn_region`, `archetype_id`) confirmed at
`schema.py:151-162` (read directly this session). `spec.entities` is fully available at
function entry — no ordering dependency on any other compile step (confirmed: step 6,
the only other reader of `spec.entities`, is at `compiler.py:352-473`, well after step 2).

This pass is pure arithmetic over already-loaded spec data — no RNG draw, so it cannot
perturb `DeterministicRNG`'s draw sequence used later in step 2 (terrain-variant
`weighted_choice`, `compiler.py:228-233`) or step 6 (entity tile/personality rolls,
`compiler.py:303-304`, `422-431`).

**Do NOT touch:** step 6's entity-spawning loop (`compiler.py:352-473`) itself — this
pre-pass only reads `spec.entities`, it does not replace or interact with step 6's own
iteration over the same list. Do not change how step 6 counts/spawns `EntityState`
objects.

**Verify:** Covered indirectly by Step 3's tests (the aggregation has no directly
observable output until Step 2 wires it into `RegionState`). Confirm via
`test_compiler_entity_mappings` and `test_compiler_placement_bounds` (existing, run
unmodified) that step 6's entity count/placement is unaffected — the "Non-interference
guard" from test_plan.md.

### Step 2 — Add `_seed_population_cohorts()` helper with fixed ratio and exact rounding

**Files:** `src/worldbuilding/compiler.py`

**Change:** Add a new module-level pure function, placed near the top of the file
alongside the other free helper functions (e.g. after `get_role_enum`, before the
`WorldCompiler` class):

```python
# Fixed young/adult/elder distribution ratio for compile-time population_cohorts seeding.
# Authored 2026-09-01 (TCK-20260831-POPULATION-COHORT-SEEDING) — no prior anchor existed
# in code or docs. Chosen as a plausible stable/mildly-growing population pyramid shape:
# a plurality of working-age adults, a meaningful youth cohort, and a smaller elder
# cohort — directionally consistent with PopulationCohort's own default
# birth_rate (0.02) > mortality_rate (0.01), which already implies net growth
# (cohort.py:41-42). Ratio is intentionally simple/round, not derived from any external
# demographic dataset — this is a fresh design choice, not a parity claim against
# real-world data.
_YOUNG_ADULT_ELDER_RATIO: Dict[str, float] = {"young": 0.30, "adult": 0.50, "elder": 0.20}
# Fixed priority order used only to break exact remainder ties deterministically.
_BRACKET_PRIORITY: List[str] = ["young", "adult", "elder"]


def _seed_population_cohorts(declared_population: int) -> Dict[str, "PopulationCohort"]:
    """
    Split declared_population into young/adult/elder PopulationCohort counts using the
    fixed _YOUNG_ADULT_ELDER_RATIO, via largest-remainder (Hamilton apportionment)
    rounding so the three counts always sum exactly to declared_population, including
    at small totals (0, 1, 2) where naive per-bracket floor/truncation can lose 1-2
    units (investigation.md "Risks and Open Questions").

    Pure arithmetic, no RNG — consistent with the only two existing precedents for
    deriving a RegionState field from other spec values (`influence`, `owner_faction_id`
    at compiler.py:250-251), neither of which uses RNG (investigation.md "Determinism
    precedent inside compile()").

    Returns {} (not three zero-count cohorts) when declared_population == 0, so the
    DemographicCycleService guard at cohort.py:349 (`if not region.population_cohorts:
    continue`) no-ops via plain dict-truthiness — matching the ticket's literal wording
    "the guard correctly no-ops" (investigation.md "Zero-PopulationSpec edge case").
    Seeded cohorts leave birth_rate/mortality_rate at their PopulationCohort dataclass
    defaults (0.02/0.01, cohort.py:41-42) untouched — see Step 2 rationale in plan.md
    Anti-Drift Notes for why.
    """
    if declared_population <= 0:
        return {}

    raw = {b: declared_population * r for b, r in _YOUNG_ADULT_ELDER_RATIO.items()}
    floors = {b: int(v) for b, v in raw.items()}
    remainder = declared_population - sum(floors.values())

    remainders = sorted(
        _BRACKET_PRIORITY,
        key=lambda b: (-(raw[b] - floors[b]), _BRACKET_PRIORITY.index(b)),
    )
    counts = dict(floors)
    for b in remainders[:remainder]:
        counts[b] += 1

    return {
        bracket: PopulationCohort(bracket=bracket, count=counts[bracket])
        for bracket in _BRACKET_PRIORITY
    }
```

Also add the import at the top of `compiler.py` (existing imports confirmed at
`compiler.py:1-30`, no prior import of `cohort.py`):

```python
from src.domains.demographics.cohort import PopulationCohort
```

No circular-import risk: `cohort.py`'s only references to `src.core.state` /
`src.core.updates` are under `TYPE_CHECKING` (`cohort.py:12-14`), so importing
`PopulationCohort` at module level into `compiler.py` does not create a runtime cycle
(confirmed by reading `cohort.py:1-16` this session).

**Do NOT touch:** `PopulationCohort`'s dataclass definition itself
(`src/domains/demographics/cohort.py:17-43`) — do not add fields, change defaults, or
change frozen/slots status. Do not touch `get_age_bracket()` or the `3000`/`7000` tick
thresholds (`cohort.py:50-65`) — those are a separate, already-flagged temporal-axis
concern out of scope per the ticket.

**Verify:** `test_compiler_population_cohorts_sum_exact_at_small_totals` (new,
`tests/unit/worldbuilding/test_world_compiler.py`) — asserts exact-sum property at
`count=1`, `count=2`, `count=7`, and a large round number, per test_plan.md.

### Step 3 — Wire seeded cohorts into `RegionState(...)` constructor call

**Files:** `src/worldbuilding/compiler.py`

**Change:** In the step-2 `RegionState(...)` constructor call (confirmed exact text at
`compiler.py:245-254`), add one new keyword argument, following the same
direct-constructor-assignment pattern already used for `influence`
(`100.0 if r_spec.type == "town" else 0.0`) and `owner_faction_id` (`owner_faction`) on
the adjacent lines:

```python
regions[r_spec.id] = RegionState(
    id=r_spec.id,
    name=r_spec.id.replace("_", " ").title(),
    bounds=(r_spec.bounds[0], r_spec.bounds[1], r_spec.bounds[2], r_spec.bounds[3]),
    kind=r_spec.type.upper(),
    influence=100.0 if r_spec.type == "town" else 0.0,
    owner_faction_id=owner_faction,
    hazard_level=getattr(r_spec, "hazard_level", 0.0),
    hazard_kind=getattr(r_spec, "hazard_kind", "PHYSICAL"),
    population_cohorts=_seed_population_cohorts(region_declared_population.get(r_spec.id, 0)),
)
```

`region_declared_population` is the `Dict[str, int]` built in Step 1, already in scope
inside the step-2 `for r_spec in spec.regions:` loop since it is defined immediately
before that loop starts. `RegionState.population_cohorts: Dict[str, Any]` field
(default `field(default_factory=dict)`) confirmed at `state.py:255` — this ticket's
change replaces the fallen-through empty-dict default with the aggregated/seeded value
for regions with a nonzero declared population, and leaves it as the same empty-dict
default (via `_seed_population_cohorts(0) == {}`) for regions with none.

**Other writers to `RegionState.population_cohorts` / `region.population_cohorts`
(shared-resource enumeration, since this field has other writers at a different
pipeline phase):**
- `src/engine/apply_plan.py:124-139` — the **tick-time** apply path, applies
  `WorldUpdate.population_cohorts_set` via `dataclasses.replace(reg, ...,
  population_cohorts=pop_cohorts, ...)` once `DemographicCycleService` or migration logic
  produces a `WorldUpdate` during a live tick (`COHORT_INTERVAL=200`,
  `cohort.py:325`/`342-343`). This compile-time write happens once, at world-assembly
  time, strictly before any tick runs — there is no ordering race with `apply_plan.py`,
  because compile-time seeding populates the *initial* state that the first
  tick-200 cycle then reads and replaces. No double-write: `compile()` never emits a
  `WorldUpdate`, and `apply_plan.py` never runs during `compile()`.
- `DemographicCycleService.process_demographics()` (`cohort.py:328-410`) and
  `_check_migration()` (referenced at `cohort.py:392-402`) — both are pure decision
  logic that *read* `region.population_cohorts` and return a `StateUpdate`/`WorldUpdate`
  for `apply_plan.py` to apply; neither writes `RegionState` directly (confirmed,
  investigation.md "Current Behavior" — `docs/mechanics/05_world_evolution.md`'s "pure
  decision logic" law). No interaction with this ticket's write beyond being its first
  real consumer.
- No other call site constructs or replaces `RegionState.population_cohorts` (confirmed:
  the only two writers found are this new compile-time constructor call and the
  tick-time `apply_plan.py` replace path — investigation.md's grep-confirmed finding).

**Do NOT touch:** the `apply_plan.py:124-139` tick-time merge path itself — do not
route compile-time seeding through `WorldUpdate.population_cohorts_set`, per the
ticket's explicit scope instruction and investigation.md's confirmation that this is a
distinct, separate code path.

**Verify:**
- `test_compiler_seeds_population_cohorts_from_spec` (new) — non-empty
  `young`/`adult`/`elder` keys, counts sum to declared population, includes a 2+
  `PopulationSpec`-sharing-one-`spawn_region` fixture.
- `test_compiler_zero_population_spec_region_no_crash_and_cohorts_empty` (new) —
  zero-`PopulationSpec` region compiles without crash, `population_cohorts == {}`.
- Full existing regression: `test_compiler_minimal_world`, `test_compiler_placement_bounds`,
  `test_compiler_entity_mappings`, `test_compile_sets_real_town_center_from_town_region`,
  `test_compiler_faction_bravery_bias_produces_real_population_skew` (all unmodified,
  per test_plan.md "Regression Surface").

### Step 4 — Determinism test

**Files:** `tests/unit/worldbuilding/test_world_compiler.py`

**Change:** Add `test_compiler_population_cohorts_deterministic_same_seed`, mirroring
the existing `test_compiler_terrain_variants_deterministic_same_seed` pattern
(`test_world_compiler.py:752-770`, read this session): compile the same spec twice with
`seed=42`, assert `report1["state_hash"] == report2["state_hash"]`, and additionally
assert direct equality of `population_cohorts` dicts per region (dataclass `__eq__` on
frozen `PopulationCohort` gives field-value equality, which is sufficient — no need for
JSON serialization since `Steps 1-3` never introduce RNG). No source change required
for this step beyond what Steps 1-3 already did — this step is pure-test.

**Do NOT touch:** `StateFingerprinter`/`report["state_hash"]` computation itself
(`compiler.py:24`, `src/replay/fingerprint.py`) — out of scope; this step only consumes
the existing hash as a second determinism signal, per precedent.

**Verify:** the new test itself, run against Steps 1-3's implementation.

### Step 5 — Integration test: guard proceeds on compiler-produced state at tick=200

**Files:** `tests/integration/scenarios/test_demographics.py`

**Change:** Add `test_demographic_cycle_proceeds_past_guard_on_compiler_produced_state_at_tick_200`:
build a real `WorldSpec` (via the same spec-construction helpers already used in this
file for `WORLD-DEMO-002`/`WORLD-DEMO-005`) with at least one region carrying a nonzero
declared population, run it through `WorldCompiler.compile()` (not a hand-built
`RegionState`/`AuthoritativeState`), then call
`DemographicCycleService.process_demographics(compiled_state, tick=200)` directly and
assert the guard at `cohort.py:349` is passed — i.e. the returned `StateUpdate` is
non-trivial (`world_updates` and/or `world_events_add` non-empty for the populated
region), distinct from the `StateUpdate()` empty-sentinel returned by the
off-cycle/empty-cohort short-circuits (`cohort.py:343`/`349-350`). This is the ticket's
headline AC — "the guard has never fired against real data" — so this test must use
`WorldCompiler.compile()` output, never a hand-built fixture, or it does not satisfy AC 2.

Optionally (belt-and-suspenders, test_plan.md marks this optional): add
`test_compiler_zero_population_region_guard_noop_via_full_tick_pipeline` confirming the
zero-`PopulationSpec` region from Step 3 produces no `WorldUpdate`/`WorldEvent` when run
through the same `process_demographics(..., tick=200)` call.

**Do NOT touch:** `DemographicCycleService.process_demographics()`'s own logic
(`cohort.py:328-410`) — this step only adds a new caller/fixture, no behavior change to
the birth/death/migration code itself.

**Verify:** the new test(s) themselves; also re-run
`test_cohort_migrates_on_scarcity` (`WORLD-DEMO-002`) and
`test_high_population_region_higher_resource_demand` (`WORLD-DEMO-005`) unmodified, per
test_plan.md's "Parity Ledger Overlap" regression note.

### Step 6 — Parity ledger entry `WORLD-DEMO-006`

**Files:** `docs/parity_ledger/world_dynamics.yaml`

**Change:** Append a new entry after the existing `WORLD-DEMO-005` block (confirmed
last entry ends at `world_dynamics.yaml:1206`, read this session — format mirrored from
that entry):

```yaml
- id: WORLD-DEMO-006
  text: 'WorldCompiler.compile() seeds RegionState.population_cohorts at world-assembly
    time. For each region, declared population = sum(PopulationSpec.count for specs
    with matching spawn_region). Counts are split into young/adult/elder using a fixed
    30/50/20 ratio via largest-remainder (Hamilton apportionment) rounding, guaranteeing
    exact-sum reproduction at any population size. Seeded PopulationCohort instances
    keep birth_rate=0.02/mortality_rate=0.01 (dataclass defaults) untouched. A region
    with zero matching PopulationSpec entries gets population_cohorts={}, on which
    DemographicCycleService''s guard (cohort.py:349) no-ops via plain dict truthiness.
    Seeding is pure arithmetic (no RNG), preserving compile() determinism.'
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: src/worldbuilding/compiler.py (_seed_population_cohorts, RegionState(...)
    construction, step 2)
  proof_type: parity
  test_path: tests/unit/worldbuilding/test_world_compiler.py::test_compiler_seeds_population_cohorts_from_spec
  divergence_note: null
  support_boundary: null
```

**Do NOT touch:** `WORLD-DEMO-001` through `WORLD-DEMO-005` — no status/evidence change,
they remain `verified`/`P1` unmodified; this ticket only adds a new entry.

**Verify:** manual check (per test_plan.md's "Parity-ledger guard") — confirm
`test_path` cites a test that actually exists and passes before Finalize; run
`python3 tools/parity_ledger_writer.py` validation if the project's tooling requires it
for schema conformance (confirm exact invocation during implementation from
`docs/parity_ledger/schema.json` / existing tooling, not assumed here).

### Step 7 — Docs: `docs/world/demographics_contract.md` new section

**Files:** `docs/world/demographics_contract.md`

**Change:** Add a new subsection (placed before or as an addendum to the existing "§1
PopulationCohort Model" section — exact heading numbering to be matched to the file's
current structure at implementation time) titled "Compile-Time Seeding", stating:
- `WorldCompiler.compile()` seeds `RegionState.population_cohorts` from
  `WorldSpec.entities` (`PopulationSpec.count`, summed by `spawn_region`) at
  world-assembly time — not via the tick-time `WorldUpdate.population_cohorts_set` path.
- The fixed 30/50/20 young/adult/elder ratio and rationale (Step 2's rationale, copied
  verbatim in substance).
- The largest-remainder rounding rule, guaranteeing exact-sum at any population size.
- Seeded cohorts keep `birth_rate=0.02`/`mortality_rate=0.01` dataclass defaults —
  explicitly note these remain a per-200-tick-cycle rate, not yet recalibrated to any
  calendar-independent unit (cross-reference `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`
  as the ticket that would revisit this).
- Zero-`PopulationSpec` regions get `population_cohorts={}`.

**Do NOT touch:** the existing "§1 PopulationCohort Model" through "§5" content
describing tick-time birth/death/migration mechanics — those are unchanged by this
ticket; this is a pure addition, not a rewrite of established sections.

**Verify:** doc review only — no automated test binds to prose content; confirmed
correct by cross-reading against Step 2/3's actual implementation before Finalize
(doc/code parity, per Authoritative Mechanics Rule).

## Unresolved Questions

None. All open design decisions flagged in investigation.md/test_plan.md are resolved
in this plan (see Anti-Drift Notes for the explicit list). No step is a placeholder.

## Scope Guards

- Do not modify `PopulationCohort`'s dataclass definition, fields, or defaults
  (`src/domains/demographics/cohort.py:17-43`).
- Do not modify `get_age_bracket()` or the `3000`/`7000` tick-based bracket thresholds
  (`cohort.py:50-65`) — a separate, already-flagged temporal-axis migration concern, out
  of scope per the ticket's "Out of Scope" section and
  `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`.
- Do not modify `DemographicCycleService.process_demographics()` or `_check_migration()`
  logic (`cohort.py:328-410`, referenced migration code) — this ticket only supplies
  input data those functions read; it does not change their behavior.
- Do not route compile-time seeding through `WorldUpdate.population_cohorts_set` /
  `apply_plan.py:124-139` — direct `RegionState(...)` constructor assignment only.
- Do not use `dataclasses.replace()` on an already-built `RegionState` as a post-hoc
  patch after step 6 — seeding must happen via the Step 3 constructor kwarg at step 2.
- Do not touch step 6's entity-spawning loop (`compiler.py:352-473`) — no change to how
  many `EntityState` objects are spawned, their placement, or their IDs.
- Do not fix the separate, already-identified `age_ticks` defaulting-to-0 gap (the
  compiler's builder chain never calling `.lifecycle(age_ticks=...)`) — explicitly listed
  as Out of Scope in the ticket.
- Do not implement downstream consumers of `population_cohorts` (ideas 32, 38, 65) —
  this ticket only seeds the field.
- Do not migrate age representation to fantasy-year units or redefine
  `birth_rate`/`mortality_rate` to a calendar-independent unit — accepted-but-not-yet-
  implemented, owned by a future calendar-migration ticket.
- Do not widen `RegionState.population_cohorts`'s keying beyond `Dict[str,
  PopulationCohort]` keyed by bracket name (`"young"`/`"adult"`/`"elder"`) — e.g. never
  key by `PopulationSpec.id` or population-group name.
- Do not change `docs/mechanics/05_world_evolution.md` — birth_rate/mortality_rate
  defaults are left untouched (Step 2), so this chapter's existing formula/cadence
  documentation stays accurate as-is; no update required (investigation.md "Docs
  Requiring Update" confirms this condition).

## Dependency Map

- Step 1 (aggregation pre-pass) must land before Step 3 (constructor wiring), since
  Step 3 reads `region_declared_population` from Step 1.
- Step 2 (`_seed_population_cohorts` helper) must land before Step 3, since Step 3 calls it.
- Steps 1, 2, and 3 together are one atomic code change to `compiler.py` — implement and
  verify them together (they cannot be independently tested mid-way since Step 3's tests
  exercise Steps 1+2 through the compiled output).
- Step 4 (determinism test) depends on Steps 1-3 being complete.
- Step 5 (integration test) depends on Steps 1-3 being complete.
- Step 6 (parity ledger) depends on Step 3's test existing and passing (its `test_path`
  cites `test_compiler_seeds_population_cohorts_from_spec`).
- Step 7 (docs) depends on Steps 1-3's final implementation shape (ratio, rounding rule,
  rate-default decision) being locked in, so the doc accurately describes shipped
  behavior.
- No step depends on anything outside this ticket's own steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC 1 — `population_cohorts` non-empty, young/adult/elder keys, counts sum to declared population per documented fixed ratio | Steps 1, 2, 3 | `test_compiler_seeds_population_cohorts_from_spec`, `test_compiler_population_cohorts_sum_exact_at_small_totals` |
| AC 2 — `process_demographics` on compiler-produced state at tick=200 proceeds past guard, returns real `StateUpdate` | Steps 1, 2, 3 (produce the data), Step 5 (proves it) | `test_demographic_cycle_proceeds_past_guard_on_compiler_produced_state_at_tick_200` |
| AC 3 — same WorldSpec+seed compiled twice produces byte-identical `population_cohorts` | Steps 1, 2, 3 (pure arithmetic, no RNG, by construction), Step 4 (proves it) | `test_compiler_population_cohorts_deterministic_same_seed` |
| AC 4 — zero-`PopulationSpec` region compiles without crash, guard correctly no-ops | Steps 1, 2, 3 (`_seed_population_cohorts(0) == {}`) | `test_compiler_zero_population_spec_region_no_crash_and_cohorts_empty`, optionally `test_compiler_zero_population_region_guard_noop_via_full_tick_pipeline` |
| AC 5 — Implementation Notes explicitly states birth_rate/mortality_rate default-untouched decision and its real-world meaning | Step 2 (decision made and documented in code comment), Step 7 (doc), and must also be copied into the ticket's own `## Implementation Notes` section at implementation time | Rate-default guard assertion in `test_compiler_seeds_population_cohorts_from_spec` (assert `cohort.birth_rate == 0.02`, `cohort.mortality_rate == 0.01`) |

## Anti-Drift Notes

- **Distribution ratio is now resolved: 30/50/20 (young/adult/elder), documented with
  rationale in Step 2.** Do not silently change these numbers without updating both the
  code comment and `docs/world/demographics_contract.md` (Step 7) — a divergence between
  the two would violate the Authoritative Mechanics Rule's doc/code parity requirement.
- **Rounding is now resolved: largest-remainder (Hamilton apportionment), fixed
  tie-break priority `["young", "adult", "elder"]`.** This is deterministic and RNG-free
  by construction — do not introduce an RNG draw here even for tie-breaking; the fixed
  priority order already makes ties deterministic.
- **Insertion point is now resolved:** the aggregation pre-pass (Step 1) goes
  immediately before the existing step-2 region-construction loop
  (`compiler.py:209-211`), not after step 6, and not via `dataclasses.replace()`
  post-construction. This was the investigation's flagged structural question — it is
  settled by this plan, not left for the implementer to decide.
- **`birth_rate`/`mortality_rate` decision is now resolved: leave dataclass defaults
  (`0.02`/`0.01`) untouched.** Rationale: this ticket's job is "seed the guard, don't
  rebalance the numbers" — no evidence or requirement exists to justify deviating from
  the existing, already-tested per-200-tick-cycle defaults, and doing so would touch
  `docs/mechanics/05_world_evolution.md` unnecessarily, expanding scope. The real-world
  (calendar) meaning of these rates remains exactly what it already was before this
  ticket — "per 200-tick cycle," per `cohort.py:31-34`'s existing doc comments — this
  ticket does not add, remove, or reinterpret that meaning; it only supplies the initial
  `count` values the existing rates apply to going forward. This satisfies AC 5's
  "either way, state it explicitly" requirement.
- **Zero-`PopulationSpec` representation is now resolved: empty dict `{}`, not three
  zero-count cohorts.** This is the only representation that satisfies the ticket's
  literal "the guard correctly no-ops" wording (an empty dict is falsy and hits the
  `continue` at `cohort.py:349` directly; three zero-count cohorts would not be falsy and
  would instead flow into the birth/death loop, still correctly producing zero net
  changes, but via a different, less literal code path — investigation.md "Zero-
  PopulationSpec edge case" flags this distinction explicitly).
- **Do not conflate `PopulationSpec.count` (step 6's entity-spawn count) with the cohort
  seeding total** — they represent the same number by construction (both derive from the
  same `spec.entities` sum) but must be computed independently. Do not wire cohort
  seeding off `len(entities)` counted after step 6 runs — this would silently break if
  step 6's spawn loop is ever short-circuited by placement constraints in the future
  (investigation.md "Anti-Drift Hazards").
- **Multiple `PopulationSpec` entries per region is real and common, not a hypothetical
  edge case** — `test_compiler_seeds_population_cohorts_from_spec` must include a fixture
  with 2+ `PopulationSpec` entries sharing one `spawn_region`, proving true aggregation
  rather than 1:1 pass-through.
- **The `<3000`/`<7000`/`≥7000` tick-based age-bracket thresholds are not owned by this
  ticket and must not be treated as permanent or reworked here** — per the ticket's own
  Temporal-axis caution, this ticket seeds counts into the existing buckets, not the
  buckets themselves.

## Deviations (recorded during implementation, 2026-09-01)

- **Step 5's "reuse existing spec-construction helpers" claim was inaccurate.** The plan
  stated Step 5 should mirror "the same spec-construction helpers already used in
  [`tests/integration/scenarios/test_demographics.py`] for WORLD-DEMO-002/WORLD-DEMO-005."
  On inspection at implementation time, that file has no `WorldSpec`/`WorldCompiler`
  helpers at all — every existing test in it (including the ones backing WORLD-DEMO-002
  and WORLD-DEMO-005) hand-builds `RegionState`/`AuthoritativeState` directly via a local
  `_make_region`/`_make_state` helper. This is itself the exact gap the ticket exists to
  close (the ticket's own Request Summary states "every existing test hand-constructs
  RegionState bypassing the compiler"), so there was nothing to reuse. Implementation
  added a new local helper `_build_population_seeding_world_spec()` in that file, modeled
  on `create_base_valid_spec()` from `tests/unit/worldbuilding/test_world_compiler.py`,
  and imported `WorldCompiler`/`WorldSpec` into the integration test file for the first
  time. No change to the plan's actual algorithm/wiring steps (1-3) resulted from this —
  only to how Step 5's test fixture was built.
- **Integration test population size.** The plan did not specify a `PopulationSpec.count`
  for Step 5's test. Implementation used `count=1000` (not a small demo number) because
  `DemographicCycleService`'s `int(births - deaths)` truncation (`cohort.py:358`) produces
  `net == 0` for every bracket at small totals under the 30/50/20 split and the
  0.02/0.01 rates (confirmed by first writing the test with `count=50`, which failed with
  `result.is_noop() == True` even though the guard itself was correctly passed) — this
  would make the "guard proceeds and returns a real StateUpdate" assertion pass or fail
  for the wrong reason. `count=1000` seeds young=300/adult=500/elder=200, each safely
  above the ~100-count threshold where net birth/death first becomes nonzero at these
  rates. Region bounds were widened to 60x60 to keep this well clear of the unrelated
  LAW-SPAWN-OCCUPANCY collision-reroll path.
- **Step 6 tooling workaround.** `tools/parity_ledger_writer.py`'s `_ID_PATTERN`
  (`^[A-Z]+-[0-9]{3}$`) rejects multi-segment IDs like `WORLD-DEMO-006` — and, confirmed
  by direct regex test, rejects all 5 pre-existing sibling entries already in
  `docs/parity_ledger/world_dynamics.yaml` (`WORLD-DEMO-001`..`005`) too. This is a
  pre-existing bug in the writer (and in `docs/parity_ledger/schema.json`'s own declared
  `id.pattern`, which the writer mirrors), not introduced by and not in scope for this
  ticket. Implementation hand-reproduced `write_entry()`'s exact validated
  read-modify-write-and-rebuild logic (manually checking every other `validate_entry()`
  rule) rather than either inventing an off-convention ID or blocking the ticket on an
  unrelated tool defect, then ran the required separate `python3 tools/parity_index.py
  build` Bash call per `.claude/agents/parity-updater.md` convention. `git diff --stat`
  confirms a clean pure-append to the ledger shard. A follow-up ticket is recommended to
  fix `_ID_PATTERN` (and `schema.json`'s `id.pattern`) to accept the established
  multi-segment convention.
