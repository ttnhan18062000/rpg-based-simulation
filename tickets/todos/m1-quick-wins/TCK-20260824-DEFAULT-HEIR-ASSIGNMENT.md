---
status: active
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
phase: open
date: 2026-08-24
tags: [social]
---

# TCK-20260824-DEFAULT-HEIR-ASSIGNMENT

## Title
Assign Heirs Automatically from Existing Relationship Data

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`heir_entity_id`'s transfer mechanic is fully wired and confirmed live, but nothing ever assigns a heir. The author wants default heir assignment built using `RelationshipService`'s existing per-pair `SocialBond` data.

## Scope
- When an active entity dies (OLD_AGE/COMBAT) with `heir_entity_id==None` and at least one bond to a living entity, add a death-path step in `LifecycleSystem` that assigns a heir via `LifecycleUpdate.heir_entity_id_set` (never direct field mutation)
- Define and document a concrete, deterministic default-heir selection rule from `RelationshipService`'s `SocialBond` data (familiarity/sentiment/last_interaction_tick), with an explicit documented tie-break formula (no hash-order dependence)
- Ensure the heir's `resource_transfers` receives inventory/heirlooms in the same tick, matching the already-proven manual-heir-set behavior in `test_succession_and_heirloom_transfer`
- Preserve the existing None-guard: zero bonds or all bonded targets dead/missing results in no heir assigned, no exception
- Add a new Mechanics Bible subsection or `docs/guidelines/intentional_divergences.md` entry documenting the default-selection rule and exact tie-break formula
- Add a determinism/replay-parity regression test proving heir selection is deterministic given identical bond data

## Out of Scope
- Reviving the superseded V1 `HeroLifecycleSystem`/`SuccessorRegistry` design -- confirmed superseded, cited as prior intent only

## Acceptance Criteria
- [ ] When an active entity dies with `heir_entity_id==None` and at least one bond to a living entity, a heir is assigned and `resource_transfers` occur in the same tick, matching the proven manual-heir test
- [ ] When zero bonds or all bonded targets are dead/missing, no heir is assigned and no exception is raised
- [ ] Heir selection is deterministic given identical bond data, with an explicit documented tie-break rule, covered by a new determinism/replay-parity regression test
- [ ] The default-selection rule is documented in `docs/mechanics/` or `intentional_divergences.md` with the exact tie-break formula matching code

## Related Tickets
- TCK-20260409-PH4-STG2-SUCCESSION-LOGIC
- TCK-20260409-PH1-STG13-14
- TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY

## Related Docs
- docs/engine/authoritative_mutation_pipeline_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/lifecycle_systems/lifecycle.py
- src/systems/lifecycle.py
- src/systems/social_systems/relationships.py
- src/core/state.py
- src/core/updates.py
- src/core/builder.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- 'Strongest bond' and 'default heir' are undefined by the original concern -- `SocialBond` has no kinship field, only familiarity/sentiment/last_interaction_tick; the selection rule is a genuine open design question this ticket must answer
- Whether heir selection runs inline inside `LifecycleSystem.resolve_lifecycle`'s death branch or as a separate earlier phase (given `resolve_lifecycle` currently reads only baseline `heir_entity_id`, not pending `entity_updates` from earlier in the tick) is an open implementation decision
- `layer: systems` was chosen because the primary changed code (`src/systems/lifecycle_systems/`, `src/systems/social_systems/`) lives under the `systems` layer directory; no `social` layer is registered in `registries/layer_registry.jsonl`

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
