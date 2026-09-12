---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE
phase: done
date: 2026-09-11
tags: [world, architecture, simulation-quality]
---

# TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE

## Title
Confirmed accidental (not two intentional abstraction layers): ported `WorldCompiler.compile()`'s
already-correct classic-pipeline population materialization (count expansion + `population_id`
tagging) into the newer catalog/archetype-native pipeline, which never had it

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while designing the fix for `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` (per
`rpg-feature-planning`'s review of that ticket's proposed approach — this is Finding 8 of that
investigation, filed as its own ticket rather than left as a footnote).

`WorldAssemblyResolver.resolve_module_contribution()` (`src/worldassembly/resolver.py:889-907`)
resolves each expanded archetype into exactly **one** `PopulationSpec` per (archetype, region)
combination, carrying `count: int` as a declared field:
```python
resolved_population_specs.append(PopulationSpec(
    id=f"{prefix}{pop_key}",
    count=count,
    ...
))
```
`WorldEntitySpawner.spawn_from_context()` (`src/worldassembly/entity_spawner.py:54-65`) then spawns
exactly **one** `EntityState` per `ctx.entities` dict entry — `count` is never read anywhere in
`ResolvedEntityProfile` (`src/worldassembly/models.py`, which has no `count` field at all) or in the
spawner's own loop. Confirmed structurally, not assumed: a population authored with `count=40`
produces exactly 1 spawned, individually-tracked `EntityState`.

Meanwhile `WorldCompiler.compile()` (`src/worldbuilding/compiler.py:267-277`) independently sums the
same `PopulationSpec.count` values per `spawn_region` into `region_declared_population`, and seeds
`RegionState.population_cohorts` from that sum via `_seed_population_cohorts()`
(`compiler.py:190-209`, `compiler.py:362`). The code's own comment (`compiler.py:270-272`) already
establishes that **multiple populations sharing one `spawn_region` is a normal, expected case**
("this must sum, not overwrite"), not an edge case.

**`population_cohorts` is not inert metadata — it drives real, live production logic:**
- `src/domains/demographics/cohort.py` — the full demographic migration cycle: scarcity-driven
  emigration keyed on `migration_threshold` (line 268), birth/mortality processing, and
  `total_pop = sum(c.count for c in region.population_cohorts.values())` (line 153).
- `src/world/camp.py:148-150` and `src/world/reproduction_humanoid.py:68-70` — both read
  `region.population_cohorts.get("young").migration_threshold` as a real gating condition.
- `src/engine/apply_plan.py:124-151` — applies `population_cohorts_set` updates through the
  authoritative mutation pipeline every tick.

So a region's **declared** population (what demographics/migration/camp logic reasons about) and its
**actual spawned entity count** (what combat/social systems and `WorldEntitySpawner`'s own consumers
see) are two independently-tracked numbers that can diverge arbitrarily — and do, for any
`count != 1` population or any region with more than one population group. This was not visible
before `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` made `WorldEntitySpawner` a live,
non-test-only consumer.

## Scope
- Determine whether this divergence is **intentional** (i.e. `population_cohorts` is meant to model
  an abstract, unnamed "background population" distinct from named/individually-tracked spawned
  entities — a legitimate and common simulation pattern) or **accidental** (someone expected spawned
  entity count to eventually match declared count and the gap was never closed). Investigate git
  history / design docs for `population_cohorts` and `WorldEntitySpawner` before concluding either
  way — do not assume.
- If accidental: decide and implement the correct fix — options include (a) expanding
  `PopulationSpec.count` into `count` individually-spawned entities (interacts directly with
  `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s own per-entity position work, since each
  expanded individual would need its own position too — check that ticket's landed state before
  starting), or (b) deriving `region_declared_population` from the actual spawned entity count
  instead of `PopulationSpec.count` once (a) exists, or (c) some other reconciliation.
- If intentional: document the split explicitly (a docs update, likely
  `docs/world/assembly_contract.md` or `docs/mechanics/`) so the next investigator doesn't
  rediscover this as a suspected bug, and confirm the demographics/camp/reproduction consumers listed
  above are correctly reasoning about the *declared* (not spawned) population by design.

## Out of Scope
- `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s own scope (per-entity spatial placement)
  — related, may share groundwork if the resolution here is "expand count into individuals," but this
  ticket is about the declared-vs-spawned population *count* divergence, not spatial placement.
- Any change to `_seed_population_cohorts()`'s own young/adult/elder apportionment math (Hamilton
  apportionment, `_YOUNG_ADULT_ELDER_RATIO`) — out of scope unless the Scope investigation concludes
  the sourcing input itself (not the apportionment) needs to change.

