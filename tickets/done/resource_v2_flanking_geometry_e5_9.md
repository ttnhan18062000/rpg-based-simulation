# TCK-20260503-FLANKING-GEOMETRY-EXPANSION

## Title
Expanding Authoritative Flanking Geometry (Diagonal & Surround)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Expand the flanking detection logic to include diagonal positions and multi-entity surrounding configurations.

## Scope
- Refactor `LegalityServiceV2.check_flanking` to use a neighbor-density or angular-offset check rather than just cardinal pairs.
- Implement "Surround" bonus for 3+ hostiles regardless of alignment.

## Acceptance Criteria
- [ ] Two entities at (N, E) positions relative to a target must trigger a flanking bonus.
- [ ] Three hostiles surrounding a target must trigger a "Surrounded" debuff in the authoritative combat resolution.

## Related Code Areas
- src/engine/legality.py
- src/engine/combat.py
