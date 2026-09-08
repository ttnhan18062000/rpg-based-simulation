---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION
phase: open
date: 2026-09-08
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION

## Title
`campaign_life_arc` episodes stall and truncate at ~tick 52 regardless of the configured 200-tick limit

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s investigation into
whether Campaign-mode baselines drifted after PR #148. That investigation ran
`campaign_life_arc` (`config/simulation_quality/profiles/campaign_life_arc.yaml`,
`campaign_episodes: 3`) directly against `CampaignOrchestrator.run_episode()`, instrumented to
capture the final `AuthoritativeState` per episode. Result: **every one of 3 episodes completed at
tick 52 — not the configured `tick_limit=200` victory condition.**

Root cause traced (cheaply — one grep, not a deep chase — flagged during that investigation as
worth its own ticket rather than resolved as an aside):
`ScenarioRuntimeService`'s own stall detector (`src/engine/scenario_runtime.py`,
`STALL_THRESHOLD=50`) sets `self._paused = True` once 50 consecutive ticks produce zero simulation
events (`kernel.tick_once()`'s own `_current_tick_event_count`), and the episode's run loop is
gated on `not self._paused` — matching the observed truncation almost exactly (50 + a couple of
ticks for the counter to cross the threshold and the loop to notice, before it can resume). The
JSONL replay for this exact run also shows `3 scenario_stalled` events (one per episode),
corroborating this directly.

**Why this matters beyond the originating investigation**: every future attempt to measure
anything about `campaign_life_arc` — whether war/siege/calamity ever fire at their intended
episode length, SimQ scoring, any future baseline work — is measured over roughly a quarter of the
intended window unless this is understood or fixed. The originating investigation could not
determine whether the PR #148-reactivated war/siege/calamity subsystems fire within a real
200-tick campaign episode specifically because of this truncation, not because those subsystems
are themselves unreachable.

## Scope
- Confirm the stall-detector mechanism is genuinely the cause (the citation above is a strong,
  directly-corroborated hypothesis from one investigation's own instrumentation, not yet
  independently re-verified from a fresh session).
- Determine whether ~50 consecutive zero-event ticks early in a `campaign_life_arc` episode is
  itself expected (e.g. a quiet narrative-setup phase genuinely produces no `SimulationEvent`
  objects for that long) or a real content/wiring gap (e.g. some system that should be producing
  events during this window silently isn't).
- If expected: determine the right fix — raise `STALL_THRESHOLD` for Campaign-mode profiles
  specifically, change what counts toward the stall counter, or accept the profile's own quiet
  start and document why 52 ticks is an acceptable/intended real episode length for this profile
  (in which case `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own Finding 3
  should be revisited with that context).
- If a real gap: fix the underlying missing event production, not the stall detector itself.
- Re-run the war/siege/calamity observability question from the originating investigation once
  episodes run to something close to their intended length, to finally answer whether those
  subsystems fire in a real, full-length Campaign-mode run.

## Out of Scope
- The stall detector's own general design/threshold value for non-Campaign-mode profiles — this
  ticket is scoped to `campaign_life_arc`'s specific observed truncation, not a general stall-
  detector redesign.
- Tuning or balancing the war/siege/calamity subsystems themselves once they are observable —
  `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own Out of Scope already
  excludes that; this ticket inherits the same boundary.
- Any performance work. Per standing user direction (2026-09-08), only hard failures are fixed
  here; anything found that is "correct but slower" is deferred to the planned performance effort.

## Acceptance Criteria
- [ ] The stall-detector-triggered truncation is independently re-confirmed (not assumed from the
      originating investigation's own citation alone).
- [ ] A real determination is made: is ~50 ticks of silence at the start of a `campaign_life_arc`
      episode expected content behavior, or a real gap in event production?
- [ ] A disposition is recorded and, if a fix is warranted, implemented with test evidence that
      episodes now run closer to their configured length (or that the shorter length is confirmed
      intended and documented).
- [ ] `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own Finding 3 (whether
      war/siege/calamity fire within a full-length episode) is revisited once episodes run long
      enough to test it for real, and that ticket's own record is updated if the answer changes.

## Related Tickets
- `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT` (origin of this finding; that
  ticket's own Finding 3 explicitly could not answer whether war/siege/calamity fire at full
  episode length because of this truncation)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up.

## Related Code Areas
- `src/engine/scenario_runtime.py` (`ScenarioRuntimeService`, `STALL_THRESHOLD`, the stall
  detector itself)
- `src/domains/campaigns/orchestrator.py` (`CampaignOrchestrator.run_episode()`, the caller)
- `config/simulation_quality/profiles/campaign_life_arc.yaml`

## Assumptions / Open Questions
- Whether the ~50-tick silence is expected narrative-setup quiet time or a real content gap is
  the central question this ticket must resolve — deliberately not decided here.
- Whether the stall detector's own zero-event-tick counting is too strict for Campaign-mode's own
  event cadence, or correctly reflects genuine simulation inactivity, is not determined here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
