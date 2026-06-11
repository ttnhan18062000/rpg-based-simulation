---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260608-REGISTRY-PARITY-SPLIT
phase: done
date: 2026-06-08
tags: [registry, parity, split]
---

# TCK-20260608-REGISTRY-PARITY-SPLIT

## Title
Split registry parity tests into separate strict, compatibility, and legacy-fallback test cases

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The existing registry projection parity test seeds with the old MIGRATION mode and asserts only an aggregate heuristic_count. After the mode expansion (RUNTIME-MODE-EXPLICIT) and the heuristic usage record change (ADAPTER-HEURISTIC-USAGE), the parity test must be split into three independent sub-suites: one proving that CATALOG_STRICT produces zero heuristic_usages, one proving that CATALOG_WITH_COMPATIBILITY produces heuristic_usages with full detail (not just a count), and one proving that LEGACY_FALLBACK seeds only hardcoded records when that mode is selected. This prevents the test suite from proving only compatibility behavior while silently missing strict-mode regressions.

## Scope
- Update tests/integration/content/test_registry_projection_parity.py to split into three distinct test functions or classes
- Add CATALOG_STRICT parity test: asserts heuristic_usages is empty tuple
- Add CATALOG_WITH_COMPATIBILITY parity test: asserts heuristic_usages non-empty and each entry has record_id, adapter, reason
- Add LEGACY_FALLBACK parity test: asserts only hardcoded fallback records are seeded
- Remove or update any assertion that checks only the raw heuristic_count int

## Out of Scope
- Changing adapter logic or mode definitions (covered in other tickets)
- Adding new integration test files beyond test_registry_projection_parity.py

## Acceptance Criteria
- [ ] A strict-mode parity test exists and passes with zero heuristic_usages
- [ ] A compatibility-mode parity test exists and asserts heuristic detail fields (not only count)
- [ ] A legacy-fallback parity test exists and asserts only hardcoded records are seeded when LEGACY_FALLBACK is selected
- [ ] No test asserts only aggregate heuristic_count as the sole correctness proof
- [ ] All three parity tests pass

## Related Tickets
- TCK-20260608-RUNTIME-MODE-EXPLICIT (dependency — must be done first; provides the four mode values)
- TCK-20260608-ADAPTER-HEURISTIC-USAGE (dependency — must be done first; provides heuristic_usages field)

## Related Docs
- docs/engine/authoritative_pipeline.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/integration/content/test_registry_projection_parity.py
- src/core/modes.py
- src/core/registries.py

## Assumptions / Open Questions
- The split is purely a test-layer change; no production logic is modified in this ticket

## Implementation Notes
Test-only change. Added 3 new test functions to test_registry_projection_parity.py covering CATALOG_STRICT (zero heuristic_usages via minimal explicit temp catalog), CATALOG_WITH_COMPATIBILITY (typed detail assertions), and LEGACY_FALLBACK (hardcoded records). No production code changed.

## Test Summary
8 tests pass (5 original + 3 new).

## Files Changed
- tests/integration/content/test_registry_projection_parity.py

## Completion Summary
Split registry parity tests into three distinct sub-suites covering all three runtime content modes. All 8 integration tests pass.
