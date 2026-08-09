---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS
phase: open
date: 2026-08-09
tags: [combat, simulation-quality, feature-flags]
---

# TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS

## Title
`ENABLE_COMBAT_ENGAGEMENT=ON` appears to suppress the tactical.py/event_shapers.py combat path
entirely, contradicting its own documented, deliberate scope ("gates posture assessment only,
not damage resolution")

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Discovered during `TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS`'s own real,
controlled A/B investigation (which definitively ruled out a suspected calibration-tool JSONL
persistence bug). A direct, controlled test on the identical `dungeon_crawl_seed42` world/seed/
tick-count/Kernel-construction: with `ENABLE_COMBAT_ENGAGEMENT=ON` set, **zero**
`combat_engagement_started/ended`, `combat_resolved`, or `combat_damage` events fire — confirmed
identically across 3 separate real runs (both in-memory and on-disk JSONL). With the flag left at
its real corpus-default (unset/OFF), these events fire reliably (`combat_engagement_ended=10` in
the identical world/seed/tick-count configuration).

This directly contradicts the flag's own documented, deliberate scope, established by
`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`'s own real DEV-002 ruling: the flag
gates `CombatEngagementPhase` (`PP-16`, posture assessment only), explicitly **not** damage
resolution or the tactical.py-driven `ATTACK` path. If turning the flag ON genuinely suppresses
the entire tactical-combat pipeline (not just posture assessment), this is either (a) a real,
undisclosed regression in `CombatEngagementPhase`'s own implementation that has drifted from its
own documented scope since the DEV-002 ruling, or (b) a real, deeper interaction where
`CombatEngagementPhase` mutates entity/task state in a way that structurally prevents
`tactical.py`'s own deliberate `ATTACK` emission branch from ever being reached.

## Scope
1. **Investigate**: trace the exact real mechanism — does `CombatEngagementPhase` (when
   `ENABLE_COMBAT_ENGAGEMENT=ON`) mutate `entity.task`/`entity.combat` state in a way that
   structurally blocks `tactical.py`'s own real `ATTACK` emission, or does it change goal/
   objective selection upstream such that `COMBAT_ENGAGE` never wins the real goal competition
   when this phase is active?
2. **Determine whether this is a real regression or a real, deliberate (if undisclosed) design
   interaction** — per the Uncertainty Rule, do not assume either way.
3. **Produce a concrete recommendation**: fix the real interaction if it's an unintended
   regression, or correct the flag's own documentation (`docs/audits/D19_domain_phase_inventory.md`
   §12, and any other doc citing the DEV-002 "posture assessment only" scope) if the interaction
   is real and intentional but previously undisclosed.

## Out of Scope
- Any change to `calibrate_simq.py`/`EventRecorder`/`event_shapers.py` — all 3 confirmed working
  correctly by the parent ticket's own investigation.
- Correcting `TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK`'s own closed record — handled
  directly as part of the parent ticket's own Finalize, not this one.

## Acceptance Criteria
- [ ] investigation.md identifies the exact real mechanism by which `ENABLE_COMBAT_ENGAGEMENT=ON`
      suppresses the tactical.py/event_shapers.py combat path
- [ ] A concrete recommendation is produced (fix vs. correct documentation), with reasoning
- [ ] If a fix lands: real corpus re-verification shows `ENABLE_COMBAT_ENGAGEMENT=ON` no longer
      suppresses push-shaper combat events
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS (DONE, same session — the ticket
  whose own real investigation surfaced this finding)
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY (DONE, prior session — the real
  DEV-002 ruling this finding potentially contradicts)

## Related Docs
- `docs/audits/D19_domain_phase_inventory.md` §12 (Combat Engagement, Enhanced RPG Phase 4)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/combat_engagement/phase.py` (`CombatEngagementPhase`)
- `src/engine/tactical.py` (the real `ATTACK` emission branch, potentially blocked)

## Assumptions / Open Questions
- Whether this is world/scenario-specific (only reproduced on `dungeon_crawl`) or a general
  effect — left to Investigate phase to confirm against `urban_political` too.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
