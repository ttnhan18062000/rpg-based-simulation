---
ticket_id: TCK-20260619-E41A-GROUP-LIFECYCLE
phase: plan
date: 2026-06-21
---

# Plan · TCK-20260619-E41A-GROUP-LIFECYCLE

## Overview

Add six lifecycle fields to `GroupRecord` in `src/core/state.py`, update `to_canonical_dict()` to emit all six, create a new test file with 9 tests plus one anti-drift key-completeness guard, run regression and new tests, then add a SOC-227 parity ledger entry.

All work is additive. No callers, no `StateUpdate`, no `ApplyPath`, no cooperation domain changes are needed.

---

## Scope Guards (What NOT to Touch)

- Do not modify `StateUpdate`, `ApplyPath`, or any cooperation domain files.
- Do not modify any existing test file — only create `tests/unit/social/test_group_lifecycle_fields.py`.
- Do not add a `"lifecycle"` sub-dict to `to_canonical_dict()` — keep all keys flat at the top level, matching the existing `last_updated_tick` / `cohesion_radius` pattern.
- Do not use `List` for `grievance_log` — it must remain `Tuple[str, ...]` in the class body (frozen dataclass constraint).
- Do not modify `GroupEvaluator` or any strategy/cognition domain file.
- Do not modify any existing parity ledger entries — only append a new SOC-227 entry.
- Do not sort `grievance_log` entries when emitting to canonical dict — preserve insertion order via `list(self.grievance_log)`.

---

## Dependency Map

```
Step 1 (read/confirm lines)
  └─> Step 2 (add fields to class body)
        └─> Step 3 (update to_canonical_dict)
              ├─> Step 4 (write new tests)
              ├─> Step 5 (run regression tests)  ← depends on Step 2+3
              └─> Step 6 (run new tests)          ← depends on Steps 4+2+3
                    └─> Step 7 (parity ledger)    ← depends on Step 6 green
```

Steps 4 and 5 can begin once Steps 2+3 are complete. Step 7 is last — only write the parity entry after the new tests pass.

---

## Steps

### Step 1 — Confirm exact line numbers in `src/core/state.py`

**Goal:** Establish precise insertion points before editing. Prevents off-by-one errors.

**Action:** Read `src/core/state.py` lines 509–551.

**Verify:**
- `@dataclass(frozen=True, slots=True)` decorating `GroupRecord` is at L509.
- `_canonical_cache` field is at L526 (last field before the method).
- `def to_canonical_dict(self)` opens at L528.
- The closing `object.__setattr__` + `return res` lines are at L549–L550.

**Files read:** `src/core/state.py:L509-L550`

**Acceptance criteria mapped:** Precondition for all AC — wrong insertion point would break construction or serialization.

---

### Step 2 — Add six lifecycle fields to `GroupRecord` class body

**Goal:** Insert all six new fields between `end_apt: float = 1.0` (currently L525) and `_canonical_cache` (currently L526).

**Action:** Edit `src/core/state.py`. Insert the following block immediately before the `_canonical_cache` line:

```python
    formation_tick: int = 0
    escort_target_id: Optional[int] = None
    grievance_log: Tuple[str, ...] = ()
    reward_pool: int = 0
    last_leadership_check_tick: int = 0
    dissolution_tick: Optional[int] = None
```

**Type imports check:** `Tuple` is already imported in `src/core/state.py` (used elsewhere). Confirm before editing; add `Tuple` to the import line if absent.

**Invariants:**
- All six defaults are immutable literals — no `field(default_factory=...)` needed.
- `Tuple[str, ...]` with default `()` is valid for `frozen=True` + `slots=True`.
- Field order must match the order that `to_canonical_dict()` will emit them (Step 3 must mirror this order).

**Files changed:** `src/core/state.py` (field insertion only)

**Acceptance criteria mapped:**
- AC: "`GroupRecord(formation_tick=10, escort_target_id=5, ...)` constructs without error" — satisfied by this step.

