---
status: active
layer: engine
authority: P1
audience: developer
---

# Replay Mode Reference

Replay richness is a mode-driven runtime cost. The governor and `ReplayManager` enforce these boundaries to ensure resource safety.

## Mode Summary

| Replay Mode | Capture Richness | Staging Window | Profile Constraint | Degradation |
| :--- | :--- | :--- | :--- | :--- |
| `OFF` | None | 0 KB | None | N/A |
| `MINIMAL` | Auth actions + errors | 64 KB | All classes | Non-auth traces first |
| `DEBUG_WINDOW` | Full component traces | 1024 KB | Class A, B | Drop to MINIMAL on pressure |
| `FORENSIC` | Byte-level detailed state | 4096 KB | Class A only | Forbidden in SURVIVAL |

## Mode Definitions

### OFF
No capture overhead. The replay subphase is skipped entirely.

### MINIMAL
Captures only CRITICAL work items and authoritative PERIODIC items. No payload data — headers only. Lowest memory and IO footprint.

### DEBUG_WINDOWED (Standard)
Captures all work-item execution and phase transitions. Includes payloads for entity updates. Maintains a sliding window for immediate forensics.

### FORENSIC_SHORT_RUN
Highest-fidelity capture. Captures internal subsystem state diffs. Only permitted on Class A hardware for short durations.

## Forbidden Behavior

- **Memory Growth**: Replay mode must not override the `max_replay_buffer_kb` ceiling of the active profile.
- **Authoritative Stalling**: Replay logic must not block kernel execution while waiting for sink availability.
- **Invisible Backlog**: No in-memory accumulation beyond the declared staging window.
