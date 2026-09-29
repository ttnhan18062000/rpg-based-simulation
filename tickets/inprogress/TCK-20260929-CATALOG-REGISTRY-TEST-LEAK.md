---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-CATALOG-REGISTRY-TEST-LEAK
phase: open
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-CATALOG-REGISTRY-TEST-LEAK

## Title
Restore the Enemy/Recipe/Service/Region registries between tests, closing the progression order leak

## Status
INPROGRESS

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
(Filled at close.)

## Files Changed
(Filled at close.)

## Completion Summary
(Open.)
