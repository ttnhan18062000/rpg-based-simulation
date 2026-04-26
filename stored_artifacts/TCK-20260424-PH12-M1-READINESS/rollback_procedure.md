# Phase 12 Rollback Procedure

## 1. Detection
Rollback is triggered if:
- `src` execution results in unhandled `Exception` (Kernel Panic).
- Bit-identical parity fails for a previously verified "Allowed" item.
- Resource interaction (Harvest/Loot) leaks memory or hangs.

## 2. Procedure
1. **CLI**: Revert default command aliases from `src` back to `src`.
2. **Environment**: Unset `BROKER_DISABLED=1` to restore legacy RabbitMQ/Kafka routing.
3. **API**: Restart the server pointing to the legacy `src.api.server` entrypoint.

## 3. Post-Rollback
- Audit the `src` logs to identify the drift.
- Re-run the `test_v2/verify/` suite to confirm the failure is reproducible in isolation.
