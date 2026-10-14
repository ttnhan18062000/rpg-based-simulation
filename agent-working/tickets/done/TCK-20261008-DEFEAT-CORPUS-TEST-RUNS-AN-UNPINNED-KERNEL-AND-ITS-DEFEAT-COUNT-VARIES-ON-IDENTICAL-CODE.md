---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261008-DEFEAT-CORPUS-TEST-RUNS-AN-UNPINNED-KERNEL-AND-ITS-DEFEAT-COUNT-VARIES-ON-IDENTICAL-CODE
phase: done
date: 2026-10-08
tags: [testing, combat]
---

# TCK-20261008-DEFEAT-CORPUS-TEST-RUNS-AN-UNPINNED-KERNEL-AND-ITS-DEFEAT-COUNT-VARIES-ON-IDENTICAL-CODE

## Title
`test_defeat_deaths_are_recorded_in_unscripted_corpus_play` runs an unpinned kernel, so its DEFEAT count varies from run to run on identical code and the test can turn main red at random.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found while closing the starvation batch: the 120-tick `frontier_marches` seed-42 run in `tests/mechanic_scenarios/test_entity_death_authority_boundary.py` read 2, 1, 2 DEFEAT deaths across runs on `main` `28e29ed2e` and 0, 2, 2 on a branch, with the default executor and governor. The test asserts at least one DEFEAT. testing-planner asked an rpg lane to fix it.

## Scope
Pin the kernel in the file (a pinned-NORMAL governor, `LocalSequentialExecutor`, no tick budget; the pattern of `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`, a 4th local copy until testing-planner extracts a helper). Keep every assertion.

## Out of Scope
- The shared helper; any assertion change.

## Acceptance Criteria
- [x] Five pinned runs give the identical death mix ({DEFEAT: 2, HAZARD: 5, COMBAT: 3}) and the file passes three times in a row; the "at least one DEFEAT" assertion is kept.

## Related Tickets
- TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK.

## Related Docs
- `docs/testing/test_taxonomy.md`.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-DEFEAT-CORPUS-TEST-RUNS-AN-UNPINNED-KERNEL-AND-ITS-DEFEAT-COUNT-VARIES-ON-IDENTICAL-CODE/`.

## Related Code Areas
- `tests/mechanic_scenarios/test_entity_death_authority_boundary.py`.

## Assumptions / Open Questions
- None.

## Implementation Notes
`_PinnedNormalGovernor` and `_pinned_kernel` in the file; both Kernel constructions use it.

## Test Summary
The file passes three times in a row; five pinned runs agree.

## Files Changed
tests/mechanic_scenarios/test_entity_death_authority_boundary.py.

## Completion Summary
The corpus DEFEAT test is deterministic; no assertion loosened.
