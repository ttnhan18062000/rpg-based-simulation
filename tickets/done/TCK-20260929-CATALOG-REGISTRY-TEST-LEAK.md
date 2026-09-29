---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-CATALOG-REGISTRY-TEST-LEAK
phase: done
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-CATALOG-REGISTRY-TEST-LEAK

## Title
Restore the Enemy/Recipe/Service/Region registries between tests, closing the progression order leak

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
7 tests in `tests/unit/domains/progression/` fail after any of 8 catalog/registry/content-mode test
files and pass alone; CI is green only because it runs that directory by itself. Re-checked at
`origin/main` `1b05a5c9c`: still reproduces (`recipe_materials("iron_shield")` returns `()`).

Root cause (measured with a teardown probe, not inferred): `tests/conftest.py` resets
`ItemRegistry`, `ResourceRegistry` and `registries.ItemRegistry` per test but not
`EnemyRegistry`, `RecipeRegistry`, `ServiceRegistry` or `RegionRegistry`. The 8 polluters
re-bootstrap those four, leaving recipes at 3 or 0 instead of the 46 the catalog loads.

Child of `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY` (Epic A), criterion 3.

## Scope
- One autouse fixture in `tests/conftest.py` restoring the four registries, same pattern as the
  existing three.
- A regression guard: a re-bootstrap in one test must not be visible in the next.
- Verify at one committed SHA: each polluter + progression; combined fast suite;
  `tests/unit/domains` alone; random-order run of the affected set.

## Out of Scope
- Claiming all order dependence is gone (only the verified set).
- Product code changes to the registries.
- Any other registry class-level state not measured here.

## Acceptance Criteria
1. Each of the 8 polluter files + the progression files: 0 failures.
2. Combined fast suite: 0 failures in the 7 nodes.
3. `tests/unit/domains` alone still passes.
4. Random-order run of the affected set passes at the same SHA, or the part closes `provisional`
   with the reason (RNG-contract check).
5. The guard fails on the old conftest and passes on the new one, asserting restore behaviour, not
   absolute counts.
6. Fixture time cost on the fast suite is recorded before and after.

## Related Tickets
- `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §3
- `docs/plans/test_architecture/reference/current_test_system_overview.md` §4.2

## Related Stored Artifacts
None.

## Related Code Areas
`tests/conftest.py`; `src/core/registries.py` (read-only); `tests/unit/core/test_catalog_registry_isolation.py`.

## Assumptions / Open Questions
- Random ordering must be checked against the RNG contract before use.

## Implementation Notes
See Request Summary for the measured cause.

## Test Summary
All at SHA `720347c44` (before the closing commit; only agent-monitoring shards differ).
- Each of the 8 polluters + `tests/unit/domains/progression/`: 0 failures (34-49 passed each).
- `tests/unit/domains` alone: 1059 passed.
- Random order (private seeded `random.Random`, scratch plugin outside `src/`, so no global/simulation
  RNG touched, consistent with the DeterministicRNG contract in `docs/engine/contracts/simulation_kernel_contract.md` §7):
  affected set (8 polluters + guard + progression, 80 tests), seeds 1-10: 80 passed each.
- Combined fast suite `pytest tests/ -m "not slow and not extra_slow"`: 11606 passed, 10 failed, 1 error
  (16m57s). None of the 7 progression nodes fail. The same 10 failures + 1 error occur on an untouched
  `origin/main` (`1b05a5c9c`, clean detached worktree, 17 failed + 1 error incl. the 7 progression
  nodes, 18m03s), and all 11 pass in isolation under both conftests. So the fix removes exactly the 7
  and adds none; the other 11 are pre-existing combined-run failures, not fixed here.
- Guard: fails on `origin/main`'s conftest, passes on the fixed one; passes under 10 shuffle seeds.
- Fixture cost: `tests/unit/domains` + `tests/unit/core` 33.3-33.9 s old vs 33.5-33.7 s new (3
  alternating pairs) - not measurable.

## Files Changed
`tests/conftest.py`; `tests/unit/core/test_catalog_registry_isolation.py`.

## Completion Summary
Fixed at the source (tests/conftest.py autouse reset for the four un-reset registries), with a guard that fails on the old conftest. Verified at SHA 720347c44: polluters+progression, domains alone, 10 random-order seeds, combined fast suite (same 10 failures+1 error as clean origin/main, none new). Not fixed and reported: those 11 pre-existing combined-run failures.
