# Investigation: Milestone C - Operational Integrity

## Status
The engine already has high-quality implementations for Replay, Shutdown, and Startup Validation. The Milestone C closure is primarily about moving from "subsystem presence" to "subsystem closure" by proving the laws in the `operational_integrity_contract_mc.md`.

## Laws to Verify

### 1. Replay Lifecycle
- [x] Staging bound (BoundedBuffer used in ReplayBuffer).
- [x] Overflow policy (EVICT_OLDEST/TRUNCATE_NEWEST implemented).
- [x] Saturation guard (0.9 threshold check in on_tick_end).
- [ ] Atomic Manifest (Implemented, but missing targeted verification test).

### 2. Startup & Flags
- [x] ConfigValidationError raised for unsafe flags.
- [x] Contradictory flags (SURVIVAL_ONLY + REPLAY) rejected.
- [ ] Contradictory Config (REPLAY_ENABLED + 0KB buffer) - Code has it, needs verification test.

### 3. Shutdown & Snapshots
- [x] Fixed 5.0s budget in Kernel.
- [x] Pre-emptive budget check in ReplayManager.
- [ ] Final authoritative hash emission (Diagnostic print present in Kernel.shutdown).

## Risks
- Terminology drift: Ensure `chunk_tick_limit` and `rotation_threshold` are the exact terms used everywhere.
- Timeout granularity: Ensure the 0.5s safety margin is sufficient for the manifest write.
