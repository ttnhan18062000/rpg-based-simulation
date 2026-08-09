---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260809-TEST-ISOLATION-ITEM-REGISTRY-STONE
phase: open
date: 2026-08-09
tags: [testing]
---

# TCK-20260809-TEST-ISOLATION-ITEM-REGISTRY-STONE

## Title
`src.core.registries.ItemRegistry` — a distinct class from `src.core.items.ItemRegistry`, which
`tests/conftest.py` already resets — had zero test-isolation reset protection, despite the
identical real-code hazard (`src/runtime/bootstrap.py` calls its `.bootstrap({})` with an empty
dict), causing `tests/unit/strategic/test_registries.py::test_referential_integrity` to fail
under specific test-ordering combinations

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found while testing `TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE` (earlier this
session): a third pre-existing test-isolation failure (`test_referential_integrity`,
`ItemRegistry.contains('stone')` returning `False`), confirmed via `git stash` bisection to be
unrelated to that ticket's own changes.

Root cause: there are **two entirely separate `ItemRegistry` classes** in this codebase —
`src.core.items.ItemRegistry` (a smaller, hardcoded-catalog class) and
`src.core.registries.ItemRegistry` (a distinct class with its own separate `_items` dict,
confirmed via direct identity check: `src.core.items.ItemRegistry is not
src.core.registries.ItemRegistry`). `tests/conftest.py`'s existing `_reset_item_registry` fixture
only ever resets the `src.core.items` one. `src/runtime/bootstrap.py` calls
`src.core.registries.ItemRegistry.bootstrap({})` (an empty dict) on the real runtime bootstrap
path — the identical hazard already fixed for `ResourceRegistry`
(`TCK-20260809-TEST-ISOLATION-RESOURCE-REGISTRY-RESET`) — but this second `ItemRegistry` had zero
reset protection until now.

## Scope
Add an autouse `_reset_registries_item_registry` fixture to `tests/conftest.py`, mirroring the
already-established `_reset_item_registry`/`_reset_resource_registry` pattern exactly, targeting
`src.core.registries.ItemRegistry` specifically.

## Out of Scope
- Consolidating the two separate `ItemRegistry` classes into one — a real, larger architectural
  question (why do two exist independently?) not decided or investigated here.
- Auditing every other registry for the same class of gap beyond the one confirmed, reproduced
  case.

## Acceptance Criteria
- [x] `tests/unit/worldgeneration/` + `tests/unit/strategic/test_registries.py` run together with
      zero failures
- [x] `tests/unit/strategic/test_registries.py` alone still passes unmodified

## Related Tickets
- TCK-20260809-TEST-ISOLATION-RESOURCE-REGISTRY-RESET (DONE, same session — the identical class
  of bug, same real hazard pattern, fixed for `ResourceRegistry` first)
- TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (DONE, same session — found this while
  testing that ticket's own unrelated change)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/conftest.py` (`_reset_item_registry`, `_reset_resource_registry`, the established
  pattern this mirrors)
- `src/core/registries.py` (`ItemRegistry`, distinct from `src/core/items.py`'s own class)
- `src/runtime/bootstrap.py` (the real code path that wipes it)

## Assumptions / Open Questions
None.

## Implementation Notes
Added `_reset_registries_item_registry` (autouse) to `tests/conftest.py`, capturing
`dict(RegistriesItemRegistry._items)` (aliased import to disambiguate from the pre-existing
`src.core.items.ItemRegistry` import) once at module import (after `src.core.registries`'s own
import-time bootstrap has already populated it with the full real catalog — confirmed directly:
`registries.ItemRegistry.contains('stone')` is `True` with 36 real items at that exact point),
restoring it before and after every test — identical shape to the two existing fixtures.

## Test Summary
`tests/unit/worldgeneration/` + `tests/unit/strategic/test_registries.py` together: 39/39 pass
(previously 1 failure). Broader scoped re-run (`tests/unit/strategic/`,
`tests/unit/worldgeneration/`, `tests/unit/worldbuilding/`, `tests/unit/worldassembly/`,
`tests/unit/combat/`, `tests/unit/core/`, `tests/unit/content/`, `tests/unit/economy/`,
`tests/unit/resource/`, `tests/unit/movement/`, `tests/unit/kernel/`, `tests/unit/tactical/`,
`tests/unit/optimization/`, `tests/unit/entities/`, `tests/unit/social/`): 1521 passed, only the
2 already-confirmed-unrelated pre-existing failures remain, zero regressions.

## Files Changed
- `tests/conftest.py` — added `_reset_registries_item_registry` autouse fixture.

## Completion Summary
Fixed the third and (per this session's own real, exhaustive scoped test sweep) apparently last
confirmed pre-existing test-isolation bug in this class — found while testing unrelated combat
work, root-caused fully via direct class-identity inspection, and fixed as a proportionate
hotfix using the exact established pattern this repo now has three real examples of.
