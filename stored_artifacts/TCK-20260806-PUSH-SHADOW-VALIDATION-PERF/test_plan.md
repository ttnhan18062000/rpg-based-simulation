---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHADOW-VALIDATION-PERF
artifact_type: test_plan
tags: [observability, engine, simulation-quality, performance]
---

# test_plan.md — TCK-20260806-PUSH-SHADOW-VALIDATION-PERF

## Tests / verification performed

- Real kernel integration comparison (not mocked) across 6 worlds × 500 ticks: `dungeon_crawl`,
  `sandbox_world`, `hero_guild_routing`, `urban_political`, `wilderness_survival`,
  `crowded_frontier`, seed 42. Event-type-set comparison per tick, plus payload-value comparison
  for `combat_damage`. Final result: 130/131 active ticks match exactly, 0 payload mismatches.
- Full `tests/unit/observability/` suite re-run after both bug fixes: 798 passed, 6 skipped.
- 2 reduced-scope performance runs (`BenchHarness`, `sandbox_world`, warmup=30/sample=150):
  -9.37% and -10.42% "overhead" (both faster than baseline, within measurement noise).

## This ticket's own code changes

None — all fixes landed in the reopened `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`. This ticket
verifies and produces the go/no-go verdict.

## Out of scope

A full, by-the-book warmup=100/sample=1000 3-mode isolation-overhead certification run —
recommended before the eventual `ON`-mode (live delivery) work, not required to gate this
SHADOW-mode validation gate.
