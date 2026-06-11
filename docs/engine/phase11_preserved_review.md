---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 11 Preserved-Row Review

This document contains the explicit proof review for every row labeled as **SUPPORTED** (Preserved) in the replacement ledger.

## 1. System Compatibility (Phase 10 Focus)

| ID | Item | Phase | Required Proof | Evidence | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LEG-SYS-001** | CLI Mode / Args | Ph 10 | Black-box / Parity | `test_entry_parity.py` | EARNED |
| **LEG-SYS-002** | Config Precedence | Ph 10 | Black-box / Parity | `test_infra_isolation.py` | EARNED |
| **LEG-SYS-006** | Disabled-mode Isolation | Ph 10 | Contract | `test_infra_isolation.py` | EARNED |
| **LEG-SYS-010** | Det. Replay Path | Ph 10 | Differential | `test_observability.py` | EARNED |
| **LEG-SYS-011** | Structured Logging | Ph 10 | Parity | `test_observability.py` | EARNED |
| **LEG-SYS-012** | Telemetry Parity | Ph 10 | Contract | `test_observability.py` | EARNED |
| **LEG-SYS-013** | WebSocket behavior | Ph 10 | Protocol Parity | `test_ws_protocol.py` | EARNED |
| **LEG-SYS-014** | Gzip/Zstd | Ph 10 | Middleware Parity | `test_rest_parity.py` | EARNED |
| **LEG-SYS-015** | Headless consistency | Ph 10 | CLI Parity | `test_entry_parity.py` | EARNED |
| **LEG-SYS-016** | Dep degradation | Ph 10 | Contract | `test_infra_isolation.py` | EARNED |
| **LEG-SYS-020** | Status endpoints | Ph 10 | REST Parity | `test_rest_parity.py` | EARNED |

## 2. Strategic & Social Cognition (Phase 9 Focus)

| ID | Item | Phase | Required Proof | Evidence | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-116** | Strategic pivot (Danger) | Ph 9 | V2 Contract | `test_event_interpretation.py` | EARNED |
| **LEG-RPG-117** | Scar detection | Ph 9 | V2 Contract | `test_event_interpretation.py` | EARNED |
| **LEG-RPG-119** | Betrayal (Avenge) | Ph 9 | V2 Contract | `test_betrayal_consequence.py` | EARNED |
| **LEG-RPG-123** | Refutation drops trust | Ph 9 | V2 Contract | `test_source_trust.py` | EARNED |
| **LEG-RPG-124** | Recruitment haggling | Ph 9 | Differential | `test_recruitment.py` | EARNED |
| **LEG-RPG-125** | Contradiction degrades cert | Ph 9 | V2 Contract | `test_belief_cycle.py` | EARNED |
| **LEG-RPG-141** | Dynamic Quests | Ph 9 | V2 Contract | `test_quest_generation.py` | EARNED |
| **LEG-RPG-144** | Innate Talents (Genetics) | Ph 9 | V2 Contract | `test_genetics.py` | EARNED |
| **LEG-RPG-145** | Skill scaling (Types) | Ph 9 | V2 Contract | `test_genetics.py` | EARNED |
| **LEG-RPG-150** | Belief cycle (Rumors) | Ph 9 | V2 Contract | `test_belief_cycle.py` | EARNED |
| **LEG-RPG-151** | Narrative memory logging | Ph 9 | V2 Contract | `test_narrative_memory.py` | EARNED |

## 3. Substrate & Lifecycle (Phase 7 Focus)

| ID | Item | Phase | Required Proof | Evidence | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-001** | Action intent-to-update | Ph 7 | Certification | `test_authoritative_apply.py` | EARNED |
| **LEG-RPG-002** | Domain-isolated update | Ph 7 | Certification | `test_authoritative_apply.py` | EARNED |
| **LEG-RPG-071** | Regional hazards | Ph 7 | V2 Contract | `test_world_dynamics_contract.py` | EARNED |
| **LEG-RPG-073** | Engine phase order | Ph 7 | Certification | `test_invariants.py` | EARNED |
| **LEG-RPG-139** | Calamity consequences | Ph 7 | V2 Contract | `test_world_dynamics_contract.py` | EARNED |
| **LEG-RPG-143** | Entity Evolution | Ph 7 | V2 Contract | `test_evolution_contract.py` | EARNED |

## 4. Tactical & Movement (Phases 5-8 Focus)

| ID | Item | Phase | Required Proof | Evidence | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-009** | Manhattan distance | Ph 5 | Differential | `test_movement_parity.py` | EARNED |
| **LEG-RPG-010** | Cardinal movement | Ph 5 | Differential | `test_movement_parity.py` | EARNED |
| **LEG-RPG-020** | Congestion handling | Ph 5 | Differential | `test_movement_parity.py` | EARNED |
| **LEG-RPG-075** | Reactive cover seeking | Ph 8 | V2 Contract | `test_tactical_behavior.py` | EARNED |
| **LEG-RPG-076** | Chokepoint holding | Ph 8 | V2 Contract | `test_tactical_behavior.py` | EARNED |
| **LEG-RPG-077** | Flanking bracketing | Ph 8 | V2 Contract | `test_bracketing_bonus.py` | EARNED |
| **LEG-RPG-091** | High ground bonus | Ph 8 | Differential | `test_terrain_semantics.py` | EARNED |
| **LEG-RPG-146** | Building Sabotage | Ph 8 | V2 Contract | `test_sabotage_contract.py` | EARNED |

## 5. Review Observations

- **Weak Proof**: `LEG-RPG-018` (Anti-stalemate logic) relies on a broad cycle-detection test but lacks a specific bit-identical parity check against legacy.
- **Downgrade Candidate**: `LEG-RPG-031` (Guild visits) is marked SUPPORTED but V2 Source is `UNSUPPORTED`. This is a clear support-boundary overclaim.
- **Divergence Check**: `LEG-RPG-012` and `LEG-RPG-013` (Melee/Ranged legality) are marked DIVERGENT status but SUPPORTED maturity. These require careful ratification in Milestone 4.

---
**Ratification Status**: OPEN
**Baseline Version**: 2026-04-24.1
