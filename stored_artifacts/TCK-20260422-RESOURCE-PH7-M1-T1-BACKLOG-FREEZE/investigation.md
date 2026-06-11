---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260422-RESOURCE-PH7-M1-T1-BACKLOG-FREEZE
artifact_type: investigation
tags: [resource, ph7, m1, t1, backlog, freeze]
---

# Investigation: Phase 7 Backlog Freeze

## Current Ledger State

The `legacy_replacement_ledger.md` identifies 7 items currently marked for **Phase 7**:

- **LEG-RPG-071**: Regional hazards
- **LEG-RPG-139**: Calamity consequences
- **LEG-RPG-141**: Dynamic Quests
- **LEG-RPG-143**: Entity Evolution
- **LEG-RPG-146**: Building Sabotage
- **LEG-RPG-150**: Belief cycle (Rumors)
- **LEG-RPG-151**: Narrative memory logging

## Substrate vs Semantic Analysis

The `resource_phase7_high_level.md` defines Phase 7 as **Substrate Closure**, not for broad semantic recovery.

| ID | Item | Category | Alignment with Ph7 |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-071** | Regional hazards | Substrate (World) | **YES** |
| **LEG-RPG-139** | Calamity consequences | Substrate (World) | **YES** |
| **LEG-RPG-141** | Dynamic Quests | Semantic (Gameplay) | **NO** (Move to Ph8/9) |
| **LEG-RPG-143** | Entity Evolution | Substrate (Archetypes) | **YES** |
| **LEG-RPG-146** | Building Sabotage | Semantic (Gameplay) | **NO** (Move to Ph8) |
| **LEG-RPG-150** | Belief cycle (Rumors) | Semantic (Social) | **NO** (Move to Ph9) |
| **LEG-RPG-151** | Narrative memory logging| Semantic (Social) | **NO** (Move to Ph9) |

## Proposed Substrate Hardening Rows

In addition to the gaps, Phase 7 must "Close" (Harden/Certify) existing substrate rows that were marked as Phase 5/6 but are critical for the deterministic baseline.

| ID | Item | Current Status | Hardening Requirement |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-001** | Action intent convergence | SUPPORTED | M7 Determinism Proof |
| **LEG-RPG-004** | World mutation separation | SUPPORTED | 6-Phase Loop Proof |
| **LEG-RPG-006** | Conflict resolution | SUPPORTED | Deterministic Tick Proof |
| **LEG-RPG-066** | World gen determinism | SUPPORTED | Bit-identical Seed Proof |
| **LEG-RPG-068** | Snapshot immutability | SUPPORTED | Purity/Deep-copy Guard |
| **LEG-RPG-070** | Deterministic replay | SUPPORTED | Replay Finalization Hardening |
| **LEG-RPG-073** | Engine phase order | SUPPORTED | Invariant Enforcement |
| **LEG-RPG-159** | Serialization Hardening | SUPPORTED | Full-Entity Serialization Proof |

## Ownership Adjustments

To align with the high-level plan, the following triage is recommended:

- **Phase 7 (Substrate Closure)**: 071, 139, 143 + Hardening rows (001, 004, 006, 066, 068, 070, 073, 159).
- **Phase 8 (Gameplay Recovery)**: 141, 146 (Quests/Sabotage).
- **Phase 9 (Social Intelligence)**: 150, 151 (Rumors/Memory).

## Next Steps

1. Create `docs/engine/phase7_backlog.md` with this triaged set.
2. Update `docs/engine/phase_allocation_map.md` to reflect the new counts.
3. Mark Phase 7 as the "Authoritative Substrate Owner".
