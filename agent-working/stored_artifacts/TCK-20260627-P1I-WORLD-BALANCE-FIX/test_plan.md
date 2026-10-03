---
ticket_id: TCK-20260627-P1I-WORLD-BALANCE-FIX
phase: test_plan
date: 2026-06-27
---

# Test Plan: Balance dungeon_crawl entity count and add building to wilderness_survival

## Test Scope

Content-only changes (YAML world modules and composition files). No engine code modified.
Tests focus on: module schema validation, world composition assembly, entity count accuracy.

## Test Suite

### T1 — World Validate (make)

```
make world-validate WORLD=dungeon_crawl
make world-validate WORLD=wilderness_survival
```

Pass condition: both exit 0 with no validation errors.

### T2 — Integration: Real Content World Compositions

File: tests/integration/worldassembly/test_real_content_world_compositions.py

Run: `pytest tests/integration/worldassembly/test_real_content_world_compositions.py -v`

Pass condition: all existing tests pass. These tests load real content YAML files
and validate the assembly pipeline succeeds.

### T3 — Integration: Real Content World Modules

File: tests/integration/worldassembly/test_real_content_world_modules.py

Run: `pytest tests/integration/worldassembly/test_real_content_world_modules.py -v`

Pass condition: all existing tests pass. These tests verify module normalization
of real content module files.

### T4 — Full World/Content Test Scope

Run: `pytest tests/integration/worldassembly/ -v`

Pass condition: all tests pass.

## Acceptance Criterion Mapping

| Criterion | Test |
|---|---|
| dungeon_crawl entity count ≤12 | T1 (world-validate), T2/T3 (module loading) |
| wilderness_survival ≥1 building | T1 (world-validate), T2/T3 (module loading) |
| survivor_camp_shelter module valid | T3 (real_content_world_modules) |
| No regression in other worlds | T2/T4 (compositions test covers all content worlds) |

## Out of Scope for Automated Tests

The following acceptance criteria from the ticket require simulation runs (not yet in
automated test suite):
- 2-seed alive_avg at tick 100 > 30% for dungeon_crawl (was ~5%)
- At least 1 non-combat behavioral event by tick 200 for wilderness_survival

These require `python3 tools/run_sim.py` invocations which are manual verification steps.
Post-change the entity math confirms the survival target is achievable:
12 entities vs 32 prior = 62.5% reduction in combat pressure.

## Notes

- The survivor_camp_shelter module will be validated by test_real_content_world_modules
  if the test loads all modules in the world_modules/ directory.
- No parity ledger updates required (content-only change).
