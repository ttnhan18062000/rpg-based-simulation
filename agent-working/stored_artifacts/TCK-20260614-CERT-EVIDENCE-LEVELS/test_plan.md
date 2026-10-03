---
ticket_id: TCK-20260614-CERT-EVIDENCE-LEVELS
phase: test_plan
date: 2026-06-14
---

# Test Plan: TCK-20260614-CERT-EVIDENCE-LEVELS

## Test file

`tests/certification/test_evidence_levels.py` (new file)

Run command:
```
pytest tests/certification/test_evidence_levels.py -v
```

Regression guard:
```
pytest tests/certification/ -v
```

---

## Fixtures

### `minimal_result(tmp_path)` — shared across all tests

Returns a `CertificationResult` with:
- `run_id = "test-run-abc123"`
- All required metadata fields populated (`profile_name`, `scenario_id`, `environment`)
- `final_state = None` (default — overridden per test when needed)
- `measurements = []`
- `baseline_hash = None`, `final_hash = None`
- `conformance_passed = True`

### `fake_state()` — for tests needing `final_state`

A minimal object with attributes `tick`, `seed`, `entities`, `resource_nodes`, `regions`, `buildings`, `corpses`, `ground_items`. Each is a plain dict or primitive. Satisfies `_final_state_summary()` access pattern. Do NOT use a real `AuthoritativeState` — keep tests unit-isolated.

```python
class FakeState:
    tick = 10
    seed = 42
    entities = {1: None, 2: None, 3: None}
    resource_nodes = {}
    regions = {}
    buildings = {}
    corpses = {}
    ground_items = {}
```

### `fake_state_with_resources()` — for COMPACT level tests

Like `FakeState` but with 7 resource node entries where each has a `quantity` attribute:

```python
class FakeResourceNode:
    def __init__(self, qty):
        self.quantity = qty

class FakeStateWithResources(FakeState):
    resource_nodes = {f"rn{i}": FakeResourceNode(i * 10) for i in range(7)}
```

---

## Tests

### TC-1: `test_evidence_level_enum_values`

**Purpose:** Verify `EvidenceLevel` exists with the correct string values.

```python
def test_evidence_level_enum_values():
    from src.certification.models import EvidenceLevel
    assert EvidenceLevel.SUMMARY.value == "summary"
    assert EvidenceLevel.COMPACT.value == "compact"
    assert EvidenceLevel.FULL.value    == "full"
    # Is a str subclass (str, Enum pattern)
    assert isinstance(EvidenceLevel.SUMMARY, str)
```

**Coverage:** enum definition, `str, Enum` inheritance.

---

### TC-2: `test_summary_level_has_no_state_artifact`

**Purpose:** SUMMARY level (default) produces `final_state_artifact=None` and `final_state_hash=None`.

```python
def test_summary_level_has_no_state_artifact(minimal_result):
    from src.certification.models import EvidenceLevel
    d = minimal_result.to_artifact_dict()  # default = SUMMARY
    assert d["final_state_artifact"] is None
    assert d.get("final_state_hash") is None
    assert d["final_state"] is None
```

**Coverage:** default parameter behavior, no regression from pre-ticket state.

---

### TC-3: `test_summary_level_final_state_summary_is_none_when_no_state`

**Purpose:** When `final_state=None`, `final_state_summary` is `None` at SUMMARY level.

```python
def test_summary_level_final_state_summary_is_none_when_no_state(minimal_result):
    from src.certification.models import EvidenceLevel
    d = minimal_result.to_artifact_dict(EvidenceLevel.SUMMARY)
    assert d["final_state_summary"] is None
```

**Coverage:** `_final_state_summary()` returns `None` when `final_state is None`.

---

### TC-4: `test_summary_level_final_state_summary_counts_when_state_present`

**Purpose:** SUMMARY with `final_state` attached returns compact count dict.

