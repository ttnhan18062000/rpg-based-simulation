---
ticket_id: TCK-20260614-CERT-SAFE-SERIAL
phase: test_plan
date: 2026-06-14
---

# Test Plan: TCK-20260614-CERT-SAFE-SERIAL

## Regression Surface (existing tests that must pass)

All tests in `tests/certification/` must pass unchanged. The key risk points per file:

| File | Risk from this change | Why safe |
|---|---|---|
| `test_harness_contract.py` | `result.to_json()` is called indirectly via `_persist_proof_bundle` → `recorder.record()` | `to_json()` now delegates to `to_artifact_dict()` which includes all keys the recorder reads |
| `test_harness_contract.py::test_honest_language_compliance` | Calls `recorder._generate_markdown(res)` directly using a manually constructed `CertificationResult` | `_generate_markdown` reads fields directly from the result object, not from `to_artifact_dict()` — no change |
| `test_allowed_failure_truth.py` | Uses `ConformanceEvaluator.evaluate()` — no serialization | Unaffected |
| `test_envelope_violations.py` | Uses `CertificationHarness.run_scenario()` — triggers `recorder.record()` → `to_json()` | If `to_json()` delegates safely, no break |
| `test_resilience_recovery.py` | Same as envelope violations | Same |
| `test_cert_long_run_stability.py` | May call `to_json()` or inspect result bundle | Must verify no key-name dependencies on old `asdict` structure |
| `test_final_gate.py` | Reads from `proofs_bundle.json` structure | Bundle keys (`profile_name`, `scenario_id`, `conformance_passed`, `failure_kind`) are preserved in `to_artifact_dict()` |
| `test_world_compile_determinism.py` | No certification serialization | Unaffected |
| `test_phase10_enhanced_determinism_parity.py` | May use harness | Verify does not inspect internal result dict structure |
| `test_phase10_enhanced_rollout_gate.py` | May read `proofs_bundle.json` | Same guard as `test_final_gate.py` |

**Run command for full regression check:**
```bash
pytest tests/certification/ -v --tb=short
```

---

## New Tests Required

New file: `tests/certification/test_cert_result_serialization.py`

### Test 1: `test_certification_result_summary_does_not_serialize_final_state`

**Purpose:** Proves `to_artifact_dict()` never walks `final_state`. Uses a PoisonState object that raises `AssertionError` on any attribute access beyond the expected summary fields.

**PoisonState pattern (from `memory_issue.md` section 7.6 and ticket Implementation Notes):**

```python
class PoisonState:
    """
    Raises AssertionError on any attribute access except the exact fields
    used by _final_state_summary(). This proves to_artifact_dict() does not
    walk final_state via asdict or any other recursive mechanism.
    """
    def __getattribute__(self, name):
        ALLOWED = {"tick", "seed", "entities", "resource_nodes",
                   "regions", "buildings", "corpses", "ground_items"}
        if name in ALLOWED:
            return {
                "tick": 5, "seed": 99,
                "entities": {"a": 1, "b": 2},
                "resource_nodes": {"r": 1},
                "regions": {},
                "buildings": {"b": 1},
                "corpses": {},
                "ground_items": {"g": 1, "h": 2},
            }[name]
        raise AssertionError(
            f"to_artifact_dict() must not access state.{name} — "
            f"deep serialization boundary violated"
        )
```

**Assertions:**
- `artifact = result.to_artifact_dict()` does not raise
- `artifact["final_state"] is None`
- `artifact["final_state_summary"] is not None`
- `artifact["final_state_summary"]["tick"] == 5`
- `artifact["final_state_summary"]["seed"] == 99`
- `artifact["final_state_summary"]["entity_count"] == 2`
- `artifact["final_state_summary"]["resource_node_count"] == 1`
- `artifact["final_state_summary"]["region_count"] == 0`
- `artifact["final_state_summary"]["building_count"] == 1`
- `artifact["final_state_summary"]["corpse_count"] == 0`
- `artifact["final_state_summary"]["ground_item_count"] == 2`
- `artifact["final_state_summary"]["final_hash"] == result.final_hash`
- `artifact["final_state_artifact"] is None`

**Full construction of `CertificationResult` for this test:**

