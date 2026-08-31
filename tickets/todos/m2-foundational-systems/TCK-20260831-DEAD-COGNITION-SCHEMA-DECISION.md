---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION
phase: open
date: 2026-08-31
tags: [cognition]
---

# TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION

## Title
Decide keep-or-cut for the dead SelfModel cognition schema wrapper

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Prune or finish the dead cognition schema. core/cognition.py's SelfModel is a genuinely dead wrapper that re-wraps self_model.py's own component classes, with zero production constructions anywhere. AttentionFocusService already reads a path (entity.cognition.subjective.self.needs.dominant_need) that nothing ever writes — currently masked only because ENABLE_SELF_MODEL_COGNITION defaults OFF, and this bug will start firing silently the moment that flag flips on, so it must be fixed as part of this decision, not left for later.

## Scope
- Make and record an explicit keep-or-cut decision scoped to SelfModel/SubjectiveModel.self specifically (not the whole cognition.py file, since PerceptionModel/EmotionalModel/TemporalModel are genuinely live sibling fields), in docs/architecture/cognition_domain_ownership.md or a new ADR.
- If cut: remove SelfModel, repoint cognition_accessors.py's get_self_awareness/get_need_interpretation/get_capability_estimate to entity.self_model.*, and repoint AttentionFocusService to read the real self_model path, proven by a test using the real SelfModelUpdatePhase path (not a hand-built cognition.py shell).
- If kept: add a real writer so entity.cognition.subjective.self.needs.dominant_need is actually populated, and add an ownership row for it in cognition_domain_ownership.md.
- Resolve and record the idea 22 and idea 24 open questions using investigation evidence: idea 22 (Relationship Roles, shipped in M1) is confirmed unrelated/moot; idea 24 (Personal Economy) is confirmed informed-but-not-blocked by a separate not-yet-filed MotivationModel.values foundation ticket.

## Out of Scope
- PerceptionModel, EmotionalModel, and TemporalModel fields in cognition.py — genuinely written by real pipeline phases, not part of this decision's scope.
- Filing the separate MotivationModel.values foundation ticket that idea 24 actually depends on.

## Acceptance Criteria
- [ ] Ticket records an explicit keep-or-cut decision scoped to SelfModel/SubjectiveModel.self specifically (not the whole file), persisted in docs/architecture/cognition_domain_ownership.md or a new ADR.
- [ ] If cut: SelfModel is removed, cognition_accessors.py's get_self_awareness/get_need_interpretation/get_capability_estimate are repointed to entity.self_model.*, and AttentionFocusService is repointed to read the real self_model path, proven by a test using the real SelfModelUpdatePhase path (not a hand-built cognition.py shell).
- [ ] If kept: a real writer is added so the path is actually populated, and cognition_domain_ownership.md gains a row naming its owner.
- [ ] Idea 22/24 open question is answered with the evidence above, recorded in the ticket, not left open.

## Related Tickets
- TCK-20260824-RELATIONSHIP-ROLE-FIELD
- TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK
- TCK-20260824-WIRE-ORPHANED-MECHANISMS

## Related Docs
- docs/architecture/cognition_domain_ownership.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/cognition.py
- src/core/self_model.py
- src/core/cognition_accessors.py
- src/domains/perception/service.py
- src/cognition/self_model_phase.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- The AttentionFocusService bug is currently masked only because ENABLE_SELF_MODEL_COGNITION defaults OFF and its only override path (src/engine/pipeline.py:72-78) is never set outside test harnesses — must be fixed as part of this decision, not deferred.
- cognition.py is not uniformly dead — a whole-file deletion would break live sibling fields; the decision must stay scoped to SelfModel/SubjectiveModel.self.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
