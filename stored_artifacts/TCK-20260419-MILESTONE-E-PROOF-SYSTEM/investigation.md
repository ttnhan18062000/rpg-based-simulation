# Investigation: Milestone E Infrastructure

## Current State Analysis (M10 Baseline)
- Certification harness exists but lacks provenance (SHA pinning).
- Results are machine-readable but not strictly derivative of a "Proof Bundle".
- Reporting logic allows implicit "universal" performance claims if not careful.
- `manifest.json` does not yet explicitly gate releases based on target-certified evidence.

## Key Findings
- **Field Mismatch**: Telemetry signal `queue_utilization` is inconsistent with M7 `capacity_utilization`.
- **Environment Capture**: HW class detection is hardcoded; needs explicit separation between detectedFacts and effectiveClass.
- **State Pollution**: `harness.py` hardcoded path overwrites production results during test runs.

## Decisions
- Terminology must follow `FAILED_*` taxonomy for consistency.
- `reports/release_proof/` is the authoritative persistent directory for the gate.
- SHA capture must be automated via `git rev-parse HEAD`.
