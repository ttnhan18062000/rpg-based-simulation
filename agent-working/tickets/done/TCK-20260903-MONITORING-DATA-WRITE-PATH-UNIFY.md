---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, hooks, data-quality]
---

# TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY

## Title
Cut over `record_run.py`/`record_events.py`/`post_tool_hook.py` to the unified
`agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` per-week folder, and fix
`record_events.py`'s live, silently-broken `TOOLS_FILE` ground-truth read

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 1 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`, must land **first** in the batch. Two
things happen in this one ticket because they are the same class of fix at the same call sites:

**1. Write-path unification.** Today: `post_tool_hook.py` writes `tools` rows to
`agent-monitoring/tools/tools-YYYY-Www.jsonl` (prior epic's shape); `record_run.py` writes `runs`
rows to a monolithic `agent-monitoring/runs.jsonl` (`RUNS_FILE`, line 13); `record_events.py` writes
`events` rows to a monolithic `agent-monitoring/events.jsonl` (`EVENTS_FILE`, line 16). All 3 must
target the corrected shape: `agent-monitoring/data/<current-ISO-week>/{runs,events,tools}.jsonl`.

**2. URGENT bug fix (this is not a side note — treat it as the highest-priority item in this
ticket).** `record_events.py` also hardcodes `TOOLS_FILE = Path("agent-monitoring/tools.jsonl")`
(line 17) and reads it directly (`load_jsonl(TOOLS_FILE)`, lines 59-60, feeding
`_compute_tool_stats_by_key()`) to deterministically compute `tool_call_count`/`cost_proxy_score` for
every event it writes (see `docs/agent-monitoring/schema.md` lines 151, 382 for the documented
contract). That path was `git rm`'d by the prior epic's `TCK-20260902-MONITORING-SHARD-MIGRATION` on
2026-09-02 and has been permanently empty ever since (`TOOLS_FILE.exists()` is `False` — a silent
degrade, not a crash). **Every real `implement-ticket.js`-orchestrated run since 2026-09-02 has
gotten `tool_call_count=0`/wrong `cost_proxy_score` on its events.** Fixing this at the same time as
the write-path cutover is natural: both are "point the `tools` read/write at the right current
location" work, and this ticket's own write-path change is what makes the fix's own test corpus
exist to test against.

**Design note carried from investigation, not yet resolved — implementer must decide and document:**
before this epic, `record_events.py`'s `TOOLS_FILE` read was a *full-corpus* read of the entire
historical `tools.jsonl` (it was the only file that ever existed). The correct read for
`compute_tool_stats()` to match `(run_id, seq)` ground truth is therefore the **union of every week
folder's `tools.jsonl`**, not just the current week's — a paused/resumed run (see
`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`) can have tool-call rows in an earlier week than
the event being written now. Globbing all weeks is not a new performance cost; it restores the
original pre-sharding read scope, which already read the entire file every time.

## Scope
- `tools/agent-monitoring/post_tool_hook.py`: change the write target from
  `agent-monitoring/tools/tools-<week>.jsonl` (prior epic's shape) to
  `agent-monitoring/data/<week>/tools.jsonl` (this epic's unified shape). Reuse the existing
  `now_dt = datetime.now(timezone.utc)` / `iso_week = now_dt.strftime("%G-W%V")` computation
  unchanged (lines 56-60) — only the target path template changes.
- `tools/agent-monitoring/record_run.py`: replace `RUNS_FILE = Path("agent-monitoring/runs.jsonl")`
  (line 13) with a write-time ISO-week computation (reuse or duplicate the `%G-W%V` pattern —
  implementer's choice, matching the prior epic's Decision 3 precedent for `post_tool_hook.py`)
  targeting `agent-monitoring/data/<week>/runs.jsonl`. Document explicitly (see Assumptions) whether
  bucketing uses write-time ("now", consistent with `post_tool_hook.py`'s existing precedent) or the
  record's own `start_ts` field — recommended default is write-time, for consistency with the other
  2 sources' existing precedent, but this is the implementer's call to make and record.
- `tools/agent-monitoring/record_events.py`:
  - Replace `EVENTS_FILE = Path("agent-monitoring/events.jsonl")` (line 16) with the same write-time
    ISO-week computation targeting `agent-monitoring/data/<week>/events.jsonl`.
  - **Fix the critical bug**: replace `TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` (line 17)
    with a glob over `agent-monitoring/data/*/tools.jsonl` (all week folders, sorted), concatenated
    before being passed into `_compute_tool_stats_by_key()` — restoring full-corpus read scope, per
    the design note above.
- Continue routing every append through `tools/agent-monitoring/writer.py::write_line()`/
  `write_lines()` unmodified — confirm (don't assume) its `target_path.parent.mkdir(parents=True,
  exist_ok=True)` call correctly creates the new nested `agent-monitoring/data/<week>/` directory on
  first write for each of the 3 sources.
- Extend `.gitattributes` with a `merge=union` entry for the new unified glob (e.g.
  `agent-monitoring/data/*/*.jsonl merge=union`), **keeping** the 3 existing lines
  (`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`,
  `agent-monitoring/tools/*.jsonl merge=union`) in place during this ticket — child 2 (migration)
  removes them once the old paths are retired, matching the prior epic's precedent exactly.
- Update the write-path language in `docs/agent-monitoring/schema.md`'s per-source sections
  (minimal, targeted paragraph edits only — the broader consumer-facing doc sweep is child 7's scope,
  matching the prior epic's own child-1/child-3 split).
- Preserve every hook/script's existing fail-silent or fail-loud contract exactly as it is today —
  `post_tool_hook.py`'s outer `try/except Exception: pass` must continue to swallow any new-path
  computation failure exactly like every other failure mode already handled there.

## Out of Scope
- Migrating the existing monolithic `runs.jsonl`/`events.jsonl` content or the prior epic's already-
  sharded `tools/tools-YYYY-Www.jsonl` files into the new layout — that is
  `TCK-20260903-MONITORING-DATA-MIGRATION` (child 2).
- Any other consumer's read path (`build_index.py`, `generate_retro.py`, `manifest.py`,
  `seq_offset.py`, `weight_sensitivity_check.py`, `retro_nudge_hook.py`,
  `done_ticket_monitoring_coverage.py`, `validate.py`, `query.py`, `done_checker_static.py`,
  `agent_ops_dashboard/ingest.py`) — those are children 3 and 4. A known, accepted transient gap:
  after this ticket alone lands, new rows are invisible to those readers until children 3/4 land —
  acceptable because they land immediately after per `SEQUENCE.md`, not as a standalone release.
- Removing the historical monolithic files or the old `tools/` shard directory from the working tree
  — they stay present (frozen, receiving no more appends after this ticket's cutover) until child 2.
- The codex-runtime-activation subsystem (`tools/agent_replay_codex/monitoring_shards.py` and its
  call sites) — that is child 5.
- Referential-integrity verification tooling — that is child 6.
- The broader docs/CLAUDE.md/skill sweep beyond the minimal write-path paragraph in `schema.md` —
  that is child 7.
- Any change to `writer.py`'s locking protocol or the 3 per-line record schemas.

## Acceptance Criteria
- [x] A test (mocked/frozen "now") asserts `post_tool_hook.py` appends its record to
      `agent-monitoring/data/<expected-ISO-week>/tools.jsonl`, never to
      `agent-monitoring/tools/tools-*.jsonl` or `agent-monitoring/tools.jsonl`.
- [x] Equivalent tests for `record_run.py` (→ `data/<week>/runs.jsonl`) and `record_events.py`
      (→ `data/<week>/events.jsonl`).
- [x] A test asserts writes in two different mocked ISO weeks land in two distinct week folders for
      all 3 sources.
- [x] **Regression test proving the critical bug is fixed**: seed `tools` ground-truth rows across 2+
      week folders (including one week different from the event being written, simulating a
      paused/resumed session per `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`'s precedent),
      then assert `record_events.py` computes a correct nonzero `tool_call_count`/`cost_proxy_score`
      for a `(run_id, seq)` pair whose matching tool-call rows live in a non-current week folder — not
      just that the current-week case works.
- [x] Existing single-writer/concurrent-writer/fail-silent tests for all 3 scripts (from
      `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`/the prior epic) still pass against the new
      paths.
- [x] `.gitattributes` contains the new unified-glob `merge=union` entry; the 3 legacy lines remain
      present (removed by child 2, not this ticket).
- [x] `docs/agent-monitoring/schema.md`'s per-source sections describe the new per-ISO-week write
      path.
- [x] No functional change to `tools/agent-monitoring/writer.py`.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — depends on this ticket landing first)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE, -CONSUMERS-GATES-DASHBOARD (children 3, 4 — depend on
  child 2, which depends on this ticket)
- TCK-20260902-MONITORING-SHARD-WRITE-PATH — established the `%G-W%V` ISO-week write-path precedent
  and the fail-silent contract this ticket extends to `runs`/`events` and re-shapes for `tools`.
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION — confirms cross-week-boundary `(run_id, seq)`
  matching is a real, already-encountered scenario, directly motivating this ticket's full-corpus-glob
  fix for `record_events.py`'s `TOOLS_FILE` read.
- TCK-20260719-COST-PROXY-WRITE-PATH / TCK-20260719-LIVE-PHASE-AGENT-LABEL — established the
  `tool_call_count`/`cost_proxy_score` deterministic-computation contract this ticket's bug fix
  restores.

## Related Docs
- `docs/agent-monitoring/schema.md` — per-source write-path paragraphs.
- `docs/agent-monitoring/schema.md` lines 151, 382 — the documented `tool_call_count`/
  `cost_proxy_score` computation contract this ticket's bug fix must keep satisfying.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-WRITE-PATH/` (if present) and
  `stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` — `writer.py`'s design rationale,
  reused unmodified.

## Related Code Areas
- `tools/agent-monitoring/post_tool_hook.py` (line ~159, target path)
- `tools/agent-monitoring/record_run.py` (line 13, `RUNS_FILE`)
- `tools/agent-monitoring/record_events.py` (lines 16-17, `EVENTS_FILE`/`TOOLS_FILE`; lines 59-60,
  the read call)
- `tools/agent-monitoring/writer.py` (read-only reference; not modified)
- `.gitattributes`
- `docs/agent-monitoring/schema.md`
- `tests/tools/test_post_tool_hook.py`, `tests/tools/test_record_run.py`,
  `tests/tools/test_record_events.py`

## Assumptions / Open Questions
- `runs.jsonl` write-time bucketing vs. `start_ts`-field bucketing is left to the implementer's
  judgment (see Scope) — recommended default is write-time for consistency with the other 2 sources'
  existing precedent; must be documented either way.
- Assumes UTC is the correct timezone for all 3 sources' ISO-week computation, matching existing
  `datetime.now(timezone.utc)` usage throughout this subsystem.
- The critical bug fix's full-corpus glob for `record_events.py`'s `TOOLS_FILE` read is recommended
  over a current-week-only glob specifically because of the pause/resume cross-week scenario — an
  implementer choosing a narrower scope must justify it against that scenario, not silently pick the
  cheaper option.
- `layer: observability` matches this repo's established pattern for all `agent-monitoring/` tooling
  tickets.

## Implementation Notes

Implemented all 6 steps from `staging_artifacts/TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY/plan.md`
exactly as written; no deviations from the plan's literal before/after code.

**Step 1 — `post_tool_hook.py`.** Changed the write-target block (previously lines 159-161) from
`Path("agent-monitoring/tools") / f"tools-{iso_week}.jsonl"` to
`Path("agent-monitoring/data") / iso_week / "tools.jsonl"`, keeping the caller-side
`tools_file.parent.mkdir(parents=True, exist_ok=True)` call immediately before `write_line(...)`,
and keeping this entire block textually inside the existing outer `try: ... except Exception: pass`
(unchanged boundaries at the module's `try`/`except` lines). Verified this explicitly: the new
`Path(...)` construction, the `mkdir`, and the `write_line` call are still all inside the `try`
block — confirmed by re-reading the final file, not just by memory of the edit. Updated the module
docstring only; the `iso_week`/`now_dt` computation (lines 54-56) and all sidecar/scope/prune logic
were left untouched, per the plan's Do NOT touch list.

**Step 2 — `record_run.py`.** Added `timezone` to the `datetime` import, removed the module-level
`RUNS_FILE` constant, and moved the ISO-week computation + path construction inside `main()`
(write-time bucketing, per the plan's Ratified Decision 5). Updated the `if not ok:` diagnostic
message to point at `agent-monitoring/data/{iso_week}/.writer_health.jsonl` — confirmed this is
accurate by reading `writer.py`'s `_diagnostic_path_for` / `_write_diagnostic`, which derive the
sidecar path from `target_path.parent`, so the new nested location is correct. Updated the module
docstring and the `argparse` description. `validate_record()` and `compute_duration_s()` were left
untouched.

**Step 3 — `record_events.py` (`EVENTS_FILE`).** Added `from datetime import datetime, timezone`.
Removed the module-level `EVENTS_FILE` constant. Computed `iso_week` once per `main()` batch
(immediately before the write, after `tool_stats` is applied to all records), matching
`write_lines()`'s single-target-path, one-lock-per-batch contract. Added a one-line comment at the
computation noting the batch-straddles-a-week-boundary edge case, as the plan specified. Updated
the diagnostic-path message and the `argparse` description; the module docstring was also updated.

**Step 4 — `record_events.py` (`TOOLS_FILE` bug fix, highest-priority item).** Removed the
module-level `TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` constant (confirmed it had no
other reference in the file). Replaced the single-file existence check + read inside
`compute_tool_stats()` with `for tools_path in sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl")):`,
concatenating rows from every week folder before grouping by `(run_id, seq)`. Did not rename the
function (confirmed its real name is `compute_tool_stats`, matching the plan's explicit correction
of the ticket's own citation drift). Did not extend the glob to also read the prior epic's
`agent-monitoring/tools/tools-*.jsonl` shape. Updated the function's docstring to describe the
multi-week glob and the `(run_id, seq)` global-uniqueness safety argument.

**Step 5 — `.gitattributes`.** Added one new line, `agent-monitoring/data/*/*.jsonl merge=union`,
immediately after the `agent-monitoring/tools/*.jsonl merge=union` line and before
`tickets/working_log.csv merge=union`. All 4 existing lines (including the comment block) are
untouched. `grep -c 'merge=union' .gitattributes` reads 5, confirming the diff is purely additive.

**Step 6 — `docs/agent-monitoring/schema.md`.** Updated all 5 locations the plan specified: (1) added
a new write-path paragraph before "Historical Corrections" under `## agent-monitoring/runs.jsonl`
and updated that section's `open(RUNS_FILE, "a")` phrasing; (2) added a write-path paragraph to the
`## agent-monitoring/events.jsonl` section, which previously had none; (3) replaced the
`## agent-monitoring/tools.jsonl` section's opening paragraph to describe the second, distinct
migration (prior-epic shard shape → this-epic unified shape), keeping the still-true
`TCK-20260902-MONITORING-SHARD-MIGRATION` history; (4) updated the "How tool calls are attributed"
paragraph to state explicitly that `compute_tool_stats()` reads the union of every week folder's
`tools.jsonl`; (5) rewrote the "Join Example" snippet's 3 glob expressions to the new unified shape,
including the `runs` dict-comprehension's shape change to a nested-loop form. Verify-phase grep
check (`grep -n 'agent-monitoring/tools/tools-\|agent-monitoring/runs.jsonl'\'')\|agent-monitoring/events.jsonl'\'')' docs/agent-monitoring/schema.md`)
returns only historical-context sentences ("were written to...", "prior epic's ... shards remain
present...") — no current-state claim describes the old shape. One additional untouched hit at line
31 (`agent-monitoring/tools/tools-*.jsonl` mtime-staleness check in `build_index.py`'s description)
is intentionally out of scope — it describes `build_index.py`, an explicitly out-of-scope consumer
per the plan's Scope Guards, not this ticket's own write path.

**Fail-silent contract verification (per the Implementer checklist's explicit ask).** Re-read the
final `post_tool_hook.py` end-to-end after all edits: the new `Path("agent-monitoring/data") /
iso_week / "tools.jsonl"` construction, its `.mkdir(parents=True, exist_ok=True)` call, and the
`write_line(...)` call are all still inside the single outer `try: ... except Exception: pass` block
that spans the whole hook body. No new code was placed at module scope or in a helper called outside
that block. Confirmed with `test_iso_week_computation_failure_does_not_propagate` (updated to add
the new negative assertion `not (tmp_path / "agent-monitoring" / "data").exists()`) and
`test_locking_failure_does_not_propagate` (updated diagnostic-path assertion) — both pass, proving
the hook still degrades silently and never creates a `data/` directory when it fails.

**`writer.py` confirmed untouched:** `git diff --stat tools/agent-monitoring/writer.py` shows no
output.

**Test updates (per plan.md's Verify sections / test_plan.md).** Updated
`tests/tools/test_post_tool_hook.py`: replaced `test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl`
with `test_writes_to_unified_week_folder`; renamed/updated
`test_two_different_iso_weeks_write_to_two_distinct_shard_files` to
`test_two_different_iso_weeks_write_to_two_distinct_week_folders`; updated
`test_iso_week_shard_directory_created_on_first_write`,
`test_iso_week_computation_failure_does_not_propagate` (added the negative `data/`-not-created
assertion), `test_locking_failure_does_not_propagate`, and the `_tools_lines()` helper. Updated
`tests/tools/test_record_run.py`: added `_freeze_now()` helper (in-process `monkeypatch` on
`record_run.datetime`, no subprocess shim needed), added `test_writes_to_unified_week_folder` and
`test_two_different_iso_weeks_write_to_two_distinct_week_folders`, updated
`TestDurationWrittenToRecord._run_and_read` (3 dependent tests) and
`test_execution_identity_fields_pass_through_unchanged` to read back from the real-current-week
path. Updated `tests/tools/test_record_events.py`: added the same `_freeze_now()` helper pattern,
added `test_writes_to_unified_week_folder` and
`test_two_different_iso_weeks_write_to_two_distinct_week_folders`, added the two critical
cross-week tests `test_tool_call_count_correct_for_tool_rows_in_a_non_current_week_folder` (seeds
`(run_id="TCK-CROSS-WEEK-TEST", seq=4)` rows in `agent-monitoring/data/2026-W20/tools.jsonl` plus
unrelated rows in `2026-W21/tools.jsonl`, asserts `tool_call_count == 2` /
`cost_proxy_score > 0.0` via the real CLI — the exact design test_plan.md specified, not a weaker
same-week variant) and `test_tool_call_count_sums_rows_across_multiple_weeks_for_same_key`. Updated
`_write_tools_jsonl()` to the new `agent-monitoring/data/<week>/tools.jsonl` shape (parameterized by
a `week` argument, default `"2026-W01"`), and every dependent test
(`test_cost_proxy_score_and_tool_call_count_computed_from_real_tools_jsonl_not_passthrough`,
`test_cost_proxy_score_absent_when_no_tools_jsonl_exists`,
`test_compute_tool_stats_only_targets_implement_ticket_workflow`,
`test_execution_identity_fields_pass_through_unchanged`,
`test_vocabulary_warning_never_raises_or_exits`,
`test_batch_write_holds_contiguous_lines_under_concurrent_writer`). Re-ran
`test_implement_epic_and_create_tickets_records_unaffected_no_sidecar` unmodified as an anti-drift
guard — still asserts `stats == {}`.

**Anti-drift/out-of-scope confirmations.** `tests/integrity/test_merge_union_gitattributes.py` (not
modified — its assertions check for presence of specific existing lines/substrings, unaffected by
the purely-additive `.gitattributes` change) and
`tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py` (targets
`tools/agent_replay_codex/monitoring_shards.py`, child 5's scope, untouched) were both re-run to
confirm no incidental breakage — both pass unmodified.

**Live side-effect observed during implementation (expected, not a bug):** because
`post_tool_hook.py`'s cutover is live in this working tree, my own tool calls during this session
started writing real records to `agent-monitoring/data/2026-W36/tools.jsonl` partway through the
session (before the edit they were landing in the legacy
`agent-monitoring/tools/tools-2026-W36.jsonl`, which is why that file also shows as modified in
`git status`). This is genuine confirmation the cutover works end-to-end, not test pollution — left
untouched for the Test/Verify phase and the ticket owner to decide on.

**Post-commit follow-up: `tests/tools/test_execution_identity_end_to_end.py` coverage gap
(found by an independent Test-phase test-scoper agent run after this ticket's work was committed
as `06597f53` and `origin/main` merged in as `42b76ac8`).** This black-box integration test
(TCK-20260730-CLAUDE-EXECUTION-IDENTITY) drives all 3 writer scripts via subprocess and had
hardcoded the pre-cutover paths — the true monolithic `agent-monitoring/events.jsonl`/`runs.jsonl`,
and a `_current_week_tools_file()` helper that still resolved the *prior* epic's per-source shard
shape (`agent-monitoring/tools/tools-<week>.jsonl`), not even the shape this ticket replaced it
with. It was missed by both plan.md's file list and test_plan.md's Regression Surface, and
consequently not run during the original implementation pass. Fixed the same way as the other 3
test files: replaced `_current_week_tools_file()`'s single-purpose body with a shared
`_current_week_dir()` helper resolving the real unified `agent-monitoring/data/<ISO-week>/`
directory (mirroring all 3 writers' own `iso_week`/path construction), plus
`_current_week_events_file()`/`_current_week_runs_file()` siblings; updated all 3 test functions'
local `events_file`/`runs_file`/`tools_file` variables to use these; updated
`_seed_one_legacy_line_per_file()` to seed both the still-true legacy monolithic files (proving
they're never touched) and the real unified week-folder files (giving the prefix-unchanged /
append-only assertions genuine pre-existing content on the real target). Strengthened (not
weakened) `test_baseline_prefix_unchanged_after_new_identity_writes`: it previously only asserted
the legacy `tools.jsonl` stays untouched (the only source that had already moved off a monolithic
path before this ticket); now that all 3 sources have moved, added the symmetric assertions that
legacy `events.jsonl`/`runs.jsonl` also stay untouched. All 3 of the file's original assertions
(identity coherence across sources, prefix-preservation via byte-prefix + checksum, no-duplicate-
identity-keys) are intact and unweakened — only the path resolution changed. Re-ran the
coordinator's exact scoped command
(`pytest tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py
tests/tools/test_record_events.py tests/tools/test_monitoring_writer.py
tests/tools/test_monitoring_writer_single_source.py
tests/tools/test_monitoring_writer_lockfile_candidate.py
tests/tools/test_current_run_sidecar_orchestrator.py
tests/tools/test_execution_identity_end_to_end.py tests/integrity/test_merge_union_gitattributes.py`)
against `.venv/bin/python3`: 114 passed, 0 failed. Not committed — left in the working tree per
the coordinator's instruction.

## Test Summary

All target test files run against the real venv (`.venv/bin/python3`, since the bare `python3`
on this host lacks `pydantic` and fails `tests/conftest.py`'s import):

- `tests/tools/test_post_tool_hook.py`: 18 passed
- `tests/tools/test_record_run.py`: 22 passed
- `tests/tools/test_record_events.py`: 26 passed
- `tests/tools/test_execution_identity_end_to_end.py`: 3 passed (fixed post-commit, see
  Implementation Notes)
- `tests/tools/test_monitoring_writer.py`,
  `tests/tools/test_monitoring_writer_single_source.py`,
  `tests/tools/test_monitoring_writer_lockfile_candidate.py`,
  `tests/tools/test_current_run_sidecar_orchestrator.py` (anti-drift, unmodified): pass
- `tests/integrity/test_merge_union_gitattributes.py` (anti-drift, unmodified): 7 passed
- `tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py` (anti-drift, unmodified): 5 passed

Coordinator's exact scoped command (8 files, excluding the last anti-drift file above): 114 passed,
0 failed. Combined with the earlier `test_tools_shard_resolution.py` run: 119 passed, 0 failed
total across this ticket's full verified surface.

## Files Changed
- `tools/agent-monitoring/post_tool_hook.py` (Step 1: write-target path template)
- `tools/agent-monitoring/record_run.py` (Step 2: write-time ISO-week bucketing, `RUNS_FILE` removed)
- `tools/agent-monitoring/record_events.py` (Steps 3 + 4: `EVENTS_FILE` write-time bucketing;
  `TOOLS_FILE` critical bug fix → multi-week glob in `compute_tool_stats()`)
- `.gitattributes` (Step 5: new unified-glob `merge=union` line)
- `docs/agent-monitoring/schema.md` (Step 6: 5 write-path prose locations + Join Example)
- `tests/tools/test_post_tool_hook.py`
- `tests/tools/test_record_run.py`
- `tests/tools/test_record_events.py`
- `tests/tools/test_execution_identity_end_to_end.py` (post-commit coverage-gap fix, see
  Implementation Notes)
- `staging_artifacts/TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY/plan.md`,
  `investigation.md`, `test_plan.md` (present in the working tree at session start as untracked
  files from this run's own Investigate/Plan phases; part of this run's real changeset)
- `tickets/inprogress/TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY.md` (this file — AC checkboxes,
  Implementation Notes, Test Summary, Files Changed, Completion Summary)

Not modified (confirmed): `tools/agent-monitoring/writer.py` (zero-diff, per Acceptance Criteria).

## Completion Summary

Cut all 3 `agent-monitoring/` writers (`post_tool_hook.py`, `record_run.py`, `record_events.py`)
over to the unified `agent-monitoring/data/<ISO-week>/{tools,runs,events}.jsonl` layout, all
write-time-bucketed via `%G-W%V`, and fixed `record_events.py`'s silently-broken `TOOLS_FILE` read
(a dangling reference to a `git rm`'d file that made every `implement-ticket`-workflow event's
`tool_call_count`/`cost_proxy_score` compute as `0`/`0.0` since 2026-09-02) by replacing it with a
sorted glob over every ISO-week folder's `tools.jsonl`, concatenated before grouping by
`(run_id, seq)`. `.gitattributes` and `docs/agent-monitoring/schema.md` were updated in the same
session per the doc-parity requirement. All 3 legacy `.gitattributes` lines and all historical
monolithic/sharded data files remain present and untouched, per the ticket's explicit Out of Scope
(migration is child 2's job). 66 updated/new tests across the 3 target test files pass, plus 12
anti-drift tests in adjacent, out-of-scope test files confirmed unaffected. `writer.py` has a
confirmed zero-diff.

Independently re-verified through the full standard-tier pipeline: Test phase (test-scoper) found
one real coverage gap post-implementation (`tests/tools/test_execution_identity_end_to_end.py`
hardcoded pre-cutover paths, missed by plan.md/test_plan.md) — fixed and re-verified clean,
114/114 passing. Architecture-Verify (architecture-reviewer): **APPROVED** — `writer.py` confirmed
untouched, fail-silent contract confirmed preserved, `(run_id, seq)` global-uniqueness assumption
independently re-derived from `seq_offset.py`/`schema.md` rather than merely trusted, no scope
creep found. Verify (done-checker): **READY TO CLOSE**, 13/13 Definition-of-Done conditions PASS.
