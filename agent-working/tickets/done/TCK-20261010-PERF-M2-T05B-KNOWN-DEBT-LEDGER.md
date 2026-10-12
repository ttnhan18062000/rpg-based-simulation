---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER
phase: done
date: 2026-10-10
tags: [performance, benchmarking, testing, regression]
---

# TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER

## Title
PERF-M2-T05b: Perf known-debt ledger as the second user of the shared known-reds module

## Status
DONE

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
- [x] docs/performance/known_debt_ledger.yaml loads through the shared known-reds module with owner, ticket, added_on, expires_on, kind and expected_signature. A test shows the lint rejects an expired entry, a shadowed entry and an ownerless entry.
- [x] The expected_signature format is defined in docs/performance/perf_baseline_policy.md, and a test rejects a malformed signature
- [x] The ticket's git diff touches no file under src/

## Related Tickets
- TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE
- TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
- TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE

## Related Docs
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md ("Delivery plan")
- docs/plans/test_architecture/reference/baseline_change_policy.md (testing expects it by 2026-10-13; until then follow docs/plans/test_architecture/reference/rpg_gate_baseline_format.md)
- docs/performance/perf_baseline_policy.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/test_architecture/known_reds.py (the shared module, merged in #502: one frozen RegistrySpec per registry)
- tools/test_architecture/slow_known_reds.yaml (the first user's data)
- tools/perf/

## Assumptions / Open Questions
- UNBLOCKED 2026-10-11: the shared module merged in #502. Perf adds its own RegistrySpec and file, with expected_signature in optional_fields and strict_fields=True. That case is unit-tested upstream (test_a_registry_can_declare_an_extension_field_without_touching_the_rules). No change to the shared rules (testing-planner, #488).
- T03 and T04 do not need the ledger, so this does not block them; T06 needs it

## Implementation Notes
- Decisions: `agent-working/stored_artifacts/TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER/plan.md`. `expected_signature` is `<STATE>:<check>`, a closed vocabulary (STATE in REGRESSION, INCONCLUSIVE, NOT_APPLICABLE; check = a `compare()` check name); a test pins the check names to `src/perf/benchmark_record.py`.
- The ledger ships empty: no lane has an owned red yet. The first real entry is expected from T08 or the mixed-state spawn fix, with a ticket.
- No change to `tools/test_architecture/` and nothing under `src/`.

## Test Summary
- New: `tests/unit/perf/test_known_debt.py` (17 tests, passing). Not run: the full suite.

## Files Changed
- `tools/perf/known_debt.py` (new), `tests/unit/perf/test_known_debt.py` (new), `docs/performance/known_debt_ledger.yaml` (new), `docs/performance/perf_baseline_policy.md` (section 4), `docs/parity_ledger/infrastructure.yaml` (INFRA-434), this ticket and its artifacts, the T03b ticket and SEQUENCE (planner commit).

## Completion Summary
Perf's known-debt ledger exists as the second user of the shared known-reds module: its own `RegistrySpec` with `expected_signature`, an empty `known_debt_ledger.yaml`, the signature format in the baseline policy, and a lint (`python3 -m tools.perf.known_debt`) with tests. The shared rules are unchanged.
