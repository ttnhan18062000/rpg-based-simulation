# Plan — TCK-20260619-E42A-INFO-NEED

## Summary
Three surgical code changes + one new test file + one new module.

## Steps

### Step 1 — Extend UnknownFact (`src/core/self_model.py`)
Add two optional fields after `recorded_tick`:
```python
priority: float = 0.0            # 0.0–1.0; >0.5 triggers seeking
seeking_project_id: Optional[str] = None
```
Update `KnowledgeModelComponent.to_canonical_dict()` to include these in the unknowns serialisation.

### Step 2 — Add INFORMATION_SEEKING to ProjectKind (`src/core/strategic.py`)
After `INFORMATION = "information"` add:
```python
INFORMATION_SEEKING = "information_seeking"
```

### Step 3 — Create InformationNeedDetector (`src/engine/domain/cognition_extras.py`)
Pure static class:
- SEEKING_THRESHOLD = 0.5
- detect_and_generate(entity, tick) scans entity.self_model.knowledge.unknowns
- Filters for priority > SEEKING_THRESHOLD and seeking_project_id is None
- Picks highest-priority candidate
- Returns StrategicUpdate with one ProjectState(kind=INFORMATION_SEEKING, objectives=[ASK_INFORMATION])
  or None if no candidate.

### Step 4 — Write test file (`tests/unit/cognition/test_information_seeking.py`)
8 test cases as defined in test_plan.md. Uses V2EntityBuilder + SelfModelBundle; no AuthoritativeState needed.

## Architecture Constraints Respected
- UnknownFact stays frozen; new fields have defaults — backward compatible.
- InformationNeedDetector is pure (no side effects, no direct state writes).
- All durable changes expressed via StrategicUpdate.
- Determinism: only entity state + tick used, no randomness.
- No raw domain objects exposed via APIs.
