---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR
phase: open
date: 2026-08-22
tags: [world, content]
---

# TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR

## Title
Retrofit World Grammar Reachability Validation for Quest Content

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a semantic validation layer, running after structural validation, that checks whether authored world/quest content forms reachable causal chains -- reframed by the author from a pre-authoring gate (moot, since E13/E23 content already shipped) to retrofit validation plus regression prevention, scoped at minimum to a reachability rule. Investigation confirms WorldCompiler.compile() already has a genuine, silent gap here: required_location_tags is checked (WARNING-only), but required_participant_tags is read from QuestDefinition and stuffed into metadata with zero verification against any entity/population data. However, the real content corpus (data/content/entities/entity_archetypes.yaml) never populates a tags field on archetypes, so a naive tags-to-tags match would find nothing to check against -- resolving which field to match against is an open design decision this ticket must make, not an assumption it can carry in. The source idea doc's framing that TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING proves this rule class is incorrect: that bug's root cause was decision-pipeline wiring (no GoalKind/scorer/phase routed to GuildAction.visit()), not a content-reachability mismatch, and this rule would not have caught it. TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP (q_slime_cull targeting a nonexistent slime archetype) is the genuine on-point precedent this rule class would catch.

## Scope
- Extend the existing WorldValidator rule-engine extension point (src/worldbuilding/validator.py, ValidationIssue/WorldValidationRule/ValidationContext pattern) with a new reachability-class rule covering QuestDefinition.required_participant_tags.
- Resolve, as an explicit design decision documented in the ticket, which field required_participant_tags is matched against (e.g. role_family via RoleSemanticsService, race, or a newly introduced/populated matching field) -- do not assume EntityArchetypeDefinition.tags is already populated.
- Slot the new check into the existing 3-level gate model (Pydantic -> Structural/Spatial-Link -> Runtime-Gated Compiler) described in docs/mechanics/06_worldbuilding_foundation.md §7, running it between WorldValidator.validate() and WorldCompiler.compile().
- Produce a WorldGrammarReport/ValidationIssue shape per docs/plans/idea_world_grammar_semantic_constraints.md for reachability violations, with rule_id, source_entity, source_file, and severity.
- Run the check as a regression test against the full real corpus under data/content/world_modules/ (20+ modules) and record the resulting baseline (clean pass or a documented expected-violation list).
- Correct the ticket/doc record on which prior bug this rule class actually would have caught, per investigation findings.

## Out of Scope
- Speculatively populating EntityArchetypeDefinition.tags (or any content field) across the full data/content/entities/ corpus as a mass content-authoring backfill -- that is a separate, larger content-authoring effort; this ticket only builds the validation mechanism and resolves the matching-field decision at the design/schema level, backfilling at most the minimum fixtures needed for its own tests.
- Pre-authoring/authoring-time gating (the original idea doc's framing) -- moot since E13/E23 content already shipped; this ticket is retrofit validation only.
- Runtime/post-authoring drift detection against AuthoritativeState (faction losing territory, resource depletion after play) -- that is the separate QUEST-OPPORTUNITY-PREEMIT-VALIDATION ticket's concern, which is blocked on this ticket landing first.
- Any semantic rule beyond the reachability rule (e.g. faction coherence, resource-availability grammar) -- explicitly out per the reframed 'at minimum the reachability rule' scope.
- Promoting docs/plans/idea_world_grammar_semantic_constraints.md's maturity/authority frontmatter beyond citing it as a related doc -- a full doc-authority promotion is a separate docs task.

## Acceptance Criteria
- [ ] The implementation first resolves, as an explicit documented design decision, which field required_participant_tags is checked against (role_family via RoleSemanticsService, race, or a newly populated matching field) -- the AC does not presume EntityArchetypeDefinition.tags is already populated, since real corpus data confirms it is not.
- [ ] A WorldSpec containing a QuestDefinition whose required_participant_tags matches no entity archetype/population reachable in that world produces a WorldGrammarReport/ValidationIssue with a reachability-class rule_id, source_entity = the quest id, source_file mapped to the authoring module, at minimum WARNING severity (elevated to ERROR only when the compiler profile requires it, per docs/mechanics/06_worldbuilding_foundation.md §7).
- [ ] A WorldSpec where every quest's required_participant_tags is satisfiable by at least one declared population/archetype produces zero reachability violations for those quests.
- [ ] Running the reachability check against the full real content corpus (20+ modules under data/content/world_modules/, not the source idea doc's stale '5+' estimate) as a regression test either passes cleanly or produces a documented, expected violation list that becomes the standing regression baseline.
- [ ] The reachability check runs between structural WorldValidator.validate() and WorldCompiler.compile(), does not mutate the input WorldSpec (matching the existing test_validator_does_not_modify_spec pattern), and does not raise/abort on WARNING-only findings.
- [ ] Ticket documentation explicitly corrects the record inherited from the source idea doc: TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING is NOT evidence for this rule class (its root cause was decision-pipeline wiring, not content-reachability, and this rule would not have caught it); TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP is the genuine on-point precedent.

## Related Tickets
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING
- TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP
- TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP
- TCK-20260702-PLANS-IDEA-REFRESH
- TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION
- TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md
- docs/plans/idea_world_grammar_semantic_constraints.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldbuilding/validator.py
- src/worldbuilding/compiler.py
- src/worldbuilding/schema.py
- src/content/schema.py
- src/content_semantics/role.py
- src/content_semantics/faction.py
- data/content/entities/entity_archetypes.yaml
- data/content/world_modules/frontier_village_core.yaml
- data/content/world_modules/forest_warden_grove.yaml
- tests/unit/worldbuilding/test_world_validator.py
- tests/unit/worldbuilding/test_quest_definition.py

## Assumptions / Open Questions
- Open design decision not resolved by any code today: which field (role_family via RoleSemanticsService, race, or a newly populated EntityArchetypeDefinition.tags) required_participant_tags should be matched against; real archetype data has no populated tags field, so a naive tags-to-tags match would find zero matches everywhere and produce a useless report unless resolved first.
- Retrofitting against 20+ already-shipped modules risks a large first-run violation count; a baseline/suppression mechanism or WARNING-only initial rollout may be needed to avoid a false 'everything is broken' report.
- The rule-engine's programmatic API shape decided here directly constrains the downstream QUEST-OPPORTUNITY-PREEMIT-VALIDATION ticket -- the API must be scoped explicitly, not just a CLI/report output.
- Semantic search tools (MCP search_docs, knowledge_search.py) were unavailable during the source investigation (offline/index-not-found); findings relied on graphify and direct file reads only -- re-run semantic search once available to confirm no additional prior art was missed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
