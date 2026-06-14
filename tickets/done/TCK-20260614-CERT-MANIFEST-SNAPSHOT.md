---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-CERT-MANIFEST-SNAPSHOT
phase: done
date: 2026-06-14
tags: [certification, manifest, proof-bundle, compliance]
---

# TCK-20260614-CERT-MANIFEST-SNAPSHOT

## Title
Write manifest_snapshot.json to proof bundle output directory per certification contract

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P1

## Request Summary
`certification_contract_me.md` section 1 (Machine-Readable Certification Law) requires the proof bundle directory to contain three artifacts: `release_proof.json`, `release_report.md`, and `manifest_snapshot.json` — defined as "copy of the manifest used for the run." Currently `CertificationHarness` and `CertificationRecorder` write the proof bundle but never write `manifest_snapshot.json`. This makes every certification run non-compliant with the Milestone E law.

## Scope
- Determine where the manifest path enters the `CertificationHarness` — either as an `__init__` parameter, read from `manifest.json` at a conventional path, or embedded in `CertificationConfig`; grep `src/certification/` for `manifest` references to confirm
- After the proof bundle is written in `CertificationRecorder.record()` (or `CertificationHarness` post-run), write a copy of the manifest contents to `<output_dir>/manifest_snapshot.json`
- Write is idempotent — if the file already exists from a previous run in the same output dir, overwrite it
- If the manifest source is unavailable (path not set, file missing), log a warning and skip — do not fail the certification run

## Out of Scope
- Validating or parsing the manifest contents — copy verbatim as JSON
- Changing the manifest schema
- Writing manifest_snapshot.json for non-release (unit test) runs — only when `output_dir` is set

## Acceptance Criteria
- After a certification run, `<output_dir>/manifest_snapshot.json` exists and contains the same content as the manifest used for the run
- If no manifest path is available, the run succeeds with a warning (no file written)
- The file is valid JSON (original manifest is already JSON — no transform needed)
- Test `test_manifest_snapshot_written_alongside_proof_bundle` passes
- Existing certification tests pass unchanged

## Related Tickets
- TCK-20260614-CERT-RECORDER-REFACTOR (implement first — establishes the recorder write path where this file belongs)
- TCK-20260614-CERT-EVIDENCE-LEVELS (parallel — adds the FULL canonical state export; both write into the same output dir)

## Related Docs
- `docs/engine/contracts/certification_contract_me.md` — section 1: Machine-Readable Certification Law; mandates this artifact

## Related Stored Artifacts
- `memory_issue.md` (source investigation)

## Related Code Areas
- `src/certification/harness.py:62` — `run_scenario()` — entry point; manifest path likely threaded in here
- `src/certification/recorder.py:26` — `bundle_path` construction — `manifest_snapshot.json` should be written to the same directory
- `reports/release_proof/` — expected output location per contract

## Assumptions / Open Questions
- Where the manifest path/contents are available in the certification pipeline — verify before implementing; if not yet threaded in, add an optional `manifest_path: Path | None = None` parameter to `CertificationHarness.__init__()`

## Implementation Notes
- Write: `(output_dir / "manifest_snapshot.json").write_text(manifest_path.read_text())` — verbatim copy
- Wrap in `try/except` — failure to write must not fail the run

## Test Summary
- `tests/certification/test_manifest_snapshot.py` (new):
  - `test_manifest_snapshot_written_alongside_proof_bundle` — run recorder with a manifest path, assert file exists and matches source
  - `test_missing_manifest_path_does_not_fail_run` — no manifest path set, assert run succeeds and snapshot is absent
- Run: `pytest tests/certification/ -v`

## Files Changed
- src/certification/harness.py (manifest_path param in __init__, hardened _persist_proof_bundle §2 block with try/except + warning)
- tests/certification/test_manifest_snapshot.py (new — 2 tests)
- docs/parity_ledger/infrastructure.yaml (INFRA-192 added)

## Completion Summary
Added manifest_path constructor param to CertificationHarness; hardened _persist_proof_bundle to wrap manifest write in try/except and emit warning when manifest missing; 2 tests pass; INFRA-192 added to parity ledger.
