---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED
artifact_type: test_plan
tags: [investigation, root-cause, corpus, world]
---

# Test Plan — TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED

## No repo test suite change

This ticket makes no `src/` or `tests/` change, so there is no pytest coverage to add. Verification
was direct execution, not a new automated test:

- **`demographic_cohort_cycle`/`camp`:** a standalone read-only script (kept in this session's
  scratchpad, not committed — a one-off diagnostic, not a regression-pinning test) that loads
  `CatalogRepository`/`WorldModuleRepository`, resolves `data/content/world_compositions/
  frontier_living_world.yaml` via `WorldAssemblyResolver.assemble()`, and calls
  `WorldCompiler.compile(seed=42, ...)` directly — the real production function, not a stub.
  Independently reproduced by `rpg-feature-planning` from a separate worktree run for the cohort
  case, with identical per-region figures.
- **`enemy_data`/`region_data`:** direct reads of `src/cognition/capability_estimate.py:124-127`
  (confirming `_ENEMY_DANGER`'s fallback branch is unconditionally live) and
  `src/domains/adventure/generator.py` (confirming `RouteFamily.SCOUT_LOCATION` is absent from
  every branch) — code reads used only to confirm a specific, falsifiable claim (a table lookup's
  branch condition; a grep's presence/absence), not "reading the code" in the sense the epic's own
  evidence bar prohibits (which requires execution or content facts, not impressions from reading).

## Regression risk

None — no code changed. A future ticket that fixes `registries/mechanisms.yaml`'s stale `camp`/
`demographic_cohort_cycle` entries, or `docs/world/raid_boss_camp_contract.md`'s stale prose, would
be the place a real regression test (e.g. a corpus-level assertion that `state.camps`/
`population_cohorts` are non-empty for a known-seeded region) belongs — out of scope here.
