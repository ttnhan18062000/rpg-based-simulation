---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CONSUMERS-CORE
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality]
---

# Investigation — TCK-20260903-MONITORING-DATA-CONSUMERS-CORE

## Current Behavior

### Confirmed on-disk state (real corpus, this worktree)
`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and `agent-monitoring/tools/` are
all absent (child 2, `TCK-20260903-MONITORING-DATA-MIGRATION`, retired them). Real data now lives
at `agent-monitoring/data/<ISO-week>/{runs,events,tools}.jsonl` — confirmed 15 week folders present
(`2026-W23` through `2026-W36`, plus `unknown-week`), each containing `runs.jsonl`/`events.jsonl`
(and `tools.jsonl` where any tool calls landed that week). This is the ground truth every one of
the 9 scripts below must read against.

### Confirmed current RED/GREEN test state (real run, this session, `/home/u24desktop/Working/venv/bin/python3 -m pytest`)
Running the full plausible regression surface (`test_agent_monitoring_manifest.py`,
`test_done_ticket_monitoring_coverage.py`, `test_agent_monitoring_legacy_reader.py`,
`test_build_index.py`, `test_seq_offset.py`, `test_weight_sensitivity_check.py`,
`test_generate_retro.py`, `test_query.py`, `test_validate_agent_monitoring.py`,
`test_skill_usage_metric.py`) together produced **9 failures, not 7**:

- `test_agent_monitoring_manifest.py::test_build_manifest_shape_against_real_corpus`,
  `::test_manifest_cli_reproducible_byte_identical_across_two_runs`,
  `::test_build_manifest_reproducible_byte_identical_direct_call`,
  `::test_manifest_run_against_real_corpus_produces_zero_diff` (the 4 named in the ticket).
- `test_done_ticket_monitoring_coverage.py::test_live_corpus_does_not_false_positive_this_sessions_own_recent_tickets`
  (the 1 named in the ticket).
- `test_agent_monitoring_legacy_reader.py::test_recent_runs_records_classify_as_current_and_agree_with_validate`,
  `::test_recent_events_records_remain_parseable` (the 2 named in the ticket).
- **2 additional failures in `test_generate_retro.py` not named anywhere in the ticket's own text**:
  `::test_correlation_real_corpus_produces_a_real_number` (asserts
  `rcc["compliant_group"]["count"] > 0`, currently gets `0 > 0` — fails) and
  `::test_parity_index_readpath_call_count_matches_real_corpus_state` (asserts `result["count"] ==
  4`, currently gets `0 == 4` — fails). Both call
  `generate_retro.load_jsonl(generate_retro.EVENTS_FILE)`/`generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)`
  directly against the real corpus — a real coverage gap in the ticket's own pre-Investigate grep,
  not a new regression this session introduced. **Total real RED count entering this ticket: 9, not
  7.**

`test_seq_offset.py`, `test_weight_sensitivity_check.py`, `test_query.py`,
`test_validate_agent_monitoring.py`, `test_skill_usage_metric.py`, `test_build_index.py` all
currently pass in full (0 failures). This is not evidence those scripts are unaffected — see below;
it is because none of their existing tests exercise the module-level path constants
(`TOOLS_FILE`/`EVENTS_FILE`/`RUNS_FILE`) or the real-file CLI entrypoints at all, only pure
fixture-dict functions or explicitly-injected `tmp_path` files.

### `tools/agent-monitoring/build_index.py` (211 lines)
- `DEFAULT_RUNS_FILE = Path("agent-monitoring/runs.jsonl")` (line 42) — dead path, `git rm`'d.
- `DEFAULT_EVENTS_FILE = Path("agent-monitoring/events.jsonl")` (line 43) — dead path, `git rm`'d.
- `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools")` (line 44) — this is the prior epic's
  (`TCK-20260902-MONITORING-SHARD-CONSUMERS`) fix, pointing at the shard *directory*. That
  directory (and its `tools-<week>.jsonl` files) was itself `git rm`'d by child 2 of *this* epic —
  the prior fix's target no longer exists either. **This constant needs a second, different fix,
  not a first one.**
- `build(args)` (lines 169-194): resolves `runs_path`/`events_path`/`tools_path` from `args.*_file`
  (CLI-arg-driven, not directly from the module constants — the constants only supply CLI
  *defaults*), then calls `load_jsonl(path)` for each — imported from `validate.py` (line 33-38),
  **not** defined locally.
- CLI args `--runs-file`/`--events-file`/`--tools-file`/`--db-path` (lines 201-204) default to the
  3 `DEFAULT_*` constants above.
- `test_build_index_never_touches_write_path_modules` (`tests/tools/test_build_index.py`, confirmed
  passing) is an AST/string guard banning any `"writer"` reference in `build_index.py`'s source —
  any glob-resolution helper added here must stay stdlib-only (`Path.glob()`), which is already
  true of every candidate design below.

