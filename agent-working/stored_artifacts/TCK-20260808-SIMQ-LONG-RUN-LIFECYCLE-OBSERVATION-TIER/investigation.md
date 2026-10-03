---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER
artifact_type: investigation
phase: investigate
date: 2026-08-08
tags: [simulation-quality, calibration]
---

# Investigation — TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER

## Real, corpus-wide survey of tick-gated detectors (beyond the 2 already known)

Surveyed `docs/simulation_quality/quality_scoring_contract.md` directly (the scorer contract, not
assumed from memory). Real tick/event-window-gated rules found, beyond
`capability_growth_stalled` (300 ticks, PROGRESSION) and `entity_lifecycle_score.py`'s own
`clustering_reliable_tick_threshold` (1000 ticks):

| Detector | Pillar | Window | Source |
|---|---|---|---|
| `belief_system_dormant` | INFORMATION | 100 ticks (population-wide zero belief updates) | §7 |
| `entropy_reward` | AGENCY | 100 ticks (route family entropy, per entity) | §7 |
| `faction_trajectory_stagnant` | FACTION | 300 ticks (territory unchanged despite diplomatic activity) | §7.6 |
| `social_structure_static` | SOCIAL | 300 ticks (zero group membership changes) | §7 |
| `trauma_hazard_broken` (loop signal) | WORLD | present for >100 ticks | §7 |
| `gold_frozen` | ECONOMY | 500 ticks (single entity, no delta, alive) | §7 |
| `emergence_dormant` | WORLD | 500 ticks (zero world emergence events) | §7 |
| `capability_growth_stalled` (already known) | PROGRESSION | 300 ticks | §7.6 |
| `clustering_reliable_tick_threshold` (already known, `entity_lifecycle_score.py`) | n/a | 1000 ticks | this tool's own calibration |

**§4.7 Loop/Stagnation Detection's own 200-event sliding window is a distinct, related-but-not-
identical concept — confirmed, not conflated** (per the ticket's own Related Docs note): it counts
**scored events**, not ticks, per pillar. At real observed densities (47-287 events per 200
ticks, `sandbox_world`/`dungeon_crawl`), the window rarely fills within 200 ticks — meaning it
carries an *indirect* tick-length implication (a run needs enough ticks to accumulate 200 scored
events **for a single pillar**, which given events are split across 10 pillars is a materially
higher tick count than the raw density alone suggests) without itself being a fixed tick number.

**Real maximum found across all detectors surveyed: 500 ticks** (`gold_frozen`,
`emergence_dormant`) — below `entity_lifecycle_score.py`'s own 1000-tick `clustering_reliable`
threshold, which remains the real, corpus-wide binding constraint, not any core SimQ scorer rule.
No detector requires more than 1000 ticks to become structurally reachable.

## Real 5000-tick runtime cost (measured, not assumed)

Live `Kernel` runs, `SIM_OBS_MODE=NORMAL`, `no_frame_pacing: True`, 2 representative larger corpus
worlds (per the ticket's own Acceptance Criteria):

```
frontier_extended: entities=59 5000 ticks in 250.3s (50.06ms/tick) dropped=0
simq_scale_stress_seed42: entities=68 5000 ticks in 250.9s (50.19ms/tick) dropped=0
```

Both of the corpus's largest worlds (59/68 entities) complete a real 5000-tick run in ~250s
(~4.2 minutes), `dropped_count=0` — zero observability data loss even at this volume/duration.
**5000 ticks is real, measured, achievable cost** — not a theoretical target. Since this tier is
explicitly NOT part of the fast-tier regression suite (additive, periodic observation, not CI),
~250s per world (worst case; smaller corpus worlds will be faster) is acceptable. **Decision:
5000 ticks for the long-run observation tier**, matching the top of the user's own originally
requested 1000-5000 range, since real cost data supports it and no detector needs fewer.

## Scope item 3: new tier value, or a cross-cutting dimension?

**Cross-cutting dimension, not a new `corpus_registry.yaml` `tier` value.** `tier`
(Unit/End-to-end/Stress/Regression-baseline, per `corpus_tier_taxonomy.md`) answers "why does this
world exist in the calibration corpus" — orthogonal to run length, exactly the same relationship
`archetype` (this session's own immediately-preceding sibling ticket,
`TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS`) has to `tier`. A world's tier doesn't
change based on how long it's run. Long-run observation is implemented as a **standing,
re-runnable script + a curated world subset**, not a new pillar-grading fixture (per this ticket's
own Out of Scope: "no change to the SimQ pillar scoring formulas... this ticket is about
observation length, not the metrics computed at that length" — `grade_anchors.json` stays
untouched).

**World subset**: reuse `TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION`'s own already-established
6-world density-correlation sample (`wilderness_survival`, `resource_dense_basin`,
`crowded_frontier`, `hero_guild_routing`, `dungeon_crawl`, `urban_political`) rather than
inventing a new selection — already spans the corpus's real density range and mixes archetypes
(2 `monster_only_gauntlet`, 4 `civilian_settlement`, per the immediately-preceding sibling
ticket's own new registry field).

## Docs Requiring Update

- `docs/simulation_quality/corpus_tier_taxonomy.md`: add a short section distinguishing the
  tier/archetype dimensions (both per-world, orthogonal to run length) from this new, separate
  long-run *observation* practice
- `docs/simulation_quality/entity_lifecycle_score.md`: document the new `make` target and its
  real tick-length choice, citing this ticket's own measured runtime data
