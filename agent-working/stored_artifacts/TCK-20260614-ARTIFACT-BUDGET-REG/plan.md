---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-ARTIFACT-BUDGET-REG
date: 2026-06-14
tags: [resource-safety, artifact, budget, registry, performance]
---

# TCK-20260614-ARTIFACT-BUDGET-REG — Implementation Plan

## Resolved Pre-Conditions

All open questions from investigation are resolved and must NOT be re-raised:

1. `soft_limit_mb`: explicit optional field on `ArtifactBudget` (default `None` = no soft limit); when set, triggers `action="warn"` before `max_size_mb` hard limit.
2. `replay_chunk` estimation: `len(json.dumps(events).encode())` called synchronously in `_rotate_chunk()` before thread submission — accurate and non-blocking.
3. `behavior_report`: stub-only registration with no wire-up this ticket (pre-register budget, no writer hook needed).
4. Registry injection: module-level singleton via `get_default_registry()` and `reset_default_registry()` for test isolation; `CertificationRecorder` accepts optional `registry: ArtifactBudgetRegistry | None = None` constructor arg (uses default singleton if `None`).

## Prerequisite Confirmation

- TCK-20260614-CERT-RECORDER-REFACTOR is in `tickets/done/` — prerequisite satisfied.
- `src/certification/recorder.py` already uses `result.to_artifact_dict()` (confirmed line 50).

---

## Dependency Map

```
Step 1 (artifact_budget.py core module)
  └── Step 2 (default budget registration)     [depends on Step 1]
        └── Step 3 (CertificationRecorder wire) [depends on Steps 1-2]
        └── Step 4 (ReplayManager wire)          [depends on Steps 1-2]
  └── Step 5 (new test file)                    [depends on Steps 1-4]
        └── Step 6 (regression test run)         [depends on Step 5]
  └── Step 7 (parity ledger entry)              [depends on Steps 1-4]
```

Steps 3 and 4 are independent of each other (both depend on Steps 1-2).
Step 7 is independent of Steps 5-6 and can be done concurrently.

---

## Step 1 — Create `src/certification/artifact_budget.py` (core module)

**Files to change:** `src/certification/artifact_budget.py` (new file)

**Scope:** Define all public types and the registry class. No wiring. No defaults registered yet.

### Deliverables

```python
# Public surface (exact names required by AC and tests):

@dataclass
class ArtifactBudget:
    artifact_type: str
    max_size_mb: float
    retention: str                         # e.g. "keep_latest_per_scenario"
    allow_full_state: bool
    compression: str                       # "optional" | "none"
    fail_on_budget_violation: bool = False # MUST default False
    soft_limit_mb: float | None = None    # None = no soft limit

@dataclass
class BudgetCheckResult:
    allowed: bool
    action: str     # "allow" | "warn" | "compact" | "reject"
    reason: str | None

class ArtifactBudgetViolationError(Exception):
    """Raised when fail_on_budget_violation=True and budget is exceeded."""
    pass

class ArtifactBudgetRegistry:
    def register(self, budget: ArtifactBudget) -> None: ...
    def get(self, artifact_type: str) -> ArtifactBudget | None: ...
    def check(self, artifact_type: str, estimated_size_bytes: int) -> BudgetCheckResult: ...

# Module-level singleton:
def get_default_registry() -> ArtifactBudgetRegistry: ...
def reset_default_registry() -> None: ...
```

### `check()` logic (exact decision tree)

```
estimated_mb = estimated_size_bytes / (1024 * 1024)
budget = self.get(artifact_type)

if budget is None:
    return BudgetCheckResult(allowed=True, action="allow", reason=None)

if estimated_mb > budget.max_size_mb:
    if budget.fail_on_budget_violation:
        return BudgetCheckResult(
            allowed=False,
            action="reject",
            reason=f"{artifact_type} estimated {estimated_mb:.2f} MB exceeds max {budget.max_size_mb} MB"
        )
    else:
        # warn-only: write is still allowed
        return BudgetCheckResult(
            allowed=True,
            action="warn",
            reason=f"{artifact_type} estimated {estimated_mb:.2f} MB exceeds max {budget.max_size_mb} MB (warn-only)"
        )

if budget.soft_limit_mb is not None and estimated_mb > budget.soft_limit_mb:
    return BudgetCheckResult(
        allowed=True,
        action="warn",
        reason=f"{artifact_type} estimated {estimated_mb:.2f} MB exceeds soft limit {budget.soft_limit_mb} MB"
    )

return BudgetCheckResult(allowed=True, action="allow", reason=None)
```

