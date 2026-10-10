---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER
phase: open
date: 2026-10-10
tags: [performance, benchmarking, testing, regression]
---

# TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER

## Title
PERF-M2-T05b: Perf known-debt ledger as the second user of the shared known-reds module

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Split out of TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE on 2026-10-10 by perf-planner, so the rest of T05 is not blocked. The M2 plan and testing-planner (#475) agreed that perf's known-debt ledger is the second user of testing's shared known-reds registry module, with one perf extension field, expected_signature. That module (TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE) is not extracted yet; the logic is still inline in slow_regression_report.py. Perf must not build an interim loader, so the module is extracted only once.

## Scope
- Add docs/performance/known_debt_ledger.yaml, loaded through the shared known-reds module with the shared fields (owner, ticket, added_on, expires_on, kind) plus expected_signature
- Define the expected_signature format (regex, scenario+phase key, or clause id) and document it in docs/performance/perf_baseline_policy.md
- Add the lint tests through the shared module's lint

## Out of Scope
- Extracting or changing the shared known-reds module (testing-owned)
- Any change under src/ (OD-8)
- Making any perf check blocking
- The baseline promotion tool (PERF-M2-T05)

## Acceptance Criteria
- [ ] docs/performance/known_debt_ledger.yaml loads through the shared known-reds module with owner, ticket, added_on, expires_on, kind and expected_signature. A test shows the lint rejects an expired entry, a shadowed entry and an ownerless entry.
- [ ] The expected_signature format is defined in docs/performance/perf_baseline_policy.md, and a test rejects a malformed signature
- [ ] The ticket's git diff touches no file under src/

## Related Tickets
- TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE
- TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
- TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE

## Related Docs
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md ("Delivery plan")
- docs/plans/test_architecture/reference/baseline_change_policy.md (not yet on main)
- docs/performance/perf_baseline_policy.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/test_architecture/slow_known_reds.yaml (the first user's data)
- tools/perf/

## Assumptions / Open Questions
- Blocked until TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE lands the shared module on main
- T03 and T04 do not need the ledger, so this does not block them; T06 needs it

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
