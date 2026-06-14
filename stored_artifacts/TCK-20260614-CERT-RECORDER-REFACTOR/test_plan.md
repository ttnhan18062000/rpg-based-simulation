---
ticket_id: TCK-20260614-CERT-RECORDER-REFACTOR
phase: test_plan
date: 2026-06-14
---

# Test Plan: TCK-20260614-CERT-RECORDER-REFACTOR

## Regression Surface

### Files whose behavior changes

| File | Change | Risk |
|---|---|---|
| `src/certification/recorder.py:L37` | `json.loads(result.to_json())` → `result.to_artifact_dict()` | Primary change — bundle entry dict content shifts from string-roundtrip to direct dict |
| `tests/certification/test_final_gate.py:L51` | `data["environment"]["effective_class"]` → `data["environment"]["effective_hardware_class"]` | Key rename from asdict field name to to_artifact_dict canonical name |
| `tests/certification/test_final_gate.py:L83` | Manual fixture `"effective_class"` → `"effective_hardware_class"` | Fixture must match what recorder now writes |

### Tests that read `proofs_bundle.json` directly

| File | How it reads the bundle | Impact of change |
|---|---|---|
| `tests/certification/test_final_gate.py:L41–57` | `validate_bundle_logic()` reads `data["conformance_passed"]`, `data["environment"]["effective_class"]`, `data["timestamp"]`, `data["commit_sha"]` | `effective_class` key rename is breaking — must update to `effective_hardware_class` |
| `tests/certification/test_final_gate.py:L75–84` | Manual fixture with `"conformance_passed"`, `"failure_kind"`, `"timestamp"`, `"commit_sha"`, `"environment": {"effective_class": ...}` | `effective_class` key in fixture is stale — must update |

### Pre-existing test files that must continue to pass (no change expected)

| File | What it tests | Expected impact |
|---|---|---|
| `tests/certification/test_cert_result_serialization.py` | `to_artifact_dict()`, `to_json()`, PoisonState, guard ValueError | No change — these test the model, not the recorder |
| `tests/certification/test_harness_contract.py` | M9 harness law, hash mismatch, scoped claims | No change to harness; recorder is an implementation detail |
| `tests/certification/test_allowed_failure_truth.py` | `allowed_failure_observed` flag behavior | No change to conformance logic |
| `tests/certification/test_envelope_violations.py` | M9 envelope violation law | No change |
| `tests/certification/test_resilience_recovery.py` | M9 recovery law | No change |

---

## New Tests Required

### File: `tests/certification/test_recorder_refactor.py` (new file)

#### Test 1: `test_recorder_does_not_call_result_to_json_roundtrip`

**What it proves:** `record()` no longer calls `result.to_json()` (which would encode to string then force a decode). Monkeypatches `result.to_json` to raise, asserts `record()` still succeeds via `to_artifact_dict()`.

```python
def test_recorder_does_not_call_result_to_json_roundtrip(tmp_path, monkeypatch):
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    result = _make_minimal_result()

    # If record() calls to_json(), this will raise and the test will fail
    def _boom():
        raise AssertionError("record() must not call result.to_json()")
    monkeypatch.setattr(result, "to_json", _boom)

    # Must not raise
    recorder.record(result)

    # proofs_bundle.json must still exist
    bundle_path = tmp_path / "proofs_bundle.json"
    assert bundle_path.exists()
```

**Acceptance criterion covered:** "CertificationRecorder.record() no longer calls json.loads(result.to_json())"

#### Test 2: `test_recorder_still_writes_proofs_bundle`

**What it proves:** After `record()`, `proofs_bundle.json` exists at `<output_dir>/proofs_bundle.json` and contains the expected run key with valid content.

```python
def test_recorder_still_writes_proofs_bundle(tmp_path):
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    result = _make_minimal_result(profile_name="test_profile", scenario_id="test_scenario")

    recorder.record(result)

    bundle_path = tmp_path / "proofs_bundle.json"
    assert bundle_path.exists(), "proofs_bundle.json must be written by record()"

    with open(bundle_path) as f:
        bundle = json.load(f)

    key = "test_profile:test_scenario"
    assert key in bundle, f"Bundle must contain key '{key}'"

    entry = bundle[key]
    assert entry["profile_name"] == "test_profile"
    assert entry["scenario_id"] == "test_scenario"
    assert isinstance(entry["conformance_passed"], bool)
```