### Scope guards (Step 1)

- Do NOT register any budgets in this step — that is Step 2.
- Do NOT import from `src.lab.guardrails` — name collision risk with `BudgetCheckResult`.
- Do NOT make the singleton automatically initialized with defaults — Step 2 does that.
- `ArtifactBudgetViolationError` is defined here but NOT raised by `check()` itself — the caller (`recorder.py`) raises it when `action="reject"`.

### Acceptance criteria mapped

- AC: "ArtifactBudgetRegistry class exists and can register, query, and check budgets" ✓
- AC: "BudgetCheckResult carries allowed, action, and reason" ✓
- Test: `test_registry_allows_within_budget`, `test_registry_rejects_over_budget`, `test_registry_warns_on_soft_limit`, `test_registry_unknown_type_returns_allow`, `test_registry_get_returns_none_for_unknown`, `test_registry_overwrite_replaces_budget`, `test_singleton_reset_between_tests` — all covered by this step's API.

---

## Step 2 — Register default budgets in `src/certification/artifact_budget.py`

**Files to change:** `src/certification/artifact_budget.py` (same file as Step 1)

**Scope:** Add a `_register_default_budgets()` function called during `get_default_registry()` initialization. This is the only place default budgets are wired — no defaults in the class constructor.

### Default budget values

```python
_DEFAULTS = [
    ArtifactBudget(
        artifact_type="certification_result",
        max_size_mb=2.0,
        soft_limit_mb=1.5,
        retention="keep_latest_per_scenario",
        allow_full_state=False,
        compression="optional",
        fail_on_budget_violation=False,
    ),
    ArtifactBudget(
        artifact_type="replay_chunk",
        max_size_mb=10.0,
        soft_limit_mb=8.0,
        retention="keep_latest_per_scenario",
        allow_full_state=False,
        compression="optional",
        fail_on_budget_violation=False,  # MUST be False — async thread path
    ),
    ArtifactBudget(
        artifact_type="behavior_report",
        max_size_mb=5.0,
        retention="keep_latest_per_scenario",
        allow_full_state=False,
        compression="optional",
        fail_on_budget_violation=False,
    ),
    ArtifactBudget(
        artifact_type="proof_index",
        max_size_mb=1.0,
        retention="keep_latest_per_scenario",
        allow_full_state=False,
        compression="optional",
        fail_on_budget_violation=False,
    ),
]
```

### Singleton initialization pattern

```python
_default_registry: ArtifactBudgetRegistry | None = None

def get_default_registry() -> ArtifactBudgetRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = ArtifactBudgetRegistry()
        for b in _DEFAULTS:
            _default_registry.register(b)
    return _default_registry

def reset_default_registry() -> None:
    global _default_registry
    _default_registry = None
```

### Scope guards (Step 2)

- `fail_on_budget_violation=False` on ALL defaults — no exceptions. Existing tests must not break.
- Do NOT call `get_default_registry()` at module import time (only on first call to the function).
- `reset_default_registry()` must leave `_default_registry = None` so the next `get_default_registry()` call re-initializes with fresh defaults.

### Acceptance criteria mapped

- AC: "Default budgets are registered for certification_result (max 2 MB, no full state), replay_chunk, behavior_report" ✓
- Test: `test_default_budgets_registered` ✓
- Test: `test_singleton_reset_between_tests` ✓

---

## Step 3 — Wire budget check into `CertificationRecorder.record()`

**Files to change:** `src/certification/recorder.py`

**Scope:** Add optional `registry` constructor parameter; add size estimation and budget check before the `json.dump(bundle, f, indent=2)` call at line 56. Raise `ArtifactBudgetViolationError` on `action="reject"`. Log warning on `action="warn"`. Never prevent the write when `action="allow"` or `action="warn"`.

### Constructor change

```python
# Before:
def __init__(self, output_dir: str = "reports/certification"):
    self._output_dir = Path(output_dir)
    self._output_dir.mkdir(parents=True, exist_ok=True)

# After:
from src.certification.artifact_budget import (
    ArtifactBudgetRegistry,
    ArtifactBudgetViolationError,
    get_default_registry,
)

def __init__(
    self,
    output_dir: str = "reports/certification",
    registry: ArtifactBudgetRegistry | None = None,
):
    self._output_dir = Path(output_dir)
    self._output_dir.mkdir(parents=True, exist_ok=True)
    self._registry = registry  # None = lazy-resolve default singleton at call time
```

### `record()` change — insertion point

