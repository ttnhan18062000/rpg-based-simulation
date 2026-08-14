---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD
artifact_type: test_plan
tags: [world, simulation-quality, corpus]
---

# Test Plan — TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD

## Normal flow
- `WorldCompiler.compile()` (or the standard `make`/CLI compile path) succeeds on the new world
  with zero region/building/faction ID collisions.
- `tools/generate_corpus_registry.py` picks up the new world with real entity/region/faction/quest
  counts (not placeholder).
- A real `tools/simq_long_run_observation.py` run (5000 ticks, seed 42) completes with
  `dropped_count=0` and produces a combined SimQ + entity-lifecycle-score snapshot under
  `docs/simulation_quality/long_run_observations/`.

## Edge cases
- Real achieved `phase_coverage` bucket count is reported exactly as observed — including if it's
  below 9/10 (the honest ceiling established in investigation.md §1), not rounded up or assumed.
- If `ENABLE_GUILD_QUEST_GENERATION` produces 0 real `quest_started` events despite the `town_hall`
  building being present (e.g. AI never selects the GUILD goal in practice due to competing
  higher-utility goals), that is reported as a real finding, not silently patched by artificially
  boosting the goal's utility score.

## Failure modes
- Module composition collision (region/building/faction ID clash) surfaces as a real
  `WorldCompiler` validation error during compile — resolved by dropping/substituting the
  colliding module, matching `simq_scale_stress_seed42`'s own precedent (2 real collisions hit and
  resolved during its authoring), not worked around silently.
- If the 5000-tick run's real measured cost exceeds a reasonable multiple (~2x) of the existing
  ~250s/60-entity baseline, that is disclosed rather than the observation silently truncated to a
  shorter tick length.

## Regression-prone paths
- `docs/simulation_quality/corpus_tier_taxonomy.md`'s per-world table must stay internally
  consistent with `corpus_registry.yaml`'s real generated counts (matching this doc's own existing
  "table can drift, read the registry" caveat) — verified by re-reading the regenerated registry
  after authoring, not by hand-transcribing numbers into the taxonomy doc.

## Scoped test commands
- `pytest tests/tools/test_corpus_registry.py -q` (registry still generates correctly with the new
  world included)
- `pytest tests/unit/worldassembly/ -k collision -q` (if a corpus-wide collision test exists,
  confirm the new world doesn't trip it)
