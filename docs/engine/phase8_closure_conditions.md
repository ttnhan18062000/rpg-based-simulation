---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 8 Closure Conditions

This document defines the exact finish lines for every Phase 8 row.

## Combat Legality & Outcomes

### LEG-RPG-098: Engagement Hostility
- **Condition**: `LegalityService` must correctly identify engagement triggers between hostile factions and neutral entities.
- **Verification**: `test_engagement_legality.py` must pass with 100% correctness.

### LEG-RPG-094: Cover bonus (Ranged)
- **Condition**: Ranged combat resolution must account for environmental cover modifiers in the `ApplyPipeline`.
- **Verification**: Differential test comparing damage outcomes with and without cover must match legacy semantics.

## Tactical Behavior

### LEG-RPG-100: Target Stickiness Bias
- **Condition**: Tactical evaluators must persist on a primary target unless a threshold-breaking threat or opportunity arises.
- **Verification**: `test_tactical_stickiness.py` scenario audit.

### LEG-RPG-102: Tactical biases
- **Condition**: Different unit archetypes (Warrior vs Scout) must exhibit distinct tactical prioritization (e.g., Aggressive vs Cautious).
- **Verification**: Archetype-weighted utility scores in `CertificationHarness`.

### LEG-RPG-075, 076, 077: Spatial Tactics (Cover, Chokepoint, Flanking)
- **Condition**: Local decision logic must recognize and utilize spatial features (terrain markers) to optimize survival or lethality.
- **Verification**: Pathfinding/positioning audits in `tests/scenarios/`.

## World Interaction

### LEG-RPG-117: Scar detection
- **Condition**: Entities must perceive and react to local "Scars" (environmental damage) during tactical movement.
- **Verification**: `test_scar_interaction_legality.py`.

### LEG-RPG-146: Building Sabotage
- **Condition**: (ALREADY SUPPORTED) - Maintain contract integrity through Phase 8.

## Phase Exit Requirements
- All Phase 8 rows marked `SUPPORTED` in the ledger.
- Phase 8 Exit Package published.
- Support Boundary ratified from certification evidence.
