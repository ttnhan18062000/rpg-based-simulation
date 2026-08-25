---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260824-ROLLOUT-FLAG-DECISIONS
phase: open
date: 2026-08-24
tags: [feature-flags]
---

# TCK-20260824-ROLLOUT-FLAG-DECISIONS

## Title
Decide the Eight Rollout Flags on Purpose

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P0

## Request Summary
Eight real, correctly-built systems (Self-Model, World Emergence, Progression Conversion, Combat Engagement, Social Cooperation, Belief Assimilation, Information Intent Execution, Guild Quest Generation) sit flag-gated OFF. The author wants a deliberate per-flag keep/cut/flip decision made now, not left as accumulating debt, because 38 more flagged ideas land on top of this precedent in M2 onward. This is a decision-only ticket, not new code, and must land before any other M1 ticket that adds new flag-gated behavior.

## Scope
- Produce a decision artifact recording keep/cut/flip verdict, with rationale citing evidence, for each of the 8 flags: ENABLE_SELF_MODEL_COGNITION, ENABLE_WORLD_EMERGENCE, ENABLE_PROGRESSION_EVOLUTION, ENABLE_COMBAT_ENGAGEMENT, ENABLE_SOCIAL_COOPERATION, ENABLE_BELIEF_ASSIMILATION, ENABLE_INFORMATION_INTENT_EXECUTION, ENABLE_GUILD_QUEST_GENERATION
- Reconcile FeatureFlagManager's all-OFF defaults (src/domains/optimization/feature_flags.py) against real per-world profiles that already turn 2 of the 8 flags ON (config/simulation_quality/profiles/urban_political.yaml, sandbox_world.yaml)
- Resolve what to do with the orphaned RolloutProfileManager (src/domains/optimization/rollout_profiles.py), which encodes a conflicting default matrix with zero callers found
- For each 'flip ON' verdict: implement the code default flip plus the required tests/unit/config/test_phase10_feature_flags.py::_DELIBERATE_ON_DEFAULT_FLAGS allowlist entry with backing ticket ref, or explicitly defer to a named follow-up ticket
- For each 'cut' verdict: remove the dead phase/call site, or document explicitly why the code stays, with a rationale class
- Add a docs/guidelines/intentional_divergences.md entry for every flip

## Out of Scope
- New gameplay content or scenario wiring for any of the 8 systems beyond the flag-default/dead-code decision itself
- Resolving the untested ENABLE_SELF_MODEL_COGNITION + ENABLE_ADVENTURE_ROUTING combination beyond flagging it as an assumption
- Any other M1 ticket that introduces new flag-gated behavior -- those must wait until this ticket closes

## Acceptance Criteria
- [ ] Decision artifact records a keep/cut/flip verdict with rationale for all 8 named flags
- [ ] For every 'flip ON' verdict, either the code default changed with a corresponding _DELIBERATE_ON_DEFAULT_FLAGS allowlist entry, or an explicit deferral to a named follow-up ticket is recorded
- [ ] For every 'cut' verdict, the dead phase/call site is removed or an explicit rationale-class note is added for why it stays
- [ ] Decision artifact explicitly reconciles FeatureFlagManager's all-OFF defaults against urban_political.yaml/sandbox_world.yaml's already-ON flags
- [ ] This ticket is closed before any other M1 ticket that adds new flag-gated behavior begins

## Related Tickets
- TCK-20260703-SIMQ-UPLIFT3-BRANCH-B
- TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING
- TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE
- TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md
- docs/brainstorm/rpg_feature_atlas.html
- src/domains/optimization/feature_flags.py
- src/domains/optimization/rollout_profiles.py
- src/domains/optimization/degradation.py
- src/engine/pipeline.py
- src/engine/pipeline_phases/guild_visit.py
- src/engine/pipeline_phases/information_intent_execution.py
- src/ai/goals/scorers.py
- src/cognition/self_model_phase.py
- config/simulation_quality/profiles/urban_political.yaml
- config/simulation_quality/profiles/sandbox_world.yaml

## Assumptions / Open Questions
- 'Progression Conversion' in the proposal's naming maps to the actual flag ENABLE_PROGRESSION_EVOLUTION -- needs confirming as part of the decision writeup
- Whether the untested combination of ENABLE_SELF_MODEL_COGNITION + ENABLE_ADVENTURE_ROUTING is safe to flip both ON simultaneously is an open question, unlike the already-fixed ENABLE_SELF_MODEL_COGNITION + ENABLE_BELIEF_ASSIMILATION combination
- TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ (C20) is sequenced strictly after this ticket's ENABLE_BELIEF_ASSIMILATION verdict lands

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
