---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260822-PERSONALITY-DRIFT-MUTATION-CAPABILITY
phase: open
date: 2026-08-22
tags: [cognition]
---

# TCK-20260822-PERSONALITY-DRIFT-MUTATION-CAPABILITY

## Title
New personality-mutation capability via typed IdentityUpdate (rule-based first)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The original proposal described replacing explicit personality/life-arc mutation rules with a latent-space representation, assuming a rule-based mutation system already exists for individual entities. Investigation found PersonalityComponent (greed/bravery/sociability/industry) is set once at spawn and never mutated afterward -- there is no rule-based drift mechanism to migrate, and src/core/updates.py's IdentityUpdate has no field targeting PersonalityComponent at all. This ticket instead builds personality mutability as a wholly new subsystem from scratch: a typed IdentityUpdate field, apply-path plumbing, and inspection visibility, using simple rule-based triggers first; a latent-space-informed representation is deferred as a secondary/stretch goal, not this ticket's primary deliverable.

## Scope
- Add a new typed IdentityUpdate field (state field -> Update dataclass -> authoritative apply path) enabling PersonalityComponent values to change
- Define at least one concrete stimulus (e.g. a wound, betrayal, or alliance event) that drives a durable personality change via the authoritative apply path
- Surface the resulting change in existing inspection tooling (PersonalitySnapshotRecorder/entity_inspector.py)
- Ship rule-based mutation logic as the primary deliverable; scope any latent-space-informed representation as an explicit stretch/future goal only

## Out of Scope
- Cross-region culture convergence (separate ticket -- different module, different lifecycle, zero shared mechanism)
- Bravery coefficient calibration (separate ticket)
- Chronicle arc clustering (separate ticket)
- Social memory vector field (separate ticket)
- Building a full latent-space/embedding representation as a hard requirement of this ticket
- Modifying AppraisalSystem.evaluate_emotional_state()'s existing per-tick transient EmotionalProfile computation

## Acceptance Criteria
- [ ] Ticket explicitly states this is building a wholly NEW subsystem (personality mutability) from scratch -- PersonalityComponent is currently set once at spawn and never mutated; there is no existing rule-based mutation system to "replace with latent space" as the proposal assumed
- [ ] Entity personality values (greed/bravery/sociability/industry) change across at least one tick/episode boundary in response to a defined stimulus (e.g. a wound, betrayal, alliance event), via a new typed IdentityUpdate field flowing through the authoritative apply path -- currently 0% true since PersonalityComponent is immutable post-spawn
- [ ] The change is durable (persists in AuthoritativeState after apply) and inspectable (surfaces in PersonalitySnapshotRecorder/entity_inspector.py)
- [ ] The mutation mechanism ships as rule-based first; a latent-space-informed representation is an explicit secondary/stretch goal, not the ticket's primary deliverable
- [ ] The mutation mechanism has a documented decode/inspection path satisfying the Durable State Rule

## Related Tickets
- TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/content_semantics/personality.py
- src/entities/archetype_factory.py
- src/worldassembly/entity_spawner.py
- src/engine/cognition.py
- src/engine/evolution.py
- src/domains/campaigns/state.py
- expected: src/observability/personality_snapshot.py
- expected: entity_inspector.py

## Assumptions / Open Questions
- Whether a rule-based mutation mechanism is sufficient for this ticket's acceptance criteria, or whether the requester specifically wants latent-space representation as a hard requirement, should be confirmed -- investigation recommends rule-based first with latent-space as a stretch goal only
- The specific stimuli that should trigger personality drift (wound, betrayal, alliance, etc.) and their magnitude/direction of effect are not yet specified and need design decisions during planning
- Interaction with AppraisalSystem.evaluate_emotional_state()'s existing per-tick transient computation (which also reads static bravery) needs clarification to avoid conflating transient emotional state with durable personality drift
- `layer: core` was chosen over `strategy` because the primary deliverable is a typed state/Update-path addition (IdentityUpdate in src/core/updates.py, PersonalityComponent in src/core/state.py) rather than goal-hierarchy/appraisal logic; src/engine/cognition.py involvement is secondary (stimulus triggering, not the core mechanism)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