```python
from src.certification.models import (
    CertificationResult, EnvironmentCapture, HardwareClass as CHC,
    FailureKind, ArenaStopCondition
)

env = EnvironmentCapture(
    detected_facts={},
    detected_class=CHC.CLASS_B,
    effective_class=CHC.CLASS_B,
    override_applied=False,
)
result = CertificationResult(
    run_id="test-run-001",
    timestamp=0.0,
    commit_sha="abc123",
    profile_name="TEST_PROFILE",
    scenario_id="TEST_SCENARIO",
    seed=99,
    environment=env,
    measurements=[],
    baseline_hash="hash_a",
    final_hash="hash_b",
    governor_mode_sequence=["NORMAL"],
    conformance_passed=True,
    failure_kind=FailureKind.NONE,
    failure_reason=None,
    final_state=PoisonState(),
)
```

---

### Test 2: `test_to_json_does_not_call_asdict`

**Purpose:** Proves `to_json()` no longer calls `dataclasses.asdict()` or `safe_asdict()` anywhere in its execution path.

**Pattern:** Monkeypatch `dataclasses.asdict` to raise, then assert `to_json()` still succeeds.

```python
import dataclasses
import pytest
from unittest.mock import patch

def test_to_json_does_not_call_asdict(monkeypatch):
    def forbidden_asdict(*args, **kwargs):
        raise AssertionError(
            "to_json() must not call dataclasses.asdict() — "
            "serialization boundary violated"
        )

    monkeypatch.setattr(dataclasses, "asdict", forbidden_asdict)
    # Also patch the local import inside to_json if it re-imports
    import src.certification.models as cert_models
    monkeypatch.setattr(cert_models, "asdict", forbidden_asdict, raising=False)

    result = _make_minimal_result()  # helper, final_state=None
    json_str = result.to_json()

    assert json_str  # non-empty
    import json
    parsed = json.loads(json_str)
    assert parsed["schema_version"] == "certification_result.v1"
    assert parsed["conformance_passed"] is True
    assert parsed["final_state"] is None
    assert parsed["final_state_summary"] is None
```

**Note on patching:** `to_json()` currently does `from dataclasses import asdict` as a local import inside the function body (L128). After the refactor, this import should be removed. The monkeypatch approach is robust either way if it patches `dataclasses.asdict` at the module level. The test also patches `cert_models.asdict` (the module-level import at L5) as a belt-and-suspenders guard.

---

### Test 3: `test_final_state_summary_none_when_no_state`

**Purpose:** Proves `_final_state_summary()` returns `None` when `final_state` is `None`, and that `to_artifact_dict()` sets `final_state_summary` to `None` in this case.

```python
def test_final_state_summary_none_when_no_state():
    result = _make_minimal_result(final_state=None)
    artifact = result.to_artifact_dict()

    assert artifact["final_state"] is None
    assert artifact["final_state_summary"] is None
    assert artifact["final_state_artifact"] is None
```

---

### Test 4: `test_to_artifact_dict_required_fields_present` (AC completeness)

**Purpose:** Assert every required key from the AC is present in the artifact dict output.

```python
REQUIRED_KEYS = [
    "schema_version", "run_id", "timestamp", "commit_sha",
    "profile_name", "scenario_id", "seed",
    "environment",          # nested dict
    "measurements",         # list of dicts
    "baseline_hash", "final_hash", "governor_mode_sequence",
    "conformance_passed", "stop_condition",
    "allowed_failure_observed", "failure_kind", "failure_reason",
    "peak_rss_mb", "total_cpu_sec",
    "final_state",          # always None
    "final_state_summary",  # None or compact dict
    "final_state_artifact", # always None (Phase 3 placeholder)
]
REQUIRED_ENVIRONMENT_KEYS = [
    "detected_hardware_class", "effective_hardware_class", "override_applied"
]

def test_to_artifact_dict_required_fields_present():
    result = _make_minimal_result()
    artifact = result.to_artifact_dict()

    for key in REQUIRED_KEYS:
        assert key in artifact, f"Missing key: {key}"

    env_dict = artifact["environment"]
    for key in REQUIRED_ENVIRONMENT_KEYS:
        assert key in env_dict, f"Missing environment key: {key}"

    assert artifact["schema_version"] == "certification_result.v1"
    assert artifact["final_state"] is None
    assert artifact["final_state_artifact"] is None
```

