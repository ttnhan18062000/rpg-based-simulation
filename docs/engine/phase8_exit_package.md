# Phase 8 Exit Package: Combat, Tactical, & Local World Closure

This package formalizes the completion of Phase 8 and establishes the baseline for Phase 9.

## 1. Phase 8 Completion Statement
Phase 8 has successfully recovered the authoritative moment-to-moment gameplay layer. The engine now supports deterministic combat resolution, bounded tactical AI decision-making, and local world-interaction semantics (terrain, buildings, LoS).

## 2. Settled Contracts
The following contracts are now frozen and authoritative:
- **Combat Resolution**: [Fractional Armor Mitigation Law](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/combat_resolution_contract.md).
- **Tactical AI**: [Bounded Pursuit & Retreat Semantics](../engine/tactical_contract.md).
- **Local World**: [Spatial Legality & LoS Blocking](../engine/local_world_interaction_contract.md).

## 3. Proof Index
Evidence of recovery is consolidated in the [Phase 8 Proof Bundle](../engine/phase8_proof_bundle.md).
- **100% Pass Rate** on Tactical and World interaction contract tests.
- **Bit-Identical Parity** on the core damage resolution formula.
- **Ratified Divergences** for AI prioritization and retreat thresholds.

## 4. Phase 9 Readiness & Assumptions
Phase 9 (Strategic & Social Expansion) is now permitted to assume the following local gameplay truth:
1. **Local Combat is Authoritative**: Strategic AI does not need to simulate combat outcomes; it can rely on the engine's deterministic resolution.
2. **Tactical AI is Self-Contained**: The local tactical layer handles pursuit and engagement; Phase 9 should focus on high-level redirection and goal-setting.
3. **Environment Constraints are Absolute**: Movement and LoS are enforced by `LegalityServiceV2`; strategic paths must respect these local blockages.

## 5. Unsupported Remainder
- **Multi-Region Coordination**: High-level troop movement across region boundaries remains simulated/stubbed.
- **Complex Progression**: Character classes, skill trees, and equipment-based breakthroughs are pending Phase 10.
- **Dynamic Terrain**: Destruction of walls or creation of bridges is not yet supported.

---
*Ratified on 2026-04-22 as the authoritative Phase 8 Exit Gate.*
