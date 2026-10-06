---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT
artifact_type: plan
tags: [strategy, cognition]
---

# Plan

Ruling (rpg-feature-planning, 2026-10-06): option A.
1. Measure the path before building (investigation section 2): rare, and self-targeted.
2. Scorer: ignore a contract the holder itself sourced, via a helper that replaces the status check so `score()` does not grow.
3. Termination: a contract-serving project ends when its contract is no longer ACTIVE; one shared `objective_outcome` used by `evaluate_strategic_intent` (through `close_entity_target_project`) and by the work queue; both call sites change by replacing one line.
4. Drop Scope 1 (typed `target_entity_id`) and keep Design Decision #8 for the other holder; record why.
5. Constructed tests with disabling controls; scoped sweep; gates in a scratch venv; re-measure; docs (Bible, divergence 2.72, parity STRAT-276).
