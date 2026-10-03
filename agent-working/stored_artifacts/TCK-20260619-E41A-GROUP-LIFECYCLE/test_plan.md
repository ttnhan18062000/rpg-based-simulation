---
ticket_id: TCK-20260619-E41A-GROUP-LIFECYCLE
phase: test_plan
date: 2026-06-21
---

# Test Plan · TCK-20260619-E41A-GROUP-LIFECYCLE

## Regression Surface (existing tests that must pass)

These tests exercise `GroupRecord` directly or consume it via `ApplyPath`/`GroupService`. They must all pass without modification after the six lifecycle fields are added.

| File | Tests | Coverage at risk |
|---|---|---|
| `tests/unit/social/test_groups.py` | `test_group_formation`, `test_group_dissolution`, `test_group_cohesion` | `GroupRecord` construction (SOC-166, 167, 173); `ApplyPath.apply_generation` with `groups_add_or_update`; `groups_remove`; `GroupService.calculate_cohesion` |
| `tests/unit/social/test_party_agency.py` | all | Party agency behavior; `GroupRecord` field access |
| `tests/unit/social/test_party_coordination.py` | `test_party_coordination_leadership_influence`, `test_party_coordination_no_contract` | `PartyCoordinationSystem.apply_leadership_influence`; `GroupRecord` leader/member resolution |
| `tests/unit/social/test_social_party_regression.py` | all | Regression guard for social/party pipeline |
| `tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py` | all | `GroupEvaluator` trust decay on leader loss; reads `leader_id`, `member_ids` |
| `tests/unit/domains/cooperation/test_phase7_party_objective_alignment.py` | all | Objective alignment; reads `GroupRecord.shared_target_id`, `contract_id` |

---

## New Tests Required (per AC)

All new tests go in `tests/unit/social/test_group_lifecycle_fields.py`.

### Test 1 — Construction with all lifecycle defaults

```
def test_group_lifecycle_default_construction():
```
Constructs `GroupRecord(id=1, leader_id=10, member_ids={10,11}, anchor=(0.0,0.0))`.
Asserts:
- `group.formation_tick == 0`
- `group.escort_target_id is None`
- `group.grievance_log == ()`
- `group.reward_pool == 0`
- `group.last_leadership_check_tick == 0`
- `group.dissolution_tick is None`

### Test 2 — Construction with explicit lifecycle values (primary AC)

```
def test_group_lifecycle_explicit_construction():
```
Constructs `GroupRecord(id=1, leader_id=10, member_ids={10,11}, anchor=(0.0,0.0), formation_tick=10, escort_target_id=5, grievance_log=("ABANDON:9",), reward_pool=50, last_leadership_check_tick=8, dissolution_tick=None)`.
Asserts each field holds the value provided. Verifies no `TypeError` is raised.

### Test 3 — `to_canonical_dict()` includes all six new fields

```
def test_group_lifecycle_canonical_dict_completeness():
```
Constructs a `GroupRecord` with all six fields set to non-default values. Calls `to_canonical_dict()`. Asserts:
- `"formation_tick"` in result and `result["formation_tick"] == 10`
- `"escort_target_id"` in result and `result["escort_target_id"] == 5`
- `"grievance_log"` in result and `result["grievance_log"] == ["ABANDON:9"]` (list form)
- `"reward_pool"` in result and `result["reward_pool"] == 50`
- `"last_leadership_check_tick"` in result and `result["last_leadership_check_tick"] == 8`
- `"dissolution_tick"` in result and `result["dissolution_tick"] is None`

### Test 4 — `to_canonical_dict()` with defaults still complete

```
def test_group_lifecycle_canonical_dict_with_defaults():
```
Constructs a minimal `GroupRecord` (no lifecycle kwargs). Calls `to_canonical_dict()`. Asserts all six new keys are present with their default values (`0`, `None`, `[]`, `0`, `0`, `None`).

### Test 5 — `to_canonical_dict()` caching is safe with new fields

```
def test_group_lifecycle_canonical_dict_cache_consistency():
```
Calls `to_canonical_dict()` twice on the same instance. Asserts both return values are identical objects (the second call returns the cached result). Asserts the cached result contains all six new keys.

### Test 6 — `grievance_log` is a tuple (immutability guard)

```
def test_group_lifecycle_grievance_log_is_tuple():
```
Constructs `GroupRecord(..., grievance_log=("ABANDON:5", "BETRAY:10"))`.
Asserts `isinstance(group.grievance_log, tuple)` is `True`.
Asserts `len(group.grievance_log) == 2`.
Confirms `group.grievance_log[0] == "ABANDON:5"`.

