---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION
phase: done
date: 2026-09-19
tags: [performance, bug, determinism]
---

# TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION

## Title
`src/perf/scenarios.py::build_metropolis_state()`'s entity-repositioning step places multiple
entities on the identical tile by construction — a real, structural defect in the perf-harness
scenario builder itself, distinct from the already-fixed `WorldCompiler` spawn-collision bug

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Discovered as a disclosed-but-unchased limitation while root-causing
`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`: running a real instrumented
`Kernel` against `build_metropolis_state(entity_count=1000, region_count=50,
buildings_per_region=20, seed=42)` logs abundant `HardLawMonitor` `LAW-SPAWN-OCCUPANCY` /
`LAW-OCCUPANCY-COLLISION` alerts (e.g. "entity 1 and entity 101 both occupy this space") at
world-construction time, before any tick runs. This makes `metropolis`'s own entity task/liveness
state unrepresentative and unreliable as a scenario for any investigation that depends on
per-entity position/occupancy being real (that investigation used it only as an intended control
and disclosed the anomaly rather than trusting it).

**Root-caused in this session, by direct code reading, not left as a bare observation**:
`build_metropolis_state()`'s own step 5 (`src/perf/scenarios.py:375-392`, comment: "Distribute
entities into regions... We should spread them out for a better test") unconditionally overwrites
every entity's position with a formula derived purely from `i` (the enumeration index over
`entities.values()`) and `region_count`:

```python
for i, entity in enumerate(entities.values()):
    r_idx = i % region_count
    region = regions[f"region_{r_idx}"]
    new_pos = (
        region.bounds[0] + 5.0 + (i % 10) * 5,
        region.bounds[1] + 5.0 + (i // 10) % 10 * 5,
    )
```

The local in-region offset `(i % 10, (i // 10) % 10)` has period 100 in `i`. With the default
`region_count=50`, `100 % 50 == 0`, so for any `i` and `i + 100`: `r_idx` is identical (adding a
multiple of 50 doesn't change `i % 50`) **and** the local offset is identical (both terms have
period 100). This means every entity 100 apart in construction order lands on the exact same
absolute tile, in the same region — with the default `entity_count=1000`, that's **10 entities
per colliding tile-slot**, deterministically, every time this function runs with default
parameters. This is not incidental RNG bad luck (unlike the already-fixed `WorldCompiler` bug
below) — it is a direct, provable consequence of `region_count` dividing evenly into the
offset formula's period, and reproduces on every call with the same `entity_count`/`region_count`
pairing.

**Explicitly distinct from an already-fixed, superficially similar bug**:
`TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE` root-caused and fixed the same
`LAW-SPAWN-OCCUPANCY`/`LAW-OCCUPANCY-COLLISION` signature, but in a completely different pipeline
— `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`), used by real corpus worlds
(`data/worlds/*/world.yaml` → `WorldSpec`). That ticket's own Out of Scope explicitly excluded
"`WorldEntitySpawner`'s shared-`default_position` bug" as "a separate, structurally different
pipeline" — `src/perf/scenarios.py`'s perf-harness builders (`build_idle_state`,
`build_combat_arena_state`, `build_mixed_state`, `build_metropolis_state`) are a **third**,
independent pipeline, never touched by that fix and not sharing its `_resolve_entity_spawn_tile()`
occupancy-tracking mechanism at all. This ticket's `LAW-SPAWN-OCCUPANCY` recurrence is not a
regression of that fix — it's a genuinely separate, never-fixed defect in a sibling code path.

Also explicitly distinct, despite the identical scenario name, from
`TCK-20260521-OCC-COLLISION`/`TCK-20260521-METROPOLIS-COLLISION` — those tickets fixed a runtime
raid-spawning collision in `RaidService.check_for_raid` (`src/world/raid.py`), a live-simulation
mechanic, not the perf-harness scenario builder in `src/perf/scenarios.py`. Coincidental name
overlap only; unrelated code.

