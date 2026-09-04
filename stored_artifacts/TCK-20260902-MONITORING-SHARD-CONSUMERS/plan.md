---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-CONSUMERS
artifact_type: plan
tags: [agent-monitoring, observability, data-quality]
---

# Implementation Plan — TCK-20260902-MONITORING-SHARD-CONSUMERS

## Summary

`agent-monitoring/tools.jsonl` no longer exists on disk (child ticket 2 `git rm`'d it); real
tool-call data now lives in `agent-monitoring/tools/tools-YYYY-Www.jsonl` shard files (14 of them,
confirmed on disk, including the `tools-unknown-week.jsonl` fallback bucket). This plan makes every
reader of that data dir-aware via one repeated pattern — **dual-mode resolution**: if the configured
path is a directory, glob `tools-*.jsonl` inside it (sorted, concatenated); if it's a literal file
(existing or not), fall back to the exact pre-existing single-file behavior unchanged. This pattern
is applied independently at four call sites across three production files
(`build_index.py`/`validate.py`'s shared `load_jsonl`, `generate_retro.py`'s own `load_jsonl` +
`_index_is_stale`, and `manifest.py`'s `_scan_file`/`build_manifest` + `capture_lines`), plus two
test-helper functions that independently hardcode the retired path. `query.py`/`validate.py`'s
report functions need no change (confirmed pure index-consumers). Two scope decisions not literally
written into the ticket's Scope text are ratified here with rationale (manifest.py formally pulled
into scope; a real, currently-red regression in `manifest.py::capture_lines()` discovered during
planning and pulled in alongside it), one doc is explicitly deferred, and the parity ledger entry
this ticket's own change stales is updated via the sanctioned writer script.

## Ratified Decisions (read before implementing)

**Decision 1 — Glob pattern and inclusion of `tools-unknown-week.jsonl`: ACCEPTED, no exclusion.**
Every glob site uses `sorted(dir.glob("tools-*.jsonl"))`, never `*.jsonl`. `tools-unknown-week.jsonl`
is real historical data and must be included like any other shard — this is codified as Anti-Drift
Hazard 1 below and as New Test 2 in the Test Plan. Rationale: the ticket's own Scope text says
"glob over `agent-monitoring/tools/tools-*.jsonl`," and investigation.md confirmed this shard's rows
are already out-of-chronological-order by construction, so its position in file-processing order
carries no chronological meaning either way — filtering it would silently drop real data for no
correctness gain.

**Decision 2 — `manifest.py` formally pulled into this ticket's Scope.** Not named in the ticket's
original `## Scope`/`## Related Code Areas`, but `_FILES_BY_SOURCE["tools.jsonl"]`
(`tools/agent-monitoring/manifest.py:23-27`) hardcodes the retired single path, and `_scan_file`'s
unconditional `open(path, "rb")` (line 36) raises `FileNotFoundError` on it — confirmed by direct
read during planning, not inferred. 4 of the ticket's 7 required-passing xfailed tests
(`test_build_manifest_shape_against_real_corpus`,
`test_manifest_cli_reproducible_byte_identical_across_two_runs`,
`test_build_manifest_reproducible_byte_identical_direct_call`,
`test_manifest_run_against_real_corpus_produces_zero_diff`, all in
`tests/tools/test_agent_monitoring_manifest.py`) cannot pass without this fix. There is no way to
satisfy the ticket's own "all 7 xfail markers removed, all 7 pass for real" bar otherwise, so this
is recorded as a deliberate scope decision, not a silent assumption.

**Decision 3 — `skill_usage_metric.py` needs zero independent production-code change.** Confirmed by
direct read (`tools/agent-monitoring/skill_usage_metric.py:24,33`): it imports
`DEFAULT_TOOLS_FILE`/`load_jsonl` directly from `generate_retro.py` and has no path constant of its
own. Fixing `generate_retro.py`'s pair (Step 2) fixes this module for free. Only its *test file*'s
own hardcoded-path helper (`_independently_derive_counts()`/`_REAL_TOOLS_FILE`) needs updating —
Step 6.

**Decision 4 — real scope addition discovered during planning: `manifest.py::capture_lines()`.**
Not named anywhere in the ticket, the investigation, or the test plan — discovered by running
`tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py` against this
branch during planning (`.venv/bin/python3 -m pytest
tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py -v`):
`test_capture_lines_reads_all_three_monitoring_files` **fails right now, on this branch, with
`FileNotFoundError: .../agent-monitoring/tools.jsonl`** — it is not xfailed, not in the ticket's
named 7, and lives outside `tests/tools/` entirely. Root cause: `capture_lines()`
(`tools/agent-monitoring/manifest.py:69-83`) has the exact same unconditional
`open(agent_monitoring_dir / filename, ...)` pattern over `_FILES_BY_SOURCE` that `_scan_file` has,
and it is not dead code — it is actively used by `tools/agent_replay_codex/containment.py:96` and
`tools/agent_codex_pilot_guardrails/baseline_manifest_gate.py:33` (both wrap it unmodified for a
real append-only-monitoring containment guarantee). Since `manifest.py` is already being pulled into
this ticket's scope specifically to fix its `tools.jsonl`-single-file assumption (Decision 2), and
this is the exact same root defect in the exact same file with a live consumer and a currently-red
test, leaving it broken would mean this ticket claims to fix `manifest.py` while leaving one of its
two file-reading functions still broken. This is not scope creep to an unrelated adjacent problem —
it is the same fix, applied to the file's second function. Pulled into Step 4 below. This is the
final child ticket before one combined PR opens for all 3 children; leaving a freshly-discovered,
already-red, non-xfailed test on the branch at that point would misrepresent the branch as clean.

**Decision 5 (ticket's own open question, ratified) — `query.py`/`validate.py`: confirmed no
functional change needed.** Grepped directly during planning: `query.py` has zero references to
`tools.jsonl`/`tools_file`/`DEFAULT_TOOLS_FILE` anywhere (only `DEFAULT_DB_PATH`, line 25).
`validate.py`'s only 4 matches for the string `tools.jsonl` (lines 152, 157, 186, 201) are all
docstring/display-text labels describing what the `tools` table represents, not file reads —
`compute_drift_report`/`compute_tool_count_drift_report`/`compute_multi_invocation_collision_report`
are pure functions over already-loaded lists; `main()` reads exclusively via
`conn.execute("SELECT raw_json FROM tools ORDER BY id")` against the SQLite index `build_index.py`
populates. Document this finding (Step 7); make no code change to either file.

**Decision 6 — root-level `agent-monitoring/README.md` (path-distinct from
`docs/agent-monitoring/README.md`): DEFERRED, not folded in.** It has the identical stale
single-`tools.jsonl` framing at lines 13, 42, and a `### tools.jsonl` heading at line 44, flagged by
investigation as a same-shaped, closely-related gap. Deferring because: (a) it is outside the
ticket's own `## Related Docs`/`## Scope` list, which names only `docs/`-prefixed files; (b) it does
not start with `docs/`, so `check_docs_to_update_coverage`'s `docs/[^\`]+` path regex would not even
register it as coverable; (c) CLAUDE.md's planning rule is explicit — "Never plan more work than the
ticket scope... note adjacent problems as future tickets, do not add them to this plan." Recommend a
small follow-up hotfix ticket (self-evident intent: reword 3 locations to describe the shard family)
once this batch's PR lands — not blocking, not silently dropped.

**Decision 7 — `docs/parity_ledger/infrastructure.yaml` INFRA-291: update via
`tools/parity_ledger_writer.py`, addendum-style, in this ticket.** Confirmed by direct read
(`docs/parity_ledger/infrastructure.yaml:6390`): `v2_evidence` literally quotes
`` `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` `` as evidence for
`TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE`. Once Step 2 repoints `DEFAULT_TOOLS_FILE`, this
quoted literal becomes factually stale. CLAUDE.md's Authoritative Mechanics Rule requires updating
the parity ledger entry in the same session as the logic change. `INFRA-291` is `P2`, not `P0` — no
gating `test_path` re-run is required by ledger rules — but the update is still owed. This entry
already carries a prior addendum block (the 2026-08-14 TCK-20260811 staleness-check addendum,
`infrastructure.yaml:6472-6488`, inside `text:`) — mirror that established pattern: append a short,
date-stamped addendum noting the new `DEFAULT_TOOLS_FILE` value and that the underlying migration
this entry documents is otherwise unaffected. **Never hand-edit the raw YAML** — this repo has a
documented prior corruption incident from that anti-pattern (see project memory:
`feedback_parity_updater_full_file_yaml_rewrite_risk`); use the sanctioned writer script only. Step 9.

## Steps

### Step 1 — Make `validate.py`'s `load_jsonl` dir-aware (feeds `build_index.py`)
**Files:** `tools/agent-monitoring/validate.py` (function at lines 223-235, confirmed by direct
read)
**Change:** `build_index.py` imports this exact function (`build_index.py:33-38`,
`from validate import (..., load_jsonl)`) and calls it identically for `runs_path`, `events_path`,
and `tools_path` (`build_index.py:175-177`). Add a dir-aware branch **before** the existing
`if not path.exists(): return []` check (a directory *does* satisfy `Path.exists()`, so the branch
order matters — check `is_dir()` first):
```python
def load_jsonl(path):
    if path.is_dir():
        records = []
        for shard in sorted(path.glob("tools-*.jsonl")):
            records.extend(load_jsonl(shard))
        return records
    if not path.exists():
        return []
    records = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"WARNING: {path}:{i}: invalid JSON — {e}", file=sys.stderr)
    return records
```
The recursive `load_jsonl(shard)` call reuses the existing per-line parsing/warning logic unchanged
(each shard is a literal file, so it hits the non-dir branch) — no duplicated parsing logic. Glob is
explicitly `sorted()` per Anti-Drift Hazard 3 (glob order is not filesystem-guaranteed).
**Other writers to this resource:** `load_jsonl` is a pure read function with no writers of its own;
the directory it now optionally globs (`agent-monitoring/tools/`) is written only by
`tools/agent-monitoring/writer.py`/`post_tool_hook.py` (append-only, outside this ticket's scope —
untouched) and by `tools/agent-monitoring/migrate_tools_shards.py` (child ticket 2, already landed,
one-time). No ordering/race concern: this is a read-only consumer invoked on-demand, never
concurrently with a write in the same process.
**Do NOT touch:** the per-line JSON parsing/warning logic in the non-dir branch (unchanged, byte-for-
byte) — only the new `is_dir()` branch is added. Do not widen the glob to `*.jsonl`.
**Verify:** `tests/tools/test_build_index.py`'s full existing suite (all currently-green tests, whose
`_make_corpus()`/`_args()` helpers pass a literal `tmp_path / "tools.jsonl"` file — must stay green
unmodified, since a literal file hits the fallback branch exactly as today) + New Test 1
(`test_build_index_reads_multiple_shard_files_from_directory`) + New Test 2
(`test_build_index_includes_unknown_week_shard`) + New Test 3
(`test_build_index_glob_result_is_sorted`), all in `tests/tools/test_build_index.py` per test_plan.md.

### Step 2 — Repoint `DEFAULT_TOOLS_FILE` in `build_index.py` and `generate_retro.py` to the shard directory
**Files:** `tools/agent-monitoring/build_index.py` (line 44), `tools/agent-monitoring/generate_retro.py`
(line 57)
**Change:** Change both from `Path("agent-monitoring/tools.jsonl")` to `Path("agent-monitoring/tools")`
(the shard directory, no trailing `.jsonl`). `DEFAULT_RUNS_FILE`/`DEFAULT_EVENTS_FILE`
(`build_index.py:42-43`) and `RUNS_FILE`/`EVENTS_FILE` (`generate_retro.py:53-54`) are **left
unchanged** — out of scope. This single-line change, combined with Step 1's dir-aware `load_jsonl`,
automatically fixes three call sites with zero further code change (confirmed by direct read):
`build_index.py`'s `--tools-file` CLI default (`build_index.py:203`); `generate_retro.py`'s
`_load_runs_and_events()`'s on-demand `build_index.build()` call
(`generate_retro.py:98-105`, `tools_file=str(DEFAULT_TOOLS_FILE)` — now resolves to the directory);
and `generate_retro.py`'s `main()` direct read at line 2255 (`all_tools = load_jsonl(DEFAULT_TOOLS_FILE)`,
feeding `_update_index()` and both xfailed tests `test_correlation_real_corpus_produces_a_real_number`
/ `test_parity_index_readpath_call_count_matches_real_corpus_state` — Step 8).
**Other writers to this resource:** none — `DEFAULT_TOOLS_FILE` is a path constant, not a mutable
shared resource; both modules only read through it.
**Do NOT touch:** `RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_RUNS_FILE`/`DEFAULT_EVENTS_FILE` in either file.
**Verify:** `python3 tools/agent-monitoring/build_index.py` (`make agent-monitoring-index`) against
the real corpus produces a `tools` row count equal to the sum across all 14 real shard files (ticket
AC1, literal command).

