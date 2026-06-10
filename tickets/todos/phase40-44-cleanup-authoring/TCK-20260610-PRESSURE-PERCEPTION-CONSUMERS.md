# TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS

## Title
Connect MotivationPressureResolver and PerceptionGate to existing decision points

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 42.3. `MotivationPressureResolver` (42.1) and `PerceptionGate` (42.2) exist but are not yet wired into simulation decision points. This ticket adds them as scoring inputs to five high-impact decision locations: combat target eligibility, territorial response, avoidance/flee decision, resource-seeking priority, service/trade seeking. The flow is: perception gate → relation projection → motivation pressure → target/goal scoring. No existing decision point is rewritten — pressures are additive scoring inputs.

## Scope
- Combat target eligibility: entity cannot target unperceived enemy (`PerceptionGate.can_perceive()` gates hostiles list in `src/engine/tactical.py`)
- Territorial animal scores intruder higher inside territory when `territory_pressure` is elevated
- Merchant avoids high-threat target when `safety_pressure` is high (flee/avoidance decision)
- Guard scores duty-related threats higher when `duty_pressure` is elevated
- Resource-seeking priority weighted by `hunger_pressure` / `wealth_pressure`
- Do NOT rewrite the entire behavior engine — insert pressure as a multiplier/gate at existing scoring callsites

## Out of Scope
- Adding new goal types or behavior trees
- Rewriting tactical decision engine
- Scripted behavior per archetype

## Acceptance Criteria
- [ ] Unperceived enemy cannot be selected as combat target
- [ ] Territorial animal scores intruder higher when territory_pressure elevated
- [ ] Merchant flee decision triggered by safety_pressure above threshold
- [ ] Guard prioritises duty-related threat when duty_pressure elevated
- [ ] Existing combat tests still pass
- [ ] New behavioral tests are deterministic and small
- [ ] No direct scripted behavior added (pressure-based scoring only)

## Related Tickets
- TCK-20260610-MOTIVATION-PRESSURE-RESOLVER (prerequisite)
- TCK-20260610-SENSE-PERCEPTION-GATE (prerequisite)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md`
- `docs/engine/kernel.md`

## Related Code Areas
- `src/engine/tactical.py` — hostile target selection (primary consumer)
- `src/engine/flee_logic.py` or equivalent — flee/avoidance decision
- `src/engine/resource_seeking.py` or equivalent — resource priority

## Assumptions / Open Questions
- Verify exact callsite locations in `tactical.py` for hostile list construction before writing integration points.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