**Acceptance criterion covered:** "proofs_bundle.json is still written after each record() call"

#### Test 3: `test_bundle_entry_does_not_contain_final_state`

**What it proves:** The bundle entry stored in `proofs_bundle.json` has `final_state: null` (i.e., `None`), even when the `CertificationResult` was constructed with a live `final_state` object. Uses `PoisonState` to confirm no traversal occurred.

```python
def test_bundle_entry_does_not_contain_final_state(tmp_path):
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    poison = PoisonState()  # raises on unexpected attribute access
    result = _make_minimal_result(final_state=poison)

    # Must not raise — PoisonState only allows the 8 contracted attrs
    recorder.record(result)

    with open(tmp_path / "proofs_bundle.json") as f:
        bundle = json.load(f)

    key = f"{result.profile_name}:{result.scenario_id}"
    entry = bundle[key]

    assert entry["final_state"] is None, \
        "Bundle entry must have final_state=None — to_artifact_dict() must not walk final_state"
```

**Acceptance criterion covered:** "Bundle entries do NOT contain final_state data (guaranteed by to_artifact_dict())"

#### Test 4: `test_bundle_entry_contains_required_scoped_metadata`

**What it proves:** The bundle entry contains all scoped metadata required by `certification_contract_me.md` §5: `profile_name`, `scenario_id`, `detected_hardware_class`, `effective_hardware_class`, `commit_sha`.

```python
def test_bundle_entry_contains_required_scoped_metadata(tmp_path):
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    result = _make_minimal_result(
        profile_name="standard_gaming_profile",
        scenario_id="scenario_basic",
        commit_sha="deadbeef",
    )

    recorder.record(result)

    with open(tmp_path / "proofs_bundle.json") as f:
        bundle = json.load(f)

    entry = bundle["standard_gaming_profile:scenario_basic"]
    assert entry["profile_name"] == "standard_gaming_profile"
    assert entry["scenario_id"] == "scenario_basic"
    assert entry["commit_sha"] == "deadbeef"
    assert "detected_hardware_class" in entry["environment"]
    assert "effective_hardware_class" in entry["environment"]
    assert "override_applied" in entry["environment"]
```

**Acceptance criterion covered:** "Bundle entries contain all required scoped metadata: runtime_profile/profile_name, scenario_id, detected_hardware_class, effective_hardware_class, commit_sha"

#### Test 5: `test_bundle_accumulates_across_multiple_records`

**What it proves:** Calling `record()` multiple times accumulates entries in `proofs_bundle.json` without overwriting prior entries. Guards against regressions in the load/merge/rewrite cycle.

```python
def test_bundle_accumulates_across_multiple_records(tmp_path):
    recorder = CertificationRecorder(output_dir=str(tmp_path))

    result_a = _make_minimal_result(profile_name="profile_a", scenario_id="scen_1")
    result_b = _make_minimal_result(profile_name="profile_b", scenario_id="scen_2")

    recorder.record(result_a)
    recorder.record(result_b)

    with open(tmp_path / "proofs_bundle.json") as f:
        bundle = json.load(f)

    assert "profile_a:scen_1" in bundle
    assert "profile_b:scen_2" in bundle
```

**Acceptance criterion covered:** Existing certification integration tests pass unchanged (regression guard on bundle accumulation behavior)

#### Test 6: `test_recorder_guard_rejects_missing_effective_class`

**What it proves:** The existing guard at `recorder.py:L22` still raises `ValueError` when `environment.effective_class` is None. Guard is not broken by the refactor.

```python
def test_recorder_guard_rejects_missing_effective_class(tmp_path):
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    env_no_class = EnvironmentCapture(
        detected_facts={},
        detected_class=HardwareClass.CLASS_B,
        effective_class=None,  # invalid
        override_applied=False,
    )
    result = _make_minimal_result(environment=env_no_class)

    with pytest.raises((ValueError, AttributeError)):
        recorder.record(result)
```

**Note:** The guard checks `result.environment.effective_class` directly [recorder.py:L22]; since `HardwareClass` is not `None`-able in normal construction, this test may require direct field mutation. Verify the exact guard behavior before finalizing.

#### Test 7: `test_release_report_md_is_written`

**What it proves:** `release_report.md` is produced alongside `proofs_bundle.json`. Derivative artifact production is not broken by the refactor.

