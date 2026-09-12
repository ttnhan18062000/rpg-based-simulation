---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT
phase: open
date: 2026-09-12
tags: [observability, api-design]
---

# TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT

## Title
A fully-built, individually-tested behavior-analytics pipeline was never started — 7 live API endpoints read a warehouse store nothing populates, always empty/404 in production

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION` while
determining why 8 of its 10 named `ObservabilityConfig.is_X_enabled()` flags have zero real
callers. Filed as its own ticket, per peer review's explicit instruction, since the real finding —
a public API surface backed by a data source nothing populates — is a bigger, different-shaped
question than "delete 8 unused flag convenience methods."

`src/observability/behavior/` contains a real, substantial analysis pipeline:
`BehaviorWorker` (the intended top-level entry point/normalizer), `EpisodeDetector`,
`CohortAnalyzer`, `RunBehaviorComparison`, `BehaviorMetricsAggregator`, pattern detectors — each
with its own dedicated test file (`tests/unit/observability/behavior/test_phase{23,24,26}_*.py`,
`tests/integration/observability/test_phase22_behavior_worker_from_{stream,jsonl}.py`). This is
**not** dead or unfinished code — it is built and individually tested.

**`BehaviorWorker(` has zero construction sites anywhere in `src/`** — confirmed directly, not the
generic-name-blind-spot risk this whole audit arc has repeatedly guarded against. It is never
started by the Kernel, the CLI, or the API layer, despite `src/engine/kernel.py:1221`'s own comment
("Wire BehaviorWorker into shutdown: join any running behavior-normalization threads") implying it
is wired in. Confirmed false — the fourth instance this batch of a confident comment describing
behavior that doesn't happen (after `invalidate_read_model`, the survivor-branch placement claim,
and `campaigns.py`'s `register_campaign()` claim).

`src/api/routes/behavior.py` has **7** live `@router.get` endpoints (`get_behavior_events`,
`get_entity_behavior_timeline`, `get_entity_behavior_episodes`, `get_run_behavior_scorecard`,
`get_run_behavior_insights`, `get_run_cohorts`, `compare_run_behavior`) reading from
`LocalWarehouseAdapter` — the exact warehouse store `BehaviorWorker`'s own pipeline would write to,
if it ran. Since nothing populates it, every real request against all 7 returns empty/404, always,
by construction.

**This is the second instance of the same shape in this batch, not a coincidence**:
`TCK-20260911-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION` found the identical
pattern for 2 campaign/chronicle API endpoints (a registry nothing populates in production). Two
instances of "API surface built ahead of the data source meant to feed it" in one batch suggests
this may be systematic in this codebase, not isolated. Cross-referenced in both directions. Whoever
picks up either ticket should treat them as possibly one problem with two faces, and should check
whether any other route module reads a store with no production writer before assuming these are
the only two instances.

## Scope
- Determine which of two real dispositions applies — **this is the open question, deliberately not
  pre-judged here, same as the campaigns/chronicle sibling finding**:
  1. **A wiring gap**: `BehaviorWorker`'s pipeline is meant to run for real (the tests, the
     dedicated API routes, and `kernel.py`'s own comment all suggest intended production use) and
     something never got connected — find the real intended lifecycle hook (kernel startup? a
     background worker thread, matching `BehaviorWorker`'s own apparent thread-based design given
     `kernel.py:1221`'s "join any running behavior-normalization threads" language?) and wire it.
  2. **Test-only scaffolding exposed as production API**: the pipeline was built and tested but
     never intended to run automatically in production (e.g. meant to be operator-invoked, like the
     warehouse CLI ingest commands), in which case the 7 API endpoints should either be gated,
     removed, or given a real trigger path — not silently return empty/404 forever.
- Check whether any other route module in `src/api/routes/` reads from a store with no confirmed
  production writer, per the cross-batch pattern observation above — do not assume campaigns/
  chronicle and behavior are the only two instances without checking.
- Check `src/lab/orchestrator.py`'s own reference to `OBS_BEHAVIOR_NORMALIZATION` (found during the
  origin investigation, a comment only) for any hint of an intended real orchestration path for this
  pipeline that hasn't been traced yet.

## Out of Scope
- `TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION`'s own disposition of
  the 8 related `is_X_enabled()` flags — that ticket documents them as a symptom of this finding,
  not an independent question; this ticket owns the real disposition, that one just names the
  symptom.
- `TCK-20260911-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION`'s own disposition —
  already open as its own ticket, cross-referenced, not merged into this one despite the shared
  shape (the two subsystems are otherwise unrelated).
- Actually implementing either disposition (wire vs. gate/remove) without a peer-routed decision.

## Acceptance Criteria
- [ ] Real evidence on the real intended lifecycle for `BehaviorWorker` (was it ever actually
      started anywhere, in any historical commit, config, or deployment script — not just "not
      started in the current code as read").
- [ ] A peer-routed determination: wire it into the real lifecycle, or formally defer the subsystem
      and stop exposing endpoints that cannot answer — obtained before implementation.
- [ ] A real check of whether any other `src/api/routes/*.py` module has the same "reads a store
      with no confirmed production writer" shape, recorded either way.
- [ ] If wired: real integration-test evidence the 7 endpoints return real data end-to-end (a real
      simulation run → BehaviorWorker processes events → warehouse populated → endpoint returns
      real data), not just a unit test of the pipeline in isolation.
- [ ] If deferred: the 7 endpoints' own behavior when the store is empty is made explicit and
      intentional (a clear "not yet available" response), not a silent empty/404 indistinguishable
      from "this run genuinely had no behavior events."

## Related Tickets
- `TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION` (origin — found while
  investigating 8 of its 10 named flags)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (the parent audit, Cluster C2)
- `TCK-20260911-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION` (the sibling finding
  — same shape, different subsystem; cross-referenced in both directions)

## Related Docs
- `stored_artifacts/TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION/
  investigation.md` (full evidence)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/observability/behavior/` (`BehaviorWorker`, `EpisodeDetector`, `CohortAnalyzer`,
  `RunBehaviorComparison`, `BehaviorMetricsAggregator`, pattern detectors)
- `src/api/routes/behavior.py` (the 7 always-empty endpoints)
- `src/observability/warehouse/adapters.py` (`LocalWarehouseAdapter`, the never-populated store)
- `src/engine/kernel.py:1221` (the misdirecting comment)

## Assumptions / Open Questions
- Whether this is a wiring gap or intentional test-only scaffolding is the entire point of this
  ticket — deliberately not pre-judged. Both are plausible and the answer isn't in the code.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
