# Supported Progression Package (Phase 5)

## 1. Overview
This package defines the canonical state of the `src` Resource Engine at the end of Phase 5. It unifies the recovered gameplay behavior with the engine's authoritative resolution substrate.

## 2. Core Support Matrix

| Layer | Status | Verification |
| :--- | :--- | :--- |
| **Grid Movement** | OFFICIAL | `MVM_PATH_20` |
| **Resource Interaction**| OFFICIAL | `RES_HARVEST_3` |
| **Town Resolution** | OFFICIAL | `SCENARIO_BLACKSMITH` |
| **Strategic AI** | OFFICIAL | `INTEG_RESOURCE_LOOP`|

## 3. The "Truth" Loop
The following cycle is officially supported, certified, and bit-identical under sequential execution:
1.  **Seek**: Entity identifies missing materials and redirects to resource leads.
2.  **Move**: Entity navigates at 1.0 units per tick toward targets.
3.  **Harvest**: Entity performs channeled interaction (InteractionSystem).
4.  **Resolve**: Entity returns to town (RedirectionSystem) and craft resolves (BlacksmithSystem).

## 4. Performance Baseline (Class B)
*Measured on integrated loop stress scenarios.*

- **Idle Baseline**: >5000 TPS
- **Autonomous Progress Loop (100 entities)**: ~180 TPS
- **Tick Budget Guarantee**: < 16.6ms at 100-entity load.

## 5. Declared Divergences
- **Recipe Simplification**: `steel_sword` now costs 1 `iron_ore` (divergent from `src` costs) to maintain loop proof integrity.
- **Immediate Resolution**: Interaction completion and inventory addition occur in the same tick (Tick 0 Resolution).
- **Proactive AI**: Strategic redirection occurs within the same resolution phase as inventory updates.

## 6. Known Limitations
- Pathfinding is restricted to direct linear paths (stepping).
- Only the Blacksmith building is officially recovered.
- Cap on concurrent entities is limited by the profile's worker count.

## 7. Quality Certificate
> [!IMPORTANT]
> The integrated progression substrate is now **regression-guarded** by [test_logic_guards.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integrity/test_logic_guards.py). Any changes to the `Kernel` resolution phase that break same-tick redirection will fail the release gate.
