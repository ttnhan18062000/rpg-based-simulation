---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING
artifact_type: test_plan
tags: [agent-monitoring, observability, process-improvement]
---

# Test Plan — TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING

## Regression Surface

**Unit — `tools/agent-monitoring/generate_retro.py`** (`tests/tools/test_generate_retro.py`, ~1830
lines, must stay green):
- `compute_tool_safety_metrics` suite (lines 1599-1801): all 13 `search_before_grep`/
  `parity_write_safety` tests, especially `test_tool_safety_function_never_crashes_on_malformed_rows`
  and `test_tool_safety_function_is_pure_no_file_io` — any extension of this function's return dict
  (per the investigation's recommendation to add the correlation data here) must not break these.
- `test_new_section_rendered_in_generate_output_when_investigate_tool_data_present` /
  `test_new_section_omitted_not_rendered_empty_when_no_investigate_tool_data` (lines 1803-1833) —
  pin the exact `## Tool Safety Audit` rendering; a new section inserted nearby must not disturb
  these literal string assertions or the `notes_idx`/`tool_safety_idx` ordering check.
- `test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope` (line 955) — will
  need a deliberate, justified update if `_update_index`'s signature changes (see New Tests Required).
- `test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` (line 1057)
  and the `_FIXED_CORPUS_EXPECTED_REPORT` frozen-literal test (lines 965-1054) — a byte-identical
  Markdown output guard; any new section must be additive and gated so this fixture (which has zero
  Investigate-phase tool data) does not start rendering the new sections.
- `TestComputeRetrievalMetrics` class and Retrieval Quality / Shadow-vs-Baseline section tests
  (lines 1117-1557) — unrelated data domain, must remain unaffected by any generate_retro.py edit.
- Full `test_generate_retro.py` file must pass with 0 regressions before/after.

**Unit — `tools/agent-monitoring/retrieval_baseline_metrics.py`**
(`tests/tools/test_retrieval_baseline_metrics.py`, 25 tests):
- `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader` (line 55) and
  `test_baseline_report_reuses_classify_provenance_not_reimplemented` (line 70) — AST-based reuse
  guards; if `SEARCH_TOOL_NAMES`/`build_search_count_section`/`build_raw_investigation_count_section`
  move to resolve the circular-import constraint (investigation.md Risks), these guards must still
  pass against the module's new import shape.
- `test_baseline_report_search_count_derivation_matches_stated_fields`,
  `test_baseline_report_raw_investigation_count_derivation_matches_stated_fields`,
  `test_baseline_report_raw_investigation_count_ratio_never_silent_if_present`,
  `test_baseline_report_raw_investigation_count_plausible_on_real_corpus` — must keep passing
  byte-for-byte if these functions are relocated, not just left alone.
- `test_baseline_report_tool_causes_zero_diff_on_real_corpus` (line 294) and
  `test_baseline_report_cli_runs_against_real_corpus_and_prints_json` (line 310) — real-corpus
  integration guards; confirm the CLI script still runs standalone after any refactor.
- Full `test_retrieval_baseline_metrics.py` file must pass with 0 regressions before/after.

**Unit/Integration — `tools/parity_index.py`** (`tests/tools/test_parity_index.py`, 34 tests,
including `TestArchitectureGuards`): this ticket does not modify `parity_index.py` itself (only
reads `tools.jsonl` to count Bash invocations of it) — must remain byte-identical / all passing,
confirming no accidental edit to the module under investigation.

**Integration — `tools/parity_ledger_writer.py`** (`tests/tools/test_parity_ledger_writer.py`, 13
tests, landed this session by `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL`) — confirms this
ticket's call-count section correctly continues to see 0 `entry`/`impact`/`health` sites even after
that sibling ticket's `build()` in-process call landed; no code change expected here, but the
regression run should include this file to detect any accidental cross-contamination.

## New Tests Required

Per AC1 (trended search/read-investigation section in the recurring report):
- `test_search_read_investigation_section_wired_into_generate_output` — unit/integration. Verifies
  `generate()`'s output contains the new section header and real numbers derived from a fixture
  `tools` list (not the corpus). Lives in `tests/tools/test_generate_retro.py`.
- `test_search_read_investigation_section_never_silent_has_derivation` — unit. Verifies the
  underlying computed dict carries a `"derivation"` string, mirroring
  `test_baseline_report_search_count_is_marked_or_derived_never_silent`'s convention. Lives in
  `tests/tools/test_generate_retro.py`.
- `test_search_read_investigation_section_reuses_retrieval_baseline_metrics_not_reimplemented` —
  architecture guard (AST- or import-based, mirroring
  `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`'s style). Asserts
  `generate_retro.py` does not contain a second independent implementation of the
  `SEARCH_TOOL_NAMES`-filtering/Read-counting logic — proves whichever circular-import resolution
  Plan picks (investigation.md Risks) is real code reuse, not silent duplication. Lives in
  `tests/tools/test_generate_retro.py`.
- `test_index_md_trends_search_and_read_investigation_columns` — integration, exercises
  `_update_index` end-to-end against a small multi-week fixture corpus (`tmp_path`-isolated,
  following `_isolate_monitoring_index`'s existing autouse-fixture pattern), asserting the rendered
  `index.md` table has per-week values that differ correctly across two synthetic weeks. Lives in
  `tests/tools/test_generate_retro.py`.
- `test_update_index_signature_change_is_deliberate_and_documented` (replaces, does not silently
  delete, `test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope` at line
  955) — asserts the new signature explicitly, and that `"load_jsonl(RUNS_FILE)"` (or equivalent
  direct-file-read) still does not appear in `_update_index`'s source, preserving that guard's
  original intent (only the migration-completeness framing changes, not the "don't bypass the
  index" property). Lives in `tests/tools/test_generate_retro.py`.

Per AC2 (compliant-vs-non-compliant Read-count correlation):
- `test_correlation_computes_read_count_per_investigate_pair` — unit. Fixture with 2+ Investigate
  pairs of known compliance and known Read-row counts; asserts the correlation dict's per-pair Read
  counts match hand-computed values. Lives in `tests/tools/test_generate_retro.py`, adjacent to the
  existing `compute_tool_safety_metrics` test block (line ~1801).
- `test_correlation_median_average_split_by_compliance` — unit. Asserts
  compliant-group/non-compliant-group median and average Read counts are computed correctly and
  independently (not conflated), using a fixture with an intentionally different distribution per
  group so a median-vs-average or group-swap bug would fail the test.
- `test_correlation_reuses_per_pair_compliance_not_a_second_pass` — architecture guard (AST-based,
  mirroring `test_tool_safety_function_is_pure_no_file_io`'s style). Asserts the correlation
  computation's source does not re-derive `investigate_pairs`/`pair_tool_rows` independently —
  proves reuse of `compute_tool_safety_metrics`'s already-computed structures per
  investigation.md's Anti-Drift Hazards.
- `test_correlation_section_omitted_when_no_investigate_pairs` — unit, mirrors
  `test_new_section_omitted_not_rendered_empty_when_no_investigate_tool_data`'s conditional-render
  convention.
- `test_correlation_handles_single_group_empty_gracefully` — edge case: all pairs compliant (or all
  non-compliant) in a period — the other group's median/average must be an explicit `None`/"n/a"
  marker, never a fabricated 0 or a `statistics.median([])` crash.
- `test_correlation_real_corpus_produces_a_real_number` — integration, against the real
  `agent-monitoring/tools.jsonl`/`events.jsonl` corpus (no `tmp_path` isolation for the source data,
  matching `test_baseline_report_raw_investigation_count_plausible_on_real_corpus`'s real-corpus
  pattern), asserting both group counts are `> 0` given the ticket's own cited "65 Investigate pairs
  / 27 non-compliant" real starting data point.

Per AC3 (`parity_index.py` call-count section):
- `test_parity_index_readpath_call_count_zero_on_current_corpus` — integration, against the real
  `agent-monitoring/tools.jsonl`, asserting the section reports `0` and a non-empty `derivation`
  string explaining why (nothing wired in yet) — matches AC3's literal "explicitly report 0/N call
  sites today with a derivation string" requirement.
- `test_parity_index_readpath_detection_matches_real_call_when_present` — unit, fixture-based:
  constructs a synthetic `tools` row shaped like a real `python3 tools/parity_index.py entry
  <id>`/`impact --changed-path ...`/`health --subsystem ...` Bash call and asserts the section's
  count becomes nonzero and the row appears in an examples list — proves the "activates
  automatically" requirement without needing a real call site to exist yet.
- `test_parity_index_readpath_detection_false_positive_guards` — unit, regression guard using the
  exact false-positive-prone patterns confirmed present in the real corpus during investigation
  (`python3 tools/parity_index.py --help`, `git log -- ... tools/parity_index.py`, `pytest
  tests/tools/test_parity_index.py -k impact`, `sed -n '1,60p' tools/parity_index.py`) — asserts
  none of these increment the count.
- `test_parity_index_readpath_section_never_silent_has_derivation` — unit, mirrors the
  never-silent convention test for every other section in this file family.
- `test_parity_index_readpath_section_denominator_documented` (only if Plan adopts an explicit `N`
  denominator per investigation.md's open question) — unit, asserts the denominator's own
  computation is documented in the derivation string, not a magic number.

Cross-cutting (AC4/AC5):
- `test_all_new_sections_have_derivation_key` — unit, table-driven over the three new
  section-producing functions, asserting each returns a dict containing a `"derivation"` (or
  equivalently-named, per the ticket's "or equivalent" allowance) string key.
- `test_new_sections_never_write_any_file` — architecture guard (AST-based, mirroring
  `test_baseline_report_tool_never_imports_writer_module`/`test_tool_safety_function_is_pure_no_file_io`),
  applied to whichever new function(s) implement AC1-AC3.

## Scoped Pytest Commands

```bash
# Primary regression + new-test surface for this ticket
.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py tests/tools/test_retrieval_baseline_metrics.py -v

# Confirm no accidental edit to the untouched-by-this-ticket parity_index.py / writer path
.venv/bin/python3 -m pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_writer.py -v

# Full real-corpus sanity: regenerate the recurring report against --all and confirm it runs clean
.venv/bin/python3 tools/agent-monitoring/generate_retro.py --all
```

Never `pytest tests/` — scoped to `tools/agent-monitoring/`'s test surface and its two directly
adjacent parity-index test files per CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader` (existing, must still pass) —
  the primary guard against `retrieval_baseline_metrics.py` growing a second `tools.jsonl` reader;
  any relocation of `build_search_count_section`/`build_raw_investigation_count_section` to resolve
  the circular-import constraint must keep this guard meaningful, not delete it to dodge the check.
- `test_correlation_reuses_per_pair_compliance_not_a_second_pass` (new, above) — the direct
  anti-scope-creep guard for AC2: catches a future edit that reimplements Investigate-pair
  attribution logic instead of reusing `compute_tool_safety_metrics`'s existing structures.
- `test_search_read_investigation_section_reuses_retrieval_baseline_metrics_not_reimplemented`
  (new, above) — catches silent vocabulary drift between the one-off snapshot's `SEARCH_TOOL_NAMES`
  and any new recurring-report search-counting logic; a failure here means the two files' notions of
  "a search call" have silently diverged, which would make the AC1 trend numbers not comparable to
  the one-off baseline they're supposed to extend.
- `test_parity_index_readpath_detection_false_positive_guards` (new, above) — the direct guard
  against the call-count section inflating itself on `--help`/`git log`/`pytest -k`/`sed` commands
  that merely mention `parity_index.py` by name without invoking `entry`/`impact`/`health` —
  prevents this section from becoming as noisy as a naive substring match would make it.
- `test_new_section_rendered_in_generate_output_when_investigate_tool_data_present` /
  `test_new_section_omitted_not_rendered_empty_when_no_investigate_tool_data` (existing, must still
  pass unmodified) — guards that the pre-existing `## Tool Safety Audit` section's exact rendered
  text and gating condition are untouched by this ticket's additions nearby.
- `test_update_index_signature_change_is_deliberate_and_documented` (new, replaces the old
  signature-pin test) — ensures the `_update_index` arity change is a conscious, tested decision
  with the "never read jsonl directly, always go through the passed-in filtered data" property
  preserved, not a regression back to a pre-SQLite-index-migration shape.
- `test_baseline_report_tool_causes_zero_diff_on_real_corpus` (existing, must still pass) — the
  dirty-tree-aware real-corpus zero-mutation guard; any new code path that reads
  `agent-monitoring/*.jsonl` for the correlation/call-count sections must never write into that
  directory, which this existing test would catch if violated by an accidental shared-state bug.
