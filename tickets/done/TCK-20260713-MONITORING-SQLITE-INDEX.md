---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260713-MONITORING-SQLITE-INDEX
phase: done
date: 2026-07-13
tags: []
---

# TCK-20260713-MONITORING-SQLITE-INDEX

## Title
Build derived, read-only SQLite index over agent-monitoring JSONL logs

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a new build script (tools/agent-monitoring/build_index.py) that reads runs.jsonl, events.jsonl, and tools.jsonl once, normalizes every legacy record shape in one place, and writes the result into SQLite tables (runs, events, tools) plus a normalized view (e.g. a resolved_status column). This mirrors the existing knowledge-index/knowledge.db precedent built by tools/knowledge_search.py: gitignored, derived, rebuildable, never the source of truth. The JSONL files themselves stay exactly as-is (append-only, hook-written) — this is purely a new read-path convenience layer, not a change to the write path. Full rebuild only (no incremental-build logic, since parsing ~47k lines is sub-second), exposed via one Make target (make agent-monitoring-index). Motivation: four independent consumers currently each re-implement their own interpretation/joins of the same raw data.

## Scope
- Create tools/agent-monitoring/build_index.py that reads runs.jsonl, events.jsonl, and tools.jsonl exactly once each
- Normalize every legacy record shape (5+ historical runs.jsonl schema generations per docs/agent-monitoring/schema.md) in one central place
- Write normalized data into a gitignored SQLite database with runs, events, and tools tables
- Produce a resolved_status (or equivalently-named normalized) column/value on the runs table consistent with generate_retro.py's _resolve_status() output and validate.py's LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES allowlists
- Add a single new Make target agent-monitoring-index (no -update variant) alongside the existing agent-monitoring-retro/validate/query/epic-staleness targets
- Add the output SQLite db path to .gitignore
- Implement full-rebuild-only logic (no incremental build)

