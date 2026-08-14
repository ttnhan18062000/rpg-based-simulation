---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260721-MONITORING-WRITER-UNIFICATION
phase: done
date: 2026-07-21
tags: [agent-monitoring, dashboard, observability]
---

# TCK-20260721-MONITORING-WRITER-UNIFICATION

## Title
Linux common monitoring writer plus additive reader/query/dashboard support

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Extract one shared Linux-only append-only writer (lock-file protocol, bounded retry, stale-lock recovery, malformed-line handling) that Claude and Codex both route new writes through only once stress/crash/concurrent-writer tests pass; add new fields additively while keeping every legacy record shape readable; update dashboard ingestion to group/filter by provider and execution identity while clearly labeling legacy-unknown records; writer failures stay non-blocking but observable via an out-of-band diagnostic surface. This matters because CLAUDE.md's hard rule requires every implement-ticket run to record a run+event entry with monitoring write failure never blocking the workflow, and the current writer logic is duplicated ad hoc across three call sites.

**Corrected per Codex review (2026-07-22):** this ticket's scope was narrowed to remove `query.py`/`validate.py`/`generate_retro.py` migration work, which belongs to the separate, already-scoped `tickets/todos/agent-monitoring-derived-index/` batch (see Related Tickets) — that batch now depends on this ticket landing first. This ticket also now has an explicit intra-batch dependency on `TCK-20260721-BASELINE-MONITORING-MANIFEST`.