---

### Step 3 — Update `to_canonical_dict()` to include all six new fields

**Goal:** Emit all six lifecycle fields in the canonical dict, in declaration order, flat at the top level. `grievance_log` must be emitted as `list(self.grievance_log)` for JSON-serializability.

**Action:** Edit the `res = { ... }` dict in `to_canonical_dict()` (currently L531–L548) to append the six new entries after the `"aptitudes"` sub-dict block:

```python
            "formation_tick": self.formation_tick,
            "escort_target_id": self.escort_target_id,
            "grievance_log": list(self.grievance_log),
            "reward_pool": self.reward_pool,
            "last_leadership_check_tick": self.last_leadership_check_tick,
            "dissolution_tick": self.dissolution_tick,
```

**Invariants:**
- The `_canonical_cache` pattern is unchanged — still set via `object.__setattr__` after `res` is built.
- All new keys are flat (no nesting under `"lifecycle"`).
- `grievance_log` field is `Tuple` internally; canonical dict key is `list` — both must hold simultaneously (tested by Tests 3 and 6).
- Key order follows field declaration order from Step 2 — deterministic for replay equality.

**Files changed:** `src/core/state.py` (dict body of `to_canonical_dict` only)

**Acceptance criteria mapped:**
- AC: "`to_canonical_dict()` includes all new fields" — satisfied by this step.

---

### Step 4 — Create `tests/unit/social/test_group_lifecycle_fields.py`

**Goal:** Write all 9 required tests plus the anti-drift key-completeness guard (10 test functions total) in a new file.

**Action:** Create `tests/unit/social/test_group_lifecycle_fields.py` with the following test functions in order:

| # | Function | What it guards |
|---|---|---|
| 1 | `test_group_lifecycle_default_construction` | All six fields have correct default values |
| 2 | `test_group_lifecycle_explicit_construction` | Explicit non-default values accepted without TypeError (primary AC) |
| 3 | `test_group_lifecycle_canonical_dict_completeness` | All six keys present in canonical dict with non-default values |
| 4 | `test_group_lifecycle_canonical_dict_with_defaults` | All six keys present even when defaults used |
| 5 | `test_group_lifecycle_canonical_dict_cache_consistency` | Second `to_canonical_dict()` call returns same cached object |
| 6 | `test_group_lifecycle_grievance_log_is_tuple` | `grievance_log` is `tuple` on the instance (not list) |
| 7 | `test_group_lifecycle_fields_survive_apply_path` | `formation_tick`, `reward_pool`, `dissolution_tick` survive `ApplyPath.apply_generation` round-trip |
| 8 | `test_group_lifecycle_grievance_log_append_via_replace` | `dataclasses.replace` append idiom preserves immutability of original |
| 9 | `test_group_lifecycle_backward_compatible_construction` | Minimal construction (no lifecycle kwargs) still works |
| Guard | `test_group_canonical_dict_has_no_missing_keys` | Full expected key set `EXPECTED_KEYS` equals `set(result.keys())` exactly |

**`EXPECTED_KEYS` constant** (defined at module level before tests):

```python
EXPECTED_KEYS = {
    "id", "leader_id", "member_ids", "anchor", "shared_target_id",
    "contract_id", "cohesion_radius", "last_updated_tick", "roles", "aptitudes",
    "formation_tick", "escort_target_id", "grievance_log",
    "reward_pool", "last_leadership_check_tick", "dissolution_tick",
}
```

**Grievance log string convention** (minimal format, used in test fixtures): `"<EVENT_TYPE>:<tick>"` e.g. `"ABANDON:9"`, `"BETRAY:10"`. Tests use this convention consistently to establish the pattern for E41B/D without enforcing it in production code yet.

**Imports required at top of file:**
```python
import dataclasses
from src.core.state import GroupRecord
from src.core.updates import StateUpdate
from src.engine.apply_path import ApplyPath
```

