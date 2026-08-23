---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD
artifact_type: plan
tags: [agent-monitoring]
---

# Implementation Plan — TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD

## Summary

Add one new module, `tools/codebase_health_snapshot.py`, that (1) appends `build_report()`'s
existing 13-field dict as one JSON line to a new append-only history file,
`agent-monitoring/codebase_health_history.jsonl`, reusing the hardened, lock-protected
`tools/agent-monitoring/writer.py::write_line` rather than a plain unlocked `open(path, "a")`; and
(2) reads back N historical snapshot lines and renders a per-dimension trend scorecard (`↑`/`↓`/`→`
arrows, mirroring `personality_audit.py`'s convention) with no aggregate/combined score anywhere in
either the structured return value or the printed text. The module follows the exact
`build_<x>()`/`format_<x>()`/`main()` triad `tools/codebase_health_baseline.py` and
`tools/code_health_impact.py` already establish, imports `build_report` directly (never
re-implements or shells out to it), and adds a frozen 13-key schema allowlist plus a
`snapshot_schema_version` field so a future change to `build_report()`'s shape fails loudly at
write time instead of silently drifting. Two Makefile targets are added
(`codebase-health-snapshot`, `codebase-health-scorecard`), both correctly listed in `.PHONY`,
neither wired into CI. Thirteen new tests land in `tests/tools/test_codebase_health_snapshot.py`,
all writing exclusively under `tmp_path`, never the real `agent-monitoring/` directory.

## Steps

### Step 1 — Module skeleton, constants, and schema-freeze allowlist

**Files:** tools/codebase_health_snapshot.py (new)

**Change:** Create the new module with the standard sibling-module shape confirmed in
`tools/codebase_health_baseline.py:63-64` (`_TOOLS_DIR = Path(__file__).resolve().parent`,
`_REPO_ROOT = _TOOLS_DIR.parent`) and `tools/code_health_impact.py`'s import-guard pattern
(`sys.path.insert(0, str(_TOOLS_DIR))` before `from codebase_health_baseline import build_report`,
since both modules live directly in plain `tools/` — no hyphenated-directory boundary for this
particular import).

Add a second `sys.path.insert` for the hyphenated `tools/agent-monitoring/` directory, mirroring
`tools/agent-monitoring/record_run.py:9-10`'s own pattern exactly but pointed at the sibling
directory instead of the file's own parent:
```python
sys.path.insert(0, str(_REPO_ROOT / "tools" / "agent-monitoring"))
from writer import write_line  # noqa: E402
```
This is confirmed necessary because `tools/agent-monitoring/`'s hyphen makes
`import tools.agent_monitoring.writer` impossible as a dotted import — no `__init__.py`-based
package name can contain a hyphen (investigation.md item 3, confirmed by reading
`tools/agent-monitoring/writer.py` in full and its real caller `tools/agent-monitoring/record_run.py:1-10`).

Define the frozen schema allowlist, hand-copied once from the real `build_report()` return
statement I read directly at `tools/codebase_health_baseline.py:238-253`:
```python
EXPECTED_SNAPSHOT_KEYS = frozenset({
    "source_loc", "source_files", "test_loc", "test_files", "test_source_ratio",
    "top_level_src_packages", "test_subdirectories", "commit_count", "doc_count",
    "registry_size_bytes", "registry_size_lines", "dead_bytecode_files",
    "unused_core_dependencies", "churn_lines_changed_excl_bookkeeping",
})
SNAPSHOT_SCHEMA_VERSION = 1
DEFAULT_HISTORY_PATH = _REPO_ROOT / "agent-monitoring" / "codebase_health_history.jsonl"
```
Also add the module's provenance docstring citing this ticket ID, the epic
(`TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`), and D24 §J/§M, following the
substantial-docstring convention both sibling modules use (`tools/codebase_health_baseline.py:1-54`,
`tools/code_health_impact.py:1-51`).

**Do NOT touch:** `tools/codebase_health_baseline.py` — no edits to `build_report()`,
`format_report()`, or any of its constituent functions. This step only imports from it.

**Verify:** No standalone test for this step alone; it is exercised indirectly by every test in
Steps 2-4. (The schema-freeze allowlist itself is verified in Step 2.)

### Step 2 — Snapshot-write entry point (schema validation + writer.py reuse)

**Files:** tools/codebase_health_snapshot.py

**Change:** Add `build_snapshot_record(repo_root: Path) -> dict`:
1. Call `build_report(repo_root)` directly — the real dict, no re-derivation (satisfies AC #4).
2. Validate `set(report.keys()) == EXPECTED_SNAPSHOT_KEYS` exactly (not a subset/superset check —
   investigation.md's option (a), which the ticket's own Risks section recommends). On mismatch,
   raise a `RuntimeError` with the actual vs. expected key diff in the message — raise loudly, do
   not silently drop/pad/warn-and-continue. This is the entire mechanism that makes a future
   `build_report()` field rename/add/remove a visible breaking change instead of silent drift, per
   Scope item 3.
3. Return `{**report, "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION}`.

Add `write_snapshot(repo_root: Path, history_path: Path) -> bool` — **`history_path` has no
default** (Review-caught fix, see Anti-Drift Notes): `write_line`'s own real signature
(`tools/agent-monitoring/writer.py:107`, confirmed by direct read) has no default for
`target_path` either, which is exactly why `test_monitoring_writer.py`'s literal-source-scan
guard (`tests/tools/test_monitoring_writer.py:31-51`) can catch a bad path — every call site is
forced to write an explicit path literal into the test source. A `history_path=DEFAULT_HISTORY_PATH`
default on `write_snapshot` would defeat that same guard mechanism: a test that simply omits the
keyword argument (`chs.write_snapshot(repo_root)`) would silently target the real
`agent-monitoring/codebase_health_history.jsonl` with no forbidden string ever appearing in that
test's source for the scan to find. Making `history_path` required turns an omitted argument into
an immediate `TypeError` at every call site instead of a silent real-file write.
`DEFAULT_HISTORY_PATH` is applied only at the `main()` layer (Step 5), where a real CLI default is
actually needed — never inside `build_snapshot_record`/`write_snapshot` themselves.
1. Call `build_snapshot_record(repo_root)`.
2. Serialize with `json.dumps(record, separators=(",", ":"))`, matching `record_run.py`'s own
   serialization convention (confirmed in `tools/agent-monitoring/record_run.py`, the call site
   `write_line(RUNS_FILE, json.dumps(record, separators=(",", ":")))`).
3. Call `write_line(history_path, line)` and return its `bool` result unchanged — never wrap it in
   a try/except that could mask `write_line`'s own already-never-raises contract, and never crash
   the caller on `False`. `main()` (Step 5) is responsible for turning `False` into a
   stderr warning, following `record_run.py`'s own `on False, print WARNING to stderr, do not
   hard-fail` convention (investigation.md item 3).

**Other writers to `agent-monitoring/codebase_health_history.jsonl`:** none exist yet — this is a
brand-new file this ticket introduces. Within `write_line` itself, the only other logic that
touches this same target path is the lock-file protocol (`_lock_path_for`,
`tools/agent-monitoring/writer.py:37-38`) and the diagnostic sidecar
(`_diagnostic_path_for`, `tools/agent-monitoring/writer.py:41-42`), both scoped by-path
automatically (they derive from `target_path`, so they will not collide with the lock file or
`.writer_health.jsonl` used by `runs.jsonl`/`events.jsonl`/`tools.jsonl` — confirmed by reading
`_lock_path_for`/`_diagnostic_path_for`'s implementations directly, both of which build their path
from `target_path.with_name(...)`/`target_path.parent / ...`, i.e. always relative to the specific
file passed in, never a shared global path). `write_line` itself already has 3 production callers
(`record_run.py`, `record_events.py`, `post_tool_hook.py`, confirmed in investigation.md item 3),
none of which write to this ticket's new path — this ticket adds a 4th caller of the shared
utility, not a 4th caller of the same *file*, so there is no ordering/race/double-counting
interaction with those 3 existing callers at all.

**Do NOT touch:** `tools/agent-monitoring/writer.py` itself — no changes to `write_line`,
`write_lines`, the lock protocol, or the diagnostic sidecar. This step only calls the existing
public function.

**Verify:**
- `test_two_invocations_append_two_separate_records_without_truncation`
- `test_appended_record_is_valid_json_matching_frozen_schema_allowlist`
- `test_write_failure_does_not_crash_caller`
- `test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented`
- `test_schema_mismatch_raises_loudly_not_silently`
- `test_schema_version_field_present_and_stable_across_writes`

### Step 3 — Scorecard build (read history, compute per-dimension trend)

**Files:** tools/codebase_health_snapshot.py

**Change:** Add `read_snapshots(history_path: Path) -> list[dict]`:
- If `history_path` does not exist, return `[]` (do not raise — this is the expected first-run
  state per AC #3's zero-snapshot edge case).
- Otherwise read the file line by line, `json.loads` each non-empty line, return the list in file
  order (oldest first).

Add `build_scorecard(snapshots: list[dict]) -> dict`. Dimension-set decision (adopting
investigation.md item 6's recommendation, made explicit here):
- **11 scalar trend dimensions** (Δ + `↑`/`↓`/`→` arrow each): `source_loc`, `source_files`,
  `test_loc`, `test_files`, `test_source_ratio`, `top_level_src_packages`, `test_subdirectories`,
  `commit_count`, `doc_count`, `dead_bytecode_files`, `churn_lines_changed_excl_bookkeeping`.
- **`registry_size_bytes` + `registry_size_lines` fold to one row**, decision: show
  `registry_size_lines` only, labeled `"registry_size_lines"`, as the scorecard's trended
  dimension — the more human-legible unit per investigation.md item 6's framing, and the same unit
  `format_report()` prints first-and-bolder in its own combined `"{bytes:,} bytes /
  {lines:,} lines"` line (`tools/codebase_health_baseline.py:268`). `registry_size_bytes` is still
  captured in every snapshot record (it is part of `EXPECTED_SNAPSHOT_KEYS`, per the Anti-Drift
  Hazards note that the frozen allowlist must not silently drop any real `build_report()` field)
  but is not rendered as its own scorecard row — one real signal, one row, not two independently
  "trending" rows over the same underlying quantity.
- **`unused_core_dependencies` renders as a raw value/count, never through the arrow branch.**
  Since it is a `list[str]`, not a scalar, `build_scorecard` must route it through a distinct
  non-trended code path — show the latest snapshot's list length and, if it changed since the
  prior snapshot, the raw before/after list values (no `↑`/`↓`/`→`), never diffed via numeric
  subtraction.

Trend-comparison scope (adopting investigation.md's recommendation): always compare only the two
*most recent* snapshots (`snapshots[-1]` vs. `snapshots[-2]`), regardless of how many total
snapshots exist. This is the simplest choice that satisfies AC #2 ("two or more snapshots render a
directional indicator") and AC #3 ("exactly one snapshot degrades gracefully") literally — no
richer N-snapshot sparkline/first-vs-last comparison is in scope; if a future ticket wants that, it
is a new feature on top of this one, not an extension of this plan.

For each of the 11 scalar dimensions: `diff = latest[key] - previous[key]`; arrow = `"↑"` if
`diff > 0` else `"↓"` if `diff < 0` else `"→"` — mirroring `personality_audit.py`'s
`_print_summary()` convention read directly at lines 277-286 (`Δ={diff:+.4f}
({'↑' if diff > 0 else '↓' if diff < 0 else '→'})`). `test_source_ratio`'s flat case uses exact
float equality (`diff == 0`), not a tolerance band: two live runs of `build_report()` against the
exact same git commit produce bit-identical floats (the ratio is a pure deterministic function of
`test_loc`/`source_loc`, both integer git-tracked line counts with no floating-point accumulation
or filesystem-order dependency), so exact-zero is the correct behavior, not an approximation —
adopting investigation.md item 8's own stated default explicitly rather than leaving it unstated.

**No aggregate signal, not even a count** (adopting investigation.md's recommendation explicitly):
`build_scorecard`'s returned dict must contain no key resembling `"score"`, `"overall"`,
`"combined"`, `"summary"`, `"up_count"`, `"down_count"`, or any other single derived
number-of-changes summary — not even a plain "N up / M down" line. This is deliberate: the
ticket's Out of Scope bullet says "at any layer of the output," and a count is itself a single
aggregate judgment over the per-dimension results, which is exactly the shape D24 §J/§M and the
epic's own Out of Scope bullet rule out. `build_scorecard`'s return shape is a per-dimension
mapping only (dimension name → `{latest, previous, diff, arrow}` or the no-trend-data variant from
Step 4), nothing above that layer.

**Do NOT touch:** `tools/personality_audit.py` — read only for its rendering convention, no
imports from it and no edits to it (its Δ computation is intra-run quartile comparison, not
cross-snapshot, so there is no function to reuse from it directly — only the presentation
convention is mirrored, per investigation.md item 2).

**Verify:**
- `test_scorecard_renders_per_dimension_trend_arrow_for_two_snapshots`
- `test_scorecard_output_has_no_aggregate_or_combined_score_field`
- `test_non_scalar_dimension_unused_core_dependencies_does_not_get_forced_arrow`

### Step 4 — Graceful degradation: one snapshot and zero snapshots

**Files:** tools/codebase_health_snapshot.py

**Change:** In `build_scorecard`, branch on `len(snapshots)`:
- `0`: return a scorecard dict with an explicit `"no_snapshots_yet": True` marker (or equivalent
  clearly-labeled empty-state shape) and no per-dimension rows — `format_scorecard` (Step 5) must
  render a clear "no snapshots yet" message from this shape, never a traceback or an empty table
  with no explanation.
- `1`: for every one of the 11 scalar dimensions plus the folded registry row and the
  `unused_core_dependencies` row, render the single snapshot's raw value alongside an explicit
  `"no trend data yet"` label (a real, assertable string/flag on each row, not merely "arrow
  omitted" — mirrors `personality_audit.py`'s own no-prior-data handling: `trend` stays `""` when
  either side is `None`, the surrounding print still executes with the label present, it just
  omits the Δ/arrow suffix, per investigation.md item 2's second bullet). Do not compute or
  fabricate a trend from the single point.
- `>=2`: the Step 3 two-most-recent-snapshot comparison path.

**Do NOT touch:** Step 3's dimension-set decisions (registry-size fold, `unused_core_dependencies`
carve-out) — this step only adds the `0`/`1`-snapshot branches around the same per-dimension shape
Step 3 already defines; it must not introduce a second, divergent dimension list for the
degraded cases.

**Verify:**
- `test_scorecard_with_one_snapshot_labels_no_trend_data_without_crashing`
- `test_scorecard_with_zero_snapshots_does_not_crash`

### Step 5 — `format_scorecard` and `main()`

**Files:** tools/codebase_health_snapshot.py

**Change:** Add `format_scorecard(scorecard: dict) -> str`: pure presentation over
`build_scorecard`'s returned dict, following `format_report`'s fixed-width-table convention read
directly at `tools/codebase_health_baseline.py:256-277` (label column padded, value column
right-aligned). Must render, per dimension: label, latest value, and either the `↑`/`↓`/`→` +
signed Δ suffix (two-or-more-snapshot case) or the `"no trend data yet"` label (one-snapshot case)
or the whole-table "no snapshots yet" message (zero-snapshot case). Must contain no aggregate line
anywhere in the printed text, matching the structured-dict guarantee from Step 3/4 — this is a
second, independent enforcement point (both the dict shape and the printed text must be clean,
since a downstream consumer could read either).

Add `main(argv=None) -> int` with an `argparse` subcommand or a `--mode {snapshot,scorecard}`-style
split (implementer's call on exact CLI shape, but it must expose both operations from one module
per the ticket's own `expected: tools/codebase_health_snapshot.py` single-file path) plus:
- `--repo-root` (default `_REPO_ROOT`), matching both sibling modules' own flag.
- `--history-path` (default `DEFAULT_HISTORY_PATH`) so tests and the Makefile's scratch-location
  invocation (test `test_make_target_runs_successfully_end_to_end`) never need to touch the real
  `agent-monitoring/` directory.
- `--last N` (optional, only meaningful for the scorecard read path) is **not** needed given Step
  3's fixed "always compare the two most recent" decision — omit it; do not add an unused flag.

On the snapshot-write path, when `write_snapshot(...)` returns `False`, print a `WARNING` to
stderr (mirroring `record_run.py`'s own convention) and still return `0` — a monitoring/snapshot
write failure must never fail the invoking process, consistent with this repo's
"monitoring write failure must never fail the workflow" Hard Rule, applied here by analogy since
this reuses the identical non-raising writer contract.

**Do NOT touch:** `format_report`/`main` in `tools/codebase_health_baseline.py` — this step adds
a wholly separate `main()` in the new module; it must not modify the sibling module's own CLI
entry point.

**Verify:** Exercised together with Step 6's Makefile end-to-end test
(`test_make_target_runs_successfully_end_to_end`), plus indirectly by every Step 2-4 test that
calls through `main()`'s underlying functions.

### Step 6 — Makefile wiring

**Files:** Makefile

**Change:** Add two new targets immediately after the existing `codebase-health-impact` target
(`Makefile:290-291`), following the exact `## <description> (on-demand only — not CI)` comment
convention confirmed at `Makefile:287-291`:
```
codebase-health-snapshot: ## Append a codebase-health metrics snapshot to agent-monitoring/codebase_health_history.jsonl (on-demand only — not CI)
	python3 tools/codebase_health_snapshot.py snapshot

codebase-health-scorecard: ## Print a per-dimension trend scorecard over codebase-health history (on-demand only — not CI)
	python3 tools/codebase_health_snapshot.py scorecard
```
(Exact subcommand names depend on Step 5's final CLI shape; the `## ... (on-demand only — not CI)`
comment text and target names `codebase-health-snapshot`/`codebase-health-scorecard` are fixed by
this plan.)

Add both new target names to the `.PHONY:` line at `Makefile:1`, following the
`agent-monitoring-index`/`parity-index` precedent (both present in `.PHONY`) rather than repeating
the `codebase-health-baseline`/`codebase-health-impact` omission confirmed in investigation.md
item 4 — this is a deliberate correction of a real, confirmed sibling gap, not a new convention.

**Other writers to the `.PHONY:` line:** none concurrent — it is a single static line in a
version-controlled file, edited serially by whichever ticket adds a new phony target; no
runtime/concurrent-write concern applies (unlike the JSONL history file in Step 2). The only
interaction to manage is textual: insert the two new names into the existing space-separated list
without disturbing any of the ~50 existing names already on that line.

**Do NOT touch:** the `codebase-health-baseline`/`codebase-health-impact` targets' own `.PHONY`
omission — fixing that pre-existing sibling gap is out of scope for this ticket; only this
ticket's own two new targets are added to `.PHONY`.

**Verify:** `test_make_target_runs_successfully_end_to_end`

### Step 7 — New tests

**Files:** tests/tools/test_codebase_health_snapshot.py (new)

**Change:** Implement all 12 tests from test_plan.md's "New Tests Required" section, plus one new
13th test (`test_no_test_target_path_resolves_under_real_agent_monitoring_dir`, Review-caught
addition, see above), following
`test_codebase_health_baseline.py`'s established fixture conventions read directly at
`tests/tools/test_codebase_health_baseline.py:1-33` — module-level `sys.path.insert(0,
str(_TOOLS_DIR))` + `import codebase_health_snapshot as chs`, a duplicated (not shared-conftest)
`_init_repo(tmp_path)`/`_commit(tmp_path, message)` helper pair, real git repos under `tmp_path`,
`build_report()`/the new module's functions called for real, never mocked except where the test
explicitly needs to inject a failure (`test_write_failure_does_not_crash_caller` monkeypatches the
imported `write_line` name to return `False`; the three schema-mismatch sub-cases in
`test_schema_mismatch_raises_loudly_not_silently` monkeypatch/stub `build_report` to return an
added/removed/renamed key). Every test's history-file path must be a `tmp_path`-rooted path passed
explicitly via `history_path=`/`--history-path`, never the module's own `DEFAULT_HISTORY_PATH` —
this is the direct guard against the Anti-Drift Test Guard in test_plan.md ("never target the real
`agent-monitoring/` directory from a test"). This is now enforced two ways, not one (Review-caught
fix): (1) `history_path` has no default on `write_snapshot`/`build_snapshot_record` themselves
(Step 2), so an omitted argument is a hard `TypeError`, not a silent real-file write; (2) add one
new test, `test_no_test_target_path_resolves_under_real_agent_monitoring_dir`, mirroring
`test_monitoring_writer.py:31-51`'s literal-source-scan pattern exactly (same `forbidden` string
list, same `inspect.getsource()` scan over every other test function in this file) — this remains
useful defense-in-depth for the CLI/Makefile end-to-end test below, where a hardcoded real path
could still slip in via a different route than an omitted keyword argument.
`test_make_target_runs_successfully_end_to_end` must
invoke `make codebase-health-snapshot`/`make codebase-health-scorecard` with an `ARGS=` or
environment override pointing at a `tmp_path` history file if the Makefile target does not itself
accept a path override — if the Makefile targets as written in Step 6 have no way to redirect the
history path from `make`, this test must instead invoke the underlying `main()` function directly
with `--history-path` (matching how `test_code_health_impact.py`'s own
`test_make_target_runs_successfully_with_plausible_values`-shaped test handles path arguments) —
implementer's call on the exact mechanism, but the real `agent-monitoring/` directory must never
be written to by any test in this file.

**Do NOT touch:** `tests/tools/test_codebase_health_baseline.py`,
`tests/tools/test_code_health_impact.py`, `tests/tools/test_monitoring_writer.py`,
`tests/tools/test_monitoring_writer_lockfile_candidate.py` — all four are regression surface only
(test_plan.md), read for pattern reference, never edited by this ticket.

**Verify:** `pytest tests/tools/test_codebase_health_snapshot.py -v` (all 13 tests pass), plus
`pytest tests/tools/ -k "codebase_health or code_health or monitoring_writer" -v` (regression
surface, per test_plan.md's Scoped Pytest Commands).

### Step 8 — New schema doc

**Files:** docs/agent-monitoring/codebase_health_history_schema.md (new)

**Change:** Confirming investigation.md's suggested path (`docs/agent-monitoring/
codebase_health_history_schema.md`) — this is the correct location, not a new
`docs/observability/` doc: `docs/agent-monitoring/` already exists as a directory
(confirmed: contains `README.md` and `schema.md`) specifically for documenting the
`agent-monitoring/*.jsonl` file family's schemas, and this ticket's new history file lives inside
that same directory (`agent-monitoring/codebase_health_history.jsonl`, per Step 2's
`DEFAULT_HISTORY_PATH`) — keeping the doc in the same directory family as the file it describes
matches the existing `schema.md` precedent exactly rather than fragmenting doc location from file
location.

Content, mirroring `docs/agent-monitoring/schema.md`'s "Historical Corrections" section language
(read directly at lines 106-115) and its per-file schema-table convention:
- File path: `agent-monitoring/codebase_health_history.jsonl`.
- Append-only contract statement: mirrors schema.md's own wording — "append-only for all new
  writes; the writer (`tools/codebase_health_snapshot.py::write_snapshot`, via
  `tools/agent-monitoring/writer.py::write_line`) only ever appends, never rewrites an existing
  line" — with no historical-correction exception yet (unlike `runs.jsonl`'s one documented
  case), since this file is new.
- Full field table: all 13 `EXPECTED_SNAPSHOT_KEYS` names + `snapshot_schema_version`, with type
  and meaning columns matching investigation.md's own field table (item 1) — the doc must state
  this is a frozen, versioned schema and that `codebase_health_snapshot.py::EXPECTED_SNAPSHOT_KEYS`
  is the enforced source of truth, raising loudly on any drift from `build_report()`.
- `snapshot_schema_version`'s meaning and bump discipline: manually incremented whenever
  `EXPECTED_SNAPSHOT_KEYS` changes, documented as a paired change (allowlist edit +
  version bump + doc table update, all in the same commit).

**Do NOT touch:** `docs/agent-monitoring/schema.md` itself — it documents `runs.jsonl`/
`events.jsonl`/`tools.jsonl`, a separate file family; this ticket adds a sibling doc, not an edit
to that file (confirmed via investigation.md's "Docs Requiring Update" section, which lists
`schema.md` as a cross-reference source only, not a file this ticket edits).

**Verify:** `pytest tests/docs/test_doc_integrity.py -v` (the new doc path must satisfy whatever
doc-path-existence check is currently wired, per test_plan.md's Regression Surface note).

### Step 9 — Epic doc bullet resolution

**Files:** docs/plans/codebase_health_observatory_tooling_epic.md

**Change:** Apply the exact `~~struck-through~~` + `**Resolved** (TICKET-ID, ...)` treatment
already used for the two sibling bullets immediately above, read directly at lines 27-64 of this
file. The target bullet (lines 65-68, starting "Historical metric snapshots: an append-only file
following the same pattern...") gets struck through in full and followed by a `**Resolved**
(`TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD`, 2026-08-2X)` paragraph summarizing: the new
`tools/codebase_health_snapshot.py` module, the `agent-monitoring/codebase_health_history.jsonl`
history file, the frozen-schema + `snapshot_schema_version` mechanism, the two new Makefile
targets (on-demand only, matching the two sibling targets' own precedent), and the explicit
no-aggregate-score decision — matching the level of implementation-summary detail the two existing
resolved bullets already carry (each cites the concrete module/function names, the design decision
made, and how it was verified).

**Do NOT touch:** the two already-resolved bullets above it (lines 27-64), or the "Out of scope"
section (lines 72-75) — this step only resolves the one bullet this ticket's scope covers.

**Verify:** No dedicated test; verified by direct diff review against the two sibling bullets'
existing formatting during Verify phase.

## Scope Guards

Explicit list of things this plan must not touch, per the ticket's Out of Scope section and
investigation.md's Anti-Drift Hazards:

- **`build_report()`'s existing metric computation** (`tools/codebase_health_baseline.py:233-253`)
  and every constituent function it calls — no edits, no re-implementation, no re-derivation
  anywhere in the new module. The new module only imports and calls `build_report` directly.
- **`format_report()`'s printed text** — the new module never parses, subprocess-shells-out to, or
  otherwise depends on `format_report()`'s text output. It consumes `build_report()`'s dict only.
- **Any aggregate/combined score field, anywhere in the output structure** — not just the printed
  text. `build_scorecard`'s returned dict must be auditable (via a denylist-style key check) to
  contain no `score`/`overall`/`combined`/`summary`-shaped key, and `format_scorecard`'s printed
  text must contain no equivalent line. This includes a plain "N up / M down" count — omitted
  entirely, per investigation.md's explicit recommendation, since even a bare count functions as a
  single derived judgment.
- **CI wiring of the new Makefile targets** — `codebase-health-snapshot` and
  `codebase-health-scorecard` are on-demand only, matching both sibling targets' precedent; no
  `.github/workflows/*.yml` file is touched by this ticket.
- **`tools/agent-monitoring/writer.py`** — no changes to `write_line`, `write_lines`, the lock
  protocol, or the diagnostic sidecar. Only a new consumer is added.
- **The real `agent-monitoring/` directory from any test** — every new test writes its synthetic
  history file under `tmp_path`, never the module's own `DEFAULT_HISTORY_PATH` default, and never
  triggers a write to `runs.jsonl`/`events.jsonl`/`tools.jsonl` even accidentally (no test should
  invoke `write_snapshot`/`main()` without an explicit `history_path`/`--history-path` override).
- **`docs/parity_ledger/`** — no entry needed or added; confirmed by investigation.md (tools/-only
  ticket, no `src/` simulation logic, matches both sibling tickets' identical zero-parity-coverage
  precedent).
- **`TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR`'s surface** — this ticket's snapshot/scorecard
  output shape is a dependency for that later ticket, but this ticket does not build any part of
  the PR/change-impact report generator itself.
- **The `codebase-health-baseline`/`codebase-health-impact` targets' own pre-existing `.PHONY`
  omission** — not fixed by this ticket; only this ticket's own two new targets are added to
  `.PHONY`.

## Dependency Map

- Step 1 (skeleton/constants) blocks Steps 2-5 (all reference `EXPECTED_SNAPSHOT_KEYS`,
  `SNAPSHOT_SCHEMA_VERSION`, `DEFAULT_HISTORY_PATH`, or the sibling-import scaffolding).
- Step 2 (write path) and Step 3 (scorecard build) are independent of each other once Step 1 is
  done — Step 2 does not depend on Step 3's dimension-set decisions, and Step 3 only needs
  Step 2's record shape (the schema-versioned dict) to exist conceptually, not Step 2's code.
- Step 4 (degradation) depends on Step 3 (extends `build_scorecard`'s branching).
- Step 5 (`format_scorecard`/`main`) depends on Steps 2-4 (composes all of them).
- Step 6 (Makefile) depends on Step 5 (needs the final CLI subcommand names).
- Step 7 (tests) depends on Steps 1-6 all being in place, though individual test groups can be
  written incrementally alongside each corresponding step.
- Step 8 (schema doc) depends on Step 1's final field list and Step 2's version field — write
  after Steps 1-2 are stable, does not block any other step.
- Step 9 (epic doc bullet) is independent of all other steps; can be done last, immediately before
  Finalize.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: running the snapshot command twice appends two separate records without truncation | Step 2 (write_snapshot/write_line reuse), Step 6 (Makefile target) | `test_two_invocations_append_two_separate_records_without_truncation` |
| AC #2: given two+ snapshots, scorecard renders per-dimension directional indicator, no aggregate/combined 'score' field | Step 3 (build_scorecard trend logic, no-aggregate guarantee), Step 5 (format_scorecard text guarantee) | `test_scorecard_renders_per_dimension_trend_arrow_for_two_snapshots`, `test_scorecard_output_has_no_aggregate_or_combined_score_field` |
| AC #3: given exactly one snapshot, scorecard renders without crashing, labels each metric as no-trend-data-yet | Step 4 (one-snapshot branch) | `test_scorecard_with_one_snapshot_labels_no_trend_data_without_crashing`, `test_scorecard_with_zero_snapshots_does_not_crash` |
| AC #4: snapshot payload built by calling build_report() directly, no re-implementation, no parsing of format_report()'s text | Step 2 (build_snapshot_record calls build_report directly) | `test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented` |

## Anti-Drift Notes

- **Do not let AC #4's "no re-derivation" become "no reuse either."** Importing `build_report`
  directly and reusing `writer.py::write_line` is required reuse, not forbidden re-derivation —
  only recomputing the individual metrics independently (LoC counts, churn, etc.) inside the new
  module would violate AC #4.
- **Do not silently drop `unused_core_dependencies` from `EXPECTED_SNAPSHOT_KEYS`** just because it
  is the one non-scalar field that renders differently in the scorecard (Step 3's carve-out) — it
  must still be captured, versioned, and validated in every snapshot record like the other 12
  fields.
- **Do not add a third-party dependency.** `json`/`pathlib`/`argparse`/`sys` cover the entire new
  module's needs; there is no stdlib-only guard in this repo's `tools/` (confirmed via
  `code_health_impact.py`'s real `import yaml`), but nothing in this ticket's scope needs one
  regardless.
- **Do not compute `test_source_ratio`'s `→` case with a tolerance band.** Exact float equality is
  the correct, deliberate choice (Step 3) — two runs against the same commit produce bit-identical
  floats since the ratio has no accumulation or filesystem-order dependency.
- **Do not let the registry-size fold (Step 3) turn into two independently-trending rows.** Only
  `registry_size_lines` is a scorecard dimension; `registry_size_bytes` stays a captured-but-not-
  rendered field in the snapshot record.
- **Do not let the new history file's path collide with or get confused for
  `agent-monitoring/runs.jsonl`.** `DEFAULT_HISTORY_PATH` is its own distinct file,
  `agent-monitoring/codebase_health_history.jsonl`, inside the same directory family purely for
  writer/lock/diagnostic-infrastructure reuse — never the same file, never a shared path constant
  with `RUNS_FILE`.
- **Every new test must pass an explicit `tmp_path`-derived history path** — no test may rely on
  `DEFAULT_HISTORY_PATH`'s real value, even indirectly through an un-overridden `main()` call.
- **`write_snapshot`'s `history_path` parameter must never gain a default value, and
  `build_snapshot_record` must never be given one either** (Review-caught fix; note
  `build_snapshot_record(repo_root: Path) -> dict` per Step 2 has no `history_path` parameter at
  all today — it never touches the history file, only `write_snapshot` does — this bullet guards
  against either function acquiring one with a default in a future refactor). `DEFAULT_HISTORY_PATH`
  is applied exactly once, at the `main()`/argparse layer (Step 5) — never inside either function
  Step 2 defines. A future refactor that adds `history_path: Path = DEFAULT_HISTORY_PATH` onto
  `write_snapshot`'s signature "for convenience" would silently reopen the exact real-file-write
  risk this plan's test-isolation guard exists to close, since an omitted keyword argument would
  then resolve to the real `agent-monitoring/codebase_health_history.jsonl` with nothing textually
  present in the calling test's source for
  `test_no_test_target_path_resolves_under_real_agent_monitoring_dir`'s literal-scan guard to
  catch.

## Deviations (recorded during Implement)

- **Key-count prose correction.** The plan's Summary/Step 1/Step 8/Anti-Drift prose describes
  `EXPECTED_SNAPSHOT_KEYS` as "13 names"/"13-field dict" in several places, but the literal
  frozenset code block in Step 1 (hand-copied from `build_report()`'s real return statement) always
  correctly listed 14 keys, matching `build_report()`'s actual 14-key return dict confirmed by
  direct re-read at implementation time (`tools/codebase_health_baseline.py:238-253`: `source_loc`,
  `source_files`, `test_loc`, `test_files`, `test_source_ratio`, `top_level_src_packages`,
  `test_subdirectories`, `commit_count`, `doc_count`, `registry_size_bytes`, `registry_size_lines`,
  `dead_bytecode_files`, `unused_core_dependencies`, `churn_lines_changed_excl_bookkeeping` = 14).
  The implementation uses the plan's own literal code block verbatim (14 keys, correct) and treats
  every "13" in the surrounding prose as a documentation miscount, not a spec to follow — the
  scorecard's *rendered dimension count* is 13 (11 scalar + 1 folded registry row + 1 non-scalar
  row, since `registry_size_bytes` is captured but not separately rendered), which is likely the
  source of the prose's "13" figure bleeding into the wrong context. `docs/agent-monitoring/codebase_health_history_schema.md`'s
  field table documents all 14 snapshot keys + `snapshot_schema_version` accurately.
- **`write_snapshot` needs an explicit parent-directory `mkdir` before calling `write_line`.**
  Confirmed by direct testing: `tools/agent-monitoring/writer.py::write_line` acquires its lock
  file (a sibling of the target path) *before* its own `target_path.parent.mkdir(...)` call, so the
  parent directory must already exist at call time or lock acquisition itself fails with
  `FileNotFoundError` (caught generically, silently returning `False`). `tools/agent-monitoring/record_run.py`
  already works around this the same way (`RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)`
  immediately before its own `write_line` call) — `write_snapshot` now does the same for
  `history_path` immediately before calling `write_line`. Not called out explicitly in this plan's
  Step 2, but required for `write_snapshot` to function at all against a fresh history-file
  location (which every test in this ticket uses).
- **Makefile targets gained a `$(ARGS)` passthrough**, deviating from Step 6's literal
  no-`$(ARGS)` snippet. Required to satisfy the Scope Guard "the real `agent-monitoring/` directory
  must never be written to by any test" for `test_make_target_runs_successfully_end_to_end`: neither
  Makefile target had any other way to redirect `--history-path` away from `DEFAULT_HISTORY_PATH`
  when invoked via a real `make <target>` subprocess call, which the test needs to genuinely
  exercise the Makefile wiring (not just `main()` directly) without polluting the real corpus. This
  mirrors the already-established `codebase-health-impact: ... $(ARGS)` precedent in the same file
  (`Makefile:290-291`) rather than inventing a new convention. Target names, comment text, and
  `.PHONY` entries are otherwise exactly as specified.
