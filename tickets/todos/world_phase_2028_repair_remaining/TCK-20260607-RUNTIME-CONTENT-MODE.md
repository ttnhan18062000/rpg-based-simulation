# TCK-20260607-RUNTIME-CONTENT-MODE

## Title
Replace migration_mode bool with RuntimeContentMode enum; add adapter heuristic report

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`seed_phase1_content()` in `src/worldassembly/resolver.py` (line 642) is called with no
arguments, accepting the default `migration_mode=True`. This default silently keeps the
simulation in migration mode without any calling code explicitly opting in.

Additionally, there is no `AdapterProjectionResult` or heuristic report tracking which
entities were projected to legacy vs resolved natively. Silent projections make it
impossible to audit how many entities actually resolved correctly.

## Scope

### Fix 1 — Replace `migration_mode: bool` with `RuntimeContentMode` enum

Create:
```python
# src/worldassembly/modes.py
from enum import Enum

class RuntimeContentMode(Enum):
    MIGRATION = "migration"    # legacy projection allowed; adapter heuristics active
    V2 = "v2"                  # fully resolved; no legacy fallback
```

Update `seed_phase1_content()`:
```python
def seed_phase1_content(
    ...,
    mode: RuntimeContentMode = RuntimeContentMode.MIGRATION,
) -> ...:
```

Update the bare call at line 642:
```python
seed_phase1_content(..., mode=RuntimeContentMode.MIGRATION)
```

Making the mode explicit means `MIGRATION` remains the current default but callers must
write it out — no silent implicit state.

### Fix 2 — `AdapterProjectionResult`

Create a typed result record:
```python
@dataclass(frozen=True)
class AdapterProjectionResult:
    total_entities: int
    native_resolved: int
    legacy_projected: int
    unresolved: int
    heuristic_details: Dict[str, str]  # entity_id → projection reason
```

`seed_phase1_content()` returns `AdapterProjectionResult` instead of `None` (or wraps
existing return with this record).

### Fix 3 — Tests

Add to `tests/unit/worldassembly/test_resolver.py`:
```python
- test_seed_with_migration_mode_returns_projection_result
- test_seed_with_v2_mode_raises_if_unresolved_entities_exist
- test_runtime_content_mode_enum_has_migration_and_v2
```

## Out of Scope
- Do not change how legacy projection logic works — only change how the mode is expressed
- Do not add new projection heuristics — just capture what already happens
- Do not change `ContentFamilyMatrixEntry` states

## Acceptance Criteria
- [ ] `RuntimeContentMode` enum exists in `src/worldassembly/modes.py`
- [ ] `seed_phase1_content()` parameter is `mode: RuntimeContentMode` not `migration_mode: bool`
- [ ] Bare call at line 642 is updated to pass explicit mode
- [ ] `AdapterProjectionResult` dataclass exists and is returned by `seed_phase1_content()`
- [ ] Tests cover enum values and projection result structure
- [ ] All existing tests pass

## Related Tickets
- TCK-20260607-RESOLVER-BOUNDARY (same resolver.py file)

## Related Docs
- `world_phase_20_28_repair_remaining.md` R5.1, R5.2, R5.3

## Related Code Areas
- `src/worldassembly/resolver.py:642` (bare call)
- `src/worldassembly/modes.py` (new)
- `tests/unit/worldassembly/test_resolver.py`

## Assumptions / Open Questions
- Does `seed_phase1_content()` currently return anything? If so, what? — must read the actual return type.
- Are there other callers of `seed_phase1_content()` besides line 642?

## Implementation Notes
Investigation phase must read `seed_phase1_content()` fully before designing `AdapterProjectionResult`.

## Test Summary
```
pytest tests/unit/worldassembly/test_resolver.py -q
```

## Files Changed
- `src/worldassembly/resolver.py`
- `src/worldassembly/modes.py` (new)
- `tests/unit/worldassembly/test_resolver.py`

## Completion Summary
(to be filled)