Insert AFTER computing `bundle[key]` (line 54) and BEFORE the `with open(bundle_path, "w")` write (line 56):

```python
# Budget check (INFRA-060: failure paths must remain visible)
registry = self._registry if self._registry is not None else get_default_registry()
artifact_dict = bundle[key]  # already computed above at line 50-54
estimated_bytes = len(json.dumps(artifact_dict).encode())
check = registry.check("certification_result", estimated_bytes)
if check.action == "reject":
    # fail_on_budget_violation=True path — raise before any write
    raise ArtifactBudgetViolationError(
        f"CertificationRecorder: budget reject for certification_result — {check.reason}"
    )
if check.action == "warn":
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "CertificationRecorder: budget warning for certification_result — %s", check.reason
    )
# Proceed with write regardless of action="allow" or action="warn"
```

### Scope guards (Step 3)

- Do NOT change `record()` method signature — only the constructor gains `registry`.
- Do NOT alter `proofs_bundle.json` key format (`profile:scenario`).
- Do NOT use `dataclasses.asdict()` or `result.to_json()` for estimation — use `artifact_dict` (the `to_artifact_dict()` output already stored in `bundle[key]`).
- Size estimation must measure the single new entry (`bundle[key]`), not the full bundle.
- The `release_report.md` write (lines 60–83) is NOT affected by the budget check.
- Do NOT introduce `import logging` if `logging` is not already imported — use the module's existing logger.
- `final_state` must never be embedded in `artifact_dict` — this is already enforced by `to_artifact_dict()` (INFRA-189); do not add any guard here.

### Acceptance criteria mapped

- AC: "CertificationRecorder.record() calls registry.check('certification_result', estimated_size) before writing; logs warning on fail_on_budget_violation=False, raises on True" ✓
- Test: `test_recorder_consults_budget_before_write` ✓

---

## Step 4 — Wire budget check into `ReplayManager._rotate_chunk()`

**Files to change:** `src/engine/replay_manager.py`

**Scope:** Add size estimation and budget check inside `_rotate_chunk()` BEFORE the `self._executor.submit(...)` / direct `_execute_persistence(...)` call. The check runs synchronously in the caller thread — not inside `_execute_persistence` (which runs in the background thread).

### Insertion point in `_rotate_chunk()` (after extracting `events`, before dispatch)

```python
from src.certification.artifact_budget import get_default_registry

# In _rotate_chunk(), after `events = self._buffer.extract_chunk()` and the early return:
# Estimate serialized size synchronously before thread dispatch (per pre-resolved decision)
estimated_bytes = len(json.dumps([e.__dict__ if not hasattr(e, 'to_dict') else e.to_dict()
                                   for e in events]).encode())
# Use a local registry reference to allow test injection via module reset
_budget_registry = get_default_registry()
check = _budget_registry.check("replay_chunk", estimated_bytes)
if check.action in ("warn", "reject"):
    logger.warning(
        "ReplayManager: budget %s for replay_chunk — %s",
        check.action,
        check.reason,
    )
# Never raise for replay_chunk regardless of action — async path swallows exceptions (INFRA-060)
# fail_on_budget_violation=False is enforced in default budget; this is a belt-and-suspenders guard.
# Proceed with dispatch in all cases.
```

**Note on TraceEvent serialization:** Check the `TraceEvent` interface in `src/core/diagnostic.py` to use the correct serialization method (`.to_dict()`, `.__dict__`, or `dataclasses.asdict()`). Use whichever is already used in `_execute_persistence` or `ReplaySink.persist_chunk()` for consistency.

### Scope guards (Step 4)

- Do NOT raise `ArtifactBudgetViolationError` in the replay path — the async thread cannot safely propagate exceptions (M6 Law "Non-blocking" + INFRA-060).
- Do NOT call the budget check inside `_execute_persistence` — it runs in the background thread. The check must run synchronously in `_rotate_chunk()`.
- Do NOT alter `_execute_persistence`, `ReplaySink.persist_chunk()`, or the manifest write path.
- Do NOT change chunk naming, format, or manifest structure (INFRA-155, INFRA-156).
- `fail_on_budget_violation=False` default for `replay_chunk` must be respected — the guard comment in code makes this explicit.

### Acceptance criteria mapped

- Ticket scope: "Wire into ReplayManager._rotate_chunk() — check budget before writing chunk" ✓

---

## Step 5 — Create `tests/certification/test_artifact_budget.py`

**Files to change:** `tests/certification/test_artifact_budget.py` (new file)

**Scope:** All tests defined in the test plan. Pure unit tests — no simulation kernel, no `WorldCompiler`, no `ScenarioLabOrchestrator`.

