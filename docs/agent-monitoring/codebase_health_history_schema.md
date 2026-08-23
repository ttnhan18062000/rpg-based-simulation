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
is meaningful on its own; the value is in the sequence.

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
  "snapshot_schema_version": 1
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

Every field below is one key from `tools/codebase_health_baseline.py::build_report()`'s
own return dict, used exactly as returned — this module never recomputes or
re-derives any individual metric. `codebase_health_snapshot.py::EXPECTED_SNAPSHOT_KEYS`
is the enforced, frozen source of truth for this set: `build_snapshot_record`
validates `set(report.keys()) == EXPECTED_SNAPSHOT_KEYS` exactly (not a
subset/superset check) on every write and raises `RuntimeError` loudly on any
mismatch, so a future `build_report()` field rename/add/remove is a visible
breaking change here, never silent drift.

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

## `snapshot_schema_version` — meaning and bump discipline

`snapshot_schema_version` versions the snapshot record's shape itself — the
set of keys captured, not any individual metric's computation. It starts at
`1` (`tools/codebase_health_snapshot.py::SNAPSHOT_SCHEMA_VERSION`) and is
manually incremented whenever `EXPECTED_SNAPSHOT_KEYS` changes.

A schema-version bump is always a **paired change**, landed in the same
commit:

1. Edit `EXPECTED_SNAPSHOT_KEYS` in `tools/codebase_health_snapshot.py` to
   match `build_report()`'s new shape.
2. Increment `SNAPSHOT_SCHEMA_VERSION`.
3. Update this doc's field table to match.

Older records in the history file keep whatever `snapshot_schema_version`
they were written with — this file is append-only, so no historical record
is ever rewritten to match a newer schema. A reader that needs to compare
across a schema-version boundary is responsible for handling that itself;
`tools/codebase_health_snapshot.py::build_scorecard` does not do this today
(it only ever compares the two most recent snapshots, and this repo has not
yet needed a version bump).

---

## Scorecard read path

`tools/codebase_health_snapshot.py::read_snapshots` / `build_scorecard` /
`format_scorecard` render a per-dimension trend view over this file's
records — 11 scalar dimensions get a Δ + `↑`/`↓`/`→` arrow, the registry-size
fold renders `registry_size_lines` only, and `unused_core_dependencies`
renders as a raw value/count. There is no aggregate/combined score anywhere
in the scorecard's structured output or printed text — see
`docs/plans/codebase_health_observatory_tooling_epic.md`'s "Out of scope"
bullet and the source audit
(`docs/audits/D24_codebase_health_observatory.md` §J/§M) this decision comes
from.

`make codebase-health-snapshot` appends one record; `make codebase-health-scorecard`
prints the trend view. Both are on-demand only, not CI-wired.
