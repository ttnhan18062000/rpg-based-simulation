---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42A-INFO-NEED
phase: done
date: 2026-06-20
tags: [information-seeking, unknown-fact, project-kind, cognition, phase-4]
---

# TCK-20260619-E42A-INFO-NEED

## Title
Epic 4.2A · InformationNeed from UnknownFact

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`UnknownFact` at `src/core/self_model.py:L65` already models known-unknowns. This ticket extends it with a `seeking_project_id` link and adds `INFORMATION_SEEKING` to `ProjectKind`. Introduces `InformationNeedDetector` that converts high-priority unknown facts into projects.

**Blocks:** All other E42 child tickets

## Scope

### 1. Extend `UnknownFact` (`src/core/self_model.py:L65`)
```python
seeking_project_id: Optional[str] = None
priority: float = 0.0   # 0.0–1.0; >0.5 triggers seeking
```

### 2. Add `INFORMATION_SEEKING` to `ProjectKind` enum (`src/core/strategic.py`)

### 3. New `InformationNeedDetector` in `src/engine/domain/cognition_extras.py` (or alongside existing cognition module):
```python
class InformationNeedDetector:
    SEEKING_THRESHOLD = 0.5

    @staticmethod
    def detect_and_generate(entity: EntityState, tick: int) -> Optional[StrategicUpdate]:
        """For unknown facts with priority > threshold and no existing seeking project, generate one."""
        ...
```

Wire into cognition phase (after existing project evaluation, before route scoring).

## Acceptance Criteria
- `test_unknown_fact_generates_seeking_project` passes
- `ProjectKind.INFORMATION_SEEKING` importable
- Existing cognition tests pass (no regression)

## Related Tickets
- TCK-20260619-E42-INFO-SEEKING (parent epic)
- TCK-20260619-E42B-INFO-PROVIDER (blocked on this)

## Related Code Areas
- `src/core/self_model.py:L65` (UnknownFact)
- `src/core/strategic.py` (ProjectKind enum)
- `src/engine/domain/cognition.py` (wire InformationNeedDetector)

## Test Summary
```bash
pytest tests/unit/cognition/test_information_seeking.py::test_unknown_fact_generates_seeking_project -x -v
```
## Files Changed
- `src/core/self_model.py` — UnknownFact extended with `priority: float = 0.0` and `seeking_project_id: Optional[str] = None`; KnowledgeModelComponent.to_canonical_dict() updated to include new fields
- `src/core/strategic.py` — ProjectKind.INFORMATION_SEEKING = "information_seeking" added
- `src/engine/domain/cognition_extras.py` — NEW: InformationNeedDetector.detect_and_generate() pure static method
- `tests/unit/cognition/test_information_seeking.py` — NEW: 12 unit tests covering normal flow, edge cases, model fields
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-229 entry added

## Completion Summary
Added `priority` and `seeking_project_id` fields to `UnknownFact` (backward compatible defaults).
Added `ProjectKind.INFORMATION_SEEKING` to the enum.
Introduced `InformationNeedDetector` in `src/engine/domain/cognition_extras.py` — a pure static
detector that scans entity unknowns, picks the highest-priority candidate (priority > 0.5, no
existing seeking link), and returns a `StrategicUpdate` with one INFORMATION_SEEKING `ProjectState`
carrying an `ASK_INFORMATION` objective. 12 new tests pass; 81 existing cognition unit tests and 7
information integration tests show zero regressions. STRAT-229 parity ledger entry added.
