# Test Plan: TCK-20260619-E-PHASE-PERMISSIONS

## Regression Surface
- `tests/architecture/` — all existing architecture guard tests must continue to pass
- `tests/unit/engine/` — if any phase enumeration tests exist

## New Tests Required (per AC)

**File:** `tests/architecture/test_phase_domain_permissions.py`

| Test | AC coverage |
|---|---|
| `test_each_authoritative_phase_declares_read_domains` | RPG-INFRA-155: all 6 phases in PHASE_READ_DOMAINS |
| `test_each_authoritative_phase_declares_write_domains` | RPG-INFRA-156: all 6 phases in PHASE_WRITE_DOMAINS |
| `test_each_authoritative_phase_declares_emit_domains` | RPG-INFRA-157: all 6 phases in PHASE_EMIT_DOMAINS |
| `test_resolution_is_sole_entity_write_phase` | Architectural invariant: only RESOLUTION writes entity/world |
| `test_collection_phase_does_not_write_entity_state` | COLLECTION produces proposals only, never entity state |
| `test_persistence_is_non_authoritative` | PERSISTENCE must not write entity or world domains |

## Scoped Pytest Commands

```bash
pytest tests/architecture/test_phase_domain_permissions.py -v
pytest tests/architecture/ -v --tb=short
```

## Anti-Drift Test Guards

- Test `test_each_authoritative_phase_declares_*` iterates all 6 phases by enum value — will fail if PHASE_READ_DOMAINS/WRITE_DOMAINS/EMIT_DOMAINS is missing any phase.
- Test `test_resolution_is_sole_entity_write_phase` will catch any future phase accidentally claiming entity/world write access.
