## Findings
- E2E suite is 90% stable on Windows.
- `test_deep_stack_error_audit` is the final blocker.
- **Root Cause**: `pika` (RabbitMQ client) in `ai_worker` logs `Socket failed to connect` as `ERROR` during the initial bootstrap phase.
- **Timing**: These logs occur within the first 30-60 seconds of cold start, which overlaps with the `time.time() - 60` window if the audit runs immediately after the stack is healthy.
- **Loki Filter**: The time-filter alone is insufficient because "Healthy" (as per Watchdog) doesn't guarantee that NO previous error logs exist in Loki's index for that window.

## Hypotheses
1. **Benign Async Noise**: (Confirmed) `pika` logs connection retries as `ERROR`.
2. **Promtail Delay**: (Probable) Logs from the first 30s are flushed to Loki at 60s.

## Next Steps
- Re-implement a hybrid filter: Time-filter (last 60s) AND specific message exclusions (`Socket failed to connect`, `AMQPConnection`, etc.).
- Run the full suite again.
