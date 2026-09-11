---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-AUDIT-D05-ENTITY-DIFF
phase: done
date: 2026-06-19
tags: [audit, entity-differentiation, personality, class, behavioral-arcs]
---

# TCK-20260619-AUDIT-D05-ENTITY-DIFF

## Title
Audit D05 — Entity Differentiation

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Observe whether entity role (HERO/MONSTER/CITIZEN/WORKER/GUARD/SHOPKEEPER) and personality traits (OCEAN-derived: bravery, greed, curiosity, industry, sociability) produce observably different behavioral arcs in the simulation. D06 confirmed behavioral activity is sustained from tick 201 onward; D05 checks whether that activity is differentiated or uniform.

## Scope
- Seeds 42 and 137, 400 ticks (covers post-lock active window 201–400)
- Per-entity: role, personality trait distribution, project kinds, survival outcomes
- Assess: does personality bias (max 0.25/trait in AdventureRouteScorer) produce route selection differentiation against hunger urgency dominance?

## Out of Scope
- Code changes
- Economic/crafting differentiation (blocked by D06 F1)

## Acceptance Criteria
1. D05 audit document written to `docs/audits/D05_entity_differentiation.md`
2. Ticket moved to done, working log updated

## Related Tickets
- TCK-20260619-AUDIT-D06-LONGRUN (F1 — survival-only routes; context for D05 scope)
- TCK-20260618-AUDIT-D03-BEHAVIOR

## Related Docs
- `docs/audits/D06_longrun_health.md`
- `docs/audits/D01_rpg_feature_impact.md` (§Personality calibration PARTIAL)
- `docs/mechanics/04_strategic_cognition.md`

## Assumptions / Open Questions
- Personality bias (0.25 max) may be too weak to overcome hunger urgency — this is a key finding to confirm or deny
- Per-entity state readable from chunk_0000.json / chunk_0003.json in the run output

## Implementation Notes
Run: `python3 -m src cli --ticks 400 --seed 42` and `--seed 137`
Extract entity personality traits and project kinds from chunk data.

## Files Changed
- `docs/audits/D05_entity_differentiation.md` (new)
- `tickets/done/TCK-20260619-AUDIT-D05-ENTITY-DIFF.md`

## Completion Summary
(fill on completion)
