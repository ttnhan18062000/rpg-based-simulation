---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP
phase: done
date: 2026-09-25
tags: [observability, testing]
---

# TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP

## Title

Fix live read sites still targeting the retired flat `agent-monitoring/{runs,events,tools}.jsonl` files

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

The user asked agent-working-design to check whether `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX`'s
write-side fix (routing every write through one shared resolver) had a read-side counterpart —
i.e., whether anything still reads the OLD flat `agent-monitoring/{runs,events,tools}.jsonl` paths,
which have not existed at all since `TCK-20260902-MONITORING-SHARD-WRITE-PATH`'s sharding
migration (independent of and predating this epic). Two confirmed real bugs were found and
relayed:

- `.claude/workflows/implement-epic.js:384` — `grep -c "\"run_id\":\"${batchRunId}\""
  agent-monitoring/events.jsonl` — silently reports 0 (the file doesn't exist, so `grep` errors
  without a match), meaning implement-epic runs have been unable to verify their own monitoring
  coverage for three weeks.
- `.claude/workflows/simq-audit.js:67` — `f = Path('agent-monitoring/tools.jsonl')`, used to
  compute `tool_call_count`/`cost_proxy_score` per agent seq — silently yields nothing, zeroing
  `cost_proxy_score` for every simq-audit run since 2026-09-02.
- `.claude/workflows/implement-ticket.js:597` names the old path too, but only in a comment.

The user's explicit instruction, relayed: fix both real bugs on this same PR (not a follow-up),
and **sweep for every read-side construction of a monitoring file path** the way the write side was
swept — "I fixed the ones I found" produced both rounds of this defect.

## Scope

A full, two-pass sweep found this to be **much larger than the two named bugs** — not just literal
flat-path string constructions, but a whole class of glob helpers that narrowed to the *bare*
per-week filename (`data/<week>/<source>.jsonl`) and never matched the *per-identifier* shape
(`data/<week>/<id>.<source>.jsonl`) introduced by the per-ticket scheme and now the per-PR/branch
one. **11 real fixes across 9 files**, not 2:

**Pass 1 — literal retired flat-path constructions** (`grep -rn` for
`agent-monitoring/{runs,events,tools}.jsonl` across `.claude/workflows/`, `tools/`, `src/`):

1. `.claude/workflows/implement-epic.js:384` — the `grep -c` verification command now targets the
   real per-branch sharded file via a small `python3 -c` snippet using
   `monitoring_batch_identifier.resolve_write_target()`.
2. `.claude/workflows/simq-audit.js:67` — the tool-call-count computation snippet now uses
   `resolve_write_target('tools')` instead of a hardcoded `Path('agent-monitoring/tools.jsonl')`.
3. `.claude/workflows/implement-ticket.js:419,597,1948` — three stale-doc mentions of the retired
   flat-path shape in LLM-facing prose (only line 597 was originally named; 419 and 1948 were
   found in this ticket's own sweep). Guidance-only, never drove executable logic, but corrected
   to the current per-branch-identifier shape while already in the file.
4. `tools/gate_checks/status_drift_check.py` — `DEFAULT_RUNS_PATH` (a single hardcoded flat file)
   replaced with the corpus-wide, multi-week `validate.load_data_glob()` read. **Confirmed by
   direct execution: this crashed with `FileNotFoundError` before the fix** — a different failure
   shape than the two silent-zero bugs (loud, not silent), but real, live, and wired bare into
   `make status-drift-check`. The function's own signature changed from a single `runs_path: Path`
   to `data_dir: Path` — this is a genuine behavior improvement (checks the WHOLE corpus across
   every week, not one flat snapshot that never existed post-migration), not a compatibility shim.

**Pass 2 — narrow week-only glob helpers, found by grepping for the `glob(f"*/{...")` shape itself**
after Pass 1 surfaced the pattern (`validate.py`'s own `load_data_glob` was the first one found and
fixed, which is what made the shape searchable):

5. `tools/agent-monitoring/validate.py::load_data_glob_with_line_count()` — the single most
   consequential fix: this function backs `done_checker_static.py`, `verify_referential_integrity.py`,
   `monitoring_anomaly_validator.py`, `duplicate_run_record_check.py`,
   `tool_call_count_mismatch_check.py`, and others. **Confirmed by direct execution before the
   fix: `load_data_glob(Path("agent-monitoring/data"), "runs")` returned 0 matches for this
   branch's own real, just-closed `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX` run record.**
6. `tools/gate_checks/done_checker_static.py::_jsonl_rows_for_run_id_across_weeks()` — backs
   `check_monitoring_write_recorded()`, the Finalize-time gate verifying a ticket's own monitoring
   write landed. **Confirmed by direct execution: this gate FAILed for
   `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX`'s own real closure before this fix** (non-blocking
   per CLAUDE.md's Hard Rule, so it never surfaced as a hard failure — exactly why it went
   unnoticed).
