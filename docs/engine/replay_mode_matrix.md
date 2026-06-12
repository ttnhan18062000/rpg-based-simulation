---
status: historical
layer: engine
authority: P2
audience: developer
---

# Milestone 6 Replay Mode Matrix

## Summary
Replay richness is a mode-driven runtime cost. The Governor and ReplayManager enforce these boundaries to ensure resource safety.

| Replay Mode | Capture Richness | Staging Window | Profile Constraint | Degradation |
| :--- | :--- | :--- | :--- | :--- |
| `OFF` | None | 0 KB | None | N/A |
| `MINIMAL` | Auth Actions + Errors | 64 KB | All Classes | Non-auth traces first |
| `DEBUG_WINDOW` | Full Component Traces | 1024 KB | Class A, B | Drop to MINIMAL on pressure |
| `FORENSIC` | Byte-level detailed state | 4096 KB | Class A Only | Forbidden in SURVIVAL |

## Mode Definitions

### 1. OFF
- No capture overhead. Replay subphase is skipped.

### 2. MINIMAL
- Captures only `CRITICAL` work items and `Authoritative PERIODIC` items.
- No payload data; headers only.
- Lowest memory and IO footprint.

### 3. DEBUG_WINDOWED (Standard)
- Captures all `WorkItem` execution and Phase transitions.
- Includes payloads for entity updates.
- Maintains a sliding window for immediate forensics.

### 4. FORENSIC_SHORT_RUN
- Highest fidelity capture.
- Captures internal subsystem state diffs.
- Only permitted on Class A hardware for short durations.

## Forbidden Behavior
- **Memory Growth**: Replay mode MUST NOT override the `max_replay_buffer_kb` ceiling of the active profile.
- **Authoritative Stalling**: Replay logic MUST NOT block kernel execution while waiting for sink availability.
- **Invisible Backlog**: No in-memory accumulation beyond the declared staging window.

## Regression Risk
Failure to enforce these modes will lead to the same unbounded memory hazards present in the legacy engine.
