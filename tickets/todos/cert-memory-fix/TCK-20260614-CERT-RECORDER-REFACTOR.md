---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-CERT-RECORDER-REFACTOR
phase: open
date: 2026-06-14
tags: [certification, memory, recorder, performance]
---

# TCK-20260614-CERT-RECORDER-REFACTOR

## Title
Refactor CertificationRecorder to eliminate JSON roundtrip while preserving proofs_bundle.json contract

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
`CertificationRecorder.record()` currently loads the entire `proofs_bundle.json`, adds `json.loads(result.to_json())` to it (a second parse), then rewrites the whole file. This pattern causes memory amplification and does not scale. The fix is to replace the `json.loads(result.to_json())` roundtrip with `result.to_artifact_dict()` (from TCK-20260614-CERT-SAFE-SERIAL) so the serialized entry no longer walks `final_state`. `proofs_bundle.json` MUST be preserved — `observability_artifact_contract.md` (section 4) names it as the "machine-readable ground truth" and `certification_contract_me.md` (section 1) mandates it as the authoritative proof artifact. The change is in how the bundle entry is populated, not whether the bundle exists.

## Scope
- Change `CertificationRecorder.record()` in `src/certification/recorder.py`:
  - Replace `bundle[key] = json.loads(result.to_json())` with `bundle[key] = result.to_artifact_dict()`
  - This stops `to_json()` → `asdict()` → deep-copy → `json.loads()` amplification chain
  - `proofs_bundle.json` continues to be written at `<output_dir>/proofs_bundle.json`
- Optionally add per-run side file `<output_dir>/runs/<run_id>.certification_result.json` alongside the bundle (additive — does not replace the bundle)
- Enforce that the bundle entry does not contain `final_state` — this is guaranteed by `to_artifact_dict()` returning `None` for that field
- Markdown report generator (if any) may continue reading from `proofs_bundle.json` unchanged

## Out of Scope
- Removing or renaming `proofs_bundle.json` — this is contract-mandated
- Replacing the bundle with a different index scheme — that would require a contract amendment
- `CertificationResult.to_artifact_dict()` — implemented in TCK-20260614-CERT-SAFE-SERIAL (this ticket depends on it)
- Full state canonical artifact export — TCK-20260614-CERT-EVIDENCE-LEVELS

## Acceptance Criteria
- `CertificationRecorder.record()` no longer calls `json.loads(result.to_json())`
- `CertificationRecorder.record()` calls `result.to_artifact_dict()` to populate the bundle entry
- `proofs_bundle.json` is still written after each `record()` call
- Bundle entries do NOT contain `final_state` data (guaranteed by `to_artifact_dict()`)
- Bundle entries contain all required scoped metadata: `runtime_profile`/`profile_name`, `scenario_id`, `detected_hardware_class`, `effective_hardware_class`, `commit_sha`
- Existing certification integration tests pass unchanged
- Test `test_recorder_does_not_call_result_to_json_roundtrip` passes

## Related Tickets
- TCK-20260614-CERT-SAFE-SERIAL (must be completed first — this ticket consumes `to_artifact_dict()`)
- TCK-20260614-CERT-EVIDENCE-LEVELS (extends this — adds optional full state artifact path in per-run file)

## Related Docs
- `docs/engine/contracts/observability_artifact_contract.md` — section 4: `proofs_bundle.json` is the "machine-readable ground truth" (CRITICAL: must not be removed)
- `docs/engine/contracts/certification_contract_me.md` — Milestone E: Machine-Readable Certification Law (section 1), scoped metadata requirement (section 5)
- `docs/engine/contracts/certification_contract.md` — M9 binding law for run semantics
- `docs/engine/performance_contract.md`
- `docs/parity_ledger/infrastructure.yaml`

## Related Stored Artifacts
- `memory_issue.md` (source investigation)

## Related Code Areas
- `src/certification/recorder.py:9` — `CertificationRecorder` class
- `src/certification/recorder.py:17` — `record()` method
- `src/certification/recorder.py:26` — `proofs_bundle.json` path construction
- `src/certification/recorder.py:37` — `bundle[key] = json.loads(result.to_json())` (line to replace)
- `src/certification/harness.py:32` — `CertificationHarness` (creates recorder, calls record)
- `tests/certification/test_harness_contract.py`
- `reports/certification/proofs_bundle.json` (generated, will be superseded)

## Assumptions / Open Questions
- `run_id` field exists on `CertificationResult` — verify at `src/certification/models.py:92`; if not, use `f"{profile_name}:{scenario_id}"` as the key (current bundle key pattern)
- Markdown report generator location — may be in harness or a separate reporter class; grep for `.md` write or `release_report` in `src/certification/`
- Existing tests that read `proofs_bundle.json` directly will need updating — identify all such references before implementation

## Implementation Notes
- Minimal diff: only change `recorder.py:37` from `json.loads(result.to_json())` to `result.to_artifact_dict()`
- If optionally adding a per-run side file: use `pathlib.Path`; create `runs/` subdirectory with `mkdir(parents=True, exist_ok=True)`; write atomically (write to `<run_id>.tmp`, rename to final path)
- `proofs_bundle.json` write path and bundle load/rewrite logic are unchanged — only the per-entry value changes

## Test Summary
- `tests/certification/test_recorder_refactor.py` (new file):
  - `test_recorder_does_not_call_result_to_json_roundtrip` — monkeypatch `to_json` to raise, assert `record()` still works via `to_artifact_dict()`
  - `test_recorder_still_writes_proofs_bundle` — after `record()`, assert `proofs_bundle.json` exists and contains the run key
  - `test_bundle_entry_does_not_contain_final_state` — assert bundle entry has no `final_state` key after `record()`
- Run: `pytest tests/certification/ -v`

## Files Changed
_(filled after implementation)_

## Completion Summary
_(filled after implementation)_
