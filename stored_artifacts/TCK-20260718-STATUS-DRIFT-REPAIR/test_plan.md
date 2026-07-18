---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATUS-DRIFT-REPAIR
artifact_type: test_plan
tags: [data-quality, agent-monitoring, observability]
---

# Test Plan — TCK-20260718-STATUS-DRIFT-REPAIR

This extends the Scope-phase test_plan.md (all of its content confirmed correct and retained in spirit
below); this pass adds a concrete Part C script design/location, exact regression-surface file paths
confirmed to exist, and one additional guard for the same-line-`## Status`-format hazard found during
investigation.

## Regression Surface

Existing tests that must keep passing (confirmed present on disk):

**Unit — agent-monitoring tooling**
- `tests/tools/test_validate_agent_monitoring.py` — covers `validate.py`'s `compute_drift_report` and
  `compute_tool_count_drift_report`; must still pass after the `runs.jsonl` edit (line-preserving
  rewrite means shapes/counts elsewhere are unaffected, but this confirms it).
- `tests/tools/test_record_run.py` — confirms `record_run.py`'s append-only append behavior is
  untouched (this ticket does not modify `record_run.py`).
- `tests/tools/test_doc_staleness_check.py` — regression coverage for the closest existing
  `gate_checks/*.py` sibling; confirms the new script's addition doesn't collide with or break its
  import/collection.
