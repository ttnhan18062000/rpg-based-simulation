---
ticket_id: TCK-20260614-CERT-RECORDER-REFACTOR
phase: plan
date: 2026-06-14
---

# Implementation Plan: TCK-20260614-CERT-RECORDER-REFACTOR

## Overview

A single-line change at `src/certification/recorder.py:L37` eliminates the
`json.loads(result.to_json())` string roundtrip in favour of the direct
`result.to_artifact_dict()` call introduced by TCK-20260614-CERT-SAFE-SERIAL.
Because `to_artifact_dict()` renames the environment field from `effective_class`
(raw dataclass name from `asdict()`) to `effective_hardware_class` (M9 canonical
name), one test file that reads the old key must be updated in the same session.
The per-run side file is explicitly deferred to TCK-20260614-CERT-EVIDENCE-LEVELS.

---

## Dependency Map

```
TCK-20260614-CERT-SAFE-SERIAL (DONE)
  └─ adds CertificationResult.to_artifact_dict()        ← consumed by Step 1
        └─ key: environment.effective_hardware_class    ← drives Step 2

Step 1: recorder.py one-line change
  └─ Step 2: test_final_gate.py key rename (required for test suite to pass)
        └─ Step 3: new test file test_recorder_refactor.py
              └─ Step 4: INFRA-190 parity ledger entry
                    └─ Step 5: full test run + ticket finalisation
```

No step may be reversed or reordered. Step 2 depends on Step 1 (key rename
is meaningless without the recorder producing the new key). Step 3 depends on
Step 1 (tests assert recorder behaviour). Step 4 depends on Step 3 (parity
entry references the new test file path). Step 5 depends on all prior steps.

---

## Acceptance Criteria → Step Mapping

| AC | Step |
|---|---|
| `record()` no longer calls `json.loads(result.to_json())` | Step 1 |
| `record()` calls `result.to_artifact_dict()` to populate bundle entry | Step 1 |
| `proofs_bundle.json` is still written after each `record()` call | Step 1 (unchanged path) + Step 3 (Test 2) |
| Bundle entries do NOT contain `final_state` data | Step 1 + Step 3 (Test 3) |
| Bundle entries contain all required scoped metadata (`effective_hardware_class`, etc.) | Step 1 + Step 3 (Test 4) |
| Existing certification integration tests pass unchanged | Step 2 (key rename) + Step 5 (full run) |
| `test_recorder_does_not_call_result_to_json_roundtrip` passes | Step 3 (Test 1) |

---

## Scope Guards (What NOT to Touch)

- **Do not remove or rename `proofs_bundle.json`** — mandated by
  `observability_artifact_contract.md` §4 and `certification_contract_me.md` §1.
- **Do not change the bundle key format** (`f"{result.profile_name}:{result.scenario_id}"`)
  — referenced by `test_final_gate.py:L47` and the §6 gate logic.
- **Do not add a per-run side file** (`runs/<run_id>.certification_result.json`)
  — deferred to TCK-20260614-CERT-EVIDENCE-LEVELS. No `runs/` directory creation.
- **Do not change the bundle load/merge/rewrite cycle** at `recorder.py:L26–40`
  — only the one-line value assignment at L37 changes.
- **Do not change `_generate_markdown(result)`** — it uses the live `result`
  object (not the bundle dict) and is unaffected by the key rename.
- **Do not touch `recorder.py:L22` guard** (`if not result.environment.effective_class`)
  — this guards against missing effective class before bundle write; it reads
  the live object attribute, not the serialised dict key.
- **Do not touch `CertificationResult.to_artifact_dict()`** — implemented and
  verified by TCK-20260614-CERT-SAFE-SERIAL; treating it as a black-box
  dependency.
- **Do not touch any file outside `src/certification/recorder.py`,
  `tests/certification/test_final_gate.py`,
  `tests/certification/test_recorder_refactor.py` (new), and
  `docs/parity_ledger/infrastructure.yaml`.**

---

## Ordered Implementation Steps

### Step 1 — Change `recorder.py:L37`: eliminate JSON roundtrip

**File:** `src/certification/recorder.py`

**Change:** Replace line 37:
```python
bundle[key] = json.loads(result.to_json())
```
with:
```python
bundle[key] = result.to_artifact_dict()
```

**Also remove:** The `import json` line's dependency on `json.loads` is now
only needed for `json.load` (bundle read, L31) and `json.dump` (bundle write,
L40). Keep the `import json` line — it is still used.

