---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-CERT-EVIDENCE-LEVELS
phase: open
date: 2026-06-14
tags: [certification, evidence, canonical-state, performance]
---

# TCK-20260614-CERT-EVIDENCE-LEVELS

## Title
Add EvidenceLevel enum and optional full canonical state export to certification

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
After the serialization boundary is fixed (TCK-20260614-CERT-SAFE-SERIAL) and the recorder is refactored (TCK-20260614-CERT-RECORDER-REFACTOR), full state evidence must still be available for debugging emergent behavior. This ticket introduces the `EvidenceLevel` enum (`SUMMARY` / `COMPACT` / `FULL`), wires it into `CertificationHarness`, and exports full canonical state as a separate artifact file when `FULL` is requested. The canonical state path uses `CanonicalStateHasher.to_canonical_data()` — the already-established deterministic serialization boundary.

## Scope
- Add `EvidenceLevel(str, Enum)` in `src/certification/models.py` with values: `SUMMARY = "summary"`, `COMPACT = "compact"`, `FULL = "full"`
- Update `CertificationResult.to_artifact_dict(self, evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY) -> dict`:
  - `SUMMARY`: `final_state=None`, `final_state_summary=<compact>`, `final_state_artifact=None`
  - `COMPACT`: include additional selected state slices (entity sample, resource snapshot) in `final_state_summary`
  - `FULL`: `final_state=None`, `final_state_summary=<compact>`, `final_state_artifact="state/<run_id>.final_state.canonical.json"`
- Update `CertificationHarness.run_scenario()` to accept optional `evidence_level: EvidenceLevel = EvidenceLevel.SUMMARY` parameter
- When `evidence_level == FULL`, after proof recording: call `CanonicalStateHasher.to_canonical_data(kernel.state)` and write to `<output_dir>/state/<run_id>.final_state.canonical.json`
- Include `final_state_hash` (SHA-256 of the canonical JSON) in the per-run artifact dict when full evidence is written
- Update `CertificationRecorder.record()` to accept `evidence_level` and pass it to `result.to_artifact_dict(evidence_level)`
- Never embed full state in `proof_index.json` regardless of evidence level

## Out of Scope
- Changing the default CI/release behavior — default remains `SUMMARY`
- Changing `CanonicalStateHasher` implementation
- Adding UI or report rendering for full evidence files

## Acceptance Criteria
- `EvidenceLevel` enum exists in `src/certification/models.py` with three values
- `CertificationHarness.run_scenario()` accepts `evidence_level` parameter (default `SUMMARY`)
- When called with `evidence_level=EvidenceLevel.FULL`, a file appears at `<output_dir>/state/<run_id>.final_state.canonical.json`
- The full state file uses `CanonicalStateHasher.to_canonical_data()` output — not `asdict()`
- `proof_index.json` never contains full state data regardless of evidence level
- Per-run artifact dict has `final_state_artifact` pointing to the relative path when FULL, `None` otherwise
- Existing tests pass (default is SUMMARY — no behavior change for existing callers)
- New test `test_full_evidence_writes_canonical_state_file` passes

## Related Tickets
- TCK-20260614-CERT-SAFE-SERIAL (must be completed first)
- TCK-20260614-CERT-RECORDER-REFACTOR (must be completed first)
- TCK-20260614-CERT-MANIFEST-SNAPSHOT (parallel — writes manifest_snapshot.json to the same output dir; coordinate output_dir layout)

## Related Docs
- `docs/engine/contracts/certification_contract_me.md` — Milestone E: Machine-Readable Certification Law; `manifest_snapshot.json` requirement is handled by TCK-20260614-CERT-MANIFEST-SNAPSHOT (separate ticket)
- `docs/engine/contracts/certification_contract.md` — M9 binding law for run semantics
- `docs/engine/contracts/observability_artifact_contract.md` — section 4: `proofs_bundle.json` is machine-readable ground truth; even with per-run side files, the bundle is never removed
- `docs/engine/performance_contract.md`
- `docs/parity_ledger/infrastructure.yaml`

## Related Stored Artifacts
- `memory_issue.md` (source investigation)

## Related Code Areas
- `src/certification/models.py:92` — `CertificationResult` and `to_artifact_dict()`
- `src/certification/harness.py:62` — `run_scenario()` method
- `src/certification/recorder.py:17` — `record()` method
- `src/engine/checkpoint.py:11` — `CanonicalStateHasher.to_canonical_data()` / `to_canonical_json()`
- `src/core/state.py:981` — `AuthoritativeState` (input to canonical hasher)

## Assumptions / Open Questions
- `CanonicalStateHasher.to_canonical_data(state)` is a pure function that does not mutate state — verify at `src/engine/checkpoint.py:36`
- COMPACT level: exact additional fields to include are not specified in the proposal — define as `entity_sample` (first 5 entity IDs) and `resource_snapshot` (top 5 resource nodes by quantity), or leave COMPACT behavior identical to SUMMARY until a caller requests it
- `run_id` field on `CertificationResult` — needed to construct the state artifact filename; verify it exists

## Implementation Notes
- Full evidence write should be wrapped in try/except — failure to write optional artifact must not fail the certification run (log warning, set `final_state_artifact=None`)
- State file directory: `<output_dir>/state/` — create with `mkdir(parents=True, exist_ok=True)`
- Compute `final_state_hash` as `hashlib.sha256(canonical_json_bytes).hexdigest()`

## Test Summary
- `tests/certification/test_evidence_levels.py` (new file):
  - `test_summary_level_has_no_state_artifact` — default level produces no state file
  - `test_full_evidence_writes_canonical_state_file` — FULL level writes `state/<run_id>.final_state.canonical.json`
  - `test_full_evidence_uses_canonical_hasher_not_asdict` — monkeypatch `asdict` to raise; assert FULL evidence write still works
  - `test_proof_index_never_contains_full_state` — FULL evidence level does not leak state into `proof_index.json`
- Run: `pytest tests/certification/ -v`

## Files Changed
_(filled after implementation)_

## Completion Summary
_(filled after implementation)_