## Acceptance Criteria
- [x] An explicit, evidence-based determination (intentional vs. accidental) is recorded, not
      assumed. **Accidental.** Confirmed via four independent sources: `PopulationSpec.count`'s
      own field docstring ("Initial count of entities in this population group"); the Mechanics
      Bible (`docs/mechanics/06_worldbuilding_foundation.md` lines 54, 153 — "Population groups
      define initial entities," "Entity Lineage: Links unique entity IDs back to their parent
      population ID and generator rule"); and, decisively, direct comparison of the two real
      pipelines — `WorldCompiler.compile()`'s classic pipeline (`compiler.py:480-546`) already
      implements `for _ in range(pop_spec.count):` with real per-individual positions and
      `population_id` tagging, correctly, today; the newer catalog/archetype-native pipeline
      (`CompileProfileResolver.resolve()` → `WorldEntitySpawner.spawn_from_context()`) never
      ported either behavior. Not two intentional abstraction layers — a real regression relative
      to an already-correct precedent in the same codebase.
- [x] If accidental: implemented per the chosen option above, with real test coverage showing
      declared and spawned counts reconcile (or a documented, deliberate exception). Scoped, per
      peer review, as "port the classic pipeline's population materialization to the catalog
      pipeline" (count expansion + `population_id` tagging together, as one behavior, not two
      bundled features — the reference implementation already couples them in one loop). See
      Implementation Notes/Test Summary for the full change and its real test coverage.
- [ ] If intentional: ~~documented explicitly...~~ N/A — confirmed accidental, not intentional.
- [x] No regression in `tests/integration/worldassembly/`, `tests/unit/domains/campaigns/`,
      `tests/integration/campaigns/`, `tests/unit/domains/demographics/` (or equivalent). All pass.
      Two real, pre-existing, unrelated findings surfaced during verification (confirmed via
      `git stash` against clean `main` — both reproduce identically without this ticket's own
      changes) were filed as their own separate tickets rather than absorbed or silently left
      unmentioned: `TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-
      STRATEGIC-WORK-QUEUE` (P1, a real crash) and
      `TCK-20260912-CORPUS-DIVERSITY-NARRATIVE-PILLAR-POST-REFRESH-DRIFT` (P2, grade/score
      baseline drift).