## Scope
- Fix `build_metropolis_state()`'s step 5 entity-repositioning formula
  (`src/perf/scenarios.py:375-392`) so it never places two entities on the same tile, for any
  `entity_count`/`region_count` pairing the perf/cert suites actually exercise — not just the
  default 1000/50 combination that happened to be measured this session.
- Preserve determinism: the same `entity_count`/`region_count`/`seed` inputs must keep producing a
  bit-identical result across repeated calls.
- Follow the existing, already-reviewed pattern from
  `TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE`'s fix
  (occupancy-tracking set + deterministic reroll/raster-scan fallback) rather than inventing a new
  mechanism, unless investigation shows a simpler fix is sufficient given this formula's fully
  deterministic (non-RNG) nature — e.g. an offset scheme whose period does not divide evenly into
  `region_count`, or an explicit occupied-tile check per entity as it's placed.
- Verify via the real `HardLawMonitor.check_initial_placement()` detection call (the same
  mechanism the sibling ticket used) that `build_metropolis_state()` produces zero
  `LAW-SPAWN-OCCUPANCY` violations at its current default parameters and at least one other
  `entity_count`/`region_count` pairing exercised elsewhere in the repo (check
  `tests/perf/`, `tests/certification/` call sites first).
- Check whether `build_mixed_state()`'s own composition (merging `build_idle_state`'s heroes with
  `build_combat_arena_state`'s monsters under independent local coordinate schemes, before step 5
  of `build_metropolis_state()` unconditionally overwrites all of it) can itself produce collisions
  when called directly, without going through `build_metropolis_state()`'s repositioning step —
  not measured in this session because step 5 always overwrites it downstream, but any caller
  using `build_mixed_state()` on its own would not get that overwrite.

## Out of Scope
- `WorldCompiler.compile()`'s own spawn-collision fix — already done
  (`TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE`), unrelated pipeline, not
  touched here.
- `RaidService.check_for_raid`'s runtime raid-spawn collision — already done
  (`TCK-20260521-OCC-COLLISION`), unrelated pipeline, not touched here.
- Any other `src/perf/scenarios.py` builder function not shown to collide
  (`build_idle_state`, `build_resource_state`, `build_movement_state`, `build_strategic_state`,
  `build_combat_arena_state` called standalone) — `build_movement_state` already explicitly
  comments that it uses "a grid layout to ensure no initial occupancy conflicts," so it is
  presumably already collision-free by construction; not re-verified here, flag as a quick sanity
  check for whoever implements this if time allows.
- Re-running the tactical-attack-path investigation's own findings against a fixed `metropolis` —
  that investigation's conclusions did not depend on `metropolis`'s per-entity positions being
  correct (disclosed as a limitation there, not a load-bearing input); no re-verification of that
  ticket is required once this is fixed.

## Acceptance Criteria
- [x] `HardLawMonitor.check_initial_placement()` (or an equivalent direct occupancy check) returns
  zero `LAW-SPAWN-OCCUPANCY` violations for `build_metropolis_state()` at its default parameters
  (`entity_count=1000, region_count=50, buildings_per_region=20, seed=42`).
- [x] Same check passes for at least one other real `entity_count`/`region_count` combination
  actually used by `tests/perf/` or `tests/certification/` call sites.
- [x] Repeated calls with identical parameters produce a bit-identical entity-position map
  (determinism preserved).
- [x] A real, short `Kernel.tick_once()` run (a handful of ticks, `LocalSequentialExecutor`)
  against the fixed `build_metropolis_state()` output produces no `hard_law_violations.jsonl`
  spawn/occupancy records.
- [x] Existing perf/cert tests that construct via `build_metropolis_state()` still pass unmodified.

## Related Tickets
- `TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE` (same violation signature,
  different pipeline — `WorldCompiler.compile()`, not `src/perf/scenarios.py`; this ticket's own
  Out of Scope explicitly excluded the sibling pipeline this ticket now covers)
- `TCK-20260521-OCC-COLLISION` / `TCK-20260521-METROPOLIS-COLLISION` (unrelated despite the shared
  "Metropolis" name — a runtime raid-spawn collision in `src/world/raid.py`, not this perf-harness
  builder)
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (closed — where this defect was
  first observed, disclosed as a limitation on its own control scenario, not chased to root cause
  there; this ticket is the follow-up that root-causes and will fix it)

