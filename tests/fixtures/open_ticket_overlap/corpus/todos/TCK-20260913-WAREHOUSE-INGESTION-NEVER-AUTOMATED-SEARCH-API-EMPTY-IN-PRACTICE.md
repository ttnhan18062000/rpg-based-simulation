---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE
phase: open
date: 2026-09-13
tags: [observability, api-design]
---

# TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE

## Title
`search.py`'s 5 live endpoints are empty in practice because the real, working, CLI-invocable warehouse-ingestion step is never automated or run anywhere — an operational gap, not a broken pipeline

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Found while checking `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT`'s and
`TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION`'s own required "check
for a third instance" step. `src/api/routes/search.py` has 5 live endpoints
(`/observability/search/runs`, `/events`, `/anomalies`, `/entity-timeline`, `/metric-trend`)
reading `get_warehouse_adapter()` — the real factory (`src/observability/warehouse/factory.py`),
which resolves Null/ClickHouse/Local backends via `ObservabilityConfig.get_warehouse_backend()`.

**This looked, at first, like a third instance of the same "inert API" shape the two sibling
tickets found — it is not, and peer review confirmed the distinction is real, not just a framing
choice.** `docs/architecture/observability_behavior_profiling_boundary.md` (P1, authoritative)
declares a real 3-stage pipeline: hot-path raw events -> async `BehaviorWorker` sidecar (confirmed
never started, see the sibling ticket) -> **post-run/offline warehouse ingestion** ("Large
JSON/YAML artifact serialization and database/warehouse ingestion"). That third stage is real,
tested, and CLI-invocable today: `make warehouse-ingest RUN_ID=<id>` -> `python3 -m src warehouse
ingest-run` (`src/cli/entry.py`), backed by multiple unit/integration test files
(`tests/integration/observability/test_warehouse_ingestion_dry_run.py`,
`test_clickhouse_ingestion.py`, `tests/unit/observability/warehouse/
test_phase24_behavior_metric_ingestion.py`, and others). Its own `ingest_run()` reads raw run
artifacts from disk directly and reconstructs warehouse records (its own `records_ingested` dict
tracks `runs`/`events`/`anomalies`/`violations`/`metrics`/`behavior_metrics`) -- independent of
whether `BehaviorWorker` ever ran live.

**The real gap: this CLI step is never invoked anywhere in CI or any deployment path** —
confirmed via a search of `.github/workflows/*.yml` (zero references) and the `Makefile`
(`warehouse-ingest` exists as a target, `RUN_ID=<id>` is a manual parameter, never called from
another target). The pipeline is not broken and does not need to be gated — running it produces
correct, real data (per its own test coverage). Nobody has established a habit, script, or
automated trigger for actually running it.

**The principle that separates this from the sibling tickets, stated explicitly per peer review**:
an endpoint that returns empty because no data has been ingested *yet* is honest -- run the ingest
command and it answers correctly. An endpoint that returns empty because *nothing can ever populate
it* is misleading. `search.py` is the first kind (a normal, correctable empty state); `behavior.py`
is the second kind (see the finding below). They look identical to a caller and are structurally
different problems -- `search.py` does not belong in the sibling tickets' gate disposition.

**A related finding, recorded here because it bears on `BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-
API-INERT`'s own eventual wire-vs-defer decision, not this ticket's own scope**: `search.py` reads
the warehouse through the real factory (`get_warehouse_adapter()`, respects
`ObservabilityConfig.get_warehouse_backend()`); `behavior.py` reads it through a **hardcoded
module-level instantiation** (`src/api/routes/behavior.py:10`: `adapter = LocalWarehouseAdapter()`),
bypassing the factory and the backend config entirely, at import time. Two route modules access the
same warehouse family through two different acquisition patterns -- one respecting configuration,
one ignoring it. This is a real parallel-mechanism instance in its own right: wiring the behavior
pipeline for real would need to fix `behavior.py`'s own adapter acquisition too, not just start
`BehaviorWorker` -- whoever picks up that future decision needs this cost named up front, not
discovered mid-implementation.

## Scope
- Determine the real disposition for the ingestion step: should it be automated (a background
  scheduler, a post-run hook, a CI job), or does it deliberately stay a manual operator step (and
  if so, is that documented anywhere an operator would actually find it)? Real product/ops
  question, not pre-judged here.
- Record `behavior.py`'s hardcoded-adapter finding cross-referenced into
  `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT`'s own Related Code Areas, so
  it's visible before that ticket's wire-vs-defer decision is made (not this ticket's own
  disposition to resolve).

## Out of Scope
- Gating or removing `search.py`'s endpoints -- explicitly not the right fix per the principle
  above; its empty state is a normal, correctable one.
- `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT`'s own wire-vs-defer decision --
  cross-referenced, not resolved here.
- Implementing any automation without a peer-routed decision on whether automation is even wanted.

## Acceptance Criteria
- [ ] Real evidence on whether any operator has ever actually run `make warehouse-ingest` against
      real run data in this project's own history (git log, run artifact directories, or an honest
      "no evidence either way").
- [ ] A peer-routed determination: automate ingestion, or document the manual step clearly and
      leave it as-is -- obtained before implementing either.
- [ ] If automated: real evidence the automation actually runs and populates the warehouse from a
      real simulation run, not just a unit test of the ingestion logic in isolation.
- [ ] If left manual: the manual step is documented somewhere a real operator would find it (already
      partially true -- `docs/observability/how_to_run_simulation.md`, `docs/guides/observability.md`
      exist; confirm they're adequate or note the gap).

## Related Tickets
- `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT` (found while checking its own
  "third instance" requirement; the hardcoded-adapter finding feeds that ticket's own future
  decision, cross-referenced there)
- `TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION` (same shape check,
  same conclusion -- this is not a third instance of that pattern)

## Related Docs
- `docs/architecture/observability_behavior_profiling_boundary.md` (the authoritative 3-stage
  pipeline declaration)
- `docs/observability/how_to_run_simulation.md`, `docs/guides/observability.md` (existing
  documentation of the manual ingest step)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/api/routes/search.py` (the 5 live endpoints, left as-is)
- `src/observability/warehouse/factory.py` (`WarehouseAdapterFactory`, the real config-respecting
  acquisition path)
- `src/cli/entry.py` (`warehouse ingest-run`/`ingest-sweep` commands)
- `src/api/routes/behavior.py:10` (the hardcoded adapter acquisition, the related finding)

## Assumptions / Open Questions
- Whether automation is even wanted (vs. a deliberate manual/on-demand step) is the entire point of
  this ticket -- deliberately not pre-judged.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