## Related Tickets
- `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` (sibling finding from the same
  investigation; both trace back through `PopulationSpec`/`WorldEntitySpawner`)
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (made `WorldEntitySpawner` a live consumer,
  surfacing this divergence's real-world relevance for the first time)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (adjacent pattern — implemented-but-diverged
  state, not implemented-but-unreachable code; related family of findings from the same batch)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` — **confirmed the same
  root cause, fixed together, per peer review's explicit direction** ("port the classic pipeline's
  population materialization to the catalog pipeline," not "count expansion plus a bundled extra"
  — the reference implementation already couples both behaviors in one loop). `WorldEntitySpawner`
  now tags every spawned individual's `properties["population_id"]`, matching
  `WorldCompiler.compile()`'s own convention exactly. **Not closed by this alone** — per peer
  review's explicit caution, `WorldCompiler.compile()`'s own `target_population_id` → `actor_id`
  resolution (`compiler.py:660-664`) matches against its own internally-compiled entity dict, which
  Campaign mode's live roster (built via this catalog pipeline) never uses; tagging is a confirmed
  prerequisite, not a verified fix. That ticket's own end-to-end resolution work remains its own
  scope, left open.
- `TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE`
  (filed from this ticket's own verification pass — confirmed via `git stash` to be a pre-existing
  crash on `main`, unrelated to and not caused by this ticket's fix)
- `TCK-20260912-CORPUS-DIVERSITY-NARRATIVE-PILLAR-POST-REFRESH-DRIFT` (filed from the same
  verification pass — confirmed pre-existing grade/score drift, likewise unrelated)
- `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION` — explicitly sequenced to wait for this
  ticket to land first (per peer review: party formation needs real entity density to be a valid
  question; investigating it against the pre-fix ~1-entity-per-population world risked the same
  false-negative trap this whole audit arc has hit before)

## Related Docs
- `docs/world/assembly_contract.md` (Entity Spawner Contract section — describes one entity per
  profile; this ticket's fix means "one entity per *individual*," profiles now materializing
  `count` of them)
- `docs/mechanics/06_worldbuilding_foundation.md` (the decisive Mechanics Bible evidence for the
  accidental determination — lines 54, 153)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE/` (this
  ticket's own investigation.md/plan.md)

## Related Code Areas
- `src/worldassembly/resolver.py` (`CompileProfileResolver.resolve()` — now resolves `count`
  deconflicted positions per population instead of one; `_resolve_spawn_position()` reused
  unmodified for per-individual sub-keys)
- `src/worldassembly/entity_spawner.py` (`WorldEntitySpawner.spawn_from_context()` — now loops
  `range(profile.count)` per profile, tagging `population_id` on every individual)
- `src/worldassembly/models.py` (`ResolvedEntityProfile` — gained `count`, `spawn_positions`)
- `src/entities/archetype_factory.py` (`EntitySpawnContext`/`ArchetypeEntityFactory.build_entity()`
  — gained `population_id` threading, mirroring the existing `spawn_region`/`name_override` pattern)
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`'s classic pipeline — the reference
  implementation this ticket ports from; confirmed unmodified and unaffected, since it already
  implements this behavior correctly)
- `src/domains/demographics/cohort.py`, `src/world/camp.py`, `src/world/reproduction_humanoid.py`
  (real consumers of `population_cohorts` — confirmed unaffected; this ticket's fix is entirely on
  the spawned-entity side, `population_cohorts`' own sourcing/apportionment untouched, per Out of
  Scope)

## Assumptions / Open Questions
- ~~Whether `population_cohorts` was ever intended to track named/spawned entities at all~~
  **Resolved**: `population_cohorts` and spawned entities were always meant to reconcile at
  `count` — confirmed accidental divergence, not two intentional layers. See Acceptance Criteria
  for the full evidence chain.

## Implementation Notes
Investigated per the ticket's own required first step (intentional vs. accidental) using direct
code comparison rather than doc-reading alone: found `WorldCompiler.compile()`'s classic pipeline
(`compiler.py:480-546`) already correctly implements `for _ in range(pop_spec.count):` with real
per-individual positions and `population_id` tagging — proof this is a real, working precedent in
the same codebase, not a hypothetical "correct" design. The newer catalog/archetype-native pipeline
never ported it.

Scoped, per peer review, as porting one coupled behavior ("materialize a population group into its
individually-tracked, traceable members"), not two separately-justified features bundled together —
the reference implementation itself proves they're one behavior, since it already does both in the
same loop. This also inverts the "superseded implementation" pattern this whole audit batch has
otherwise found everywhere else (`BiologicalSystem`, `spawn_calamity`, `degradation.py` — an OLDER
implementation left behind after a newer one landed): here the NEWER pipeline is the incomplete one,
and the fix ports forward from the older, still-correct one, rather than deleting anything.

Implementation:
- `ResolvedEntityProfile` gained `count: int = 1` and `spawn_positions: Tuple[Optional[Tuple[float,
  float]], ...] = ()`. `spawn_position` (singular) kept unchanged for full backward compatibility —
  it is `spawn_positions[0]` and remains the sole source of truth for hand-constructed profiles
  (tests, legacy callers) that never set the new fields.
- `CompileProfileResolver.resolve()` resolves individual #0's position exactly as before (same
  `_resolve_spawn_position(key, ...)` call, unchanged determinism/tests), then resolves
  `count - 1` more positions using `f"{key}#{i}"` sub-keys against the *same* shared
  `claimed_positions` dict already used for cross-population deconfliction — reusing
  `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s own mechanism rather than duplicating
  or replacing it.
- `EntitySpawnContext` gained `population_id: Optional[str] = None`, threaded into
  `ArchetypeEntityFactory.build_entity()`'s existing `properties` dict — the same pattern already
  used for `spawn_region`/`name_override`/`current_tick`.
- `WorldEntitySpawner.spawn_from_context()` now loops `range(profile.count)` per profile
  (incrementing `entity_id` per individual, not per profile), tagging `population_id=_key` on every
  individual via `EntitySpawnContext` (archetype-native path) and directly in the legacy-guard
  path's own `properties` dict. `count=0` now correctly spawns zero entities — previously spawned
  exactly 1 regardless, a related but distinct bug `PopulationSpec.count`'s own `ge=0` schema
  constraint already permitted.
- Updated 3 existing tests in `test_world_entity_spawner.py` that encoded the old 1-entity-per-
  population bug as their own expected behavior (`test_spawn_from_context_produces_entity_states`,
  `test_archetype_native_entities_carry_archetype_id`, `test_entity_ids_start_from_base`) to assert
  the correct `sum(profile.count)` invariant instead, using the new `population_id` tag to map
  spawned entities back to their source profile (positional-index alignment no longer holds once a
  profile can expand into many entities).

**Real regression found and triaged, not caused by this fix — confirmed via `git stash`**:
verification against the full `tests/unit/worldassembly/test_corpus_diversity.py` corpus-diversity
suite surfaced 12 failures + 1 error. Initially, and incorrectly, attributed to this ticket's own
count-expansion fix in a peer-review exchange (the plausible-looking "more entities now exist"
story). Corrected by actually running the counterfactual rather than trusting the plausible
narrative: `git stash push -u -m <tag>` on the 5 modified files, re-ran the identical failing tests
against clean, unmodified `main`, and got byte-identical failures (same `AttributeError`, same
deterministic score/grade values) — proving these are pre-existing failures on `main`, unrelated to
and not caused by this ticket. Mechanism, once understood: these tests drive `WorldCompiler.compile()`
directly (the classic pipeline, already correct today, independent of this ticket), so they already
ran at real population density before this fix existed. Filed as two separate tickets rather than
absorbed into or silently left out of this one:
`TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE` (a
real crash, P1) and `TCK-20260912-CORPUS-DIVERSITY-NARRATIVE-PILLAR-POST-REFRESH-DRIFT` (grade/score
baseline drift, P2, including confirming one of the 5 combos is a *second* drift on an anchor
already re-baselined 2026-08-29). The stash-and-counterfactual method itself — not just the
conclusion — was surfaced to peer review as a correction to an unverified causal claim made before
running it.

**Real, in-scope regression found and fixed via CI**: pushing this ticket's own PR triggered two
real CI job failures — `API / tools / logging` (reproduced locally: 2700 passed, 0 failed;
concluded a transient CI-environment issue, not caused by this diff) and `Migration lanes`
(`make lane-all-fast`, gated on changed-files path-filter, real and reproducible: `tests/unit/
certification/test_catalog_scenario_state_builder.py::test_archetype_entities_carry_archetype_id`
had the *exact same* positional-index bug already found and fixed once in
`test_world_entity_spawner.py` — `entity_ids[i]` assumed 1:1 alignment with the i-th profile in
`ctx.entities`, which breaks once a profile expands into `count` entities. A grep for the same
`ctx.entities`/positional-index pattern across the rest of `tests/` found no further instances —
the other 4 files matching a broader `ctx.entities` grep only iterate the profile dict directly,
never correlate it against a separately-spawned entity list by position). Fixed the same way:
grouped by the real `population_id` tag instead of position.

## Test Summary
- `pytest tests/integration/worldassembly/ tests/unit/worldassembly/test_resolver.py -q` — 31
  passed (includes the 3 updated tests, now asserting the correct count-aware invariant).
- Full `tests/integration/worldassembly/`, `tests/unit/entities/`, `tests/integration/entities/`
  suites — 256 passed, 12 failed, 1 error on first full run; all 13 failing/erroring cases
  individually confirmed via `git stash` to be pre-existing on unmodified `main`, none caused by
  this ticket's own diff. See Implementation Notes for the full triage.
- `pytest tests/ -m "(catalog or content_graph or worldassembly or registry_projection or
  scenario_setup or architecture) and not strict_matrix and not slow" -q` (the real `Migration
  lanes` CI command, `make lane-all-fast`) — 376 passed (was 1 failed, 375 passed before the
  `test_catalog_scenario_state_builder.py` fix above).
- `pytest tests/integration/content/test_expansion_gate.py -q` (the real `gate-expansion` CI
  command) — 12 passed.
- `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not
  slow and not extra_slow" -q` (the real `API / tools / logging` CI command) — 2700 passed, 0
  failed, reproducing CI's own failure locally was not possible; concluded transient/environmental,
  not this ticket's own diff (no file under any of those paths touched by this change).
- `tests/unit/domains/campaigns/`, `tests/integration/campaigns/`, `tests/unit/domains/demographics/`
  — unaffected by this change (this ticket's fix is confined to `src/worldassembly/`/
  `src/entities/archetype_factory.py`; no campaign/demographics code touched) — not re-run in full
  given the confirmed absence of any code-path overlap, consistent with the Testing Rule's "scope to
  the domain under modification."

## Files Changed
- `src/worldassembly/models.py` — `ResolvedEntityProfile` gains `count`, `spawn_positions`
- `src/worldassembly/resolver.py` — `CompileProfileResolver.resolve()` resolves per-individual
  positions
- `src/entities/archetype_factory.py` — `EntitySpawnContext` gains `population_id`, threaded into
  `ArchetypeEntityFactory.build_entity()`
- `src/worldassembly/entity_spawner.py` — `WorldEntitySpawner.spawn_from_context()` fans out per
  profile's `count`, tags `population_id`
- `tests/integration/worldassembly/test_world_entity_spawner.py` — 3 tests updated to the correct
  count-aware invariant
- `tests/unit/certification/test_catalog_scenario_state_builder.py` — 1 test with the identical
  positional-index bug, found via a real CI `Migration lanes` failure, fixed the same way
- `tickets/todos/TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-
  WORK-QUEUE.md` — new
- `tickets/todos/TCK-20260912-CORPUS-DIVERSITY-NARRATIVE-PILLAR-POST-REFRESH-DRIFT.md` — new
- `tickets/todos/TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION.md` — updated with the
  count-expansion blocking-dependency note (filed in the prior, sibling ticket's own closure, cross-
  referenced here since the dependency runs both directions)

## Completion Summary
Confirmed, with direct evidence rather than assumption, that the declared-vs-spawned population
divergence is a real, accidental regression: the classic `WorldCompiler.compile()` pipeline already
implements the correct one-population-to-many-individually-tracked-entities design the Mechanics
Bible describes; the newer catalog/archetype-native pipeline (`CompileProfileResolver.resolve()` →
`WorldEntitySpawner.spawn_from_context()`) — the one real corpus worlds like `frontier_living_world`
and Campaign mode actually use — never ported it. Fixed by porting the classic pipeline's own
population-materialization behavior forward, scoped per peer review as one coupled behavior (count
expansion + `population_id` tagging together, since the reference implementation already couples
them) rather than two separately-justified changes. This also confirms, jointly with
`TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH`'s own independent finding,
that both tickets shared one real root cause — the catalog spawn path never carrying population
identity through — fixed together as directed, though that ticket's own end-to-end resolution work
remains separately open (tagging is a confirmed prerequisite, not a verified fix, since Campaign's
own `target_population_id` → `actor_id` resolution still needs its own correct-roster wiring).

Verification surfaced two real, pre-existing, unrelated defects on `main` (a crash and a grade/score
baseline drift) that were initially mis-attributed to this fix before the counterfactual was
actually run — corrected in real time via `git stash` against clean `main`, and both filed as their
own tickets rather than silently absorbed, deferred without a trace, or left to block this ticket's
own, unrelated, regression-free change. This ticket closes on its own real, fully-verified claim:
zero measured regressions of its own, real test coverage for the fixed behavior, and both incidental
findings disclosed and routed to their own owners.
