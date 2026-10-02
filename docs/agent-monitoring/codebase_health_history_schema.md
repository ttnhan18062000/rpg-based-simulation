---
status: active
layer: observability
authority: P2
audience: developer
tags: [agent-monitoring, schema]
---

# Codebase Health History — Schema Reference

One append-only JSONL file, written by `tools/codebase_health_snapshot.py`
(`TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD`, item 3 of
`TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`). It persists
`tools/codebase_health_baseline.py::build_report()`'s live metrics across
runs so a scorecard can render per-dimension trends — no single record here
is meaningful on its own; the value is in the sequence. Since schema version 2
(`TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS`) each record also carries Python craft
metrics from a second source, `tools/code_health/metrics.py` — see "Second metric source".

**File path:** `agent-monitoring/codebase_health_history.jsonl`

This lives inside the same directory family as `runs.jsonl`/`events.jsonl`/
`tools.jsonl` purely for writer/lock/diagnostic-infrastructure reuse — it is
its own distinct file, joined to nothing else in that family, and shares no
path constant with `RUNS_FILE`.

```json
{
  "source_loc": 142318,
  "source_files": 601,
  "test_loc": 168204,
  "test_files": 812,
  "test_source_ratio": 1.18,
  "top_level_src_packages": 24,
  "test_subdirectories": 143,
  "commit_count": 3412,
  "doc_count": 918,
  "registry_size_bytes": 812004,
  "registry_size_lines": 15230,
  "dead_bytecode_files": 0,
  "unused_core_dependencies": [],
  "churn_lines_changed_excl_bookkeeping": 812340,
  "craft_ruff_findings": 6472,
  "craft_correctness_findings": 1050,
  "craft_missing_public_docstrings": 1908,
  "craft_missing_annotations": 378,
  "craft_functions_over_cognitive_limit": 384,
  "craft_functions_over_length_limit": 251,
  "craft_classes_over_length_limit": 21,
  "craft_modules_over_length_limit": 11,
  "craft_longest_function_lines": 2409,
  "craft_highest_cognitive_complexity": 789,
  "craft_baseline_rows": 3617,
  "craft_baseline_unreviewed_rows": 3617,
  "craft_baseline_duplicate_file_pairs": 58,
  "craft_baseline_duplicated_lines": 1392,
  "snapshot_schema_version": 2
}
```

---

## Append-only contract

`agent-monitoring/codebase_health_history.jsonl` is append-only for all
writes — mirroring `docs/agent-monitoring/schema.md`'s own wording for
`runs.jsonl`. The writer
(`tools/codebase_health_snapshot.py::write_snapshot`, via
`tools/agent-monitoring/writer.py::write_line`) only ever appends, never
rewrites an existing line. There is no historical-correction exception
documented for this file yet (unlike `runs.jsonl`'s one documented case,
`TCK-20260718-STATUS-DRIFT-REPAIR`) — this file is new, and no correction has
been needed. If one ever is, it should follow that same precedent: an atomic,
audited, line-scoped substitution, never a bulk parse/re-serialize.

---

## Field table

Every field in the first table below is one key from
`tools/codebase_health_baseline.py::build_report()`'s own return dict, used exactly as
returned — this module never recomputes or re-derives any individual metric.
`codebase_health_snapshot.py::EXPECTED_BASELINE_KEYS` is the enforced, frozen source of truth
for that set, and `EXPECTED_SNAPSHOT_KEYS` is that set plus the craft keys below:
`build_snapshot_record` validates `set(report.keys()) == EXPECTED_BASELINE_KEYS` and the
craft source's keys against `CRAFT_METRIC_KEYS` exactly (not a subset/superset check) on
every write and raises `RuntimeError` loudly on any mismatch, so a future field
rename/add/remove is a visible breaking change here, never silent drift.

| Field | Type | Meaning |
|---|---|---|
| `source_loc` | int | Total lines across git-tracked `src/**/*.py` files. |
| `source_files` | int | Count of git-tracked `src/**/*.py` files. |
| `test_loc` | int | Total lines across git-tracked `tests/**/*.py` files. |
| `test_files` | int | Count of git-tracked `tests/**/*.py` files. |
| `test_source_ratio` | float | `test_loc / source_loc` (0.0 if `source_loc` is 0). |
| `top_level_src_packages` | int | Count of unique top-level directories directly under `src/` that contain git-tracked files. |
| `test_subdirectories` | int | Count of unique parent directories of git-tracked `tests/**/*.py` files (excluding the `tests/` root itself), content-based, not a raw filesystem walk. |
| `commit_count` | int | Total commits in the repo's full history (`git log --oneline`). |
| `doc_count` | int | Count of git-tracked `docs/**/*.md` files. |
| `registry_size_bytes` | int | `docs/REGISTRY.yaml`'s size in bytes at snapshot time. Captured for completeness but not rendered as its own scorecard dimension — see the scorecard's registry-size fold below. |
| `registry_size_lines` | int | `docs/REGISTRY.yaml`'s line count at snapshot time. This is the unit the scorecard actually trends for registry size (the more human-legible of the two, matching `format_report()`'s own presentation order). |
| `dead_bytecode_files` | int | Count of `.pyc` files anywhere in the live tree with no corresponding `.py` source. |
| `unused_core_dependencies` | list[string] | `pyproject.toml` `[project.dependencies]` entries with no matching `import`/`from` statement anywhere in the git-tracked tree. Not a scalar — the scorecard renders this dimension as a raw value/count, never through the Δ/arrow trend branch. |
| `churn_lines_changed_excl_bookkeeping` | int | Total insertions+deletions across full history, excluding `agent-monitoring/*.jsonl`, `tickets/working_log.csv`, and `docs/REGISTRY.yaml` via a real git pathspec exclusion. |
| `snapshot_schema_version` | int | Version of this snapshot record's own shape (distinct from any individual field's meaning) — see below. |

