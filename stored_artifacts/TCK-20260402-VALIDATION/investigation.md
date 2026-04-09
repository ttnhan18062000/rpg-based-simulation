# Investigation: TCK-20260402-VALIDATION

## Findings

### Profiler Regression
- `scripts/profile_simulation.py` fails with `ModuleNotFoundError: No module named 'src.core.snapshot'`.
- AOA migration moved this to `src.core.models.snapshot`.

### Performance Concerns
- `Entity.property_shims` uses `hasattr` and `getattr` which can be slow in hot-loops.
- `SimulationModel._validate_before` is called on every update.
- **Hypothesis**: The overhead should be < 1ms per tick for 100 entities, but needs verification.

### Test Flakiness
- Some integration tests rely on environment-specific services (Kafka, RabbitMQ, Redis).
- We should focus on core simulation tests first.
