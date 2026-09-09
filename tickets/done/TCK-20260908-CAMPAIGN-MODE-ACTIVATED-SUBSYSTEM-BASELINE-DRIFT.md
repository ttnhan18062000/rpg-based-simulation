---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT
phase: done
date: 2026-09-08
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT

## Title
Campaign-mode baselines and SimQ expectations predate three subsystems that PR #148 activated

## Status
DONE

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
- [x] A definitive list exists of which Campaign-mode baselines/expectations predate `cb0b23b0`:
      **none exist** — confirmed via a real check of `grade_anchors.json`,
      `expected_world_flag_state.json`, and `FAST_ANCHOR_KEYS` (zero Campaign-mode entries in any
      of the three).
- [x] Each observed difference is classified as expected-and-correct or a real regression, with
      evidence, and no difference is left unclassified — N/A, no baseline existed to diff against;
      the one real-run observation made (war/siege/calamity absent within 52-tick episodes) was
      classified honestly as "unknown at intended episode length," not force-classified either way.
- [x] Stale baselines are refreshed with fresh recorded evidence; any real regression found gets
      its own ticket rather than being silently absorbed here — N/A (no stale baseline existed);
      the real, separate finding that surfaced (episode stall truncation) WAS filed as its own
      ticket, `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`, per this same principle.
- [x] If the conclusion is that no baseline actually drifted, that null result is recorded with
      the evidence that supports it — a clean answer is an acceptable outcome. Recorded in
      `staging_artifacts/TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT/investigation.md`.

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

Full investigation in `staging_artifacts/TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT/investigation.md`.
Summary: no Campaign-mode baseline exists in any regression-tracked fixture (`grade_anchors.json`,
`expected_world_flag_state.json`, `FAST_ANCHOR_KEYS` — zero `campaign_*` entries in any of the
three; the one Campaign-mode profile's own calibration test is deliberately marked
`@pytest.mark.slow`, excluded from the fast sweep by design). All 154 existing Campaign-mode
unit/integration tests pass cleanly on current `main`.

Ran `campaign_life_arc` for real (not reasoning from code) both via `calibrate_simq.py` and via a
direct instrumented `CampaignOrchestrator.run_episode()` call inspecting the final
`AuthoritativeState` after each of 3 episodes — confirmed `state.regions`/`.places` genuinely
survive the whole episode (not just tick 1, post-`HOTFIX-STATE-PLACES-APPLY-CARRYFORWARD-GAP`),
but no war declaration, siege, or calamity occurred in any observed episode.

**Peer review (`rpg-feature-planning`) caught a real overstatement in the first draft**: episodes
completed at tick 52, not the configured 200-tick limit, and the initial conclusion ("these
subsystems structurally can't fire in practice") was not actually supported by evidence from a
~26%-length run. Corrected to the honest, narrower claim — war/siege/calamity did not fire within
the 52-tick episodes *observed*; whether they fire at the intended 200-tick length is genuinely
unknown. Traced the truncation's own likely cause cheaply (one grep, not a deep chase, since it
deserves its own scope): `ScenarioRuntimeService`'s stall detector (`STALL_THRESHOLD=50`) pauses
an episode after 50 consecutive zero-event ticks, matching the observed ~52-tick truncation and
corroborated by the JSONL trace's own `3 scenario_stalled` events (one per episode). Filed as its
own ticket rather than resolved here or silently dropped:
`TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`.

Also found, during the survey work that overlapped with `WORLD-MATURITY-START-VALUE-DESIGN`'s own
Scope (both tickets share the same peer-recommended sequencing), that
`docs/world/raid_boss_camp_contract.md`'s own "Boss spawn conditions" incorrectly says
`camp.maturity >= 50` — the real code (`src/world/boss.py:92,218`) uses `state.maturity`
(a global, not per-camp, value) for both `check_for_boss_spawn` and `check_for_lair_spawn`. Not
fixed as part of THIS ticket (out of its own named scope, a doc-parity nit unrelated to baseline
drift) — noted here for traceability; corrected as part of `WORLD-MATURITY-START-VALUE-DESIGN`'s
own work instead, since that ticket already touches this exact doc section.

**Addendum (2026-09-08, post-closure, peer review during `DIRTY-SET-PASSIVE-DECAY-CONSUMER-
INVESTIGATION`'s pickup):** the "did not fire within the 52-tick episodes observed" wording above
is itself still weaker than what the evidence actually supports. Independently confirmed by reading
`ScenarioRuntimeService._evaluate_after_tick()` (`src/engine/scenario_runtime.py:340-357`) and
`Kernel.tick_once()`'s event-count computation (`src/engine/kernel.py:1000-1078`,
`generated_events = EventExtractor.extract(...)` plus grief/shaper/violation/governor-mode events):
the stall counter increments on **any** tick where the kernel produced **zero** `SimulationEvent`
objects of **any** kind — not just war/siege/calamity events. `STALLED` fires at
`stall_counter > 50`. The observed ~52-tick truncation therefore means these episodes produced no
simulation events of any kind for roughly 50 consecutive ticks starting around tick 2, not merely
"no war/siege/calamity events." The correct, stronger claim: **these 52-tick episodes tell us
nothing about whether war/siege/calamity can fire, because the simulation itself went event-silent
almost immediately — the runs were effectively dead, not merely short.** This does not change the
ticket's own disposition (no baseline exists to refresh, no code change warranted by this
investigation) but corrects the evidentiary framing above. See
`TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION` (cross-referenced with a hypothesized,
not yet confirmed, shared root cause with
`TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`) for the actual resolution of why the
simulation goes silent.

## Test Summary
- `grep -rn "campaign" tests/simulation_quality/fixtures/grade_anchors.json
  tests/simulation_quality/fixtures/expected_world_flag_state.json` — zero hits, confirmed twice
  (investigation and closure).
- `pytest tests/integration/campaigns/ tests/unit/domains/campaigns/ -m "not slow and not
  extra_slow"` — 154 passed, 0 failed, confirmed twice (investigation and closure).
- Real `campaign_life_arc` runs (both `tools/calibrate_simq.py --seed 42 --ticks 200` and a direct
  instrumented `CampaignOrchestrator.run_episode()` call across 3 episodes) — real state
  inspection, not inference.

## Files Changed
- `staging_artifacts/TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT/` (investigation.md,
  plan.md, test_plan.md — new).
- `tickets/todos/TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION.md` (new, filed not
  implemented).

No `src/`, `tests/`, or fixture file changed — this ticket produces no baseline refresh because no
baseline existed to refresh.

## Completion Summary
Investigated whether Campaign-mode baselines/fixtures/SimQ expectations drifted after PR #148
reactivated three previously-dormant subsystems. Found no such baseline exists anywhere in this
repo's regression-tracked fixtures to begin with — Campaign mode's one profile
(`campaign_life_arc`) was never added to the fast SimQ regression sweep, by design (its own
calibration test is marked `@pytest.mark.slow`). All existing Campaign-mode tests pass cleanly.
A real-run observation (war/siege/calamity did not fire within observed 52-tick episodes) was
initially overstated as a structural conclusion; caught by peer review and corrected to the
honestly narrower claim, with the actual cause of the episode truncation (a stall-detector timeout)
traced and filed as its own separate, real ticket rather than resolved as an aside or dropped
silently. Post-closure addendum (see Implementation Notes) further corrected the framing: the
52-tick episodes produced zero simulation events of any kind for ~50 consecutive ticks, not merely
zero war/siege/calamity events — the runs were event-silent, not just short, so no observation from
them bears on subsystem reachability either way. No baseline refresh and no code change are
warranted by this investigation itself.
