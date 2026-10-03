---
content_type: doc
status: historical
layer: observability
authority: P2
audience: agent
tags: [debug_tests]
---

# Implementation Plan - Fix WorldLoop Tests

Fix the 8 failing tests and investigate/address the 51 skipped tests to achieve a stable test suite.

## Proposed Changes

### AI & Core Unit Tests
- [MODIFY] `tests/unit/ai/test_emotions.py`: Mock `actor.stats.hp_ratio` and `actor.progression.age_ticks` as floats/ints to avoid `TypeError` when compared in `AIBrain`.
- [MODIFY] `tests/unit/ai/test_stuck.py`: Same as above; also fix `FactionRegistry.is_hostile` mocking.
- [MODIFY] `tests/unit/core/test_breakthroughs.py`: Ensure `stats.atk` and traits are properly mocked for comparison.
- [MODIFY] `tests/unit/core/test_genetics.py`: Fix `FactionRegistry` mocking.

### Quest System
- [MODIFY] `src/core/quests.py`: Ensure `target_pos` is correctly initialized at the top of `generate_quest` to avoid `UnboundLocalError`.

### Docker Port Isolation (E2E Tests)
- [MODIFY] `docker-compose.yml`: Use environment variables for all host port mappings (e.g., `${BACKEND_PORT:-8000}:8000`).
- [MODIFY] `tests/e2e/conftest.py`: 
    - Dynamically assign available ports for the E2E test session.
    - Pass these ports via environment variables to `docker compose`.
    - Provide a mechanism (fixture or shared config) for tests to discover the assigned ports.
- [MODIFY] `tests/e2e/test_production_stack.py`: Replace hardcoded URLs/ports with values from the `engine_stack` fixture.

### Test Suite Stability
- Investigate skip reasons for the 51 tests. If they are due to missing environment (Redis/Kafka), ensure they are elegantly skipped with clear messages or mocked where appropriate for unit tests.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/ai/test_emotions.py`
- Run `pytest tests/unit/ai/test_stuck.py`
- Run `pytest tests/unit/core/test_breakthroughs.py`
- Run `pytest tests/unit/core/test_genetics.py`
- Run `pytest tests/unit/core/test_quests.py`
- Final full run: `pytest tests/unit`

### Manual Verification
- None required for these unit test fixes.
