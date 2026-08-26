---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR
phase: done
date: 2026-08-22
tags: [world, content]
---

# TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR

## Title
Retrofit World Grammar Reachability Validation for Quest Content

## Status
DONE

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
- [x] The implementation first resolves, as an explicit documented design decision, which field required_participant_tags is checked against (role_family via RoleSemanticsService, race, or a newly populated matching field) -- the AC does not presume EntityArchetypeDefinition.tags is already populated, since real corpus data confirms it is not.
- [x] A WorldSpec containing a QuestDefinition whose required_participant_tags matches no entity archetype/population reachable in that world produces a WorldGrammarReport/ValidationIssue with a reachability-class rule_id, source_entity = the quest id, source_file mapped to the authoring module, at minimum WARNING severity (elevated to ERROR only when the compiler profile requires it, per docs/mechanics/06_worldbuilding_foundation.md §7).
- [x] A WorldSpec where every quest's required_participant_tags is satisfiable by at least one declared population/archetype produces zero reachability violations for those quests.
- [x] Running the reachability check against the full real content corpus (20+ modules under data/content/world_modules/, not the source idea doc's stale '5+' estimate) as a regression test either passes cleanly or produces a documented, expected violation list that becomes the standing regression baseline.
- [x] The reachability check runs between structural WorldValidator.validate() and WorldCompiler.compile(), does not mutate the input WorldSpec (matching the existing test_validator_does_not_modify_spec pattern), and does not raise/abort on WARNING-only findings.
- [x] Ticket documentation explicitly corrects the record inherited from the source idea doc: TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING is NOT evidence for this rule class (its root cause was decision-pipeline wiring, not content-reachability, and this rule would not have caught it); TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP is the genuine on-point precedent.

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

Implemented per `staging_artifacts/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR/plan.md`
exactly, with one deviation noted (SUB-### ID reassignment) recorded in that plan's own
Deviations section. Summary of what was built:

1. `ValidationIssue` (`src/worldbuilding/validator.py`) gained two additive optional fields,
   `source_entity: Optional[str] = None` and `source_file: Optional[str] = None`.
2. New module `src/worldbuilding/reachability.py` holds three pure/read-only functions —
   `is_reachable`, `resolve_population_tags`, `build_available_participant_tags` — deliberately
   decoupled from `WorldValidationRule` so the downstream `TCK-20260822-QUEST-OPPORTUNITY-
   PREEMIT-VALIDATION` ticket can reuse the core predicate against `AuthoritativeState`-derived
   tag sets.
3. New rule class `ParticipantReachabilityRule` (`rule_id="WORLD-REACH-001"`, WARNING severity,
   `applicable_contexts={WORLD, COMPILE, EXPERIMENT}` — excludes `MODULE`) added to
   `src/worldbuilding/validator.py`. Matches each `QuestDefinition.required_participant_tags`
   against the union of `PopulationSpec.archetype_id -> EntityArchetypeDefinition.role ->
   RoleDefinition.compatible_traits` across `spec.entities`. A population with
   `archetype_id=None` contributes no tags (excluded, not a wildcard). No catalog
   (`catalog_repo=None`) short-circuits to zero issues, never a crash or false positive.
4. `WorldValidator.__init__` gained an optional `catalog_repo: Optional[CatalogRepository] = None`
   parameter and appends `ParticipantReachabilityRule(catalog_repo=catalog_repo)` as its 9th
   default rule. Only `WorldAssemblyValidator.validate()` (`src/worldassembly/resolver.py`) was
   updated to pass `catalog_repo=self.catalog_repo` (its already-held `CatalogRepository`
   instance) — all 6 other real `WorldValidator()` call sites are untouched and remain
   catalog-blind by design (verified: `tests/unit/lab/`, `tests/unit/worldgeneration/` all still
   pass unmodified). The `world_report` dict comprehension in `resolver.py` now also surfaces
   `source_entity`/`source_file`.
5. Dedicated unit tests added in new `tests/unit/worldbuilding/test_world_grammar_reachability.py`
   (rule behavior, no-catalog degradation, `archetype_id=None` handling, non-mutation, severity
   override, default-rule-set guard) and one new test in the existing
   `tests/unit/worldbuilding/test_world_validator.py` (`ValidationIssue` field round-trip).
6. Corpus-wide regression baseline: new `tests/unit/worldbuilding/test_corpus_reachability_
   baseline.py` runs the rule against all 21 real composed worlds under
   `data/worlds/*/resolved/world.resolved.yaml` (real `CatalogRepository("data/content")`) and
   asserts the exact violation set against a committed baseline,
   `tests/fixtures/world_grammar_reachability_baseline.json`. The real first-run result is
   **non-empty by design**: 75 violations across 16 of 21 worlds. As expected from the
   investigation, the bulk are the `opportunistic` (goblin/bandit quests) and `beast` (wolf
   quests) vocabulary gap — neither tag exists anywhere in the real catalog's
   `compatible_traits`/`role_family`/`tags` fields. A smaller, newly-discovered subset are
   `spiritual`/`undead` quests (e.g. `undead_hunt_wraith_patrol`, `spirit_source_trace`) whose
   referenced archetype's actual role trait doesn't match the tag the quest author chose (e.g.
   `undead_sentinel`'s role `sentinel` has `compatible_traits=['undead']`, but the quest requires
   `spiritual`) — a genuine, real content-authoring mismatch the rule correctly surfaces, not an
   implementation bug. This is documented as an accepted baseline, not "fixed" by loosening the
   check or backfilling catalog content (both explicitly out of scope).
7. Docs: `docs/mechanics/06_worldbuilding_foundation.md` §7 gained a "Participant Reachability
   Rule (`WORLD-REACH-001`)" subsection describing the rule, its context scoping, and the accepted
   vocabulary-gap limitation. `docs/parity_ledger/substrate.yaml` gained entry `SUB-387` (status
   `verified`, priority `P2`, consistent with sibling `SUB-385`/`SUB-386`), with a
   `divergence_note` capturing the `opportunistic`/`beast`/mismatched-trait gap.
8. `compiled_quests` (`src/worldbuilding/compiler.py`) remains fully dead code — never attached to
   `AuthoritativeState`. This ticket's validator has no live runtime consumer yet; the corpus
   baseline reflects authoring-time content quality, not currently-live, broken runtime behavior.

**AC6 record correction (ticket documentation)**: `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` is
**not** evidence for this rule class — its root cause was decision-pipeline wiring (no
`GoalKind`/scorer/phase routed to `GuildAction.visit()`), not a content-reachability mismatch, and
this validator would not have caught it. `TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP` is a
genuine but **general-failure-class** precedent, not a literal catch: its `q_slime_cull` bug lives
entirely in `src/quests/generator.py`'s `QuestTemplate.target_kind`/`race_id` matching, a fully
separate legacy quest-generation pipeline from `WorldSpec.QuestDefinition.
required_participant_tags`/`WorldCompiler.compile()` — this validator never touches
`QuestTemplate` or `race_id` matching, so it would not have mechanically caught that specific bug.

**Deviation from plan (architecture-review directive)**: the plan assumed the next parity-ledger ID
after `SUB-384` would be `SUB-385`; by implementation time `substrate.yaml` already contained
`SUB-385` and `SUB-386` (landed by other concurrent work). Used the real next available ID,
`SUB-387`, instead — see `staging_artifacts/.../plan.md`'s Deviations section.

## Test Summary

`pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/integration/worldassembly/ -m "not slow" -q`
— 318 passed, 33 deselected (includes 2 new test files: `test_world_grammar_reachability.py`,
`test_corpus_reachability_baseline.py`, and 1 extended test in `test_world_validator.py`).

`pytest tests/unit/lab/ tests/unit/worldgeneration/ -m "not slow" -q` — 156 passed (confirms the 6
untouched `WorldValidator()` call sites are unaffected).

`pytest tests/unit/content/ tests/unit/content_semantics/ -m "not slow" -q` — 248 passed.

## Files Changed

- `src/worldbuilding/validator.py` — `ValidationIssue.source_entity`/`.source_file`;
  `ParticipantReachabilityRule`; `WorldValidator.__init__` `catalog_repo` param + 9th default rule.
- `src/worldbuilding/reachability.py` — new module (`is_reachable`, `resolve_population_tags`,
  `build_available_participant_tags`).
- `src/worldassembly/resolver.py` — `WorldValidator(catalog_repo=self.catalog_repo)` wiring;
  `world_report` comprehension gains `source_entity`/`source_file`.
- `tests/unit/worldbuilding/test_world_grammar_reachability.py` — new.
- `tests/unit/worldbuilding/test_world_validator.py` — extended (`ValidationIssue` round-trip test).
- `tests/unit/worldbuilding/test_corpus_reachability_baseline.py` — new.
- `tests/fixtures/world_grammar_reachability_baseline.json` — new (committed baseline).
- `docs/mechanics/06_worldbuilding_foundation.md` — new §7 subsection.
- `docs/parity_ledger/substrate.yaml` — new entry `SUB-387`.
- `staging_artifacts/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR/plan.md` — Deviations
  section added (SUB-### ID reassignment).
- `staging_artifacts/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR/investigation.md` — created
  during this run's earlier Investigate phase; uncommitted, part of this run's changeset.
- `staging_artifacts/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR/test_plan.md` — created
  during this run's earlier Plan phase; uncommitted, part of this run's changeset.
- `tickets/inprogress/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR.md` — this file.

## Completion Summary

Added a new `WORLD-REACH-001` `WorldValidator` rule that checks each quest's
`required_participant_tags` against reachable populations' `compatible_traits`
(`archetype_id -> role -> compatible_traits`), wired via an optional `catalog_repo` constructor
parameter that defaults to `None` everywhere except `WorldAssemblyValidator.validate()`. Extended
`ValidationIssue` with `source_entity`/`source_file`, added dedicated unit tests plus a corpus-wide
regression baseline (75 documented, expected violations across 16 of 21 real worlds, driven by a
known `opportunistic`/`beast` vocabulary gap and a few mismatched `spiritual`/`undead` tags — not a
rule defect), and updated the Mechanics Bible and parity ledger (`SUB-387`) accordingly. Also
corrected the ticket record per AC6 on which prior bug this rule class actually would have caught.