**Verification (before proceeding):** Confirm the file contains exactly one
occurrence of `json.loads` (at L37) and no other call to `to_json()` in
`record()`. After editing, `json.loads` must not appear anywhere in `record()`.

**Why this step is first:** All other steps either test or document this change.

---

### Step 2 — Fix `test_final_gate.py`: rename stale `effective_class` key

**File:** `tests/certification/test_final_gate.py`

**Change A — `validate_bundle_logic()` at L51:**
```python
# Before
if data["environment"]["effective_class"] not in required_classes:
# After
if data["environment"]["effective_hardware_class"] not in required_classes:
```

**Change B — manual fixture in `test_gate_rejects_malformed_bundle()` at L82–83:**
```python
# Before
"environment": {"effective_class": "class_b"}
# After
"environment": {"effective_hardware_class": "class_b"}
```

**Rationale:** `to_artifact_dict()` (now used by both `to_json()` after
TCK-20260614-CERT-SAFE-SERIAL, and directly via Step 1) outputs
`effective_hardware_class` as the canonical M9 key name. The test was written
against the old `asdict()` field name `effective_class`. Both the logic at L51
and the manual fixture at L83 must use the canonical name.

**Scope guard:** Do not change any other logic in this file. The `validate_bundle_logic`
function signature, the `REAL_PROOF_DIR` path, the SHA check at L56, and the
`test_real_release_proof_is_valid` integration guard are all unchanged.

**Verification:** After editing, the string `"effective_class"` must not appear
anywhere in `test_final_gate.py`.

---

### Step 3 — Create `tests/certification/test_recorder_refactor.py`

**File:** `tests/certification/test_recorder_refactor.py` (new file)

**Contents:** Implement all 7 tests defined in `test_plan.md`:

1. `test_recorder_does_not_call_result_to_json_roundtrip` — monkeypatch `to_json`
   to raise `AssertionError`; assert `record()` succeeds and bundle exists.
2. `test_recorder_still_writes_proofs_bundle` — assert bundle exists and contains
   the expected `profile_name:scenario_id` key with valid content.
3. `test_bundle_entry_does_not_contain_final_state` — pass `PoisonState` as
   `final_state`; assert `record()` does not raise and `entry["final_state"]` is `None`.
4. `test_bundle_entry_contains_required_scoped_metadata` — assert
   `entry["environment"]` contains `detected_hardware_class`, `effective_hardware_class`,
   `override_applied`; assert top-level `commit_sha`, `profile_name`, `scenario_id` present.
5. `test_bundle_accumulates_across_multiple_records` — two sequential `record()`
   calls produce two distinct keys in the bundle.
6. `test_recorder_guard_rejects_missing_effective_class` — construct
   `EnvironmentCapture` with `effective_class=None`; assert `record()` raises
   `ValueError` (or `AttributeError`). Use `object.__setattr__` for frozen
   dataclass field mutation if required.
7. `test_release_report_md_is_written` — assert `release_report.md` exists
   and contains `result.scenario_id` and `result.profile_name`.

**Helper `_make_minimal_result()`:** Constructs a valid `CertificationResult`
with all required fields (`profile_name`, `scenario_id`, `environment` with
non-None `effective_class`, `commit_sha`, `run_id`, `seed`, `measurements`,
`conformance_passed`, `failure_kind`, `failure_reason`, `peak_rss_mb`,
`total_cpu_sec`, `baseline_hash`, `final_hash`, `allowed_failure_observed`).
Accepts keyword overrides for parametric tests. Must not use `PoisonState`
by default.

**Import note:** Import `PoisonState` from wherever TCK-20260614-CERT-SAFE-SERIAL
placed it (likely `tests/certification/test_cert_result_serialization.py` as a
local fixture, or `src/certification/models.py`). If `PoisonState` is a test-local
class in the serialisation test, duplicate the minimal class definition in this
file rather than importing across test files.

**Scope guard:** Do not import or reference any test helper from
`test_cert_result_serialization.py` — that file tests the model boundary;
this file tests the recorder boundary. Keep fixtures independent.

**Verification:** Run `pytest tests/certification/test_recorder_refactor.py -v`
and confirm all 7 tests pass before moving to Step 4.

---

### Step 4 — Add INFRA-190 to `docs/parity_ledger/infrastructure.yaml`

**File:** `docs/parity_ledger/infrastructure.yaml`

**Action:** Append the following entry at the end of the file (after INFRA-189):

