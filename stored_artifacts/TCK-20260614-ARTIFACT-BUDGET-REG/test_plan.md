---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-ARTIFACT-BUDGET-REG
date: 2026-06-14
tags: [resource-safety, artifact, budget, registry, testing]
---

# TCK-20260614-ARTIFACT-BUDGET-REG — Test Plan

## Regression Surface

These existing test suites must pass without modification after implementation:

| Suite | File | Why at risk |
|---|---|---|
| Certification recorder | `tests/certification/test_recorder_refactor.py` | Wire point for budget check is in `record()` — must not break existing call signatures or `proofs_bundle.json` write behavior |
| Evidence levels | `tests/certification/test_evidence_levels.py` | `to_artifact_dict()` is the size estimation input; any change to its call must remain backward compatible |
| Cert result serialization | `tests/certification/test_cert_result_serialization.py` | Validates `to_artifact_dict()` field contract; budget check must not alter artifact dict shape |
| Manifest snapshot | `tests/certification/test_manifest_snapshot.py` | Non-fatal write pattern; budget check must follow same non-fatal pattern |
| Lab budget guardrails | `tests/unit/lab/test_lab_budget_guardrails.py` | `BudgetCheckResult` name exists in `src/lab/guardrails.py`; the new module's `BudgetCheckResult` must not shadow or conflict with the lab import |
| Harness contract | `tests/certification/test_harness_contract.py` | End-to-end harness path exercises `record()` — must remain unaffected |
| Queue worker singleton | `tests/unit/test_queue_worker_singleton.py` | Singleton pattern reference (INFRA-179) — registry singleton must not interfere |

---

## New Tests Required

**File**: `tests/certification/test_artifact_budget.py` (new file)

All tests are pure unit tests — no simulation kernel, no file I/O beyond tmp_path, no orchestrator.

---

### `test_registry_allows_within_budget`

**AC coverage**: "ArtifactBudgetRegistry class exists and can register, query, and check budgets"; "BudgetCheckResult carries allowed, action, and reason"

```
Arrange:
  registry = ArtifactBudgetRegistry()
  budget = ArtifactBudget(
      artifact_type="certification_result",
      max_size_mb=2.0,
      soft_limit_mb=1.5,   # or derived as 75% of max
      retention="keep_latest_per_scenario",
      allow_full_state=False,
      compression="optional",
      fail_on_budget_violation=False,
  )
  registry.register(budget)
  estimated_bytes = int(1.0 * 1024 * 1024)  # 1 MB — well within 2 MB

Act:
  result = registry.check("certification_result", estimated_bytes)

Assert:
  assert result.allowed is True
  assert result.action == "allow"
  assert result.reason is None
```

---

### `test_registry_rejects_over_budget`

**AC coverage**: "BudgetCheckResult carries allowed, action, and reason"; default `fail_on_budget_violation=False` must only warn, not raise; `fail_on_budget_violation=True` path should return action="reject" with allowed=False.

```
Arrange:
  registry = ArtifactBudgetRegistry()
  budget = ArtifactBudget(
      artifact_type="certification_result",
      max_size_mb=2.0,
      retention="keep_latest_per_scenario",
      allow_full_state=False,
      compression="optional",
      fail_on_budget_violation=True,
  )
  registry.register(budget)
  estimated_bytes = int(3.0 * 1024 * 1024)  # 3 MB — exceeds 2 MB max

Act:
  result = registry.check("certification_result", estimated_bytes)

Assert:
  assert result.allowed is False
  assert result.action == "reject"
  assert result.reason is not None
  assert "certification_result" in result.reason or "2.0" in result.reason
```

Also test with `fail_on_budget_violation=False` for same oversized estimate:
```
  result_warn = registry_warn.check("certification_result", estimated_bytes)
  assert result_warn.allowed is True   # warn-only, not rejected
  assert result_warn.action == "warn"
  assert result_warn.reason is not None
```

---

### `test_registry_warns_on_soft_limit`

**AC coverage**: soft-limit action ("warn") is distinct from hard-limit action ("reject" / warn-allowed); tests the middle tier.

```
Arrange:
  registry = ArtifactBudgetRegistry()
  # soft_limit_mb=1.0, max_size_mb=2.0
  budget = ArtifactBudget(
      artifact_type="certification_result",
      max_size_mb=2.0,
      soft_limit_mb=1.0,
      retention="keep_latest_per_scenario",
      allow_full_state=False,
      compression="optional",
      fail_on_budget_violation=False,
  )
  registry.register(budget)
  estimated_bytes = int(1.5 * 1024 * 1024)  # 1.5 MB — above soft_limit, below max

Act:
  result = registry.check("certification_result", estimated_bytes)

Assert:
  assert result.allowed is True
  assert result.action == "warn"
  assert result.reason is not None
```

---

### `test_recorder_consults_budget_before_write`

