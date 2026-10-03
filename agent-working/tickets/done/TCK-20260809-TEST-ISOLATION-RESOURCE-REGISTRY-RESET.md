---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260809-TEST-ISOLATION-RESOURCE-REGISTRY-RESET
phase: done
date: 2026-08-09
tags: [testing]
---

# TCK-20260809-TEST-ISOLATION-RESOURCE-REGISTRY-RESET

## Title
`ResourceRegistry` has no test-isolation reset fixture, unlike `ItemRegistry` — real runtime code
(`src/runtime/bootstrap.py:112`, `ResourceRegistry.bootstrap({})`) wipes it empty if exercised by
any test, causing 13 unrelated failures in `tests/unit/strategic/test_opportunities.py` whenever
`tests/unit/worldgeneration/` runs first in the same pytest process

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found while testing `TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION` (earlier this session):
running `tests/unit/worldgeneration/` together with `tests/unit/strategic/test_opportunities.py`
in one pytest process produces 13 failures (`assert 0 > 0` — `ResourceOpportunityProvider.
get_opportunities()` returns an empty list). Confirmed via `git stash` bisection to be entirely
unrelated to that ticket's own changes — a pre-existing test-isolation gap.

Root cause: `tests/conftest.py` already has a precedented, established fix for this exact class of
bug — `_reset_item_registry` (an autouse fixture) exists specifically because
`AuthoritativeApplyPipeline.refine()` calls `ItemRegistry.bootstrap(catalog)` on every real
pipeline run, which can corrupt `ItemRegistry` state for later tests if not reset. `ResourceRegistry`
has the identical real-code hazard (`src/runtime/bootstrap.py:112`,
`ResourceRegistry.bootstrap({})` — an empty dict) but was never given the equivalent fixture. Once
a `worldgeneration` test exercises that bootstrap path, `ResourceRegistry._resources` stays empty
for the rest of the process, so `ResourceOpportunityProvider.get_opportunities()`'s own
`ResourceRegistry.contains(node.kind)` check silently filters out every real resource kind
(`wood`, `herb`, `iron_vein`, etc.) in any test that runs afterward.

## Scope
Add an autouse `_reset_resource_registry` fixture to `tests/conftest.py`, mirroring
`_reset_item_registry`'s own established pattern exactly: capture the canonical post-import
`ResourceRegistry._resources` state once at module load, restore it before and after every test.

## Out of Scope
- Auditing every other registry in `src/core/registries.py` for the same class of gap — this
  ticket fixes the one confirmed, reproduced case.

## Acceptance Criteria
- [x] `tests/unit/worldgeneration/` + `tests/unit/strategic/test_opportunities.py` run together
      in one process with zero failures
- [x] `tests/unit/strategic/test_opportunities.py` alone still passes unmodified

## Related Tickets
- TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION (DONE, same session — found this while
  testing that ticket's own unrelated change)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/conftest.py` (`_reset_item_registry`, the established pattern this mirrors)
- `src/core/registries.py` (`ResourceRegistry`)
- `src/runtime/bootstrap.py` (the real code path that wipes it)

## Assumptions / Open Questions
None.

## Implementation Notes
Added `_reset_resource_registry` (autouse) to `tests/conftest.py`, capturing
`dict(ResourceRegistry._resources)` once at module import (after `src.core.registries`'s own
import-time bootstrap has already populated it with the full real catalog), restoring it before
and after every test — identical shape to `_reset_item_registry`.

## Test Summary
`tests/unit/worldgeneration/ + tests/unit/strategic/test_opportunities.py` together: 0 failures
(previously 13). Full `tests/unit/strategic/test_opportunities.py` alone: unchanged, still passes.
Broader scoped re-run (`tests/unit/worldbuilding/`, `tests/unit/worldgeneration/`,
`tests/unit/worldassembly/`, `tests/unit/strategic/`, `tests/unit/combat/`): no new failures
introduced.

## Files Changed
- `tests/conftest.py` — added `_reset_resource_registry` autouse fixture.

## Completion Summary
Fixed a real, reproducible, pre-existing test-isolation bug using the exact established pattern
this repo already uses for the identical class of bug on a sibling registry (`ItemRegistry`) —
found while testing unrelated combat work this session, root-caused fully, and fixed as a
proportionate hotfix rather than left as an open ticket.