### Step 3 — Make `generate_retro.py`'s own `load_jsonl` dir-aware, and generalize `_index_is_stale()` to multi-shard max-mtime
**Files:** `tools/agent-monitoring/generate_retro.py` (`load_jsonl` at lines 64-67,
`_index_is_stale` at lines 70-81, both confirmed by direct read)
**Change:** `generate_retro.py` defines its **own separate** `load_jsonl` (not the one imported from
`validate.py` that `build_index.py` uses — confirmed two independent definitions exist,
investigation.md Risk 2). Apply the identical dir-aware branch as Step 1, mirrored, not
consolidated (per Out-of-Scope: "do not re-derive... normalization logic already centralized" — this
ticket adds the same small branch twice rather than restructuring which file owns canonical logic):
```python
def load_jsonl(path):
    if path.is_dir():
        records = []
        for shard in sorted(path.glob("tools-*.jsonl")):
            records.extend(load_jsonl(shard))
        return records
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
```
Then generalize `_index_is_stale()`. Current code (confirmed, lines 70-81) does a single
`.stat().st_mtime` per source; with `DEFAULT_TOOLS_FILE` now a directory, using the directory's own
`.stat().st_mtime` would be wrong (Anti-Drift Hazard 6 — a directory's mtime does not reliably
update when an existing file inside it is appended to, only on create/remove). Add a small dual-mode
helper and use it for all three sources (symmetric with the file case, no behavior change for
`RUNS_FILE`/`EVENTS_FILE` which are never directories):
```python
def _source_mtime(source):
    """Newest relevant mtime for a source: max shard mtime if `source` is a directory
    (the sharded tools/ family), else the file's own mtime if it exists, else None."""
    if source.is_dir():
        shard_mtimes = [f.stat().st_mtime for f in source.glob("tools-*.jsonl")]
        return max(shard_mtimes) if shard_mtimes else None
    if source.exists():
        return source.stat().st_mtime
    return None


def _index_is_stale(db_path):
    if not db_path.exists():
        return True
    db_mtime = db_path.stat().st_mtime
    for source in (RUNS_FILE, EVENTS_FILE, DEFAULT_TOOLS_FILE):
        mtime = _source_mtime(source)
        if mtime is not None and mtime > db_mtime:
            return True
    return False
```
(Sorting is not needed inside `_source_mtime` — only `max()` is computed, no ordering requirement.)
**Other writers to this resource:** `agent-monitoring-index/monitoring.db` (the file `db_path` names)
is written only by `build_index.build()` (full-rebuild-only, confirmed by `build_index.py`'s own
module docstring, "Full-rebuild-only, on-demand only... no incremental-build mode exists here,
ever"), invoked either directly (`make agent-monitoring-index`) or on-demand from
`_load_runs_and_events()` (this same file, line ~94-105) when `_index_is_stale()` returns `True`. No
other writer exists. Reading `db_path.stat().st_mtime` immediately before a possible rebuild (as the
existing code already does) is unaffected by this change — only the *source*-side mtime computation
changes.
**Do NOT touch:** `_load_runs_and_events()`'s overall try/except/fallback structure (lines 84-120,
unchanged) — only `_index_is_stale()`'s internals and the new `_source_mtime()` helper are added.
**Verify:** the 3 existing tests that monkeypatch `DEFAULT_TOOLS_FILE` to a single tmp file
(`test_generate_retro_builds_index_on_demand_when_missing`,
`test_generate_retro_rebuilds_stale_index_not_just_missing_index`,
`test_index_is_stale_false_when_index_newer_than_all_sources`,
`tests/tools/test_generate_retro.py:896-986`) stay green unmodified (literal file hits the non-dir
branch exactly as today) + New Test 4
(`test_generate_retro_index_is_stale_detects_write_to_non_newest_shard`, per test_plan.md: monkeypatch
`DEFAULT_TOOLS_FILE` to a tmp directory with 2+ shard files, build the index, append a row to the
*older*-named shard, touch its mtime, assert `_index_is_stale()` returns `True`) + New Test 5
(`test_generate_retro_load_jsonl_globs_shard_directory`) — ticket AC3.

