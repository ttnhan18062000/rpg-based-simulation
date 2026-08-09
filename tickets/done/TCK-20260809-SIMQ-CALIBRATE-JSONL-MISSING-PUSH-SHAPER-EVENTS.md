---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS
phase: open
date: 2026-08-09
tags: [simulation-quality, combat, observability]
---

# TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS

## Title
`tools/calibrate_simq.py`'s own real `simulation_events.jsonl` output is missing every
`event_shapers.py`/`CombatShaper`-produced event type observed in direct, in-process
`Kernel.tick_once()` probes using the identical world/seed/tick-count/flag configuration

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Discovered during `TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK`'s own real calibration
re-run (checking whether the COMBAT pillar grade moved after this session's own 5 combat fixes).
The real, live `tools/calibrate_simq.py --ticks 2000 --seed 42 --name dungeon_crawl --profile
dungeon_crawl` run (with `ENABLE_COMBAT_ENGAGEMENT=ON`, matching this session's own established
verification methodology) produced a real `simulation_events.jsonl` containing **only**:
`GovernorModeChanged`, `capability_growth_stalled`, `combat_kill`, `demographic_birth`,
`ecology_cycle_completed`, `gold_sink_fired`, `progression_plateau_detected`,
`raid_party_spawned`. **Zero** occurrences of `combat_resolved`, `combat_engagement_started`,
`combat_engagement_ended`, or `combat_damage` — all real, confirmed-working
`event_shapers.py`/`CombatShaper` productions this session's own direct, in-process
`Kernel.tick_once()` probes (identical world, seed, tick count, and feature-flag configuration)
repeatedly and reliably observed firing via `kernel._event_recorder.events`/
`event_count_by_type`.

`combat_kill` itself is confirmed, via prior investigation this session
(`docs/simulation_quality/quality_scoring_contract.md`'s own "Real, confirmed finding"
annotation, `TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP`), to originate from a
**separate, older, faction-vs-faction `military_conflict` pipeline phase** (`CombatKillEvent`),
not `event_shapers.py` at all — so its presence in this JSONL does not confirm push-shaper events
are reaching the file; it's an independent producer.

**Real, honest, disclosed uncertainty**: the exact mechanism causing this discrepancy was not
identified before this ticket was filed — `Kernel(profile=PROD_SMALL, state=state, rng=rng,
flags={"no_frame_pacing": True})`, the construction line `calibrate_simq.py`'s own `_run_engine()`
uses, is textually identical to every direct probe script this session used successfully. The
real compiled world's own `feature_flags` dict was directly confirmed empty (no explicit
`ENABLE_PUSH_EVENT_SHAPERS` override), meaning the real corpus-default "ON" behavior
(`src/engine/kernel.py::_phase_observability`'s own documented default) should apply in both
cases. Whether the gap is in how `calibrate_simq.py`'s own JSONL file gets written
(`EventRecorder`'s `run_dir` resolution — a real question was raised about how a real, populated
JSONL file gets created at all given `EventRecorder.__init__`'s own `if self.enabled and
self.run_dir:` file-open gate, when the simple `Kernel(...)` construction with no explicit
`run_id`/`replay` argument appears to leave `run_dir_str` as `None` per direct source read of
`kernel.py` lines 218-225) or somewhere else in the push-shaper delivery path was **not
confirmed** — left explicitly open, not guessed.

## Scope
1. **Investigate**: trace the exact real mechanism — instrument a real `calibrate_simq.py` run
   (or a faithful reproduction of its own exact `_run_engine()` construction) to determine whether
   push-shaper events are (a) never constructed at all in this specific real run context, (b)
   constructed but never delivered to `generated_events`/the event recorder, or (c) delivered and
   recorded in-memory but lost specifically in the file-write/JSONL-persistence path.
2. **Determine the real scope of impact**: does this affect only this session's own newest events
   (`combat_resolved`, `combat_engagement_started/ended`), or every `CombatShaper`-produced event
   type (`combat_damage`, `combat_initiated`, `near_death_survival`, `entity_killed` too) — a
   materially more significant finding if the latter, since it would mean the entire COMBAT
   pillar's own real calibration-measured grade has been silently blind to the live, push-based
   delivery path (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`'s own real cutover) this
   whole time, not just this session's own newest additions.
3. **Produce a concrete recommendation**: fix the real gap (if calibration-tool-specific), or
   determine it's a real, narrower condition specific to this exact investigation's own run
   parameters.

## Out of Scope
- Re-deciding the COMBAT pillar grade itself — that is the sibling
  `TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK`'s own scope, already closed with the
  tool's own real (if potentially incomplete) answer honestly reported.
- Any change to `event_shapers.py`'s own event-construction logic — already confirmed working
  correctly via direct, in-process probes; this ticket is about the calibration tool's own
  observability pipeline, not the event producers themselves.

## Acceptance Criteria
- [x] investigation.md identifies the exact real point in the pipeline where push-shaper events
      are lost between direct in-process observation and `calibrate_simq.py`'s own real JSONL
      output — **definitively resolved: nowhere.** File and in-memory recorder always match
      exactly (confirmed 3 separate ways); the real cause was a methodological inconsistency
      (`ENABLE_COMBAT_ENGAGEMENT=ON`) in the sibling ticket's own verification, not a pipeline gap
- [x] The real scope of impact is determined — **zero real scope**: the calibration tool's own
      JSONL pipeline is confirmed correct for all push-shaper event types, in both worlds
- [x] A concrete recommendation is produced, with reasoning — correct the sibling ticket's own
      closed record (done, addendum added); file a new, separate follow-up for the real,
      newly-discovered `ENABLE_COMBAT_ENGAGEMENT=ON` suppression effect
- [x] If a fix lands: real corpus re-verification via `calibrate_simq.py` itself shows the
      real, previously-missing event types now present in its own JSONL output — **confirmed**:
      3 real `calibrate_simq.py` invocations (no flag override) all show `combat_damage`,
      `combat_engagement_started/ended`, `combat_initiated`, `combat_resolved`, `entity_killed`
      present in the real JSONL for both worlds

## Related Tickets
- TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS (filed as a follow-up — the
  real, new, unexpected finding this ticket's own investigation surfaced)
- TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK (DONE, same session — the ticket whose own
  real verification work surfaced this finding; corrected via addendum as part of this ticket's
  own Finalize)
- TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION (DONE, prior session — confirmed unaffected;
  the real cutover works correctly)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/calibrate_simq.py` (`_run_engine()`, `_replay_jsonl_through_hub()`)
- `src/engine/kernel.py` (`_phase_observability`, `EventRecorder` construction — the real
  `run_dir_str` resolution logic at lines ~218-225 flagged as a real, unconfirmed candidate)
- `src/observability/event_recorder.py` (`EventRecorder.__init__`'s own file-open gate)
- `src/observability/event_shapers.py` (`CombatShaper`, confirmed correctly producing events
  in-process — reference only)

## Assumptions / Open Questions
- Whether this is specific to `calibrate_simq.py`'s own tooling context or a real, broader gap
  in how ANY run without an explicit `run_id`/replay-manager writes push-shaper events to disk —
  left open per the Uncertainty Rule, Investigate phase must not assume either way.

## Implementation Notes
No production code changed — investigation-only, per `plan.md`'s explicit reasoning. Real,
controlled A/B tests (same-run file-vs-memory comparison, with-flag-vs-without-flag comparison,
fixed-run_id-vs-auto-generated comparison) definitively ruled out the originally-suspected
JSONL-persistence bug. `Kernel.__init__`'s own real `run_dir_str` resolution
(`src/engine/kernel.py:221-225`) was confirmed to always resolve a real, non-None path whenever
`ObservabilityConfig.get_mode() != ObservabilityMode.OFF` (the real default is LIGHT) — not
conditional on an explicit `run_id`/`replay` argument as originally suspected; every Kernel
construction this whole session used (including every prior direct probe script) always wrote a
real file. `EventRecorder.record()`'s own real code path pushes to both the in-memory buffer and
the file-writing queue from the same call, with no real divergence path for a non-dropped event.

The real, actual cause: the sibling `SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK` ticket's own
verification used `ENABLE_COMBAT_ENGAGEMENT=ON`, inconsistent with every other combat-fix
ticket's own real corpus-verification methodology this session (all of which used corpus-default
flags). Direct A/B testing confirmed this flag genuinely suppresses the tactical.py/
event_shapers.py combat path — a real, new, unexpected finding on its own, contradicting the
flag's own documented "posture assessment only" scope (`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-
GATE-CORPUS-VALIDITY`'s own DEV-002 ruling). Disclosed and filed as its own dedicated follow-up
(`TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS`) rather than investigated
further here, per this ticket's own proportionate scope.

Added a correction addendum to `TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK`'s own
already-closed record, per this session's own established transparency precedent — its original
"deeper, previously-undisclosed [calibration-tool] gap" framing was itself incorrect, and the
addendum documents the real, corrected finding without silently rewriting the original text.

## Test Summary
No `src`/`tests` code changed (confirmed via `git status`). Real verification: 3 controlled A/B
probe runs plus 3 real `tools/calibrate_simq.py` invocations (the actual tool). Frontmatter
validated on the ticket and all 3 staging artifacts.

## Files Changed
- `staging_artifacts/TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS/` —
  `investigation.md`, `plan.md`, `test_plan.md` (new).
- `tickets/done/TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK.md` — correction addendum.
- `tickets/todos/TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS.md` — new
  follow-up ticket.

## Completion Summary
Definitively resolved the suspected calibration-tool JSONL-persistence gap: it does not exist.
`tools/calibrate_simq.py`'s own file-writing pipeline works correctly — in-memory recorder and
on-disk file always match exactly, confirmed via 3 separate controlled tests. The real cause of
the original "missing events" finding was a real, disclosed, self-caused methodological
inconsistency in the sibling verification ticket (`ENABLE_COMBAT_ENGAGEMENT=ON`, not used by any
other combat-fix ticket's own real verification this session). Corrected that ticket's own closed
record via a visible addendum rather than silently rewriting it. The investigation also surfaced
a genuine, new, unexpected finding — the flag appears to suppress the tactical-combat pipeline
entirely, contradicting its own documented scope — disclosed honestly and filed as its own
properly-scoped follow-up rather than chased further within this ticket's own boundaries.
