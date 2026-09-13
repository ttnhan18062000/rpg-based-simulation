---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT
phase: done
date: 2026-09-12
tags: [observability, api-design]
---

# TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT

## Title
A fully-built, individually-tested behavior-analytics pipeline was never started — 7 live API endpoints read a warehouse store nothing populates, always empty/404 in production

## Status
DONE

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
- [x] Real evidence on the real intended lifecycle for `BehaviorWorker`: confirmed dormant not just
      today but for over five weeks, via an independent prior investigation
      (`TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION`, 2026-08-05) that already found
      "never instantiated anywhere in `src/` outside its own module and tests." No historical
      commit, config, or deployment script wires it in.
- [x] A peer-routed (and, for this genuine architecture/product-shaped decision, user-routed)
      determination: gate — stop exposing the 7 endpoints by default, keep the implementation.
      Neither wired nor removed.
- [x] A real check of whether any other `src/api/routes/*.py` module has the same shape: found
      `search.py`, confirmed a *different* shape (a real, working, CLI-invocable ingestion path
      simply never automated, not "nothing can ever populate it") — filed separately
      (`TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE`), not gated.
- [x] The disposition is "gate," not "wire" — the wire-only AC item ("real integration-test
      evidence the 7 endpoints return real data end-to-end") does not apply; recorded as still open
      for whichever future ticket picks up the wire-vs-defer decision for real.
- [x] The gate itself is the "explicit, intentional" signal the original deferred-disposition AC
      asked for: by default, `RuntimeProfile.enable_behavior_analytics_api=False` means the routes
      are genuinely unmounted (a real 404, "capability not exposed") rather than mounted-but-silently-
      empty (indistinguishable from "this run genuinely had no behavior events"). No separate
      handler-level "not yet available" response was needed once the disposition is a route-level
      gate.

## Related Tickets
- `TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION` (origin — found while
  investigating 8 of its 10 named flags)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (the parent audit, Cluster C2)
- `TCK-20260911-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION` (the sibling finding
  — same shape, different subsystem; cross-referenced in both directions)
- `TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE` (found while
  checking this ticket's own "third instance" requirement — confirmed NOT a third instance of this
  shape, `search.py`'s empty state is a normal, correctable one; that ticket's own hardcoded-adapter
  finding feeds this ticket's eventual wire-vs-defer decision, see Related Code Areas)

## Related Docs
- `stored_artifacts/TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION/
  investigation.md` (full evidence)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/observability/behavior/` (`BehaviorWorker`, `EpisodeDetector`, `CohortAnalyzer`,
  `RunBehaviorComparison`, `BehaviorMetricsAggregator`, pattern detectors)
- `src/api/routes/behavior.py` (the 7 always-empty endpoints). **New finding (2026-09-13,
  `TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE`)**:
  `behavior.py:10` hardcodes `adapter = LocalWarehouseAdapter()` at module level, bypassing
  `get_warehouse_adapter()`/`WarehouseAdapterFactory` and `ObservabilityConfig.get_warehouse_backend()`
  entirely -- unlike `search.py`, which reads the same warehouse family through the real,
  config-respecting factory. A future wire-vs-defer decision on this ticket must account for fixing
  this acquisition pattern too, not just starting `BehaviorWorker` -- the cost is two problems, not
  one.
- `src/observability/warehouse/adapters.py` (`LocalWarehouseAdapter`, the never-populated store)
- `src/engine/kernel.py:1221` (the misdirecting comment)

## Assumptions / Open Questions
- Whether this is a wiring gap or intentional test-only scaffolding is the entire point of this
  ticket — deliberately not pre-judged. Both are plausible and the answer isn't in the code.
  **Resolved by user decision: gate — neither presumed wiring gap nor removed, deferred pending a
  real wire decision.**

## Implementation Notes
Full investigation (pre-checks, historical lifecycle evidence, third-instance check) recorded in
`stored_artifacts/TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT/investigation.md`.

Added `RuntimeProfile.enable_behavior_analytics_api: bool = False` (`src/config/profiles.py`),
matching `api_key_hashes`'s own fail-closed-by-default precedent. `src/api/server.py::create_v2_app()`
now only calls `app.include_router(behavior.router, ...)` when the flag is `True`. Confirmed
`behavior.py` contains exactly the 7 affected endpoints and nothing else before gating the whole
router.

Found and filed a real third-instance check result as its own ticket
(`TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE`) rather than
folding `search.py` into this disposition, per peer review's explicit confirmation that it is a
structurally different problem (a real, working, CLI-invocable pipeline simply never automated, not
"nothing can ever populate it"). Also recorded, in that same new ticket and cross-referenced here,
that `behavior.py` itself hardcodes its warehouse-adapter acquisition (bypassing the same factory
`search.py` uses) — a second, independent parallel-mechanism cost that whoever eventually revisits
this ticket's own wire-vs-defer decision needs to know about up front.

## Test Summary
New tests in `tests/api/test_inert_route_gating.py` (shared with the sibling ticket, 6 tests, all
pass) prove the gate: disabled by default (real 404), reachable when enabled (real 200/empty
list), gates independent of each other, `search.py` unaffected. Full `tests/api/` regression sweep
(153 passed) confirms nothing existing regressed, including the direct-handler-call tests for this
exact subsystem. `tests/unit/core/test_runtime_profile_contract.py` confirms the new field doesn't
break `RuntimeProfile` construction/immutability.

## Files Changed
- `src/config/profiles.py` — `RuntimeProfile.enable_behavior_analytics_api` field added.
- `src/api/server.py` — `behavior.router` registration gated behind the new flag.
- `tests/api/test_inert_route_gating.py` — new, shared with the sibling ticket.
- `tickets/todos/TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE.md` —
  new ticket, the third-instance check's own real finding.

## Completion Summary
Disposition (gate) was the user's own decision, routed via peer, not picked here. Confirmed both
pre-checks peer required before implementing: nothing real depends on these routes today (zero
frontend, tests call handlers directly), and the `RuntimeProfile`-based startup-config mechanism
follows this repo's own existing `api_key_hashes` precedent rather than inventing a new one.
Historical evidence (a five-week-old prior investigation) independently corroborates the gate
decision — this has been known-dormant, not freshly-discovered. The required "check for a third
instance" surfaced a real finding (`search.py`) that turned out to be a genuinely different problem
shape, filed on its own rather than folded in, per peer review's explicit confirmation of the
distinction. No known material gap left unstated: the wire-vs-defer decision for `BehaviorWorker`
itself remains open, now with two named costs (starting the worker, and fixing its own hardcoded
adapter acquisition) for whoever picks it up next.
