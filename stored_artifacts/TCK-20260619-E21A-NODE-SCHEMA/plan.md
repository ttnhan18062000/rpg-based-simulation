---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E21A-NODE-SCHEMA
artifact_type: plan
tags: [resource-ecology, state-schema, event-taxonomy, phase-2]
---

# Plan — TCK-20260619-E21A-NODE-SCHEMA
## Epic 2.1A · ResourceNodeState Schema Extension + RESOURCE_RECOVERED Event

## Ordered Steps

### Step 1: Add `regen_rate_per_tick` field to `ResourceNodeState`
**File:** `src/core/state.py`
**Location:** After `cooldown_remaining: int = 0` (L819), before `_canonical_cache` field.

Change:
```python
    cooldown_remaining: int = 0
    # INSERT:
    regen_rate_per_tick: int = 0  # charges regenerated per ecology tick (0 = no regen)
    _canonical_cache: ...
```

AC mapped: AC1 (constructor), AC3 (default=0 backward compat)

### Step 2: Add `regen_rate_per_tick` to `to_canonical_dict()`
**File:** `src/core/state.py`
**Location:** In `to_canonical_dict()` `res` dict, after `"cooldown_remaining"` entry (L838), before `object.__setattr__`.

Change:
```python
    res = {
        ...
        "cooldown_remaining": self.cooldown_remaining,
        # INSERT:
        "regen_rate_per_tick": self.regen_rate_per_tick,
    }
    object.__setattr__(self, "_canonical_cache", res)
```

AC mapped: AC2 (canonical_dict includes field)

### Step 3: Add `RESOURCE_RECOVERED` to `WorldEventCategory`
**File:** `src/domains/world_emergence/schema.py`
**Location:** After `RESOURCE_DEPLETED = "RESOURCE_DEPLETED"` (L16).

Change:
```python
    RESOURCE_DEPLETED = "RESOURCE_DEPLETED"
    # INSERT:
    RESOURCE_RECOVERED = "RESOURCE_RECOVERED"
```

AC mapped: AC4 (enum accessible and equals string)

### Step 4: Add new tests to `tests/unit/resource/test_resource_contract.py`
Test all 4 ACs in a new test class or standalone test functions at the end of the file.

### Step 5: Run scoped test suite
```bash
pytest tests/unit/resource/ tests/unit/core/test_hardening_e5.py tests/unit/core/test_engine_integrity.py tests/unit/core/test_interaction_recovery.py tests/unit/strategic/ tests/unit/optimization/ -x -v -q
```

## Files Per Step

| Step | File |
|---|---|
| 1 | `src/core/state.py` |
| 2 | `src/core/state.py` |
| 3 | `src/domains/world_emergence/schema.py` |
| 4 | `tests/unit/resource/test_resource_contract.py` |
| 5 | (run only) |

## Scope Guards (what NOT to touch)

- Do NOT modify `src/content/schema.py` (ResourceDefinition is catalog schema, not runtime state)
- Do NOT add regen logic anywhere (E21B scope)
- Do NOT emit events or add event consumers (E21B/E21D scope)
- Do NOT change `WorldEvent` dataclass or any consumer of `WorldEventCategory`
- Do NOT change `to_dict()` on EntityState or any other state class

## Dependency Map

Step 1 → Step 2 (must add field before adding to dict)
Step 1, 2, 3 → Step 4 (tests validate all three changes)
Step 4 → Step 5 (run after tests are written)

## Acceptance Criteria Mapped to Steps

| AC | Step |
|---|---|
| AC1: Constructor accepts regen_rate_per_tick | Step 1 |
| AC2: to_canonical_dict() includes regen_rate_per_tick | Step 2 |
| AC3: Default=0 preserves existing callers | Step 1 |
| AC4: WorldEventCategory.RESOURCE_RECOVERED accessible | Step 3 |

## Deviations

_None._
