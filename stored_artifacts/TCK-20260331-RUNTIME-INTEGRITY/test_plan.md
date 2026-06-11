---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260331-RUNTIME-INTEGRITY
artifact_type: test_plan
tags: [runtime, integrity]
---

# Test Plan: TCK-20260331-RUNTIME-INTEGRITY

## Strategy
We will use a combination of static analysis (grep), unit tests, and integration tests to ensure that the refactor doesn't break the simulation.

## Test Cases

### 1. Static Validation (Legacy Purge)
- **Check**: `grep -r ".stats." src/` should return 0 hits (excluding comments/logs if any).
- **Check**: `grep -r ".mind.ai_state" src/` should return 0 hits.

### 2. Functional Correctness
- **Unit Tests**: Run `pytest tests/unit/` to ensure discrete components still work with aspect-based access.
- **AI Handlers**: Specifically test `VisitShopHandler` and `VisitBlacksmithHandler` to ensure they no longer mutate the actor but produce valid `ActionProposal`s.
- **Presenter**: Test `EntityPresenter` with various entity configurations (different aspects present/absent).

### 3. Regression & Stability
- **Full Suite**: Run `pytest tests/` (748+ tests).
- **Determinism**: Run `tests/integration/test_determinism.py` to ensure that moving to aspects and proposal-based interactions doesn't change the outcome of a fixed seed.

### 4. API Integrity
- **Mock API Calls**: Verify that `/api/v1/state` returns the expected JSON structure without internal server errors (500) caused by missing `.to_slim_schema()` methods.

## Regression Surface
- **Combat Resolution**: Ensure that changing HP/target access doesn't break damage application.
- **Economy**: Verify that shop transactions still result in gold/item changes (now via the resolver).
- **Replay**: Ensure the replay recorder correctly captures the new aspect-based state.
