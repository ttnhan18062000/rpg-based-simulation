---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION
phase: open
date: 2026-09-15
tags: [combat]
---

# TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION

## Title
`CombatEngagementPhase`'s entire tactical decision (posture, `ActionIntent`, opponent memory,
combat_risk belief) has zero downstream consumers — confirmed by both static trace and a real
four-condition A/B; wire the posture through to a real consumer, or decide not to

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
While investigating why cross-faction hostile interaction is rare across the corpus
(`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`), traced `CombatEngagementPhase.apply()`
(`src/domains/combat_engagement/phase.py`) end to end and found its entire tactical output —
not just one field, all of it — is write-only:

1. `PostureIntentResolver.resolve()` (`src/domains/combat_engagement/resolver.py`) builds a real
   `ActionIntent(kind="ATTACK_TARGET"/"MOVE_TO", ...)` for every posture (`ENGAGE`, `RETREAT`,
   `AVOID`, `VENGEANCE_ENGAGE`). The phase computes this intent and then never stages it anywhere:
   `EntityUpdate.intent_results` is hardcoded to `[]` in the constructed update, and the real field
   for a raw pending intent, `EntityUpdate.pending_action_intent`, is never set. (That field's only
   real consumer, `src/engine/pipeline_phases/information_intent_execution.py`, is for an entirely
   unrelated feature — self-model information queries.)
2. `last_combat_posture`/`last_combat_posture_target` (`property_updates` written by the same
   phase) have zero readers anywhere in `src/` (confirmed via repo-wide grep).
3. The opponent-memory writes (`OpponentModel` via `cognition_bundle_set`) don't reach capability
   estimates either — `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (still
   BLOCKED) confirms that chain is also dead.
4. The one real, confirmed consumer is the `combat_risk` belief, read by
   `HelpNeedEvaluator.evaluate()` — but this only affects cooperation/help-seeking scoring, not
   whether the assessing entity itself fights.

**Confirmed with a real A/B, not just static tracing**: re-ran the exact scenario
(`build_metropolis_state`, 1000 entities, seed 42) that `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-
POWER` originally used to claim a 4.1x combat-volume increase from enabling this feature, across
four conditions (flag OFF; flag ON unmodified; flag ON with this phase's output discarded; flag ON
with the phase never run at all), counting real `CombatActions.execute_attack()` calls directly.
**All four conditions produced the identical count (1960).** The phase's own tactical decision has
no measurable causal effect on real combat today — full detail and the four-condition table are in
`docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`'s
2026-09-15 correction and `docs/brainstorm/rpg_feature_atlas.html`'s Combat Engagement card.

**This means the feature as specified and as documented ("an entity assessing a threat and
committing or withdrawing") is only half-built.** The assessment genuinely happens; the commit/
withdraw decision it should produce does not execute.

## Scope
- **Design/scoping question first, same sequencing discipline as this week's other findings**:
  decide what "wiring the posture" should mean before building it. Candidates to evaluate, not
  assumed:
  1. Route `PostureIntentResolver`'s built `ActionIntent` through the same real dispatch path
     `action_routing`'s own attack dispatch already uses (the pipeline runs `action_routing`/
     `movement_routing` *before* `combat_engagement` in the same tick — see
     `src/engine/pipeline.py`'s own comment at the `combat_engagement` call site — so a same-tick
     intent from this phase cannot reach that tick's own routing; the intent would need to persist
     and be picked up at the *start* of the next tick, or the phase would need to move earlier in
     the pipeline, or routing would need a second pass).
  2. Have some other, already-real decision system (e.g. the adventure/goal system's
     `DEFEAT_ENEMY` objective, confirmed via `src/domains/adventure/resolver.py` to be the actual
     live path issuing real `ATTACK_TARGET` intents today) read this phase's outputs
     (`combat_risk`, `OpponentModel.estimated_power`/`confidence`) as an input to its own scoring,
     rather than trying to make `CombatEngagementPhase` itself the executor.
  3. Determine the posture/intent construction was never intended to execute at all — e.g., it may
     have been designed as a stepping-stone toward option 2 above, or a placeholder for a future
     execution path that was never finished — and decide explicitly whether to keep it as
     observability-only (rename/re-document it as such) or complete the wiring.
- Do not silently pick one of these and build it — this changes real gameplay behavior (whether
  entities actually fight based on their own risk assessment) and was explicitly flagged by peer
  review as needing a decision, not an assumption.

## Out of Scope
- Investigating why the original 4.1x combat-volume measurement no longer reproduces — separate,
  already-filed ticket (`TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES`).
- The cross-faction combat rarity investigation itself, which surfaced this finding but has its own
  separate scope (`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`).
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`'s own scope (the capability-
  estimate chain) — referenced here as corroborating evidence, not re-investigated.

## Acceptance Criteria
- A reviewed decision on what "correct" behavior is for this phase's posture/intent output —
  wired to a real consumer, or explicitly re-scoped as observability-only — before any code change.
- If wiring is chosen: a real end-to-end proof (not unit tests alone) that an entity's `ENGAGE`
  posture decision measurably changes real combat outcomes in an unmodified corpus world.
- `docs/brainstorm/rpg_feature_atlas.html`'s Combat Engagement card and
  `docs/guidelines/intentional_divergences.md` (if an entry is added for whichever decision is
  made) updated to match whatever is actually true after this ticket closes.

## Related Tickets
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (parent investigation that surfaced this)
- `TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES` (sibling — the measurement
  side of the same finding)
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (BLOCKED — the memory-side half
  of the same "write-only" shape)
- `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` (built the phase; the ticket whose own 4.1x
  measurement this finding supersedes)

## Related Docs
- `docs/brainstorm/rpg_feature_atlas.html` (Combat Engagement card, corrected 2026-09-15)
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`
  (4.1x correction, 2026-09-15)
- `docs/simulation/domains/combat_engagement_contract.md`

## Related Stored Artifacts
_(none yet — filed as a finding, not yet investigated)_

## Related Code Areas
- `src/domains/combat_engagement/phase.py` (`CombatEngagementPhase.apply()`)
- `src/domains/combat_engagement/resolver.py` (`PostureIntentResolver.resolve()`)
- `src/core/updates.py` (`EntityUpdate.intent_results`/`pending_action_intent`)
- `src/domains/adventure/resolver.py` (the real, currently-independent `ATTACK_TARGET` producer)
- `src/engine/pipeline.py` (phase ordering: `action_routing`/`movement_routing` run before
  `combat_engagement` in the same tick)

## Assumptions / Open Questions
- Not yet known which of the three candidate resolutions in Scope is correct — a real design
  decision, not assumed here.

## Implementation Notes
_(none — filed as a finding, not yet investigated)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_
