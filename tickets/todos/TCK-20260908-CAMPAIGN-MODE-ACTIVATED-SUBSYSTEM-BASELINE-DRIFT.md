---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT
phase: open
date: 2026-09-08
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT

## Title
Campaign-mode baselines and SimQ expectations predate three subsystems that PR #148 activated

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
PR #148 (`TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`) fixed a real root cause:
`CampaignOrchestrator._build_initial_state()` never called `WorldCompiler.compile()`, so
`state.regions`/`state.places` were empty for every Campaign-mode episode.

Populating them re-activated at least three subsystems that had been silently no-op'ing in
Campaign mode, because each gates on a non-empty `state.regions`:

1. **War / siege / territory transfer** — `MilitaryConflictPhase._find_contested_region()`
   iterates `state.regions` in all three of its priority branches, and the siege loop then does
   `reg = state.regions.get(contested_region_id); if reg is None: continue`. With empty regions no
   siege ever began, so `siege_progress` never advanced and the `EXPAND_TERRITORY`/territory-
   transfer path never fired.
2. **Calamity / world-boss spawning** — `CalamityService.process_world_dynamics()` selects its
   spawn target via `[r for r in state.regions.values() if r.calamity_intensity > 0.3]`, which is
   unconditionally empty when `state.regions` is.
3. **Regional tax / suppression logic** — the originally-scoped consequence in the parent ticket.

Consequence this ticket exists to address: **any Campaign-mode baseline, fixture, or SimQ
expectation captured before PR #148 merged was recorded under the dormant (no-op) behavior.**
Those recorded values describe a simulation in which sieges, territory transfer, and calamity
spawning could not occur at all.

This is not a hypothetical slow drift. Siege completion is fast once a war pair persists:
`_SIEGE_PROGRESS_DELTA = 0.05` per tick, offset by `_DEF_PROGRESS_DELTA = -0.02` when a region has
>= 3 GUARD entities, so `siege_progress` reaches 1.0 in roughly 20 ticks undefended and roughly 34
ticks defended — well inside ordinary run lengths.

Nothing in CI covers this gap: PR #148's own CI run was fully green, because the affected
expectations are recorded baselines rather than assertions that fail on a behavior change.

## Scope
- Determine which Campaign-mode baselines/fixtures/SimQ expectations were captured before PR #148
  (merge commit `cb0b23b0`) and are therefore recorded under the dormant behavior.
- Re-run the affected Campaign-mode calibration/SimQ paths against current `main` and compare
  against the recorded values.
- For each difference, classify it: expected-and-correct (the newly-live subsystem legitimately
  changed the outcome) versus a real regression that needs its own ticket.
- Refresh the baselines that are merely stale, with the fresh evidence recorded, following the
  existing precedent for SimQ drift follow-ups (see `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-
  DRIFT`, filed for exactly this shape of deferred-finding drift).

## Out of Scope
- Tuning or balancing the newly-active subsystems. If siege/calamity behavior is judged badly
  balanced, that is a separate gameplay ticket, not this one.
- Any performance work. Per standing user direction (2026-09-08), a dedicated performance-
  optimization effort is planned after the current major epic; anything found here that is
  "correct but slower" is recorded and deferred to that effort, and only hard failures are fixed.
- Re-litigating PR #148's fix itself, which is correct and already merged.

## Acceptance Criteria
- [ ] A definitive list exists of which Campaign-mode baselines/expectations predate `cb0b23b0`.
- [ ] Each observed difference is classified as expected-and-correct or a real regression, with
      evidence, and no difference is left unclassified.
- [ ] Stale baselines are refreshed with fresh recorded evidence; any real regression found gets
      its own ticket rather than being silently absorbed here.
- [ ] If the conclusion is that no baseline actually drifted, that null result is recorded with
      the evidence that supports it — a clean answer is an acceptable outcome.

## Related Tickets
- `TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY` (`tickets/done/`) — the root-cause fix that activated
  these subsystems; its own post-closure disclosure names all three.
- `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT` (`tickets/done/`) — precedent for a SimQ drift
  follow-up filed from a deferred finding.
- `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX`, `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-
  INVESTIGATION` — sibling follow-ups filed out of the same PR #148 batch.

## Related Docs
- `docs/mechanics/05_world_evolution.md` (calamity/world-evolution laws)
- `docs/engine/authoritative_pipeline.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up.

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (`_build_initial_state()`)
- `src/engine/military_conflict.py` (`_find_contested_region()`, siege loop, `_SIEGE_PROGRESS_DELTA`)
- `src/world/calamity.py` (`CalamityService.process_world_dynamics()`)
- `tests/simulation_quality/`, `tools/calibrate_simq.py`

## Assumptions / Open Questions
- Unknown whether any Campaign-mode baseline actually shifted in practice — the reactivation is
  confirmed from code, but the downstream numeric impact is not measured. Determining that is this
  ticket's work; a null result is a valid outcome and must not be forced into a change.
- Unknown whether a war pair actually persists long enough in real corpus runs for a siege to
  complete. Previously unanswerable, since empty regions made it structurally impossible; now
  answerable for the first time.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
