# Test Plan: Replay Sink Hardening and Test Closure

## Automated Tests
- Run `pytest tests/cli/test_observability.py` to verify replay persistence integrity.
- Run `pytest tests/arena/test_arena_regional_control.py` to verify scenario combat stat preservation and regional debuff application.
- Run `pytest tests/certification/test_final_gate.py` to verify release proof validation.
- Run `pytest` across the repository.

## Expected Outcomes
- All tests pass with zero failures.
