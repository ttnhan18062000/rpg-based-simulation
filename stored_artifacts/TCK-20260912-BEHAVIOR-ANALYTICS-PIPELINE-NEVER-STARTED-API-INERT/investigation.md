# Investigation — TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT

## Disposition: gate (user decision, routed via peer)

Two dispositions were possible per this ticket's own Scope: (1) a wiring gap, wire `BehaviorWorker`
into the real lifecycle, or (2) test-only scaffolding, gate/remove/redesign. The user decided (2),
specifically gate: "stop exposing them, keep the implementations... gate registration behind a flag
that's off by default." Both subsystems (`behavior.py` here, `campaigns.py`/`chronicle.py` in the
sibling ticket) are fully built and individually tested; deleting would mean rebuilding if the data
sources are ever wired, and that wire-vs-defer question stays genuinely open.

## Pre-check 1: is anything real calling these endpoints today?

- Zero frontend references anywhere (`frontend/src/` clean).
- `tests/api/test_phase27_behavior_query_api.py` explicitly documents "Call the route handler
  directly (no HTTP layer needed)" — imports and calls the handler functions directly, never goes
  through `create_v2_app()`'s router registration. Gating registration breaks nothing here.
- No integration test touches `TestClient`/`create_v2_app`/`api/v1` for this subsystem; the
  adjacent-looking integration tests (`tests/integration/observability/test_phase2{2..7}_*.py`)
  exercise `BehaviorWorker`'s own pipeline directly, not the HTTP layer.
- Safe to gate registration with zero test fallout.

## Pre-check 2: precedent for gated route registration

`src/api/server.py`'s `create_v2_app()` registers all 15 routers unconditionally — no existing
precedent for conditional route registration specifically. A related, live mechanism exists —
`FeatureFlagManager`/`FeatureMode` (`src/domains/optimization/feature_flags.py`), used by
`pipeline.py`'s `run_phase()` to gate tick-level phases ON/OFF/SHADOW — but it is
`AuthoritativeState`-scoped (configured via `state.rollout_profile`/`feature_flags`), and no
`AuthoritativeState` exists at server-startup time when routers get registered, so it does not fit.
The real precedent is `RuntimeProfile.api_key_hashes`'s own "empty/false means disabled,
fail-closed by default" pattern, already env-var-configurable via `ConfigLoader`'s generic bool-field
loop (`src/config/loader.py:54-70`) with zero extra loader code needed for a new bool field.

## Real intended lifecycle for `BehaviorWorker` — confirmed dormant historically, not just today

A prior, already-closed investigation (`TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION`,
2026-08-05, over five weeks before this ticket) independently confirmed: "`BehaviorWorker`... is
never instantiated anywhere in `src/` outside its own module and tests — no engine wiring at all,"
and recommended reviving narrowly (episode/category detection) only if ever needed, while noting
the scorecard's 6 numeric fields have "zero production computation logic anywhere" and "must be
designed from scratch regardless of substrate." Independently re-confirmed today via direct
construction-site grep: `BehaviorWorker(` has zero real construction sites. `kernel.py:1221`'s own
comment ("Wire BehaviorWorker into shutdown...") is confirmed false, not aspirational — the fourth
instance this arc has found of a confident comment describing behavior that doesn't happen. This is
strong, multi-week-spanning evidence supporting "gate" over "we just forgot to wire it" — it has
been known dormant for over a month with no wiring attempt in between.

## Check for a third instance — found one, ruled it NOT a third instance of this shape

`src/api/routes/search.py` has 5 live endpoints reading `get_warehouse_adapter()` — the real
factory (`WarehouseAdapterFactory`), respecting `ObservabilityConfig.get_warehouse_backend()`.
`docs/architecture/observability_behavior_profiling_boundary.md` (P1, authoritative) declares a
real 3-stage pipeline: hot-path -> async `BehaviorWorker` sidecar -> post-run/offline warehouse
ingestion (`make warehouse-ingest` -> `ingest_run()`, real, tested, CLI-invocable, never run in CI
or any deployment path found). Per peer review's own framing: an endpoint empty because no data has
been ingested *yet* is honest (run the ingest command and it answers correctly); one empty because
nothing can ever populate it is misleading. `search.py` is the first kind — filed separately
(`TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE`), not gated, not
folded into this ticket.

**Related finding recorded for this ticket's own future wire-vs-defer decision, not resolved
here**: `behavior.py:10` hardcodes `adapter = LocalWarehouseAdapter()` at module level, bypassing
the factory and `ObservabilityConfig.get_warehouse_backend()` entirely — unlike `search.py`, it
cannot be pointed at a populated backend by configuration even if one existed. Wiring the behavior
pipeline for real would need to fix this acquisition pattern too, not just start `BehaviorWorker`.

## `src/lab/orchestrator.py`'s `OBS_BEHAVIOR_NORMALIZATION` reference

Confirmed comment-only, no real orchestration hook found for this pipeline beyond what's already
documented as dormant.
