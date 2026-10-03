---
status: active
artifact_type: test_plan
ticket_id: TCK-20260627-P2D-FACTION-RELS
date: 2026-06-27
---

# Test Plan — TCK-20260627-P2D-FACTION-RELS

## Regression Surface

Existing tests that must continue to pass:
- `tests/unit/content/test_catalog.py` — catalog load, schema validation
- `tests/unit/content/test_layered_catalog.py` — layered catalog loading
- `tests/unit/content/test_content_usage_matrix.py` — content usage matrix
- `tests/unit/content/test_reference_graph.py` — reference graph

## New Tests Required

Per acceptance criteria:
1. **Count check**: `faction_relationships` catalog has ≥30 entries.
2. **Hostile count**: at least 10 entries with `axes.hostility` in {"high", "high_contextual"}.
3. **Schema load**: all new entries load without Pydantic validation errors (covered by catalog test).
4. **Faction ID validity**: all `source_faction`/`target_faction` values are registered faction IDs.

These will be added to `tests/unit/content/test_catalog.py` or a new focused test module.

## Scoped Pytest Commands

```bash
# Primary — catalog schema validation
pytest tests/unit/content/test_catalog.py -v

# Regression — full content test suite (scoped)
pytest tests/unit/content/ -v -m "not slow"

# Quick inline count verification
python3 -c "
import yaml
data = yaml.safe_load(open('data/content/social/faction_relationships.yaml'))
print(f'Total entries: {len(data)}')
hostile = [r for r in data if r.get('axes', {}).get('hostility', '') in ('high', 'high_contextual', 'high_if_intruding')]
print(f'Hostile entries: {len(hostile)}')
assert len(data) >= 30, f'Need >=30, got {len(data)}'
assert len(hostile) >= 10, f'Need >=10 hostile, got {len(hostile)}'
print('AC assertions PASSED')
"
```

## Anti-Drift Test Guards

- If a new field is added to `FactionRelationshipDefinition` with `extra="forbid"`, any entry with that field present will start failing. Monitor `test_catalog.py` as the guard.
- Schema load test (`CatalogRepository.load_all()`) is the primary guard for well-formedness.
