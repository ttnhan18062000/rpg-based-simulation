# Infra 01: Automated Testing Infrastructure

## Status: DONE

## Summary

Add automated testing commands and key test suites to catch regressions across the simulation engine.

## Deliverables

### Makefile Commands

| Command | Purpose |
|---------|---------|
| `make test` | Run all Python tests (`pytest tests/ -v`) |
| `make test-quick` | Run fast tests only (skip `@pytest.mark.slow`) |
| `make test-cov` | Run tests with coverage report |

### New Test Files

| File | Tests | Covers |
|------|-------|--------|
| `tests/test_deterministic_replay.py` | 4 tests | Run N ticks twice with same seed, verify identical state via SHA-256 fingerprint. Catches any non-determinism across the entire engine. |
| `tests/test_conflict_resolver.py` | 10 tests | Move collision, priority (next_act_at + ID tie-break), wall/occupied rejection, diagonal HUNT deadlock (bug-01 scenario), combat dead-target rejection, resolution determinism. |
| `tests/test_inventory_goals.py` | 6 tests | Full-bag loot returns 0, nearly-full penalty, empty-bag positive score, no-loot-nearby low score, trade boost on full bag, trade outscores loot on full bag (bug-02 scenario). |

### Config

- Registered `slow` pytest marker in `pyproject.toml`

### Per-Tick Phase Timing

Added `time.perf_counter()` instrumentation to `WorldLoop._step()` — logs schedule/collect/resolve/cleanup times at DEBUG level. Zero overhead when not in DEBUG mode.

## How to Run

```bash
make test          # All tests (currently 296+ pass)
make test-quick    # Skip slow integration tests
make test-cov      # With coverage
```

## Labels

`infra`, `testing`, `automation`, `done`