**Environment dict key mapping:**
- `detected_hardware_class` ← `environment.detected_class.value`
- `effective_hardware_class` ← `environment.effective_class.value`
- `override_applied` ← `environment.override_applied`

---

### Test 5: `test_to_artifact_dict_guard_raises_on_missing_metadata`

**Purpose:** Proves that `to_artifact_dict()` raises when required scoped metadata fields are absent.

```python
def test_to_artifact_dict_guard_raises_on_missing_metadata():
    # Missing profile_name
    with pytest.raises((ValueError, AssertionError)):
        result = _make_minimal_result(profile_name="")
        result.to_artifact_dict()

    # Missing scenario_id
    with pytest.raises((ValueError, AssertionError)):
        result = _make_minimal_result(scenario_id="")
        result.to_artifact_dict()
```

Note: The guard for `detected_hardware_class` / `effective_hardware_class` is harder to trigger because `EnvironmentCapture` is typed — passing `None` requires bypassing type checks. The test for missing profile/scenario is sufficient for the AC requirement. The environment guard (checking `self.environment` is not None) is validated by type safety.

---

### Helper: `_make_minimal_result()`

```python
def _make_minimal_result(
    profile_name="TEST_PROFILE",
    scenario_id="TEST_SCENARIO",
    final_state=None,
):
    from src.certification.models import (
        CertificationResult, EnvironmentCapture, HardwareClass as CHC,
        FailureKind, ArenaStopCondition
    )
    env = EnvironmentCapture(
        detected_facts={"cpu_count": 4, "total_ram_gb": 16.0},
        detected_class=CHC.CLASS_B,
        effective_class=CHC.CLASS_B,
        override_applied=False,
    )
    return CertificationResult(
        run_id="test-run-001",
        timestamp=1234567890.0,
        commit_sha="deadbeef",
        profile_name=profile_name,
        scenario_id=scenario_id,
        seed=42,
        environment=env,
        measurements=[],
        baseline_hash="base_hash",
        final_hash="final_hash_x",
        governor_mode_sequence=["NORMAL"],
        conformance_passed=True,
        stop_condition=ArenaStopCondition.TIMEOUT,
        failure_kind=FailureKind.NONE,
        failure_reason=None,
        peak_rss_mb=256.0,
        total_cpu_sec=1.234,
        final_state=final_state,
    )
```

---

## Scoped Pytest Commands

Run only the new test file during implementation:
```bash
pytest tests/certification/test_cert_result_serialization.py -v
```

Run all certification tests to verify no regression:
```bash
pytest tests/certification/ -v --tb=short
```

Run with the resource budget that was failing under Memray (to confirm amplification is gone):
```bash
pytest tests/certification/ -v --tb=short -m "not slow and not extra_slow"
```

If `test_cert_long_run_stability.py` is slow, run without it first:
```bash
pytest tests/certification/ -v --tb=short --ignore=tests/certification/test_cert_long_run_stability.py
```

---

## Anti-Drift Test Guards

### Guard 1: `asdict` ban in `to_json()`

The monkeypatch test (`test_to_json_does_not_call_asdict`) serves as the regression guard. If a future change reintroduces `asdict()` inside `to_json()`, this test fails immediately.

### Guard 2: PoisonState as the serialization boundary oracle

The PoisonState test (`test_certification_result_summary_does_not_serialize_final_state`) will catch any regression where `to_artifact_dict()` is changed to use `asdict`, `vars()`, `__dict__`, or any other reflective traversal that walks beyond the explicitly coded fields. It is the single strongest guard for this ticket's core requirement.

### Guard 3: Required keys completeness test

`test_to_artifact_dict_required_fields_present` ensures that a future refactor of `to_artifact_dict()` cannot silently drop a key that the M9/ME contracts require. If a key is removed, this test fails.

### Guard 4: `schema_version` sentinel

The `assert artifact["schema_version"] == "certification_result.v1"` check in multiple tests ensures the artifact is identifiably the new schema. If `to_json()` ever regresses to returning the old `asdict` output (which has no `schema_version` key), every test that checks this will fail.

### Guard 5: Regression gate via existing harness tests

`test_harness_contract.py::test_certification_detects_semantic_drift` runs a full end-to-end harness execution and calls `result.to_json()` implicitly via `_persist_proof_bundle`. If the artifact dict breaks recorder compatibility, this integration test fails — it is the canary for the serialization→recorder→bundle pipeline.
