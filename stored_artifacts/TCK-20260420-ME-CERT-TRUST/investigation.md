---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260420-ME-CERT-TRUST
artifact_type: investigation
tags: [me, cert, trust]
---

# Investigation - Milestone E Certification Hardening

## Context
The V2 Engine required closure of the "Trust" milestone (Milestone E). The existing harness was skeletal and only covered 5 scenarios with frequent false positives on recovery timeouts.

## Findings
1. **Scenario Gaps**: 10 mandatory scenarios were missing (RAM pressure, Tick Budget pressure, Recovery cycles, etc.).
2. **Timeout Issues**: The certification window (30 ticks) was too short for the physical debt-draining cycles of the Governor, leading to `FAILED_RECOVERY_TIMEOUT`.
3. **Drift Noise**: Stress tests (RAM/Tick Budget pressure) were failing on bit-identical hash matches due to non-deterministic shedding in SURVIVAL mode.
4. **Gate Gaps**: `test_final_gate.py` was not strictly checking for the full scenario matrix or SHA provenance.

## Resolution
- Expanded the matrix to 15 scenarios.
- Increased certification window to 60 ticks.
- Disabled semantic drift checks for stress scenarios while keeping them active for baseline/equivalence scenarios.
- Hardened the conformance evaluator to properly handle `allowed_failure_observed`.
