# Investigation — TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY

## The central question and its answer

**Does Campaign SimQ scoring depend on `ScenarioRuntimeService`/`CampaignOrchestrator`'s
`event_recorder` parameter, which only ever receives 3 scenario-bookkeeping event types?**

**No.** This was flagged as potentially the widest-reaching finding in the whole batch — the
possibility that every Campaign SimQ score to date was computed from `scenario_objective_progressed/
completed/stalled` alone, with no combat, cooperation, deaths, or hard-law signal in it at all.
It wasn't. Real evidence, not code-reading alone, settles this.

## Why: two completely separate recorders, same name, no wiring between them

1. `ScenarioRuntimeService.__init__`'s `event_recorder` param (now renamed
   `scenario_event_recorder`, see Disposition below) is only ever called from
   `_evaluate_after_tick()`, at exactly 3 sites (`scenario_runtime.py`, formerly lines 306-308,
   324-326, 360-362). `CampaignOrchestrator` threads its own same-named `self._event_recorder`
   straight through, unchanged. This is the recorder this ticket's title is about, and it is
   genuinely limited to those 3 event types — that part of the original finding was correct.

2. **Separately**, `Kernel.__init__()` (`kernel.py:270`) constructs its OWN internal
   `EventRecorder`, with `enabled=(obs_mode != ObservabilityMode.OFF)`. `ObservabilityConfig.
   get_mode()`'s default is `ObservabilityMode.LIGHT`, not `OFF` (`config.py:310`) — confirmed
   `tools/calibrate_simq.py` never overrides it. This internal recorder is fed the real per-tick
   event stream via `EventExtractor.extract()` → `self._event_recorder.record(event)`
   (`kernel.py:1086`), and is exposed publicly as `Kernel.event_recorder` (a `@property`,
   `kernel.py:1322-1324`).

3. This internal Kernel recorder writes to `data/runs/{kernel._run_id}/simulation_events.jsonl`.
   `ScenarioRuntimeService.run_id` (→ `CampaignOrchestrator.EpisodeSummary.run_id`,
   `orchestrator.py:233`) is literally `self._kernel._run_id` — so this IS the exact per-episode
   file `tools/calibrate_simq.py::_run_campaign_engine()` appends onto the campaign-level
   recorder's own JSONL, and the exact file `_replay_jsonl_through_hub()` replays through
   `QualityHub` for SimQ scoring.

4. The two recorders are fully independent objects that happen to share the attribute name
   `_event_recorder` on two different classes. `ScenarioRuntimeService._build_kernel()` does not
   pass its own `event_recorder` param into `Kernel(...)` construction at all — confirmed by
   reading `_build_kernel()` directly. There is no wiring between them, correct or otherwise;
   they were never connected.

## Empirical confirmation, not just tracing

Ran a real 70-tick `CampaignOrchestrator.run_episode()` (default config — same as
`calibrate_simq.py`'s own real entrypoint, no observability overrides), captured
`summary.run_id`, and read `data/runs/{run_id}/simulation_events.jsonl` directly:

```
episode_run_id: run_1789101299_5169
303 total events across 19 types:
gold_transaction(4), hazard_drain_applied(18), gold_sink_fired(119), world_emergence_event(6),
GovernorModeChanged(1), region_trauma_delta(5), cooperation_event(101), route_selected(2),
action_executed(2), route_family_first_use(2), combat_initiated(3),
combat_engagement_started(3), combat_engagement_ended(17), contract_offer_created(2),
progression_plateau_detected(13), contract_expired_offer(2), near_death_survival(1),
combat_damage(1), xp_granted(1)
```

Not the 2-event bookkeeping-only stream the ticket's own origin test found on the narrow
`scenario_event_recorder` mechanism. This is the real, full per-tick event stream, confirming the
file SimQ actually reads carries real signal.

## Conclusion (record plainly — this is the valuable output)

**Campaign SimQ scoring was never computed from bookkeeping events alone.** The only real
invalidation risk to prior Campaign SimQ measurements was the already-known, already-fixed
empty-world problem (`TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`). A ticket that
closes a live concern with real evidence is worth as much as one that fixes something — this
should read as a closed, evidence-backed concern, not "investigated, nothing to do."

## Disposition: rename, not docstring-only

Per peer review (`rpg-feature-planning`), the disposition for the "no" branch is a rename, not a
comment. Rationale (peer's, verified and agreed):

- The confusion didn't happen from reading a docstring — it happened at the call site, where
  `event_recorder=self._event_recorder` reads as "the event recorder." A parameter name is read
  everywhere the function is called; a docstring only helps whoever opens that one file.
- **Both objects were named `_event_recorder`.** `Kernel._event_recorder`/`.event_recorder` is
  the real full stream; `ScenarioRuntimeService`/`CampaignOrchestrator`'s own `_event_recorder`
  was the narrow bookkeeping channel. Same name, two unrelated things, no cross-reference. That's
  the actual trap this whole investigation exists because of.
- Renamed the narrow one to `scenario_event_recorder` (param + attribute) on both
  `ScenarioRuntimeService` and `CampaignOrchestrator` — 2 real call sites
  (`orchestrator.py`'s own construction of `ScenarioRuntimeService`, and
  `tools/calibrate_simq.py`'s own construction of `CampaignOrchestrator`) plus every test
  construction site. Left `Kernel._event_recorder`/`.event_recorder` untouched — it is correctly
  named; it IS the general event recorder.
- Added explicit cross-reference docstrings in both directions: `ScenarioRuntimeService.__init__`
  and `CampaignOrchestrator.__init__` now name `Kernel.event_recorder` as the real stream;
  `Kernel.event_recorder`'s own docstring now names `scenario_event_recorder` as the unrelated
  narrow side channel. Also added a comment at `tools/calibrate_simq.py`'s own
  `campaign_recorder` construction, since that is the exact site this investigation started from.
- Naming and docs only — no functional change. The narrow recorder's own behavior stays exactly
  as-is; its output is genuinely harmless (it becomes a small additional slice in the final
  merged JSONL once per-episode files are appended, not misleading SimQ).

**One correction made during implementation**: the peer's review named two call sites to rename,
"orchestrator.py:229, kernel.py:1110." Verified `kernel.py:1110` directly before touching
anything — it is `self._cognition_recorder.record_tick(..., event_recorder=self._event_recorder)`,
Kernel passing its OWN correctly-named full recorder into its own cognition-recorder call, wholly
unrelated to the narrow-vs-full naming collision this ticket is about. Left it untouched; flagged
the correction back to the peer rather than renaming a site that didn't need it.
