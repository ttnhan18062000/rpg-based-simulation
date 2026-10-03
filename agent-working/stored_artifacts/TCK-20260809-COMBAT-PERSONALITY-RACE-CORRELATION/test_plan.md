---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION

## Normal flow
- `test_get_bravery_bias_by_real_alignment_bucket`
  (`tests/unit/worldbuilding/test_world_compiler.py`): asserts the real bias value for one real
  content faction per `alignment_bucket` (`wild_beast_pack`→0.35, `goblin_warband`→0.25,
  `orc_clan`→0.15, `hero_guild`→0.05, `merchant_league`→0.0).
- `test_compiler_faction_bravery_bias_produces_real_population_skew`: a full synthetic-world
  compile (30 `wild_beast_pack` + 30 `merchant_league` entities) asserts the real, compiled
  population's average bravery differs by >0.2 between the two factions, and that individual
  per-entity variance survives within the predator faction (`len(set(bravery_values)) > 1`).

## Edge cases
- `get_bravery_bias("nonexistent_faction_xyz")` returns `0.0` (no crash) — covered directly in
  `test_get_bravery_bias_by_real_alignment_bucket`.
- Bias clamping: bravery is clamped to `[0.0, 1.0]` after the additive bias — implicitly exercised
  by the population-skew test (predator faction's real max observed values sit at/near 1.0, never
  exceeding it).

## Failure modes / regression-prone paths
- Full existing `tests/unit/worldbuilding/test_world_compiler.py` suite re-run unmodified (27
  pre-existing tests) to confirm no regression to unrelated compiler behavior (faction tension,
  information sources, quest warnings, resource regen, etc.).

## Real corpus re-verification (not unit-test-only)
- Live probe (same methodology used throughout this session) against real compiled
  `dungeon_crawl` and `urban_political` worlds, post-fix: confirmed real, ordered, measurable
  per-faction bravery averages matching the expected `alignment_bucket` ranking in both worlds.

## Not fixed here (disclosed)
`WorldEntitySpawner`'s own zero-personality bug (both branches) is real and confirmed via direct
source read but not re-verified against a live corpus world here — no real corpus world tested
this session uses that code path for its initial population (only `src/scenarios/
catalog_state_builder.py` calls it). Filed as its own separate ticket.

## Scoped test commands
```
.venv/bin/python3 -m pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ \
  tests/unit/combat/ tests/unit/strategic/ tests/unit/entities/ tests/unit/content/ \
  tests/unit/core/ -q -m "not slow"
```
Result: 1 pre-existing failure (`test_corpus_diversity.py::test_module_family_anchored`,
missing world data directory unrelated to this ticket, confirmed via `git stash` bisection to
fail identically on the pristine pre-ticket codebase). 998 passed, including the 2 new tests.

**Real, separate pre-existing test-pollution finding (bisected, not caused by this ticket)**:
running `tests/unit/worldgeneration/` together with `tests/unit/strategic/test_opportunities.py`
in the same pytest process produces 13 failures in the latter (`assert 0 > 0` — opportunities
list empty) — confirmed via `git stash` bisection to reproduce identically with this ticket's own
`compiler.py`/test changes fully reverted. A pre-existing test-isolation gap (likely shared
registry/singleton state leaking across directories), unrelated to this ticket's own scope —
disclosed, not chased down further here.
