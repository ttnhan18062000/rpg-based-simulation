---
status: done
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D10-TESTS
phase: open
date: 2026-06-18
tags: [audit, test-coverage, regression-risk, test-suite-health]
---

# TCK-20260618-AUDIT-D10-TESTS

## Title
D10 — Test Coverage & Regression Risk Audit

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Audit the current test suite for coverage breadth, failure distribution, and regression risk across the simulation codebase. Document which domains are well-tested, which are fragile, and which have known systematic failures.

## Scope
- Survey test count, file count, and breakdown by domain/layer
- Identify active failures (count, categories, systemic causes)
- Classify teardown contamination issues
- Assess coverage gaps relative to the mechanics and engine contracts
- Produce a scored D10 audit document

## Out of Scope
- Fixing failing tests
- Writing new tests
- Coverage percentage measurement (requires instrumentation run)

## Acceptance Criteria
- `docs/audits/D10_test_coverage.md` written with domain-specific scoring rubric
- Key findings scored with risk ratings
- Recommended follow-up tickets listed
- `audit_dimensions.md` D10 row updated to `done`
- Working log entry appended
- Agent monitoring records written

## Related Tickets
- TCK-20260618-AUDIT-EPIC (parent)
- TCK-20260618-AUDIT-D15-INSPECT (sibling — test coverage of D15 gaps noted there)

## Related Docs
- `docs/testing/v2_test_taxonomy.md`
- `docs/audits/audit_dimensions.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260618-AUDIT-D10/`

## Related Code Areas
- `tests/` (all domains)
- `src/` (all domains)

## Assumptions / Open Questions
- Test run data already collected: 4045 tests, 58 failures, 16 teardown errors from FallbackRestrictedError
- Coverage% not measured — structural assessment only

## Implementation Notes
Data collected in prior session:
- 4045 tests collected across 766 test files
- 58 failures in broad unit+integration run
- 16 FallbackRestrictedError teardown errors in tests/unit/core/test_registry_bridge.py and related
- 4 inventory test failures (resource/ domain) — connect to D17 uncertain finding on slot/weight defaults

## Test Summary
N/A (this IS the test audit ticket)

## Files Changed
- docs/audits/D10_test_coverage.md (create)
- docs/audits/audit_dimensions.md (update D10 row)
- tickets/working_log.csv (append)
- agent-monitoring/runs.jsonl (append)
- agent-monitoring/events.jsonl (append)

## Completion Summary
D10 audit complete. Ran `pytest tests/unit tests/integration` (3,292 tests). Found 121 failures + 34 errors across 9 distinct root-cause clusters. Top risk: teardown mode contamination (14/15) and `ItemStack.position` AttributeError (12/15). Determinism breach (bare random usage, 11/15) is a P0 engine contract violation. Strategic AI (41 files), unit observability (81 files), and world (33 files) are the most regression-protected domains. Audit document written at `docs/audits/D10_test_coverage.md` with 3×5 Regression Risk rubric. 9 follow-up tickets recommended (3 P0, 4 P1, 2 P2).
