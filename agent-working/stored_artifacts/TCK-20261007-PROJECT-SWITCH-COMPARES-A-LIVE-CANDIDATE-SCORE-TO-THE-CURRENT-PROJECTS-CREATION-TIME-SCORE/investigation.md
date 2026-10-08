---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE
artifact_type: investigation
tags: [strategy, cognition, bug]
---

# Investigation

- `evaluate_project_switch` (intelligence.py): `effective_current_score = current.score + retention_margin`, then `candidate_project.score > effective_current_score` (and a normalized version for the lock bypass). The candidate's `score` is `best_candidate.utility` (live, after the personality, life-stage, boredom and blocker modifiers); the current project's `score` was set at creation and never refreshed.
- Scale: `_score_scale_max` classifies by the enum class: a `ProjectKind` project stores a raw score on the 2.9 scale (adventure routes, contracts via `raw_score`), a `GoalKind` project stores a utility on the 100 scale. So only a `GoalKind` project can be refreshed from a live utility.
- Symptom (measured, one tree each, seed 42, 1500 ticks, audit_mode, crowded_frontier / frontier_living_world): same-kind duplicate switches (a project replacing itself with a fresh project of the same kind, suspending the original) 16 / 20 before; harvesting to harvesting 7 / 8, town_return to town_return 8 / 11, combat_engage to combat_engage 1 / 1; 0 / 0 after.
- For the fatigue project in `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`: stored 50.5, live 52.5 to 53.5 over t430-470; the flat-80 `resolve_blocker` (95.3 after modifiers) outranks it either way, so the refresh does not keep the project (see the divergence entry).
- Probes (scratchpad, not committed): `measure_switch.py`.