7. `src/api/agent_ops_dashboard/ingest.py::_week_shard_paths()` — **the actual dashboard backend.**
   Before this fix, the dashboard was blind to every ticket closed under the per-ticket or
   per-PR/branch schemes.
8. `tools/agent_replay_codex/monitoring_shards.py::source_paths()`.
9. `tools/agent-monitoring/manifest.py::_source_paths()` — backs
   `tools/agent_replay_codex/containment.py`'s `snapshot_monitoring_lines`/
   `assert_monitoring_prefix_preserved` append-only guard.
10. `tools/agent-monitoring/bash_command_mix.py::week_shards()`.
11. `tools/agent-monitoring/generate_retro.py::_source_mtime()` — feeds the SQLite index's own
    staleness detection; a per-branch shard's mtime wasn't being considered, risking a
    stale-but-reported-fresh index.

**Pass 3 — a related but distinct containment gap, found while reading `manifest.py`'s own
consumer**:

12. `tools/agent_replay_codex/containment.py` — `_WATCHED_GIT_PATHSPECS` listed the three retired
    flat paths as the git-diff pathspecs this mechanism watches for unexpected agent-monitoring
    writes during codex pilot/replay runs, and `_watched_files()` globbed the bare top-level
    `agent-monitoring/*.jsonl` (not even the `data/` subfolder). **Confirmed by direct test: a real
    mutation to a real per-branch-shaped monitoring file went completely undetected before this
    fix** — a silent gap in an isolation/safety mechanism, not merely a stale metric. Fixed by
    watching the whole `agent-monitoring/data/` directory (a directory pathspec, not enumerated
    filenames, so it does not need updating again the next time the identifier shape changes, as
    it already has twice).

## Out of Scope

- The separate, explicitly read-only investigation of the 7 `.claude/workflows/*.js` files that
  emit no monitoring records at all (`investigate-simulation-result.js`,
  `register-simulation-result.js`, `update-knowledge-store.js`, `compact-simulation-result.js`,
  `generate-simulation-setup.js`, `prepare-simulation-execution.js`,
  `propose-simulation-enhancements.js`) — reported separately, not implemented, per the user's
  explicit instruction that this is investigate-and-report only. See the separate investigation
  report relayed to agent-working-design/the user; no ticket filed for it.
- Any further sweep beyond `.claude/workflows/`, `tools/`, `src/` — two full passes (literal
  flat-path strings, then the narrow-glob-helper shape itself) were run and re-verified clean
  after all fixes landed (zero remaining `glob(f"*/{...")`-shaped monitoring reads without a
  paired per-identifier widening). `dashboard-frontend/` was not searched — it does not read
  `agent-monitoring/` files directly, only the dashboard API `ingest.py` already fixed here.
- Consolidating all ~8 independent glob-widening call sites into one shared helper (mirroring
  `monitoring_batch_identifier.resolve_write_target()`'s write-side consolidation) — each fix here
  is the same minimal, already-proven-safe one-line widening applied locally, not a deeper
  refactor. A shared read-side helper is a reasonable future improvement but a larger, riskier
  change (several of these call sites have their own subtly different fallback/legacy-shape
  semantics — see `manifest.py`'s and `ingest.py`'s own scratch-shape fallback docstrings) than
  this hotfix's job.

## Acceptance Criteria

1. `implement-epic.js`'s Step 2b verification command targets the real sharded per-branch file,
   not the retired flat one.
2. `simq-audit.js`'s tool-call-count/cost-proxy-score computation reads the real sharded
   per-branch file, not the retired flat one.
3. All three stale-doc mentions in `implement-ticket.js` (lines 419, 597, 1948) are corrected to
   describe the current per-branch-identifier shape.
4. `status_drift_check.py`'s corpus-wide check no longer crashes when invoked bare (matching its
   Makefile wiring) against the real, current sharded corpus — confirmed by direct `make
   status-drift-check` execution, not just unit tests.
