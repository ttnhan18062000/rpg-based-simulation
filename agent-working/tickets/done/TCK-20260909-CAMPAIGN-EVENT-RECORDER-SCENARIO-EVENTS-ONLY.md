---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY
phase: done
date: 2026-09-09
tags: [observability, simulation-quality]
---

# TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY

## Title
`ScenarioRuntimeService`'s `event_recorder` parameter only ever receives 3 scenario-level bookkeeping event types, never the kernel-generated combat/cooperation/hard-law stream — DETERMINED: Campaign SimQ scoring reads a separate, unaffected Kernel-internal recorder; renamed to `scenario_event_recorder` to remove the naming collision that caused this investigation

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while writing real test coverage for
`TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`: `ScenarioRuntimeService`'s own `event_recorder`
constructor parameter (`src/engine/scenario_runtime.py`) is ONLY ever called at exactly 3 sites,
all inside `_evaluate_after_tick()`'s own scenario-objective-evaluation logic (lines 306-308,
324-326, 360-362 — `scenario_objective_completed`, `scenario_objective_progressed`,
`scenario_stalled`). It is never passed to `Kernel`'s own `_event_listeners` — confirmed:
`ScenarioRuntimeService._build_kernel()` constructs `Kernel(profile, state, rng, flags={"no_replay":
True})` with no `event_recorder`/listener parameter threaded through at all. `CampaignOrchestrator`
threads its own `self._event_recorder` straight into `ScenarioRuntimeService(spec,
initial_state=initial_state, event_recorder=self._event_recorder)` — the same object, same
limitation.

**Directly confirmed via a real test** (`test_real_campaign_episode_event_stream_is_plausible_not_degenerate`
in `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`): a duck-typed recorder passed
as `event_recorder=` to a real `CampaignOrchestrator.run_episode()`-equivalent call, over 70 real
ticks with real combat happening, received exactly 2 event types
(`scenario_objective_progressed`/`scenario_objective_completed`) and nothing else — zero combat,
cooperation, economic, or hard-law events, despite all of those genuinely occurring in the same
run (confirmed separately by hooking `kernel._event_listeners` directly on the identical
construction, which DID see them).

