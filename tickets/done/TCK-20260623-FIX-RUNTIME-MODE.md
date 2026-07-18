---
status: done
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-RUNTIME-MODE
phase: done
date: 2026-06-23
tags: [test-repair, registry, content-mode, enum]
---

# TCK-20260623-FIX-RUNTIME-MODE

## Title
Fix RuntimeContentMode.V2 AttributeError (5 failures)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tests/unit/core/test_registry_adapters.py` fails with:
```
AttributeError: type object 'RuntimeContentMode' has no attribute 'V2'
```
on all 5 test methods. The `RuntimeContentMode.V2` enum variant was renamed or removed
from `src/core/modes.py` without updating the test file. This is distinct from the
FallbackRestrictedError teardown contamination (TCK-20260623-FIX-TEST-TEARDOWN) —
these are actual test failures, not teardown errors.

Note: one of the 5 failures also shows a FallbackRestrictedError at teardown, suggesting
the teardown contamination overlaps here. Fix the `V2` attribute first; the teardown
error may disappear once TCK-20260623-FIX-TEST-TEARDOWN is applied.

## Scope
- Find the current name of the mode that was previously `RuntimeContentMode.V2`
- Update the 5 test call sites in `test_registry_adapters.py` to use the current variant name
- If `V2` was not renamed but deleted, determine the intended replacement and update accordingly
- Do NOT change production `RuntimeContentMode` logic — test-side fix only (unless `V2` was
  the correct variant and was accidentally removed, in which case restore it)

## Out of Scope
- Registry logic changes
- Catalog mode changes
- Other test files

## Acceptance Criteria
- `tests/unit/core/test_registry_adapters.py` — all 5 tests pass without AttributeError
- No `RuntimeContentMode` AttributeError anywhere in the test suite

## Related Tickets
- TCK-20260623-FIX-TEST-TEARDOWN (teardown contamination that also affects this file)

## Related Docs
- `docs/audits/D10_test_coverage.md` F1 (registry mode contamination)

## Related Code Areas
- `src/core/modes.py` (`RuntimeContentMode` enum definition)
- `tests/unit/core/test_registry_adapters.py` (5 failing call sites)

## Assumptions / Open Questions
- Was `V2` renamed to `CATALOG`, `CATALOG_ONLY`, or something else? Check `src/core/modes.py`.
- Is there a git log entry for the rename?

## Implementation Notes
Hotfix tier — no staging artifacts required.
1. Read `src/core/modes.py` — find all `RuntimeContentMode` members
2. Match against what test expects (`V2`) to find the replacement name
3. Update `test_registry_adapters.py` with correct name

## Test Summary
Run: `pytest tests/unit/core/test_registry_adapters.py --tb=short`

## Files Changed
- `tests/unit/core/test_registry_adapters.py` — replaced 4 `RuntimeContentMode.V2` with `CATALOG_WITH_COMPATIBILITY`; fixed `test_fallback_usage_reported_in_legacy_mode` to use `LEGACY_FALLBACK` mode

## Completion Summary
TCK-20260608-RUNTIME-MODE-EXPLICIT replaced MIGRATION/V2 with four explicit modes; 5 tests still used the removed .V2 attribute. Replaced with CATALOG_WITH_COMPATIBILITY (the V2 equivalent for catalog-backed mode). Also fixed one additional seed_phase1_content(None) call in the same file. 14/14 tests in the file pass.
