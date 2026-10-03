---
ticket_id: TCK-20260614-CERT-SAFE-SERIAL
phase: plan
date: 2026-06-14
---

# Plan: TCK-20260614-CERT-SAFE-SERIAL

## Overview

Replace `CertificationResult.to_json()` — which currently calls `asdict(self)` and
recursively deep-copies the live `AuthoritativeState` — with a field-by-field
`to_artifact_dict()` method that never walks `final_state`. `to_json()` delegates to
`to_artifact_dict()`. Dead serialization scaffolding (`safe_asdict`, the local `asdict`
import inside `to_json`) is removed.

---

## Ordered Implementation Steps

### Step 1 — Add `MeasurementPoint.to_dict()` method

**File:** `src/certification/models.py`

**What:** Add a `to_dict(self) -> dict` method to the `MeasurementPoint` dataclass
(lines 44–58). Map all twelve primitive fields explicitly: `tick`, `mode`,
`memory_rss_mb`, `memory_trend_mb_per_tick`, `tick_compute_ms`, `tick_compute_ms_avg`,
`work_debt`, `worker_utilization`, `queue_utilization`, `replay_pressure`,
`active_workers`, `timestamp`. Return a plain dict of primitives — no `asdict()` call.

**Why first:** `to_artifact_dict()` (Step 3) calls `[m.to_dict() for m in self.measurements]`.
This dependency must exist before Step 3 is written.

**Scope guard:** Do not touch `ScenarioExpectations`, `EnvironmentCapture`, or
`CertificationResult` in this step.

**Independently verifiable:** Import `MeasurementPoint` in a REPL/test, call `.to_dict()`,
assert all twelve keys are present with correct values.

---

### Step 2 — Add `CertificationResult._final_state_summary()` private method

**File:** `src/certification/models.py`

**What:** Add `_final_state_summary(self) -> dict | None` to `CertificationResult`.

Logic:
- If `self.final_state is None`, return `None`.
- Otherwise, access exactly these attributes via `getattr(state, name, default)` — never
  direct attribute access:
  - `tick` (default `None`)
  - `seed` (default `None`)
  - `entities` (default `{}`) → `entity_count = len(entities)`
  - `resource_nodes` (default `{}`) → `resource_node_count`
  - `regions` (default `{}`) → `region_count`
  - `buildings` (default `{}`) → `building_count`
  - `corpses` (default `{}`) → `corpse_count`
  - `ground_items` (default `{}`) → `ground_item_count`
- Also include `final_hash` from `self.final_hash` (NOT from the state object).
- Return a dict with keys: `tick`, `seed`, `entity_count`, `resource_node_count`,
  `region_count`, `building_count`, `corpse_count`, `ground_item_count`, `final_hash`.

**Why this order:** `to_artifact_dict()` (Step 3) calls this method. It must exist first.
Using `getattr` throughout is mandatory — the PoisonState test will raise `AssertionError`
if any direct attribute access beyond the listed names is attempted.

**Scope guard:** Do not modify any other method. Do not access any field on `final_state`
beyond the eight listed above. Do not call `asdict`, `vars()`, or `__dict__` on `final_state`.

**Independently verifiable:** Instantiate `CertificationResult` with `final_state=None`,
call `_final_state_summary()`, assert `None`. Instantiate with a simple namespace object
having the eight fields, call method, assert correct counts.

---

### Step 3 — Add `CertificationResult.to_artifact_dict()` method

**File:** `src/certification/models.py`

**What:** Add `to_artifact_dict(self) -> dict` to `CertificationResult`. Build the
proof artifact dict field-by-field. Do not call `asdict()`, `safe_asdict()`, `vars()`,
or `__dict__` at any point.

**Guard block at top of method:**
```python
if not self.profile_name:
    raise ValueError(
        "to_artifact_dict(): profile_name is required (certification_contract_me.md §5)"
    )
if not self.scenario_id:
    raise ValueError(
        "to_artifact_dict(): scenario_id is required (certification_contract_me.md §5)"
    )
if self.environment is None:
    raise ValueError(
        "to_artifact_dict(): environment is required (certification_contract_me.md §5)"
    )
```

**Environment sub-dict** (key names differ from field names per AC):
```python
"environment": {
    "detected_hardware_class": self.environment.detected_class.value,
    "effective_hardware_class": self.environment.effective_class.value,
    "override_applied": self.environment.override_applied,
    "detected_facts": self.environment.detected_facts,
    "os_name": self.environment.os_name,
    "python_version": self.environment.python_version,
}
```

**Measurements list:** `[m.to_dict() for m in self.measurements]` (requires Step 1).

**Enum fields:** `.value` on `stop_condition` and `failure_kind`.