```python
def test_summary_level_final_state_summary_counts_when_state_present(minimal_result, fake_state):
    from src.certification.models import EvidenceLevel
    import dataclasses
    result = dataclasses.replace(minimal_result, final_state=fake_state)
    d = result.to_artifact_dict(EvidenceLevel.SUMMARY)
    s = d["final_state_summary"]
    assert s is not None
    assert s["entity_count"] == 3
    assert s["tick"] == 10
    assert "entity_sample" not in s   # SUMMARY does not include sample
    assert "resource_snapshot" not in s
```

**Coverage:** SUMMARY summary shape; COMPACT-only fields are absent.

---

### TC-5: `test_compact_level_adds_entity_sample_and_resource_snapshot`

**Purpose:** COMPACT level extends summary with `entity_sample` and `resource_snapshot`.

```python
def test_compact_level_adds_entity_sample_and_resource_snapshot(minimal_result, fake_state_with_resources):
    from src.certification.models import EvidenceLevel
    import dataclasses
    result = dataclasses.replace(minimal_result, final_state=fake_state_with_resources)
    d = result.to_artifact_dict(EvidenceLevel.COMPACT)
    s = d["final_state_summary"]
    assert "entity_sample" in s
    assert len(s["entity_sample"]) <= 5
    assert "resource_snapshot" in s
    assert len(s["resource_snapshot"]) <= 5
    # Top resource nodes by quantity — highest quantity first
    assert s["resource_snapshot"][0] == "rn6"  # quantity=60, highest
    assert d["final_state_artifact"] is None   # COMPACT still no side file
    assert d.get("final_state_hash") is None
```

**Coverage:** COMPACT summary shape; sort order; COMPACT does not write side file.

---

### TC-6: `test_full_level_artifact_path_in_dict`

**Purpose:** FULL level sets `final_state_artifact` to the expected relative path string.

```python
def test_full_level_artifact_path_in_dict(minimal_result, fake_state):
    from src.certification.models import EvidenceLevel
    import dataclasses
    result = dataclasses.replace(minimal_result, final_state=fake_state)
    d = result.to_artifact_dict(EvidenceLevel.FULL)
    assert d["final_state_artifact"] == f"state/{result.run_id}.final_state.canonical.json"
    assert d["final_state"] is None  # full state never embedded
```

**Coverage:** FULL artifact path construction; `final_state` remains `None` in dict.

---

### TC-7: `test_full_evidence_writes_canonical_state_file` (AC test)

**Purpose:** Calling `run_scenario()` with `evidence_level=EvidenceLevel.FULL` writes the canonical state file.

```python
def test_full_evidence_writes_canonical_state_file(tmp_path, monkeypatch):
    from src.certification.models import EvidenceLevel
    from src.certification.harness import CertificationHarness
    from src.config.profiles import RuntimeProfile

    # Minimal mocks for harness to avoid full engine spin-up
    # Use a pre-baked CertificationResult with final_state set
    # Monkeypatch _persist_proof_bundle to capture the write
    ...
```

**Note:** This test requires either a real engine run (slow, integration-level) or monkeypatching `run_scenario()` internals. The recommended approach:

- Use the integration test pattern from `tests/integration/certification/test_catalog_arena_smoke.py` (which uses `CertificationHarness` with a real small catalog state).
- Alternatively, extract the side-file write logic into a standalone function `_write_full_evidence(output_dir, result)` and test that function directly with `fake_state`.

**Preferred approach (testable and isolated):**

```python
def test_full_evidence_writes_canonical_state_file(tmp_path, fake_state, minimal_result):
    from src.certification.models import EvidenceLevel
    import dataclasses, json
    from src.certification.harness import CertificationHarness

    result = dataclasses.replace(minimal_result, final_state=fake_state)

    # Call the internal write helper directly (if extracted) or mock harness
    harness = _make_minimal_harness(tmp_path)
    harness._write_full_evidence(result)

    expected_path = tmp_path / "state" / f"{result.run_id}.final_state.canonical.json"
    assert expected_path.exists()
    data = json.loads(expected_path.read_text())
    assert data["tick"] == fake_state.tick
    assert "entities" in data
```

