# TCK-20260428-PH10-EXTERNAL-TRUTH

## Title

External Truth and Replay Proof (Tracing & Metrics)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Ensure authoritative state transitions (transactions, rewards) are fully visible to external observers and reproducible in replays.

## Scope

- Add transaction tracing to `EntityState`.
- Add global resource conservation metrics to `AuthoritativeState`.
- Populate tracing data in `AuthoritativeApplyPipeline`.
- Ensure `ApplyPath` preserves tracing/metrics.
- Add replay test for rejected transactions.

## Acceptance Criteria

- [x] Entity state contains a list of intent results for the most recent tick.
- [x] Global resources include counters for items and gold in circulation.
- [x] Replay reproduces the exact same accepted/rejected status for intents.
- [x] Test suite confirms failure reasons (e.g. INVENTORY_FULL) are persisted.

## Related Tickets

- [TCK-20260428-PH9-WORLD-LIFECYCLE](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260428-PH9-WORLD-LIFECYCLE.md)

## Related Docs

- [resource_v2_e3_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e3_phases.md) (Phase 10)

## Related Stored Artifacts

- [staging_artifacts/TCK-20260428-PH10-EXTERNAL-TRUTH/plan.md](file:///home/vboxuser/Work/rpg-based-simulation/staging_artifacts/TCK-20260428-PH10-EXTERNAL-TRUTH/plan.md)

## Related Code Areas

- [src/core/state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- [src/engine/pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- [src/engine/apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)

## Test Summary

- `tests/engine/test_phase10_replay.py` passed.

## Files Changed

- [src/core/state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- [src/core/updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- [src/engine/pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- [src/engine/apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)

## Completion Summary

Implemented transaction tracing and conservation metrics, providing a verifiable "External Truth" for all authoritative state changes.
