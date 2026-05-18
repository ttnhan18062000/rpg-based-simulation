# Phase 12 Cutover Constraints

This document defines the operational caveats and constraints that must be obeyed during Phase 12 cutover.

## 1. Divergence Constraints (Divergent-but-Supported)
- **Bounded Cognition**: Consumers must expect AI to "lose interest" in projects that exceed attention or detour depth limits. This is intentional and justified.
- **Engagement Lock**: Move commands that violate engagement truth will be rejected by the `LegalityService`. Consumers must handle `ILLEGAL_MOVE` rejection codes.
- **Lowercase Normalization**: All external inputs (items, materials) must be normalized to lowercase before API submission.

## 2. Unsupported-Scope Exclusions (Forbidden Assumptions)
- **Gameplay Remains**: Any logic related to `XP`, `Levels`, `Milestones`, or `Territory Ownership` must be handled by an external wrapper or considered "No-Op" in Phase 12.
- **Combat Variance**: Resolution is 100% deterministic. AI strategies relying on "RNG-luck" for evasion or criticals will fail.

## 3. Retired-Scope Exclusions (Removed Items)
- **Broker PUB/SUB**: External message brokers are retired. Cutover must use the in-process `V2EngineManager` listeners or WebSocket stream.
- **Legacy Geometry**: Exploits involving corner-clipping are removed. V2 enforces true LoS.

## 4. Operational Caveats
- **Replay JSON-L**: Flush timing is deterministic per tick, but the underlying file descriptor is buffered. Replays must be finalized via `finalize_replay()` before external consumption.
- **Concurrency**: Parallel AI is safe (single-writer), but memory overhead increases with entity count. Monitor `worker_utilization` in Phase 12.

---
**Ratification Status**: PROVISIONAL (Cutover Constraints Defined)
**Audit Date**: 2026-04-24
