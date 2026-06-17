---
status: historical
layer: engine
authority: P2
audience: developer
---

# Remaining Replacement Scope (Phases 6-10)

This document summarizes the high-level backlog of legacy requirements that remain open at the end of Phase 6.

## Execution Backlog by Phase

### Phase 6: P0/P1 Recovery
- **Social Trust Baseline**: 12 items (LEG-RPG-049 to 060).
- **Opportunity Attacks**: 2 items (LEG-RPG-099, 017 partial fix).
- **Combat XP & Rewards**: 1 item (LEG-RPG-061).
- **Interaction Hardening**: 3 items (LEG-RPG-012 to 014 divergent items).

### Phase 7: Substrate & Hazards
- **Regional Hazards**: (LEG-RPG-071).
- **Calamity Evolution**: (LEG-RPG-139).
- **Dynamic Quests**: (LEG-RPG-141).
- **Substrate Determinism Hardening**: (Various RPG-CORE items).

### Phase 8: Combat & World Semantics
- **Advanced Tactical AI**: 119 items (The majority of currently UNSUPPORTED legacy behaviors).
- **Engagement Hostility**: (LEG-RPG-098).
- **Target Stickiness**: (LEG-RPG-100).
- **Navigational Depth**: (LEG-RPG-101 onwards).

### Phase 10: Legacy Compatibility
- **Telemetry Parity**: (LEG-SYS-012).
- **WebSocket Behavior**: (LEG-SYS-013).
- **Compression (Gzip/Zstd)**: (LEG-SYS-014).
- **Headless Consistency**: (LEG-SYS-015).

## Closure Strategy

Every open item labeled as **DIFFERENTIAL PARITY** requires a bit-identical or semantic-equivalent proof artifact before it can be closed. Items labeled as **V2 CONTRACT** are considered closed once the strict logic is implemented and regression-tested in V2.