### Test 7 — Lifecycle fields survive `groups_add_or_update` apply path

```
def test_group_lifecycle_fields_survive_apply_path():
```
Constructs a `GroupRecord` with `formation_tick=10`, `reward_pool=100`, `dissolution_tick=None`.
Wraps in `StateUpdate(groups_add_or_update=[group])`. Applies via `ApplyPath.apply_generation(state, update)`.
Asserts `new_state.groups[group.id].formation_tick == 10`.
Asserts `new_state.groups[group.id].reward_pool == 100`.
Asserts `new_state.groups[group.id].dissolution_tick is None`.

### Test 8 — `dataclasses.replace` appends to `grievance_log` correctly

```
def test_group_lifecycle_grievance_log_append_via_replace():
```
Constructs a `GroupRecord` with `grievance_log=()`.
Uses `dataclasses.replace(group, grievance_log=group.grievance_log + ("ABANDON:5",))` to produce a new group record.
Asserts original `group.grievance_log == ()` (immutability preserved).
Asserts new record `grievance_log == ("ABANDON:5",)`.

### Test 9 — Existing constructions unaffected (regression)

```
def test_group_lifecycle_backward_compatible_construction():
```
Constructs `GroupRecord(id=100, leader_id=1, member_ids={1}, anchor=(0,0))` (the exact pattern used in `test_group_dissolution`).
Asserts it succeeds without `TypeError`.
Asserts `to_canonical_dict()` runs without error and returns a dict with key `"id"`.

---

## Scoped Pytest Commands

Run these in order; all must pass before implementation is considered complete.

```bash
# 1. Regression: existing group/party/cooperation tests
pytest tests/unit/social/test_groups.py tests/unit/social/test_party_agency.py tests/unit/social/test_party_coordination.py tests/unit/social/test_social_party_regression.py tests/unit/domains/cooperation/ -x -v

# 2. New lifecycle field tests
pytest tests/unit/social/test_group_lifecycle_fields.py -x -v

# 3. Broader social domain to catch any indirect breakage
pytest tests/unit/social/ -x -v -m "not slow"

# 4. Quest/transaction group tests (also import GroupRecord transitively)
pytest tests/unit/quest/test_transaction_groups.py tests/unit/resource/test_transaction_grouping.py -x -v
```

---

## Anti-Drift Test Guards

### Guard 1 — `to_canonical_dict()` completeness enforcement

Add a test that explicitly iterates over the **expected full key set** and asserts each is present:

```python
EXPECTED_KEYS = {
    "id", "leader_id", "member_ids", "anchor", "shared_target_id",
    "contract_id", "cohesion_radius", "last_updated_tick", "roles", "aptitudes",
    # E41A new keys:
    "formation_tick", "escort_target_id", "grievance_log",
    "reward_pool", "last_leadership_check_tick", "dissolution_tick",
}

def test_group_canonical_dict_has_no_missing_keys():
    group = GroupRecord(id=1, leader_id=1, member_ids={1}, anchor=(0.0,0.0))
    result = group.to_canonical_dict()
    assert EXPECTED_KEYS == set(result.keys()), \
        f"Missing keys: {EXPECTED_KEYS - set(result.keys())}"
```

This test fails immediately if a future refactor accidentally drops a key or adds one without updating the guard.

### Guard 2 — `grievance_log` type guard

The type-mismatch risk (list vs tuple) is covered by Test 6 above. Additionally, the canonical dict test (Test 3) verifies that `grievance_log` is emitted as a `list` in the dict output (JSON-serializable) while the field itself remains a `tuple`. Both invariants must hold simultaneously.

### Guard 3 — No mutation of `_canonical_cache` outside `to_canonical_dict()`

The `_canonical_cache` is set via `object.__setattr__` inside `to_canonical_dict()` only. No other code path should call `object.__setattr__` on a `GroupRecord`. This is enforced by `frozen=True` — any attempt raises `FrozenInstanceError`. The existing pattern is correct and requires no additional guard here; the test that calls `to_canonical_dict()` twice (Test 5) confirms cache consistency.

### Guard 4 — E41B pre-conditions

Before E41B implementation begins, run:

```bash
pytest tests/unit/social/test_group_lifecycle_fields.py::test_group_lifecycle_explicit_construction -x -v
```

This single test confirms that `formation_tick` and `last_leadership_check_tick` are accessible, which are the two fields E41B will read on its first tick.
