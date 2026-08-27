---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260824-OCCUPATION-CHANGE-TRIGGER
phase: done
date: 2026-08-24
tags: [combat, economy, social, world]
---

# TCK-20260824-OCCUPATION-CHANGE-TRIGGER

## Title
Add the Missing Occupation-Change Transition Trigger (Careers & Apprenticeships)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
IdentityUpdate.role_set already has a full live apply path with 12 confirmed consumers -- the largest confirmed blast radius of any M1 idea. Only the transition trigger that would actually change role/occupation is missing, and the author wants that trigger added.

## Scope
- Design and implement a new AI-selectable action/goal that produces IdentityUpdate(role_set=...), reachable through a real Kernel.tick_once() run (no role_set= assignment site exists anywhere in src/ today)
- Define a concrete real-world trigger condition (career milestone, apprenticeship completion, promotion, etc.) -- none is specified in the original proposal, this is a genuine multiple-valid-implementations decision requiring options+recommendation
- Commit the role change only through the existing authoritative IdentityPatch.apply path, no bespoke parallel mutation
- Verify event_extractor.py's entity_role_changed fires with the correct payload on a real transition; update ENTITY-007's ledger note from unscored_intentional to verified/live
- Regression-check all 12 confirmed role-reading consumers behave consistently with no stale-cache regression: spawn/occupancy priority, legality readiness, crafting required_role gate, adventure route scoring, routine behavior, combat rewards/lethality, military conflict GUARD check, cooperation role==1 checks, evolution HERO check, regional sovereignty HERO check
- Flag (not necessarily fix) the cooperation/providers.py:52 and evaluators.py:180 role==1 magic-number/EntityRole(1)=SHOPKEEPER mismatch, since dynamic role mutation could newly expose this as a live bug

## Out of Scope
- Extending the EntityRole enum with genuinely new occupation types beyond existing bounds -- only in scope if the chosen trigger design requires it, and if so requires re-auditing all 12+ consumers

## Acceptance Criteria
- [x] A new AI-selectable action/goal produces IdentityUpdate(role_set=...) reachable through a real Kernel.tick_once() run
- [x] The existing authoritative apply path commits the value with no bespoke parallel mutation
- [x] event_extractor.py's entity_role_changed fires with correct payload on a real transition; ENTITY-007's note is updated to verified/live
- [x] All 12 confirmed consumers read the new role consistently with no stale-cache regression
- [x] All 4 existing identity-event tests still pass unmodified

## Related Tickets
- TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP
- TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD
- TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION
- TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION

## Related Docs
- docs/event_ledger/entity.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/updates.py
- src/engine/patches.py
- src/engine/apply.py
- src/systems/world_systems/routine.py
- src/domains/adventure/scoring.py
- src/systems/economy_systems/crafting.py
- src/engine/combat_rewards.py
- src/engine/combat.py
- src/world/spawn.py
- src/engine/occupancy_snapshot.py
- src/engine/legality.py
- src/engine/military_conflict.py
- src/domains/cooperation/providers.py
- src/domains/cooperation/evaluators.py
- src/engine/evolution.py
- src/world/regional_sovereignty.py
- src/world/camp.py
- src/entities/identity_resolver.py
- src/observability/event_extractor.py
- src/engine/domain/action_router.py
- src/engine/domain/core_actions.py
- src/api/presenters/state_presenter.py
- src/observability/live/entity_inspector.py
- src/observability/personality/recorder.py
- src/core/enums.py

## Assumptions / Open Questions
- No concrete real-world trigger condition is specified by the original proposal -- options+recommendation needed before implementation
- This is closer to new cognition/goal-hierarchy wiring than a bugfix, given no AI goal/driver currently proposes a role change anywhere
- layer set to `core` (registered in registries/layer_registry.jsonl) since the change centers on entity identity/state primitives (IdentityUpdate.role_set, IdentityPatch.apply) with cross-cutting consumers spanning combat, economy, cooperation, evolution, and world layers; no single one of those layers covers the full scope

