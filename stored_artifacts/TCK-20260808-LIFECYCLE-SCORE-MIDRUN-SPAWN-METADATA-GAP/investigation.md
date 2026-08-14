---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP
artifact_type: investigation
phase: investigate
date: 2026-08-08
tags: [simulation-quality, observability, world]
---

# Investigation — TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP

## Real cause of the metadata gap: confirmed, mechanical

`tools/entity_lifecycle_score.py::extract_entity_paths()` (line ~203) falls back to
`{"role": None, "faction": None, "kind": None, "region": None}` for any `entity_id` present in
`simulation_events.jsonl` but absent from `metadata` — and `metadata` is built once, from
`_entity_metadata(world_state)`, where `world_state` comes from `_load_world_state(world, seed)` —
**always the initial, pre-run compiled state**, called before `Kernel.tick_once()` ever executes.
Any entity that enters existence *during* the run has a real, complete event history but no
metadata source to join against.

## Real, multi-source population-growth mechanism (not a single mechanic)

Traced `src/engine/world_dynamics.py`'s own tick-172 world-dynamics phase: `update.entities_add`
is the union of **5 independent sources** every `should_run(state.tick, None, cadence.
world_dynamics)` tick — `CalamityService`, `SpawnService.process_spawns` ("Standard Monster
Replenishment"), `BossService.check_for_boss_spawn`, `RaidService.check_for_raid`, and
`CampService.process_camps` — plus a 6th, separately-merged source,
`DemographicCycleService.process_demographics` (real, confirmed via direct code read:
`update.merge(demo_update)` at line 185 — not a dropped/orphaned update). `demographic_birth`
(the event `entity_lifecycle_score.py`'s own `CONCLUSION_DEMOGRAPHIC` bucket reads) fires
generically for **any** entity in `entities_add`, regardless of which of these 6 sources produced
it (`event_shapers.py:984-992`) — so "births" in the observable sense are really "any new entity
from any of 6 real mechanics," not one single birth-rate formula.

**A real, disclosed, out-of-scope connection found while tracing `SpawnService.process_spawns`**:
its own density-replenishment check counts existing monsters via `entity.identity.role ==
EntityRole.MONSTER` (`src/world/spawn.py:55`) — the same `EntityRole` field this session's own
`TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS` ticket already found is mistagged
corpus-wide (real monster-kind entities carry `role=CITIZEN`, not `role=MONSTER`). If that
mistagging is real and universal (not re-verified again here — already disclosed and out of scope
for that prior ticket too), `region_monster_count` would always read 0 regardless of the real
living monster population, meaning `SpawnService`'s own deficit-based replenishment could
under-detect existing monsters and over-spawn relative to its own intended density target. This
would be a genuine, separate mechanism bug — **not investigated to full closure here**, since
confirming and fixing it is out of this ticket's own scope (which is the observability tool's
metadata join, not the spawn mechanic itself). Flagged for a future ticket if the pattern proves
material once `EntityRole.MONSTER` mistagging itself is ever addressed.

**Why exactly 10 per world, not conclusively pinned down.** Multiple real, independent mechanics
contribute to `entities_add`, each cadence- and RNG-gated differently per world/region content —
tracing the precise arithmetic that converges to "10" in every one of the 6 curated worlds
(21-48 total population each) would require per-mechanism instrumentation across all 6, a real but
disproportionate effort relative to this ticket's own fix. **Real, sufficient conclusion for this
ticket's own purpose**: population growth during a run is a genuine, multi-source, real mechanic
producing entities with substantial, real event histories (`path_length` up to 3289) — not
observability noise or a counting bug on this tool's own read side. The fix must handle real
mid-run population growth as an expected, ongoing occurrence, not a rare edge case.

## Real cause resolved: post-run state resolution is viable, with one honest limitation

`entity_lifecycle_score.py::_run_for_analysis()` drives the `Kernel` directly and currently
discards it after computing `health` — but `kernel.state.entities` (the real, final, live state)
is available immediately after the tick loop, before `kernel.shutdown()`. Any entity present in
`kernel.state.entities` at run-end — including one born mid-run — has real, resolvable identity
metadata (`role`/`faction`/`kind`/`region`), via the exact same `_entity_metadata()` logic already
used for the pre-run snapshot.

**One real, disclosed residual limitation**: an entity that is **both born and removed** (death,
despawn) entirely within the observed window would appear in neither the pre-run nor the post-run
`state.entities` snapshot — its metadata would remain unresolvable by this fix. Real data check:
none of the 60 (10 × 6 worlds) currently-`None`-role entities in the committed 2000-tick
observation data have `path_length == 0` or a trivially short path, so this specific edge case
doesn't appear to affect the current real dataset — but it is a genuine, structural gap the fix
cannot close, disclosed rather than silently assumed away.

## Docs Requiring Update

- `docs/simulation_quality/entity_lifecycle_score.md`: document the post-run metadata resolution
  fix and its one disclosed residual limitation (born-and-removed-within-window entities)
- `docs/guides/entity_lifecycle_score.md`: practitioner-facing note that `role: None` in output
  should now be rare, and what it means if it still appears
