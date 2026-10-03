---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION
artifact_type: plan
tags: [determinism]
---

# Plan — TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION

This is an investigation-tier ticket per its own Scope — no fix is implemented here regardless of
outcome. The plan is:

1. Trace the real mechanism (`AuthoritativeApplyPipeline.refine()`'s dirty-set checkpoints,
   `ApplyPlanBuilder.build_plan()`'s passive "candidates" path) to confirm the ticket's own
   Request Summary is accurate before testing anything.
2. For each of the two named consumers, construct a real scenario (real `refine()` +
   `ApplyPath.apply_generation()` call, not a synthetic stub) where the tick's only relevant
   change is passive-decay-only, and write a real, evidence-based test proving confirmed-bug /
   confirmed-benign / inconclusive for that consumer.
3. Record each verdict in `investigation.md` with the mechanism, not just the outcome.
4. If either consumer is confirmed a real bug: route a fix-approach decision through peer review
   (`rpg-feature-planning`) before implementing anything, per this ticket's own Scope and this
   repo's standing decision-routing convention. Do not implement inline even if the fix looks
   small.
5. Close this ticket once the decision is recorded (whether the outcome is "no bug — nothing to
   implement" or "bug confirmed, fix-approach agreed"). If a fix is warranted, file it as its own
   new ticket rather than implementing inside this investigation ticket — matches this session's
   established pattern (e.g. `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION` was filed
   separately from the investigation that found it).

## Outcome

- Consumer #1 (phase short-circuiting): confirmed benign — no follow-up ticket needed.
- Consumer #2 (read-model invalidation): confirmed a real bug, but at `ReadModelCache`
  (`src/api/read_model_cache.py`), not the ticket's originally-named `apply_plan.py`
  `invalidate_read_model` field (confirmed dead code). Fix-approach decision routed to peer review
  before any implementation; see `investigation.md` for the proposed approach and
  `## Implementation Notes` in the ticket body for the recorded decision once received.
- A new follow-up ticket carries the actual fix, filed after the decision is recorded — not
  implemented inside this investigation ticket.
