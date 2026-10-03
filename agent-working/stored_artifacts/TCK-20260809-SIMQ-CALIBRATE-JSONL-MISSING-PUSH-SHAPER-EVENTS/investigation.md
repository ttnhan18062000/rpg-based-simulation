---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS
artifact_type: investigation
tags: [simulation-quality, combat, observability]
---

# Investigation — TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS

## Methodology
Real, controlled A/B tests against real compiled worlds, reading both `kernel._event_recorder`'s
own in-memory event stream AND the real, on-disk `simulation_events.jsonl` file for the
**identical** run (not separate process invocations compared indirectly) — closing the exact
methodological gap the parent ticket's own investigation flagged as unconfirmed.

## Definitively ruled out: this is NOT a JSONL persistence bug
Three separate controlled tests (`dungeon_crawl` with `ENABLE_COMBAT_ENGAGEMENT=ON`,
`urban_political` with the same, `dungeon_crawl` with a fixed `run_id` to rule out RNG-consuming
side effects of Kernel's own auto-generated run-id suffix) all confirm: **the in-memory event
list and the real on-disk JSONL file always match exactly**, event-type-for-event-type,
count-for-count. `EventRecorder.record()`'s own real code path
(`src/observability/event_recorder.py:216-223`) pushes to both `self.events` (in-memory) and
`self.queue` (which the async `QueueDrainWorker` drains to the real file) from the same call,
with no real divergence path for a non-dropped event. There is no real gap here.

Also confirmed and ruled out: `Kernel.__init__`'s own real `run_dir_str` resolution
(`src/engine/kernel.py:221-225`) is **not** conditional on an explicit `run_id`/`replay` argument
as originally suspected — `self._artifact_repo` is auto-created whenever
`ObservabilityConfig.get_mode() != ObservabilityMode.OFF` (the real default is LIGHT, not OFF),
so a real `run_dir` is always resolved and a real file always gets written, for every Kernel
construction this whole session used, including every prior direct probe script.

## Real, actual root cause: a real methodological inconsistency in the sibling ticket, not a bug
Direct, controlled comparison on the identical `dungeon_crawl_seed42` corpus:
- **With `ENABLE_COMBAT_ENGAGEMENT=ON`** (the flag `TCK-20260809-SIMQ-COMBAT-PILLAR-
  RECALIBRATION-CHECK`'s own verification run used): zero `combat_engagement_started/ended`,
  zero `combat_resolved`, zero `combat_damage` in both the in-memory recorder and the real JSONL
  file — confirmed identically across 3 separate real runs.
- **Without the flag** (corpus-default — the real methodology every *other* combat-fix ticket
  this session used for its own verification, `TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`
  through `TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET`): `combat_engagement_ended=10`
  appears immediately in the identical world/seed/tick-count run. Re-running
  `tools/calibrate_simq.py` itself (the real tool, not a hand probe) without the flag confirms
  the same: its own real JSONL output includes `combat_damage`, `combat_engagement_started`,
  `combat_engagement_ended`, `combat_initiated`, `combat_resolved`, and `entity_killed` — all
  present, all correctly persisted.

**The parent ticket's own real verification used `ENABLE_COMBAT_ENGAGEMENT=ON` inconsistently
with the rest of this session's own established methodology** — a real, disclosed, self-caused
error, not a tool defect. `calibrate_simq.py`'s own real JSONL-persistence pipeline works
correctly and is not blind to the push-shaper delivery path.

## New, real, secondary finding — disclosed, not resolved here
`ENABLE_COMBAT_ENGAGEMENT=ON` appears to genuinely **suppress** the tactical.py/event_shapers.py
push-shaper combat path (confirmed via the direct A/B test above — with the flag ON, zero
`combat_engagement_*`/`combat_resolved`/`combat_damage` events across 3 separate runs; without
it, they appear reliably). This is unexpected given the flag's own documented, deliberate scope:
`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`'s own real DEV-002 ruling states the
flag "gates posture assessment [`CombatEngagementPhase`], not damage resolution" — implying it
should have no bearing on the tactical.py-driven `ATTACK` path at all. Whether `ON` genuinely
interferes with tactical decision-making (e.g. by changing entity task state before tactical.py's
own evaluation runs) or this is a real, narrower artifact of this specific test setup was **not
investigated further** — out of this ticket's own proportionate scope (which was the calibration
tool's own JSONL pipeline, now definitively cleared). Filed as its own dedicated follow-up.

## Real COMBAT pillar grade under the correct (corpus-default) methodology
`tools/calibrate_simq.py` (real tool, no flag override), 3 samples: `dungeon_crawl` COMBAT
grade=C, norm ranging -0.0142 to -0.0284 (events 29-32, genuine small-sample variance, matching
this session's own repeatedly-documented combat-event sparsity); `urban_political` COMBAT
grade=C, norm=-0.0290 (events=31). The letter grade is unchanged from the pre-session baseline
in both worlds under this real, correct methodology — a small, real, honest improvement in the
underlying norm is visible in some samples, but not enough to cross a grade boundary at this
corpus's own current combat-activity scale.

## Docs Requiring Update
None — no code or documented contract was found to be wrong; the resolution is a corrected
understanding, not a doc gap.