### Step 4 — Fix `manifest.py`: aggregate the `tools` source across shards in `_scan_file`/`build_manifest`, and fix `capture_lines()` the same way
**Files:** `tools/agent-monitoring/manifest.py` (`_scan_file` lines 30-59, `build_manifest` lines
62-66, `capture_lines` lines 69-83, all confirmed by direct read)
**Change (build_manifest/_scan_file path):** `_FILES_BY_SOURCE` (lines 23-27) stays **unchanged** —
the output record for the tools source must still be labeled `"tools.jsonl"` (hard constraint from
`test_build_manifest_shape_against_real_corpus`'s `set(filenames) == {"events.jsonl", "runs.jsonl",
"tools.jsonl"}` assertion — Anti-Drift Hazard 4). Refactor `_scan_file`'s inner per-line streaming
loop into a shared helper both the single-file and multi-shard paths call, so the AST guard
(`test_manifest_source_never_calls_full_file_read_methods`, bans `read_text`/`read_bytes`/
`readlines`/`read` anywhere in the file) stays satisfied by construction — only `open(..., "rb")` +
line iteration is used, in both places:
```python
def _stream_file_into(path: Path, source: str, hasher, counts: dict) -> None:
    with open(path, "rb") as f:
        for line_bytes in f:
            hasher.update(line_bytes)
            stripped = line_bytes.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                counts["parse_errors"] += 1
                continue
            counts["parsed_ok"] += 1
            labels = classify_provenance(record, source)
            if labels and labels != frozenset({"interactive_null"}):
                counts["legacy_warning_count"] += 1