**Open question, not yet investigated**: `tools/calibrate_simq.py`'s own `_run_campaign_engine()`
constructs a `campaign_recorder = EventRecorder(...)` and passes it to `CampaignOrchestrator`,
then appends each episode's own `data/runs/{episode_run_id}/simulation_events.jsonl` onto the
campaign-level recorder's own JSONL file, and SimQ pillar scoring reads from that combined JSONL
via `_replay_jsonl_through_hub()`. If each episode's own `simulation_events.jsonl` is *also*
produced via this same `event_recorder` mechanism (not yet confirmed — it may instead come from a
separate Kernel-internal replay/telemetry buffer, independent of the `event_recorder` constructor
parameter examined here), then every Campaign-mode SimQ measurement to date may have been
computed from scenario bookkeeping alone — no combat, no cooperation, no deaths — which would be a
materially worse problem than merely "measured on an empty world"
(`TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`'s own finding): it would mean Campaign
SimQ scores are derived from almost no real signal even in a fully-populated, fully-active episode.
**This has NOT been confirmed — it is the central thing this ticket must determine.**

## Scope
- Determine, with real evidence, where each episode's own `data/runs/{episode_run_id}/
  simulation_events.jsonl` file actually comes from — the `event_recorder` parameter examined here,
  a separate Kernel-internal replay/telemetry mechanism, or something else entirely.
- If Campaign SimQ scoring genuinely depends on the impoverished `event_recorder` stream: this is a
  real, consequential bug — determine the right fix (wire kernel-generated events into the
  recorder properly, likely via `kernel._event_listeners`, matching how `V2EngineManager` and other
  live consumers already do it) and route the fix-approach decision through peer review before
  implementing, given this touches shared `ScenarioRuntimeService`/telemetry code, not
  Campaign-only.
- If Campaign SimQ scoring reads from a different, unaffected mechanism: record that as the
  disposition — this ticket's own concern would then be narrower (still worth fixing if
  `event_recorder`'s own 3-event-type behavior is misleading/unused dead weight, but not the
  SimQ-correctness emergency the open question raises).

## Out of Scope
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own entity-spawn wiring — already
  implemented and closed; this is an independently-scoped finding from that ticket's own test
  work.
- Any other SimQ scoring correctness question beyond this specific event-stream question.

## Acceptance Criteria
- [x] Real evidence establishes whether Campaign SimQ scoring depends on `event_recorder`'s own
      3-event-type-only stream. — **NO.** Ran a real 70-tick `CampaignOrchestrator.run_episode()`
      and read the resulting `data/runs/{run_id}/simulation_events.jsonl` directly: 303 real
      events across 19 types (combat, cooperation, economy, hard-law, etc.), not the 2-event
      bookkeeping-only stream. That file is written by `Kernel`'s own separate, internal
      `EventRecorder` (`kernel.py:270`), fed by the real per-tick stream, completely independent
      of `ScenarioRuntimeService`/`CampaignOrchestrator`'s narrow `event_recorder` param.
- [x] If it does not: the disposition is recorded with the real mechanism SimQ actually reads, and
      a decision is made (fix `event_recorder`'s own limited scope anyway, or accept it as
      intentional/harmless) with rationale. — Disposition: **rename, not accept as-is.** Per peer
      review, the behavior is harmless but the shared name (`_event_recorder` on both `Kernel` and
      `ScenarioRuntimeService`/`CampaignOrchestrator`, for two unrelated objects) is exactly what
      caused this entire investigation. Renamed the narrow one to `scenario_event_recorder`
      throughout, with cross-reference docstrings added in both directions.

## Related Tickets
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (origin of this finding)
- `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION` (a related, but distinct, prior finding
  that Campaign SimQ measurements were taken on an empty world — this ticket asks whether they were
  also taken from an impoverished event stream even once the world is populated)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/engine/scenario_runtime.py` (`ScenarioRuntimeService.__init__`, `_evaluate_after_tick()`,
  `_build_kernel()`)
- `tools/calibrate_simq.py` (`_run_campaign_engine()`, the real SimQ-scoring entrypoint for
  Campaign mode)
- `src/observability/event_recorder.py` (`EventRecorder`)
- `src/simulation_quality/quality_hub.py` (SimQ pillar scoring, the eventual consumer)

## Assumptions / Open Questions
- ~~Whether each episode's own `simulation_events.jsonl` comes from `event_recorder` or a
  separate mechanism~~ **Resolved**: a separate mechanism — `Kernel`'s own internal
  `EventRecorder`, not `ScenarioRuntimeService`/`CampaignOrchestrator`'s `event_recorder` param.
  See investigation.md for the full trace and real-run evidence.

## Implementation Notes
Full investigation, plan, and test plan in
`staging_artifacts/TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY/`. Determination
reported to and confirmed by peer review (`rpg-feature-planning`) before implementation, per this
batch's own working agreement.

1. **Determination** (no code changes): traced the two independent `EventRecorder` instances —
   `ScenarioRuntimeService`/`CampaignOrchestrator`'s narrow scenario-bookkeeping one, and
   `Kernel`'s own separate, full-stream one — and confirmed empirically via a real 70-tick episode
   that the file SimQ actually reads (`Kernel`'s own, via `run_id` matching) carries the full real
   event stream (303 events, 19 types), not the impoverished one.
2. **Rename** (`src/engine/scenario_runtime.py`, `src/domains/campaigns/orchestrator.py`,
   `tools/calibrate_simq.py`, and every test construction/attribute-access site): `event_recorder`
   → `scenario_event_recorder` for the narrow, scenario-bookkeeping-only recorder specifically.
   `Kernel._event_recorder`/`Kernel.event_recorder` (the real, correctly-named general recorder)
   is untouched.
3. **Cross-reference docstrings added in both directions**: `ScenarioRuntimeService.__init__` and
   `CampaignOrchestrator.__init__` now name `Kernel.event_recorder` as the real stream;
   `Kernel.event_recorder`'s own docstring now names `scenario_event_recorder` as the unrelated
   narrow side channel. A comment was also added at `tools/calibrate_simq.py`'s own
   `campaign_recorder` construction site, since that's exactly where this investigation started.
4. **One correction made to the peer's review**: they named 2 call sites to rename,
   "orchestrator.py:229, kernel.py:1110." Verified `kernel.py:1110` directly before touching
   anything — it turned out to be `Kernel` passing its OWN correctly-named recorder into its own
   cognition-recorder call, unrelated to the narrow-vs-full naming collision. Left untouched;
   flagged the correction back rather than renaming a site that didn't need it.
5. **One real test miss caught by re-running the full suite, not by a mechanical find-and-replace
   alone**: `tests/unit/domains/campaigns/test_campaign_orchestrator.py`'s own
   `kwargs.get("event_recorder")` assertion was a string-literal dict lookup, not an attribute
   access — a `replace_all` on `self._event_recorder` didn't touch it, and only the actual test
   run caught the resulting failure.

## Test Summary
- Determination evidence: real 70-tick `CampaignOrchestrator.run_episode()` run, `data/runs/
  {run_id}/simulation_events.jsonl` read directly — 303 events, 19 real types (see
  investigation.md for the full breakdown).
- Rename regression: `pytest tests/unit/engine/test_scenario_runtime_service.py
  tests/unit/domains/campaigns/ tests/integration/campaigns/
  tests/integration/scenarios/test_social_memory.py
  tests/integration/tools/test_calibrate_simq_campaign_mode.py -m "not slow and not extra_slow"`
  — 197 passed, 1 skipped, 0 failed (1 real failure caught and fixed mid-pass, see Implementation
  Notes #5).
- Real Campaign episode re-verification (production path, unaffected by the rename):
  `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` (3 `@pytest.mark.slow` +
  1 fast) — 4/4 passed.
- Sanity check (confirms `Kernel`'s own recorder genuinely untouched):
  `tests/simulation_quality/test_calibrate_simq.py`,
  `tests/simulation_quality/test_kernel_simq_integration.py`,
  `tests/unit/observability/test_event_recorder.py` — 23 passed, 0 failed.

## Files Changed
- `src/engine/scenario_runtime.py` — param/attribute rename, cross-reference docstring
- `src/domains/campaigns/orchestrator.py` — param/attribute rename, cross-reference docstring
- `src/engine/kernel.py` — cross-reference docstring only (no rename)
- `tools/calibrate_simq.py` — call-site rename, explanatory comment
- `tests/unit/engine/test_scenario_runtime_service.py` — 4 construction sites
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` — 1 construction site, 1 assertion,
  1 docstring
- `tests/unit/domains/campaigns/test_grief_urgency.py` — 4 attribute-access sites
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` — 1 construction site,
  docstring recording this ticket's own conclusion
- `tests/integration/scenarios/test_social_memory.py` — 1 construction site, 1 comment
- `tests/integration/tools/test_calibrate_simq_campaign_mode.py` — 1 comment
- `staging_artifacts/TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY/` —
  investigation.md, plan.md, test_plan.md

## Completion Summary
**Determined, with real evidence, that Campaign SimQ scoring was never computed from the
impoverished bookkeeping-only event stream** — the potentially widest-reaching risk this whole
follow-up batch had surfaced. A real 70-tick episode's `simulation_events.jsonl` (the exact file
SimQ scoring replays) contains 303 real events across 19 types, not 2. The mechanism: `Kernel`
constructs its own, separate, full-stream `EventRecorder` internally, entirely independent of
`ScenarioRuntimeService`/`CampaignOrchestrator`'s own narrow `event_recorder` parameter — the two
objects were never connected, and shared a name only by coincidence. The only real invalidation
risk to prior Campaign SimQ measurements remains the already-known, already-fixed empty-world
problem. Disposition, per peer review: renamed the narrow recorder to `scenario_event_recorder`
throughout (not a docstring-only fix), since the shared name — not a documentation gap — was the
actual root cause of this investigation ever being needed. Added cross-reference docstrings in
both directions so the next investigator doesn't have to re-run this trace. No functional
behavior changed anywhere.
_(pending)_