### `validate.py`'s `load_jsonl(path)` (lines 223-240) — the function `build_index.py` imports
```python
def load_jsonl(path):
    if path.is_dir():
        records = []
        for shard in sorted(path.glob("tools-*.jsonl")):
            records.extend(load_jsonl(shard))
        return records
    if not path.exists():
        return []
    ...
```
This dual-mode design (prior epic) hardcodes the glob pattern `tools-*.jsonl` inside the `is_dir()`
branch — a pattern that only ever matched the now-`git rm`'d `agent-monitoring/tools/` flat shard
directory. It is **source-blind**: it has no way to know whether the directory it was handed is a
"runs" root, an "events" root, or a "tools" root — it always globs for `tools-*.jsonl` regardless.
`validate.py`'s own `main()` never calls this function itself (it reads exclusively via the SQLite
index — `load_runs_from_index`/`load_events_from_index`/`load_tools_from_index`, lines 43-55); it
exists purely as a library function `build_index.py` (and, via `generate_retro.py`'s **separate,
independent copy** — see below — `seq_offset.py`/`skill_usage_metric.py`) imports.

### `tools/agent-monitoring/generate_retro.py` (2,361 lines) — 6 real touch points, all confirmed by line number
- `RUNS_FILE = Path("agent-monitoring/runs.jsonl")` (line 53) — dead.
- `EVENTS_FILE = Path("agent-monitoring/events.jsonl")` (line 54) — dead.
- `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools")` (line 57) — same "prior fix's target itself
  retired" situation as `build_index.py`'s copy.
- `load_jsonl(path)` (lines 64-72) — **this file's own independent copy** of the identical
  `is_dir(): glob "tools-*.jsonl"` dual-mode function `validate.py` defines separately. Confirmed
  by direct read: `build_index.py` imports its copy from `validate.py`; `generate_retro.py` never
  imports `validate.py`'s copy or vice versa — two independently-maintained functions with
  identical bodies, both now hardcoding the same dead glob pattern.
- `_source_mtime(source)` (lines 75-83) — same `is_dir(): glob "tools-*.jsonl"` pattern, used only
  for staleness comparison (`max()` of shard mtimes).
- `_index_is_stale(db_path)` (lines 86-98) — loops `for source in (RUNS_FILE, EVENTS_FILE,
  DEFAULT_TOOLS_FILE): mtime = _source_mtime(source)`. Since `RUNS_FILE`/`EVENTS_FILE` are literal
  files that no longer exist, `_source_mtime()` returns `None` for both — this staleness check can
  **never** fire for a `runs`/`events` write today, and (per the point above) the `tools` branch's
  glob pattern also matches nothing. `_index_is_stale()` degrades to "always False once any DB
  exists," silently reproducing exactly the bug class
  `TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS` was built to prevent — but now for all 3
  sources, not just `tools`.
- `_load_runs_and_events()` (lines 101-137): on staleness, calls
  `build_index.build(SimpleNamespace(runs_file=str(RUNS_FILE), events_file=str(EVENTS_FILE),
  tools_file=str(DEFAULT_TOOLS_FILE), db_path=str(DEFAULT_DB_PATH)))`; on any `Exception`, falls
  back to `load_jsonl(RUNS_FILE), load_jsonl(EVENTS_FILE)` (both now silently `[]`, `[]` — no
  exception, no warning distinguishable from "genuinely empty corpus"). Since the primary path
  (build via SQLite) also resolves the same 3 dead constants, `_load_runs_and_events()` returns
  `([], [])` today for the fallback branch and an index built from 0 rows for the primary branch.
