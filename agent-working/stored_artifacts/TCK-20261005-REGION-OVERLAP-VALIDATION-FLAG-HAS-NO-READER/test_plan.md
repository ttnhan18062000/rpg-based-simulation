---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER
phase: done
date: 2026-10-05
tags: [world]
---

# test_plan — TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER

- `tests/unit/engine/test_region_lookup_policy.py` (18 tests, 9 fail on the old code): inclusive edges, smallest area, declaration-order ties, `None`, lookups agree, the measured `(29, 40)` death.
- `tests/unit/worldbuilding/test_allow_overlapping_regions_unread.py`: no production code reads the field; positive control on the scanner.
- Full CI lane set re-run on the final tree (all green): core 1698, gameplay 1372, integration 1057, simulation_quality 504, mechanic_scenarios 89, domains/observability/entity/cognition/certification 2350, api/cli/logging/engine/architecture/perf/certification 450, `make lane-all-fast` 431, `make gate-expansion` 12, mechanism registry targets OK.

## Proof Plan
- level: unit plus full CI lane set
- proof kind: behavioural tests that fail on the old code (9 of 18), an unread-pin source scan with a positive control
- oracle source: owner decision 11 and the planner ruling; the measured `(29, 40)` far-edge death
- expected effect: one rule for every lookup; far-edge death credited; no un-shadowing claimed
- selected commands: `pytest tests/unit/engine/test_region_lookup_policy.py tests/unit/worldbuilding/test_allow_overlapping_regions_unread.py`; the CI lane set listed above