---

## Second metric source — craft metrics (schema version 2)

These keys come from `tools/code_health/metrics.py::compute_craft_metrics`, not from
`build_report()`. `build_report()` and `make codebase-health-baseline` are unchanged, so the baseline
target does not depend on the code-health tools. Every key is a plain integer and each trends on its
own: there is no aggregate or combined craft number anywhere (D24 sections J and M).

**Live keys** (`craft_<thing>`) are measured at snapshot time from ruff, complexipy and the line-count
report over `src/` with the repository's own configuration. They are the offline Python tools; a
snapshot never runs jscpd or needs the network.

| Field | Type | Meaning |
|---|---|---|
| `craft_ruff_findings` | int | Total ruff findings for the rules in `[tool.ruff.lint]` (the standard's rules plus the pyflakes correctness group). |
| `craft_correctness_findings` | int | Ruff findings whose code starts `F` (pyflakes) or `E9` (syntax and I/O errors). |
| `craft_missing_public_docstrings` | int | Ruff `D100` to `D104` findings: public modules, classes, methods, functions and packages without a docstring. |
| `craft_missing_annotations` | int | Ruff `ANN` findings (`ANN401`, `Any` in a signature, is not selected). |
| `craft_functions_over_cognitive_limit` | int | Functions over `[tool.complexipy] max-complexity-allowed` (15). |
| `craft_functions_over_length_limit` | int | Functions over the fail length in `[tool.code_health.size]` (80 lines). |
| `craft_classes_over_length_limit` | int | Classes over the class length limit (500 lines). |
| `craft_modules_over_length_limit` | int | Modules over the module length limit (1,000 lines). |
| `craft_longest_function_lines` | int | Length of the longest function over the fail limit, 0 if none. |
| `craft_highest_cognitive_complexity` | int | Highest cognitive complexity among functions over the limit, 0 if none. |

**Registry-derived keys** (`craft_baseline_<thing>`) are read from
`registries/code_health_exceptions.jsonl`. They describe the baselined state as of the last seed or
`tighten`, not a live measurement, and the scorecard labels them "(registry)". Duplication is
reported this way because jscpd needs `npx`; it can become a live key once jscpd has a lockfile.

| Field | Type | Meaning |
|---|---|---|
| `craft_baseline_rows` | int | Rows in the registry (0 if the repository has none). |
| `craft_baseline_unreviewed_rows` | int | Rows with `reviewed: false`. |
| `craft_baseline_duplicate_file_pairs` | int | jscpd rows: pairs of files sharing duplicated blocks. |
| `craft_baseline_duplicated_lines` | int | Sum of duplicated lines over those pairs. |

---

## `snapshot_schema_version` — meaning and bump discipline

`snapshot_schema_version` versions the snapshot record's shape itself — the
set of keys captured, not any individual metric's computation. It starts at
`1` (`tools/codebase_health_snapshot.py::SNAPSHOT_SCHEMA_VERSION`) and is
manually incremented whenever `EXPECTED_SNAPSHOT_KEYS` changes.

| Version | Keys |
|---|---|
| 1 | `build_report()`'s 14 keys. No record of this version has been written to `agent-monitoring/codebase_health_history.jsonl`. |
| 2 | Version 1's keys plus the 14 `craft_*` keys above (`TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS`). |

A schema-version bump is always a **paired change**, landed in the same
commit:

1. Edit `EXPECTED_BASELINE_KEYS` (or the craft key set in `tools/code_health/metrics.py`) to
   match the new shape, which updates `EXPECTED_SNAPSHOT_KEYS`.
2. Increment `SNAPSHOT_SCHEMA_VERSION`.
3. Update this doc's field tables to match.

Older records in the history file keep whatever `snapshot_schema_version`
they were written with — this file is append-only, so no historical record
is ever rewritten to match a newer schema. `build_scorecard` still only compares the two most
recent snapshots, and it tolerates a version boundary for the craft dimensions: if the previous
record has no such key the dimension shows "no trend data yet", and if the latest record has none
the dimension is left out. The 14 baseline dimensions are required in every record.

---

## Scorecard read path

`tools/codebase_health_snapshot.py::read_snapshots` / `build_scorecard` /
`format_scorecard` render a per-dimension trend view over this file's
records — 11 scalar dimensions get a Δ + `↑`/`↓`/`→` arrow, the registry-size
fold renders `registry_size_lines` only, `unused_core_dependencies`
renders as a raw value/count, and each `craft_*` key gets its own Δ + arrow row. An arrow
shows direction only; it does not say whether up is good or bad. There is no aggregate/combined score anywhere
in the scorecard's structured output or printed text — see
`docs/plans/archive/codebase_health_observatory_tooling_epic.md`'s "Out of scope"
bullet and the source audit
(`docs/audits/D24_codebase_health_observatory.md` §J/§M) this decision comes
from.

`make codebase-health-snapshot` appends one record; `make codebase-health-scorecard`
prints the trend view. Both are on-demand only, not CI-wired.