## Out of Scope
- Migrating query.py, validate.py, or generate_retro.py to actually consume the index (tracked separately as follow-on tickets TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE, TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE, TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE)
- Any change to the JSONL write path (pre_tool_hook.py, post_tool_hook.py, record_run.py, record_events.py) — append-only write behavior must remain untouched
- Adding test coverage to query.py itself (separate migration ticket's responsibility)
- Automatic or hook-triggered index builds — this ticket delivers strictly on-demand builds only

## Acceptance Criteria
- [ ] Running `python3 tools/agent-monitoring/build_index.py` (or `make agent-monitoring-index`) reads all 3 JSONL files exactly once each, writes a gitignored SQLite file with runs/events/tools tables, and exits 0
- [ ] The build script never modifies any of the 3 source JSONL files — byte-identical before/after, verified by hash comparison in a test
- [ ] The runs table's resolved_status (or equivalently-named) column agrees with generate_retro.py's existing _resolve_status() output for every row in the current runs.jsonl
- [ ] The runs table's completeness/terminal-status classification is consistent with validate.py's LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES allowlists, verified on the same fixture data used by tests/tools/test_validate_agent_monitoring.py
- [ ] Re-running the build script twice in a row with unchanged JSONL inputs produces a byte-identical (or row-count-identical) SQLite output both times
- [ ] `make agent-monitoring-index` is defined as a single new Makefile target and the output db path is added to .gitignore

## Related Tickets
- TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE (sibling — depends on this ticket)
- TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE (sibling — depends on this ticket)
- TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE (sibling — depends on this ticket)
- TCK-20260607-MON-SCHEMA
- TCK-20260705-MONITORING-RUNID-JOIN
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX
- TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH
- TCK-20260612-LOCAL-CTX-OPS

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- docs/agent-monitoring/schema.md
- docs/agent-monitoring/README.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- tools/agent-monitoring/query.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/vocabulary.py
- tools/knowledge_search.py
- docs/agent-monitoring/schema.md
- docs/agent-monitoring/README.md
- Makefile
- .gitignore
- agent-monitoring/runs.jsonl
- agent-monitoring/events.jsonl
- agent-monitoring/tools.jsonl

## Assumptions / Open Questions
- Whether resolved_status should be a build-time SQL column/view vs. a Python helper is an open decision to resolve during Scope/Plan
- Whether a Make target or a tools/agent-monitoring/ CLI subcommand is the right home is an open decision (both conventions coexist in this repo); Make target is the author's stated preference
- The index should stay strictly on-demand (no hook-triggered auto-build) per the author's framing
- query.py currently has zero test coverage; this ticket does not address that gap, it is left to the query.py migration ticket
- tools.jsonl is actively growing (~49k lines); normalization logic must handle every legacy shape validate.py/generate_retro.py currently special-case

## Implementation Notes
Implemented `tools/agent-monitoring/build_index.py` following `staging_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/plan.md`'s 8 steps exactly, with one corrective deviation (below).

- `build_index.py` inserts `sys.path` to its own directory and imports `load_jsonl`/`LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES`/`_record_is_complete` from `validate.py`, `_resolve_status` from `generate_retro.py`, and `CANONICAL_TIERS`/`infer_workflow` from `vocabulary.py` — no normalization logic is reimplemented.
- `_create_schema()` creates `runs`/`events`/`tools` tables exactly per the plan's DDL, with non-unique `(run_id, seq)` indexes on `events`/`tools` (no `UNIQUE` constraint, deliberately, per the pause/resume seq-collision precedent).
- `_ingest_runs()` computes `resolved_status` via `_resolve_status(record)` and `is_complete` via `_record_is_complete(record)`, and emits a stderr warning (never fatal) for any `tier` not in `CANONICAL_TIERS`.
- `_ingest_events()` inserts every record as its own row; duplicate `(run_id, seq)` pairs are tolerated by design (no dedup, no unique constraint).
- `_ingest_tools()` skips and warns-to-stderr for the 3 confirmed off-schema `tools.jsonl` shapes.
- `build()`/`main()` wire the full pipeline: unconditional delete-and-recreate of the db file, ingest all 3 files, single `commit()`/`close()`, print a one-line summary, return 0.
- Added `agent-monitoring-index:` Makefile target (interpreter-fallback shell pattern mirroring `knowledge-index:`), not wired into `test:`/`test-quick:`/`test-cov:`/`ci:`/`all:`.
- Added `agent-monitoring-index/` to `.gitignore` (whole-directory ignore, mirroring `knowledge-index/`).

**Deviation from plan (corrective, discovered via live-data verification):** Step 5's literal Python expression (`record.get("run_id") is not None and record.get("seq") is not None`) does not match the plan's own stated intent (Anti-Drift Notes: "Filter on presence/type of `run_id`/`seq`/`tool`, not on matching the specific known record contents"). Running the build against a snapshot of the live `agent-monitoring/tools.jsonl` showed the not-None check incorrectly excluded ~30,372 legitimate interactive-use tool-call records (structurally valid records with `run_id: null, seq: null` but a real string `tool` field — the same class `validate.py::compute_tool_count_drift_report()` already treats as legitimate-but-unattributed, not off-schema) instead of only the 3 confirmed off-schema records. Fixed `_ingest_tools()` to check **key presence** (`"run_id" not in record or "seq" not in record`) instead of value non-nullness, which correctly excludes exactly the 3 off-schema records (verified: `tools: 67723 rows (3 skipped)` against the live corpus, matching `67726` total valid JSON lines). See `plan.md`'s Deviations section for the full writeup.

Verified against a snapshot of the live repo data (`agent-monitoring/{runs,events,tools}.jsonl`, 715/3,773/67,726 lines): build exits 0, produces `runs: 715 rows, events: 3773 rows, tools: 67723 rows (3 skipped)`, source file SHA-256 hashes are byte-identical before/after, and exactly 3 `tools.jsonl` skip warnings + 2 non-canonical-tier warnings are emitted to stderr.

## Test Summary
New: `tests/tools/test_build_index.py` (17 tests, all passing) covering build happy path/schema (AC1), source-file byte-identity (AC2), `resolved_status`/completeness parity with `generate_retro.py`/`validate.py` (AC3/AC4), the `TCK-20260623-TYPE-CHECKER` legacy-shape no-crash guard, off-schema `tools.jsonl` skip-and-warn (including the interactive-use-record false-positive regression this deviation fixed), duplicate `(run_id, seq)` tolerance in `events`, row-count stability across two reruns (AC5), Makefile target + `.gitignore` presence (AC6), and 3 architecture anti-drift guards (no `--incremental` flag, no write-path imports, vocabulary imported not re-encoded).

Regression (unmodified, confirmed still green): `tests/tools/test_validate_agent_monitoring.py` + `tests/tools/test_generate_retro.py` (52 passed), and the write-path guard suite `tests/tools/test_agent_monitoring_legacy_reader.py`, `test_agent_monitoring_manifest.py`, `test_monitoring_bypass_fix.py`, `test_monitoring_writer.py`, `test_monitoring_writer_lockfile_candidate.py`, `test_monitoring_writer_single_source.py` (59 passed).

Commands run:
```
pytest tests/tools/test_build_index.py -v
pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py -q
pytest tests/tools/test_agent_monitoring_legacy_reader.py tests/tools/test_agent_monitoring_manifest.py tests/tools/test_monitoring_bypass_fix.py tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_monitoring_writer_single_source.py -q
```

## Files Changed
- `tools/agent-monitoring/build_index.py` (new)
- `tests/tools/test_build_index.py` (new)
- `Makefile` (new `agent-monitoring-index:` target)
- `.gitignore` (new `agent-monitoring-index/` entry)
- `staging_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/plan.md` (Deviations section added)

## Completion Summary
Built `tools/agent-monitoring/build_index.py`, a full-rebuild-only, on-demand, strictly read-only script that reads `agent-monitoring/{runs,events,tools}.jsonl` and writes a gitignored SQLite index (`agent-monitoring-index/monitoring.db`) with `runs`/`events`/`tools` tables. `resolved_status` and completeness on `runs` reuse `generate_retro.py`/`validate.py`'s existing normalization functions by import; `events`/`tools` tolerate historical `(run_id, seq)` duplicates via a non-unique index; the 3 confirmed off-schema `tools.jsonl` records are skipped with a stderr warning, never coerced or written back. One corrective deviation from the plan's literal Step 5 code (value non-nullness vs. key presence for the `tools.jsonl` validity check) was found via live-data verification and fixed to match the plan's own stated intent, documented in both this ticket and `plan.md`'s Deviations section. `make agent-monitoring-index` and `.gitignore`'s `agent-monitoring-index/` entry are wired and verified via `make --dry-run` and `git check-ignore`. All 17 new tests pass; all named regression suites (111 tests) remain green; a live-corpus dry run confirms byte-identical source files and exit 0. Out-of-scope items (query.py/validate.py/generate_retro.py migration, parity ledger entry, incremental build) intentionally left untouched per the ticket's Out of Scope and the sibling tickets that own them.