def _scan_file(path: Path, source: str) -> dict:
    hasher = hashlib.sha256()
    counts = {"parsed_ok": 0, "parse_errors": 0, "legacy_warning_count": 0}
    _stream_file_into(path, source, hasher, counts)
    return {
        "file": path.name,
        "line_count": counts["parsed_ok"] + counts["parse_errors"],
        "byte_size": path.stat().st_size,
        "sha256": hasher.hexdigest(),
        "parser_result": {"parsed_ok": counts["parsed_ok"], "parse_errors": counts["parse_errors"]},
        "legacy_warning_count": counts["legacy_warning_count"],
    }


def _scan_tools_shards(tools_dir: Path, source: str) -> dict:
    hasher = hashlib.sha256()
    counts = {"parsed_ok": 0, "parse_errors": 0, "legacy_warning_count": 0}
    byte_size = 0
    for shard in sorted(tools_dir.glob("tools-*.jsonl")):
        _stream_file_into(shard, source, hasher, counts)
        byte_size += shard.stat().st_size
    return {
        "file": "tools.jsonl",
        "line_count": counts["parsed_ok"] + counts["parse_errors"],
        "byte_size": byte_size,
        "sha256": hasher.hexdigest(),
        "parser_result": {"parsed_ok": counts["parsed_ok"], "parse_errors": counts["parse_errors"]},
        "legacy_warning_count": counts["legacy_warning_count"],
    }


def build_manifest(agent_monitoring_dir: Path) -> list:
    records = []
    for filename, source in sorted(_FILES_BY_SOURCE.items()):
        if source == "tools":
            records.append(_scan_tools_shards(agent_monitoring_dir / "tools", source))
        else:
            records.append(_scan_file(agent_monitoring_dir / filename, source))
    return records