**AC coverage**: "`CertificationRecorder.record()` calls `registry.check('certification_result', estimated_size)` before writing"

```
Arrange:
  Use tmp_path as output_dir.
  Build a minimal CertificationResult (can reuse fixture from test_recorder_refactor.py).
  Create a mock ArtifactBudgetRegistry with a tracked check() call.
  Inject registry into CertificationRecorder (via constructor arg or module-level singleton setter).

Act:
  recorder.record(result)

Assert:
  mock_registry.check.assert_called_once()
  call_args = mock_registry.check.call_args
  assert call_args[0][0] == "certification_result"
  estimated = call_args[0][1]
  assert isinstance(estimated, int)
  assert estimated > 0
  # proofs_bundle.json still written (warn-only default)
  assert (tmp_path / "proofs_bundle.json").exists()
```

Second sub-test — when registry returns `allowed=False` and `fail_on_budget_violation=True`, recorder raises:
```
  mock_registry.check.return_value = BudgetCheckResult(allowed=False, action="reject", reason="too large")
  # registry has fail_on_budget_violation=True on the registered budget
  with pytest.raises(ArtifactBudgetViolationError):
      recorder.record(result)
  # proofs_bundle.json NOT written on hard reject
  assert not (tmp_path / "proofs_bundle.json").exists()
```

---

### Additional recommended tests (not in AC but cover regression-prone paths)

#### `test_registry_unknown_type_returns_allow`

When `check()` is called for an artifact type not registered in the registry, it must return `BudgetCheckResult(allowed=True, action="allow", reason=None)` — unknown types are not blocked. This prevents future artifact writers from failing silently because they forgot to register a budget.

#### `test_registry_get_returns_none_for_unknown`

`registry.get("unknown_type")` returns `None` without raising.

#### `test_registry_overwrite_replaces_budget`

Calling `register()` twice for the same `artifact_type` replaces the prior budget (last-write-wins), consistent with the singleton reset requirement for tests.

#### `test_singleton_reset_between_tests`

Call `ArtifactBudgetRegistry._reset_for_testing()` (or equivalent) between two test scenarios and verify that a previously registered budget is no longer present. This is the guard against test pollution.

#### `test_default_budgets_registered`

The module-level default budget setup registers budgets for at minimum:
- `certification_result` — max 2 MB, `fail_on_budget_violation=False`
- `replay_chunk` — some reasonable default, `fail_on_budget_violation=False`
- `behavior_report` — some reasonable default, `fail_on_budget_violation=False`

Assert all three types return non-None from `registry.get(artifact_type)`.

---

## Scoped Pytest Commands

```bash
# Primary suite for this ticket (new tests):
pytest tests/certification/test_artifact_budget.py -v

# Regression: full certification suite
pytest tests/certification/ -v

# Regression: lab guardrails (name conflict check)
pytest tests/unit/lab/test_lab_budget_guardrails.py -v

# Combined scoped run (all directly touched modules):
pytest tests/certification/ tests/unit/lab/test_lab_budget_guardrails.py -v

# Exclude slow tests if running locally:
pytest tests/certification/ tests/unit/lab/test_lab_budget_guardrails.py -v -m "not slow"
```

Do NOT run `pytest tests/` (full suite) — this is out of scope and violates the Testing Rule.

---

## Anti-Drift Test Guards

1. **`BudgetCheckResult` import isolation**: the test file must import `BudgetCheckResult` from `src.certification.artifact_budget`, not from `src.lab.guardrails`. If both are imported, use aliases (`from src.lab.guardrails import BudgetCheckResult as LabBudgetCheckResult`) to prevent shadowing.

2. **`proofs_bundle.json` presence invariant**: `test_recorder_consults_budget_before_write` must assert that `proofs_bundle.json` IS written when `action="warn"` (default) and is NOT written when `action="reject"` with `fail_on_budget_violation=True`. This guards against regression to the INFRA-060 invariant.

3. **No simulation kernel in budget tests**: `test_artifact_budget.py` must not import or construct `Kernel`, `WorldCompiler`, or `ScenarioLabOrchestrator`. If these appear, the test has drifted into integration territory.

4. **Size estimation uses `to_artifact_dict()`**: any test that constructs a `CertificationResult` and estimates size must call `len(json.dumps(result.to_artifact_dict()).encode())` — not `len(result.to_json().encode())`. A comment in the test should cite INFRA-189.

5. **`fail_on_budget_violation=False` is the default**: every test that constructs `ArtifactBudget` without explicitly setting `fail_on_budget_violation` must pass — the default must be `False`. A test that sets `fail_on_budget_violation=True` must do so explicitly and test the raise path.

6. **Registry singleton cleanup**: any test that mutates the module-level registry singleton (if used) must call `_reset_for_testing()` in a `pytest.fixture` with `autouse=True` or in teardown. Failure to reset is a test order dependency hazard.
