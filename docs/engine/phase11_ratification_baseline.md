# Phase 11 Ratification Baseline

This document contains the frozen set of legacy replacement rows from Phases 5-10 that are subject to final ratification in Phase 11.

## 1. System Compatibility (SYS-COMPAT)
All operational and infrastructure surfaces hardened in Phase 10.

| ID | Item | Phase | Status | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **LEG-SYS-001** | CLI Mode / Args | Phase 10 | SUPPORTED | `src/cli/entry.py` |
| **LEG-SYS-002** | Config Precedence | Phase 10 | SUPPORTED | `src/config/loader.py` |
| **LEG-SYS-006** | Disabled-mode Isolation | Phase 10 | SUPPORTED | `src/config/loader.py` |
| **LEG-SYS-010** | Det. Replay Path | Phase 10 | SUPPORTED | `src/engine/replay_manager.py` |
| **LEG-SYS-011** | Structured Logging | Phase 10 | SUPPORTED | `src/logging/formatter.py` |
| **LEG-SYS-012** | Telemetry Parity | Phase 10 | SUPPORTED | `src/config/loader.py` |
| **LEG-SYS-013** | WebSocket behavior | Phase 10 | SUPPORTED | `src/api/ws/stream.py` |
| **LEG-SYS-014** | Gzip/Zstd | Phase 10 | SUPPORTED | `src/api/server.py` |
| **LEG-SYS-015** | Headless consistency | Phase 10 | SUPPORTED | `src/cli/entry.py` |
| **LEG-SYS-016** | Dep degradation | Phase 10 | SUPPORTED | `src/config/loader.py` |
| **LEG-SYS-020** | Status endpoints | Phase 10 | SUPPORTED | `src/api/server.py` |

## 2. RPG Core (RPG-CORE)
Gameplay and strategic logic recovered in Phases 5-9.

### Strategic & Social Cognition (Phase 9)
| ID | Item | Phase | Status | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-116** | Cognitive Bandwidth | Phase 9 | SUPPORTED | `src/systems/strategic.py` |
| **LEG-RPG-117** | Interruption Resistance | Phase 9 | SUPPORTED | `src/systems/strategic.py` |
| **LEG-RPG-119** | Believability thresholds | Phase 9 | SUPPORTED | `src/systems/strategic.py` |
| **LEG-RPG-123** | Directive Strengthening | Phase 9 | SUPPORTED | `src/systems/strategic.py` |
| **LEG-RPG-124** | Strategic Lock-in | Phase 9 | SUPPORTED | `src/systems/strategic.py` |
| **LEG-RPG-125** | Pivot Thresholds | Phase 9 | SUPPORTED | `src/systems/strategic.py` |
| **LEG-RPG-141** | Relationship Scars | Phase 9 | SUPPORTED | `src/systems/social.py` |
| **LEG-RPG-144** | Betrayal History | Phase 9 | SUPPORTED | `src/systems/social.py` |
| **LEG-RPG-145** | Recruitment Logic | Phase 9 | SUPPORTED | `src/systems/social.py` |
| **LEG-RPG-150** | Strategic Blocker Detect | Phase 9 | SUPPORTED | `src/systems/strategic.py` |
| **LEG-RPG-151** | Blocker resolution logic | Phase 9 | SUPPORTED | `src/systems/strategic.py` |

### Substrate & Core Mechanics (Phases 5-8)
*(Selected high-impact items)*
| ID | Item | Phase | Status | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-001** | Authoritative Action Model | Phase 7 | SUPPORTED | `src/engine/kernel.py` |
| **LEG-RPG-002** | Typed Update Schema | Phase 7 | SUPPORTED | `src/core/state.py` |
| **LEG-RPG-010** | Movement Determinism | Phase 5 | SUPPORTED | `src/systems/movement.py` |
| **LEG-RPG-020** | Resource Locking | Phase 8 | SUPPORTED | `src/systems/resource.py` |
| **LEG-RPG-030** | Combat Tick Purity | Phase 6 | SUPPORTED | `src/systems/combat.py` |

## 3. Retirement Candidate Remainder
Rows explicitly marked as DIVERGENT or DEPRECATED.

| ID | Item | Status | Reason |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-158** | Flanking / Backstab | UNSUPPORTED | Deferred to post-transition gameplay overhaul. |
| **LEG-SYS-003** | Broker Fallback | SUPPORTED | V2 uses in-memory fallback by default. |

---
**Ratification Status**: OPEN
**Baseline Version**: 2026-04-24.1
