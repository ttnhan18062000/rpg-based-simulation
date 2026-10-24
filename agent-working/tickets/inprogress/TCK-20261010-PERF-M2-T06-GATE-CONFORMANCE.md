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
INPROGRESS

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
- Known-debt matching (added 2026-10-12 from the #525 review): `Outcome` in src/perf/benchmark_record.py is only `(state, reason)`, so no code can match a real outcome against a known-debt `expected_signature` (`<STATE>:<check>`, PERF-M2-T05b) without parsing the reason string. Add a typed `check` field to `Outcome`, set by each `_check_*` in `compare()` (None for PASS). Match ledger entries (tools/perf/known_debt.py) against `state` and `check`, never against `reason`. src/perf/ is perf-owned, so no lift is needed. Keep BenchmarkRecord serialization backward-compatible, or bump the schema MINOR version.

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

- [ ] `Outcome` carries a typed `check` naming the `compare()` check that produced it. A test shows a known-debt entry matching on `state` + `check`, and no code path matches a ledger entry by parsing `Outcome.reason`.

## Related Tickets
- TCK-20261003-PERF-M2-CLAUSE-INVENTORY
- TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
- TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE
- TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
- TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER

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
- src/perf/benchmark_record.py (`Outcome`, `compare()`)
- tools/perf/known_debt.py
- tools/perf/perf_threshold_inventory.py
- tests/tools/perf_assertions.py
- docs/engine/performance_contract.md
- docs/engine/contracts/certification_contract.md
- docs/performance/performance_clause_inventory.md

## Assumptions / Open Questions
- **Unblocked 2026-10-24:** T02b, T03, T03b, T04, T05, T05b, T07, T08 and PERFBUDGET-RETIRE are all DONE on main.
- **Tripwire threshold: decided (owner, 2026-10-24, option A, logged on #715 issuecomment-6386636889).** §5 publishes `max(5.0 ms, base x 1.40)` as **final, report-only**. The edit drops the "provisional" wording and the "must be recalibrated ... on the CI runner once the CI step lands" sentence. It cites the evidence: the CI A/A runs 40106785877 (main 10422cedd: max head/base deviation 0.206 idle, 0.095 movement) and 40109334529 (main 667552eb9: 0.005 / 0.010), 8 trials each, plus the 2026-10-10 host calibration (0.35, 44 pairs, 6-vCPU VM). It states the limit: the CI evidence covers only 2 runner VMs, and the tripwire detects only changes above about 40 %. Evidence write-up: #593 issuecomment-6386482656. Options B (1.30x) and C (more A/A runs) were not chosen. No code or `TRIPWIRE_THRESHOLDS` change.
- **`docs/engine` lift:** `docs/engine/performance_contract.md` is rpg-owned. Asked on #593 (perf issuecomment-6386482656, relayed by lead issuecomment-6386486051); it is NOT yet granted. The §3.3/§5 edit is the PR's last commit and waits for rpg's lift. Every other scope item (gate_conformance.yaml, the tests/docs test, `Outcome.check` in `src/perf/`, the certification_contract grep guard) is perf-owned and may start now. Note: certification_contract.md is also under `docs/engine/`. The grep guard only reads it; if any edit to it turns out to be needed, it is covered by the same lift.
- The D-9/D-10 rename already landed in #306, so that scope item is a verify-only no-op
- P1 owner approval is a human gate that the ticket cannot self-close
- About 30 test files call the helpers today (T03 has landed, so the map can be written now). Re-count the call sites at implementation time (§5.2 says 56).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
