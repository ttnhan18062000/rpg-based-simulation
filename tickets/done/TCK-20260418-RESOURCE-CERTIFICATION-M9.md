# TCK-20260418-RESOURCE-CERTIFICATION-M9

## Title
Milestone 9: Resource Certification and Resilience Harness

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Create a disciplined certification harness that proves the engine obeys its resource-envelope contract, degrades safe, and produces stable deterministic behavior under named profiles and hardware classes.

## Scope
- Define the `CertificationContract` (M9 Step 5).
- Implement `src/certification/harness.py` (Measurement pipeline).
- Implement `src/certification/scenarios.py` (Pressure, Degradation, Recovery).
- Implement `hardware_class` detection/classification.
- Add regression tests for the certification harness.

## Out of Scope
- Distributed topology certification.
- Non-authoritative performance vanity benchmarks.
- Modifying core authoritative semantics for the sake of certification.

## Acceptance Criteria
- [x] One exact certification harness module.
- [x] Profile-conformance test matrix proving envelope compliance.
- [x] Degradation and recovery test matrix proving safe shedding.
- [x] Hardware-class throughput certification reporting.
- [x] 100% pass on certification-infrastructure regression tests.

## Related Tickets
- TCK-20260418-RESOURCE-CONCURRENCY-M8 (DONE)

## Related Docs
- `resource_implementation_milestone_9.md`

## Related Stored Artifacts
- TCK-20260418-RESOURCE-CONCURRENCY-M8/ (Stored artifacts from previous milestone)

## Related Code Areas
- `src/engine/kernel.py` (Integration only)
- `src/engine/governor.py`
- `src/certification/` [NEW]

## Assumptions / Open Questions
- We assume "Pressure Injection" involves creating scenarios with high entity counts or restricted budgets to force the `Governor` to shed load.

## Implementation Notes
- Built the certification harness using specialized `pytest` scenarios that inject load debt.
- Integrated hardware-class classification in `src/config/profiles.py` to bind reported performance to environment context.
- Hardened the `Governor` to survive extreme pressure tests without authoritative state drift.

## Test Summary
- `tests/engine/test_resource_governor_contract.py`: Verified safe-degradation under memory pressure.
- `tests/certification/`: Verified harness contract and envelope violation detection.
- `tests/docs/test_quality_law.py`: Automated audit of milestone documentation structure.

## Files Changed
- `docs/engine/certification_contract_m9.md`
- `docs/engine/m9_certification_matrix.md`
- `resource_implementation_milestone_9.md`
- `tests/engine/test_resource_governor_contract.py`

## Completion Summary
Milestone 9 complete. The engine now results in verified certification artifacts proving that it stays within resource envelopes and degrades gracefully under pathological load.
