---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY
phase: open
date: 2026-09-09
tags: [observability, simulation-quality]
---

# TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY

## Title
`ScenarioRuntimeService`'s `event_recorder` parameter only ever receives 3 scenario-level bookkeeping event types — never the kernel-generated combat/cooperation/hard-law stream — open question whether Campaign SimQ scoring depends on it

## Status
OPEN

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
- [ ] Real evidence establishes whether Campaign SimQ scoring depends on `event_recorder`'s own
      3-event-type-only stream.
- [ ] If it does: a fix-approach decision is obtained via peer review before implementation, and a
      real test confirms the fix (kernel-generated events reach the recorder/JSONL for a real
      Campaign episode).
- [ ] If it does not: the disposition is recorded with the real mechanism SimQ actually reads,
      and a decision is made (fix `event_recorder`'s own limited scope anyway, or accept it as
      intentional/harmless) with rationale.

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
- Whether each episode's own `simulation_events.jsonl` comes from `event_recorder` or a separate
  mechanism is the central, deliberately-unresolved question this ticket exists to answer.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
