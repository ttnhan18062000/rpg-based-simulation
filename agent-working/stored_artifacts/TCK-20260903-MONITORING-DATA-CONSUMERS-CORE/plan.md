---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CONSUMERS-CORE
artifact_type: plan
tags: [agent-monitoring, observability, data-quality]
---

# Implementation Plan — TCK-20260903-MONITORING-DATA-CONSUMERS-CORE

## Summary

Migrate all 9 in-scope `tools/agent-monitoring/` reader scripts off the dead monolithic/
flat-shard paths (`agent-monitoring/{runs,events,tools}.jsonl`, `agent-monitoring/tools/
tools-*.jsonl`) onto the unified per-week `agent-monitoring/data/<ISO-week>/{runs,events,
tools}.jsonl` layout child 1/2 already established, and fix the two live silent-zero bugs
(`weight_sensitivity_check.py`'s `TOOLS_FILE`, `retro_nudge_hook.py`'s `RUNS_FILE`) along the
way. Ratifies investigation's **Option B**: `load_jsonl(path)` keeps its existing "read exactly
one literal file, `[]` if missing" contract (its old `is_dir(): glob "tools-*.jsonl"` branch is
deleted, not repointed), and a new sibling function, `load_data_glob(data_dir, source)`, added to
`validate.py`, does the multi-week glob (`sorted(data_dir.glob(f"*/{source}.jsonl"))`, concat via
`load_jsonl`). Because every one of `RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_TOOLS_FILE`/
`DEFAULT_RUNS_FILE` etc. must default to the **same** `agent-monitoring/data` root (there is no
longer a directory shape that implies "this one is the runs root") while ~15+ currently-green
tests keep monkeypatching those same constants to a **literal single tmp file**, every call site
that reads one of these constants goes through a small dispatcher — `_load_source(path, source)`
(`build_index.py` gets its own private copy; `generate_retro.py` gets its own private copy,
mirroring the two files' existing independent-`load_jsonl`-copy convention) — that checks
`path.is_dir()` and routes to `load_data_glob(path, source)` (production default) or
`load_jsonl(path)` (literal-file test injection) accordingly, with `source` ("runs"/"events"/
"tools") always resolved statically per call site, never inferred from the directory's own
contents. `weight_sensitivity_check.py` and `retro_nudge_hook.py` import `load_data_glob` from
`validate.py` directly rather than hand-rolling a fourth/fifth glob implementation (ratifying
investigation's Risk #3 recommendation (b)). This same restructuring is why two call sites
investigation described as "zero code change" in fact need a one-line change under Option B —
flagged explicitly in Step 3 below, corrected from investigation's assumption. 16 test-touching
items are covered: 9 real RED tests fixed, 7 currently-green tests rewritten to the new
week-subdirectory shape, plus one brand-new test file (`test_retro_nudge_hook.py`) and one new
`test_build_index.py` class for the AC2-mandated 2+-week-folder integration test.

## Steps

### Step 1 — `validate.py`: simplify `load_jsonl`, add `load_data_glob`
**Files:** `tools/agent-monitoring/validate.py`
**Change:** Read and confirmed at `validate.py:223-240` (current `load_jsonl`). Delete the
`if path.is_dir(): ... glob("tools-*.jsonl") ...` branch (lines 224-228) — `load_jsonl(path)`
becomes: if not `path.exists()`, return `[]`; else read/parse line-by-line exactly as today
(unchanged body otherwise). Add a new function immediately after it:
```python
def load_data_glob(data_dir: Path, source: str) -> list:
    """Concatenate source.jsonl from every ISO-week folder under data_dir, sorted by week-folder
    name for determinism (matches record_events.py's write-side glob shape,
    tools/agent-monitoring/record_events.py:65)."""
    records = []
    for shard in sorted(data_dir.glob(f"*/{source}.jsonl")):
        records.extend(load_jsonl(shard))
    return records
```
**Do NOT touch:** `main()` (lines 251-330, confirmed reads exclusively via `open_index()`/
`load_*_from_index()` — zero JSONL file reads), `compute_drift_report()`/
`compute_tool_count_drift_report()`/`compute_multi_invocation_collision_report()` (lines 88-220,
pure functions), `_record_is_complete()`, `LEGACY_COMPLETION_FIELDS`/
`LEGACY_TERMINAL_STATUS_VALUES`.
**Verify:** `tests/tools/test_validate_agent_monitoring.py` (full suite, must stay green — confirmed
by direct read this session it has zero real-corpus JSONL dependency); new
`test_validate_drift_reports_identical_pre_and_post_migration_fixed_window` (test_plan item 10).

### Step 2 — `build_index.py`: repoint defaults, add `_load_source` dispatcher, update `build()`
**Files:** `tools/agent-monitoring/build_index.py`
**Change:** Confirmed at `build_index.py:33-38` (import block), `:42-44` (`DEFAULT_*` constants),
`:169-194` (`build()`). Add `load_data_glob` to the existing `from validate import (...)` block
(line 33-38). Change all 3 constants to the same directory:
```python
DEFAULT_RUNS_FILE = Path("agent-monitoring/data")
DEFAULT_EVENTS_FILE = Path("agent-monitoring/data")
DEFAULT_TOOLS_FILE = Path("agent-monitoring/data")
```
Add a private dispatcher (placed above `build()`):
```python
def _load_source(path: Path, source: str) -> list:
    """path is either the agent-monitoring/data root (production default, a directory) or a
    literal single JSONL file (explicit --runs-file/--events-file/--tools-file override, or a
    test's SimpleNamespace injection) — dispatch accordingly. `source` ("runs"/"events"/"tools")
    is resolved statically by the caller, never inferred from the directory's own contents."""
    if path.is_dir():
        return load_data_glob(path, source)
    return load_jsonl(path)
```
In `build()` (lines 175-177), replace:
```python
runs = load_jsonl(runs_path)
events = load_jsonl(events_path)
tools = load_jsonl(tools_path)
```
with:
```python
runs = _load_source(runs_path, "runs")
events = _load_source(events_path, "events")
tools = _load_source(tools_path, "tools")
```
No change to `--runs-file`/`--events-file`/`--tools-file`/`--db-path` CLI arg wiring (lines
201-204) — only their default *values* changed via the constants above. CONFIRMED by direct read
of `tests/tools/test_build_index.py:115-119` (`_args()` helper) that every existing test calls
`build()` with an explicit `SimpleNamespace(runs_file=..., events_file=..., tools_file=...)` — no
test relies on argparse's own default resolution — so `TestBuildHappyPath`/
`TestReadOnlyGuarantee`/`TestNormalizationParity`/`TestLegacyShapeGuards` (all pass literal single
tmp files) hit `_load_source`'s `is_dir()`-False branch unchanged.
**Do NOT touch:** `_create_schema()`, `_ingest_runs()`/`_ingest_events()`/`_ingest_tools()` (lines
99-166, off-schema-record skip logic — explicitly out of scope per ticket), `main()`'s argparse
wiring beyond the default values, the `--db-path` handling.
**Verify:** `test_build_index_never_touches_write_path_modules` (must keep passing — `_load_source`
is stdlib-`Path.glob()`-only); `TestBuildHappyPath`/`TestReadOnlyGuarantee`/
`TestNormalizationParity`/`TestLegacyShapeGuards` (must stay green unmodified).

### Step 3 — `generate_retro.py`: repoint constants, simplify local `load_jsonl`, add local dispatcher, fix 3 real call sites
**Files:** `tools/agent-monitoring/generate_retro.py`
**Change:** Confirmed at `generate_retro.py:53-72` (constants + local `load_jsonl` copy),
`:75-83` (`_source_mtime`), `:86-98` (`_index_is_stale`), `:101-137` (`_load_runs_and_events`),
main() at the `all_tools = load_jsonl(DEFAULT_TOOLS_FILE)` line (confirmed present, ~line 2269 in
the current file — citation-drift from the ticket's/investigation's "~2255"/"2272" both
superseded by this direct read; re-grep at implementation time since line numbers shift as edits
land).

1. Add `from validate import load_data_glob` to the existing `sys.path.insert(...)` +
   `from vocabulary import ...` import block (near line 33-34).
2. Repoint constants (lines 53, 57 — `EVENTS_FILE` stays at line 54):
   ```python
   RUNS_FILE = Path("agent-monitoring/data")
   EVENTS_FILE = Path("agent-monitoring/data")
   DEFAULT_TOOLS_FILE = Path("agent-monitoring/data")
   ```
3. Simplify the local `load_jsonl` (lines 64-72): delete the `is_dir(): glob("tools-*.jsonl")`
   branch (lines 65-68), keep the rest unchanged (file-exists check + line-by-line parse) —
   mirrors Step 1's change to `validate.py`'s copy exactly, kept as a separate local definition
   (not imported from `validate.py`) to match this file's existing independent-copy convention
   and avoid a broader consolidation the ticket's scope does not ask for.
4. Add a local dispatcher immediately after `load_jsonl`:
   ```python
   def _load_source(path, source):
       if path.is_dir():
           return load_data_glob(path, source)
       return load_jsonl(path)
   ```
5. Rewrite `_source_mtime(source)` (lines 75-83) to take a source name too, since the old
   `.is_dir()`-alone check can no longer distinguish "this is the tools root" from "this is the
   runs root" (all 3 constants now resolve to the identical directory):
   ```python
   def _source_mtime(path, source_name):
       """Newest relevant mtime for one source: max mtime across
       agent-monitoring/data/*/<source_name>.jsonl if path is the data-dir root (a directory),
       else the literal file's own mtime if it exists, else None."""
       if path.is_dir():
           mtimes = [f.stat().st_mtime for f in path.glob(f"*/{source_name}.jsonl")]
           return max(mtimes) if mtimes else None
       if path.exists():
           return path.stat().st_mtime
       return None
   ```
   CONFIRMED by grep this session: no test calls `_source_mtime` directly (it is only exercised
   indirectly via `_index_is_stale()`), so this signature change breaks no pinned-signature test.
6. Update `_index_is_stale()`'s loop (lines 92-96) from
   `for source in (RUNS_FILE, EVENTS_FILE, DEFAULT_TOOLS_FILE): mtime = _source_mtime(source)` to:
   ```python
   for path, source_name in ((RUNS_FILE, "runs"), (EVENTS_FILE, "events"), (DEFAULT_TOOLS_FILE, "tools")):
       mtime = _source_mtime(path, source_name)
       if mtime is not None and mtime > db_mtime:
           return True
   ```
7. **`_load_runs_and_events()`'s fallback branch (line ~135, confirmed
   `return load_jsonl(RUNS_FILE), load_jsonl(EVENTS_FILE)`) — CORRECTION to investigation's own
   assumption, not a "zero-change" call site**: under Option B, `RUNS_FILE`/`EVENTS_FILE` now
   default to a *directory*; calling the simplified `load_jsonl` directly on a directory would hit
   `path.exists()` → `True` → `path.read_text()` → `IsADirectoryError` (directories do not support
   `read_text()`). This line must change to
   `return _load_source(RUNS_FILE, "runs"), _load_source(EVENTS_FILE, "events")`. The primary
   (SQLite-index) branch above it (`build_index.build(SimpleNamespace(runs_file=str(RUNS_FILE),
   events_file=str(EVENTS_FILE), tools_file=str(DEFAULT_TOOLS_FILE), db_path=str(DEFAULT_DB_PATH)))`)
   needs **no change** — it already just stringifies the constants; `build_index.build()`'s own
   `_load_source` (Step 2) handles the dir-vs-file dispatch on the receiving end.
8. **`main()`'s `all_tools = load_jsonl(DEFAULT_TOOLS_FILE)` — second correction to
   investigation's "zero code change at this call site" claim**, for the identical reason as #7:
   with `DEFAULT_TOOLS_FILE` now a directory by default, plain `load_jsonl(DEFAULT_TOOLS_FILE)`
   would crash the same way. Change to `all_tools = _load_source(DEFAULT_TOOLS_FILE, "tools")`.
   Verified this does not violate `test_main_loads_via_index_not_direct_jsonl_scan`'s guard
   (`assert "load_jsonl(RUNS_FILE)" not in source; assert "load_jsonl(EVENTS_FILE)" not in
   source; assert "_load_runs_and_events" in source` — confirmed at
   `tests/tools/test_generate_retro.py:1102-1105` — this guard never references
   `DEFAULT_TOOLS_FILE` or checks `main()`'s tools-loading line at all).
**Do NOT touch:** `_update_index()` (must still contain no `load_jsonl(RUNS_FILE)` per
`tests/tools/test_generate_retro.py:1120` guard — untouched by this plan), any
`compute_*_metrics`/`compute_tool_safety_metrics`/`build_skill_usage_section` pure function (all
have their own `"EVENTS_FILE"/"RUNS_FILE"/"DEFAULT_TOOLS_FILE"/"load_jsonl" not in source` guards
per `tests/tools/test_generate_retro.py:1794-1795, 2027-2029, 2362-2364` — none of these functions
are touched by this step), `generate()`, `_resolve_status()`, `_is_legacy_event()`,
`_is_gate_fail()`, the retrieval/outlier/skill-usage sections.
**Other readers of `generate_retro.py`'s constants (enumerated per Fact-Verification requirement
#2 — every other consumer of `RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_TOOLS_FILE`/`load_jsonl`, since
this step changes what those names resolve to for everyone who imports them):**
- `build_index.py:39` imports only `_resolve_status` from `generate_retro.py` — unaffected.
- `done_ticket_monitoring_coverage.py:22` imports `RUNS_FILE, load_jsonl` directly — see Step 7,
  this is the "inherits the fix for free" call site; `load_jsonl(RUNS_FILE)` there will crash
  under the new directory-valued `RUNS_FILE` exactly like `main()`'s old call did, so Step 7 is
  NOT actually a zero-code-change step either — see Step 7 for the correction.
- `skill_usage_metric.py:24` imports `DEFAULT_TOOLS_FILE, build_skill_usage_section, load_jsonl`
  and calls `load_jsonl(DEFAULT_TOOLS_FILE)` in its own `main()` (per
  `generate_retro.py:439-445`'s comment, confirmed by investigation) — same crash risk. Out of
  this ticket's Related Code Areas (see Anti-Drift Notes) — flagged, not fixed here.
- `retrieval_baseline_metrics.py:28` and `security_gate_firing_check.py:18` both import a block
  from `generate_retro.py` (confirmed by direct read this session) built around
  `_load_runs_and_events`/other composed functions, not `load_jsonl`/`DEFAULT_TOOLS_FILE`
  directly (grep confirmed no `load_jsonl(` or `DEFAULT_TOOLS_FILE` reference in either file) —
  they inherit Step 3's `_load_runs_and_events()` fix for free with zero crash risk, same
  no-code-change category as `done_ticket_monitoring_coverage.py`'s non-tools-reading behavior.
  Not in this ticket's Related Code Areas; flagged in Anti-Drift Notes as unverified this session,
  same treatment as `skill_usage_metric.py`.
**Verify:** `test_generate_retro_builds_index_on_demand_when_missing`,
`test_generate_retro_rebuilds_stale_index_not_just_missing_index`,
`test_index_is_stale_false_when_index_newer_than_all_sources` (all 3 monkeypatch `RUNS_FILE`/
`EVENTS_FILE`/`DEFAULT_TOOLS_FILE` to literal single tmp files — must stay green via the
dispatcher's `is_dir()`-False branch); `test_main_loads_via_index_not_direct_jsonl_scan`;
`test_update_index_signature_change_is_deliberate_and_documented`;
`test_correlation_real_corpus_produces_a_real_number`;
`test_parity_index_readpath_call_count_matches_real_corpus_state` (both RED, both call
`generate_retro.load_jsonl(generate_retro.EVENTS_FILE)`/`load_jsonl(generate_retro.
DEFAULT_TOOLS_FILE)` directly against the real corpus per investigation — re-check at
implementation time whether these two call sites in the *test file itself* also need updating to
call `_load_source`/`load_data_glob` instead of the now-crash-prone bare `load_jsonl` against a
directory-valued constant; if so, that is a legitimate test-fixture-shape update, not a
production-code change).

### Step 4 — `manifest.py`: fix all 3 branches of `build_manifest()` and `capture_lines()`
**Files:** `tools/agent-monitoring/manifest.py`
**Change:** Confirmed at `manifest.py:23-27` (`_FILES_BY_SOURCE`), `:48-59` (`_scan_file`), `:62-76`
(`_scan_tools_shards`), `:79-86` (`build_manifest`), `:89-113` (`capture_lines`). Replace
`_scan_tools_shards(tools_dir, source)` with a source-generic
`_scan_data_dir_glob(data_dir: Path, source: str) -> dict` that globs `data_dir.glob(f"*/{source}.jsonl")`
instead of `tools_dir.glob("tools-*.jsonl")`, sorted, streaming each shard through the existing
`_stream_file_into()` helper unchanged (keeps `line_count`/`byte_size`/`sha256`/`parser_result`/
`legacy_warning_count` accumulation logic identical — only the glob target and per-record `file`
key change: return `{"file": f"{source}.jsonl", ...}` instead of the hardcoded `"tools.jsonl"`).
Rewrite `build_manifest(agent_monitoring_dir)` (lines 79-86) so **all 3** sources go through the
new glob-based scan against `agent_monitoring_dir / "data"`, not just `tools`:
```python
def build_manifest(agent_monitoring_dir: Path) -> list:
    data_dir = agent_monitoring_dir / "data"
    records = []
    for filename, source in sorted(_FILES_BY_SOURCE.items()):
        records.append(_scan_data_dir_glob(data_dir, source))
    return records
```
Rewrite `capture_lines()` (lines 89-113) the same way — for every `filename` in
`_FILES_BY_SOURCE`, glob `agent_monitoring_dir / "data"` for `*/<source>.jsonl` (sorted), open
each shard in text mode, append lines in order — replacing both the old flat-`tools`-only special
case and the plain-`runs`/`events` unconditional-`open()` branch with one unified streaming loop.
**Do NOT touch:** `assert_prefix_preserved()`, `_stream_file_into()`'s own per-line
parse/hash/classify logic, the `capture_lines()`/`assert_prefix_preserved()` pairing contract,
`_assert_safe_output_path` (imported by `done_ticket_monitoring_coverage.py`).
**Verify:** `test_build_manifest_shape_against_real_corpus` (must still assert exactly 3 records,
`{"events.jsonl", "runs.jsonl", "tools.jsonl"}` — one logical record per source aggregated across
all week folders, never one record per week file — this is the single most likely scope-creep
failure mode per investigation's Anti-Drift Hazards), `test_manifest_cli_reproducible_byte_
identical_across_two_runs`, `test_build_manifest_reproducible_byte_identical_direct_call`,
`test_manifest_run_against_real_corpus_produces_zero_diff` (all 4 RED → GREEN);
`test_manifest_source_never_calls_full_file_read_methods` (AST guard, must stay green — no
`read_text`/`read_bytes`/`readlines`/`read` anywhere).

### Step 5 — Rewrite `test_agent_monitoring_manifest.py`'s 2 flat-shard-shape tests
**Files:** `tests/tools/test_agent_monitoring_manifest.py`
**Change:** `test_manifest_tools_source_aggregates_all_shards` (currently writes
`tmp_path/"tools"/"tools-2026-W01.jsonl"` etc.) and `test_manifest_tools_source_sha256_is_order_
stable_across_shards` (same old shape) must be rewritten to construct
`tmp_path/"data"/"2026-W01"/"tools.jsonl"` + `tmp_path/"data"/"2026-W02"/"tools.jsonl"` (matching
Step 4's `agent_monitoring_dir / "data"` glob target), call `build_manifest(tmp_path)`, and assert
the aggregated `tools.jsonl` record's `line_count`/`sha256`/order reflects both weeks concatenated
in sorted-week order — same assertions as before, new fixture shape only.
**Do NOT touch:** the other tests in this file already covered by Step 4's verify list.
**Verify:** both tests pass against the new fixture shape; `test_manifest_source_never_calls_full_
file_read_methods` still passes (unaffected).

### Step 6 — New `test_agent_monitoring_manifest.py` (or `test_build_index.py`-style) multi-source glob test
**Files:** `tests/tools/test_agent_monitoring_manifest.py`
**Change:** Add `test_manifest_aggregates_all_3_sources_across_all_week_folders` (test_plan item
9): construct `tmp_path/"data"/"2026-W01"/{runs,events,tools}.jsonl` and
`tmp_path/"data"/"2026-W02"/{runs,events,tools}.jsonl`, call `build_manifest(tmp_path)`, assert
exactly 3 records returned with the exact filename set `{"events.jsonl", "runs.jsonl",
"tools.jsonl"}`, each aggregating both weeks (nonzero `line_count` summing both weeks' lines, not
just one).
**Do NOT touch:** manifest.py itself in this step (already fixed in Step 4).
**Verify:** the new test itself, plus re-confirms Step 4's "never one record per week folder"
invariant from a `runs`/`events` angle, not just `tools`.

### Step 7 — `tests/tools/test_agent_monitoring_legacy_reader.py`: fix `_recent_records()` real-corpus path
**Files:** `tests/tools/test_agent_monitoring_legacy_reader.py`
**Change:** Per investigation, `_recent_records()` (test-only helper, ~lines 200-243) does
`path.read_text().splitlines()` directly against `_REAL_AGENT_MONITORING_DIR / "runs.jsonl"` /
`"events.jsonl"` — both dead paths post child-2-migration. Confirm the exact helper body at
implementation time (not directly read this planning session — flagged as an open verification
item, see Unresolved Questions) and repoint it to read the union of
`agent-monitoring/data/*/{runs,events}.jsonl`, sorted, consistent with every other rewritten
glob in this plan. `legacy_reader.py` itself (`classify_provenance()`) needs zero change — pure
classifier, no file I/O (confirmed by investigation's direct read).
**Do NOT touch:** `tools/agent-monitoring/legacy_reader.py` production code.
**Verify:** `test_recent_runs_records_classify_as_current_and_agree_with_validate`,
`test_recent_events_records_remain_parseable` (both RED → GREEN).

### Step 8 — `seq_offset.py`: repoint `EVENTS_FILE`, glob at the `__main__` call site
**Files:** `tools/agent-monitoring/seq_offset.py`
**Change:** Confirmed at `seq_offset.py:25` (`from validate import load_jsonl`), `:27`
(`EVENTS_FILE = Path("agent-monitoring/events.jsonl")`), `:43-44` (`__main__`:
`compute_seq_offset(sys.argv[1], load_jsonl(EVENTS_FILE))`). Change the import to
`from validate import load_data_glob`, change `EVENTS_FILE = Path("agent-monitoring/data")`, and
change the `__main__` call to `compute_seq_offset(sys.argv[1], load_data_glob(EVENTS_FILE,
"events"))`. `compute_seq_offset(run_id, events)` itself (lines 30-40) needs zero change — pure
function taking an already-loaded list, confirmed by direct read.
**Do NOT touch:** `compute_seq_offset()`'s body.
**Verify:** `tests/tools/test_seq_offset.py` (4 existing pure-function tests, must stay green —
zero `EVENTS_FILE` reference, confirmed by direct read); new
`test_seq_offset_reads_events_across_multiple_week_folders` (test_plan item 5) — seed
`agent-monitoring/data/<week1>/events.jsonl` and `.../<week2>/events.jsonl` for the same `run_id`
with different `seq` values, invoke the `__main__` entrypoint (subprocess, matching
`scope_ticket_relocate.py`'s existing `MARKER:`-prefixed-JSON pattern this file mirrors), assert
the returned offset reflects the max `seq` across both weeks.

### Step 9 — `weight_sensitivity_check.py`: fix the named critical bug (`TOOLS_FILE`/`EVENTS_FILE`)
**Files:** `tools/agent-monitoring/weight_sensitivity_check.py`
**Change:** Confirmed at `weight_sensitivity_check.py:29-30` (`TOOLS_FILE`/`EVENTS_FILE`
constants), `:137-167` (`_load_tool_rows_and_events(tools_path, events_path)` — a third,
independent hand-rolled single-file-read implementation, not calling either `load_jsonl` copy),
`:221` (`main()`'s call site: `_load_tool_rows_and_events(TOOLS_FILE, EVENTS_FILE)`). Ratifying
investigation's Risk #3 recommendation (b): rather than hand-roll a fourth glob implementation,
add `from validate import load_data_glob` to the import block (near line 24, alongside the
existing `from cost_proxy import W_AGENT, W_BASH, W_EDIT`), change
`TOOLS_FILE = Path("agent-monitoring/data")` and `EVENTS_FILE = Path("agent-monitoring/data")`,
and rewrite `_load_tool_rows_and_events(tools_path, events_path)`'s two file-reading blocks (lines
~139-146 for tools, ~150-163 for events) to iterate over `load_data_glob(tools_path, "tools")` /
`load_data_glob(events_path, "events")` respectively instead of their own `if
tools_path.exists(): with open(tools_path, ...)` / `if events_path.exists(): with
open(events_path, ...)` blocks — the per-record filtering/grouping logic inside each loop
(`(run_id, seq)` key construction, `phase_of`/`agent_of` dict population) stays exactly as-is,
only the source of the record stream changes from a manual file-open loop to
`load_data_glob()`'s returned list.
**Do NOT touch:** `compute_weight_sensitivity_report()` (lines 96-134),
`_score_with_weights()`, `_spearman_rank_correlation()`, `_group_report()`, `SHIPPED_WEIGHTS`,
`--candidate-weights`/`--baseline-weights` CLI contract (`main()`'s weight-parsing block) — all
pure/unaffected per investigation's direct read and per `INFRA-285`'s parity ledger entry (checked,
not affected — never quotes a literal `TOOLS_FILE`/`EVENTS_FILE` path value).
**Verify:** `tests/tools/test_weight_sensitivity_check.py` (10 existing pure-function tests, must
stay green — zero `TOOLS_FILE`/`EVENTS_FILE` reference, confirmed by direct read); new
`test_weight_sensitivity_check_real_multi_week_tools_and_events_produce_nonzero_score`
(test_plan item 4, **highest-priority regression test in this ticket**) — seed real
`agent-monitoring/data/<week1>/{tools,events}.jsonl` + `.../<week2>/{tools,events}.jsonl` (2+
distinct weeks, cross-week case required, mirroring child 1's own `record_events.py` regression
test — a same-week-only variant must NOT be substituted), invoke `main()`'s real CLI path (not
`compute_weight_sensitivity_report()` directly — must exercise
`_load_tool_rows_and_events()`'s real file-reading logic), assert `n_groups_scored > 0` and at
least one bucket's `baseline_mean`/`candidate_mean` is nonzero.

### Step 10 — `retro_nudge_hook.py`: fix the second silent-zero critical bug (`RUNS_FILE`)
**Files:** `tools/agent-monitoring/retro_nudge_hook.py`
**Change:** Confirmed at `retro_nudge_hook.py:18` (`RUNS_FILE = Path("agent-monitoring/
runs.jsonl")`), `:38-61` (`_count_done_since(cutoff)` — third independent hand-rolled
single-file-read implementation: `if not RUNS_FILE.exists(): return 0; for line in
RUNS_FILE.read_text().splitlines(): ...`). Add an import (near the top, before the `THRESHOLD`
constant): `sys.path.insert(0, str(Path(__file__).resolve().parent))` then `from validate import
load_data_glob` (this file currently has no `sys.path.insert` — none of its existing imports are
local-module imports; add both lines). Change `RUNS_FILE = Path("agent-monitoring/data")`.
Rewrite `_count_done_since(cutoff)`'s body: replace the `if not RUNS_FILE.exists(): return 0` +
manual `RUNS_FILE.read_text().splitlines()` loop with `for record in
load_data_glob(RUNS_FILE, "runs"):` (an empty/missing `agent-monitoring/data` directory or a
missing `runs.jsonl` inside a given week folder both already resolve to `load_data_glob` safely
returning `[]`/skipping, matching the old function's `if not RUNS_FILE.exists(): return 0`
short-circuit's intent) — the per-record filtering logic below it (`workflow`/`status`/`start_ts`
extraction, `ts > cutoff` comparison) stays exactly as-is. **The entire fix must stay inside the
existing outer `try/except Exception: pass` (lines 64-93)** — this hook's fail-silent contract
(never raises, never blocks the tool call) is unconditional; a malformed `runs.jsonl` line inside
any week folder must degrade the same way a malformed line degrades today (per-line
`json.loads` already wrapped in its own local `try/except Exception: continue` inside
`_count_done_since`, unaffected by this change) — do not let a directory-listing error
(`PermissionError`, `agent-monitoring/data` entirely absent) escape past the module-level guard
either; `Path.glob()` on a nonexistent directory returns an empty iterator rather than raising, so
no additional guard is needed for that specific case, but confirm this at implementation time
since `load_data_glob`'s `data_dir.glob(...)` call is the first thing that would surface a
permissions error.
**Do NOT touch:** the once-per-session gating logic (`_load_state`/`STATE_FILE`/`session_id`/
`COOLDOWN_S`), `_last_dated_retro_mtime()`, the `THRESHOLD`/hook-output JSON shape.
**Verify:** new file `tests/tools/test_retro_nudge_hook.py` (test_plan items 6-7, **no existing
test file for this script at all** — confirmed by grep, genuine new coverage, not a
regression-test rewrite):
- `test_retro_nudge_hook_counts_done_runs_across_multiple_week_folders` — seed
  `agent-monitoring/data/<week1>/runs.jsonl` and `.../<week2>/runs.jsonl` each with a DONE
  `implement-ticket` run past the retro cutoff, assert `_count_done_since(cutoff)` counts records
  from both weeks (must be a cross-week test, same anti-drift class as Step 9's regression test —
  a same-week-only fix could pass a weaker version of this test while remaining broken).
- `test_retro_nudge_hook_fail_silent_on_malformed_data_dir` — malformed JSON in a week-folder
  `runs.jsonl` line, and `agent-monitoring/data/` entirely absent, both must not raise out of the
  hook's outer `try/except Exception: pass` (invoke the module's `__main__`-level script body via
  subprocess with a crafted stdin payload, matching how `post_tool_hook.py`'s equivalent tests
  from child 1's plan invoke that hook, per investigation's citation).

### Step 11 — `done_ticket_monitoring_coverage.py`: no production code change, add regression test
**Files:** `tests/tools/test_done_ticket_monitoring_coverage.py` (test-only — no change to
`tools/agent-monitoring/done_ticket_monitoring_coverage.py` itself)
**Change:** Confirmed at `done_ticket_monitoring_coverage.py:22`
(`from generate_retro import RUNS_FILE, load_jsonl`) and `:71` (`build_coverage_section()`'s only
read call site: `runs = load_jsonl(RUNS_FILE)`). This is genuinely a real bug today under Step
3's Option B fix if left completely untouched at the call level: `RUNS_FILE` now resolves to a
directory, and bare `load_jsonl(RUNS_FILE)` would `IsADirectoryError` exactly like `main()`'s old
call did (Step 3, correction #7/#8) — **this is NOT actually a zero-code-change file**, contrary
to investigation's stated conclusion; it needs the same one-line fix as `main()`'s old call site.
Change the import at line 22 to `from generate_retro import RUNS_FILE, load_data_glob` (or import
`_load_source` from `generate_retro.py` if that name is kept private — prefer importing
`load_data_glob` directly from `validate.py` instead, to avoid depending on `generate_retro.py`'s
private dispatcher: `from validate import load_data_glob` alongside the existing `from
generate_retro import RUNS_FILE`), and change line 71 to `runs = load_data_glob(RUNS_FILE,
"runs")`. This preserves the documented design rationale at lines 62-70 exactly (direct-read
bypass of the SQLite index for freshness) — only what `RUNS_FILE` resolves to and how it's read
changes.
**Do NOT touch:** `_collect_done_ticket_ids()`, `_assert_safe_output_path` import, the
docstring/comment block explaining the freshness rationale (still accurate, no wording change
needed).
**Verify:** `test_live_corpus_does_not_false_positive_this_sessions_own_recent_tickets` (RED →
GREEN); new `test_done_ticket_monitoring_coverage_reads_runs_across_multiple_week_folders`
(test_plan item 8, optional-but-recommended, included here since Step 11 turns out to require a
real code change contrary to investigation's assumption) — seed 2 week folders' `runs.jsonl` with
different `run_id`s matching 2 different `tickets/done/`-style ticket IDs, assert
`build_coverage_section()` reports both as covered.

### Step 12 — `build_index.py`: new 2+-week-folder integration test class
**Files:** `tests/tools/test_build_index.py`
**Change:** Rewrite `TestShardedToolsSource`'s 3 tests (`test_build_index_reads_multiple_shard_
files_from_directory`, `test_build_index_includes_unknown_week_shard`,
`test_build_index_glob_result_is_sorted`) to construct `tmp_path/"2026-W01"/{runs,events,
tools}.jsonl`, `tmp_path/"2026-W02"/{runs,events,tools}.jsonl`, and (for the unknown-week test)
`tmp_path/"unknown-week"/{runs,events,tools}.jsonl`, call `_bi.build(SimpleNamespace(runs_file=
str(tmp_path), events_file=str(tmp_path), tools_file=str(tmp_path), db_path=str(db_path)))`
(passing the same `tmp_path` root for all 3 args — `_load_source`'s `source` parameter, resolved
per-arg inside `build()`, is what differentiates them), and assert records from every week folder
appear in the corresponding SQLite table. Add a new class `TestUnifiedDataDirSource` (or extend
the rewritten `TestShardedToolsSource` — implementer's choice, whichever reads more clearly) with
`test_build_index_2plus_week_folders_all_included` (test_plan item 2, AC2's own literal text): 2+
week folders, distinct `run_id`s per week, assert all records from both weeks appear in **all 3**
tables (`runs`/`events`/`tools`), not just `tools` as the old class covered.
**Do NOT touch:** `TestBuildHappyPath`/`TestReadOnlyGuarantee`/`TestNormalizationParity`/
`TestLegacyShapeGuards`/`TestRerunStability`/`TestMakeTarget`/`TestGitignore`/
`TestArchitectureGuards` — all use literal single tmp files via `_args()`, unaffected by this
step.
**Verify:** the rewritten `TestShardedToolsSource` tests plus the new
`test_build_index_2plus_week_folders_all_included`, run against real
`python3 tools/agent-monitoring/build_index.py` too (AC1's literal wording: row counts equal
totals across all weeks, for all 3 tables) as a manual/CI sanity check, not just the unit test.

### Step 13 — `generate_retro.py` test file: rewrite 2 flat-shard-shape tests, add cross-week staleness test
**Files:** `tests/tools/test_generate_retro.py`
**Change:**
1. `test_generate_retro_load_jsonl_globs_shard_directory` (currently asserts
   `generate_retro.load_jsonl(tools_dir)` itself globs `tools-*.jsonl`) — under Option B,
   `load_jsonl` no longer supports dir-mode at all, so this test's core assertion is now false by
   design. Rewrite it to test the new split responsibility instead:
   `generate_retro.load_data_glob` is not a local name (it's imported from `validate.py`), so
   assert `generate_retro._load_source(data_dir, "tools")` (constructed as
   `tmp_path/"2026-W01"/"tools.jsonl"` + `tmp_path/"2026-W02"/"tools.jsonl"`) returns the
   concatenated, sorted-by-week result, AND separately assert `generate_retro.load_jsonl(single_
   file)` / `generate_retro.load_jsonl(missing_file)` still behave as pure single-file reads
   (`[]` on missing) — preserving the "dual-mode... unaffected" literal-file half of the old
   test's intent, now split across two named behaviors instead of one overloaded function.
2. `test_generate_retro_index_is_stale_detects_write_to_non_newest_shard` — rewrite from the old
   `tmp_path/"tools"/"tools-2026-W01.jsonl"` + `"tools-2026-W05.jsonl"` flat-shard fixture to
   `tmp_path/"2026-W01"/"tools.jsonl"` + `tmp_path/"2026-W05"/"tools.jsonl"`, with `RUNS_FILE`/
   `EVENTS_FILE` monkeypatched to their own literal `tmp_path/"runs.jsonl"`/`"events.jsonl"` files
   (unchanged from the old test) and `DEFAULT_TOOLS_FILE` monkeypatched to `tmp_path` itself (the
   data-dir root, not a `"tools"` subdirectory) — same "write to the older, non-newest-by-name
   week folder must still register as stale" assertion, new directory shape.
3. Add `test_generate_retro_index_is_stale_detects_append_in_any_week_folder_any_source`
   (test_plan item 3, directly implements AC3's literal wording: "a newly appended row in ANY
   week folder's ANY of the 3 files" — a strictly broader assertion than #2 above, which only
   covers the `tools` source): monkeypatch `RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_TOOLS_FILE` all to
   the same `tmp_path` data-dir root containing 2+ week folders, build the index, append one line
   to `runs.jsonl` in the OLDER week folder, assert stale; rebuild; append one line to
   `events.jsonl` in the NEWER week folder, assert stale; rebuild; append to `tools.jsonl`, assert
   stale — covering all 3 sources, not just `tools`.
**Do NOT touch:** every other test in this 54-test file not named in this step or Step 3's Verify
list — re-run in full per test_plan's instruction, but no fixture changes expected for the
remaining tests.
**Verify:** the 2 rewritten tests plus the 1 new cross-source staleness test, all passing;
re-confirm the architecture guards at lines 1102-1105, 1120, 1794-1795, 2027-2029, 2362-2364 still
pass unmodified (Step 3's Do NOT touch list).

### Step 14 — Docs: `schema.md`, `README.md`
**Files:** `docs/agent-monitoring/schema.md`, `docs/agent-monitoring/README.md`
**Change:** `schema.md` lines 29-32 (confirmed by direct read this session): currently reads
"...(`runs.jsonl`/`events.jsonl` each compared by their own single mtime; the `tools` source
compares against the newest mtime across all `agent-monitoring/tools/tools-*.jsonl` shard files,
via `max()`...)". Reword to describe all 3 sources uniformly comparing against the newest mtime
across their respective `agent-monitoring/data/*/<source>.jsonl` week files (matching Step 3's
`_source_mtime(path, source_name)` design) — remove the now-inaccurate "each compared by their
own single mtime" framing for `runs`/`events` and the dead `agent-monitoring/tools/tools-*.jsonl`
path reference. `README.md` line 148 (confirmed by direct read): currently reads "Full field
reference for runs.jsonl, events.jsonl, and the tools/tools-YYYY-Www.jsonl shard family" — update
to describe the current `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` layout.
**Do NOT touch:** `README.md` line 54 (`retrieval_baseline_metrics.py` description — investigation
confirmed still-accurate, describes a script this ticket does not touch), `README.md` lines
128-129 (`done_ticket_monitoring_coverage.py`'s "reads directly, bypassing the index" description
— still conceptually accurate after Step 11's fix, only the underlying path resolution changed,
not the architectural claim), `schema.md`'s already-updated per-source write-path prose and
worked-join example (lines ~474-500, confirmed present/correct by investigation, written by
children 1/2 — this ticket's doc fix is narrower).
**Verify:** manual read-through; no automated doc test exists for this content per investigation.

### Step 15 — Parity ledger: `INFRA-291` third addendum
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** `INFRA-291` (confirmed at lines 6363-6510, `tools/agent-monitoring/
generate_retro.py:5803` area per investigation's citation) already carries 2 dated addenda
(2026-08-14 index-staleness fix, 2026-09-03 prior epic's shard-directory repoint). Its current
`v2_evidence` states `DEFAULT_TOOLS_FILE` was repointed to `Path("agent-monitoring/tools")` and
`load_jsonl()` globs `sorted(tools_dir.glob("tools-*.jsonl"))` — both now factually superseded.
Use `tools/parity_ledger_writer.py` (never a raw YAML edit) to append a **third**, separately
dated addendum describing: `RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_TOOLS_FILE` all now default to
`Path("agent-monitoring/data")`; `load_jsonl()` is now literal-single-file-only (dir-mode branch
removed); the new `load_data_glob(data_dir, source)` (added to `validate.py`, imported by
`generate_retro.py`) does `sorted(data_dir.glob(f"*/{source}.jsonl"))`; `_source_mtime()`/
`_index_is_stale()` now take an explicit source name per source rather than inferring it from
`path.is_dir()` alone. Do not rewrite either of the 2 earlier addenda — append only.
**Do NOT touch:** `INFRA-285` (`weight_sensitivity_check.py` — investigation confirmed its
`v2_evidence` never quotes a literal `TOOLS_FILE`/`EVENTS_FILE` path value, not stale),
`INFRA-288` (`seq_offset.py` — same reasoning), `INFRA-289`/`INFRA-290` (`query.py`/`validate.py`'s
original SQLite-index migrations — neither cites a literal path value this ticket changes). No
new parity ledger entry needed for `manifest.py`, `retro_nudge_hook.py`, or
`done_ticket_monitoring_coverage.py` — investigation confirmed (grep) none of these 3 has its own
dedicated entry in `infrastructure.yaml`.
**Verify:** `tools/parity_ledger_writer.py`'s own schema validation passes; visually confirm the 2
prior addenda are byte-unchanged.

## Scope Guards

- Do not touch `record_run.py`, `record_events.py`, `post_tool_hook.py`, `writer.py` — the write
  path is child 1's completed, separate work; this ticket is read-path only.
- Do not touch `tools/gate_checks/done_checker_static.py` or `src/api/agent_ops_dashboard/
  ingest.py` — child 4.
- Do not touch `tools/agent_replay_codex/monitoring_shards.py` or any codex subsystem file —
  child 5.
- Do not touch any referential-integrity verification tooling — child 6.
- Do not change `build_index.py`'s table schema (`_create_schema()`), or `_ingest_runs()`/
  `_ingest_events()`/`_ingest_tools()`'s off-schema-record skip logic, or `_resolve_status()`/
  `_is_legacy_event()`/`_is_gate_fail()` — only the file-resolution layer changes anywhere in this
  ticket.
- Do not widen any new glob beyond `*/<source>.jsonl` under `agent-monitoring/data/` — no `**`,
  no broader pattern. Do not special-case the real `unknown-week` folder out of any glob.
- Do not modify `compute_weight_sensitivity_report()`, `_score_with_weights()`,
  `_spearman_rank_correlation()`, `_group_report()`, `compute_seq_offset()`,
  `compute_drift_report()`, `compute_tool_count_drift_report()`,
  `compute_multi_invocation_collision_report()` — all pure functions, zero change anywhere in this
  plan.
- Do not modify `query.py` — confirmed zero reference to any legacy path or `load_jsonl` anywhere
  (grep-confirmed this session); its own architecture guard test
  (`tests/tools/test_query.py:394`) must keep passing unmodified with zero edits to `query.py`.
- Do not modify `tools/agent-monitoring/skill_usage_metric.py`,
  `tools/agent-monitoring/retrieval_baseline_metrics.py`, or
  `tools/agent-monitoring/security_gate_firing_check.py` — none are in this ticket's Related Code
  Areas; all 3 inherit Step 3's fix transitively (confirmed by direct read of their imports this
  session) but their own real-corpus tests are not part of this ticket's gate and must not be
  edited to "help" them pass.
- Do not consolidate `validate.py`'s and `generate_retro.py`'s two independent `load_jsonl` copies
  into one shared import — out of scope; each keeps its own local, now-simplified copy.
- Every new/rewritten glob call must be wrapped in `sorted(...)` — determinism requirement, tied
  to `test_manifest_cli_reproducible_byte_identical_across_two_runs`, `test_build_manifest_
  reproducible_byte_identical_direct_call`, and `test_build_index_glob_result_is_sorted`'s
  successor.

## Dependency Map

- Steps 1 and 2 are independent of each other but both must land before Step 12's tests can pass
  (`build_index.py` imports `load_jsonl`/`load_data_glob` from `validate.py`).
- Step 3 depends on Step 1 (`generate_retro.py` imports `load_data_glob` from `validate.py`).
- Step 13 depends on Step 3 (tests exercise the rewritten `generate_retro.py` functions).
- Step 4 is independent of Steps 1-3 (`manifest.py` does not import from `validate.py`/
  `generate_retro.py` for its glob logic — self-contained fix).
- Steps 5 and 6 depend on Step 4.
- Step 7 is independent (touches only the test file's own helper, not production code).
- Step 8 depends on Step 1 (`seq_offset.py` imports `load_data_glob` from `validate.py`).
- Step 9 depends on Step 1 (`weight_sensitivity_check.py` imports `load_data_glob` from
  `validate.py`).
- Step 10 depends on Step 1 (`retro_nudge_hook.py` imports `load_data_glob` from `validate.py`).
- Step 11 depends on Step 3 (imports `RUNS_FILE` from `generate_retro.py`) and Step 1 (imports
  `load_data_glob` from `validate.py`).
- Steps 14 and 15 (docs/ledger) should land last, once the final function/constant shapes from
  Steps 1-11 are settled, so the doc/ledger prose describes the actual landed design rather than
  an intermediate one.
- All other step pairs are independent and may be implemented/tested in any order.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `build_index.py` builds all 3 tables from all week folders, row counts equal totals | Steps 1, 2 | `test_build_index_2plus_week_folders_all_included` (Step 12), manual `make agent-monitoring-index` run |
| Test simulates 2+ week folders under a temp `agent-monitoring/data/`-shaped dir, all 3 sources | Step 12 | `test_build_index_2plus_week_folders_all_included` |
| `generate_retro.py`'s staleness check detects a newly appended row in ANY week folder's ANY of the 3 files | Steps 1, 3 | `test_generate_retro_index_is_stale_detects_append_in_any_week_folder_any_source` (Step 13) |
| Regression test proving `weight_sensitivity_check.py`'s bug is fixed (nonzero score, cross-week) | Step 9 | `test_weight_sensitivity_check_real_multi_week_tools_and_events_produce_nonzero_score` |
| `seq_offset.py`, `retro_nudge_hook.py`, `done_ticket_monitoring_coverage.py` each read the union of week folders | Steps 8, 10, 11 | `test_seq_offset_reads_events_across_multiple_week_folders`, `test_retro_nudge_hook_counts_done_runs_across_multiple_week_folders`, `test_done_ticket_monitoring_coverage_reads_runs_across_multiple_week_folders` |
| `query.py`'s existing test suite passes unmodified | (no step — confirmed no-op) | `tests/tools/test_query.py` full suite, incl. line-394 architecture guard |
| `validate.py`'s drift-report functions produce identical results pre/post migration, fixed window | Step 1 | `test_validate_drift_reports_identical_pre_and_post_migration_fixed_window` |
| (implicit, ticket's own Related Code Areas) 7 previously-deferred RED tests from child 2 pass | Steps 3, 4, 7, 11 | `test_agent_monitoring_manifest.py` (4), `test_done_ticket_monitoring_coverage.py` (1), `test_agent_monitoring_legacy_reader.py` (2) |
| (investigation-discovered, not in ticket text) 2 additional RED `test_generate_retro.py` tests | Step 3 | `test_correlation_real_corpus_produces_a_real_number`, `test_parity_index_readpath_call_count_matches_real_corpus_state` |

## Anti-Drift Notes

- **Ratification of investigation's decision #1 (Option B) — accepted as specified**, with the
  correction (Step 3, Step 11) that two call sites investigation described as "zero code change"
  (`generate_retro.py::main()`'s `load_jsonl(DEFAULT_TOOLS_FILE)`, `_load_runs_and_events()`'s
  fallback `load_jsonl(RUNS_FILE)`/`load_jsonl(EVENTS_FILE)`, and
  `done_ticket_monitoring_coverage.py`'s `load_jsonl(RUNS_FILE)`) in fact require a one-line
  change each under full Option B, because dropping `load_jsonl`'s dir-mode branch means calling
  it directly on a now-directory-valued constant crashes with `IsADirectoryError` rather than
  transparently globbing. This does not change Option B's recommendation or its rationale
  (minimizing blast radius on literal-file-injection tests) — it only means "zero code change"
  should be read as "zero change to the ~15+ tests using literal single-tmp-file monkeypatches,"
  not "zero change to any call site of a `DEFAULT_*`-valued constant."
- **Ratification of investigation's decision #4 (Risk #3, recommendation (b))** — accepted:
  `weight_sensitivity_check.py` and `retro_nudge_hook.py` both import and reuse `load_data_glob`
  from `validate.py` rather than hand-rolling a fourth/fifth glob implementation. `seq_offset.py`
  already imports from `validate.py` (confirmed, `load_jsonl` today) — extended to also import
  `load_data_glob`, same treatment.
- **`skill_usage_metric.py` is NOT in this ticket's Related Code Areas** — it inherits Step 3's
  fix for free via its `from generate_retro import DEFAULT_TOOLS_FILE, build_skill_usage_section,
  load_jsonl` (confirmed by direct grep this session) and its own `main()`'s bare
  `load_jsonl(DEFAULT_TOOLS_FILE)` call — under the new directory-valued `DEFAULT_TOOLS_FILE`,
  this call would crash the same way `generate_retro.py::main()`'s old call did, unless/until this
  file is separately fixed. Its own real-corpus test
  (`test_live_corpus_matches_independently_derived_counts`) was not run this session; its
  post-this-ticket status is unconfirmed. Not this ticket's job to fix — flagged so Finalize does
  not assume it was silently covered.
- **`retrieval_baseline_metrics.py` and `security_gate_firing_check.py`** (found by this session's
  own direct grep, not named in investigation.md) both import a block from `generate_retro.py`
  built around composed functions (`_load_runs_and_events` and others), not `load_jsonl`/
  `DEFAULT_TOOLS_FILE` directly — grep confirmed zero `load_jsonl(`/`DEFAULT_TOOLS_FILE` reference
  in either file. These two inherit Step 3's fix with **no** crash risk (unlike
  `skill_usage_metric.py`), but their own test suites are still outside this ticket's regression
  surface and were not run this session — same "flagged, not verified" treatment.
- **`_load_source` dispatcher is duplicated (not shared) across `build_index.py` and
  `generate_retro.py`** — deliberate, matching each file's pre-existing independent-`load_jsonl`
  convention rather than introducing new cross-module coupling beyond the shared `load_data_glob`
  primitive in `validate.py`. `weight_sensitivity_check.py`/`retro_nudge_hook.py`/`seq_offset.py`
  do not need their own `_load_source` dispatcher at all — they only ever read the
  `DEFAULT_*`-style default (never take a CLI override to a literal single file the way
  `build_index.py`'s `--runs-file` etc. do), so they call `load_data_glob` directly, no dispatch
  needed.
- **`test_agent_monitoring_legacy_reader.py::_recent_records()`'s exact current body was not
  directly read this planning session** (investigation cites approximate line numbers ~200-243
  from its own earlier read) — Step 7 flags this as needing reconfirmation at implementation time
  before the exact rewrite is written. Not expected to change the overall approach (repoint to the
  same `agent-monitoring/data/*/{runs,events}.jsonl` glob every other step uses), only the exact
  diff.
- **Glob determinism is load-bearing, not cosmetic** — `sorted(...)` around every new
  `Path.glob()` call is required by name in 3+ existing reproducibility tests; a non-deterministic
  glob order would produce flaky byte-identity failures, not an obvious functional bug, making it
  easy to miss in review.

## Unresolved Questions

None blocking implementation start. The two corrections to investigation's "zero code change"
claims (Step 3 items 7-8, Step 11) are resolved within this plan, not left open — they are a
direct, mechanical consequence of ratifying Option B as specified, not a new design choice
requiring a separate decision. The only item genuinely deferred to implementation time is Step 7's
exact `_recent_records()` current body (flagged above, not expected to change the approach).

## Deviations (recorded during Implement)

- **4 additional real-corpus call sites in `tests/tools/test_generate_retro.py` were found and
  fixed, beyond the 2 named in Step 3's Verify list.** Running the full 167-test file after Steps
  1-14 landed surfaced 4 failures the plan did not anticipate:
  `TestComputeRetrievalMetrics::test_expansion_rate_reads_zero_percent_on_real_corpus_absent_any_real_trigger`
  (`generate_retro.load_jsonl(generate_retro.EVENTS_FILE)`), and
  `test_skill_usage_section_matches_real_corpus_counts`,
  `test_backend_testing_post_fix_state_not_currently_flagged`,
  `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` (all 3
  `generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)`) — each crashed with
  `IsADirectoryError` for the identical structural reason Step 3 items 7-8/Step 11 already
  document (bare `load_jsonl()` against a now-directory-valued constant). Fixed the same way:
  changed each call site to `generate_retro._load_source(generate_retro.EVENTS_FILE, "events")` /
  `generate_retro._load_source(generate_retro.DEFAULT_TOOLS_FILE, "tools")`. This is the same
  correction class the plan already ratified for Steps 3/7/11, just at 4 more call sites
  investigation's grep did not surface — a test-fixture-shape update, not a production-code
  change, matching Step 3's own "if so, that is a legitimate test-fixture-shape update" framing.
- **`tests/tools/test_done_ticket_monitoring_coverage.py` mocks `load_jsonl` on the module object
  in 7 places (`patch.object(dtmc, "load_jsonl", ...)`) — none of this was flagged by the plan.**
  Since Step 11 changes `done_ticket_monitoring_coverage.py`'s import from `load_jsonl` to
  `load_data_glob`, `dtmc.load_jsonl` no longer exists as a module attribute, so every existing
  `patch.object(dtmc, "load_jsonl", ...)` call would raise `AttributeError`. Renamed all 7 mock
  targets (and the `test_reuses_generate_retro_load_jsonl_not_a_second_loader` architecture-guard
  test, renamed to `test_reuses_shared_load_data_glob_not_a_second_loader` and asserting
  `load_data_glob` instead) to `load_data_glob` — same mocking pattern, new attribute name.
- **`manifest.py`'s test file has a second, previously-unnoted real-corpus read site:
  `_content_hash_snapshot()`** (used only by `test_manifest_run_against_real_corpus_produces_zero_diff`,
  one of the 4 tests the ticket's own text already named as RED) did `path.read_bytes()` directly
  against `agent-monitoring/runs.jsonl`/`events.jsonl` (dead paths) for 2 of its 3 watched files,
  and only handled `tools.jsonl`'s old flat-shard glob for the third. Rewritten to glob
  `agent-monitoring/data/*/<source>.jsonl` uniformly for all 3 watched files, matching Step 4's
  production glob shape.
- **`test_agent_monitoring_legacy_reader.py::_recent_records()`'s exact fix needed one adjustment
  beyond a literal glob repoint**, flagged in the plan itself as deferred-to-implementation-time
  (Anti-Drift Notes, last bullet). The real `agent-monitoring/data/unknown-week/` folder holds a
  genuine, dated-2026-06-14 legacy-shaped record
  (`FOLDER-tickets-todos-cert-memory-fix`) that sorts alphabetically AFTER every real `YYYY-Www`
  week folder (`'u' > '2'`/`'9'`), so a plain `sorted(glob(...))[-N:]` "most recent N records"
  selection wrongly treated it as newer than genuinely current 2026-W36 data, breaking
  `test_recent_runs_records_classify_as_current_and_agree_with_validate`'s "recent records must be
  current-schema" assertion. Fixed by excluding `unknown-week` specifically from this **test-only**
  recency-sampling helper (production glob reads elsewhere — `load_data_glob()`,
  `manifest.py`, etc. — still correctly include it; the Anti-Drift Hazard about never
  special-casing `unknown-week` out of a glob applies to those production aggregation reads, not
  to this test's own "most recent N" heuristic, which has no reliable way to place `unknown-week`
  records on a real timeline).
- **Added the AC7/test_plan-item-10 regression test that Step 1's own Verify list named
  (`test_validate_drift_reports_identical_pre_and_post_migration_fixed_window`) but which was
  initially missed during the Steps-1-15 pass** — added afterward as
  `TestDriftReportsUnaffectedByWeekShardMigration::test_validate_drift_reports_identical_pre_and_post_migration_fixed_window`
  in `tests/tools/test_validate_agent_monitoring.py`, per test_plan item 10's exact design (build
  the SQLite index from a synthetic 2-week corpus via `build_index.build()`, compare
  `compute_drift_report()`'s output against the same records read as one flat pre-migration list).
  No other test_plan item was found missing on final audit.
- **`weight_sensitivity_check.py`'s previously-unused `_scan_file`-equivalent (a hand-rolled
  single-file reader inside `_load_tool_rows_and_events`)** was replaced with `load_data_glob()`
  calls exactly as planned; no deviation there. Separately, `manifest.py`'s own now-orphaned
  `_scan_file()` helper (superseded by `_scan_data_dir_glob()` in Step 4, no longer called from
  anywhere in `manifest.py`) was deliberately left in place rather than deleted — the plan did not
  instruct removing it, and this ticket already touches a large, shared, concurrently-worked-on
  file; removing an unused-but-harmless helper was judged out of this ticket's minimal-footprint
  scope rather than a required cleanup.
- **`test_agent_monitoring_manifest.py::test_manifest_run_against_real_corpus_produces_zero_diff`
  was observed to fail intermittently on a real-corpus content-hash comparison, unrelated to
  `manifest.py`'s own correctness** — verified in isolation (a standalone script calling
  `build_manifest()` directly against the real `agent-monitoring/` dir) that `build_manifest()`
  itself performs zero mutation and produces byte-identical before/after hashes; the observed
  failures happened only when the test ran as part of a larger `pytest` invocation immediately
  after other Bash tool calls in this same live, actively-monitored session (or from a genuinely
  concurrent sibling session per this ticket's own shared-worktree warning), which can append a
  new row to the current ISO week's real `tools.jsonl` between the test's own pre/post hash
  snapshots. Re-running the test in isolation was consistently green. Not a code defect —
  documented here per CLAUDE.md's regression-policy guidance on environment/concurrency-dependent
  flakiness against a live corpus, not silently re-run past without comment.
