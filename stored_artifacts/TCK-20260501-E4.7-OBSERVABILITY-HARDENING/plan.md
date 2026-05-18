# Walkthrough — Phase E4.7 Observability & Certification

We have completed the authoritative hardening of the V2 Engine's observability stack. This phase ensures that every engine failure (rejection) is now a first-class, auditable "Truth Signal" rather than a silent drop.

## Changes Made

### 1. Rejection Registry Infrastructure
- **AuthoritativeState**: Added `rejection_registry` to store cumulative failure counts (e.g., `OCCUPANCY_CONFLICT`, `READINESS_NOT_READY`).
- **StateUpdate**: Added `rejections_delta` to carry per-tick failures through the pipeline.
- **ApplyPath**: Modified `apply_generation` to merge tick deltas into the persistent registry authoritatively.

### 2. Pipeline Injection
- **Pipeline Resolution**: Injected rejection tracking into:
    - `_resolve_occupancy_conflicts`: Captures tile clashes.
    - `_route_movement_intent`: Captures blocked paths.
    - `_route_combat_intent`: Captures target invalidity or distance failures.
    - `_route_action_intent`: Captures readiness failures.
    - `_resolve_resource_transactions`: Captures inventory-full or cost-unaffordable rejections.

### 3. Observability & Reporting
- **MetricsService**: Surface `rejection_counts` in `WorldMetrics`.
- **CertificationReporter**: Extended JSON report with an `observability` section containing rejections, social shifts, and active blockers.

## Verification Results

### Automated Tests
- **test_rejection_tracking_certification**: Successfully verified that simultaneous movement to a single tile triggers `OCCUPANCY_CONFLICT` and acting without readiness triggers `READINESS_NOT_READY`.
- **test_final_certification_report_generation**: Verified the reporter correctly packages these signals for external audit.

```bash
pytest tests/engine/test_certification_scenarios.py
```
**Result**: `2 passed`

### Proof of Work
- [resource_v2_e4_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e4_phases.md)
- [logic_checklist_exhaustive_v2.md](file:///home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive_v2.md)
- [test_certification_scenarios.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/engine/test_certification_scenarios.py)

## Next Steps
The engine is now "Logic Hardened" and "Observability Hardened" for Phase 13 Legacy Retirement. We have 100% visibility into why any intent fails, enabling a full audit of legacy parity.