- `tests/tools/test_workflow_meta_conformance.py` — same rationale, second closest sibling.
- `tests/tools/test_generate_retro.py` — `generate_retro.py` also reads `runs.jsonl`'s `final_status`
  field (per `docs/agent-monitoring/schema.md`'s note on its fallback matching); confirms the 7-record
  casing fix doesn't change retro aggregation output in a way its existing fixtures don't already cover.
- `tests/tools/test_validate_frontmatter.py` — confirms the two `staging_artifacts/.../*.md` files this
  ticket writes/overwrites still pass frontmatter validation (`ARTIFACT_TYPE_VALUES = {"investigation",
  "plan", "test_plan"}`, confirmed by direct read of `tools/validate_frontmatter.py` lines 44-52).

**Integration**
- `python3 tools/agent-monitoring/validate.py` — not a pytest test but an explicit AC; must exit 0
  after the `runs.jsonl` edit. Run directly, not via pytest.

**Arena-combat** — none. This ticket touches no combat/simulation code path; no arena-combat regression
surface applies.

## New Tests Required

Per acceptance criteria, new pytest coverage under `tests/tools/test_status_drift_check.py` (new file,
mirrors `tests/tools/test_workflow_meta_conformance.py`'s `tmp_path`-fixture style — confirmed that
style by reading its test bodies, e.g. `test_flags_declared_phase_with_zero_events(tmp_path, ...)`):

| Test name | Category | What it verifies | Where |
|---|---|---|---|
| `test_clean_corpus_passes` | unit | Fixture dir with all `## Status` == `DONE` (two-line format) and a fixture `runs.jsonl` with all `final_status` == `"DONE"` → checker returns all-PASS / exits 0 | `tests/tools/test_status_drift_check.py` |
| `test_stale_ticket_status_flagged` | unit | Fixture ticket file, two-line `## Status\nOPEN`, non-exempt filename/value → checker returns a FAIL entry naming that file | same |
| `test_lowercase_final_status_flagged` | unit | Fixture `runs.jsonl` line with `"final_status":"done"` → checker returns a FAIL entry naming that `run_id` | same |
| `test_epic_tier_exception_ignored_by_value` | unit | Fixture ticket with `## Status` == `EPIC_SCOPED` (and, separately, one with `== "SCOPED"`) → checker does not flag it, confirming the exemption is value-based (`{"EPIC_SCOPED","SCOPED"}`) not a hardcoded filename list | same |
| `test_legacy_naming_file_ignored_by_pattern` | unit | Fixture file named without a `TCK-` prefix (e.g. `resource_v2_fixture_e9_9.md`) with a non-`DONE` `## Status` → checker does not flag it, confirming the exemption is filename-pattern-based, not a hardcoded list | same |
| `test_legacy_runs_jsonl_shape_ignored` | unit | Fixture `runs.jsonl` line using the legacy `status`/`started_at`/`completed_at` field set (no `final_status` key) → checker does not attempt to validate it, confirming Part B scope is limited to current-schema (`final_status`-bearing) records only | same |
| `test_same_line_colon_status_format_not_newly_flagged` | unit / anti-drift guard | Fixture ticket using the same-line `## Status: INPROGRESS` format (no newline before the value) found during investigation (see investigation.md Risks) → checker does NOT flag it, confirming the extraction regex is `^## Status\s*\n+\s*(\S+)`-equivalent (matching the baseline scan), not a broader pattern that would newly expand scope beyond the approved 71/12/83 baseline | same |
| `test_check_is_read_only` | unit / architecture guard | Checker never writes to any file it scans (mirrors `test_drift_report_is_read_only` / `test_tool_count_drift_report_is_read_only` pattern in `test_validate_agent_monitoring.py`) — snapshot fixture dir/file mtimes and contents before/after, assert unchanged | same |
| `test_marker_json_output_contract` | unit / architecture guard | CLI invocation prints a `MARKER:`-prefixed line whose payload is valid JSON (list of dicts with `status`/`evidence` keys), matching `doc_staleness_check.py`/`workflow_meta_conformance.py`'s established output contract | same |
| `test_exit_code_nonzero_on_any_fail_zero_on_clean` | integration | Full CLI subprocess or `main()`-equivalent invocation: exit code 1 when any FAIL entry present, exit code 0 when all-PASS | same |

Data-fix verification (one-time, not pytest — run manually at implementation time, not part of the
regression suite going forward):

1. Re-run the Part A baseline scan post-fix; assert output is exactly the 12 documented exceptions,
   zero other results.
2. `git diff --stat tickets/done/` post-fix: assert every touched file shows a 1-line change, and the
   touched-file count equals the re-derived in-scope count from investigation.md (71, unless a ticket
   closed between scoping and implementation — re-derive, don't assume).
3. Parse `agent-monitoring/runs.jsonl` post-fix; assert all 7 target `run_id`s have `final_status ==
   "DONE"` exactly; assert line count unchanged (641 before → 641 after).
4. Diff `runs.jsonl` pre/post fix line-by-line, excluding the 7 target lines; assert byte-identical
   (e.g. `diff <(git show HEAD:agent-monitoring/runs.jsonl) agent-monitoring/runs.jsonl` filtered to
   exclude the 7 known line numbers, or a Python line-by-line comparison skipping those indices).
5. Run `python3 tools/agent-monitoring/validate.py`; assert exit code 0.
6. Frontend trace (manual or existing test extension, do not modify `GanttBar.tsx`): confirm
   `classifyFinalStatus('DONE')` (the corrected value for all 7 records) returns `'done'` — already
   covered implicitly by `dashboard-frontend/src/test/GanttBar.test.tsx`'s existing fixtures (lines 18,
   95 both use `final_status: 'DONE'`), so no new frontend test is strictly required by the AC's
   "verified via existing/new frontend test, or manual trace" language; a manual trace suffices.

## Scoped Pytest Commands

```
pytest tests/tools/test_status_drift_check.py -v
pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_run.py \
       tests/tools/test_doc_staleness_check.py tests/tools/test_workflow_meta_conformance.py \
       tests/tools/test_generate_retro.py tests/tools/test_validate_frontmatter.py -v
```

Never `pytest tests/` — scoped to `tests/tools/` per the project testing rule and this ticket's
tooling-only surface. No `src/` or simulation-engine test directories are in scope; this ticket touches
no simulation code.

## Anti-Drift Test Guards

- `test_same_line_colon_status_format_not_newly_flagged` (above) is the single most important
  anti-drift guard this ticket adds: without it, a future edit to the checker's regex (made in good
  faith, to "catch more cases") would silently expand Part A's flagged set beyond the 83/71/12 baseline
  this ticket's ACs were written against, and nothing else in the suite would catch that expansion.
- `test_check_is_read_only` guards against the checker accidentally becoming a second, undocumented
  write path into `tickets/done/*.md` or `runs.jsonl` — this ticket's entire write-safety design (Part
  A single-line replace, Part B line-scoped string substitution) depends on there being exactly one
  authoritative write path per corpus, not two.
- `test_legacy_runs_jsonl_shape_ignored` guards the Out-of-Scope boundary explicitly: the ~98
  legacy-shaped `status`/`started_at` records must never be pulled into Part B's current-schema-only
  scan, even by future maintenance that "helpfully" generalizes the field lookup.
- `test_epic_tier_exception_ignored_by_value` and `test_legacy_naming_file_ignored_by_pattern` together
  guard against the exemption mechanism regressing into a brittle hardcoded filename list (see
  investigation.md Anti-Drift Hazards) — if a future epic ticket closes with `## Status: EPIC_SCOPED`
  and is NOT in some maintained literal list, these tests (via their value-based/pattern-based, not
  name-based, fixtures) confirm the checker still correctly exempts it without a code change.
- `validate.py`'s own existing `LEGACY_TERMINAL_STATUS_VALUES` allowlist is intentionally NOT modified
  or tested against by any new test in this ticket — its existing test coverage in
  `test_validate_agent_monitoring.py` is the correct and sufficient guard for that orthogonal concern.