**Full returned dict keys** (in this order, per AC):
`schema_version`, `run_id`, `timestamp`, `commit_sha`, `profile_name`, `scenario_id`,
`seed`, `environment`, `measurements`, `baseline_hash`, `final_hash`,
`governor_mode_sequence`, `conformance_passed`, `stop_condition`,
`allowed_failure_observed`, `failure_kind`, `failure_reason`, `peak_rss_mb`,
`total_cpu_sec`, `final_state` (always `None`), `final_state_summary`,
`final_state_artifact` (always `None`).

`schema_version` value: `"certification_result.v1"`.

`final_state_summary` value: `self._final_state_summary()` (requires Step 2).

`detected_facts` handling: include as-is; `json.dumps` in `to_json()` will use
`default=str` to handle non-JSON-serializable values.

**Scope guard:** Do not touch `to_json()` yet (that is Step 4). Do not modify any other
class.

**Independently verifiable:** Call `to_artifact_dict()` on a minimal `CertificationResult`
with `final_state=None`; assert all required keys are present; assert `final_state` is
`None`; assert `environment["detected_hardware_class"]` is a string (not enum).

---

### Step 4 — Replace `to_json()` implementation; remove dead code

**File:** `src/certification/models.py`

**What:** Rewrite `to_json()` to delegate entirely to `to_artifact_dict()`:

```python
def to_json(self) -> str:
    from enum import Enum

    def _default(obj):
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, (set, frozenset)):
            return sorted(list(obj))
        return str(obj)

    return json.dumps(self.to_artifact_dict(), default=_default, indent=2)
```

Remove from the new `to_json()` body:
- The `from dataclasses import asdict, is_dataclass` local import.
- The `safe_asdict(obj, memo=None)` inner function definition (all 37 lines).
- The `try/except RecursionError` block that called `asdict(self)` and `safe_asdict(self)`.
- The old `custom_serializer` inner function.

Also remove the module-level `asdict` import on line 5 if `asdict` is no longer used
anywhere else in the module. Verify by scanning the full file: if no other call to
`asdict()` exists after this change, remove it from `from dataclasses import dataclass, field, asdict`.

**Scope guard:** Do not change `to_artifact_dict()` or `_final_state_summary()`. Do not
change any other class or method. Do not change `recorder.py` or `harness.py`.

**Independently verifiable:** Call `to_json()` on a minimal result; assert the returned
string parses as valid JSON; assert the parsed dict contains `schema_version`; assert
`final_state` key is `None`; assert no `AssertionError` when monkeypatching
`dataclasses.asdict` to raise.

---

### Step 5 — Write new test file

**File:** `tests/certification/test_cert_result_serialization.py` (new file)

**What:** Create the test file as specified in `test_plan.md`. Implement all five tests
and the `_make_minimal_result()` and `PoisonState` helpers:

1. `test_certification_result_summary_does_not_serialize_final_state` — PoisonState guard
2. `test_to_json_does_not_call_asdict` — monkeypatch `dataclasses.asdict` to raise
3. `test_final_state_summary_none_when_no_state` — `final_state=None` path
4. `test_to_artifact_dict_required_fields_present` — AC key completeness
5. `test_to_artifact_dict_guard_raises_on_missing_metadata` — ValueError on empty
   `profile_name` or `scenario_id`

`PoisonState.__getattribute__` must allow only: `tick`, `seed`, `entities`,
`resource_nodes`, `regions`, `buildings`, `corpses`, `ground_items`. All other attribute
access raises `AssertionError`.

**Scope guard:** Do not add tests to existing files. Do not alter test fixtures in
other test files.

**Independently verifiable:** `pytest tests/certification/test_cert_result_serialization.py -v`
— all five tests pass.

---

### Step 6 — Add INFRA-189 parity ledger entry

**File:** `docs/parity_ledger/infrastructure.yaml`

**What:** Append the new INFRA-189 entry at the bottom of the YAML list (do not insert
in the middle). Entry as specified in `investigation.md`:

```yaml
- id: INFRA-189
  text: >
    CertificationResult.to_artifact_dict() builds the proof artifact field-by-field
    without calling asdict() or safe_asdict(). final_state is always None in the
    artifact dict. final_state_summary contains compact counts when final_state is
    attached, None otherwise.
  status: verified
  priority: P0
  v2_evidence: >
    src/certification/models.py::CertificationResult.to_artifact_dict +
    tests/certification/test_cert_result_serialization.py
  test_path: tests/certification/test_cert_result_serialization.py
  divergence_note: ""
```

**Scope guard:** Do not alter any existing entry. Do not modify `schema.json`.

**Independently verifiable:** Open file, confirm INFRA-189 block is present and valid YAML.

---

### Step 7 — Run regression suite; verify no existing test breaks

**Command:** `pytest tests/certification/ -v --tb=short`

**What:** Run the full certification test suite. All pre-existing tests must pass.
New tests (Step 5) must also pass here.