5. `containment.py`'s watched pathspecs and hashed files cover the real current write targets —
   confirmed by a test that plants a real mutation to a real per-branch-shaped file and asserts
   detection fires, not just that the mechanism runs without error.
6. `validate.py::load_data_glob()`, `done_checker_static.py`'s `check_monitoring_write_recorded()`,
   `ingest.py`'s dashboard read path, `monitoring_shards.py`, `manifest.py`, `bash_command_mix.py`,
   and `generate_retro.py`'s staleness-mtime check all find a per-identifier-shaped shard, each
   confirmed by a dedicated test proving detection (not just that the code runs).
7. Full sweep re-run after all fixes land shows zero remaining literal flat-path constructions or
   un-widened narrow week-only globs in `.claude/workflows/`, `tools/`, `src/` (excluding
   historical/comment mentions explicitly describing the pre-migration shape for context, e.g.
   `workflow_meta_conformance.py`'s own already-correct "was retired... in favor of" comment).
8. Existing tests for every touched file still pass; full `tests/tools/ tests/agent_replay_codex/
   tests/api/` regression run clean.

## Related Tickets

- `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX` — the write-side fix and shared resolver
  (`monitoring_batch_identifier.py`) this ticket's read-side fixes build on.
- `TCK-20260902-MONITORING-SHARD-WRITE-PATH` — the original sharding migration that retired the
  flat files these reads still (wrongly) target.

## Related Docs

None requiring update — this ticket corrects code and in-code prose, not standalone documentation.

## Related Stored Artifacts

None (hotfix tier, no staging artifacts required).

## Related Code Areas

- `.claude/workflows/implement-epic.js`
- `.claude/workflows/simq-audit.js`
- `.claude/workflows/implement-ticket.js`
- `tools/gate_checks/status_drift_check.py`
- `tools/gate_checks/done_checker_static.py`
- `tools/agent-monitoring/validate.py`
- `tools/agent-monitoring/manifest.py`
- `tools/agent-monitoring/bash_command_mix.py`
- `tools/agent-monitoring/generate_retro.py`
- `tools/agent_replay_codex/monitoring_shards.py`
- `tools/agent_replay_codex/containment.py`
- `src/api/agent_ops_dashboard/ingest.py`

## Assumptions / Open Questions

None — every fix in Scope is a confirmed-real, directly-verified defect (either by reasoning
about the file's own existence, or by direct execution — `status_drift_check.py`,
`validate.py::load_data_glob`, `done_checker_static.py::check_monitoring_write_recorded`, and
`containment.py`'s mutation-detection were each confirmed broken before the fix and confirmed
fixed after, via a real invocation, not just a unit test in isolation).

**Tier note**: this ticket grew from 2 named bugs to 11 fixes across 9 files during its own
mandated sweep — file *count* is large, but every fix is the identical, minimal, mechanical,
already-proven-safe one-line glob-widening pattern (no design decision repeated per site, no new
abstraction introduced per site). Kept at hotfix tier on that basis — the nature of each change is
self-evident and targeted, matching hotfix's own definition, even though the number of call sites
touched is larger than this repo's typical hotfix. Full regression (3238 tests) stayed green
throughout, run after every individual fix and again at the end.

## Implementation Notes

Ran two sweep passes rather than one, per plan: Pass 1 (`grep -rn` for the literal retired
flat-path strings) found the 2 originally-named bugs plus 2 more stale-doc mentions in
`implement-ticket.js`. Fixing `validate.py::load_data_glob` (needed for `status_drift_check.py`'s
own fix) made the underlying SHAPE of the defect class visible — narrowed to `glob(f"*/{...")`
without a paired per-identifier widening — which turned Pass 2 (grepping for that shape directly)
into a much larger, second real finding: 7 more independent glob helpers sharing the exact same
narrow pattern, including the actual dashboard backend (`src/api/agent_ops_dashboard/ingest.py`)
and `done_checker_static.py`'s own Finalize-time monitoring-write-verification gate. Every one of
these was confirmed broken by *reasoning* about it, then in the two most consequential cases
(`load_data_glob`, `check_monitoring_write_recorded`) confirmed by *direct execution* against this
branch's own real, already-closed `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX` run record before
fixing, and confirmed fixed by re-running the exact same command after.

Deliberately did NOT consolidate all ~8 read-side glob call sites into one shared helper (mirroring
`monitoring_batch_identifier.resolve_write_target()`'s write-side consolidation) — each fix applies
the same already-proven-safe one-line widening locally instead. Checked each site's own existing
fallback semantics first (several have their own legacy/scratch-shape fallback docstrings,
e.g. `manifest.py`'s and `ingest.py`'s dual-mode resolution predating this fix) rather than
assuming they were interchangeable enough to unify safely in one hotfix-tier pass.

`containment.py`'s fix is a different flavor from the rest: not a read-side data-correctness gap,
but a write-detection/safety-mechanism coverage gap (a codex-sandbox containment guard watching
paths that can never change). Found while reading `manifest.py`'s own consumers, not from either
sweep pass's grep pattern directly.

For each of the two most consequential fixes, confirmed the defect existed and was fixed via a
real invocation against the real repo state, not only a synthetic unit test:
- `load_data_glob(Path("agent-monitoring/data"), "runs")` — 0 matches for
  `TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX`'s own run_id before the fix, 1 after.
- `check_monitoring_write_recorded("TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX")` — `("FAIL",
  "No row with run_id == ... found under agent-monitoring/data/*/runs.jsonl")` before the fix,
  `("PASS", ...)` after.
- `make status-drift-check` — `FileNotFoundError` crash before the fix, clean run (surfacing only
  the real, pre-existing, unrelated `## Status` body-drift backlog) after.

## Test Summary

- `python3 -m pytest tests/tools/test_status_drift_check.py -v` — **20 passed** (19 existing,
  rewritten for the `data_dir`-based signature, plus 1 new test proving both bare and
  per-identifier shards are found).
- `python3 -m pytest tests/tools/test_validate_agent_monitoring.py -q` — **37 passed** (35
  existing + 2 new direct `load_data_glob`/`load_data_glob_with_line_count` tests).
- `python3 -m pytest tests/agent_replay_codex/test_containment.py -v` — **3 passed** (2 existing
  + 1 new test planting a real mutation to a real per-branch-shaped file and asserting detection
  fires — the exact gap that was silently broken before).
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py -q` — **49 passed** (48
  existing + 1 new `_week_shard_paths` test).
- `python3 -m pytest tests/tools/test_bash_command_mix.py tests/tools/test_verify_referential_integrity.py tests/agent_replay_codex/test_monitoring_shards.py tests/tools/test_generate_retro.py -q -k "..."` —
  every affected file's own new detection-proving test passes alongside its full existing suite.
- Direct execution confirmations (not test-suite, real repo state): `make status-drift-check`
  (crash → clean run), `check_monitoring_write_recorded()` (FAIL → PASS) — see Implementation
  Notes.
- Full regression: `python3 -m pytest tests/tools/ tests/agent_replay_codex/ tests/api/ -m "not
  slow and not extra_slow" -q` — **3238 passed**, 30 skipped, 28 deselected, 1 xfailed, 0 failed.
- Final sweep re-check (AC7): `grep -rn 'glob(f"\*/{'` across `.claude/workflows/`, `tools/`,
  `src/` shows every remaining hit paired with its widening (`+ sorted(...glob(f"*/*.{...}.jsonl"))`),
  except the two unrelated ticket-`.md`-file globs in `done_checker_static.py`/
  `epic_blocked_status_static.py` (confirmed unrelated by reading their context, not assumed from
  the grep alone). Zero remaining bare quoted flat-path literals anywhere in the same scope.

## Files Changed

- `.claude/workflows/implement-epic.js` — Step 2b verification command targets the real per-branch
  file via `monitoring_batch_identifier.resolve_write_target()`.
- `.claude/workflows/simq-audit.js` — tool-call-count computation uses `resolve_write_target('tools')`.
- `.claude/workflows/implement-ticket.js` — 3 stale-doc mentions corrected (lines 419, 597, 1948).
- `tools/gate_checks/status_drift_check.py` — `check_runs_jsonl_final_status_drift`/
  `check_status_drift`/CLI signature changed from a single `runs_path` to a `data_dir`, backed by
  `validate.load_data_glob()`; stale "ships unwired" docstring claim corrected too.
- `tools/agent-monitoring/validate.py` — `load_data_glob_with_line_count()` widened to glob both
  shapes.
- `tools/gate_checks/done_checker_static.py` — `_jsonl_rows_for_run_id_across_weeks()` widened.
- `src/api/agent_ops_dashboard/ingest.py` — `_week_shard_paths()` widened.
- `tools/agent_replay_codex/monitoring_shards.py` — `source_paths()` widened.
- `tools/agent-monitoring/manifest.py` — `_source_paths()` widened.
- `tools/agent-monitoring/bash_command_mix.py` — `week_shards()` widened.
- `tools/agent-monitoring/generate_retro.py` — `_source_mtime()` widened.
- `tools/agent_replay_codex/containment.py` — `_WATCHED_GIT_PATHSPECS`/`_watched_files()` now
  cover the real `agent-monitoring/data/` tree; stale docstring/error-message mentions corrected.
- Tests: `tests/tools/test_status_drift_check.py` (rewritten for new signature + 1 new test),
  `tests/tools/test_validate_agent_monitoring.py` (+2), `tests/agent_replay_codex/test_containment.py`
  (rewritten fixture + 1 new test), `tests/tools/test_agent_ops_dashboard_ingest.py` (+1),
  `tests/tools/test_bash_command_mix.py` (+1), `tests/tools/test_verify_referential_integrity.py`
  (+1), `tests/agent_replay_codex/test_monitoring_shards.py` (+1), `tests/tools/test_generate_retro.py`
  (+1).
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule).

## Completion Summary

Grew from 2 named, confirmed read-path bugs into a full ecosystem sweep: **12 real fixes across
11 files**. The two originally-named bugs (`implement-epic.js`'s monitoring-verification grep,
`simq-audit.js`'s tool-call-count computation) were confirmed and fixed exactly as reported. The
mandated sweep — "sweep for read paths the way you swept for writes" — found far more: a whole
class of read-side glob helpers narrowed to the bare per-week filename and never widened for the
per-identifier shape, spanning `validate.py` (backing most of the gate-check ecosystem),
`done_checker_static.py`'s own Finalize-time monitoring-write-verification gate, the actual
dashboard backend (`src/api/agent_ops_dashboard/ingest.py`), and four more independent glob
implementations — plus a separate but related containment/safety-mechanism coverage gap in
`tools/agent_replay_codex/containment.py`.

The two most consequential findings were confirmed by direct execution against this branch's own
real state, not assumed from reading code: `load_data_glob()` returned 0 matches for
`TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX`'s own real run record before the fix (1 after), and
`done_checker_static.py`'s own monitoring-write-verification gate FAILed for that same real ticket
closure before the fix (PASSed after) — meaning this repo's own Finalize-time monitoring check had
been silently wrong for every ticket closed since the per-identifier write scheme was introduced,
non-blocking only because CLAUDE.md's Hard Rule says a monitoring-write failure must never fail the
workflow.

Every fix is the same minimal, already-proven-safe one-line glob-widening pattern, each confirmed
by a dedicated test proving detection (not just that the code runs) and the file's own full
existing suite still passing. Full cross-cutting regression: 3238 passed, 0 failed. Deliberately
did not consolidate the ~8 read-side call sites into one shared helper — each has its own
fallback/legacy-shape nuances not worth risking in a hotfix-tier pass; a shared helper is a
reasonable future improvement, not this ticket's job.

No known material gap. Did not implement the separate, explicitly read-only investigation of the
7 uninstrumented `.claude/workflows/*.js` files — reported to agent-working-design/the user
separately, per their explicit instruction.