```yaml
- id: INFRA-190
  text: >
    CertificationRecorder.record() populates the proofs_bundle.json entry via
    result.to_artifact_dict() directly, eliminating the json.loads(result.to_json())
    string roundtrip. proofs_bundle.json continues to be written after every record()
    call. Bundle entries never contain final_state data.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/certification/recorder.py::CertificationRecorder.record +
    tests/certification/test_recorder_refactor.py
  proof_type: null
  test_path: tests/certification/test_recorder_refactor.py
  divergence_note: ""
```

**Scope guard:** Do not modify INFRA-058 or INFRA-055. Those entries remain
correct — the bundle is still produced (INFRA-055) and entries remain mutually
consistent (INFRA-058 is satisfied by the `effective_hardware_class` key being
present in both the recorder output and the gate test after Step 2).

**Verification:** Confirm `INFRA-190` appears once in the file and that the
YAML is syntactically valid (`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` exits 0).

---

### Step 5 — Run tests and verify

**Commands (in order):**

```bash
# Primary: new recorder refactor tests
pytest tests/certification/test_recorder_refactor.py -v

# Gate test with key rename fix
pytest tests/certification/test_final_gate.py -v

# Serialisation baseline (CERT-SAFE-SERIAL regression guard)
pytest tests/certification/test_cert_result_serialization.py -v

# Full certification suite (required before claiming completion)
pytest tests/certification/ -v -m "not slow"
```

**Pass criteria:**
- Zero failures across all commands above.
- `test_recorder_does_not_call_result_to_json_roundtrip` explicitly listed as PASSED.
- `test_gate_rejects_malformed_bundle` explicitly listed as PASSED (confirms key rename took effect in the fixture).

**If `test_real_release_proof_is_valid` fails:** This test requires a real proof
bundle in `reports/release_proof/`. If that directory is absent, pytest will call
`pytest.fail()` rather than skip. This is a pre-existing integration guard, not
a regression from this ticket. It does not block completion if the rest of
`tests/certification/` passes.

---

## Files Changed (Summary)

| File | Type | Change |
|---|---|---|
| `src/certification/recorder.py` | Modify | L37: `json.loads(result.to_json())` → `result.to_artifact_dict()` |
| `tests/certification/test_final_gate.py` | Modify | L51: key rename; L83: fixture key rename |
| `tests/certification/test_recorder_refactor.py` | Create | 7 new tests covering all ACs |
| `docs/parity_ledger/infrastructure.yaml` | Modify | Append INFRA-190 entry |

**Explicitly NOT changed:**
- `src/certification/models.py` (owned by TCK-20260614-CERT-SAFE-SERIAL)
- `src/certification/harness.py` (no recorder interface change)
- Any file under `docs/engine/contracts/` (contracts are not amended by this ticket)
- `docs/guidelines/v2_intentional_divergences.md` (no intentional behaviour divergence)
- `tickets/working_log.csv` and `tickets/done/` (post-completion finalisation, not implementation)

---

## Deviations from Plan

### PoisonState definition (Step 3, Test 3)

**Plan stated:** "PoisonState as final_state; after record(), assert bundle entry has no 'final_state' key with live data (final_state value is None)"

**Deviation:** The plan described PoisonState as a sentinel that prevents all traversal. In practice, `_final_state_summary()` (called by `to_artifact_dict()`) legitimately accesses final_state attributes via safe `getattr()` — this is the correct, non-amplifying path. A fully poison `__getattribute__` override that blocked `getattr` would incorrectly fail the safe summary path.

**Resolution:** PoisonState was implemented as a class with the 8 named attributes that `_final_state_summary()` reads via `getattr` (so those pass safely), but with `__dict__` overridden as a property that raises `RuntimeError` — blocking the bulk serialization path (`vars()`, `asdict()`, `dataclasses.asdict()`). This correctly tests that `final_state` is never bulk-traversed while allowing the safe compact-summary path. The assertion `entry["final_state"] is None` still validates the AC (live state is never written to the bundle entry).

---

## Post-Completion Checklist (for finalisation phase, not implementation)

- Move ticket to `tickets/done/TCK-20260614-CERT-RECORDER-REFACTOR.md`
- Move staging artifacts to `stored_artifacts/TCK-20260614-CERT-RECORDER-REFACTOR/`
- Append working log entry to `tickets/working_log.csv`
- Run `make knowledge-index-update` (docs unchanged, but parity ledger was modified)
- Clean `data/runs/` and `reports/release_proof/` if populated during testing
- Write agent monitoring run entry (`agent-monitoring/runs.jsonl`) and at least one event entry (`agent-monitoring/events.jsonl`)
