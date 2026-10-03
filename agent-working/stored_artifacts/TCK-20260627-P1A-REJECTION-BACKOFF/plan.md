# Plan — TCK-20260627-P1A-REJECTION-BACKOFF

## Ordered Steps

### Step 1 — Add module-level constant to intelligence.py
**File**: `src/systems/strategic_systems/intelligence.py`
**Change**: Add `_MAX_CONSECUTIVE_REJECTIONS = 20` near the top of the file, after imports.
**Scope guard**: Do NOT change existing class/function signatures.
**AC mapped**: AC-1 (ProjectState carries backoff field — already exists as `failure_count`)

### Step 2 — Wire up failure_count increment/reset in evaluate_strategic_intent
**File**: `src/systems/strategic_systems/intelligence.py`
**Change**: In `evaluate_strategic_intent`, inside the "Project Abandonment (PH6)" block
(currently L1142-1158), before the existing `if project.failure_count >= 3:` check:

```python
# Rejection backoff: track consecutive intent failures against this project
_intent_results = entity.identity.latest_intent_results
if _intent_results:
    _any_accepted = any(r.accepted for r in _intent_results)
    _all_failed   = not _any_accepted
    if _all_failed:
        project = replace(project, failure_count=project.failure_count + 1)
    elif project.failure_count > 0:
        project = replace(project, failure_count=0)
```

**Scope guard**: Only read `latest_intent_results`; do not alter any other component.
**AC mapped**: AC-1, AC-2

### Step 3 — Change abandonment threshold and persist sub-threshold increments
**File**: `src/systems/strategic_systems/intelligence.py`
**Change**:
1. Change `if project.failure_count >= 3:` → `if project.failure_count >= _MAX_CONSECUTIVE_REJECTIONS:`
2. After the abandonment early-return block (around L1158), add a sub-threshold persistence path:
   ```python
   # Persist failure_count update even when below threshold
   elif project is not strat.projects.get(strat.current_project_id):
       return StrategicUpdate(
           projects_add_or_update=[project],
           leads_add_or_update=memory_upd.leads_add_or_update,
           leads_remove=memory_upd.leads_remove
       )
   ```
   This ensures the incremented count is saved even when abandonment is not yet triggered.
**Scope guard**: Do NOT change the boredom penalty or the abandoned StrategicUpdate content.
**AC mapped**: AC-2 (mechanism correctly abandons/suppresses), AC-3 (< 50K rejections)

### Step 4 — Write new test file
**File**: `tests/unit/strategic/test_rejection_backoff.py`
**Change**: New file with 4 unit tests (see test_plan.md).
**Scope guard**: No changes to existing test files.
**AC mapped**: AC-4 (unit test), AC-5 (rejection count threshold)

### Step 5 — Update parity ledger
**File**: `docs/parity_ledger/strategic_cognition.yaml`
**Change**: Add STRAT-234 entry for rejection-based project abandonment.
**AC mapped**: AC-4 (parity ledger updated)

## Files Per Step

| Step | File(s) |
|------|---------|
| 1 | `src/systems/strategic_systems/intelligence.py` |
| 2 | `src/systems/strategic_systems/intelligence.py` |
| 3 | `src/systems/strategic_systems/intelligence.py` |
| 4 | `tests/unit/strategic/test_rejection_backoff.py` (new) |
| 5 | `docs/parity_ledger/strategic_cognition.yaml` |

## Dependency Map

Steps 1 → 2 → 3 (sequential, all in same file)
Step 4 depends on steps 1-3 (tests validate the wired-up logic)
Step 5 is independent

## Explicit Scope Guards

- Do NOT add a new field to `ProjectState` — `failure_count` already exists and serves this purpose
- Do NOT modify `src/core/strategic.py` (field is already there)
- Do NOT modify `src/core/state.py`, `src/engine/apply.py`, or `src/engine/interaction.py`
- Do NOT modify `src/world/providers/requirements.py` (root cause of failures is out of scope)
- Do NOT touch the existing abandonment boredom penalty logic

## AC-to-Step Mapping

| AC | Step(s) |
|----|---------|
| ProjectState carries backoff field | 1 (constant), field already exists |
| Mechanism correctly abandons/suppresses stale projects | 2, 3 |
| 1000-tick rejection count < 50,000 | 3 (threshold=20, runtime improvement) |
| Parity ledger updated | 5 |
| New test: rejection count < threshold | 4 |

## Deviations
(none yet)
