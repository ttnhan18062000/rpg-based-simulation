---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK
artifact_type: plan
tags: [combat, strategy, cognition]
---

# Plan

The ticket's deliverable is a distinction (rejected versus never attempted) from one traced sample; a fix was permitted only as
far as the planner ruled. Ruling (planner, 2026-10-05): option (A), framed as the missing lifecycle of `ENTITY_MOVE`.

1. Trace one entity end to end, then aggregate, without touching contested files.
2. (A): a pursuit `ENTITY_MOVE` ends when the **live** target is within attack reach (keyed on the target entity, not the
   navigation destination); the completion also clears the navigation target. Applies only to `PURSUE` moves. Both dispatchers.
3. Fold in the redirection writer fix (planner ruling): for an entity-typed objective, no navigation point from strategy.
4. Measure the next gates (brain cadence, flee gate) before proposing anything; do not edit `scheduler.py` (contested) or
   appraisal thresholds (semantics, parked).
5. Docs: tactical contract, lane doc (`worker_logic.py` Lane A, `scheduler.py` contested), divergence 2.68, parity `COMB-329`.

Scope guards: no `scheduler.py` edit; no appraisal or trauma change; the sticky `ATTACK` re-dispatch, the friendly-fire verdicts and
the flee gate stay separate tickets.