## Implementation Notes
Added `GoalKind.OCCUPATION_CHANGE`/`ProjectKind.CAREER_CHANGE`/`ObjectiveKind.CHANGE_OCCUPATION` (no
`EntityRole` enum extension). New `OccupationChangeGoalScorer` (`src/ai/goals/occupation_change_scorer.py`)
gates on `role==CITIZEN`, resolves the entity's region via `LegalityServiceV2`, tallies live headcount
per candidate role (SHOPKEEPER/WORKER/GUARD) against a config-driven area/density target
(`src/world/occupation_config.py`, mirrors `spawn_config.py`'s monster-density pattern), and checks a
baseline `entity.attributes` aptitude gate (charisma/endurance/strength >= 5). Registered as a tier-5
GoalRegistry candidate (`src/ai/goals/__init__.py`). A winning candidate materializes a
`ProjectKind.CAREER_CHANGE` project via a bespoke branch in `StrategicIntelligenceSystem.evaluate_strategic_intent`
(`raw_score`, never `utility` -- same scale-mismatch class as `RegionStabilizationGoalScorer`'s own
precedent bug), with a per-tick completion check once `entity.identity.role != CITIZEN`. Resolves
through `ObjectiveIntentResolver.resolve()`'s new `CHANGE_OCCUPATION` branch into
`ActionIntentAdapter.execute()`'s new `CHANGE_OCCUPATION` branch, the sole new producer of
`IdentityUpdate(role_set=...)` in the codebase, committed only through the pre-existing authoritative
`IdentityPatch.apply` path -- enforced by a new architecture guard
(`tests/architecture/test_role_set_identity_patch_only_guard.py`). `cooperation/providers.py:52,88` and
`evaluators.py:180`'s `role==1` (SHOPKEEPER, not a distinct "Hireling" role) magic-number mismatch is
flagged with `# TODO` comments only, per scope -- not fixed; locked in by
`tests/unit/domains/cooperation/test_role_1_magic_number_disclosure.py`. `docs/event_ledger/entity.yaml`
ENTITY-007's `entity_role_changed` note moved from "zero producers, unreachable" to verified/live;
`entity_faction_changed` left unchanged (out of scope, still no producer). Docs updated:
`docs/mechanics/04_strategic_cognition.md` (Tier 4 row + corrected "sole live tier-5 candidate" claim)
and `docs/parity_ledger/strategic_cognition.yaml` (new entry STRAT-259).

Test-phase finding and fix (documented here per Gate Integrity -- a real regression was found and
fixed, not routed around): the two new real-`Kernel.tick_once()` integration tests
(`test_occupation_change_reachable_through_real_kernel_tick_once`,
`test_entity_role_changed_event_fires_on_real_occupation_transition`) initially failed. Root cause was
in the tests' own world construction, not the shipped feature code: both built their `RegionState`
without an explicit `kind`, defaulting to `"FOREST"`, which `SpawnService.process_spawns`
(`src/world/spawn.py:65`) matches against `SPAWN_POOLS` and seeds a wandering `MONSTER` at tick 0. The
monster reaches aggro range of the lone citizen right as it arrives at the region center (~tick 20),
and the resulting tactical `INTERCEPT` response permanently preempts the `CHANGE_OCCUPATION`
objective's navigation, so the transition never completes. Fixed by setting `kind="TOWN"` on both
tests' `RegionState` (a region kind absent from `SPAWN_POOLS`, so no wildlife spawns there) -- also the
semantically correct kind for a civilian-employment scenario. No production code was touched to make
this pass.

## Test Summary
970 tests passed, 0 failed, across the full scoped regression sweep (plan.md Step 12): identity events
(9/9, including all 8 pre-existing unmodified), `tests/unit/strategic/`, `tests/unit/domains/adventure/`,
`tests/unit/domains/cooperation/`, `tests/unit/domains/faction/`, `tests/unit/domains/optimization/`,
`tests/unit/world/`, `tests/unit/combat/`, both architecture guards, the occupation-change integration
test, and `tests/unit/world/test_economy_contract.py`. All 12 confirmed role-reading consumers'
pre-existing suites pass unmodified -- no consumer file itself was changed by this ticket.

## Files Changed
- src/ai/goals/occupation_change_scorer.py (new)
- src/world/occupation_config.py (new)
- src/ai/goals/__init__.py
- src/core/strategic.py
- src/domains/adventure/resolver.py
- src/domains/cooperation/evaluators.py (TODO comment only)
- src/domains/cooperation/providers.py (TODO comments only)
- src/engine/intent/action_intent.py
- src/systems/strategic_systems/intelligence.py
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml (new entry STRAT-259)
- docs/event_ledger/entity.yaml (ENTITY-007 updated)
- tests/architecture/test_legacy_enum_usage_boundaries.py
- tests/architecture/test_role_set_identity_patch_only_guard.py (new)
- tests/unit/strategic/test_occupation_change_scorer.py (new)
- tests/unit/strategic/test_intents.py
- tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py
- tests/unit/domains/cooperation/test_role_1_magic_number_disclosure.py (new)
- tests/unit/observability/test_event_extractor_identity.py
- tests/integration/strategic/test_occupation_change_reachability.py (new)

## Completion Summary
Implemented the missing occupation-change transition trigger: a new tier-5 `OccupationChangeGoalScorer`
lets a `CITIZEN` entity take an open, skill-matched civilian job (`SHOPKEEPER`/`WORKER`/`GUARD`) based
on per-region open-slot density (`src/world/occupation_config.py`) and a baseline attribute gate,
producing the first-ever `IdentityUpdate(role_set=...)` in the codebase, committed only through the
existing authoritative `IdentityPatch.apply` path (enforced by a new architecture guard). `ENTITY-007`'s
`entity_role_changed` ledger note moved from unreachable/unscored to verified/live. All 12 confirmed
role-reading consumers regression-checked via their existing test suites, unmodified and passing. The
`cooperation/providers.py`/`evaluators.py` `role==1` magic-number mismatch was flagged with `# TODO`
comments only, per scope (not fixed), and locked in by a dedicated disclosure test. During Test phase,
found and fixed a real defect in this ticket's own two new integration tests (not the shipped feature):
both built a `RegionState` with the default `kind="FOREST"`, which let the ambient monster-spawn system
seed a wildlife entity that permanently distracted the citizen's tactical navigation via an `INTERCEPT`
response before it could reach the region center and dispatch the role change. Fixed by setting
`kind="TOWN"` on both tests' region (semantically correct for a civilian-employment scenario, and a
region kind absent from `SPAWN_POOLS`) — no production code changed. Final: 970 tests passed, 0 failed,
across the full scoped regression sweep; all 4+ existing identity-event tests pass unmodified.