If the write logic is NOT extracted into a separate method, test via `_persist_proof_bundle()` directly by injecting `evidence_level=FULL` and asserting the side file path.

**Coverage:** FULL evidence side file created; correct path; content uses canonical data (not `asdict`).

---

### TC-8: `test_full_evidence_uses_canonical_hasher_not_asdict`

**Purpose:** FULL evidence write calls `CanonicalStateHasher.to_canonical_data()`, NOT `asdict()`.

```python
def test_full_evidence_uses_canonical_hasher_not_asdict(tmp_path, fake_state, minimal_result, monkeypatch):
    from dataclasses import asdict
    from src.certification.models import EvidenceLevel
    import dataclasses

    # Make asdict raise if called
    def forbidden_asdict(obj):
        raise AssertionError("asdict() must not be called during FULL evidence write")
    monkeypatch.setattr("src.certification.harness.asdict", forbidden_asdict, raising=False)
    monkeypatch.setattr("src.certification.models.asdict", forbidden_asdict, raising=False)

    result = dataclasses.replace(minimal_result, final_state=fake_state)
    harness = _make_minimal_harness(tmp_path)
    harness._write_full_evidence(result)  # must not raise

    expected_path = tmp_path / "state" / f"{result.run_id}.final_state.canonical.json"
    assert expected_path.exists()
```

**Coverage:** Architectural guard — the canonical path, not `asdict`, is always used.

---

### TC-9: `test_proof_index_never_contains_full_state`

**Purpose:** Even with `evidence_level=FULL`, `proofs_bundle.json` never contains raw state data.

```python
def test_proof_index_never_contains_full_state(tmp_path, fake_state, minimal_result):
    from src.certification.models import EvidenceLevel
    from src.certification.recorder import CertificationRecorder
    import dataclasses, json

    result = dataclasses.replace(minimal_result, final_state=fake_state)
    recorder = CertificationRecorder(str(tmp_path))
    recorder.record(result, EvidenceLevel.FULL)

    bundle_path = tmp_path / "proofs_bundle.json"
    assert bundle_path.exists()
    bundle = json.loads(bundle_path.read_text())
    key = f"{result.profile_name}:{result.scenario_id}"
    entry = bundle[key]

    # Full state must never appear in the bundle entry
    assert entry["final_state"] is None
    # final_state_artifact is a path string, not the state content
    if entry["final_state_artifact"] is not None:
        assert isinstance(entry["final_state_artifact"], str)
        assert entry["final_state_artifact"].startswith("state/")
    # No deeply nested entity structure embedded
    assert "entities" not in entry
```

**Coverage:** Bundle isolation invariant — state data never leaks into `proofs_bundle.json`.

---

### TC-10: `test_full_evidence_write_failure_is_nonfatal`

**Purpose:** If the state file write fails (e.g., OS error), the recorder call still succeeds.

```python
def test_full_evidence_write_failure_is_nonfatal(tmp_path, fake_state, minimal_result, monkeypatch):
    from src.certification.models import EvidenceLevel
    from src.certification.harness import CertificationHarness
    import dataclasses

    # Make Path.write_text raise
    def raise_on_write(self, *args, **kwargs):
        raise OSError("Simulated disk failure")
    monkeypatch.setattr("pathlib.Path.write_text", raise_on_write)

    result = dataclasses.replace(minimal_result, final_state=fake_state)
    harness = _make_minimal_harness(tmp_path)

    # Must not raise
    harness._write_full_evidence(result)
```

**Coverage:** try/except non-fatal guarantee per ticket implementation notes.

---

### TC-11: `test_full_evidence_final_state_hash_in_artifact`

**Purpose:** When FULL evidence is requested, the artifact dict includes `final_state_hash` as a SHA-256 hex string.

