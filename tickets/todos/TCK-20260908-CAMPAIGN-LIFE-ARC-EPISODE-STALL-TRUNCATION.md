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
`campaign_life_arc` episodes produce zero kernel `SimulationEvent`s from ~tick 2 onward — the
stall-detector truncation at ~tick 52 is its correct downstream report, not the bug

**Naming note (2026-09-08, peer review `rpg-feature-planning`):** this ticket's original title
("episodes stall and truncate at ~tick 52") named the symptom the stall detector correctly
reports, not the underlying defect — that framing invites the wrong fix (raising
`STALL_THRESHOLD` past 200 makes the ticket's own AC read "closed" while the simulation is still
dead for ~198 of 200 ticks, and disables the one mechanism that was honestly reporting the
problem). Retitled to name the real finding. **Do not fix this ticket by raising
`STALL_THRESHOLD` or otherwise changing what the stall detector counts** — see amended Scope/Out
of Scope below.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
**The real finding: `campaign_life_arc` episodes produce zero kernel `SimulationEvent`s from
roughly tick 2 onward.** The ~tick-52 truncation is the stall detector correctly reporting that
inactivity 50 ticks later — it is the downstream symptom, not the defect. Confirmed directly from
the originating investigation's own event-stream data (18 `world_emergence_event`s, all at tick 1;
`scenario_objective_progressed` is recorded after `kernel.tick_once()` returns each tick and so
never resets the stall counter) — every simulation-quality measurement made against
`campaign_life_arc` to date was measured on a world that stops doing anything after the first tick.

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
- Confirm the "zero kernel events from ~tick 2 onward" finding directly (per-tick
  `_current_tick_event_count` logging across a real `campaign_life_arc` episode), not only via the
  originating investigation's own aggregate JSONL counts.
- Determine WHY the simulation goes event-silent that early — this is the actual defect to find,
  not merely re-confirm the stall detector's report of it. Test the peer-raised hypothesis (not
  yet confirmed — see `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`'s
  cross-reference) that `RuntimeMode.DEGRADED`/`ScanPolicy.EXACT_DIRTY` movement starvation is the
  cause, alongside any other real candidate (e.g. a genuinely quiet, event-sparse narrative-setup
  phase by design — check content/scenario config before assuming a bug).
- If a real gap in event production (or in whatever mechanism should be generating activity) is
  found: fix that underlying cause.
- If the ~50-tick silence is confirmed to be intended, event-sparse content behavior (not a bug):
  document that explicitly as the disposition, with real evidence for why it's intended — do not
  default to this conclusion without positive evidence.
- Once the real silence is fixed (or confirmed intended and something else explains the observed
  truncation), re-run the war/siege/calamity observability question from the originating
  investigation to finally answer whether those subsystems fire in a real, full-length Campaign-mode
  run.

## Out of Scope
- **Raising `STALL_THRESHOLD`, or otherwise changing what the stall detector counts, as a fix.**
  The detector is correctly reporting genuine simulation inactivity — per peer review, this is the
  same class of defect as violating Gate Integrity: the stall detector is a correctness signal,
  not an obstacle, and tuning it to stop reporting the silence would hide the real defect rather
  than fix it. A disposition of "raise the threshold" is not an acceptable closure for this ticket
  under any circumstance short of the event-silence itself being fixed or independently confirmed
  as intended content behavior with real evidence.
- The stall detector's own general design/threshold value for non-Campaign-mode profiles — this
  ticket is scoped to `campaign_life_arc`'s specific observed event-silence, not a general stall-
  detector redesign.
- Tuning or balancing the war/siege/calamity subsystems themselves once they are observable —
  `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own Out of Scope already
  excludes that; this ticket inherits the same boundary.
- Any performance work. Per standing user direction (2026-09-08), only hard failures are fixed
  here; anything found that is "correct but slower" is deferred to the planned performance effort.

## Acceptance Criteria
- [ ] Per-tick `_current_tick_event_count` evidence directly confirms the event-silence (not
      inferred only from the stall detector's own aggregate report).
- [ ] A real determination is made of WHY the simulation goes event-silent: a real gap (e.g. the
      peer-hypothesized `EXACT_DIRTY` movement-starvation link, confirmed or ruled out with real
      evidence) or genuinely intended event-sparse content behavior (with positive evidence, not
      assumed).
- [ ] A disposition is recorded and, if a fix is warranted, implemented with test evidence that
      the simulation produces real activity across the episode (not merely that episodes now run
      to their full configured tick count — running longer while still silent is not a fix).
- [ ] The fix, if any, is NOT a `STALL_THRESHOLD` change or any other alteration to what the stall
      detector counts (see Out of Scope) — verified by checking the diff touches
      `scenario_runtime.py` only if fixing a genuine bug in the detector's own logic (e.g. an
      off-by-one), never its threshold or event-counting policy as a workaround.
- [ ] `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own Finding 3 (whether
      war/siege/calamity fire within a full-length episode) is revisited once episodes run long
      enough to test it for real, and that ticket's own record is updated if the answer changes.

## Related Tickets
- `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT` (origin of this finding; that
  ticket's own Finding 3 explicitly could not answer whether war/siege/calamity fire at full
  episode length because of this truncation)
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` — **hypothesized (not yet confirmed)
  shared root cause**, raised by peer review (`rpg-feature-planning`, 2026-09-08): under
  `RuntimeMode.DEGRADED`/`ScanPolicy.EXACT_DIRTY`, non-urgent entities (including freshly-spawned
  ones with no active AI goal) are permanently excluded from movement candidacy; if most of a
  `campaign_life_arc` episode's entities fall into that category, nothing moves, no movement events
  are generated, `kernel._current_tick_event_count` stays at 0, and this ticket's own stall counter
  climbs to the threshold — one phenomenon (event-silence under `EXACT_DIRTY`), not two unrelated
  bugs. Not traced end to end; the cheap falsification test is logging
  `_current_tick_event_count` per tick in a `campaign_life_arc` episode and checking whether it goes
  to 0 at the same tick `RuntimeMode` enters `DEGRADED`. Whoever picks up either ticket first should
  check this before treating the two as independent.

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
