---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP
phase: open
date: 2026-08-08
tags: [simulation-quality, observability, world]
---

# TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP

## Title
`entity_lifecycle_score.py` silently drops role/faction/kind/region for entities born mid-run —
21-48% of the real long-run observed population in every one of the 6 curated worlds

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Child ticket of `TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC`. Found while deeply reading the
epic's own real 2000-tick observation data (`docs/simulation_quality/long_run_observations/
*.json`): every one of the 6 worlds shows a `"role": None` group in its per-role aggregation
breakdown, with an oddly precise, constant count — **exactly 10 entities per world**, regardless
of that world's own real total population (21 in `wilderness_survival` up to 48 in
`crowded_frontier`):

| World | Compiled `entity_count` | Total in run | `role=None` count | % of run |
|---|---|---|---|---|
| `wilderness_survival` | 11 | 21 | 10 | 48% |
| `resource_dense_basin` | 23 | 33 | 10 | 30% |
| `crowded_frontier` | 38 | 48 | 10 | 21% |
| `hero_guild_routing` | 31 | 41 | 10 | 24% |
| `dungeon_crawl` | 32 | 42 | 10 | 24% |
| `urban_political` | 30 | 40 | 10 | 25% |

These are not junk/edge-case entities — their `path_length` values are substantial (as high as
3289 in `urban_political`; several worlds show entities alive for the large majority of the
2000-tick run). Root cause traced directly: `entity_lifecycle_score.py`'s
`extract_entity_paths()` (line ~203) falls back to `{"role": None, "faction": None, "kind": None,
"region": None}` whenever an `entity_id` appears in `simulation_events.jsonl` but not in the
`world_state.entities` snapshot used to build `metadata` — and that snapshot is loaded **once,
before the run** (`_load_world_state()`, called before `Kernel.tick_once()` ever executes). Any
entity that comes into existence *during* the run — confirmed a real, gated mechanic via
`demographic_birth` (`src/observability/event_shapers.py`, `event_extractor.py`,
`src/simulation_quality/scorers/world_dynamics.py`) — has its full, real event history correctly
captured, but its identity metadata is unrecoverable from the pre-run snapshot.

**Real consequence**: every per-role/per-faction/per-kind/per-region aggregation and clustering
breakdown this tool produces is silently missing 21-48% of the real population in a long (2000+
tick) run — a population fraction this large is not a rounding error; it materially affects the
population-level stats users read.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm the real cause of the exactly-10-per-world consistency: is there a real,
     deterministic population-growth cap/rate (e.g. a fixed reinforcement-wave size, a
     population-cap-relative-to-starting-count rule) driving this, or is it coincidental? Trace
     the real birth-triggering logic in `src/engine/world_dynamics.py` or wherever
     `demographic_birth`'s own `StateUpdate.entities_add` is produced.
   - Confirm whether the newly-born entities' own real identity (role/faction/kind/region) is
     knowable at all post-run — e.g. by reading `kernel.state.entities` (the FINAL state, not the
     pre-run snapshot) after the run completes, before the run's own scratch directory is cleaned
     up.
2. **Plan**: design the fix — most likely, build `metadata` from the run's own FINAL state
   (post-run `kernel.state.entities`, or a state snapshot taken after `tick_once()` loop
   completes) rather than (or in addition to) the pre-run snapshot, so newly-born entities get
   real metadata. Decide whether entities present in BOTH snapshots should prefer final-state
   metadata (e.g. a role/faction change mid-run — ties into
   `TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP`'s own sibling finding about
   `entity_role_changed`/`entity_faction_changed`) or pre-run metadata (spawn-time identity) —
   this is a real design decision, not assumed either way.
3. **Implement**: the fix, verified by re-running `make simq-long-run-lifecycle-observation` and
   confirming the `"None"` role group disappears (or shrinks to genuinely-unresolvable cases only,
   if any real ones exist) across the 6 curated worlds.

## Out of Scope
- Investigating WHY role/faction changes are rare (a separate, real finding noted during this same
  investigation but not root-caused here) — if relevant, a future ticket.
- Any change to the real `demographic_birth` game mechanic itself — this ticket is purely about
  the observability tool's own metadata-join gap, not the birth mechanic.

## Acceptance Criteria
- [ ] investigation.md reports the real cause of the exactly-10-per-world pattern
- [ ] investigation.md confirms whether post-run state resolution is viable
- [ ] A real fix lands, re-verified via the real long-run observation tier — the `"None"` role
      group shrinks or disappears on all 6 curated worlds
- [ ] `docs/simulation_quality/entity_lifecycle_score.md` / `docs/guides/entity_lifecycle_score.md`
      updated to document the fix
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC (parent epic)
- TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER (DONE — the tool/data source this bug was
  found in)
- TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS (DONE — the tool this bug lives in)

## Related Docs
- `docs/simulation_quality/entity_lifecycle_score.md`, `docs/guides/entity_lifecycle_score.md`
- `docs/simulation_quality/long_run_observations/*.json` (the real data this ticket's own finding
  is grounded in)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS/`

## Related Code Areas
- `tools/entity_lifecycle_score.py` (`_entity_metadata()`, `extract_entity_paths()`)
- `src/engine/world_dynamics.py` (real `demographic_birth` trigger)
- `src/observability/event_shapers.py` (`demographic_birth` emission)

## Assumptions / Open Questions
- Whether the exactly-10 pattern is a real, deterministic mechanic or coincidental across these 6
  specific worlds/seed — not assumed; Investigate must trace the real trigger logic.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
