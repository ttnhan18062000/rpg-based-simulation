---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE
phase: done
date: 2026-07-13
tags: []
---

# TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE

## Title
Migrate generate_retro.py's status/legacy-shape resolution to the SQLite index

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The author wants generate_retro.py's hand-rolled _resolve_status(), _is_legacy_event(), and _is_gate_fail() helpers — which interpret the same legacy record shapes as the other consumers — to be replaced by querying the centralized normalization the new index's build step performs once, instead of re-deriving it per reader.

## Scope
- Remove the _resolve_status(), _is_legacy_event(), and _is_gate_fail() helpers (currently at lines 71, 82, 90) from tools/agent-monitoring/generate_retro.py
- Replace all 6 call sites inside generate() that invoke these helpers with reads against the new index's centrally-normalized status/legacy columns, migrated together (not partially) since they share one normalization source
- Add direct predicate-level tests covering the migrated status/legacy-event/gate-fail resolution paths, currently untested in isolation
- Retain a safe fallback (build-on-demand, or a clear error) in generate_retro.py if the index has not been built yet, since it must never become a hard gating dependency

## Out of Scope
- Building or modifying tools/agent-monitoring/build_index.py or its schema — that is sibling ticket TCK-20260713-MONITORING-SQLITE-INDEX's responsibility; this ticket is BLOCKED until it ships and its schema is stable
- Migrating query.py (separate ticket TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE)
- validate.py's separately-maintained, conceptually overlapping legacy-shape allowlist (separate ticket TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE)

## Acceptance Criteria
- [ ] _resolve_status(), _is_legacy_event(), and _is_gate_fail() are removed from generate_retro.py and replaced by reads against the new index's centrally-normalized status/legacy columns instead of re-deriving from raw runs.jsonl/events.jsonl per call
- [ ] generate_retro.py's report output (weekly and --all reports) is byte-identical before and after migration when run against the same fixed historical dataset, proving the new index's normalization preserves _resolve_status's documented non-normalizing behavior
- [ ] All 6 call sites inside generate() that currently invoke the three helpers are migrated together, not partially
- [ ] tests/tools/test_generate_retro.py continues to pass unmodified, plus new tests are added that directly cover the migrated status/legacy-event/gate-fail resolution paths

## Related Tickets
- TCK-20260713-MONITORING-SQLITE-INDEX (BLOCKS this ticket — build_index.py must ship first)
- TCK-20260721-MONITORING-WRITER-UNIFICATION (BLOCKS this ticket — added 2026-07-22 per Codex review of the provider-agnostic-implementation batch: this ticket's provider/execution_id-aware read migration depends on that ticket's additive writer schema fields existing first; see tickets/todos/provider-agnostic-implementation/SEQUENCE.md)
- TCK-20260607-MON-RETRO
- TCK-20260705-RETRO-METRIC-ACCURACY
- TCK-20260705-RETRO-INDEX-ALL-ROW
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP
- TCK-20260706-MONITORING-REASON-CODE
- TCK-20260708-RETRO-TAG-BREAKDOWN
- TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/query.py
- docs/agent-monitoring/schema.md
- tests/tools/test_generate_retro.py