```python
def test_release_report_md_is_written(tmp_path):
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    result = _make_minimal_result()
    recorder.record(result)

    md_path = tmp_path / "release_report.md"
    assert md_path.exists(), "release_report.md must be written by record()"
    content = md_path.read_text()
    assert result.scenario_id in content
    assert result.profile_name in content
```

**Acceptance criterion covered:** "Existing certification integration tests pass unchanged" (MD generation is a core side effect of `record()`)

---

## Test Updates Required

### `tests/certification/test_final_gate.py`

#### Update 1: `validate_bundle_logic()` at L51

Change:
```python
if data["environment"]["effective_class"] not in required_classes:
```
To:
```python
if data["environment"]["effective_hardware_class"] not in required_classes:
```

Rationale: `to_artifact_dict()` uses `effective_hardware_class` (M9 canonical name). The old `effective_class` was the raw dataclass field name exposed by `asdict()`. This key was already changed when TCK-20260614-CERT-SAFE-SERIAL redirected `to_json()` to `to_artifact_dict()` — the recorder's `json.loads(result.to_json())` now produces `effective_hardware_class`. This update makes the test consistent with what the recorder already writes.

#### Update 2: Manual fixture in `test_gate_rejects_malformed_bundle()` at L83

Change:
```python
"environment": {"effective_class": "class_b"}
```
To:
```python
"environment": {"effective_hardware_class": "class_b"}
```

Rationale: Same key rename. The fixture simulates what the recorder writes into `proofs_bundle.json`. After the refactor, the recorder writes `effective_hardware_class`.

---

## Scoped Pytest Commands

### Run only the new recorder refactor tests (fastest, primary validation)
```bash
pytest tests/certification/test_recorder_refactor.py -v
```

### Run the full certification test suite (required before claiming completion)
```bash
pytest tests/certification/ -v
```

### Run with the gate tests isolated (verify gate logic after key rename fix)
```bash
pytest tests/certification/test_final_gate.py -v
```

### Run serialization tests to confirm CERT-SAFE-SERIAL baseline still holds
```bash
pytest tests/certification/test_cert_result_serialization.py -v
```

### Full scoped run (all of the above, no slow marks)
```bash
pytest tests/certification/ -v -m "not slow"
```

### Confirm no cross-module breakage in harness contract tests
```bash
pytest tests/certification/test_harness_contract.py tests/certification/test_allowed_failure_truth.py -v
```

---

## Anti-Drift Test Guards

### Guard 1: `test_recorder_does_not_call_result_to_json_roundtrip` (Test 1 above)

This test is the primary anti-drift guard. If a future change reintroduces a `result.to_json()` call in the recorder (e.g., someone "helpfully" adds a JSON string for logging), this test will catch it immediately. The monkeypatch on `to_json` is the enforcement mechanism.

### Guard 2: `test_bundle_entry_does_not_contain_final_state` (Test 3 above)

Uses `PoisonState` as `final_state`. If any code path in `record()` triggers deep traversal of `final_state` (e.g., by calling `to_json()` which would previously call `asdict()`), the `PoisonState.__getattribute__` guard raises `AssertionError`. This creates an explicit, testable contract that the recorder never touches `final_state`.

### Guard 3: `test_bundle_entry_contains_required_scoped_metadata` (Test 4 above)

Verifies `effective_hardware_class` (not `effective_class`) is in `entry["environment"]`. If someone changes `to_artifact_dict()` to revert to raw field names, this test breaks immediately.

### Guard 4: Key rename consistency guard in `test_final_gate.py`

After updating `test_final_gate.py:L51` and `L83`, the gate test itself becomes a drift guard: if the environment key is ever changed again, `validate_bundle_logic()` will fail for any real proof bundle run.

### Guard 5: INFRA-190 parity ledger entry

Adding INFRA-190 to `docs/parity_ledger/infrastructure.yaml` with `test_path: tests/certification/test_recorder_refactor.py` creates a machine-checkable coupling. If the test file is renamed or deleted, any CI system that validates parity test_path references (INFRA-094) will catch it.

### Guard 6: Regression on bundle accumulation (Test 5 above)

`test_bundle_accumulates_across_multiple_records` guards against a regression where the load/merge cycle is accidentally dropped — e.g., if someone changes the bundle load to always return `{}`. Two sequential `record()` calls must produce two keys.
