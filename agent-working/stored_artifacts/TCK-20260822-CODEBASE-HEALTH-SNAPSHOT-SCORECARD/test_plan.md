---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD
artifact_type: test_plan
tags: [agent-monitoring]
---

# Test Plan — TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD

## Regression Surface

Existing tests that must keep passing — none of this ticket's scope touches their subject
modules, but they exercise the exact functions/conventions this ticket's new code imports and
reuses, so a regression in any of them would silently invalidate this ticket's own assumptions.

**Unit (tools/):**
- `tests/tools/test_codebase_health_baseline.py` — `build_report()` and its constituent functions
  must keep their current dict shape; this ticket's frozen schema allowlist (Investigation item 7)
  is built directly against them.
- `tests/tools/test_code_health_impact.py` — the CLI/module-structure/Makefile-target-shell-out
  pattern this ticket's new module mirrors; also exercises `compute_churn_lines_changed`, which
  this ticket does not call but which lives in the same source module (`codebase_health_baseline
  .py`) this ticket imports from.
- `tests/tools/test_monitoring_writer.py` — the real production coverage for
  `tools/agent-monitoring/writer.py::write_line`/`write_lines`, which this ticket's new
  snapshot-writer is expected to reuse (Investigation item 3 / Risks). Must stay green since this
  ticket adds a 4th consumer on top of the existing 3.
- `tests/tools/test_monitoring_writer_lockfile_candidate.py` — the original lock-file evidence
  test `test_monitoring_writer.py` promotes to production coverage; kept alongside it per that
  file's own docstring.

