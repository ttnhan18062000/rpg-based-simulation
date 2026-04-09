# TCK-20260405-LOGFIX: Fix E2E Logging Timeouts

## Description
The `tests/e2e/test_logging_structure.py` was failing in certain headless environments due to subprocess timeouts (60s). This occurred because the CLI mode attempted to initialize heavyweight infrastructure (Kafka/RabbitMQ) even for simple log structure verification.

## Scope
- Disable Kafka and RabbitMQ in `_run_cli` mode across the simulation.
- Optimize CLI grid scaling parameters in tests for faster execution.
- Maintain JSON log format integrity.

## Acceptance Criteria
- [x] `tests/e2e/test_logging_structure.py` passes within 60s in headless mode.
- [x] Kafka/RabbitMQ disabled globally for CLI execution unless `DISABLE_*=0` is set.
- [x] CLI logs are strictly JSON formatted and contain `timestamp`, `level`, `message`, `component`.

## Status
DONE
