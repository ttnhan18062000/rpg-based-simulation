---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260831-POPULATION-COHORT-SEEDING
artifact_type: investigation
tags: [world]
---

# Investigation — TCK-20260831-POPULATION-COHORT-SEEDING

## Current Behavior

### `WorldCompiler.compile()` — `src/worldbuilding/compiler.py`

- Step 2 (region compile, `compiler.py:213-254`) builds `regions: Dict[str, RegionState]` by iterating `spec.regions` (`List[RegionSpec]`). The `RegionState(...)` constructor call is at `compiler.py:245-254`:
  ```python
  regions[r_spec.id] = RegionState(
      id=r_spec.id,
      name=r_spec.id.replace("_", " ").title(),
      bounds=(r_spec.bounds[0], r_spec.bounds[1], r_spec.bounds[2], r_spec.bounds[3]),
      kind=r_spec.type.upper(),
      influence=100.0 if r_spec.type == "town" else 0.0,
      owner_faction_id=owner_faction,
      hazard_level=getattr(r_spec, "hazard_level", 0.0),
      hazard_kind=getattr(r_spec, "hazard_kind", "PHYSICAL")
  )
  ```
  Confirmed: `influence` and `owner_faction_id` are set via direct keyword-argument constructor assignment, derived from `r_spec.type` (a pure/local computation, no cross-referencing of other spec lists at this point in the function). No `population_cohorts=` kwarg is passed — the field falls through to its dataclass default, an empty `dict` (`src/core/state.py:255`).
- Step 6 (entity compile, `compiler.py:352-473`) is the **only** place in `compile()` that reads `spec.entities: List[PopulationSpec]`. It iterates `for pop_idx, pop_spec in enumerate(spec.entities)`, looks up `region = regions.get(pop_spec.spawn_region)` (`compiler.py:366-367`), and for each of `pop_spec.count` iterations spawns one `EntityState` inside that region's bounds. This is the only existing code path that already associates a `PopulationSpec` with a region — there is no pre-existing per-region population aggregation anywhere in `compile()`.

**Architectural consequence for this ticket:** `RegionState` is `@dataclass(frozen=True, slots=True)` (`src/core/state.py:235`). Region construction (step 2) happens *before* any `spec.entities` list is consulted (step 6). To honor the ticket's "direct constructor assignment" instruction, the implementation must aggregate `spec.entities` by `spawn_region` (sum `count` per region id) *before or during* step 2's region-construction loop — i.e. compute a `Dict[str, int]` of region_id → declared_population ahead of/alongside the existing step-2 loop, then pass `population_cohorts=` into the `RegionState(...)` call at `compiler.py:245`. Building `RegionState` first and `dataclasses.replace()`-ing it afterward (post step 6) would still be "direct constructor assignment" in a broader sense but breaks the ticket's explicit precedent-following framing and would require rebuilding the `regions` dict entry (and any tile/warning bookkeeping keyed on region identity elsewhere) after step 6 — the cleaner path is to precompute the sum before step 2 runs. Plan should decide exactly where this precompute pass lives (e.g. a small loop over `spec.entities` immediately before the step-2 `for r_spec in spec.regions:` loop).

### `WorldSpec` / `PopulationSpec` — `src/worldbuilding/schema.py`

There is no single "declared population" scalar per region on `WorldSpec`. Instead:
- `WorldSpec.entities: list[PopulationSpec]` (`schema.py:236`) — a flat list, **not** grouped by region.
- `PopulationSpec` (`schema.py:151-162`): `id: str`, `count: int (ge=0)`, `role: str`, `faction: str`, `spawn_region: str`, `archetype_id: Optional[str] = None`. Frozen pydantic model (`ConfigDict(frozen=True)`).
- Multiple `PopulationSpec` entries can (and in realistic worlds do) target the same `spawn_region` (e.g. separate `citizen`/`worker`/`guard` population groups spawned into the same town region) — `WorldSpec.validate_unique_identifiers` (`schema.py:277-282`) only guarantees uniqueness of `PopulationSpec.id`, not uniqueness of `spawn_region`.