### Test list (exact names from AC and test plan)

**AC-required (must exist and pass for Definition of Done):**

1. `test_registry_allows_within_budget` — 1 MB estimated vs 2 MB max → `allowed=True, action="allow"`
2. `test_registry_rejects_over_budget` — 3 MB vs 2 MB max, `fail_on_budget_violation=True` → `allowed=False, action="reject"`; also sub-case with `fail_on_budget_violation=False` → `allowed=True, action="warn"`
3. `test_registry_warns_on_soft_limit` — 1.5 MB vs `soft_limit_mb=1.0`, `max_size_mb=2.0` → `allowed=True, action="warn"`
4. `test_recorder_consults_budget_before_write` — mock registry injected via constructor; assert `check()` called once with `("certification_result", <int>)`; assert `proofs_bundle.json` written (warn path); assert `ArtifactBudgetViolationError` raised and file NOT written (reject path)

**Recommended (regression-prone paths):**

5. `test_registry_unknown_type_returns_allow` — unregistered type → `BudgetCheckResult(allowed=True, action="allow", reason=None)`
6. `test_registry_get_returns_none_for_unknown` — `registry.get("unknown")` returns `None`
7. `test_registry_overwrite_replaces_budget` — register same type twice → second budget wins
8. `test_singleton_reset_between_tests` — register budget, call `reset_default_registry()`, `get_default_registry().get(type)` returns default (not custom) budget
9. `test_default_budgets_registered` — `get_default_registry()` has non-None entries for `certification_result`, `replay_chunk`, `behavior_report`

### Fixture requirement

```python
@pytest.fixture(autouse=True)
def reset_registry():
    reset_default_registry()
    yield
    reset_default_registry()
```

This must be present to guard against test-order pollution.

### Import isolation guard

```python
from src.certification.artifact_budget import (
    ArtifactBudget,
    ArtifactBudgetRegistry,
    ArtifactBudgetViolationError,
    BudgetCheckResult,
    get_default_registry,
    reset_default_registry,
)
# If lab guardrails BudgetCheckResult must be imported, alias it:
# from src.lab.guardrails import BudgetCheckResult as LabBudgetCheckResult
```

### Anti-drift guards embedded in tests

- Size estimation in any test using `CertificationResult` must use `len(json.dumps(result.to_artifact_dict()).encode())` — add comment `# INFRA-189: must use to_artifact_dict(), not to_json() or asdict()`
- `test_recorder_consults_budget_before_write` must assert `proofs_bundle.json` EXISTS after warn path and DOES NOT EXIST after reject path (INFRA-060 guard).
- No `Kernel`, `WorldCompiler`, or `ScenarioLabOrchestrator` imports allowed.

### Acceptance criteria mapped

- AC: "Tests: test_registry_rejects_over_budget, test_registry_allows_within_budget, test_recorder_consults_budget_before_write" ✓
- Regression: existing test suites remain unaffected ✓

---

## Step 6 — Run scoped test suite and verify regressions

**Files to change:** None (verification step)

**Commands (in order):**

```bash
# 1. New tests (primary):
pytest tests/certification/test_artifact_budget.py -v

# 2. Regression: full certification suite
pytest tests/certification/ -v

# 3. Regression: lab guardrails (BudgetCheckResult name collision check)
pytest tests/unit/lab/test_lab_budget_guardrails.py -v
```

**Pass criteria:** All three commands exit 0. No existing test may be broken. No skip of previously passing tests.

**Scope guards (Step 6):**

- Do NOT run `pytest tests/` (full suite) — violates Testing Rule.
- If any regression fails: fix the violation before proceeding to Step 7.

---

## Step 7 — Add INFRA-193 parity ledger entry

**Files to change:** `docs/parity_ledger/infrastructure.yaml`

**Scope:** Append one new entry at the bottom of the file.

### Entry to add

```yaml
- id: INFRA-193
  text: >-
    `ArtifactBudgetRegistry.check()` enforces per-artifact-type write-time size
    budgets. Unknown types return action="allow". Violations with
    fail_on_budget_violation=True return action="reject" (allowed=False). Violations
    with fail_on_budget_violation=False return action="warn" (allowed=True). Soft
    limit (soft_limit_mb) triggers action="warn" before hard limit. All violation
    events are logged (INFRA-060 compliance). Default registry pre-registers budgets
    for certification_result (2 MB), replay_chunk (10 MB), behavior_report (5 MB),
    proof_index (1 MB).
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >-
    Implemented in src/certification/artifact_budget.py; wired in
    src/certification/recorder.py and src/engine/replay_manager.py; verified by
    tests/certification/test_artifact_budget.py.
  proof_type: null
  test_path: tests/certification/test_artifact_budget.py
  divergence_note: null
  support_boundary: null
```

