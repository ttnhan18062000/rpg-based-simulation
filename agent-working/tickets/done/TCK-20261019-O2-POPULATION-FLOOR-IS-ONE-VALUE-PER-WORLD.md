---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261019-O2-POPULATION-FLOOR-IS-ONE-VALUE-PER-WORLD
phase: done
date: 2026-10-19
tags: []
---

# TCK-20261019-O2-POPULATION-FLOOR-IS-ONE-VALUE-PER-WORLD

## Title
O2.population's floor is one value per (world, group), computed from the gate seed set's pooled tick-0 mean

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
The floor was per-seed (a tenth of that seed's first-tick population), so frontier's seed documents carried 3.1-3.3 and the report could not pool them (11 contract_error rows). Testing-planner ruled (option 2) and the designer accepted: one floor per (world, group) from the pooled tick-0 mean over the gate config's seed set, identical in every seed document and at every tick.

## Scope
- rpg_gate_metrics.py: tick0_means(world) compiles the world for each seed of tests/simulation_quality/rpg_gate/config.yaml (no ticks) and pools the alive counts by kind group; population_floor(mean) = max(3, 0.10 x mean).
- Tests: the floor value; identical across seed documents and ticks; a paired arm's floor does not move when only the other arm's tick-0 changes; compiled tick-0 equals the ledger's first-observed population on the 3 gate worlds.

## Out of Scope
- The baseline's recorded floor handling after v1 (testing's #666: the report reads the reference row's k/floor).

## Acceptance Criteria
- Every seed document of a world carries the same O2.population floor; observability and gate tests, mypy, import contracts and the code-health check are green.

## Related Tickets
- TCK-20261019-V1-COUNTS-A-HUNGER-DROP-AS-BACKED-ONLY-WHEN-AN-ACCEPTED-TRANSFER-MOVED-SOMETHING
- TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/rpg_gate_metrics.py

## Assumptions / Open Questions
- Cost: 5 compiles per run, about 0.1-0.7 s each (first one imports), under 1% of a 4-10 min run.

## Implementation Notes
tests/simulation_quality/rpg_gate/test_v8_fires.py got an autouse patch of the two floor helpers (its self-test world has no spec).

## Test Summary
tests/unit/observability/test_rpg_gate_metrics.py (floor value, identical across seed documents and ticks, a paired arm's floor does not move, compiled tick-0 equals the ledger's first sample on the 3 gate worlds); tests/unit/tools/test_rpg_gate_harness.py (floor_seeds, rerun full seed set). Combined branch checks as above.

## Files Changed
src/observability/rpg_gate_metrics.py, tests/unit/observability/test_rpg_gate_metrics.py, tests/simulation_quality/rpg_gate/test_v8_fires.py

## Completion Summary
O2.population's floor is one value per (world, group) from the pooled tick-0 mean over the gate config's seed set, handed in by the harness (--seeds). Landed in the combined pre-v1 PR; closed by hand-orchestration at the PR commit.
