# Phase Dependency & Blocker Map

This document tracks the dependencies between engine phases and identifies specific blockers for downstream semantics.

## Phase 8 -> Phase 9 Blockers

| Downstream Row | Phase 9 Requirement | Phase 8 Blocker | Reason |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-150** | Belief cycle (Rumors) | **LEG-RPG-098** (Hostility) | Strategic belief requires stable local hostility/engagement triggers. |
| **LEG-RPG-119** | Betrayal (Avenge) | **LEG-RPG-102** (Tactical Bias) | Betrayal logic assumes archetype-consistent tactical responses. |
| **LEG-RPG-141** | Dynamic Quests | **LEG-RPG-117** (Scar Detection) | Quest generation depends on environment/scar awareness. |

## Substrate Dependencies

| Phase 8 Row | Substrate Dependency | Status |
| :--- | :--- | :--- |
| All Tactical AI | **Phase 7 Substrate Closure** | **CLOSED** |
| All World Interaction | **Phase 7 Deterministic RNG** | **CLOSED** |

## Phase 10 -> Phase 11/12 Blockers

| Downstream Phase | Requirement | Phase 10 Blocker | Reason |
| :--- | :--- | :--- | :--- |
| **Phase 11** | System Ratification | **LEG-SYS-001** (CLI Parity) | Cannot ratify system behavior without original entrypoint semantics. |
| **Phase 11** | Replay Validation | **LEG-SYS-009** (JSON-L) | Replay-based proof requires exact bit-identical artifact parity. |
| **Phase 12** | Consumer Cutover | **LEG-SYS-013** (WebSocket) | External consumers depend on stable WebSocket lifecycle signals. |
| **Phase 12** | Tooling Integration | **LEG-SYS-012** (Telemetry) | Operations tooling requires disaggregated metrics parity. |

## Strategic Assumptions
Phase 10 system compatibility closure assumes:
- Phase 9 semantic stability for all RPG domains.
- Stable deterministic replay substrate (Phase 7).
- Verified concurrent worker management (Phase 5).
