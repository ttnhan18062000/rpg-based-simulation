# TCK-20260418-RESOURCE-PERSISTENCE-M6

## Title
Milestone 6: Streaming Replay and Bounded Persistence

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement a resource-safe persistence model for replay data with streaming emission, bounded staging, and deterministic chunking.

## Scope
- Define `ReplayContract` for non-authoritative event capture.
- Implement `ReplayBuffer` with policy-bound staging (Drop/Overflow).
- Implement `ReplaySink` with compact serialization (JSON fallback used).
- Implement `ReplayManager` for chunk rotation and manifest indexing.
- Integrate with `Kernel` persistence phase and `GovernorPolicy`.

## Out of Scope
- Concurrency (M7).
- Full observability plumbing.
- Remote transport.

## Acceptance Criteria
- [x] Replay is non-authoritative (failures do not stall kernel).
- [x] No whole-run in-memory accumulation.
- [x] Deterministic chunk rotation (Tick-based).
- [x] Valid `manifest.json` tracker for every run.
- [x] 100% test pass for replay laws.

## Related Tickets
- TCK-20260418-RESOURCE-KERNEL-M5 (DONE)

## Related Docs
- `replay_contract_m6.md`
- `m6_replay_mode_matrix.md`
- `m6_test_matrix.md`

## Related Code Areas
- `src/engine/` (replay_manager, replay_buffer, replay_sink, kernel)
- `src/core/` (replay_modes, policy)

## Assumptions / Open Questions
- Falling back to JSON for chunks due to `msgpack` library unavailability in the isolated environment.

## Implementation Notes
- Enforced "Non-Blocking" law by hardening the `ReplayManager` against sink IO errors.
- Implemented "Waterfall Drop" policy in `GovernorPolicy` to shed internal traces before critical actions.

## Test Summary
- 6 new tests added in `tests/engine/`.
- `test_non_authoritative` verified kernel resilience to disk failure.
- `test_replay_overflow` verified buffer eviction policy.
- `test_replay_chunk_rotation` verified manifest and rotation logic.

## Files Changed
- `src/core/replay_modes.py`
- `src/engine/replay_buffer.py`
- `src/engine/replay_sink.py`
- `src/engine/replay_manager.py`
- `src/engine/policy.py`
- `src/engine/kernel.py`

## Completion Summary
Milestone 6 finalized. The engine now supports resource-safe replay persistence. Replay data is streamed in deterministic chunks via a policy-bound buffer, ensuring that even under severe IO or memory pressure, the authoritative simulation remains stable and bit-identical.
