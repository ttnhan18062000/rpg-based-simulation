---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION
phase: done
date: 2026-08-22
tags: [world, content, determinism]
---

# TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION

## Title
Pre-Emit Grammar Validation for Procedurally-Generated Quest Opportunities

## Status
DONE

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
- [x] This ticket is explicitly blocked on, and sequenced after, the World Grammar reachability-validator ticket landing a runtime-callable rule API -- WorldValidator as it exists today is spec-time/WorldSpec-only and cannot substitute; implementation must not begin until that API exists.
- [x] Calling the pre-emit validation API with a QuestOpportunity referencing a faction with zero territorial presence in current AuthoritativeState returns an explicit rejection (not a silent None-passthrough), and that opportunity is excluded from `update.quest_registry_add` in `WorldEmergencePhase.execute()` step 5b.
- [x] Calling it with a QuestOpportunity whose objective_chain references a depleted (quantity==0) resource node returns a rejection, and the opportunity is excluded from `quest_registry_add`.
- [x] A QuestOpportunity that passes all grammar checks is unaffected: `quest_registry_add` still contains it, byte-identical to current output -- existing tests `test_resource_crisis_quest_generated_on_depletion` and `test_threat_response_quest_generated_on_high_severity` continue passing unmodified.
- [x] The validation call is deterministic and read-only: identical (QuestOpportunity, AuthoritativeState) inputs give identical verdicts across repeated calls, and AuthoritativeState is unmutated after the call, preserving QuestOpportunityGenerator's documented read-only/no-uuid/no-time-seeding contract.
- [x] Defined, documented behavior exists for the case where faction_source is None (current default for world-event-triggered opportunities) in the faction-coherence check -- unspecified in the source idea doc and resolved as part of this ticket's design.

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
Implemented exactly per `staging_artifacts/.../plan.md` Steps 1-5, no deviations.

- New pure-predicate module `src/domains/world_emergence/quest_grammar.py`:
  - `build_faction_territory_pool(state)` — set of faction IDs with non-empty `territory`.
  - `check_faction_coherence(faction_source, state)` — reuses `is_reachable` from
    `src/worldbuilding/reachability.py`; `faction_source=None` auto-passes via `is_reachable([], pool)`.
  - `_parse_fetch_resource_type(token)` — tolerant parse; only `"fetch:<resource>:<qty>"` tokens
    carry a resource claim, everything else (e.g. `"eliminate:<subject>:1"`) is skipped.
  - `check_resource_availability(objective_chain, state)` — rejects only when at least one matching
    `ResourceNodeState` exists AND every matching node has `remaining_charges == 0`; zero matching
    nodes is cannot-verify-pass, not reject (protects the empty-`resource_nodes` regression case).
  - `validate_quest_opportunity(opportunity, state)` — combinator returning `"faction_zero_territory"`
    / `"resource_depleted"` / `None` (admissible).
- Wired into `src/domains/world_emergence/phase.py` `WorldEmergencePhase.execute()` step 5b: added a
  second filtering pass building `admitted_quest_opps` from `quest_opps`, changed
  `quest_registry_add=list(quest_opps)` to `quest_registry_add=list(admitted_quest_opps)`, and added
  `metric_counters["quest_opportunities_rejected"]`. `result.quest_opportunities` (line 94) remains
  unfiltered, unchanged.
- All new code is a pure function of `(QuestOpportunity, AuthoritativeState)`: no `uuid()`, no
  time/clock reads, no RNG, no mutation of either frozen dataclass.
- Added `tests/unit/domains/world_emergence/test_quest_opportunity_preemit_validation.py` (10 tests)
  covering both predicates' positive/negative/cannot-verify paths, the `faction_source=None` pass
  (exercised through both live generator methods), determinism/read-only/no-uuid guards, and the two
  phase-wiring integration tests (passing opportunity unfiltered; rejected opportunity excluded).
- Updated `docs/mechanics/06_worldbuilding_foundation.md` with a new `## 10. Runtime Pre-Emit
  Validation` section (sibling to §7's build-time gate ladder) and `docs/parity_ledger/world_dynamics.yaml`
  entry `WORLD-102` (`v2_evidence` + `test_path` extended, `status`/`priority` unchanged) per the
  Authoritative Mechanics Rule's Parity clause.
- Environment note: `graphify update .` timed out in this worktree (no pre-built `graphify-out/graph.json`
  here, matching the investigation's own note) and `make knowledge-index-update` could not complete
  (`sentence-transformers` not installed in this environment) — both are pre-existing environment gaps
  unrelated to this ticket's code, not skipped by choice.

## Test Summary
Final scoped command actually run this session (corrected after the structural
`test_scope_coverage_static` backstop flagged the initial `tests/unit/domains/world_emergence/`-only
scope as under-covering the changed `src/domains/world_emergence/quest_grammar.py`, which maps to the
full `tests/unit/domains/` directory, not just its `world_emergence` subdirectory):
```
pytest tests/unit/quest/ tests/unit/domains/ tests/integration/domains/world_emergence/ \
  tests/unit/worldbuilding/ tests/integration/scenarios/test_phase8_world_emergence_scenarios.py \
  tests/integration/scenarios/test_resource_depletion.py -m "not slow" -q
→ 951 passed, 1 deselected, 0 failed
```
No existing test modified. The AC3-named regression tests
(`test_resource_crisis_quest_generated_on_depletion`, `test_threat_response_quest_generated_on_high_severity`,
`test_world_emergence_populates_quest_registry`, `test_world_emergence_phase_emits_quest_opportunities`)
all pass unmodified.

## Files Changed
- `src/domains/world_emergence/quest_grammar.py` (new)
- `src/domains/world_emergence/phase.py` (modified — step 5b filter + metric counter)
- `tests/unit/domains/world_emergence/test_quest_opportunity_preemit_validation.py` (new)
- `docs/mechanics/06_worldbuilding_foundation.md` (modified — new §10)
- `docs/parity_ledger/world_dynamics.yaml` (modified — WORLD-102 updated)
- `staging_artifacts/TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION/plan.md` (no content deviation;
  no edits required)
- `tickets/inprogress/TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION.md` (this file)

## Completion Summary
Added a pure, read-only runtime grammar gate (`src/domains/world_emergence/quest_grammar.py`) that
checks a generated `QuestOpportunity`'s faction-coherence (via `is_reachable` reuse against
`state.factions`/`FactionState.territory`) and resource-availability (against
`state.resource_nodes`/`ResourceNodeState.remaining_charges`) before it is admitted into
`StateUpdate.quest_registry_add`, wired into `WorldEmergencePhase.execute()` step 5b in `phase.py`.
Rejected opportunities are excluded from the registry and counted in a new
`metric_counters["quest_opportunities_rejected"]`, while `result.quest_opportunities` stays
unfiltered per scope. All acceptance criteria are met and verified by 10 new unit/integration tests
plus a full pass of the existing quest/world-emergence/worldbuilding regression surface (269 tests,
0 failures, no existing test modified). Mechanics Bible §10 and parity ledger entry WORLD-102 were
updated in the same session per the Authoritative Mechanics Rule.