```python
def test_full_evidence_final_state_hash_in_artifact(minimal_result, fake_state):
    from src.certification.models import EvidenceLevel
    import dataclasses, hashlib, json

    result = dataclasses.replace(minimal_result, final_state=fake_state)
    d = result.to_artifact_dict(EvidenceLevel.FULL)

    assert "final_state_hash" in d
    assert d["final_state_hash"] is not None
    assert len(d["final_state_hash"]) == 64  # SHA-256 hex
    # Verify it matches manual computation
    from src.engine.checkpoint import CanonicalStateHasher
    expected_hash = CanonicalStateHasher.get_hash(fake_state)
    assert d["final_state_hash"] == expected_hash
```

**Note:** This test requires `FakeState` to be compatible with `CanonicalStateHasher.to_canonical_data()`. The fake state must expose the same fields that `to_canonical_data()` accesses. Consider using a real minimal `AuthoritativeState` for this test if `FakeState` is insufficient.

**Coverage:** `final_state_hash` derivation matches existing `get_hash()` behavior.

---

### TC-12: `test_existing_callers_not_broken_by_evidence_level_default`

**Purpose:** Regression — existing callers that call `to_artifact_dict()` without arguments continue to work.

```python
def test_existing_callers_not_broken_by_evidence_level_default(minimal_result):
    d = minimal_result.to_artifact_dict()   # no evidence_level arg
    assert d["schema_version"] == "certification_result.v1"
    assert d["final_state"] is None
    assert d["final_state_artifact"] is None
    assert "conformance_passed" in d
    assert "failure_kind" in d
```

**Coverage:** Backward compatibility of the `evidence_level` default.

---

### TC-13: `test_recorder_record_accepts_evidence_level`

**Purpose:** `CertificationRecorder.record()` accepts `evidence_level` kwarg without error.

```python
def test_recorder_record_accepts_evidence_level(tmp_path, minimal_result):
    from src.certification.models import EvidenceLevel
    from src.certification.recorder import CertificationRecorder

    recorder = CertificationRecorder(str(tmp_path))
    path = recorder.record(minimal_result, EvidenceLevel.SUMMARY)
    assert path.endswith("proofs_bundle.json")
    path2 = recorder.record(minimal_result, EvidenceLevel.FULL)
    assert path2.endswith("proofs_bundle.json")
```

**Coverage:** Signature extension accepted; recorder returns expected path.

---

### TC-14: `test_state_dir_created_on_full_evidence`

**Purpose:** The `state/` subdirectory is created by `mkdir(parents=True, exist_ok=True)` when writing the side file.

```python
def test_state_dir_created_on_full_evidence(tmp_path, fake_state, minimal_result):
    from src.certification.models import EvidenceLevel
    import dataclasses

    result = dataclasses.replace(minimal_result, final_state=fake_state)
    harness = _make_minimal_harness(tmp_path)
    harness._write_full_evidence(result)

    state_dir = tmp_path / "state"
    assert state_dir.is_dir()
```

**Coverage:** Directory creation behavior.

---

## Helper: `_make_minimal_harness(tmp_path)`

```python
def _make_minimal_harness(tmp_path):
    from src.certification.harness import CertificationHarness
    from src.config.profiles import RuntimeProfile
    from unittest.mock import MagicMock
    profile = MagicMock(spec=RuntimeProfile)
    profile.name = "test_profile"
    profile.max_tick_budget_ms = 50.0
    # Bypass HardwareClassifier and git subprocess in __init__
    with patch("src.certification.harness.HardwareClassifier.get_detailed_telemetry", return_value={}):
        with patch("src.certification.harness.HardwareClassifier.detect_class", return_value=...):
            harness = CertificationHarness(profile, output_dir=str(tmp_path))
    return harness
```

Alternatively: add a `@classmethod` or extract the side-file write as a standalone free function for easier testing.

---

## Parity entries to update after tests pass

| Entry | Action |
|---|---|
| INFRA-189 | Update `text` to note `evidence_level` parameter; add `tests/certification/test_evidence_levels.py` to `test_path` |
| INFRA-190 | Update `text` to note `evidence_level` threading in recorder; extend `test_path` |
| INFRA-191 (new) | Add — covers FULL evidence side-file write, `CanonicalStateHasher` usage, non-fatal failure |
