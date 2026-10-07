---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE
artifact_type: plan
tags: [strategy, cognition, bug]
---

# Plan

1. Add `with_live_current_score(entity, live_scores)`: the entity with the current project's score replaced by its goal's live (modified) utility, only for a `GoalKind` project with a live score this evaluation.
2. Use it at the one `evaluate_project_switch` call in `evaluate_strategic_intent`; leave `evaluate_project_switch` itself alone.
3. Tests for the helper's rules and for the duplicate-replacement symptom through the real arbiter; measure before and after on one tree.
4. Out of scope: need priority against flat-80 goals (designer), persisting the refresh, the action semantics (Lane B).
