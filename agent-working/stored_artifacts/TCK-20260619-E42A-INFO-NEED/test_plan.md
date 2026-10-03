# Test Plan — TCK-20260619-E42A-INFO-NEED

## Scope
Unit tests for InformationNeedDetector and the extended UnknownFact model.
No integration test required at this tier (E42 child tickets add integration).

## Test File
`tests/unit/cognition/test_information_seeking.py`

## Cases

### Normal flow
1. `test_unknown_fact_generates_seeking_project` (acceptance criterion)
   - Entity with one UnknownFact (priority=0.6, no seeking_project_id)
   - detect_and_generate() → StrategicUpdate with one INFORMATION_SEEKING project
   - Project id contains the subject; objective kind is ASK_INFORMATION

2. `test_low_priority_unknown_does_not_generate_project`
   - Entity with UnknownFact(priority=0.3) — below threshold
   - detect_and_generate() → None (no project created)

3. `test_already_linked_unknown_does_not_generate_duplicate`
   - Entity with UnknownFact(priority=0.8, seeking_project_id="existing_proj")
   - detect_and_generate() → None (already linked, skip)

### Edge cases
4. `test_no_unknowns_returns_none`
   - Entity with empty knowledge.unknowns
   - detect_and_generate() → None

5. `test_highest_priority_unknown_chosen_when_multiple`
   - Entity with two unknowns: priority=0.9 and priority=0.6
   - detect_and_generate() returns project whose id references the 0.9-priority subject

6. `test_exactly_at_threshold_does_not_trigger`
   - priority=0.5 (not strictly greater than) → None

7. `test_project_kind_is_information_seeking`
   - Returned project has kind == ProjectKind.INFORMATION_SEEKING

### Regression
8. Run existing tests: `pytest tests/unit/cognition/ -x -q`
   - All Phase 2 cognition tests must continue to pass (UnknownFact accepts old positional args).

## Run Command
```bash
pytest tests/unit/cognition/test_information_seeking.py -x -v
pytest tests/unit/cognition/ -x -q
```
