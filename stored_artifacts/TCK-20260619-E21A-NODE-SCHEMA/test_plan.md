---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E21A-NODE-SCHEMA
artifact_type: test_plan
tags: [resource-ecology, state-schema, event-taxonomy, phase-2]
---

# Test Plan — TCK-20260619-E21A-NODE-SCHEMA

## Regression Surface (existing tests that must pass)

All existing callers of `ResourceNodeState(...)` use keyword args with defaults —
no breakage expected. Key regression suites:

| Suite | Path | Risk |
|---|---|---|
| Resource contract | `tests/unit/resource/test_resource_contract.py` | Constructs ResourceNodeState |
| Resource conservation | `tests/unit/resource/test_resource_conservation_regression.py` | Constructs ResourceNodeState |
| Harvest channeling | `tests/unit/resource/test_harvest_channeling.py` | Constructs ResourceNodeState |
| Engine integrity | `tests/unit/core/test_engine_integrity.py` | Constructs ResourceNodeState |
| Hardening E5 | `tests/unit/core/test_hardening_e5.py` | Constructs ResourceNodeState |
| Strategic lifecycle | `tests/unit/strategic/test_strategic_lifecycle_v2.py` | Constructs ResourceNodeState |
| World index service | `tests/unit/optimization/test_world_index_service.py` | Constructs ResourceNodeState |

## New Tests Required (per AC)

### AC1: Constructor accepts regen_rate_per_tick
```python
from src.core.state import ResourceNodeState
n = ResourceNodeState(
    id=1, kind='IRON', position=(0,0), yields_item='iron_ore',
    remaining_charges=3, max_charges=5, required_ticks=10,
    regen_rate_per_tick=2
)
assert n.regen_rate_per_tick == 2
```

### AC2: to_canonical_dict() includes regen_rate_per_tick
```python
d = n.to_canonical_dict()
assert 'regen_rate_per_tick' in d
assert d['regen_rate_per_tick'] == 2
```

### AC3: Default is 0 (backward compat)
```python
n2 = ResourceNodeState(
    id=2, kind='WOOD', position=(1,1), yields_item='wood',
    remaining_charges=5, max_charges=5, required_ticks=5
)
assert n2.regen_rate_per_tick == 0
d2 = n2.to_canonical_dict()
assert d2['regen_rate_per_tick'] == 0
```

### AC4: WorldEventCategory.RESOURCE_RECOVERED accessible
```python
from src.domains.world_emergence.schema import WorldEventCategory
assert WorldEventCategory.RESOURCE_RECOVERED == 'RESOURCE_RECOVERED'
```

## Scoped Pytest Commands

```bash
# Primary: resource test directory
pytest tests/unit/resource/ -x -v -q

# Core state regressions
pytest tests/unit/core/test_hardening_e5.py tests/unit/core/test_engine_integrity.py tests/unit/core/test_interaction_recovery.py -x -v -q

# Strategic callers
pytest tests/unit/strategic/ -x -v -q

# Optimization callers
pytest tests/unit/optimization/ -x -v -q
```

## Anti-Drift Test Guards

- All new tests must construct `ResourceNodeState` with keyword args only.
- No test should import or touch regen logic (E21B) — schema-only assertions.
- Do not add tests for `WorldEvent` or event emission — out of scope.
- The `to_canonical_dict()` test must assert the key exists AND has the correct value.