**Integration / cross-cutting:**
- `tests/docs/test_doc_integrity.py` (or whichever doc-path-existence check is currently wired,
  per this repo's D24 §G/§J doc-path CI check) — will start checking any new doc path this ticket
  adds (see investigation.md's "Docs Requiring Update"); must not break on the new doc's own
  internal path references.
- `tools/gate_checks/done_checker_static.py`'s `check_docs_to_update_coverage` — parses this
  ticket's own `investigation.md` "Docs Requiring Update" bullet format; not a pytest suite to
  run directly, but the format used in investigation.md must satisfy it (already verified: exact
  backtick-path-then-colon bullet form used throughout).

**Arena-combat:** none — this ticket has no combat-adjacent surface.

## New Tests Required

Location for all new tests: `tests/tools/test_codebase_health_snapshot.py` (per the ticket's own
`expected:` path), following `test_codebase_health_baseline.py`/`test_code_health_impact.py`'s
established `sys.path.insert` + `import <module> as <alias>` + `tmp_path`-rooted real-git-repo
fixture conventions (no mocking `build_report()` — call it for real against a small synthetic
`tmp_path` repo, matching the "every check the tool claims to compute has at least one fixture
proving it computes correctly" convention both sibling test files state explicitly).

### Persistence / append-only behavior (AC #1)

- **`test_two_invocations_append_two_separate_records_without_truncation`**
  Category: unit / integration (exercises the real writer against a real `tmp_path` file).
  Verifies: call the snapshot-write entry point twice against a fresh `tmp_path` history file;
  re-open and read the file after each call; assert exactly 1 line exists after call 1, exactly 2
  lines exist after call 2, and the first line's content is byte-identical before and after the
  second call (proves no truncation/rewrite, not just "2 lines exist").
  Location: `tests/tools/test_codebase_health_snapshot.py`

- **`test_appended_record_is_valid_json_matching_frozen_schema_allowlist`**
  Category: unit.
  Verifies: one appended record parses as JSON and its key set equals the frozen
  `EXPECTED_SNAPSHOT_KEYS` allowlist from Investigation item 7 exactly (not a subset check) —
  this is the schema-freeze mechanism's own positive-path test.
  Location: `tests/tools/test_codebase_health_snapshot.py`

- **`test_write_failure_does_not_crash_caller`**
  Category: unit (mirrors `test_monitoring_writer.py`'s own non-raising contract tests, applied
  at this ticket's call site rather than re-testing `write_line` itself).
  Verifies: if the underlying writer reports failure (inject via monkeypatching the imported
  `write_line` to return `False`), the snapshot-write entry point degrades to a clear
  warning/non-zero-but-non-crashing outcome rather than raising — matches this repo's established
  "monitoring write failure must never fail the workflow" convention (CLAUDE.md Hard Rules),
  applied here even though this isn't a workflow-monitoring write per se, since it reuses the same
  writer with the same non-raising contract.
  Location: `tests/tools/test_codebase_health_snapshot.py`

### Schema freeze / versioning (Scope item 3, AC #4)

- **`test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented`**
  Category: unit / architecture guard (asserts *behavior* — same values as a live `build_report()`
  call — not source-text scanning, which would be a weaker, more easily-gamed check).
  Verifies: call the new module's snapshot-payload builder against a `tmp_path` repo, call
  `codebase_health_baseline.build_report()` directly against the same `tmp_path` repo, assert the
  two dicts are equal (modulo the schema-version field this ticket adds on top, if any) — proves
  AC #4's "no re-derivation" empirically, not just by code inspection.
  Location: `tests/tools/test_codebase_health_snapshot.py`

- **`test_schema_mismatch_raises_loudly_not_silently`**
  Category: unit — the core test for the schema-freeze mechanism itself (Investigation item 7,
  option (a)).
  Verifies: monkeypatch/stub `build_report` to return a dict with an added key, a removed key, and
  a renamed key (three separate sub-cases or three separate tests) and assert the snapshot-write
  path raises/errors visibly in each case, rather than silently writing a differently-shaped
  record or silently dropping/padding fields.
  Location: `tests/tools/test_codebase_health_snapshot.py`

- **`test_schema_version_field_present_and_stable_across_writes`**
  Category: unit.
  Verifies: every appended record carries the `snapshot_schema_version` field (Investigation item
  7, option (b)) with the same current value across repeated writes in the same test run.
  Location: `tests/tools/test_codebase_health_snapshot.py`

### Trend-arrow rendering (AC #2)

- **`test_scorecard_renders_per_dimension_trend_arrow_for_two_snapshots`**
  Category: unit.
  Verifies: given two hand-constructed synthetic snapshot dicts (not real `build_report()` output
  — deliberately synthetic so the up/down/flat cases are exactly controlled) with one field
  increased, one decreased, and one unchanged between them, the scorecard render shows the
  correct directional indicator (mirroring personality_audit.py's `↑`/`↓`/`→` convention, per
  Investigation item 2) for each of the three cases.
  Location: `tests/tools/test_codebase_health_snapshot.py`

- **`test_scorecard_output_has_no_aggregate_or_combined_score_field`**
  Category: unit — the direct, explicit test for AC #2's negative requirement and this ticket's
  Out of Scope bullet ("no aggregate/combined score field... at any layer of the output").
  Verifies: given two synthetic snapshots, assert the rendered/returned scorecard structure
  contains no key/line matching an aggregate-score shape (e.g. no `"score"`, `"overall"`,
  `"combined"`, `"health_score"` key in the structured return value, and no analogous line in the
  printed/formatted text output) while asserting the per-dimension directional indicators *are*
  present — a test that only checked one half would miss half of AC #2.
  Location: `tests/tools/test_codebase_health_snapshot.py`

- **`test_non_scalar_dimension_unused_core_dependencies_does_not_get_forced_arrow`**
  Category: unit — regression guard for Investigation item 6's explicit non-scalar-field carve-out.
  Verifies: `unused_core_dependencies` (a `list[str]`) renders as a raw value/count, never through
  the same Δ/arrow branch used for the 11 scalar dimensions, across at least one case where the
  list changes between snapshots and one where it doesn't.
  Location: `tests/tools/test_codebase_health_snapshot.py`

### Single-snapshot degradation (AC #3)

- **`test_scorecard_with_one_snapshot_labels_no_trend_data_without_crashing`**
  Category: unit — the direct test for AC #3.
  Verifies: given exactly one synthetic snapshot record, the scorecard render completes without
  raising, and every dimension is labeled as having no trend data yet (an explicit, assertable
  string/flag — not merely "no arrow shown," which could pass accidentally even with a bug that
  silently omits dimensions rather than correctly labeling them).
  Location: `tests/tools/test_codebase_health_snapshot.py`

- **`test_scorecard_with_zero_snapshots_does_not_crash`**
  Category: unit — edge case one step before AC #3's stated minimum, worth covering explicitly
  since a fresh install/first run will hit exactly this state.
  Verifies: given an empty/nonexistent history file, the scorecard command exits cleanly with a
  clear "no snapshots yet" message rather than a traceback (`FileNotFoundError`, empty-list index
  error, etc.).
  Location: `tests/tools/test_codebase_health_snapshot.py`

### Makefile wiring (Scope item 6)

- **`test_make_target_runs_successfully_end_to_end`**
  Category: integration — mirrors both sibling test files' own
  `test_make_target_runs_successfully_with_plausible_values` pattern.
  Verifies: shells out to the real `make <new-snapshot-target>` (and, if a separate scorecard
  target is added, that one too) against the real repo from a scratch/isolated history-file
  location (never the real `agent-monitoring/` directory — see Anti-Drift Test Guards below),
  asserts `returncode == 0` and expected key strings appear in stdout.
  Location: `tests/tools/test_codebase_health_snapshot.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_codebase_health_snapshot.py -v
pytest tests/tools/ -k "codebase_health or code_health or monitoring_writer" -v
```

The second command is the regression-surface scope: it re-runs this ticket's own new tests plus
every existing test file identified above under "Regression Surface" in one pass, without
invoking the full `tests/tools/` directory (which includes many unrelated tool suites) or the
forbidden bare `pytest tests/`.

If the new module also needs verification against the doc-path-existence check (only if the new
doc file from investigation.md's "Docs Requiring Update" is added):

```
pytest tests/docs/test_doc_integrity.py -v
```

## Anti-Drift Test Guards

- **Never target the real `agent-monitoring/` directory from a test.** Every new test must write
  its synthetic history file under `tmp_path`, exactly mirroring
  `test_monitoring_writer.py`'s own explicit guard test
  (`test_no_test_target_path_resolves_under_real_agent_monitoring_dir`) — a new test in this
  ticket's own file should add the equivalent guard (scan this file's own test bodies for a
  real-corpus-shaped path) if the new module's default history-file path lives inside
  `agent-monitoring/`, since that default must never leak into a test run and start appending
  real records to the production `agent-monitoring/*.jsonl` family (this ticket's own new file
  specifically, or worse, an accidental typo'd write into `runs.jsonl` itself).
- **Guard against AC #4 regressing silently**: `test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented`
  above is the standing regression guard against a future edit that starts recomputing metrics
  independently inside the new module instead of calling `build_report()` — if that test ever
  needs a mock/stub to keep passing after a source change, that is itself the signal that AC #4
  has been silently violated.
- **Guard against the "no aggregate score" constraint eroding via a future field addition**:
  `test_scorecard_output_has_no_aggregate_or_combined_score_field` should assert on the *shape* of
  the structured return value (e.g. iterate `scorecard_dict.keys()` and assert none match a
  small denylist of aggregate-sounding names), not just grep the printed text — a future change
  that adds a `"summary_score"` key to the structured output but never prints it in the default
  CLI render would otherwise pass a text-only test while still violating the Out of Scope
  constraint for any downstream consumer reading the structured form directly (e.g. the future
  TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR ticket sequenced after this one).
- **Guard against silent schema drift specifically**: `test_schema_mismatch_raises_loudly_not_silently`
  is the standing regression guard for the entire reason this ticket exists (per its own Scope
  item 3) — if `codebase_health_baseline.py::build_report()` is ever changed in a future ticket
  and this test starts silently passing with a differently-shaped record written, that is the
  exact "silent drift" failure mode the schema-freeze mechanism was built to prevent, and should
  block that future ticket's own Verify phase, not just this one's.
