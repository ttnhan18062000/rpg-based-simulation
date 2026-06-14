---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-CERT-SAFE-SERIAL
phase: open
date: 2026-06-14
tags: [certification, memory, serialization, performance]
---

# TCK-20260614-CERT-SAFE-SERIAL

## Title
Add safe artifact serialization boundary to CertificationResult

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P0

## Request Summary
`CertificationResult.to_json()` calls `dataclasses.asdict(self)` which recursively deep-copies the full live `AuthoritativeState` attached as `final_state`. This creates a memory amplification path: live state → asdict deep copy → JSON string → json.loads dict → bundled write. The fix is to add an explicit `to_artifact_dict()` method that builds the proof artifact without walking `final_state`, and redirect `to_json()` to use it. A compact `final_state_summary` replaces the full object in the default serialization path.

## Scope
- Add `CertificationResult.to_artifact_dict(self) -> dict` in `src/certification/models.py`
- Redirect `CertificationResult.to_json()` to call `json.dumps(self.to_artifact_dict())`
- `to_artifact_dict()` must never call `asdict(self)` or `safe_asdict(self)` — build the dict field-by-field explicitly
- `final_state` field must be excluded from the artifact dict (set to `None`)
- Add `_final_state_summary(self) -> dict | None` returning: `tick`, `seed`, `entity_count`, `resource_node_count`, `region_count`, `building_count`, `corpse_count`, `ground_item_count`, `final_hash`
- Include `final_state_summary` key in artifact dict output
- Add `final_state_artifact: None` key as placeholder for Phase 3 (TCK-20260614-CERT-EVIDENCE-LEVELS)

## Out of Scope
- Changing `CertificationRecorder` (TCK-20260614-CERT-RECORDER-REFACTOR)
- EvidenceLevel enum or full canonical state export (TCK-20260614-CERT-EVIDENCE-LEVELS)
- Changes to `CertificationHarness.run_scenario()` — `final_state=kernel.state` assignment on the runtime result object is fine; only the artifact serialization path changes

## Acceptance Criteria
- `CertificationResult.to_artifact_dict()` exists and returns a dict with all required fields including: `schema_version`, `run_id`, `timestamp`, `commit_sha`, `profile_name` (= `runtime_profile` per M9 contract), `scenario_id`, `seed`, `environment` (with `detected_hardware_class`, `effective_hardware_class`, `override_applied`), `measurements`, `baseline_hash`, `final_hash`, `governor_mode_sequence`, `conformance_passed`, `stop_condition`, `allowed_failure_observed`, `failure_kind`, `failure_reason`, `peak_rss_mb`, `total_cpu_sec`, `final_state`, `final_state_summary`, `final_state_artifact`
- Scoped metadata required by `certification_contract_me.md` section 5 is present: `runtime_profile`, `scenario_id`, `detected_hardware_class`, `effective_hardware_class` — `to_artifact_dict()` must fail if any of these are missing
- `to_artifact_dict()["final_state"]` is always `None`
- `to_artifact_dict()["final_state_summary"]` is a compact dict when `final_state` is attached, `None` when not
- `to_json()` returns `json.dumps(self.to_artifact_dict())` — no longer calls `asdict()` or `safe_asdict()`
- Test `test_certification_result_summary_does_not_serialize_final_state` passes using a `PoisonState` object that raises `AssertionError` on unexpected attribute access
- Existing tests in `tests/certification/` pass unchanged

## Related Tickets
- TCK-20260614-CERT-RECORDER-REFACTOR (depends on this — recorder must consume `to_artifact_dict()`)
- TCK-20260614-CERT-EVIDENCE-LEVELS (extends this — adds EvidenceLevel and full state export)

## Related Docs
- `docs/engine/contracts/certification_contract.md` — M9 binding law: run must bind `runtime_profile`, `scenario_id`, `detected_hardware_class`, `effective_hardware_class`
- `docs/engine/contracts/certification_contract_me.md` — Milestone E: Machine-Readable Certification Law (section 1) and Honest Reporting Law (section 5, scoped metadata requirement)
- `docs/engine/contracts/observability_artifact_contract.md` — section 4: `proofs_bundle.json` is the machine-readable ground truth
- `docs/engine/performance_contract.md`
- `docs/parity_ledger/infrastructure.yaml`

## Related Stored Artifacts
- `memory_issue.md` (source investigation)

## Related Code Areas
- `src/certification/models.py:92` — `CertificationResult` dataclass
- `src/certification/models.py:126` — `to_json()` method with `asdict(self)` call (line 171)
- `src/certification/models.py:131` — `safe_asdict()` fallback
- `src/certification/harness.py:223` — `final_state=kernel.state` assignment
- `src/core/state.py:981` — `AuthoritativeState` class (large object being serialized)
- `src/engine/checkpoint.py:11` — `CanonicalStateHasher` (reference for canonical boundary)
- `tests/certification/test_harness_contract.py`
- `tests/certification/test_allowed_failure_truth.py`

## Assumptions / Open Questions
- `CertificationResult` fields like `environment`, `stop_condition`, `failure_kind` are typed (enums/dataclasses) — `to_artifact_dict()` must call `.value` on enums and `.to_dict()` / explicit field mapping on nested dataclasses
- `measurements` has a `to_dict()` method or equivalent — verify before implementing; if not, add it or map fields explicitly
- `run_id` and `timestamp` fields exist on `CertificationResult` — verify exact field names at `src/certification/models.py:92`

## Implementation Notes
- Do NOT use `asdict()` anywhere in `to_artifact_dict()`. Build the dict literally.
- PoisonState test pattern: override `__getattribute__` to allow only `tick`, `seed`, `entities`, `resource_nodes`, `regions`, `buildings`, `corpses`, `ground_items` — raise `AssertionError` for all others.
- `schema_version` value: `"certification_result.v1"`

## Test Summary
- `tests/certification/test_cert_result_serialization.py` (new file):
  - `test_certification_result_summary_does_not_serialize_final_state` — PoisonState as `final_state`, asserts artifact dict has `final_state=None` and `final_state_summary` with correct counts
  - `test_to_json_does_not_call_asdict` — monkeypatch `dataclasses.asdict` to raise, assert `to_json()` still works
  - `test_final_state_summary_none_when_no_state` — `final_state=None` yields `final_state_summary=None`
- Run: `pytest tests/certification/ -v`

## Files Changed
_(filled after implementation)_

## Completion Summary
_(filled after implementation)_
