---
status: active
layer: content
authority: P1
audience: agent
ticket_id: TCK-20260624-FIX-SPAWN-SCHEMA
phase: open
date: 2026-06-24
tags: [content, schema, spawn-table, pydantic, class-table]
---

# TCK-20260624-FIX-SPAWN-SCHEMA

## Title
Add ClassTableDefinition schema for spawn_tables.yaml class_id_by_role record type

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`spawn_tables.yaml` contains two logically different record types:
1. `forest_spawn_pool` — uses `spawn_weights: Dict[str, float]` → matches existing `SpawnTableDefinition` schema ✓
2. `default_class_table` — uses `class_id_by_role: Dict[str, str]` → added by `TCK-20260619-P0-ENTITY-INIT` but `SpawnTableDefinition` was never updated

`SpawnTableDefinition` has `extra="forbid"` so `class_id_by_role` triggers `Extra inputs are not permitted`, and `spawn_weights` is `Required` so the second record type also fails that check. The test `test_strict_load_on_real_content_dir` catches both violations.

The data is intentional and newer than the schema — the schema must be extended, not the data.

## Scope
- Define a new `ClassTableDefinition` Pydantic model with `class_id_by_role: Dict[str, str]` and appropriate `extra="forbid"`
- Register it as a separate content family or as a union variant in the spawn-table loader
- Update `CANONICAL_FAMILIES` (or equivalent registry) so the strict-load test can validate `default_class_table` against the new schema
- Update `docs/mechanics/content_usage_matrix.md` if a new content family row is added
- Update the parity ledger (`docs/parity_ledger/town_resource.yaml` or `substrate.yaml`) if the schema change affects a tracked behavior

## Out of Scope
- Changing `data/content/spawn_tables.yaml`
- Changing `SpawnTableDefinition` itself (it is correct for `forest_spawn_pool`)
- Changing `test_strict_load_on_real_content_dir` (the test is correct)

## Acceptance Criteria
- `tests/unit/content/test_content_paths.py::test_strict_load_on_real_content_dir` passes
- `default_class_table` validates correctly against `ClassTableDefinition`
- `forest_spawn_pool` still validates correctly against `SpawnTableDefinition`
- No regression in other content schema tests

## Related Tickets
- `TCK-20260619-P0-ENTITY-INIT` — added `default_class_table` to `spawn_tables.yaml`

## Related Docs
- `docs/mechanics/content_usage_matrix.md`
- `docs/parity_ledger/substrate.yaml` or `town_resource.yaml`

## Related Stored Artifacts
None

## Related Code Areas
- `src/content/schema.py` — `SpawnTableDefinition` (line ~271)
- `data/content/spawn_tables.yaml`
- `tests/unit/content/test_content_paths.py::test_strict_load_on_real_content_dir`
- Content family registry (wherever `CANONICAL_FAMILIES` is defined)

## Assumptions / Open Questions
- Determine whether `default_class_table` should be a union variant of the same loader (same YAML file, polymorphic) or registered under a separate content family key
- If polymorphic: use a `type` discriminator field, or detect by presence of `class_id_by_role` vs `spawn_weights`
- If separate family: the key in `CANONICAL_FAMILIES` would be e.g. `"spawn/class_table"` with schema `ClassTableDefinition`

## Implementation Notes
Minimal path (separate family key):
```python
class ClassTableDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    class_id_by_role: Dict[str, str]

# In CANONICAL_FAMILIES:
"spawn/class_table": ClassTableDefinition
```
Then the strict-load validator needs to know `default_class_table` maps to `"spawn/class_table"` — this may require a `schema_key` field in the YAML or a name-based dispatch rule.

## Test Summary
Run: `pytest tests/unit/content/test_content_paths.py -v`
Also run: `pytest tests/unit/content/ -v` to confirm no schema regression.

## Files Changed
TBD

## Completion Summary
TBD