## Scope
- **Entry criterion: consume the read-only baseline manifest produced by `TCK-20260721-BASELINE-MONITORING-MANIFEST`** before any writer change — this ticket's data-preservation claim must be checked against that manifest, not asserted from a clean-tree assumption
- Extract one shared Linux-only append-only writer module (O_CREAT|O_EXCL lock-file protocol, bounded retry, stale-lock recovery, malformed-line handling) used by post_tool_hook.py, record_run.py, and record_events.py — replacing 3 separate ad hoc implementations
- Promote tests/tools/test_monitoring_writer_lockfile_candidate.py's 3 tests to production coverage plus a concurrency+crash-recovery stress test (0 corrupted/interleaved/lost lines) and a simulated stale-lock recovery scenario
- Add new fields (execution_id, provider) additively to new records using the already-decided execution_id format (f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"), while every legacy record shape (5+ generations) remains readable via load_jsonl
- Update src/api/agent_ops_dashboard/ingest.py to group/filter by provider and execution_id, and to visibly label legacy/unknown records rather than dropping them
- Ensure writer failures remain non-blocking to the calling workflow but become observable via an **out-of-band** diagnostic surface (e.g. structured stderr output or a local diagnostic/health file written outside the writer's own append path) — never by attempting to emit a "writer health event" through the same writer that just failed, which would either recurse or silently lose the diagnostic
- **Exit criterion: re-run the baseline manifest against the post-migration corpus and diff against the entry-criterion manifest** — the only allowed differences are explicitly identified new append records; any other change (rewrite, reorder, deletion) fails this ticket's own DoD

## Out of Scope
- Does not implement `query.py`, `validate.py`, or `generate_retro.py` migration to provider/execution_id-aware reads — that is owned by `tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE.md`, `TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE.md`, and `TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE.md`, which depend on this ticket in turn (their own `SEQUENCE.md` was updated in the same review-correction pass to record this cross-batch dependency)
- Does not modify, own, or duplicate the SQLite index schema or build process owned by `TCK-20260713-MONITORING-SQLITE-INDEX`
- Does not enable any non-Linux (Windows/macOS) writer path — Linux-only per decision, other platforms remain BLOCKED
- Does not touch or rewrite historical pre-existing JSONL records (append-only, additive-fields-on-new-records only)
- Does not begin before `TCK-20260721-BASELINE-MONITORING-MANIFEST` has landed and its manifest tooling is available to consume

## Acceptance Criteria

**Amended at Plan phase (2026-07-22):** per `docs/architecture/agent_orchestration_contract.md:150-156`'s
Execution Identity Model (verified by architecture-reviewer to accurately treat `execution_id`/
`provider`/`ticket_id` as one indivisible additive field set), `ticket_id` is added to every AC below
that originally named only `execution_id`/`provider`, so the schema migration is not left half-done
against the higher-authority ADR this epic is built from. See
`staging_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/plan.md`'s own "Amendment to Ticket AC
(Decision #1)" section for full rationale.

- [x] This ticket's entry criterion is satisfied only once `TCK-20260721-BASELINE-MONITORING-MANIFEST`'s manifest tool exists and has been run against the pre-migration corpus to produce a baseline
- [x] A single shared Linux-only append writer module (O_CREAT|O_EXCL lock-file, bounded retry, stale-lock recovery) is used by post_tool_hook.py AND record_run.py/record_events.py — not 3 separate ad hoc implementations (verified by code inspection/import graph)
- [x] Concurrency+crash-recovery stress test (promoted from test_monitoring_writer_lockfile_candidate.py) shows 0 corrupted/interleaved/lost lines across concurrent writers
- [x] A simulated stale-lock recovery scenario test passes (writer recovers from an abandoned lock file)
- [x] New records carry additive execution_id + provider **+ ticket_id (amended)** fields; every legacy record shape (all 5+ documented generations) still loads successfully via load_jsonl with zero exceptions
- [x] dashboard ingest.py can group/filter results by provider and execution_id **+ ticket_id (amended)**, visibly labeling records missing those fields as legacy/unknown rather than silently dropping or erroring on them
- [x] Writer failures do not raise/propagate to fail the calling workflow (non-blocking), and are recorded via an out-of-band diagnostic surface (structured stderr or a separate local health file) — not by routing a "health event" back through the writer itself
- [x] Exit criterion: re-running the baseline manifest tool against the post-migration corpus and diffing against the entry-criterion manifest shows only explicitly identified new append records — zero rewrites, reorders, or deletions of pre-existing lines
- [x] This ticket's scope is explicitly disambiguated from TCK-20260713-MONITORING-SQLITE-INDEX and its 3 reader-migration sub-tickets: no changes are made to the SQLite index schema, its build process, or to query.py/validate.py/generate_retro.py themselves — those tickets consume this ticket's new fields, they are not implemented here

## Related Tickets
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK
- TCK-20260719-LIVE-PHASE-AGENT-LABEL
- TCK-20260719-COST-PROXY-WRITE-PATH
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260607-MON-SCHEMA
- TCK-20260721-BASELINE-MONITORING-MANIFEST (hard predecessor — this ticket's entry/exit criteria consume its manifest tool)
- TCK-20260713-MONITORING-SQLITE-INDEX (dependent — its 3 sub-tickets below now depend on this ticket, not the reverse)
- tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE.md (dependent)
- tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE.md (dependent)
- tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE.md (dependent)

## Related Docs
- docs/ai/monitoring_writer_decision.md
- docs/agent-monitoring/schema.md
- docs/architecture/agent_orchestration_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/vocabulary.py
- tests/tools/test_monitoring_writer_lockfile_candidate.py
- tests/tools/test_post_tool_hook.py
- tests/tools/test_record_run.py
- tests/tools/test_record_events.py
- docs/ai/monitoring_writer_decision.md
- docs/agent-monitoring/schema.md
- docs/architecture/agent_orchestration_contract.md
- src/api/agent_ops_dashboard/ingest.py
- tickets/todos/agent-monitoring-derived-index/ (dependent batch — not modified by this ticket)

## Assumptions / Open Questions
- "Two-writer" concurrency evidence in this ticket is necessarily simulated/synthetic since no real second-provider (Codex) writer exists yet (that lands via the Codex replay/pilot tickets)
- The out-of-band writer-failure diagnostic surface (structured stderr vs. a separate local health file) is new design work for this ticket's Plan phase to choose — it must not route through the writer's own append path
- This concern is explicitly confirmed authorized to modify production writer files (post_tool_hook.py, record_run.py, record_events.py) — not containment-locked like the discovery epic. It is NOT authorized to modify query.py, validate.py, or generate_retro.py — that ownership moved to the agent-monitoring-derived-index batch's sub-tickets per Codex's 2026-07-22 review correction.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/plan.md`'s 11 steps,
in the stated dependency order.

- **Step 1**: Entry-criterion manifest snapshot captured via `manifest.capture_lines()` (imported,
  not reimplemented) and saved to a session-scratch path outside the repo before any writer file
  was touched; discarded after Step 11's diff (never committed).
- **Steps 2+3**: `tools/agent-monitoring/writer.py` created directly in its final Step-3 shape (the
  non-raising, three-region try/except structure with structural — not type-based — exception
  classification, plus the diagnostic sidecar with the single-`os.write()` atomicity commitment).
  Since implementation happened in one pass rather than incremental commits, Step 2's intermediate
  "raise on failure" shape was not separately materialized — the final code matches Step 3's
  corrected structure exactly, including the literal `write_line` shape quoted in the plan.
  `_write_diagnostic` builds its JSON line via `json.dumps` (not manual string escaping) before the
  single `os.write()` call — functionally identical to the plan's description, safer against
  escaping bugs, and preserves the required atomicity (still one `os.write()` syscall).
- **Steps 4-6**: `post_tool_hook.py`, `record_run.py`, `record_events.py` migrated to
  `write_line`/`write_lines`. `execution_id`/`provider`/`ticket_id` added to `tools.jsonl`'s sidecar
  read (additive keys, same `sidecar.get(...) or None` pattern) and to `_RECORD_FIELDS`.
  `record_run.py`/`record_events.py` needed no new code for field passthrough (arbitrary
  caller-supplied dict, not filtered to a fixed key set) — only the new `WARNING:`-on-append-failure
  path (exit 0, distinct from the pre-existing `ERROR:`/exit-1 validation path) was added.
- **Step 7**: Mixed-population concurrency stress test (`write_line` + `write_lines` from separate
  thread populations against the same target) and stale-lock-recovery test added to
  `tests/tools/test_monitoring_writer.py`, asserting the actual lock-file existence transition, not
  just eventual success.
- **Step 8**: `test_locking_failure_does_not_propagate` rewritten to force `os.open` to raise for
  `.lock`-suffixed paths (structural `lock_acquire` classification) instead of monkeypatching
  `fcntl.flock`. **Deviation from the plan's literal description, recorded in
  `staging_artifacts/.../plan.md`'s Deviations section**: the source-string-injection shim
  technique needed an additional `sys.path` fix not anticipated by the plan — see that section for
  detail.
- **Step 9**: Legacy-shape regression test added to `test_agent_ops_dashboard_ingest.py`, reusing
  the 6 real-corpus fixture files verbatim plus one new-format line constructed inline (never added
  to `tests/fixtures/agent_monitoring/`, per the Scope Guard).
- **Step 10**: `RunSummary` gained `provider`/`execution_id`/`ticket_id`/`identity_provenance`
  (Optional, default `None`/`"legacy"`, always explicitly set by `_build_run_summary`).
  `_resolve_identity_provenance()` added next to `_resolve_final_status()`. `get_runs()` gained 3
  new optional filter kwargs following the existing `if x is not None and field != x: continue`
  pattern. `main.py`'s route was intentionally left untouched — the plan's Step 10 file list named
  only `models.py`/`ingest.py`/the ingest test file, not `main.py`.
- **Step 11**: Exit-criterion manifest diff via `assert_prefix_preserved()` passed with zero
  rewrites/reorders/deletions. `runs.jsonl`/`events.jsonl` had 0 new lines (no real CLI invocations
  during this session); `tools.jsonl` gained 51 new lines from this session's own real `PostToolUse`
  hook firings (routed through the new writer — legitimate production behavior, not a test leak).
  No stray `.lock` file and no `.writer_health.jsonl` exist under the real `agent-monitoring/`
  directory.
- **Test-phase regression fix (2026-07-22)**: a broader test sweep beyond the plan's own Step 11
  list (deliberately requested, per this batch's ticket 4/7 precedent of a Test-phase-only regression
  catch) found `tests/tools/test_agent_monitoring_manifest.py::test_writer_files_are_byte_unchanged_by_this_ticket`
  failing — a guard test written for `TCK-20260721-BASELINE-MONITORING-MANIFEST`'s own Out-of-Scope
  line ("must never touch `validate.py`/`record_run.py`/`record_events.py`/`post_tool_hook.py`"),
  unconditionally checking `git diff --stat HEAD` against all 4 files with no ticket-scoping — this
  is the same shape of stale cross-ticket invariant as ticket 4/7's `.codex/`-directory scope-creep
  test. This ticket's own explicit, reviewed scope is to modify exactly 3 of those 4 files (migrating
  their append step to the new shared writer), so the guard's original assertion is now factually
  incompatible with legitimate, approved work. Fixed by narrowing `_WRITER_GUARD_FILES` to
  `["validate.py"]` only (confirmed genuinely untouched by this ticket's diff, per this ticket's own
  Scope Guards) and updating the test's docstring/assertion message to record why, citing this
  ticket by ID. Re-verified: `tests/tools/test_agent_monitoring_manifest.py` — 6 passed.

New test files: `tests/tools/test_monitoring_writer.py` (9 tests),
`tests/tools/test_monitoring_writer_single_source.py` (4 tests, the AST/import-graph guard from the
Acceptance Criteria Map). `tests/tools/test_monitoring_writer_lockfile_candidate.py` left unmodified
per the plan (its 3 tests remain as independent evidence-gathering tests).

## Test Summary

All scoped pytest commands from `test_plan.md`/plan Step 11 pass. Initial implementer-run total: 141
tests across `test_post_tool_hook.py` (6), `test_record_run.py` (18), `test_record_events.py` (22),
`test_monitoring_writer_lockfile_candidate.py` (3, unmodified), `test_monitoring_writer.py` (9, new),
`test_monitoring_writer_single_source.py` (4, new), `test_agent_ops_dashboard_ingest.py` (33),
`test_agent_ops_dashboard_api.py` (8), `test_agent_ops_dashboard_api_boundary.py` (5),
`test_agent_ops_dashboard_concurrency.py` (2), `test_agent_monitoring_legacy_reader.py` (21,
unmodified — confirms the new fixture reuse in Step 9 didn't disturb this file's own independent
coverage).

A Test-phase broader sweep (beyond the plan's own Step 11 list, requested per ticket 4/7's precedent
of a Test-phase-only regression catch) added `test_agent_monitoring_manifest.py` and 11 further files
one hop out via `vocabulary.py`/transitive imports — found and fixed one real regression (see
Implementation Notes: a stale cross-ticket guard test in `test_agent_monitoring_manifest.py`).

**Final combined total**: 253 passed, 0 failed, across all 22 scoped files run
(`tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py
tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_monitoring_writer.py
tests/tools/test_monitoring_writer_single_source.py tests/tools/test_agent_ops_dashboard_ingest.py
tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py
tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_monitoring_legacy_reader.py
tests/tools/test_agent_monitoring_manifest.py tests/tools/test_current_run_sidecar_orchestrator.py
tests/tools/test_codex_capability_diagnostics.py tests/tools/test_monitoring_bypass_fix.py
tests/tools/test_validate_agent_monitoring.py tests/tools/test_agent_ops_dashboard_glossary.py
tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_generate_retro.py
tests/tools/test_registry_query.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py
tests/tools/test_agent_ops_dashboard_serve.py tests/tools/test_dashboard_makefile_targets.py`).
`pytest tests/` was never run (repo policy); all commands were scoped to `tests/tools/`.

## Files Changed

- `tools/agent-monitoring/writer.py` (new)
- `tools/agent-monitoring/post_tool_hook.py` (migrated to shared writer; +3 sidecar fields)
- `tools/agent-monitoring/record_run.py` (migrated to shared writer; WARNING-on-append-failure path)
- `tools/agent-monitoring/record_events.py` (migrated to shared writer via `write_lines`;
  WARNING-on-append-failure path)
- `src/api/agent_ops_dashboard/models.py` (`RunSummary` +4 fields)
- `src/api/agent_ops_dashboard/ingest.py` (`_resolve_identity_provenance`, `_build_run_summary`
  extension, `get_runs()` +3 filter kwargs)
- `tests/tools/test_monitoring_writer.py` (new)
- `tests/tools/test_monitoring_writer_single_source.py` (new)
- `tests/tools/test_post_tool_hook.py` (4 field-set assertions updated, 1 test rewritten, 1 new test)
- `tests/tools/test_record_run.py` (2 new tests)
- `tests/tools/test_record_events.py` (3 new tests)
- `tests/tools/test_agent_ops_dashboard_ingest.py` (4 new tests)
- `tests/tools/test_agent_monitoring_manifest.py` (⚠ cross-ticket edit, flagged explicitly — narrowed
  `test_writer_files_are_byte_unchanged_by_this_ticket`'s `_WRITER_GUARD_FILES` from 4 files to just
  `validate.py`; a file owned by the already-closed `TCK-20260721-BASELINE-MONITORING-MANIFEST`,
  edited here because that test's unconditional guard over `record_run.py`/`record_events.py`/
  `post_tool_hook.py` is factually superseded by this ticket's own explicit, reviewed scope to
  migrate those exact 3 files — see Implementation Notes for full rationale, mirrors ticket 4/7's own
  precedent for this exact situation)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-275` — appended `TCK-20260721-MONITORING-WRITER-UNIFICATION`
  evidence to `v2_evidence` and `test_path`, following that entry's own established cumulative-append
  pattern used by every prior ticket that touched `src/api/agent_ops_dashboard/`. Unlike tickets 1-4
  of this batch, this ticket has real `src/` changes — `models.py`/`ingest.py`'s additive
  `provider`/`execution_id`/`ticket_id`/`identity_provenance` fields — and `INFRA-275` (P2, not P0)
  directly documents that subsystem's contract, so CLAUDE.md's Parity Rule ("when a behavior
  changes, find the relevant entry and update it") applied even though `find_p0_intersection`
  returned empty and this ticket remained parity-skip-eligible for the P0 gate itself)

## Completion Summary

Extracted the 3 previously separate, inconsistent append implementations (`fcntl.flock`-locked,
and two entirely unlocked) behind one shared, production-grade writer module
(`tools/agent-monitoring/writer.py`) exposing `write_line`/`write_lines`, both of which never raise
to their caller — any lock-acquire or write failure is caught internally via structural (not
exception-type-based) classification, recorded to a new out-of-band diagnostic sidecar
(`agent-monitoring/.writer_health.jsonl`, atomic via a single `os.write()` call), and reported back
as a plain `bool`. All 3 call sites (`post_tool_hook.py`, `record_run.py`, `record_events.py`)
migrated their append step only — pre-write validation/CLI contracts untouched. Per the ADR's
Execution Identity Model, all 3 corpus files (`runs.jsonl`, `events.jsonl`, `tools.jsonl`) now
additively carry `execution_id`/`provider`/`ticket_id`, with every legacy record shape still
loading via the existing tolerant `load_jsonl`. The dashboard's `ingest.py`/`models.py` gained
provider/execution_id/ticket_id filtering with an explicit `"native"`/`"legacy"` label, purely
additive.

This plan went through 3 architecture-review rounds — the second round caught a real bug (exception
stage-classification tied to exception type would have misclassified the exact failure scenario
the plan's own test exercises) and an unacknowledged batch-lock-duration starvation risk, both
fixed before Implement began. Architecture-Verify (single pass, APPROVED) confirmed the fixes
landed correctly in code. A Test-phase broader sweep — deliberately requested given ticket 4/7's
precedent of catching a regression two Architecture-Verify passes missed — found and fixed one more
real issue: a stale cross-ticket guard test in `tests/tools/test_agent_monitoring_manifest.py`
whose unconditional "these files must never be touched" assertion was factually incompatible with
this ticket's own explicit, approved scope; narrowed to the one file (`validate.py`) that
invariant still genuinely holds for.

`docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry updated to reflect the additive
dashboard-model changes, per CLAUDE.md's Parity Rule (this ticket has real `src/` changes, unlike
tickets 1-4 of this batch, even though it remained P0-gate skip-eligible).

Final combined test total: 253 passed, 0 failed, across 22 scoped test files. Exit-criterion
manifest diff (`assert_prefix_preserved`) confirmed zero rewrites/reorders/deletions of pre-existing
monitoring lines. No stray `.lock` file, no unexpected `.writer_health.jsonl` entries. All 9
(amended) acceptance criteria satisfied.
