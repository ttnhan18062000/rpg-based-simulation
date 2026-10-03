# Test Plan: TCK-20260619-E-CAP-REGISTRY

## Regression Surface
- `tests/unit/engine/` — existing engine unit tests must pass
- `tests/architecture/` — existing architecture tests must pass

## New Tests Required (per AC)

### `tests/unit/engine/test_capability_registry.py`
| Test | Purpose |
|---|---|
| `test_capability_registry_yaml_exists` | File docs/engine/capability_registry.yaml exists |
| `test_capability_registry_is_valid_yaml` | YAML loads without error |
| `test_all_registry_entries_have_required_fields` | Each entry has capability_id, name, status, description, since_version |
| `test_all_registry_statuses_are_valid` | All status values in {OFFICIAL, SUPPORTED, EXPERIMENTAL, DEPRECATED, UNSUPPORTED} |
| `test_registry_has_minimum_entries` | ≥20 entries |
| `test_capability_reader_is_supported` | is_supported("quest_generation") returns True |
| `test_capability_reader_is_unsupported` | is_supported("complex_pathfinding") returns False |
| `test_capability_reader_get_status` | get_status("deterministic_replay") returns "OFFICIAL" |
| `test_capability_reader_unknown_id` | get_status("nonexistent_cap") returns None |

### `tests/architecture/test_capability_references.py`
| Test | Purpose |
|---|---|
| `test_capability_ids_are_unique` | No duplicate capability_id in registry |

## Scoped Pytest Commands
```bash
pytest tests/unit/engine/test_capability_registry.py -v
pytest tests/architecture/test_capability_references.py -v
pytest tests/architecture/ tests/unit/engine/ -v --tb=short
```