**Consequence:** "a region's declared population" (ticket AC 1) is not a field read directly off the spec — it must be *derived* as `sum(p.count for p in spec.entities if p.spawn_region == region_id)`. This is a concrete finding Plan needs: the AC's "region's declared population" = the per-region sum over `PopulationSpec.count`, computed fresh inside `compile()` (not a new schema field).

### `PopulationCohort` / `DemographicCycleService` — `src/domains/demographics/cohort.py`

Confirmed exact shape (`cohort.py:17-43`), `@dataclass(frozen=True, slots=True)`:

| Field | Type | Default |
|---|---|---|
| `bracket` | `str` | required |
| `count` | `int` | `0` |
| `birth_rate` | `float` | `0.02` (comment: "births per 200-tick cycle as fraction of count") |
| `mortality_rate` | `float` | `0.01` (comment: "deaths per 200-tick cycle as fraction of count") |
| `migration_threshold` | `float` | `0.7` |

No other fields exist. The 3 valid `bracket` values (by convention, not an enum — `bracket` is a plain `str`) are `"young"`, `"adult"`, `"elder"`, per `get_age_bracket()` (`cohort.py:50-65`) and the doc comment at `cohort.py:28`.

`RegionState.population_cohorts` (`src/core/state.py:255`) is `Dict[str, Any]` typed loosely at the state-model level, but every real consumer (`compute_population_density` at `cohort.py:132`, `_check_migration` at `cohort.py:245-246`, `DemographicCycleService.process_demographics` at `cohort.py:352-355`) treats it as `Dict[str, PopulationCohort]` **keyed by bracket name** — i.e. at most one `PopulationCohort` per bracket per region, matching `docs/world/demographics_contract.md` §1: "Cohorts are stored in `RegionState.population_cohorts: Dict[str, PopulationCohort]` keyed by bracket name." This means a compiler-seeded region can have at most 3 entries (`"young"`, `"adult"`, `"elder"`), each holding the *total* count for that bracket across the region — not one `PopulationCohort` per `PopulationSpec`/population group.

`DemographicCycleService.process_demographics()` (`cohort.py:328-410`):
- Off-cycle short-circuit: `if tick % DemographicCycleService.COHORT_INTERVAL != 0: return StateUpdate()` (`cohort.py:342-343`), `COHORT_INTERVAL = 200` (`cohort.py:325`).
- The guard the ticket cites: `if not region.population_cohorts: continue` — confirmed at **`cohort.py:349`** inside `for region_id, region in state.regions.items():` (`cohort.py:348`).
- Immediately after the guard passes, the birth/death loop (`cohort.py:352-364`) does `new_cohorts: Dict[str, PopulationCohort] = dict(region.population_cohorts)` then `for bracket, cohort in region.population_cohorts.items(): births = cohort.count * cohort.birth_rate; deaths = cohort.count * cohort.mortality_rate; net = int(births - deaths); ...` — this directly confirms the dict-of-bracket-to-`PopulationCohort` structural assumption above; the code would `AttributeError` on `.count`/`.birth_rate` if a bracket mapped to a bare `int` instead of a `PopulationCohort` instance.
- A second pass (`cohort.py:392-402`) runs `_check_migration` per region (also gated on the same `if not region.population_cohorts: continue`, `cohort.py:393`), merging any migration `WorldUpdate`s into the same `StateUpdate`.
- Both passes never mutate `AuthoritativeState` directly — they return a `StateUpdate`/`WorldUpdate`, consistent with `docs/mechanics/05_world_evolution.md`'s "pure decision logic" law. The **tick-time** apply path (`WorldUpdate.population_cohorts_set`, `src/core/updates.py:788`) is applied via `src/engine/apply_plan.py:124-139` (`dataclasses.replace(reg, ..., population_cohorts=pop_cohorts, ...)`), which is the "tick-time WorldUpdate.population_cohorts_set merge path" the ticket explicitly says NOT to reuse for compile-time seeding — confirmed as a real, distinct code path from the compile-time constructor call.

### Determinism precedent inside `compile()`

`compile()` uses `DeterministicRNG` (`src/platform.rng`) for: terrain-variant fill (`weighted_choice`, `compiler.py:228-233`), resource/building/entity tile placement (`get_int`, e.g. `compiler.py:303-304`), and per-entity personality/class rolls (`get_float`/`choice`, `compiler.py:422-431`). All of these draw from a genuinely stochastic design space (spatial placement, personality variance) where a *choice* must be made and RNG is the only deterministic way to make it reproducibly.