If a pre-existing test fails, diagnose and fix in `src/certification/models.py` only.
Do not alter existing test files to make tests pass.

**Scope guard:** This is a verification step — make no code changes here unless a
pre-existing test reveals an incompatibility in the implementation from Steps 1–5.

---

## Dependency Map

```
Step 1 (MeasurementPoint.to_dict)
    └─► Step 3 (to_artifact_dict uses m.to_dict())

Step 2 (_final_state_summary)
    └─► Step 3 (to_artifact_dict calls _final_state_summary())

Step 3 (to_artifact_dict)
    └─► Step 4 (to_json delegates to to_artifact_dict)
    └─► Step 5 (tests call to_artifact_dict directly)

Step 4 (to_json rewrite)
    └─► Step 5 (test_to_json_does_not_call_asdict tests to_json)
    └─► Step 7 (regression suite exercises to_json via harness/recorder path)

Step 5 (new test file)
    └─► Step 7 (pytest collects new tests)

Step 6 (parity ledger)
    no code dependency — can be done any time after Step 3 is complete
```

Steps 1 and 2 are independent of each other and can be written in the same edit pass.
Step 6 is independent of all code changes and can be done after Step 3.

---

## Scope Guards (what NOT to touch)

| Area | Rationale |
|---|---|
| `src/certification/recorder.py` | Sibling ticket TCK-20260614-CERT-RECORDER-REFACTOR owns recorder changes. The current `json.loads(result.to_json())` path works correctly with the new `to_json()` output. |
| `src/certification/harness.py` | `final_state=kernel.state` assignment is correct; only the serialization path changes. Out of scope per ticket. |
| `src/core/state.py` | `AuthoritativeState` is not modified. The fix avoids walking it, not rewriting it. |
| `tests/certification/test_harness_contract.py` | Must not be altered. The existing tests are the regression gate. |
| `tests/certification/test_allowed_failure_truth.py` | No serialization — unaffected and must not be touched. |
| `docs/parity_ledger/` other entries | Only INFRA-189 is added. No existing entry is changed. |
| EvidenceLevel enum or full canonical state export | Owned by TCK-20260614-CERT-EVIDENCE-LEVELS. |
| `ScenarioExpectations` dataclass | Not in scope — no fields needed in artifact dict. |

---

## Acceptance Criteria Mapped to Steps

| Acceptance Criterion | Covered by Step(s) |
|---|---|
| `to_artifact_dict()` exists and returns dict with all required fields | Step 3, verified by Step 5 (Test 4) |
| `profile_name`, `scenario_id`, `detected_hardware_class`, `effective_hardware_class` required — fails if missing | Step 3 (guard block), verified by Step 5 (Test 5) |
| `to_artifact_dict()["final_state"]` is always `None` | Step 3, verified by Step 5 (Tests 1, 3, 4) |
| `to_artifact_dict()["final_state_summary"]` is compact dict when `final_state` attached, `None` otherwise | Steps 2+3, verified by Step 5 (Tests 1, 3) |
| `to_json()` returns `json.dumps(self.to_artifact_dict())` — no `asdict()` or `safe_asdict()` | Step 4, verified by Step 5 (Test 2) |
| `test_certification_result_summary_does_not_serialize_final_state` passes with PoisonState | Step 5 (Test 1) + Step 7 |
| Existing tests in `tests/certification/` pass unchanged | Step 7 |
| `environment` dict exposes `detected_hardware_class` / `effective_hardware_class` keys | Step 3, verified by Step 5 (Test 4) |
| `schema_version: "certification_result.v1"` present in artifact | Step 3, verified by Step 5 (Tests 2, 4) |
| `final_state_artifact: None` placeholder present | Step 3, verified by Step 5 (Test 4) |
| INFRA-189 parity entry added | Step 6 |

---

## Unresolved Questions

None. All open questions from the investigation are resolved:

| Question | Resolution |
|---|---|
| Add `MeasurementPoint.to_dict()` or map inline? | Add `to_dict()` — ticket spec says `[m.to_dict() for m in self.measurements]`. Step 1. |
| `detected_facts` non-JSON-safe values? | Pass as-is; use `default=str` in `to_json()`. No sanitizer needed. Step 4. |
| `ValueError` or `AssertionError` for missing metadata guard? | `ValueError` — matches existing recorder guard pattern at `recorder.py:22`. Step 3. |
| Is recorder compatibility broken by this change? | No. Recorder reads `conformance_passed`, `failure_kind`, `failure_reason`, `profile_name`, `scenario_id` — all present in `to_artifact_dict()` output. Recorder change is deferred to sibling ticket. |
| Does `asdict` module-level import need removal? | Yes — after Step 4, `asdict` is unused in the module. Remove from the `from dataclasses import ...` line. Step 4. |