- **`main()`'s third call site (line 2272, confirmed by grep — not the prior-epic-cited "~2255",
  citation drift already accounted for)**: `all_tools = load_jsonl(DEFAULT_TOOLS_FILE)` — feeds
  `generate()`'s `tools=`/`all_tools=` params (line 2302-2304) and `_update_index(all_runs,
  all_tools)` (line 2314), which threads `all_tools` into the per-week retro-index table
  (`_update_index`, lines 2317+, "Mirrors main()'s own per-period run_id filter of all_tools").
  This call site is not named anywhere in the ticket's own Scope/Request-Summary text but is
  squarely in-scope: fixing `DEFAULT_TOOLS_FILE`'s value + `load_jsonl`'s glob logic fixes it with
  zero code change at this call site, exactly like the prior epic's precedent.
- **`skill_usage_metric.py` (NOT in this ticket's Related Code Areas) inherits the fix for free**:
  its `main()` does `load_jsonl(DEFAULT_TOOLS_FILE)` using names imported directly from
  `generate_retro.py` (comment at generate_retro.py:439-445 confirms this deliberate reuse — no
  independent path constant of its own). Its own tests
  (`test_live_corpus_matches_independently_derived_counts` and friends) are not in this ticket's
  regression surface and were not run this session — flagged as a real, out-of-this-ticket's-scope,
  likely-currently-broken sibling (same shape as the 9 confirmed RED tests) for whoever eventually
  owns it; not this ticket's job to fix or verify.

### `tools/agent-monitoring/manifest.py` (153 lines) — worse than the ticket's own citation implies
- `_FILES_BY_SOURCE = {"events.jsonl": "events", "runs.jsonl": "runs", "tools.jsonl": "tools"}`
  (lines 23-27).
- `_scan_file(path, source)` (lines 48-59): unconditional `open(path, "rb")` — for the
  `events.jsonl`/`runs.jsonl` entries this now hits a **dead path directly**, not just the `tools`
  entry the prior epic's own fix addressed.
- `_scan_tools_shards(tools_dir, source)` (lines 62-76): the prior epic's fix — globs
  `tools_dir.glob("tools-*.jsonl")`. `tools_dir` (`agent_monitoring_dir / "tools"`) no longer
  exists either.
- `build_manifest(agent_monitoring_dir)` (lines 79-86): for `source == "tools"`, calls
  `_scan_tools_shards(dir / "tools", ...)`; for `events`/`runs`, calls `_scan_file(dir /
  filename, ...)` directly. **All 3 branches now hit a nonexistent path** — this is why 4 of
  `test_agent_monitoring_manifest.py`'s real-corpus tests fail (confirmed above), and it is a
  strictly bigger gap than the ticket's own citation ("`manifest.py`'s tools-source branch") states
  — the `events`/`runs` branches were already broken before this ticket, by the same
  `_scan_file`-unconditional-`open()` mechanism the prior epic diagnosed for `tools` alone.
- `capture_lines(agent_monitoring_dir)` (lines 89-113): the identical unconditional-open + old
  tools-dir-glob pattern, for the same 3 filenames. No test in
  `tests/tools/test_agent_monitoring_manifest.py` currently calls `capture_lines()` against the
  real corpus (confirmed by grep — no `capture_lines(` call site targets
  `_REAL_AGENT_MONITORING_DIR`), so this function's break is currently silent/untested, not just
  broken-and-flagged.
- **2 currently-GREEN `tmp_path`-fixture tests hardcode the now-obsolete flat-shard shape** and
  will regress once the glob pattern changes to match the new `agent-monitoring/data/<week>/
  <source>.jsonl` layout:
  `test_manifest_tools_source_aggregates_all_shards` (writes `tmp_path/"tools"/"tools-2026-W01.jsonl"`
  etc., line 87-109) and `test_manifest_tools_source_sha256_is_order_stable_across_shards` (same
  fixture shape, line 111-129). Both currently pass because they construct their own synthetic
  `tools_dir` matching the OLD shape and never touch the real corpus — but a redesign of
  `build_manifest()`'s glob target (see Risks below) will silently stop exercising anything
  meaningful for these two unless their fixtures are rewritten to the new week-subdirectory shape.
- `test_manifest_source_never_calls_full_file_read_methods` (AST guard, currently passing) bans
  `read_text`/`read_bytes`/`readlines`/`read` anywhere in `manifest.py`'s source — `Path.glob()` +
  `open(..., "rb")` + line iteration remain compliant under any redesign that stays streaming.

### `tools/agent-monitoring/legacy_reader.py` (100 lines) — confirmed no independent fix surface
Pure classifier (`classify_provenance(record, source)`), zero file I/O, zero path constants.
`manifest.py` is its only production caller. Its own test file,
`tests/tools/test_agent_monitoring_legacy_reader.py`, is a *different* file from `manifest.py`'s
test file and has its own, separate real-corpus dependency (`_recent_records()`, lines ~200-243,
does `path.read_text().splitlines()` directly against `_REAL_AGENT_MONITORING_DIR / "runs.jsonl"` /
`"events.jsonl"` — dead paths, confirmed as 2 of the 9 currently-RED tests above). Fixing this test
file's own `_recent_records()`/`_SAMPLE_SIZE` helper (test-only code, not `legacy_reader.py` itself)
is required for this ticket's own explicit Definition-of-Done citation of this file.

### `tools/agent-monitoring/seq_offset.py` (45 lines) — confirmed, matches ticket's own citation exactly
- `EVENTS_FILE = Path("agent-monitoring/events.jsonl")` (line 27) — dead, confirmed stale exactly
  as the ticket's Assumptions section (citing the prior epic's architecture-reviewer) flagged.
- `compute_seq_offset(run_id, events)` (lines 30-40) is pure/read-only, takes an already-loaded
  `events` list — needs zero change itself.
- `__main__` entrypoint (line 43-44): `load_jsonl(sys.argv[1], load_jsonl(EVENTS_FILE))` — wait,
  exact form is `compute_seq_offset(sys.argv[1], load_jsonl(EVENTS_FILE))`, imported from
  `validate.py` (line 25). This is the only real call site needing a fix — glob
  `agent-monitoring/data/*/events.jsonl`, concatenate, pass to the unchanged pure function.
- **No existing test exercises this `__main__`/`EVENTS_FILE` path at all**:
  `tests/tools/test_seq_offset.py` (44 lines, read in full) tests only `compute_seq_offset()`
  directly with hand-built fixture dicts — zero file I/O, zero reference to `EVENTS_FILE`. This is
  exactly why the live bug went undetected — matches the ticket's framing precisely.

### `tools/agent-monitoring/weight_sensitivity_check.py` (232 lines) — the named critical bug, confirmed and quantified
- `TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` (line 29) — the *original* monolithic path,
  dead since `TCK-20260902-MONITORING-SHARD-MIGRATION` (2026-09-02), predating even this epic.
- `EVENTS_FILE = Path("agent-monitoring/events.jsonl")` (line 30) — dead since this epic's child 2.
- `_load_tool_rows_and_events(tools_path, events_path)` (lines 137-167): does its **own**
  unconditional `if tools_path.exists(): with open(tools_path, ...)` / `if events_path.exists():
  with open(events_path, ...)` — a third, independent single-file-read implementation (not
  `load_jsonl` from either `validate.py` or `generate_retro.py`). Both `.exists()` guards are
  `False` today, so `main()` (line 221: `tool_rows_by_group, phase_of, agent_of =
  _load_tool_rows_and_events(TOOLS_FILE, EVENTS_FILE)`) silently computes `n_groups_scored: 0` and
  empty `by_phase`/`by_agent` reports — **exactly the "TOOLS_FILE ground-truth bug" the ticket
  names**, confirmed by direct read (not inferred): no exception anywhere, a fully well-formed but
  empty/zero report every real invocation.
- `compute_weight_sensitivity_report()` (lines 96-134) and `_score_with_weights()`/
  `_spearman_rank_correlation()`/`_group_report()` are all pure functions taking pre-loaded dicts —
  need zero change.
- **Confirmed: no existing test in `tests/tools/test_weight_sensitivity_check.py` (139 lines, read
  in full) exercises `_load_tool_rows_and_events()`, `TOOLS_FILE`, `EVENTS_FILE`, or `main()`'s CLI
  path at all** — every test calls `compute_weight_sensitivity_report()`/`_score_with_weights()`/
  `_spearman_rank_correlation()` directly with hand-built dicts. This is why the bug has been live
  and undetected — the ticket's own AC4 (a new regression test with real multi-week seeded data
  asserting a nonzero score) is the first test that will ever actually exercise this code path.

### `tools/agent-monitoring/retro_nudge_hook.py` (93 lines) — confirmed, plus a real test-coverage gap
- `RUNS_FILE = Path("agent-monitoring/runs.jsonl")` (line 18) — dead.
- `_count_done_since(cutoff)` (lines 38-61): `if not RUNS_FILE.exists(): return 0`; then
  `for line in RUNS_FILE.read_text().splitlines():` — a third independent single-file-read
  implementation (neither `load_jsonl` copy). Silently returns `0` today for every invocation
  (`RUNS_FILE.exists()` is `False`), meaning the retro-nudge PostToolUse hook **can never fire**
  right now — `count >= THRESHOLD` (5) can never be reached with a permanent `count == 0`. This is
  a live, silent behavioral regression of the same class as `weight_sensitivity_check.py`'s named
  bug, just not named in the ticket's own text.
- Entire `try/except Exception: pass` wraps the whole module body (lines 64-93) — the fail-silent
  contract child 1's write-path work established for hooks applies identically here; any fix must
  stay inside this block.
- **No test file exists for this script at all**: `grep -rl "retro_nudge_hook" tests/` returns zero
  matches in `tests/tools/` (one unrelated fixture-data hit in
  `tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json`, a string literal, not a test of
  this module). This is a genuine coverage gap, not a currently-passing-then-regressed test — a new
  test file is needed from scratch to satisfy the ticket's AC5 ("`retro_nudge_hook.py`... correctly
  read[s] the union of week folders").

### `tools/agent-monitoring/done_ticket_monitoring_coverage.py` (123 lines) — resolves the ticket's own open question
- Line 22: `from generate_retro import RUNS_FILE, load_jsonl` — **confirmed: this file has no
  independent path constant of its own.** It fully inherits `generate_retro.py`'s `RUNS_FILE` value
  and `load_jsonl` function by direct import (the ticket's Assumptions section correctly flagged
  this as unresolved by its own grep; now resolved).
- `build_coverage_section(done_dir)` (lines 60-104): `runs = load_jsonl(RUNS_FILE)` (line 71) — the
  only read call site. Its own docstring/comment (lines 62-70) explicitly documents *why* it
  bypasses `generate_retro._load_runs_and_events()`'s SQLite-index path in favor of a direct
  `load_jsonl(RUNS_FILE)` scan — freshness (the SQLite index can lag by up to "the last time
  something happened to call it"). This design rationale is unaffected by this ticket's fix; only
  `RUNS_FILE`'s resolved value/glob behavior changes, automatically, once `generate_retro.py`'s
  `RUNS_FILE`/`load_jsonl` are fixed. **Zero code change needed in this file itself** — confirmed by
  direct read, matching the ticket's own prediction ("fixing manifest.py/
  done_ticket_monitoring_coverage.py's read paths here... will naturally fix most of these").
- The 1 currently-failing test,
  `test_live_corpus_does_not_false_positive_this_sessions_own_recent_tickets`, will pass once
  `generate_retro.RUNS_FILE`/`load_jsonl` are fixed, with no change to
  `done_ticket_monitoring_coverage.py` itself.

### `tools/agent-monitoring/query.py` (165 lines) — confirmed no-op, matches prior epic's and this ticket's own claim
Read in full. Only path constant: `DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")`
(line 25), used by `open_index()`/`--db-path` (lines 29, 145). Zero reference to
`runs.jsonl`/`events.jsonl`/`tools.jsonl`/`RUNS_FILE`/`EVENTS_FILE`/`load_jsonl` anywhere in the
file (grep confirmed, zero matches). `load_runs_from_index`/`load_events_from_index` (lines 39-51)
read exclusively via `conn.execute("SELECT ... FROM runs/events ORDER BY id")` against the SQLite
index. `tests/tools/test_query.py` has its own architecture guard
(`for forbidden in ("RUNS_FILE", "EVENTS_FILE", "load_jsonl"): ...`, line 394) explicitly pinning
this invariant, currently passing. **No change needed to `query.py`; AC "query.py's existing test
suite passes unmodified" is expected to hold with zero edits to this file.**

### `tools/agent-monitoring/validate.py` (331 lines) — confirmed: `main()` itself is a no-op, `load_jsonl()` is the real fix surface
`main()` (lines 251-330) reads exclusively via `open_index()`/`load_runs_from_index()`/
`load_events_from_index()`/`load_tools_from_index()` (lines 33-55), all SQLite-backed — zero direct
JSONL file reads in `main()` itself. `compute_drift_report()`/`compute_tool_count_drift_report()`/
`compute_multi_invocation_collision_report()` (lines 88-220) are all pure functions taking
pre-loaded lists — need zero change. **The only fix surface in this file is `load_jsonl(path)`
itself (lines 223-240)** — the function `build_index.py` imports and depends on (see above); fixing
it here is what fixes `build_index.py`'s read layer. `tests/tools/test_validate_agent_monitoring.py`
(confirmed by grep) uses `_build_db()` (constructs a SQLite DB directly) and
`monkeypatch.chdir(tmp_path)` + `assert not (tmp_path / "agent-monitoring").exists()`-style
read-only guards — zero real-corpus JSONL dependency found. AC "validate.py's drift-report functions
produce identical results... regression check" is expected to hold with the fix confined to
`load_jsonl()`.

## Mechanics / Engine Constraints

None. This is pure agent-orchestration/monitoring tooling (`docs/agent-monitoring/`), not a
simulation-behavior change — no `src/` file is touched, no Mechanics Bible chapter or engine
contract governs this subsystem's semantics (same category as the entire INFRA-28x through
INFRA-333 run of parity ledger entries covering this tooling's prior migrations, confirmed by
direct read of the relevant entries below).

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: lines 29-32 ("Derived SQLite Index" section) describe the
  staleness mechanism as "`runs.jsonl`/`events.jsonl` each compared by their own single mtime; the
  `tools` source compares against the newest mtime across all `agent-monitoring/tools/tools-*.jsonl`
  shard files" — inaccurate on both halves once this ticket lands: `runs`/`events` become
  multi-week-glob sources too (no longer "their own single mtime"), and the `tools` shard-glob path
  it names (`agent-monitoring/tools/tools-*.jsonl`) no longer exists on disk at all. Must be
  reworded to describe all 3 sources comparing against the newest mtime across their respective
  `agent-monitoring/data/*/<source>.jsonl` week files.
- `docs/agent-monitoring/README.md`: the Navigation table (line 148, the ticket's own named
  example) reads "Full field reference for runs.jsonl, events.jsonl, and the
  tools/tools-YYYY-Www.jsonl shard family" — must be updated to describe the current
  `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` layout (already the accurate physical
  shape per `schema.md`'s own already-updated per-source sections from children 1/2).
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-291` entry, `tools/agent-monitoring/
  generate_retro.py:5803` area, confirmed by direct read at lines 6363-6510): this entry already
  carries 2 addenda (2026-08-14 for the index-staleness fix, 2026-09-03 for the prior epic's
  shard-directory repoint) and its most recent `v2_evidence` text explicitly states
  `DEFAULT_TOOLS_FILE` was repointed to `Path("agent-monitoring/tools")` and `load_jsonl()` globs
  `sorted(tools_dir.glob("tools-*.jsonl"))` — both now factually superseded by this ticket's own
  change (per CLAUDE.md's Authoritative Mechanics Rule: "If logic changes, update the corresponding
  doc AND the parity ledger entry... in the same session"). Needs a third, dated addendum describing
  the new `agent-monitoring/data/*/<source>.jsonl` glob design for all 3 sources, following the
  entry's own established addendum pattern (do not rewrite the earlier addenda).

The following were considered and explicitly excluded:

`docs/agent-monitoring/README.md`'s line 54 ("prints a JSON report over the same
`runs.jsonl`/`events.jsonl`/`tools/tools-YYYY-Www.jsonl` sources") is not required to change for
this ticket: it describes `tools/agent-monitoring/retrieval_baseline_metrics.py`, a script not
among this ticket's 9 in-scope files and not touched by this ticket's own Related Code Areas or
Scope text. Fixing this line's prose without fixing the script it describes would make the doc
describe intended-but-not-yet-implemented behavior — worse, not better. Left for whichever future
ticket (likely child 7's broader sweep, or a dedicated fix to `retrieval_baseline_metrics.py`
itself, which was not investigated here) actually touches that script.

`docs/agent-monitoring/README.md`'s lines 128-129 ("Deliberately reads `runs.jsonl` directly rather
than through `generate_retro`'s SQLite-index path") describing `done_ticket_monitoring_coverage.py`
is not required to change: this description is conceptual/architectural ("reads directly, bypassing
the index, for freshness"), not a physical-file-shape claim, and remains true after this ticket's
fix — `build_coverage_section()` still reads directly via `load_jsonl(RUNS_FILE)`, bypassing the
SQLite index, exactly as documented; only what `RUNS_FILE`/`load_jsonl` resolve to under the hood
changes.

`docs/parity_ledger/infrastructure.yaml`'s `INFRA-285` entry (`weight_sensitivity_check.py`,
lines 5889-5941) is not required to change: its `v2_evidence` documents the pure
`compute_weight_sensitivity_report()`/`_spearman_rank_correlation()` functions and the
`--candidate-weights`/`--baseline-weights` CLI contract — none of which this ticket touches. It
never quotes a literal `TOOLS_FILE`/`EVENTS_FILE` path value (confirmed by direct read), so this
ticket's fix to those two constants does not make any claim in this entry stale.

`docs/parity_ledger/infrastructure.yaml`'s `INFRA-288` entry (`seq_offset.py`, lines 6119-6177) is
not required to change for the same reason: its `v2_evidence` documents `compute_seq_offset()`'s
pure-function shape and the `implement-ticket.js` `resolveSeqOffset()`/`seqOffset` call-site wiring
— never a literal `EVENTS_FILE` path value. This ticket's fix to `EVENTS_FILE`'s resolution does not
make any claim in this entry stale.

## Parity Ledger Overlap

- `INFRA-291` (`docs/parity_ledger/infrastructure.yaml`, status `verified`, priority `P2`) —
  directly touched; needs a third addendum, see Docs Requiring Update above. Not `P0`, so no gating
  `test_path` re-run is required by ledger rules, but correction is still required per the
  Authoritative Mechanics Rule.
- `INFRA-285` (weight_sensitivity_check.py, `verified`/`P2`) and `INFRA-288` (seq_offset.py,
  `verified`/`P2`) — checked, not affected (see Docs Requiring Update's exclusions above).
- `INFRA-289`/`INFRA-290` (`query.py`/`validate.py`'s original SQLite-index migrations,
  `verified`/`P2`) — checked, not affected; neither cites a literal path value this ticket changes.
- No entry anywhere in `infrastructure.yaml` was found for `manifest.py`, `retro_nudge_hook.py`, or
  `done_ticket_monitoring_coverage.py` specifically (grep confirmed zero `- id:` block headers near
  any reference to these 3 filenames beyond incidental mentions) — none of these 3 scripts has its
  own dedicated parity ledger entry to update.
- No `P0` entries anywhere in `infrastructure.yaml` were found referencing any of this ticket's 9
  files or their path constants — all touched/considered entries are `P2`, so none carries CLAUDE.md's
  "P0 requires a passing `test_path`" hard requirement.

## Prior Work

- `stored_artifacts/TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY/` (child 1) — established the
  write-side `agent-monitoring/data/<ISO-week>/{runs,events,tools}.jsonl` layout this ticket's
  readers must now target, and fixed `record_events.py`'s analogous `TOOLS_FILE` ground-truth bug
  via `sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl"))` — the exact glob shape this
  ticket's design should match for consistency (confirmed by direct read of its plan.md Step 4).
- `stored_artifacts/TCK-20260903-MONITORING-DATA-MIGRATION/` (child 2) — the one-time migration that
  physically moved all historical data into the new layout and `git rm`'d the 3 legacy paths this
  ticket's 9 scripts still reference; its own plan.md's "Deviations" section is where the 7 (now 9,
  per this investigation) newly-broken tests were first surfaced and explicitly deferred to this
  ticket.
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-CONSUMERS/` (prior epic's consumer-migration
  ticket) — built the dual-mode directory-glob-or-literal-file `load_jsonl()` pattern and the
  multi-shard-mtime staleness-check design this ticket is asked to "reuse/extend." **Critical
  finding: that prior design's directory-glob target (`agent-monitoring/tools/tools-*.jsonl`, a flat
  shard directory) is itself now dead — child 2 of the current epic superseded it, not merely left
  it in place.** This ticket cannot literally "extend" that pattern to `runs`/`events`; it must
  redesign the glob target for all 3 sources. See Risks below.
- `docs/agent-monitoring/schema.md` — already updated by children 1/2 for the per-source write-path
  prose and the worked join example (lines 429-505-ish, confirmed present and correct at lines
  474-500 of the current file) — this ticket's own doc fix is narrower (just the staleness-check
  paragraph and the README Navigation-table line), not a repeat of that work.

## Risks and Open Questions

1. **The single biggest open design decision, requiring Plan's explicit ratification**: the
   existing `load_jsonl(path)` dual-mode signature (`validate.py` and `generate_retro.py`'s
   independent copies) is source-blind — it decides what to glob purely from `path.is_dir()`, with
   the glob pattern (`tools-*.jsonl`) hardcoded inside the function body. The new unified
   `agent-monitoring/data/` layout is **source-agnostic at the top level**: `runs.jsonl`,
   `events.jsonl`, and `tools.jsonl` all live as siblings inside the *same* week directories, so a
   single directory argument can no longer imply which source to glob for. Two concrete resolution
   options, evaluated:
   - **Option A — parameterize by source.** Change `load_jsonl`'s signature to accept a source name
     (or add a new `load_source_jsonl(data_dir: Path, source: str) -> list` function), and change
     `DEFAULT_RUNS_FILE`/`DEFAULT_EVENTS_FILE`/`DEFAULT_TOOLS_FILE` to all point at the same
     `Path("agent-monitoring/data")` root, differentiated only by the source string each call site
     already knows. Requires touching every call site's signature, but keeps one shared, explicit
     mechanism.
   - **Option B — keep `load_jsonl(path)`'s meaning as "read exactly this one literal file, or `[]`
     if missing" unchanged (drop its dir-mode branch entirely), and add a small new helper (e.g.
     `load_data_glob(data_dir: Path, source: str) -> list`, doing
     `concat(load_jsonl(p) for p in sorted(data_dir.glob(f"*/{source}.jsonl")))`) used only by the
     `DEFAULT_*`-constant-driven default path.** This keeps every currently-passing
     literal-single-file-monkeypatch test (the large majority of `test_generate_retro.py`'s
     staleness/build-on-demand tests, and every `test_build_index.py`
     `TestBuildHappyPath`/`TestReadOnlyGuarantee`/`TestNormalizationParity`/`TestLegacyShapeGuards`
     test) passing unmodified, since they never exercise the new glob helper at all — they inject a
     literal `tmp_path / "runs.jsonl"` file directly.
   **Recommendation: Option B.** It minimizes the blast radius on the ~15+ currently-green tests
   that rely on `load_jsonl`'s existing literal-file semantics staying exactly as-is, and it mirrors
   child 1's own write-side precedent exactly (`Path("agent-monitoring/data") / iso_week /
   f"{source}.jsonl"` on write, `sorted(Path(...).glob(f"*/{source}.jsonl"))` on read — a clean,
   symmetric pair). This is a real decision Plan must ratify explicitly, not silently default into.

2. **A real, evidence-confirmed consequence of resolving #1 either way: several currently-GREEN
   tests hardcode the now-permanently-dead flat "tools/tools-<week>.jsonl in one directory" shape
   and will need rewriting to the new week-subdirectory shape, regardless of which option is
   chosen** (any correct fix stops matching `tools-*.jsonl` glob patterns against that flat shape).
   Confirmed by direct read:
   - `tests/tools/test_build_index.py::TestShardedToolsSource` (3 tests: `test_build_index_reads_
     multiple_shard_files_from_directory`, `test_build_index_includes_unknown_week_shard`,
     `test_build_index_glob_result_is_sorted`).
   - `tests/tools/test_agent_monitoring_manifest.py` (2 tests: `test_manifest_tools_source_
     aggregates_all_shards`, `test_manifest_tools_source_sha256_is_order_stable_across_shards`).
   - `tests/tools/test_generate_retro.py` (2 tests: `test_generate_retro_index_is_stale_detects_
     write_to_non_newest_shard`, `test_generate_retro_load_jsonl_globs_shard_directory`).
   **This is 7 additional currently-passing tests this ticket's own correct fix will legitimately
   break and must rewrite** — a materially larger regression surface than the ticket's own text
   implies ("generalize"/"extend" undersells that the shape being extended from no longer exists).
   Rewriting them to construct `tmp_path/"2026-W01"/"tools.jsonl"`-style week-subdirectory fixtures
   (matching the ticket's own AC2 test shape) is legitimate test-helper maintenance to keep the
   assertion meaningful, not a gate-dodge — same category as child 2's own explicitly-accepted
   precedent for the 7 (9) originally-RED tests.

3. **`weight_sensitivity_check.py`'s and `retro_nudge_hook.py`'s and `seq_offset.py`'s file-reading
   logic is each a *third* independent hand-rolled single-file-open implementation**, not a call to
   either `load_jsonl` copy: `weight_sensitivity_check.py::_load_tool_rows_and_events()` does its own
   `if path.exists(): with open(path) as f: for line in f: ...`; `retro_nudge_hook.py::
   _count_done_since()` does its own `if not RUNS_FILE.exists(): return 0` + `RUNS_FILE.read_text()`.
   Neither currently imports `load_jsonl` from anywhere. Plan must decide whether to (a) make each
   glob independently (duplicating the new glob helper's 2-3 lines a third/fourth time, matching
   these files' existing pattern of not sharing `load_jsonl`), or (b) have them import and reuse
   whatever new helper #1 introduces. Recommend (b) for `weight_sensitivity_check.py` (it already
   imports from `cost_proxy.py`, so cross-module imports within `tools/agent-monitoring/` are an
   established pattern) and `retro_nudge_hook.py` (it is a hook with the strictest fail-silent
   requirement — reusing an already-tested helper is lower-risk than hand-rolling a 4th glob
   implementation inside a `try/except Exception: pass` block).

4. **`retro_nudge_hook.py` has zero existing test coverage** — any new test file is new coverage,
   not a coverage-gap fix. Because this hook silently degrades to a permanent no-op today
   (`count` can never exceed 0), there is no existing "was it ever really tested" baseline to
   preserve — the new test(s) should assert both the fixed multi-week glob behavior AND the
   fail-silent contract (malformed `agent-monitoring/data/` content must not raise from inside the
   hook's outer `try/except`).

5. **`skill_usage_metric.py` inherits this ticket's `generate_retro.py` fix for free but is out of
   this ticket's own Related Code Areas/Scope** — its own real-corpus test
   (`test_live_corpus_matches_independently_derived_counts`) was not run this session and its
   status post-fix is unconfirmed. Flagged so Finalize does not assume it was silently covered by
   this ticket's own verification; it likely needs its own follow-up check (not necessarily its own
   ticket, since the fix requires zero code change to that file — see Prior Work).

## Anti-Drift Hazards

- **Do not widen any new glob beyond `*/<source>.jsonl` under `agent-monitoring/data/`.** A broader
  pattern (e.g. `**/*.jsonl`) risks silently picking up an unrelated future file dropped anywhere
  under `agent-monitoring/`. Match child 1's write-side glob shape exactly:
  `agent-monitoring/data/*/<source>.jsonl` (one wildcard segment for the week folder, then the
  literal source filename).
- **Do not forget the `unknown-week` folder.** It is real historical data (confirmed present on disk
  at `agent-monitoring/data/unknown-week/`), not a sentinel to filter — `*` in
  `agent-monitoring/data/*/<source>.jsonl` naturally includes it; do not special-case it out.
- **Do not change `_ingest_runs()`/`_ingest_events()`/`_ingest_tools()`'s off-schema-record skip
  logic in `build_index.py`** (lines 99-166) — pure normalization logic, explicitly out of scope
  per the ticket's own Out of Scope ("Any change to build_index.py's table schema, or to
  `_resolve_status()`/`_is_legacy_event()`/any other centralized normalization logic — only the
  file-resolution layer changes").
- **Do not touch `record_run.py`/`record_events.py`/`post_tool_hook.py`/`writer.py`** — the write
  path is child 1's completed, separate work; this ticket is read-path only.
- **Do not touch `tools/gate_checks/done_checker_static.py`, `src/api/agent_ops_dashboard/
  ingest.py`, `tools/agent_replay_codex/monitoring_shards.py`, or any new referential-integrity
  tooling** — explicitly children 4/5/6, confirmed zero references to any of this ticket's 9 files
  found in a scoped grep of the first two (not independently re-verified for the codex subsystem,
  since it is explicitly out of scope per the assigning agent's own instruction).
- **`compute_seq_offset()`, `compute_weight_sensitivity_report()`, `_score_with_weights()`,
  `_spearman_rank_correlation()`, `compute_drift_report()`, `compute_tool_count_drift_report()`,
  `compute_multi_invocation_collision_report()` are all pure functions that need zero change** —
  the fix is exclusively in the file-resolution layer feeding them. Do not "simplify" or refactor
  these functions' internals while touching the surrounding read logic.
- **Do not let `manifest.py`'s fix change its 3-record output shape.** `test_build_manifest_shape_
  against_real_corpus` hard-requires exactly 3 manifest records with the literal filename set
  `{"events.jsonl", "runs.jsonl", "tools.jsonl"}` — aggregate across all week folders into one
  logical record per source, never one record per week file.
- **Glob determinism**: every new glob call must be wrapped in `sorted(...)` — `Path.glob()` does
  not guarantee sort order, and multiple currently-passing reproducibility tests
  (`test_manifest_cli_reproducible_byte_identical_across_two_runs`, `test_build_manifest_
  reproducible_byte_identical_direct_call`, `test_build_index_glob_result_is_sorted`'s successor)
  depend on it.
