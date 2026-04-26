# TCK-20260424-PH2-M4-SOCIAL-CONTINUITY

## Title
Phase 2 Milestone 4: Social Continuity & Nemesis System

## Status
OPEN

## Request Summary
Implement the Nemesis System to enable persistent social interactions. Entities should remember combatants and adjust their tactical behavior based on past harm.

## Scope
- Add grudge tracking to `SocialComponent` and `SocialUpdate`.
- Implement grudge accumulation during combat.
- Integrate grudge-based bias into the cognitive appraisal system.
- Ensure authoritative persistence of social state.

## Acceptance Criteria
- Taking damage from an attacker increases the victim's grudge toward that attacker.
- Entities show increased aggression or panic toward high-grudge neighbors (Nemeses).
- Grudge state persists across ticks and affects target selection.

## Related Tickets
- TCK-20260424-PH2-M3-REGIONAL-SOVEREIGNTY (Done)

## Related Docs
- [rpg_refinement_pillars.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/rpg_refinement_pillars.md)

## Implementation Notes
- Grudge is stored as a float map `EntityID -> Score`.
- High grudge lowers the "Saliency" threshold or increases "Aggression" bias.