**Scope guards (Step 7):**

- Do NOT modify any existing INFRA-* entries.
- Append at the bottom of the file only.
- After adding the entry, run `make knowledge-index-update` (docs were modified).

---

## Full Ordered Step List

| # | Step | Files Changed | Depends On |
|---|---|---|---|
| 1 | Create `src/certification/artifact_budget.py` — core types and registry class | `src/certification/artifact_budget.py` (new) | — |
| 2 | Add default budgets and module-level singleton to `artifact_budget.py` | `src/certification/artifact_budget.py` | Step 1 |
| 3 | Wire budget check into `CertificationRecorder.record()` | `src/certification/recorder.py` | Steps 1-2 |
| 4 | Wire budget check into `ReplayManager._rotate_chunk()` | `src/engine/replay_manager.py` | Steps 1-2 |
| 5 | Create `tests/certification/test_artifact_budget.py` | `tests/certification/test_artifact_budget.py` (new) | Steps 1-4 |
| 6 | Run scoped test suite — no files changed, verify no regressions | — (verification) | Step 5 |
| 7 | Add INFRA-193 to `docs/parity_ledger/infrastructure.yaml` + `make knowledge-index-update` | `docs/parity_ledger/infrastructure.yaml` | Steps 1-4 |

Steps 3 and 4 are independent and can be implemented in either order.
Step 7 is independent of Steps 5-6 and can be done concurrently with the test pass.

---

## Scope Guards — Global

The following are explicitly NOT touched by this ticket:

- Dynamic compaction of oversized artifacts
- `docs/engine/contracts/observability_artifact_contract.md` (read-only reference)
- `proofs_bundle.json` key format or write path structure
- `ReplaySink`, `ReplayBuffer`, chunk naming or manifest format (INFRA-155, INFRA-156)
- `src/lab/guardrails.py` or any lab-domain code
- `src/config/optimization_profiles.py` (budget override via config is future scope)
- `release_report.md` write path in `recorder.py`
- Any file in `src/engine/` except `replay_manager.py`
- UI or dashboard (TCK-20260614-RESOURCE-DASHBOARD)
- Retention enforcement

---

## Acceptance Criteria → Step Mapping

| Acceptance Criterion | Covered By |
|---|---|
| `ArtifactBudgetRegistry` class exists and can register, query, and check budgets | Step 1 |
| `BudgetCheckResult` carries `allowed`, `action`, and `reason` | Step 1 |
| Default budgets registered for `certification_result` (max 2 MB, no full state), `replay_chunk`, `behavior_report` | Step 2 |
| `CertificationRecorder.record()` calls `registry.check("certification_result", estimated_size)` before writing | Step 3 |
| Logs warning on `fail_on_budget_violation=False` | Step 3 |
| Raises on `fail_on_budget_violation=True` (via `ArtifactBudgetViolationError`) | Step 3 |
| Test: `test_registry_allows_within_budget` | Steps 1-2, 5 |
| Test: `test_registry_rejects_over_budget` | Steps 1-2, 5 |
| Test: `test_recorder_consults_budget_before_write` | Steps 1-3, 5 |
| Parity ledger updated (INFRA-193) | Step 7 |

---

## Deviations from Plan

1. **`_rotate_chunk()` event serialization** (Step 4): Plan specified `e.__dict__` for estimation. `TraceEvent` is a frozen slotted dataclass (`slots=True`) — `__dict__` raises `AttributeError`. Fixed by using `dataclasses.asdict()` via an `is_dataclass()` guard, which is consistent with how Python frozen slotted dataclasses must be introspected. The bare `__dict__` path is retained as fallback for non-dataclass objects. This deviation does not affect the contract (estimation accuracy is unchanged) and is required for correctness.

2. **`compression` default on `ArtifactBudget`**: The ticket prompt specified `compression: str = "none"` as the default, but the plan's default budget table used `compression="optional"` for all registered budgets. Both are valid per spec; `compression="none"` is the dataclass field default and the registered defaults explicitly pass `compression="optional"`.

3. **`import dataclasses` placement**: Added as a top-level import (`import dataclasses`) in `replay_manager.py` rather than inline inside `_rotate_chunk()` to avoid per-call import overhead, keeping it consistent with the module-level import style of the file.
