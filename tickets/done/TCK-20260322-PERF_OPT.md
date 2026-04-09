# TCK-20260322-PERF_OPT: RPG Simulation Performance Optimization

## Description
Critical performance bottleneck causing 100% CPU usage and drastic TPS drop (0.4 TPS). Investigated and resolved through multi-layer optimizations in world state management, grid serialization, and communication protocols.

## Scope
- `src/core/grid.py`: `bytearray` migration + Enum cache.
- `src/core/models.py`: Shallow copy implementation.
- `src/engine/worker_pool.py`: AI Task Batching.
- `src/workers/ai_worker_daemon.py`: Batch result processing.
- `src/ai/perception.py`: Scan radius tuning.

## Acceptance Criteria
- [x] Restore TPS to > 10 (Achieved ~20 TPS in local testing).
- [x] Reduce CPU utilization in the backend container.
- [x] Verify correctness with unit/integration tests.

## Final Status: DONE
Implemented all planned optimizations. Verified with micro-benchmarks and automated tests. Corrected Enum instantiation overhead during verification.

## Test Coverage
- `tests/unit/core/test_performance_optimizations.py`: 4 new unit tests.
- `tests/integration/engine/test_worker_pool_rabbitmq.py`: 1 updated integration test.
- All 5 tests passed.

## Notes
- `Material` cache was added to avoid `Enum` instantiation overhead ($50\times$ speedup).
- AI Task Batching reduces RabbitMQ roundtrips from 188 to 2 per tick.
- Docker environment requires `up --build` to propagate code changes.