(Confirm exact import paths for `StateUpdate` and `ApplyPath` match repo conventions before writing — check `tests/unit/social/test_groups.py` for the pattern.)

**Files changed:** `tests/unit/social/test_group_lifecycle_fields.py` (new file, create only)

**Acceptance criteria mapped:** All three AC plus anti-drift coverage.

---

### Step 5 — Run regression tests (existing group/party/cooperation tests)

**Goal:** Confirm no existing test is broken by the field additions.

**Command:**

```bash
pytest tests/unit/social/test_groups.py \
       tests/unit/social/test_party_agency.py \
       tests/unit/social/test_party_coordination.py \
       tests/unit/social/test_social_party_regression.py \
       tests/unit/domains/cooperation/ \
       -x -v
```

**Expected result:** All tests pass. No `AttributeError`, no `TypeError` from existing `GroupRecord` constructions.

**If any test fails:** Diagnose before proceeding to Step 6. The most likely cause is a missing import (`Tuple`) or an indentation error in the field block inserted in Step 2.

**Files changed:** None (read-only validation step)

**Acceptance criteria mapped:** AC: "All existing GroupRecord tests pass."

---

### Step 6 — Run new lifecycle field tests

**Goal:** Confirm all 10 new test functions pass.

**Command:**

```bash
pytest tests/unit/social/test_group_lifecycle_fields.py -x -v
```

**Expected result:** 10 tests collected, 10 passed, 0 errors.

**If Test 7 (apply path) fails:** Check that `StateUpdate.groups_add_or_update` and `ApplyPath.apply_generation` import paths in the test file are correct for this repo. Do not modify the apply path implementation — only fix the import in the test.

**If the anti-drift guard fails:** The canonical dict is missing a key. Return to Step 3 and confirm all six new entries are present in the `res` dict.

**Files changed:** None (read-only validation step)

**Acceptance criteria mapped:** All three AC (construction, canonical dict completeness, regression pass).

---

### Step 7 — Add SOC-227 entry to `docs/parity_ledger/social_narrative.yaml`

**Goal:** Record the new lifecycle fields as a verified parity claim with a test path pointing to the new test file.

**Action:** Append the following entry to the bottom of `docs/parity_ledger/social_narrative.yaml` (after the SOC-226 block):

```yaml
- id: SOC-227
  text: >
    GroupRecord carries lifecycle fields (formation_tick, escort_target_id,
    grievance_log, reward_pool, last_leadership_check_tick, dissolution_tick)
    that survive across ticks and are serialized in to_canonical_dict().
  status: verified
  priority: P1
  v2_evidence: >
    src/core/state.py GroupRecord class body L526-L531 (six fields with immutable
    defaults); to_canonical_dict() emits all six keys flat at the top level;
    grievance_log emitted as list() for JSON serializability.
  test_path: tests/unit/social/test_group_lifecycle_fields.py
  divergence_note: ""
```

**Precondition:** Step 6 must be green before writing `status: verified`. Do not add a parity entry for a claim that has failing tests.

**Files changed:** `docs/parity_ledger/social_narrative.yaml` (append only)

**Acceptance criteria mapped:** Parity ledger consistency — ensures downstream E41B/C/D agents can locate the canonical evidence for these fields.

---

## Acceptance Criteria Traceability

| Acceptance Criterion | Satisfied by Step(s) |
|---|---|
| `GroupRecord(formation_tick=10, escort_target_id=5, ...)` constructs without error | Step 2, confirmed by Step 6 Test 2 |
| `to_canonical_dict()` includes all new fields | Step 3, confirmed by Step 6 Tests 3, 4, Guard |
| All existing GroupRecord tests pass | Step 5 |
| Parity ledger updated with SOC-227 | Step 7 |

---

## Deviations

_(None — plan matches investigation findings exactly.)_
