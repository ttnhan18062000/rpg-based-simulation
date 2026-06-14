---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-CERT-EVIDENCE-LEVELS
phase: done
date: 2026-06-14
tags: [certification, evidence, canonical-state, performance]
---

# TCK-20260614-CERT-EVIDENCE-LEVELS

## Title
Add EvidenceLevel enum and optional full canonical state export to certification

## Status
DONE

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
- OPEN-1 (coordination timing): _write_full_evidence() is called BEFORE recorder.record() in
  _persist_proof_bundle(). The resolved path/hash (or None) is passed into recorder.record(),
  which passes them to to_artifact_dict(). The bundle entry never carries a speculative path.
- to_artifact_dict() signature changed to accept evidence_level, final_state_artifact_path,
  final_state_hash — all defaulted so existing no-arg callers are unaffected.
- EvidenceLevel placed above ArenaStopCondition in models.py. Uses str,Enum pattern.
- _final_state_summary_compact() delegates to _final_state_summary() for the base dict, then
  adds entity_sample (first 5 IDs sorted ascending as strings) and resource_snapshot (top 5
  node IDs by quantity descending). PoisonState-safe via getattr.
- _write_full_evidence() wrapped in try/except — always non-fatal. Returns None on failure.
  Uses CanonicalStateHasher.to_canonical_data() (never asdict). Pretty JSON written to disk;
  compact JSON used for SHA-256 hash computation (matches get_hash() format).
- State file directory: <output_dir>/state/ — created with mkdir(parents=True, exist_ok=True).
- final_state_hash is hashlib.sha256(compact_json.encode("utf-8")).hexdigest().
- FakeState in tests uses _FakeCanonicalObj instances (with to_canonical_dict()) to satisfy
  CanonicalStateHasher.to_canonical_data() requirements for TC-7/TC-8/TC-11.

## Deviations from Plan
- TC-6 in the test plan described calling to_artifact_dict(FULL) directly and asserting
  final_state_artifact path. After OPEN-1 resolution, to_artifact_dict() does NOT compute
  the path — it receives it as a param. TC-6 was adapted to test _write_full_evidence()
  return value directly (still covers the same AC: path is as expected).
- FakeState required _FakeCanonicalObj children (with to_canonical_dict()) to be compatible
  with CanonicalStateHasher.to_canonical_data() for hash comparison tests. Test plan did not
  anticipate this; adapted fixture accordingly.

## Test Summary
- `tests/certification/test_evidence_levels.py` (new file, 14 tests, all passing):
  - TC-1 through TC-14 as defined in test_plan.md, with adaptations noted above.
- Regression: tests/certification/test_cert_result_serialization.py (8 tests) — all pass
- Regression: tests/certification/test_recorder_refactor.py (7 tests) — all pass
- Run: `pytest tests/certification/test_evidence_levels.py -v`

## Files Changed
- src/certification/models.py
- src/certification/recorder.py
- src/certification/harness.py
- tests/certification/test_evidence_levels.py
- docs/parity_ledger/infrastructure.yaml

## Completion Summary
EvidenceLevel enum (SUMMARY/COMPACT/FULL) added; to_artifact_dict() extended with evidence_level/artifact_path/hash params; _write_full_evidence() added to harness (non-fatal, writes canonical state side-file); recorder.record() threaded; 14 new tests pass; INFRA-189/190/191 updated in parity ledger
