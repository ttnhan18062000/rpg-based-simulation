---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE
phase: open
date: 2026-10-09
tags: [performance, documentation, certification]
---

# TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE

## Title
PERF-M2-T06: P1 contract publication and gate-conformance map

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Have performance_contract.md state the decided thresholds, outcomes and claims (rpg-owned P1, owner approves). Add a new docs/performance/gate_conformance.yaml that maps each live check to a clause or to 'enforces none'. Add a test that fails on an unmapped assert_perf_threshold/perf_check call site. Fix the D-9/D-10 names in certification_contract.md. Depends on T03, T04, T05 and T08. This makes the contract the single clause-level authority (PERF-D4), where every clause says whether a check enforces it today.

Source concern IDs: C7.

## Scope
- Update docs/engine/performance_contract.md §3.3/§5 to publish the tripwire threshold decided in T03, the outcome set and the claim scope per projection, with P1 owner approval. Invent no numbers.
- Create docs/performance/gate_conformance.yaml keyed on file + enclosing function + message/ordinal (not line numbers), mapping each live check to a clause ID from performance_contract.md/performance_clause_inventory.md or 'enforces none'
- Add a tests/docs/ test using tools.perf.perf_threshold_inventory.build_report(REPO_ROOT) that fails on unmapped call sites, unknown clause IDs and stale mappings
- Verify the D-9/D-10 names in docs/engine/contracts/certification_contract.md (already fixed in #306) and add a grep guard instead of repeating the edit
- Decide and document whether non-helper live checks (PerfRegressionGate, long_run_harness comparative checks, CI selectors) are covered by the map

## Out of Scope
- Setting new threshold values (PERF-M2-T03 owns them)
- Making any perf check blocking (OD-8)
- Absorbing or deleting absolute-ceiling call sites (PERF-M2-T03)
- Re-editing certification_contract.md names that already landed in #306

## Acceptance Criteria
- [ ] docs/performance/gate_conformance.yaml exists, and each entry keys a live check (file::function plus the helper call) to either a clause ID present in performance_contract.md / performance_clause_inventory.md or the literal 'enforces none'
- [ ] A new test under tests/docs/ calls tools.perf.perf_threshold_inventory.build_report(REPO_ROOT) and fails, naming file and function, when any assert_perf_threshold/perf_check call site under tests/ (excluding tests/tools/perf_assertions.py) has no gate_conformance.yaml entry. A synthetic tmp_path case shows an unmapped site failing.
- [ ] The same test fails when a gate_conformance.yaml entry names a clause ID that does not exist, or a call site that no longer exists
- [ ] performance_contract.md §3.3/§5 states concrete tripwire threshold values, the outcome set and the claim scope for each projection, and no sentence still says 'The threshold is not yet set'
- [ ] A grep test finds FAILED_DEGRADATION_ORDER, FAILED_RECOVERY (as a bare legacy name) and hardware_class_override_applied in certification_contract.md only within the documented 'earlier name' notes

## Related Tickets
- TCK-20261003-PERF-M2-CLAUSE-INVENTORY
- TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
- TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE
- TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE

## Related Docs
- docs/engine/performance_contract.md
- docs/engine/contracts/certification_contract.md
- docs/performance/performance_clause_inventory.md
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/certification/models.py
- src/perf/long_run_harness.py
- tools/perf/perf_threshold_inventory.py
- tests/tools/perf_assertions.py
- docs/engine/performance_contract.md
- docs/engine/contracts/certification_contract.md
- docs/performance/performance_clause_inventory.md

## Assumptions / Open Questions
- Blocked until PERF-M2-T03, PERF-M2-T04, PERF-M2-T05 and PERF-M2-T08 land. The thresholds it publishes do not exist yet.
- The D-9/D-10 rename already landed in #306, so that scope item is a verify-only no-op
- P1 owner approval is a human gate that the ticket cannot self-close
- About 30 test files call the helpers today. Writing the map before T03 lands would cause churn.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
