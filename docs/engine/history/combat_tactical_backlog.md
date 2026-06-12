---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 8 Implementation Backlog - Combat & Tactical Semantics

This document defines the frozen row set for Phase 8, focused on moment-to-moment combat legality, tactical decision-making, and local world interaction.

## Phase 8 Backlog (12 Items)

| ID | Atomic Item | Legacy Source | Legacy Test | Status | Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-075** | Reactive cover seeking | `ai/` | `test_reactive_cover.py` | UNSUPPORTED | Tactical positioning. |
| **LEG-RPG-076** | Chokepoint holding | `ai/` | `test_chokepoint.py` | UNSUPPORTED | Spatial tactical behavior. |
| **LEG-RPG-077** | Flanking bracketing | `ai/` | `test_flanking.py` | UNSUPPORTED | Group tactical coordination. |
| **LEG-RPG-094** | Cover bonus (Ranged) | `combat/` | `test_cover.py` | UNSUPPORTED | Environmental combat modifiers. |
| **LEG-RPG-098** | Engagement Hostility | `combat/` | `test_host.py` | UNSUPPORTED | Combat legality trigger. |
| **LEG-RPG-100** | Target Stickiness Bias | `combat/` | `test_sticky.py` | UNSUPPORTED | Tactical focus persistence. |
| **LEG-RPG-102** | Tactical biases | `ai/` | `test_tactics.py` | UNSUPPORTED | Archetype-specific combat choice. |
| **LEG-RPG-103** | Skirmish behavior | `unit/ai/` | `test_skirmish.py` | UNSUPPORTED | Hit-and-run tactics. |
| **LEG-RPG-116** | Strategic pivot (Danger) | `integration/strat/` | `test_danger.py` | UNSUPPORTED | Bounded tactical threat response. |
| **LEG-RPG-117** | Scar detection | `integration/strat/` | `test_scar.py` | UNSUPPORTED | Local hazard/scar interaction. |
| **LEG-RPG-140** | [MERGED into LEG-RPG-001] | - | - | SUPPORTED | Substrate complete. |
| **LEG-RPG-146** | Building Sabotage | `unit/combat/` | `test_sabotage.py` | SUPPORTED | Infrastructure interaction. |

## Excluded Rows (Reallocated to Phase 9)
The following rows were previously in Phase 8 but have been reallocated to **Phase 9 (Strategic Intelligence & Social Narrative)** to preserve Phase 8's focus on local semantics:
- **LEG-RPG-119**: Betrayal (Avenge)
- **LEG-RPG-123**: Refutation drops trust
- **LEG-RPG-125**: Contradiction degrades cert
- **LEG-RPG-141**: Dynamic Quests
- **LEG-RPG-144**: Innate Talents (Genetics)
- **LEG-RPG-145**: Skill scaling (Types)

## Closure Conditions
Every item in this backlog requires:
1. **Contract Enforcement**: Validated via `LegalityService` or `ApplyPipeline` unit tests.
2. **AI Heuristic Proof**: Verified via scenario-based tactical audits in the `CertificationHarness`.
3. **Parity/Divergence Record**: Documented in the Phase 8 Exit Package.