## Related Docs
- `docs/observability/hard_law_monitor.md` (`LAW-SPAWN-OCCUPANCY` row — detection mechanism this
  ticket reuses, not modifies)

## Related Stored Artifacts
_(none yet — filed as a root-caused finding, not yet implemented)_

## Related Code Areas
- `src/perf/scenarios.py` (`build_metropolis_state()` step 5, lines ~375-392 — the defect;
  `build_mixed_state()`, `build_combat_arena_state()`, `build_idle_state()` — the upstream
  composition step 5 unconditionally overwrites, relevant to the Scope item checking
  `build_mixed_state()` called standalone)
- `src/observability/hard_law_monitor.py` (`HardLawMonitor.check_initial_placement()` — the real
  detection mechanism to verify against, read-only reference)
- `src/worldbuilding/compiler.py` (`_resolve_entity_spawn_tile()` — the existing, already-reviewed
  fix pattern from the sibling ticket, reference for this ticket's own fix design)

## Assumptions / Open Questions
- Not yet confirmed which real test files or perf/cert CI jobs actually call
  `build_metropolis_state()` today, or with what parameters besides the 1000/50/20/42 default used
  in this session's own instrumentation — needs a grep pass at implementation time
  (`grep -rn "build_metropolis_state" tests/ tools/`) before scoping the fix's verification matrix.
- Whether a purely deterministic (non-RNG) formula fix (e.g. choosing an offset period that does
  not divide evenly into arbitrary `region_count` values) is sufficient, or whether an explicit
  occupancy-tracking set (mirroring the `WorldCompiler` fix) is needed for full generality across
  all `entity_count`/`region_count`/`buildings_per_region` combinations — not decided here; left
  for whoever implements this to choose based on what the actual call-site matrix requires.

## Implementation Notes
### perf-planner dispatch notes, 2026-10-04

- **Authorization.** The owner extended the partial lift to `src/perf/scenarios.py` for this ticket only
  (`performance_optimization_roadmap.md`, gate item 4). No other `src/` file is in scope. Stop and tell
  perf-planner if the fix seems to need one.
- **Call-site matrix (grep done by the planner).** `build_metropolis_state` at 1000/50/20
  (`tests/perf/test_perf_metropolis.py:40`, `src/perf/profile_governance.py:17`), at 500 and at 200
  (`test_perf_metropolis.py:102,127`, default `region_count`). `build_mixed_state` standalone at 200
  (`tests/perf/test_perf_stress.py`), 1000 (`tools/perf/run_perf_baseline.py`) and 100
  (`tools/release/verify_production_profiles.py`). AC2 uses the 500 and 200 pairings. The Scope item on
  `build_mixed_state` standalone must be answered for 100/200/1000 with a measured result.
- **Fix shape (planner preference, not binding).** The formula is fully deterministic, so the simplest
  fix is enough: give each entity a per-region slot index `i // region_count` on a grid that fits
  inside the region, and raise a `ValueError` when `entity_count` exceeds the region capacity, instead
  of wrapping silently. A per-entity occupancy set is only needed if the measured matrix shows the
  slot scheme cannot cover it.
- **Determinism.** AC3 compares the full position map from two calls. Also compare the state digest
  from two calls (the `flat-sha256-v1` `ProofDigest`); do not invent a new digest.
- **Remove the workaround.** Remove `METROPOLIS_WARNING` and the branch that adds it in
  `tools/perf/_profiling_common.py`, and update any test that asserts it. Then run the fix: do not leave
  a warning about a defect that is gone.
- **Measurement.** The metropolis TPS/p99 thresholds are soft, and stay soft. Record before/after
  avg TPS and p99 for `test_perf_metropolis_longevity` (500) once, marked provisional, in the ticket.
  Do not retune thresholds here.
- **Heavy runs.** `test_perf_metropolis_stress` (1000) is `extra_slow`: run it once, in the foreground,
  under the `systemd-run` memory cap, or skip it and say so.
- **Parity/docs.** Check `docs/parity_ledger/infrastructure.yaml` and `docs/observability/hard_law_monitor.md`
  for a metropolis or perf-scenario entry; update one only if it exists and changes meaning.

**Implemented (perf-implementer, 2026-10-04).** Hotfix tier: no staging artifacts (repo rule); findings live here.
- **Root cause was wider than the ticket said.** Besides the period-100 offset, the old step 5 also put entities on
  building tiles (entity grid 5+5k collides with buildings at 5+10k) and on resource-node tiles (nodes sit at
  `(id%100, id//100)`, y>=10, inside region 0). A pure per-region slot index would still have collided, so the fix
  uses the planner's fallback: per-region slot cursor `i // region_count` over a 19x19 grid (5-tile pitch, 5..95)
  with building and resource-node tiles removed; `ValueError("... raise region_count")` when a region runs out.
  Deterministic, no RNG.
- **Measured before -> after (`HardLawMonitor.check_initial_placement`, LAW-SPAWN-OCCUPANCY count):**
  metropolis 200/50: 50 -> 0; 500/50: 100 -> 0; 1000/50: 100 -> 0.
- **Scope item, `build_mixed_state` standalone: it DOES collide, not fixed here.** 100: 2, 200: 2, 1000: 7
  violations (hero id%100==5 vs monsters at (5.0, i); heroes vs resource nodes, e.g. entity 51 vs node 1005 at
  (5,10)). Callers: `tests/perf/test_perf_stress.py` (200), `tools/perf/run_perf_baseline.py` (1000),
  `tools/release/verify_production_profiles.py` (100). Fixing it moves those baselines' positions, so it is left
  for the planner to file; `build_idle_state`/`build_resource_state`/`build_movement_state` unchecked (out of scope).
- **Workaround removed:** `METROPOLIS_WARNING`, its header branch and the two CLI prints
  (`tools/perf/_profiling_common.py`, `profile_tick.py`, `flag_attribution.py`), the 3 tests asserting it, and the
  "known defective" line in `docs/guides/performance_profiling.md`.
- **Provisional measurement, `test_perf_metropolis_longevity` (500), soft threshold unchanged:** avg TPS 1.84 before,
  1.84 after (limit 5.0, breached both times, as before). p99 was not captured on the before run, so no p99
  comparison is claimed. Single run each, noisy machine.
- **Not run:** `test_perf_metropolis_stress` (1000, extra_slow), skipped to protect the machine; the 1000/50
  placement is covered by the zero-violation check instead.
- Parity ledger and `hard_law_monitor.md`: no metropolis/perf-scenario entry exists, nothing updated.

## Test Summary
- New `tests/tools/test_perf_scenarios_placement.py`: zero LAW-SPAWN-OCCUPANCY at 1000/50, 500/50, 200/50, 100/7;
  two-call position map and `CanonicalHashScheduler.compute_digest` (flat-sha256-v1) equal; ValueError on
  overflow; 3 real `Kernel.tick_once()` ticks (LocalSequentialExecutor) record no spawn/occupancy violation.
- `tests/tools/test_perf_scenarios_placement.py` + `tests/tools/test_profiling_toolkit.py`: 33 passed, 1 skipped.
- `tests/perf/test_perf_metropolis.py -k "longevity or chaos"`: 2 passed (soft-threshold warnings only).

## Files Changed
- `src/perf/scenarios.py`, `tools/perf/_profiling_common.py`, `tools/perf/profile_tick.py`,
  `tools/perf/flag_attribution.py`, `tests/tools/test_profiling_toolkit.py`,
  `tests/tools/test_perf_scenarios_placement.py` (new), `docs/guides/performance_profiling.md`

## Completion Summary
`build_metropolis_state()` now places every entity on its own tile (zero LAW-SPAWN-OCCUPANCY at 200/500/1000 entities, was 50/100/100), deterministically, via helpers `_region_free_slots` and `_spread_entities_into_regions`; overflow raises ValueError. The known-defect warning workaround was removed. Code-health 0 new / 0 worse; typecheck baseline filter clean. Standalone `build_mixed_state` collisions split to TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION.
