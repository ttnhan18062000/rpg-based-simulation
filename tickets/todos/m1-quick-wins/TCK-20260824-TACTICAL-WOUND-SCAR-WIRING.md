---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260824-TACTICAL-WOUND-SCAR-WIRING
phase: open
date: 2026-08-24
tags: [combat]
---

# TCK-20260824-TACTICAL-WOUND-SCAR-WIRING

## Title
Wire Structured Wound/Scar Data into Tactical Decision-Making

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The Tactical Decision System already reacts to raw HP ratio, but it never reads the structured WoundState/ScarState data that already exists. The author wants the real structured data wired in.

## Scope
- Make TacticalDecisionSystem read entity.combat.wounds/.scars via the existing WoundService.get_wound_stat_penalties/get_scar_stat_penalties aggregator (not re-derived inline)
- An entity with an active WoundState of sufficient severity triggers cover-seeking/retreat behavior earlier/independently of the existing hp_percent checks (tactical.py:442-469), verified by a test with high hp_percent but a severe wound
- PROTECTOR-role 'guard wounded ally' selection (tactical.py:492-519) considers ally wound/scar severity as an additional signal, not just hp_ratio
- A scarred entity exhibits a durable behavior difference from an unwounded entity at the same hp_ratio
- Add a new parity_ledger entry or explicit extension note for the new wound/scar tactical branch, distinct from COMB-268's existing hp-ratio-only verified entry

## Out of Scope
- Duplicating the already-correct wound/scar stat-penalty pipeline (SkillScalingService.get_effective_stats -> apply.py) -- this ticket is scoped to decision-making (retreat/cover/guard) only
- Any change to the underlying WoundState/ScarState data model -- this ticket depends on, and must be re-validated against, whatever C2/C3/C4 land

## Acceptance Criteria
- [ ] An entity with active WoundState of sufficient severity triggers cover-seeking/retreat behavior in TacticalDecisionSystem earlier/independently of existing hp_percent checks, verified by a test with high hp_percent but a severe wound
- [ ] PROTECTOR-role 'guard wounded ally' selection considers ally wound/scar severity as an additional signal, not just hp_ratio
- [ ] A scarred entity exhibits a durable behavior difference from an unwounded entity at the same hp_ratio
- [ ] New reads reuse WoundService.get_wound_stat_penalties/get_scar_stat_penalties rather than re-deriving inline

## Related Tickets
- TCK-20260429-E3-MISSING-LOGIC
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS
- TCK-20260619-PARITY-P0-BUGS
- TCK-20260824-WOUND-THRESHOLD-DECISION
- TCK-20260824-WOUND-PENALTY-FORMULA-WIRING
- TCK-20260824-WOUND-HEALING-DECISION

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/tactical.py
- src/core/state.py
- src/engine/rpg_depth.py
- src/engine/combat.py
- src/engine/apply.py

## Assumptions / Open Questions
- Explicit blocking dependency on TCK-20260824-WOUND-THRESHOLD-DECISION (C2), TCK-20260824-WOUND-PENALTY-FORMULA-WIRING (C3), and TCK-20260824-WOUND-HEALING-DECISION (C4) landing first, since all three touch the same underlying WoundState/ScarState data model this ticket reads -- if those tickets change the data shape, this ticket's design must be re-validated

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
