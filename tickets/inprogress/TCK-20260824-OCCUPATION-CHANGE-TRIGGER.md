---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260824-OCCUPATION-CHANGE-TRIGGER
phase: open
date: 2026-08-24
tags: [combat, economy, social, world]
---

# TCK-20260824-OCCUPATION-CHANGE-TRIGGER

## Title
Add the Missing Occupation-Change Transition Trigger (Careers & Apprenticeships)

## Status
OPEN

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
- [ ] A new AI-selectable action/goal produces IdentityUpdate(role_set=...) reachable through a real Kernel.tick_once() run
- [ ] The existing authoritative apply path commits the value with no bespoke parallel mutation
- [ ] event_extractor.py's entity_role_changed fires with correct payload on a real transition; ENTITY-007's note is updated to verified/live
- [ ] All 12 confirmed consumers read the new role consistently with no stale-cache regression
- [ ] All 4 existing identity-event tests still pass unmodified

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

## Test Summary

## Files Changed

## Completion Summary
