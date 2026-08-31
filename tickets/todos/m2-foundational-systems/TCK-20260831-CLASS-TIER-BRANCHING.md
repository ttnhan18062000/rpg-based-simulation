---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260831-CLASS-TIER-BRANCHING
phase: open
date: 2026-08-31
tags: [progression]
---

# TCK-20260831-CLASS-TIER-BRANCHING

## Title
Design and build mutually-exclusive class-tier branch choices

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build Diversity is, in the atlas's own words, a genuine gap, not a disconnection — "the one place on this list where the honest answer is design and build it, not wire it up." class_id is never reassigned anywhere in the live codebase, BreakthroughService perks are always-additive (not mutually-exclusive branches) and nothing in production ever grants one, and EvolutionSystem's kind_set mutation is a single linear chain, not a branching pattern — idea 11 needs to generalize that pattern, not copy it.

## Scope
- Define a class-tier registry with >=2 mutually-exclusive next-tier options per base class.
- Add a new typed update field (e.g. class_id_set on IdentityUpdate, mirroring EvolutionSystem's kind_set pattern) that authoritatively mutates class_id at a defined milestone via the apply path.
- Record the divergence from PROG-108's spawn-only class_id assignment law in docs/guidelines/intentional_divergences.md.
- Verify a tier's stat bonuses do not decrease average combat win-rate via a metamorphic-style comparison.
- Add a test analogous to test_goblin_evolution proving two entities with identical starting class/race but different branch-selection inputs diverge in class_id/tier state.

## Out of Scope
- Re-fixing BreakthroughService's bonus application — already closed by TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION; the atlas's older 'needs a real body' note is stale, do not re-fix.
- Making breakthroughs mutually exclusive — they remain always-additive perks, a separate concept from this ticket's branch tiers.

## Acceptance Criteria
- [ ] A class-tier registry exists defining >=2 mutually-exclusive next-tier options per base class (not a single linear chain).
- [ ] A new typed update field (e.g. class_id_set on IdentityUpdate, mirroring EvolutionSystem's kind_set pattern) authoritatively mutates class_id at a defined milestone via the apply path, with the divergence from PROG-108's spawn-only law recorded in docs/guidelines/intentional_divergences.md.
- [ ] Two entities with identical starting class/race but different branch-selection inputs end up with different class_id/tier state, verified by a test analogous to test_goblin_evolution.
- [ ] A tier's stat bonuses do not decrease average combat win-rate, verified via a metamorphic-style comparison.

## Related Tickets
- TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION
- TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION
- TCK-20260824-ALLOCATE-AP-BRANCH-DECISION

## Related Docs
- docs/parity_ledger/progression.yaml
- docs/mechanics/attribute_progression_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/progression/breakthroughs.py
- src/engine/evolution.py
- src/engine/rpg_depth.py
- src/core/classes.py
- src/core/updates.py

## Assumptions / Open Questions
- No numeric anchor exists anywhere for branch-tier stat bonuses — genuinely free creative territory needing explicit authored values per Content & Balance Requirements.
- The first real sub-scope may need to be defining the choice-surface shape itself before any application logic.
- `layer: core` was chosen over `engine` or a new `progression` layer because the affected code spans src/core/ (classes.py, updates.py), src/engine/ (evolution.py, rpg_depth.py), and src/progression/ (breakthroughs.py); no `progression` layer is currently registered in registries/layer_registry.jsonl, and `core` best matches the entity/class-identity primitive this ticket adds (class_id_set on IdentityUpdate). Revisit if a dedicated `progression` layer gets registered later.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
