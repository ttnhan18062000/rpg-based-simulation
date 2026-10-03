---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260627-P2O-ENTITY-PERSONALITY-OBS
artifact_type: test_plan
tags: [observability, personality, snapshot, jsonl]
---

# Test Plan — TCK-20260627-P2O-ENTITY-PERSONALITY-OBS

## Test File
`tests/unit/observability/test_entity_personality_snapshot.py`

## Unit Tests

### TC-1: LIGHT mode emits on project kind change
- Build a `PersonalitySnapshotRecorder` with a temp `run_dir`
- Call `record_tick()` twice with same entity and same project kind
- Expect: JSONL file has exactly 1 record (first tick triggers initial emission)
- Call again with changed project kind
- Expect: JSONL file now has 2 records

### TC-2: LIGHT mode does NOT emit when project kind unchanged (after initial)
- Build recorder, call `record_tick()` twice with identical state (same project kind)
- Expect: exactly 1 record (first call emits, second does not)

### TC-3: DEBUG mode emits every tick
- Build recorder, set mode to DEBUG
- Call `record_tick()` 5 times with same entity and same project kind
- Expect: 5 records in JSONL file

### TC-4: Record contains all required fields
- Emit one record for an entity with explicit personality, role, class_id, project
- Parse JSONL line, assert keys: entity_id, tick, role, class_id, personality, active_project_kind, run_id
- Assert personality sub-keys: greed, bravery, sociability, industry (all float)

### TC-5: Entity without strategic component is skipped
- Build state with entity that has `strategic=None`
- Call `record_tick()`
- Expect: no file written (or empty file)

### TC-6: Entity with no active project emits None for active_project_kind
- Entity with `current_project_id=None`
- First tick emits a record with `active_project_kind=None`

### TC-7: Regression — observability tests in unit/observability/ unaffected
Run: `pytest tests/unit/observability/ -m "not slow" -x -q`

## Acceptance Criteria Cross-Check
| Criterion | Test |
|---|---|
| entity_personality_snapshots.jsonl written | TC-1 |
| Record has entity_id, tick, role, class_id, personality, active_project_kind | TC-4 |
| Emit on project kind change in LIGHT mode | TC-1 |
| Emit every tick in DEBUG mode | TC-3 |
| Unit test 100-tick equiv: ≥1 snapshot per entity | TC-1, TC-3 |
| Parity ledger entry | Phase 7 |