```
The output record shape, key set, and `"tools.jsonl"` filename label are byte-identical to today's
single-file output shape — only the source producing `line_count`/`byte_size`/`sha256`/
`parser_result`/`legacy_warning_count` is now an aggregate across shards, streamed in
filename-sorted order (Anti-Drift Hazard 3 — sortedness is required for
`test_manifest_cli_reproducible_byte_identical_across_two_runs` and
`test_build_manifest_reproducible_byte_identical_direct_call` to pass, since the running
`hashlib.sha256()` accumulates across shard boundaries in that exact order).

**Change (capture_lines path — Decision 4, discovered during planning, confirmed currently broken by
running the real test):** `capture_lines()` (lines 69-83) has its own separate unconditional-open
loop over `_FILES_BY_SOURCE`, independent of `_scan_file`/`build_manifest`. It needs the same
dual-mode treatment (directory-of-shards vs. literal single file) because
`tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`'s
`_monitoring_dir()` fixture (lines 17-22) writes a literal `tools.jsonl` **file** into a synthetic
`agent-monitoring/` dir for 3 currently-passing tests — a bare "always treat as shard dir" fix would
break those:
```python
def capture_lines(agent_monitoring_dir: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for filename in _FILES_BY_SOURCE:
        if filename == "tools.jsonl":
            tools_dir = agent_monitoring_dir / "tools"
            if tools_dir.is_dir():
                lines: list[str] = []
                for shard in sorted(tools_dir.glob("tools-*.jsonl")):
                    with open(shard, "r", encoding="utf-8") as file:
                        for line in file:
                            lines.append(line)
                result[filename] = lines
                continue
        path = agent_monitoring_dir / filename
        lines: list[str] = []
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                lines.append(line)
        result[filename] = lines
    return result
```
Result stays keyed by the literal string `"tools.jsonl"` (not `"tools"` or a shard name) — required
so `assert_prefix_preserved()` (lines 86-94, unchanged, matches `pre`/`post` dicts by filename key)
and the 2 downstream consumers (`tools/agent_replay_codex/containment.py:96`,
`tools/agent_codex_pilot_guardrails/baseline_manifest_gate.py:33`, both call `capture_lines`
unmodified) keep working against the same key shape.
**Other writers to this resource:** `_AGENT_MONITORING_DIR`/`agent_monitoring_dir` here is read-only
in both functions — the only writers to the real `agent-monitoring/tools/` directory are the
append-only writer path (`writer.py`/`post_tool_hook.py`, out of scope, untouched) and child ticket
2's already-landed one-time migration script. `capture_lines()`'s own docstring-stated contract
("never writes") is unaffected; this is a pure read-path fix.
**Do NOT touch:** `assert_prefix_preserved()` (lines 86-94), `_assert_safe_output_path()` (lines
97-104), `main()` (lines 107-119) — none reference the retired path, none need changes. Do not emit
one manifest record per shard file (Anti-Drift Hazard 4).
**Verify:** New Test 6 (`test_manifest_tools_source_aggregates_all_shards`) + New Test 7
(`test_manifest_tools_source_sha256_is_order_stable_across_shards`), both in
`tests/tools/test_agent_monitoring_manifest.py` per test_plan.md, plus re-running
`test_manifest_source_never_calls_full_file_read_methods` (existing, unaffected by construction) —
AND `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py::test_capture_lines_reads_all_three_monitoring_files`
(currently red on this branch — must go green) plus its 3 sibling tests in the same file (currently
green via the literal-file fixture — must stay green).

### Step 5 — Un-xfail and verify the 4 `manifest.py` xfailed tests
**Files:** `tests/tools/test_agent_monitoring_manifest.py` (no production code in this step — Step 4
already landed the fix)
**Change:** Remove `@pytest.mark.xfail(reason=_XFAIL_TOOLS_JSONL_RETIRED_REASON, strict=True)` from
the 3 tests whose bodies need no further change once Step 4 lands
(`test_build_manifest_shape_against_real_corpus` line 42,
`test_manifest_cli_reproducible_byte_identical_across_two_runs` line 69,
`test_build_manifest_reproducible_byte_identical_direct_call` line 82). Confirm `_XFAIL_TOOLS_JSONL_RETIRED_REASON`
(lines 30-35) becomes unused and remove it once all 4 manifest xfails referencing it are gone (see
Step 6 for the 4th, which additionally needs its own test-helper fix).
**Do NOT touch:** the test bodies themselves — only the decorator lines and the now-dead reason
constant.
**Verify:** `pytest tests/tools/test_agent_monitoring_manifest.py -v -rA` shows these 3 as genuine
`PASSED`, zero `XFAIL`/`XPASS`/`error`.

### Step 6 — Fix the 2 test-helper functions that independently hardcode the retired path
**Files:** `tests/tools/test_agent_monitoring_manifest.py` (`_content_hash_snapshot()`/
`_WATCHED_JSONL_FILES`), `tests/tools/test_skill_usage_metric.py` (`_independently_derive_counts()`/
`_REAL_TOOLS_FILE`)
**Change:** These are test-*helper* functions, not the test bodies under the ticket's Out-of-Scope
guard against "re-deriving normalization logic" — this is legitimate test-fixture maintenance
required to make the assertion meaningful again (investigation.md Risk 5), not a workaround.

`test_agent_monitoring_manifest.py`'s `_content_hash_snapshot()` (lines 121-127, confirmed by direct
read) currently does `path.read_bytes()` per filename in `_WATCHED_JSONL_FILES = ["events.jsonl",
"runs.jsonl", "tools.jsonl"]` (line 28) against `_REAL_AGENT_MONITORING_DIR`. Since this helper only
ever runs against the real corpus (never a synthetic fixture), update it directly (no dual-mode
needed):
```python
def _content_hash_snapshot() -> str:
    hasher = hashlib.sha256()
    for filename in _WATCHED_JSONL_FILES:
        hasher.update(filename.encode("utf-8"))
        if filename == "tools.jsonl":
            tools_dir = _REAL_AGENT_MONITORING_DIR / "tools"
            for shard in sorted(tools_dir.glob("tools-*.jsonl")):
                hasher.update(shard.read_bytes())
            continue
        path = _REAL_AGENT_MONITORING_DIR / filename
        hasher.update(path.read_bytes())
    return hasher.hexdigest()
```
(`read_bytes()` here is fine — the AST full-read-method guard applies only to `manifest.py`'s own
source, not to this test file.) This is the helper that feeds `test_manifest_run_against_real_corpus_produces_zero_diff`
(the 4th manifest xfail); remove its `@pytest.mark.xfail` (line 130) once this lands.

`test_skill_usage_metric.py`'s `_independently_derive_counts()` (lines 133-152, confirmed by direct
read) currently does `with open(_REAL_TOOLS_FILE, encoding="utf-8") as f:` where
`_REAL_TOOLS_FILE = _REAL_AGENT_MONITORING_DIR / "tools.jsonl"` (line 23). Change the constant and
the open loop:
```python
_REAL_TOOLS_DIR = _REAL_AGENT_MONITORING_DIR / "tools"
```
```python
def _independently_derive_counts() -> dict:
    counts: dict = {}
    pattern = re.compile(r"'skill':\s*'([^']*)'")
    for shard in sorted(_REAL_TOOLS_DIR.glob("tools-*.jsonl")):
        with open(shard, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("tool") != "Skill":
                    continue
                m = pattern.search(rec.get("input_summary", ""))
                if m:
                    counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return counts
```
Remove `@pytest.mark.xfail` (line 155) from `test_live_corpus_matches_independently_derived_counts`
(line 165) once this lands — this is the 5th of the 7 named xfails, and the only one whose
production-side dependency is entirely Step 2/3's `generate_retro.py` fix (per Decision 3), not any
change to `skill_usage_metric.py` itself.
**Other writers to this resource:** none — both are read-only test helpers against the committed,
static real corpus.
**Do NOT touch:** the test *assertion* bodies (`assert output_1 == output_2` /
`assert report["per_skill"] == expected` etc.) — unchanged; only the fixture-construction helpers
that feed them.
**Verify:** `test_manifest_run_against_real_corpus_produces_zero_diff` and
`test_live_corpus_matches_independently_derived_counts` both show genuine `PASSED`, zero `XFAIL`.

### Step 7 — Document `query.py`/`validate.py`'s confirmed no-op status
**Files:** ticket's `## Implementation Notes` section (`tickets/inprogress/TCK-20260902-MONITORING-SHARD-CONSUMERS.md`)
**Change:** No production code change. Record Decision 5's finding verbatim in the ticket's
Implementation Notes at Finalize time: both files were grepped directly, confirmed to reference only
`DEFAULT_DB_PATH`, and both suites (`tests/tools/test_query.py`,
`tests/tools/test_validate_agent_monitoring.py`) are expected to pass with zero code changes.
**Do NOT touch:** `query.py`, `validate.py` — zero diff expected in both files this ticket.
**Verify:** `pytest tests/tools/test_query.py tests/tools/test_validate_agent_monitoring.py -v`
passes unmodified (ticket AC4, AC5) + `git diff --stat -- tools/agent-monitoring/query.py
tools/agent-monitoring/validate.py` shows zero output.

### Step 8 — Un-xfail and verify the 2 `generate_retro.py` xfailed tests
**Files:** `tests/tools/test_generate_retro.py` (no production code in this step — Steps 2/3 already
landed the fix)
**Change:** Remove `@pytest.mark.xfail(...)` (lines 2209-2216) from
`test_correlation_real_corpus_produces_a_real_number` (line 2217) and `@pytest.mark.xfail(...)`
(lines 2230-2237) from `test_parity_index_readpath_call_count_matches_real_corpus_state` (line 2238).
No test-body change needed for either — confirmed by direct read: both call
`generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)`/`generate_retro.EVENTS_FILE`
directly, which Steps 2/3 already fix. Test 2's pinned expected value (`result["count"] == 4`) is a
fixed historical fact about already-migrated, byte-preserved data (4 confirmed real historical
`parity_index.py` Bash calls, per the test's own inline comment) — if it does not equal 4 after the
fix, that signals a real bug in the glob/aggregation logic (e.g. a shard silently skipped), not
legitimate new drift requiring a baseline bump; investigate before assuming the pinned value needs
changing (test_plan.md's explicit instruction).
**Do NOT touch:** the assertion bodies or the pinned `== 4` value.
**Verify:** both tests show genuine `PASSED`, zero `XFAIL`.

### Step 9 — Doc updates
**Files:** `docs/agent-monitoring/schema.md` (line 30), `docs/agent-monitoring/README.md` (lines
19-21, 54, 148), `docs/ai/system_overview.md` (lines 231-244)
**Change:**
- `docs/agent-monitoring/schema.md:30` — reword `"(any of runs.jsonl/events.jsonl/tools.jsonl has a
  newer mtime than the index —"` to describe the multi-shard comparison: the `tools` source now
  compares against the newest of all `agent-monitoring/tools/tools-*.jsonl` shard files' mtimes, not
  one file's mtime. This is the build-index staleness-check paragraph; child ticket 1's own doc
  update covered the *write-path* section of this same file, not this paragraph — confirmed distinct
  by line number.
- `docs/agent-monitoring/README.md` — line 19-21's "What It Captures" bullets currently cite
  `(tools.jsonl)` alongside `runs.jsonl`/`events.jsonl` in identical parenthetical-filename style;
  reword the tools bullet to name the `agent-monitoring/tools/tools-YYYY-Www.jsonl` shard family
  instead of one physical file, while leaving the `runs.jsonl`/`events.jsonl` bullets untouched (they
  remain genuinely single files). Line 54's "same `runs.jsonl`/`events.jsonl`/`tools.jsonl` sources"
  phrase — reword similarly. Line 148's Navigation table entry ("Full field reference for
  runs.jsonl, events.jsonl, and tools.jsonl") — reword to name the shard family for the tools part
  (this is the ticket's own named example).
- `docs/ai/system_overview.md:231-244` §6 — currently states "Agent activity is recorded in 3
  append-only JSONL files under `agent-monitoring/`" (line 231) and lists `tools.jsonl` (line 242) as
  a third physical sibling file with a physical-record description. Reword to describe 2 single files
  (`runs.jsonl`, `events.jsonl`) plus the `agent-monitoring/tools/tools-YYYY-Www.jsonl` shard family
  — this is the most literal "3 files" claim in scope and must not continue asserting a single
  physical `tools.jsonl`.
- `docs/guides/agent_monitoring.md` — **confirmed excluded, no change** (Decision ratified from
  investigation): its 2 references (lines 218, 262) are logical/conceptual ("`tools.jsonl` rows"),
  matching the retained historical/logical naming convention `docs/agent-monitoring/schema.md` itself
  keeps under its own `## agent-monitoring/tools.jsonl` heading even after documenting the sharded
  physical layout in the same section (schema.md line 337). Neither line claims a physical
  single-file storage location.
**Do NOT touch:** `docs/agent-monitoring/schema.md`'s `## agent-monitoring/tools.jsonl` heading text
itself (line 337 area) or its already-updated write-path section (child ticket 1's territory) — only
the staleness-check paragraph at line 30. Do not touch `agent-monitoring/README.md` (root-level,
Decision 6 — deferred).
**Verify:** `grep -rn "3 append-only JSONL" docs/ai/system_overview.md` returns no match; manual read
confirms all 3 in-scope docs no longer describe `tools.jsonl` as a single physical file (ticket AC6).

### Step 10 — Parity ledger addendum for INFRA-291
**Files:** `docs/parity_ledger/infrastructure.yaml` (`INFRA-291` entry, `v2_evidence` field at line
6390, confirmed by direct read)
**Change:** Use `tools/parity_ledger_writer.py` (never a raw YAML edit) to append a short,
date-stamped addendum to `INFRA-291`'s `v2_evidence` (or `text`, mirroring the entry's own existing
2026-08-14 addendum pattern at `text:` lines ~6472-6488) noting: `DEFAULT_TOOLS_FILE` was repointed
from `Path("agent-monitoring/tools.jsonl")` to `Path("agent-monitoring/tools")` (a shard directory)
by `TCK-20260902-MONITORING-SHARD-CONSUMERS`, `load_jsonl` became dir-aware, and the underlying
migration this entry documents (`_load_runs_and_events()`'s index-on-demand-build/fallback shape) is
otherwise unaffected — this is a file-resolution-layer change only, per Decision 7. Status stays
`verified` (unaffected), priority stays `P2`.
**Other writers to this resource:** `docs/parity_ledger/infrastructure.yaml` is a single YAML file
also touched by other tickets' parity-updater runs at unrelated entry IDs — using
`tools/parity_ledger_writer.py` (schema-validating, single-entry-scoped) rather than a raw file edit
avoids clobbering concurrent unrelated entries or corrupting the file structure.
**Do NOT touch:** any other `INFRA-*` entry in this file, including `INFRA-289`/`INFRA-290`/`INFRA-333`
(checked during investigation, confirmed unaffected — none cites a literal `tools.jsonl` path value
that changes).
**Verify:** `python3 tools/parity_index.py health` (or equivalent ledger-schema validation) shows no
new errors; `git diff -- docs/parity_ledger/infrastructure.yaml` shows a scoped addition only to
`INFRA-291`.

### Step 11 — Full xfail-removal confirmation pass and gate-integrity re-checks
**Files:** none (verification-only step)
**Change:** N/A.
**Do NOT touch:** anything — this step is read-only verification.
**Verify:** run all of test_plan.md's Scoped Pytest Commands, in particular:
```bash
pytest tests/tools/test_agent_monitoring_manifest.py tests/tools/test_skill_usage_metric.py \
       tests/tools/test_generate_retro.py -v -rA | grep -E "XFAIL|XPASS|PASSED.*(manifest|skill_usage|correlation_real_corpus|parity_index_readpath_call_count)"
```
must show **zero** `XFAIL`/`XPASS`/`error` lines and genuine `PASSED` for all 7 previously-xfailed
tests. Additionally re-run (per test_plan.md's Anti-Drift Test Guards):
`test_build_index_never_touches_write_path_modules`,
`test_manifest_source_never_calls_full_file_read_methods`,
`test_reuses_generate_retro_loader_not_a_second_loader`,
`TestReadOnlyGuarantee::test_source_jsonl_files_byte_identical_after_build`, and the manifest suite's
zero-mutation tests. Also re-run
`tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py` in full (all 4
tests, including the previously-red `test_capture_lines_reads_all_three_monitoring_files`) and
`git diff --stat -- tools/gate_checks/done_checker_static.py` (must show zero output, ticket AC7).

## Scope Guards

- Do not change `build_index.py`'s table schema (`runs`/`events`/`tools` tables) — only source-file
  resolution changes (ticket Out of Scope).
- Do not touch `tools/gate_checks/done_checker_static.py` — confirmed zero references to
  `tools.jsonl` in any form; touching it fails the ticket's own AC7.
- Do not re-derive `_resolve_status()`, `_is_legacy_event()`, `_is_gate_fail()`, or any other
  normalization logic already centralized in `build_index.py`/`generate_retro.py` — file
  *resolution* only.
- Do not touch `runs.jsonl`/`events.jsonl` reading logic in any of the files this ticket touches —
  those remain single physical files, unaffected by this migration.
- Do not widen any glob beyond `tools-*.jsonl` (never `*.jsonl`).
- Do not filter out or special-case `tools-unknown-week.jsonl` anywhere.
- Do not change `manifest.py`'s 3-record output shape or the literal `"tools.jsonl"` filename label
  on the aggregate record.
- Do not consolidate `build_index.py`'s (via `validate.py`) and `generate_retro.py`'s separate
  `load_jsonl` definitions into one shared function — mirror the same small branch in both
  (Decision/Risk 2 from investigation.md); a larger refactor is out of scope.
- Do not use a directory's own mtime as a staleness-check shortcut — must be `max()` over each shard
  file's individual mtime.
- Do not touch `query.py` or `validate.py` production code — confirmed no-op (Decision 5).
- Do not fold in `agent-monitoring/README.md` (root-level) doc fixes — deferred (Decision 6).
- Do not hand-edit `docs/parity_ledger/infrastructure.yaml` directly — use
  `tools/parity_ledger_writer.py` only (Decision 7).
- Do not edit any of the 7 xfailed tests' *assertion* bodies to make them pass — only remove the
  `@pytest.mark.xfail` decorator once the underlying production code and/or test-helper fixture
  genuinely fixes the condition being tested (Gate Integrity rule).

## Dependency Map

- Step 1 (validate.py `load_jsonl`) and Step 3 (generate_retro.py `load_jsonl` + `_index_is_stale`)
  are independent of each other (separate functions in separate files) but both depend on Step 2
  (the `DEFAULT_TOOLS_FILE` repoint) landing first in their respective file, since the dir-aware
  branch is inert until the default actually points at a directory in real usage. In practice, Steps
  1+2 (build_index.py's side) and Step 2+3 (generate_retro.py's side) should land together per file.
- Step 4 (manifest.py) is fully independent of Steps 1-3 — separate file, separate `load_jsonl`
  entirely (manifest.py does not import or call `load_jsonl` at all).
- Step 5 depends on Step 4 (manifest.py fix) landing first.
- Step 6 depends on Step 2+3 (for the skill-usage test helper) and Step 4 (for the manifest test
  helper) landing first.
- Step 7 has no code dependency — pure documentation/verification, can run any time.
- Step 8 depends on Step 2+3 landing first.
- Step 9 (docs) depends on Steps 1-4 conceptually (describes the shipped behavior) but has no code
  dependency — can be written in parallel and reviewed against the final implementation before
  Finalize.
- Step 10 (parity ledger) depends on Step 2 (the literal old-path quote it corrects) but not on any
  other step.
- Step 11 must run last — it is the final verification gate and depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `python3 tools/agent-monitoring/build_index.py` builds `tools` table from all shard files, row count = sum across shards | Steps 1, 2 | `make agent-monitoring-index` run against real corpus (Step 2's Verify) + New Test 1 |
| Test simulates 2+ shard files, confirms `build_index.py` reads all of them | Steps 1, 2 | New Test 1 (`test_build_index_reads_multiple_shard_files_from_directory`) |
| `generate_retro.py`'s on-demand build + staleness check detect a newly appended row in ANY shard, not only the newest-named one | Step 3 | New Test 4 (`test_generate_retro_index_is_stale_detects_write_to_non_newest_shard`) |
| `query.py`'s existing test suite still passes unmodified | Step 7 (no-op, documented) | `pytest tests/tools/test_query.py` (zero changes) |
| `validate.py`'s drift-report functions produce identical results on the sharded corpus | Step 7 (no-op, documented) | `pytest tests/tools/test_validate_agent_monitoring.py` (zero changes) |
| `docs/agent-monitoring/README.md`, `schema.md`, `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md` §6 no longer describe `tools.jsonl` as a single physical file | Step 9 | manual read + grep check |
| `tools/gate_checks/done_checker_static.py` has zero diff | (untouched by design) | `git diff --stat -- tools/gate_checks/done_checker_static.py` (Step 11) |
| **(Implicit AC, ticket's own stated primary success condition)** all 7 xfail markers removed, all 7 tests genuinely pass | Steps 4, 5, 6, 8 | Step 11's full xfail-removal confirmation pass |

## Anti-Drift Notes

1. **This is the branch's final child ticket before one combined PR opens covering all 3 children.**
   Finalize/Verify for this ticket must independently re-run all 7 previously-xfailed tests
   (`test_build_manifest_shape_against_real_corpus`,
   `test_manifest_cli_reproducible_byte_identical_across_two_runs`,
   `test_build_manifest_reproducible_byte_identical_direct_call`,
   `test_manifest_run_against_real_corpus_produces_zero_diff`,
   `test_live_corpus_matches_independently_derived_counts`,
   `test_correlation_real_corpus_produces_a_real_number`,
   `test_parity_index_readpath_call_count_matches_real_corpus_state`) and confirm **zero**
   `xfail`/`error`/`failed` remain — all must show genuine `passed`. Child 2's own plan.md staked its
   hard release gate on this being true after this ticket lands; do not report this ticket done
   without that confirmation run's actual output in hand.
2. **`tools-unknown-week.jsonl` is real data, never a sentinel to filter.** Every glob site
   (`build_index.py` via Step 1, `generate_retro.py` via Step 3, `manifest.py` via Step 4) must
   include it identically to any dated shard.
3. **Glob determinism is required at every site, not optional.** `Path.glob()` does not guarantee
   sorted order across all filesystems/Python versions — every glob call in Steps 1, 3, 4 must be
   wrapped in `sorted(...)` explicitly. This is load-bearing for reproducibility tests
   (`test_manifest_cli_reproducible_byte_identical_across_two_runs`,
   `test_build_manifest_reproducible_byte_identical_direct_call`,
   `test_build_index_glob_result_is_sorted`) and for the SHA-256 hash in `manifest.py`'s aggregate
   record to be well-defined at all (a running hasher over an unsorted glob would be
   non-deterministic).
4. **Directory mtime is not a valid staleness proxy.** `_index_is_stale()`'s fix (Step 3) must use
   `max()` over each shard file's individual mtime — never the shard directory's own `.stat().st_mtime`
   — because a directory's mtime does not reliably update when an existing file inside it is appended
   to on all filesystems, only on file create/remove. Using it as a shortcut would silently
   reintroduce exactly the staleness bug class `TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS`
   was built to prevent.
5. **The `capture_lines()` fix (Step 4, Decision 4) was not in any prior artifact for this ticket** —
   discovered live during planning by actually running
   `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py` against this
   branch, not by reading investigation.md (which flagged `capture_lines()` as "unconfirmed, Plan
   should check" but did not itself run the test). Do not skip Step 4's `capture_lines()` half on the
   assumption that only `_scan_file`/`build_manifest` needed fixing — both are real, independent
   unconditional-open call sites in the same file.
6. **Dual-mode (dir-or-file) resolution is the load-bearing design choice threaded through every
   step.** It is what keeps every currently-green test that constructs a literal single `tools.jsonl`
   tmp file passing unmodified (`test_build_index.py`'s full suite, 3 named `test_generate_retro.py`
   tests, `test_containment_append_only_monitoring.py`'s 3 synthetic-fixture tests). Do not simplify
   any of the four dual-mode implementations (Steps 1, 3, 4×2) down to "always assume a directory" —
   that would silently break all of the above.
7. **Do not treat Decision 6 (deferring `agent-monitoring/README.md`) as license to defer anything
   else flagged in this plan.** It is deferred specifically because it sits outside both the ticket's
   own doc list and the machine-checked coverage regex — every other doc/code change in this plan is
   in scope and must land.

## Deviations (recorded during Implement)

1. **Step 7's "zero diff" framing for `validate.py` was internally inconsistent with Step 1 and has
   been corrected in practice, not silently followed.** Step 1 (this same plan.md, above) explicitly
   and necessarily adds a 5-line dir-aware branch to `validate.py`'s `load_jsonl()` — required because
   `build_index.py` imports that exact function (`from validate import (..., load_jsonl)`) and calls
   it for `tools_path`; without this change, Step 2's `DEFAULT_TOOLS_FILE` repoint to a directory
   would make `build_index.py` silently produce an empty `tools` table forever (`path.exists()` is
   `True` for a directory, but the un-fixed function had no dir-handling branch, so `read_text()`
   would raise `IsADirectoryError`). Step 7's own "Do NOT touch: query.py, validate.py — zero diff
   expected in both files this ticket" line, and its verify command
   (`git diff --stat -- tools/agent-monitoring/query.py tools/agent-monitoring/validate.py` shows
   zero output), directly contradict Step 1's own explicit instruction to modify `validate.py`.
   Resolution: Decision 5's actual finding (and the ticket's own AC4/AC5 wording) is about
   `query.py` having zero references at all, and about `validate.py`'s three *report* functions
   (`compute_drift_report`/`compute_tool_count_drift_report`/`compute_multi_invocation_collision_report`)
   needing no change — not about `validate.py`'s `load_jsonl()`, a separate function Step 1 correctly
   and necessarily touches. Confirmed post-implementation: `git diff --stat -- tools/agent-monitoring/query.py`
   is empty (true zero-diff, as both Step 7 and Decision 5 state); `git diff --stat -- tools/agent-monitoring/validate.py`
   shows a 5-line insertion (Step 1's dir-aware branch only — `compute_drift_report`/
   `compute_tool_count_drift_report`/`compute_multi_invocation_collision_report` are byte-identical,
   confirmed by `tests/tools/test_validate_agent_monitoring.py`'s full suite passing unmodified,
   including its `TestRegressionParity` pre/post-migration byte-identical-output tests). No ticket AC
   is violated by this: AC4 (query.py's test suite passes unmodified) and AC5 (validate.py's
   drift-report functions produce identical results) both hold. Only AC7 (which names
   `tools/gate_checks/done_checker_static.py`, not `validate.py`) has a genuine zero-diff
   requirement, and that file is confirmed untouched.
2. **`docs/agent-monitoring/schema.md`'s "Join Example" code snippet (around line 446) was fixed in
   addition to the line-30 staleness paragraph Step 9 explicitly named.** Not called out by
   investigation.md or plan.md's Step 9 file/line list, but it is squarely within the ticket's own
   Scope text ("any remaining single-file framing... in schema.md") — the snippet literally did
   `Path('agent-monitoring/tools.jsonl').read_text()`, which is now stale/would raise
   `FileNotFoundError` if actually run, and the ticket's AC6 requires schema.md to "no longer
   describe `tools.jsonl` as a single physical file." Updated to iterate
   `sorted(Path('agent-monitoring/tools').glob('tools-*.jsonl'))`, matching the module's own
   dir-aware pattern. This is the same category of fix Step 9 already performs elsewhere in the same
   file, not a new scope area.