By contrast, the two closest precedents to "deriving one field from other spec values with no free stochastic choice" — `influence` (`100.0` or `0.0`, a pure function of `r_spec.type`) and `owner_faction_id` (either `None`/`Faction.HERO_GUILD` or a `context.region_ownership` lookup) — use **no RNG at all**; they are plain deterministic arithmetic/lookups. There is no existing precedent in `compile()` for using RNG to split one aggregate total into deterministic sub-counts. This directly supports (without deciding, per this ticket's scope boundary) that a **fixed proportional ratio with deterministic rounding** (no RNG draw) is sufficient and is the pattern most consistent with existing code — Plan should pick a rounding method (e.g. largest-remainder / floor-then-distribute-remainder-by-fixed-priority) that guarantees `young + adult + elder == declared_population` exactly, since floor-per-bracket alone can lose 1-2 units to integer truncation.

### Zero-`PopulationSpec` edge case

If no `PopulationSpec` in `spec.entities` has `spawn_region == region.id` (either because `spec.entities` is empty entirely, or none target that region), the derived per-region declared population is `0`. Two sub-cases for Plan to be explicit about:
- **No aggregation entry for the region at all** → `population_cohorts` stays the dataclass default `{}` (empty dict) unless the implementation always builds 3 zero-count `PopulationCohort` entries. Both compile without crashing today (confirmed: `RegionState.population_cohorts` has a `default_factory=dict`, `state.py:255`, and nothing in step 2 or step 6 requires it to be non-empty).
- The `cohort.py:349` guard (`if not region.population_cohorts: continue`) is a plain truthiness check — an empty `dict` (`{}`) is falsy in Python, so it correctly no-ops with **zero risk of crash or exception**, regardless of which of the two zero-population representations the implementation picks (empty dict, or 3 cohorts all with `count=0` — note: a dict of 3 zero-count cohorts is *not* falsy, so it would **not** hit the `continue` and would instead flow into the birth/death loop with `net = int(0*0.02 - 0*0.01) = 0` → `if net == 0: continue` per-bracket, `cohort.py:359-360`, which also correctly no-ops with zero events emitted, zero updates written. Plan must pick one representation and Implementation Notes must record which — they are both technically safe, but only the empty-dict form satisfies the literal ticket wording "the guard correctly no-ops.").

## Mechanics / Engine Constraints

- **`docs/world/demographics_contract.md`** (Certified Level 1 Authoritative) §1 is the binding contract for `PopulationCohort`'s shape and the `Dict[str, PopulationCohort]`-keyed-by-bracket structure — any seeding logic must produce state matching this shape exactly (see "Docs Requiring Update" below for why this doc itself is not expected to change).
- **`docs/mechanics/05_world_evolution.md` §5 "Demographic Cohort Cycle"** documents the same birth/death formula and the "runs every 200 ticks" cadence — the seeding logic itself does not alter this formula, but the seeded `birth_rate`/`mortality_rate` values (if the implementer chooses to override the `0.02`/`0.01` defaults) would need this chapter's cross-reference kept consistent per the Authoritative Mechanics Rule.
- **Determinism law** (`docs/core/state.md` immutability law, `docs/engine/kernel.md`'s deterministic loop contract): `compile()` must be a pure, reproducible function of `(spec, seed)`. Since the fixed distribution ratio is proposed as pure arithmetic (no RNG draw), this is straightforward to satisfy — but Plan must still confirm the exact rounding algorithm produces byte-identical results across two `compile()` calls with the same seed (trivially true for pure arithmetic, but worth an explicit test per the ticket's own AC 3).
- **Frozen-dataclass constraint**: `RegionState` (`src/core/state.py:235`, `frozen=True, slots=True`) cannot be field-mutated after construction — reinforces that seeding must happen via constructor kwarg at `compiler.py:245-254`, not via post-hoc attribute assignment.

## Docs Requiring Update

- `docs/world/demographics_contract.md`: currently states the model only as it is populated by `DemographicCycleService`/migration/tick-time mechanics (§1-§5); it has no section describing how `population_cohorts` gets its *initial* (compile-time) values, or the fixed young/adult/elder distribution ratio this ticket must author. Once this ticket lands, the ratio and the compile-time seeding mechanism become real, certified-doc-relevant behavior (a "brand-new feature" per this agent's instructions, treated the same as a behavior change) and need a new subsection (e.g. "0. Compile-Time Seeding" before the existing "1. PopulationCohort Model", or a new "§8 Compile-Time Seeding").
- `docs/parity_ledger/world_dynamics.yaml`: needs a new entry (next free ID in the `WORLD-DEMO-` numbering is `WORLD-DEMO-006`, since `WORLD-DEMO-001` through `WORLD-DEMO-005` are already used — confirmed via full `id:` grep of the file) documenting the compile-time seeding behavior (fixed ratio, rounding rule, zero-PopulationSpec no-op), with `status: verified`, `priority: P1` (matching the sibling WORLD-DEMO-* entries) and a real `test_path` pointing at whichever new compiler-driven test(s) Plan/Implementer land.

The `docs/mechanics/05_world_evolution.md` §5 doc (path: `docs/mechanics/05_world_evolution.md`) is not required to change for this ticket unless the implementer chooses non-default `birth_rate`/`mortality_rate` seed values — the existing chapter already correctly documents the per-200-tick-cycle birth/death formula and cadence, which this ticket does not alter. If Implementation Notes records that seeded cohorts keep the dataclass defaults (`0.02`/`0.01`) untouched, no update to this chapter is needed. **Resolved during implementation, condition not met** should be added to this line (or a corresponding investigation/plan note) if the implementer confirms defaults were left untouched; if instead new non-default rate values are chosen, this doc DOES need updating and Plan should re-flag it as a Format 1 bullet at that point.

The `docs/brainstorm/rpg_expected_schemas.html` doc (path: `docs/brainstorm/rpg_expected_schemas.html`, under `docs/`) is not required to change for this ticket: it is a brainstorm-tier reference (not Certified/authoritative) that the ticket's own "Assumptions/Open Questions" section cites only to confirm the real class name is `PopulationCohort`; this ticket does not add or rename any class, so nothing in that doc becomes stale.

## Parity Ledger Overlap

`docs/parity_ledger/world_dynamics.yaml` entries `WORLD-DEMO-001` through `WORLD-DEMO-005` (all `status: verified`, `priority: P1`) cover migration, age-bracket classification, elder modifiers, and the density signal — all *consumers* of `population_cohorts` once populated. None of the five existing entries covers compile-time seeding; this is a genuine gap, confirmed by reading every `WORLD-DEMO-*` entry's `text` field (`docs/parity_ledger/world_dynamics.yaml:1132-1206`). A new `WORLD-DEMO-006` entry is required (see "Docs Requiring Update"). None of the 5 existing entries are P0, so none *require* a passing `test_path` as a hard gate for this ticket, but `WORLD-DEMO-001` and `WORLD-DEMO-005`'s `test_path`s (`tests/integration/scenarios/test_demographics.py::test_cohort_migrates_on_scarcity`, `tests/integration/scenarios/test_demographics.py::test_high_population_region_higher_resource_demand` — file confirmed to exist) are worth re-running as regression coverage since this ticket is, for the first time, the reason those cohorts could plausibly originate from `compile()` rather than a hand-built fixture in a future scenario test.

## Prior Work

- `stored_artifacts/TCK-20260619-E52A-COHORT-MODEL/` (investigation.md, plan.md, test_plan.md) — built `PopulationCohort` + `DemographicCycleService`'s birth/death cycle. Grepped its investigation.md for `compile`/`WorldCompiler`/`seed` — **zero matches**. Confirms compile-time seeding was never in scope or even mentioned as a follow-up in the original cohort-model ticket; this ticket is genuinely the first to address it.
- `stored_artifacts/TCK-20260619-E52B-MIGRATION/`, `TCK-20260619-E52C-AGE-ADVANCEMENT/`, `TCK-20260619-E52D-DENSITY-SIGNAL/` — all downstream consumers of `population_cohorts`, all built and tested against hand-constructed `RegionState` fixtures (see "Existing Tests" below); none touch `compile()`.
- `stored_artifacts/TCK-20260523-WORLD-COMPILER/` — the original `WorldCompiler` ticket (found via `docs/REGISTRY.yaml` path match `tickets/done/TCK-20260523-WORLD-COMPILER.md`). Predates the cohort model entirely (2026-05-23 vs. cohort model's 2026-06-19), so it could not have anticipated `population_cohorts` — consistent with the current gap.

## Risks and Open Questions

- **Distribution-ratio authorship is explicitly out of scope for Investigate** (per this ticket's own scope and the dispatching agent's instructions) — Plan must choose and document the young/adult/elder split. This investigation only establishes that (a) no anchor exists anywhere in code/docs, and (b) the split must be pure arithmetic (no RNG) to stay consistent with the rest of `compile()`.
- **Rounding-to-exact-total is a real correctness risk**, not just a cosmetic one: AC 1 explicitly requires "counts summing to the region's declared population." A naive `int(declared_population * ratio)` per bracket will under-count by 0-2 units whenever the multiplication doesn't divide evenly. Plan needs a specific remainder-assignment rule (e.g. give the remainder to the largest-ratio bracket, or to a fixed bracket like `"adult"`) — this is a concrete design decision, not just an implementation detail, since it affects reproducibility documentation.
- **Where exactly the spec.entities aggregation pass lives inside `compile()`** is an open structural question this investigation flags but does not resolve (see "Current Behavior" above) — Plan should specify the exact insertion point (a new small loop before the step-2 region loop, reusing `spec.entities` which is already fully available at function entry since it's just `spec.entities`, no ordering dependency on any other compile step).
- **`birth_rate`/`mortality_rate` seed-value meaning** (ticket AC 5, already flagged as settled guidance in the ticket's own Assumptions section) — this investigation additionally confirms via direct code read that the fields' doc comments (`cohort.py:31-34`, "per 200-tick cycle") are exactly what the ticket describes; no new finding here beyond confirming the settled ticket text is accurate.
- **Multiple `PopulationSpec` entries per region is real and common** (not a hypothetical edge case) — any test fixture used for AC 1 should include at least one region with 2+ `PopulationSpec` entries sharing a `spawn_region`, to prove the aggregation-then-split logic (not just a 1:1 pass-through) is what's actually implemented.

## Anti-Drift Hazards

- **Do not conflate `PopulationSpec.count` (raw entity spawn count, step 6) with the cohort seeding total.** They must represent the *same* number (a region's declared population = sum of `PopulationSpec.count` for that `spawn_region`) but are two independent things: step 6 spawns that many real `EntityState` objects; the new cohort-seeding logic separately writes an *abstract* `population_cohorts` total. It would be easy to accidentally wire the cohort seed off of `len(entities)` counted post-step-6 instead of the pre-aggregated spec sum, which would silently break if step 6's spawn loop is ever short-circuited (e.g. LAW-SPAWN-OCCUPANCY warnings, which only affect *placement*, not count, today — but a future change could).
- **Do not touch step 6's entity-spawning loop.** This ticket's scope is region-level `population_cohorts` seeding only; the ticket's "Out of Scope" explicitly excludes downstream consumers and the separate `age_ticks` defaulting gap (`.lifecycle(age_ticks=...)` never called) — do not "fix" that adjacent gap opportunistically while touching this file.
- **Do not use `dataclasses.replace()` on an already-built `RegionState` as a post-hoc patch after step 6** — this contradicts the ticket's explicit "direct constructor assignment" instruction and its stated rationale (following the `influence`/`owner_faction_id` precedent), and would be a real, reviewable deviation from scope, not just a style choice.
- **Do not let the fixed ratio's rounding silently break the "sums to declared population" AC** for small counts (e.g. `declared_population=1` or `2`) — a naive per-bracket floor could leave 1 unit permanently missing. Any chosen algorithm must be tested at small totals, not just large round numbers.
- **Do not widen `RegionState.population_cohorts`'s type** beyond `Dict[str, PopulationCohort]` keyed by bracket (e.g. do not key by `PopulationSpec.id` or population group) — this would break every existing consumer (`compute_population_density`, `_check_migration`, `DemographicCycleService.process_demographics`), all of which assume at most 3 entries keyed by `"young"`/`"adult"`/`"elder"`.
