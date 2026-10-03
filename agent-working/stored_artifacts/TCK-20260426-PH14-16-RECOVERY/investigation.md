---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260426-PH14-16-RECOVERY
artifact_type: investigation
tags: [ph14, recovery]
---

# Investigation: RPG-Core Logic Gaps (Phases 14-16)

## Findings

### 1. Opportunity Attack (OA) Gap
- **Legacy Behavior**: Multiple enemies can trigger OAs against a single target moving through their reach in one tick.
- **V2 State**: Only the first hostile detected was triggering OA.
- **Solution**: `LegalityService` must return a deterministic list of all engaged hostiles. `MovementSystem` must generate a multi-intent combat update.

### 2. Social System Gap
- **Legacy Behavior**: Familiarity and Sentiment are tracked as directed bonds. CHA affects the rate of familiarity gain.
- **V2 State**: Using a single `trust_history` score as a proxy for all social dynamics.
- **Solution**: Implement a first-class `SocialBond` record tracking `familiarity` and `sentiment` separately. Update appraisal systems to emit bond updates.

### 3. AoE Combat Gap
- **Legacy Behavior**: AoE attacks have a center legality check (LOS/Range) and a secondary splash effect (radius/damage).
- **V2 State**: AoE was partially simulated via individual attacks or not authoritative.
- **Solution**: Implement `verify_aoe_legality` for impact centers and `extra_damage` aggregation in the `ApplyPath` for splash consequences.

### 4. Post-Implementation Audit Finding
- **Bug**: Primary target of AoE was taking 0 damage due to splash skip logic and missing `hp_delta` in `resolve_aoe_attack`.
- **Correction**: Updated `resolve_aoe_attack` to accept `defender` and calculate primary impact damage.