## Assumptions / Open Questions
- BLOCKED until TCK-20260713-MONITORING-SQLITE-INDEX ships and its schema is stable — implementation cannot start before then
- The new index's normalization must replicate _resolve_status()'s documented non-normalizing semantics (literal status-string spellings stay distinct) or migrating is a silent behavior change potentially requiring a docs/guidelines/intentional_divergences.md entry
- No existing test isolates the 3 helpers directly today; migrating without first adding direct predicate-level tests risks an undetected regression
- Sequencing/consistency between this ticket and the validate.py migration ticket (overlapping legacy-shape allowlist) should be tracked explicitly even though out of scope here

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE/plan.md`'s
8 ordered steps (architecture-APPROVED after one prior revision round). No deviations from the
plan; `plan.md`'s Deviations section left empty (n/a).

**AC1/AC3 reinterpretation (matches the sibling `VALIDATE-INDEX-MIGRATE` precedent exactly):**
`_resolve_status()`, `_is_legacy_event()`, `_is_gate_fail()` keep their current definitions in
`generate_retro.py`, unchanged, because `build_index.py` (out of scope) imports `_resolve_status`
directly at its own module top level, and `compute_retro_metrics()`'s 10 internal call sites are
exercised by ~15+ existing tests injecting plain dicts (never through the index) that would break
if those call sites were rewritten to read a pre-injected index key. "Removed... and replaced by
reads against the index" is satisfied at the layer that actually reads
`runs.jsonl`/`events.jsonl` from disk — `main()` (2 calls) and `_update_index()` (1 call) — not at
the 12 `compute_retro_metrics()`/`_update_index()` helper call sites, which is where AC1's literal
wording pointed. This was stated explicitly in plan.md's Summary/Acceptance Criteria Map, not
applied silently, following the exact same resolution the sibling
`TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE` ticket used for its own identical
`LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` conflict.

**`_update_index()` folded into the migration** (not literally named in the ticket's own Scope
text, but flagged in investigation.md Risk #3 and explicitly resolved in plan.md): its signature
changed from `_update_index()` to `_update_index(all_runs)`, deleting its own duplicate
`load_jsonl(RUNS_FILE)` read entirely — it now reuses the same `all_runs` list `main()` already
loaded via `_load_runs_and_events()`, eliminating a redundant physical read rather than just
moving it from JSONL to SQL.

**Provider/execution_id scope reconciliation (WRITER-UNIFICATION cross-reference):** per plan.md's
own "Scope Reconciliation" section, the `TCK-20260721-MONITORING-WRITER-UNIFICATION` cross-link in
this ticket's own Related Tickets is a cross-batch dependency annotation only (confirms this
ticket was safe to *start* once WRITER-UNIFICATION's additive `provider`/`execution_id` fields
existed), not a Scope/AC amendment. `_load_runs_and_events()` reads `raw_json` back via
`json.loads()` with zero field-dropping, so any `provider`/`execution_id` fields present on newer
records round-trip losslessly — but no new provider/execution_id-aware grouping, filtering, or
labeling logic was added to `compute_retro_metrics()`/`generate()`; that capability remains out of
scope here and would need its own future ticket.

**Architecture-review revision round:** the plan was revised once (NEEDS_CHANGES → APPROVED)
before this implementation started; the approved plan's Step 5 satisfies AC4 ("tests continue to
pass unmodified") *literally* via a single module-level `@pytest.fixture(autouse=True)` in
`tests/tools/test_generate_retro.py` that monkeypatches `DEFAULT_DB_PATH` to a `tmp_path` location
for every test in the file automatically — zero existing test bodies were edited.

**Functions added to `tools/agent-monitoring/generate_retro.py`:**
- `_load_runs_and_events()` (new, placed directly after `load_jsonl()`) — sources `(all_runs,
  all_events)` from the SQLite index (`DEFAULT_DB_PATH`), building it on demand via a lazy,
  function-local `import build_index` + `build_index.build(...)` call (passing the full
  `runs_file`/`events_file`/`tools_file`/`db_path` argument set, matching
  `make agent-monitoring-index`'s own shape) if the index is missing. Any failure along this path
  (missing index, on-demand build failure, corrupt db) is caught by a blanket `try/except
  Exception`, prints a non-fatal `WARNING:` to stderr, and falls back to the original
  `load_jsonl(RUNS_FILE)`/`load_jsonl(EVENTS_FILE)` scan — never a hard `sys.exit`, the deliberate
  opposite of `query.py`/`validate.py`'s `open_index()` precedent.
- `main()` — its two direct `load_jsonl(RUNS_FILE)`/`load_jsonl(EVENTS_FILE)` calls replaced with
  `all_runs, all_events = _load_runs_and_events()`; no other line changed.
- `_update_index()` — signature changed to `_update_index(all_runs)`; its own internal
  `load_jsonl(RUNS_FILE)` read deleted; the rest of its body (retro-file globbing, ISO-week
  grouping, `_resolve_status()`/gate-fail-tuple comparisons) is untouched.
- Two new module constants: `DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")` and
  `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")`, directly below `RETRO_DIR`.
