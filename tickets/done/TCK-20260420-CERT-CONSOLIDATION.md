# TCK-20260420-CERT-CONSOLIDATION

## Title
Certification Artifact Consolidation

## Status
DONE

## Request Summary
The user requested a reduction in the file count in `reports/release_proof/`, which was cluttered with 60+ individual scenario JSON and MD files.

## Scope
- Update `CertificationRecorder` to support a consolidated `proofs_bundle.json`.
- Update `CertificationRecorder` to generate a unified `release_report.md`.
- Update `test_final_gate.py` to verify conformance using the new bundle.
- Fix protocol TypeErrors identified during execution.

## Acceptance Criteria
- [x] `reports/release_proof/` contains exactly 3 authoritative files.
- [x] `proofs_bundle.json` contains all 30 required scenario results.
- [x] `release_report.md` provides a summary of all scenarios.
- [x] `pytest tests_v2/certification/test_final_gate.py` passes 100%.

## Related Tickets
- `TCK-20260420-CORE-MOVEMENT-SLICE`

## Related Docs
- `docs/engine/certification_contract_me.md`
- `docs/engine/manifest.json`

## Implementation Notes
- Reordered `WorkerPacket` fields to ensure non-default arguments precede defaults.
- Added missing `json` and `field` imports in `recorder.py` and `worker_protocol.py`.

## Test Summary
- `scripts/refresh_proofs.py`: Successfully re-certified 30 scenario targets into the bundle.
- `tests_v2/certification/test_final_gate.py`: 3/3 passed (including manifest compliance).

## Files Changed
- `src_v2/certification/recorder.py`
- `src_v2/core/worker_protocol.py`
- `tests_v2/certification/test_final_gate.py`

## Completion Summary
Consolidated all certification evidence into a single machine-readable bundle and a unified human-readable report. This drastically reduces repository noise while hardening the release gate's ability to verify the entire engine state in a single pass.
