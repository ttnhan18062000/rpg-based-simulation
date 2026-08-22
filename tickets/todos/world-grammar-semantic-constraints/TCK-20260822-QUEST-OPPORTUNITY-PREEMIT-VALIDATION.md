---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION
phase: open
date: 2026-08-22
tags: [world, content, determinism]
---

# TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION

## Title
Pre-Emit Grammar Validation for Procedurally-Generated Quest Opportunities

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Give QuestOpportunityGenerator a lightweight pre-emit check, reusing the World Grammar rule engine from the reachability-validator ticket, before a QuestOpportunity is added to an entity's opportunity pool. Investigation confirms QuestOpportunityGenerator (`src/domains/world_emergence/services.py`) is a fully distinct code path from QuestGenerator/GuildAction.visit()/QuestState -- different graphify community (364 vs 935) -- so the two TCK-20260807 tickets cited elsewhere as proof-bugs for this problem class do not actually cover this code path and must not be treated as direct precedent here. The concrete integration point is `WorldEmergencePhase.execute()` step 5b (`src/domains/world_emergence/phase.py` lines 61-75, 134), which currently assigns generated quest_opps to `update.quest_registry_add` with no filtering step. This ticket has a hard sequencing dependency on the reachability-validator ticket: no runtime-callable grammar API exists yet, and `src/worldbuilding/validator.py` is confirmed build-time/WorldSpec-only and cannot detect runtime drift (a faction losing territory, a resource depleting after play), so it cannot substitute.

## Scope
- Define and implement a pre-emit validation call site in `WorldEmergencePhase.execute()` step 5b that filters generated QuestOpportunity objects before they reach `update.quest_registry_add`.
- Reuse the runtime-callable rule API from the reachability-validator ticket, applied against AuthoritativeState rather than WorldSpec.
- Cover at minimum: faction-coherence rejection (QuestOpportunity referencing a faction with zero territorial presence) and resource-availability rejection (objective_chain referencing a depleted, quantity==0 resource node).
- Preserve QuestOpportunityGenerator's documented read-only, deterministic, no-uuid/no-time-seeding contract in the new check.
- Define explicit behavior for faction_source=None (current default for world-event-triggered opportunities) in the faction-coherence check.
- Add fixtures and tests for the negative paths (dispossessed-faction state, depleted-resource state), since none exist in the current test harness.

## Out of Scope
- Any change to `src/worldbuilding/validator.py` itself -- investigation confirmed it is build-time/WorldSpec-only and the wrong tool for runtime AuthoritativeState checks; this ticket only calls into the reachability-validator ticket's rule API from the runtime phase, it does not modify the spec-time validator.
- Building the underlying grammar rule engine/API itself -- that is the reachability-validator ticket's scope; this ticket only wires a pre-emit call site around an API that must already exist.
- Citing TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING or TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP as direct precedent for this concern -- investigation confirmed both concern QuestState via GuildAction.visit(), a fully distinct code path from QuestOpportunityGenerator; they inform the reachability-validator ticket only, not this one.
- Any performance-optimization work beyond confirming the check stays within WorldEmergencePhase's existing `metric_counters['world_emergence_ms']` tick budget -- deeper optimization, if the naive check proves too costly, is a follow-up, not baseline scope.

## Acceptance Criteria
- [ ] This ticket is explicitly blocked on, and sequenced after, the World Grammar reachability-validator ticket landing a runtime-callable rule API -- WorldValidator as it exists today is spec-time/WorldSpec-only and cannot substitute; implementation must not begin until that API exists.
- [ ] Calling the pre-emit validation API with a QuestOpportunity referencing a faction with zero territorial presence in current AuthoritativeState returns an explicit rejection (not a silent None-passthrough), and that opportunity is excluded from `update.quest_registry_add` in `WorldEmergencePhase.execute()` step 5b.
- [ ] Calling it with a QuestOpportunity whose objective_chain references a depleted (quantity==0) resource node returns a rejection, and the opportunity is excluded from `quest_registry_add`.
- [ ] A QuestOpportunity that passes all grammar checks is unaffected: `quest_registry_add` still contains it, byte-identical to current output -- existing tests `test_resource_crisis_quest_generated_on_depletion` and `test_threat_response_quest_generated_on_high_severity` continue passing unmodified.
- [ ] The validation call is deterministic and read-only: identical (QuestOpportunity, AuthoritativeState) inputs give identical verdicts across repeated calls, and AuthoritativeState is unmutated after the call, preserving QuestOpportunityGenerator's documented read-only/no-uuid/no-time-seeding contract.
- [ ] Defined, documented behavior exists for the case where faction_source is None (current default for world-event-triggered opportunities) in the faction-coherence check -- unspecified in the source idea doc and resolved as part of this ticket's design.

## Related Tickets
- TCK-20260619-E23A-QUEST-OPPORTUNITY
- TCK-20260619-E23B-QUEST-LIFECYCLE
- TCK-20260702-PLANS-IDEA-REFRESH
- TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR

## Related Docs
- docs/plans/idea_world_grammar_semantic_constraints.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/world_emergence/services.py
- src/domains/world_emergence/phase.py
- src/core/models/quests.py
- src/worldbuilding/validator.py
- tests/unit/quest/test_quest_generation.py
- tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py
- tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py

## Assumptions / Open Questions
- Hard dependency on the reachability-validator ticket: the callable World Grammar API does not exist anywhere yet; this ticket cannot be implemented until that ticket lands a runtime-callable rule engine that operates against AuthoritativeState (not just WorldSpec).
- The source idea doc's own open questions -- Python predicates vs. YAML rules, and whether runtime checks can be made cheaper than build-time ones -- are unresolved and material, given WorldEmergencePhase's tick-budget tracking (E23 runs every tick).
- reward_spec['faction_rep'] and the faction_source=None default (world-event-triggered opportunities currently never set faction_source) need defined behavior for a faction-coherence check; not specified in the source proposal.
- No existing test harness constructs a QuestOpportunity against a genuinely depleted-resource or dispossessed-faction state; new fixtures are needed for the negative-path acceptance criteria.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