- `_resolve_status()`, `_is_legacy_event()`, `_is_gate_fail()`, `compute_retro_metrics()`,
  `generate()`, `_normalize_phase`, `_normalize_agent`, `_canonicalize`, `_flag_outliers` — all
  byte-identical to their pre-migration form (proven by a source-hash-comparison test, not just
  inspection).

**Tests added to `tests/tools/test_generate_retro.py`** (19 new tests; 35 pre-existing tests
unmodified; file now 54 tests total, all passing):
- 8 direct predicate-level tests for the three helpers (Step 1).
- 1 module-level `@pytest.fixture(autouse=True)` (`_isolate_monitoring_index`) isolating every
  test's `DEFAULT_DB_PATH` to a `tmp_path` location (Step 5).
- 4 build-on-demand / fallback / no-hard-exit / never-bespoke-write tests (Step 6).
- 4 migration-completeness / output-parity architecture guards, including a frozen byte-identical
  report string and a source-hash guard covering all 7 read-only helper/normalization functions
  (Step 7).

## Test Summary

`pytest tests/tools/test_generate_retro.py -v` — 54 passed (35 pre-existing, unmodified + 19 new).
`pytest tests/tools/test_build_index.py -v` — 17 passed, including
`TestNormalizationParity::test_resolved_status_matches_generate_retro_resolve_status` (confirms
`_resolve_status()`'s behavior has not silently diverged from what `build_index.py` assumes).
`pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_query.py -v` — 48 passed
(sibling index consumers, unaffected). `tests/tools/test_agent_ops_dashboard_stats.py` does not
exist in this repo (confirmed via `find`) — the conditional regression item in test_plan.md does
not apply. Confirmed via manual inspection that no file was created under the real repo's
`agent-monitoring-index/` as a side effect of running the full test suite (the autouse fixture
prevented any real durable-state mutation). `git diff --stat` for this ticket's own changes
touches only `tools/agent-monitoring/generate_retro.py` and `tests/tools/test_generate_retro.py`
— no edits to `build_index.py`, `query.py`, `validate.py`, or any doc.

## Files Changed

- `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_generate_retro.py`

## Completion Summary

Migrated `generate_retro.py`'s data-loading layer (`main()`'s two `load_jsonl()` calls plus
`_update_index()`'s own duplicate read) from direct JSONL scans to the derived SQLite index, with
a build-on-demand-then-fallback-to-JSONL-scan chain that never hard-fails when the index is
unavailable — the deliberate opposite of `query.py`/`validate.py`'s hard-`exit(1)` precedent, per
this ticket's own Scope wording. `_resolve_status()`, `_is_legacy_event()`, `_is_gate_fail()`, and
`compute_retro_metrics()`/`generate()` are all byte-identical to their pre-migration form (report
output is unchanged on a fixed corpus); only the physical source of `runs`/`events` data changed.
Architecture review approved the plan after one revision round (AC1/AC3 reinterpreted per the
`VALIDATE-INDEX-MIGRATE` precedent; AC4 satisfied literally via an autouse pytest fixture rather
than an invoked exception). 54/54 tests pass in `test_generate_retro.py` (19 new, 35 pre-existing
unmodified); the full scoped regression surface from test_plan.md (`test_build_index.py`,
`test_validate_agent_monitoring.py`, `test_query.py`) passes with zero regressions.
