---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY
artifact_type: plan
tags: [agent-monitoring, observability, hooks, data-quality]
---

# Implementation Plan — TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY

## Summary

Cut all three `agent-monitoring/` writers (`post_tool_hook.py`, `record_run.py`,
`record_events.py`) over to the unified `agent-monitoring/data/<ISO-week>/{tools,runs,events}.jsonl`
layout, and fix `record_events.py`'s silently-broken `TOOLS_FILE` read (a dangling reference to a
file `TCK-20260902-MONITORING-SHARD-MIGRATION` `git rm`'d on 2026-09-02, currently making every
`implement-ticket`-workflow event's `tool_call_count`/`cost_proxy_score` compute as `0`/`0.0`). The
approach is six narrow, independently verifiable steps: one per writer's path-template change
(post_tool_hook.py, record_run.py, record_events.py's `EVENTS_FILE`), one dedicated step for the
critical `TOOLS_FILE` → multi-week-glob bug fix, one for `.gitattributes`, and one for
`docs/agent-monitoring/schema.md`. Every writer step keeps its own pre-`write_line`/`write_lines`
`mkdir(parents=True, exist_ok=True)` call (load-bearing per `writer.py:113-120`'s lock-before-mkdir
ordering) and, for `post_tool_hook.py`, stays textually inside the existing outer
`try/except Exception: pass` block. Two decisions the ticket left open are ratified below rather
than re-opened: `runs.jsonl` uses write-time ("now") ISO-week bucketing, and the `schema.md` worked
join-example snippet is fixed in this ticket rather than deferred to child 7.

## Ratified Decisions

**Decision 5 — `runs.jsonl` bucketing: write-time ("now"), not `start_ts`.** Ratifying the
ticket's recommended default and investigation's finding (`investigation.md` "Risks and Open
Questions" first bullet): every real `record_run.py` call site
(`.claude/workflows/implement-ticket.js:390`, plus `implement-epic.js`, `create-tickets.js`,
`simq-audit.js`, and each script's early-failure fallback paths) invokes it at/near the run's
actual end, while `start_ts` is captured much earlier and can diverge by the run's full duration
for a long-running or paused/resumed run. Write-time bucketing puts a run's record in the week a
retro consumer covering "runs that finished this week" would actually look in, matches
`post_tool_hook.py`'s existing precedent (each tool call bucketed by when it physically happened),
and matches `record_events.py`'s ticket-mandated write-time behavior (not left open, unlike
`runs.jsonl`). For the early-failure fallback paths, `start_ts == end_ts` (same literal timestamp
variable), so the two bucketing choices are identical there — zero regression risk either way.
**Decided: write-time.**

**Decision 7 — `schema.md` worked join-example (lines 430-459): fix in this ticket, not child 7.**
Accepting investigation's recommendation. The snippet under "Join Example" reads
`Path('agent-monitoring/runs.jsonl')`, `Path('agent-monitoring/events.jsonl')`, and
`Path('agent-monitoring/tools').glob('tools-*.jsonl')` directly (confirmed at those exact lines by
direct read in Step 6 below) — all three become actively wrong, not merely stale, the moment this
ticket's cutover lands: a reader who copy-pastes it gets empty results, not slightly-outdated
results. This is the same file and the same "per-source write path" concern the ticket's own scope
item already covers (`docs/agent-monitoring/schema.md`'s per-source sections), not a broader sweep
into unrelated docs — child 7's scope is the broader docs/CLAUDE.md/skill sweep beyond this file's
write-path paragraphs. **Decided: fix the worked example in Step 6 below.**

## Steps

### Step 1 — post_tool_hook.py: write target → agent-monitoring/data/<week>/tools.jsonl

**Files:** `tools/agent-monitoring/post_tool_hook.py`, `tests/tools/test_post_tool_hook.py`

**Change:** Confirmed by direct read: the `iso_week` computation already exists unchanged at
`post_tool_hook.py:54-56` (`now_dt = datetime.now(timezone.utc)`;
`iso_week = now_dt.strftime("%G-W%V")`) — do not touch those three lines. Only the write-target
block at `post_tool_hook.py:159-161` changes:

```python
# before (lines 159-161)
tools_file = Path("agent-monitoring/tools") / f"tools-{iso_week}.jsonl"
tools_file.parent.mkdir(parents=True, exist_ok=True)
write_line(tools_file, json.dumps(record, separators=(",", ":")))

# after
tools_file = Path("agent-monitoring/data") / iso_week / "tools.jsonl"
tools_file.parent.mkdir(parents=True, exist_ok=True)
write_line(tools_file, json.dumps(record, separators=(",", ":")))
```

Keep the `tools_file.parent.mkdir(parents=True, exist_ok=True)` call exactly where it is, before
`write_line(...)` — confirmed load-bearing at `writer.py:113-120`: `write_line()` calls
`_acquire_lock(lock_path)` (line 115) *before* its own internal `target_path.parent.mkdir(...)`
(line 120), and `_acquire_lock`'s `os.open(..., O_CREAT | O_EXCL | O_WRONLY)` (line 53) raises an
uncaught `FileNotFoundError` — not the `FileExistsError` its own `except` clause at line 56 handles
— if the lock file's parent directory doesn't exist yet. Without the caller-side `mkdir`, the very
first write to a brand-new week folder would silently fail (return `False`, diagnostic-only via
`_write_diagnostic` at line 117). This entire block sits inside the outer `try: ... except
Exception: pass` spanning lines 47/163-164 (confirmed by direct read) — the new
`Path("agent-monitoring/data") / iso_week / "tools.jsonl"` construction must remain textually
inside that same block; do not extract it to a helper defined outside the `try`.

Update the module docstring at line 2 (`"""PostToolUse hook: appends one tool-call record to
agent-monitoring/tools/tools-<ISO-week>.jsonl."""`) to reference the new path.

**Shared-resource note:** `agent-monitoring/data/<week>/tools.jsonl` is written only by this one
call site (`post_tool_hook.py`, one `write_line()` call per tool-call event) — no other production
code writes to this path. Multiple concurrent Claude Code sessions/processes each independently
invoke this same hook script per tool call, but `writer.py`'s per-target-file lock protocol
(unchanged by this ticket) already serializes those concurrent appends; nothing about the path
change affects that. `record_events.py`'s `compute_tool_stats()` (Step 4 below) becomes the first
*reader* of this path — that dependency is one-directional (Step 4 depends on this step's output
shape, not vice versa) and is called out in the Dependency Map.

**Do NOT touch:** The sidecar read/scope/prune logic (lines 47-158, `_input_summary`,
`_prune_stale_scoped_sidecars`, status derivation), the `iso_week`/`now_dt` computation itself
(lines 54-56), or the outer `try/except` structure's boundaries.

**Verify:** `test_writes_to_unified_week_folder` (new, replaces
`test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl` per test_plan.md's Regression Surface)
and `test_two_different_iso_weeks_write_to_two_distinct_week_folders` (existing test, paths
updated) in `tests/tools/test_post_tool_hook.py`. Also update in the same file, per test_plan.md:
`test_iso_week_shard_directory_created_on_first_write`, `test_iso_week_computation_failure_does_not_
propagate` (add negative assertion that `agent-monitoring/data/` is not created either),
`test_locking_failure_does_not_propagate` (diagnostic-path assertion), and the `_tools_lines()`
helper (all other sidecar/attribution tests route through this helper and must keep passing
unmodified once it points at the new path).

---

### Step 2 — record_run.py: write target → agent-monitoring/data/<week>/runs.jsonl (write-time)

**Files:** `tools/agent-monitoring/record_run.py`, `tests/tools/test_record_run.py`

**Change:** Confirmed by direct read: `record_run.py:6` currently imports
`from datetime import datetime` only (no `timezone`), and `RUNS_FILE = Path("agent-monitoring/
runs.jsonl")` is a module-level constant at line 13, used at line 86
(`RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)`) and line 87
(`write_line(RUNS_FILE, ...)`). A module-level constant cannot reflect "now" at import time, so
this becomes a locally-computed value inside `main()`, per Decision 5 above (write-time bucketing):

```python
# import line 6, before:
from datetime import datetime
# after:
from datetime import datetime, timezone

# remove module-level line 13:
# RUNS_FILE = Path("agent-monitoring/runs.jsonl")

# inside main(), replacing lines 86-87:
iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
runs_file = Path("agent-monitoring/data") / iso_week / "runs.jsonl"
runs_file.parent.mkdir(parents=True, exist_ok=True)
ok = write_line(runs_file, json.dumps(record, separators=(",", ":")))
```

Update line 88's `if not ok:` block and line 91's diagnostic-path message text (currently says "see
agent-monitoring/.writer_health.jsonl" — the diagnostic sidecar now lives alongside the new target,
i.e. `agent-monitoring/data/<week>/.writer_health.jsonl`; update the message string accordingly so
it doesn't point a human at a now-empty legacy location). Update the module docstring at line 2
(`"""Append a run record to agent-monitoring/runs.jsonl."""`) and the `argparse` description at
line 64 to reference the new path. Use `datetime.now(timezone.utc)`, not `datetime.utcnow()` — the
latter is deprecated as of Python 3.12 and this repo's established `agent-monitoring/` convention
(matching `post_tool_hook.py:54`) is the explicit `timezone.utc` form.

**Shared-resource note:** `agent-monitoring/data/<week>/runs.jsonl` is written only by this one
call site (`record_run.py::main()`, one `write_line()` call per invocation). Four workflow scripts
invoke `record_run.py` as a subprocess (`implement-ticket.js:390`, `implement-epic.js`,
`create-tickets.js`, `simq-audit.js`), each as an independent process — `writer.py`'s per-target
lock (unchanged) already serializes any two of those that happen to land in the same ISO week
concurrently. No other reader of `runs.jsonl` is touched by this ticket (`generate_retro.py`,
`validate.py`, `query.py`, `build_index.py`, the dashboard `ingest.py`, etc. are explicitly Out of
Scope per the ticket — they keep reading the legacy monolithic path until child 3/4, a known,
accepted transient gap already documented in the ticket).

**Do NOT touch:** `validate_record()` (lines 16-25) or `compute_duration_s()` (lines 28-60) — both
unaffected by the path change, confirmed by direct read (neither references `RUNS_FILE`).

**Verify:** `test_writes_to_unified_week_folder` (new) and
`test_two_different_iso_weeks_write_to_two_distinct_week_folders` (new) in
`tests/tools/test_record_run.py`, using the in-process `monkeypatch` pattern (`record_run.main()`
called directly, following the existing `test_append_failure_is_non_blocking`'s pattern — no
subprocess shim needed since the module is directly importable). Also update, per test_plan.md's
Regression Surface: `TestDurationWrittenToRecord` (3 tests) and
`test_execution_identity_fields_pass_through_unchanged`, which read back
`tmp_path / "agent-monitoring" / "runs.jsonl"` directly — update to
`tmp_path / "agent-monitoring" / "data" / "<real-current-week>" / "runs.jsonl"` (compute the real
current week in the test body via `datetime.now(timezone.utc).strftime("%G-W%V")`; these tests
don't need a frozen clock).

---

### Step 3 — record_events.py: EVENTS_FILE write target → agent-monitoring/data/<week>/events.jsonl (write-time, computed once per batch)

**Files:** `tools/agent-monitoring/record_events.py`, `tests/tools/test_record_events.py`

**Change:** Confirmed by direct read: `EVENTS_FILE = Path("agent-monitoring/events.jsonl")` at
`record_events.py:16`, used at line 143 (`EVENTS_FILE.parent.mkdir(...)`) and line 145
(`write_lines(EVENTS_FILE, lines)`). `record_events.py` has no `timezone` import currently (line 6
imports only `from collections import defaultdict`, `pathlib.Path`; no `datetime` import at all —
confirmed, unlike `record_run.py` which at least imports `datetime`). Add
`from datetime import datetime, timezone` to the import block. Per the ticket's explicit scope text
(this is write-time, not left open like `runs.jsonl`) and investigation's note that
`write_lines()` takes one `target_path` for the whole batch (`writer.py:137-162` — "one lock = one
contiguous block in one file" only holds if the whole batch shares one target), compute `iso_week`
**once per `main()` invocation**, not once per record, inside `main()` immediately before line 143:

```python
# main(), replacing lines 143-145:
iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
events_file = Path("agent-monitoring/data") / iso_week / "events.jsonl"
events_file.parent.mkdir(parents=True, exist_ok=True)
lines = [json.dumps(record, separators=(",", ":")) for record in records]
ok = write_lines(events_file, lines)
```

Leave a one-line comment at this computation noting the batch-straddles-a-week-boundary edge case
investigation flagged (a batch that happens to cross UTC-midnight-on-a-Sunday, the ISO week
boundary, lands entirely in whichever week `main()` computed "now" as — this is the only
interpretation compatible with `write_lines`' single-`target_path` batch-contiguity contract, not a
bug to fix here). Update the module docstring (line 2) and the `--data` argparse help text (around
line 87) to reference the new path.

**Shared-resource note:** `agent-monitoring/data/<week>/events.jsonl` is written only by this one
call site (`record_events.py::main()`, one `write_lines()` batch call per invocation). Callers are
`implement-ticket.js` (Finalize's `writeMonitoring` Step 2, batch of the run's accumulated events)
and equivalent call sites in `implement-epic.js`/`create-tickets.js`/`simq-audit.js`. No other
production writer targets this path. This step does not touch `TOOLS_FILE`/`compute_tool_stats()`
at all — that is Step 4, kept separate because it is a distinct concern (read-path bug fix vs.
write-path cutover) per investigation's own structuring.

**Do NOT touch:** `compute_tool_stats()` (lines 35-68, this is Step 4), `validate_record()` (lines
20-32), `warn_vocabulary_drift()` (lines 71-83) — none reference `EVENTS_FILE`.

**Verify:** `test_writes_to_unified_week_folder` (new) and
`test_two_different_iso_weeks_write_to_two_distinct_week_folders` (new) in
`tests/tools/test_record_events.py`, in-process via `record_events.main()`. Also update, per
test_plan.md: `test_execution_identity_fields_pass_through_unchanged`,
`test_vocabulary_warning_never_raises_or_exits`, `test_append_failure_is_non_blocking`,
`test_batch_write_holds_contiguous_lines_under_concurrent_writer` — all read back or write to
`agent-monitoring/events.jsonl` directly; update to the real-current-week
`agent-monitoring/data/<week>/events.jsonl` path (no frozen clock needed, same reasoning as
`record_run.py`'s equivalent tests). `test_batch_write_holds_contiguous_lines_under_concurrent_
writer`'s core race-condition mechanics must stay unchanged — only the target path it reads back
from moves.

---

### Step 4 — record_events.py: fix the critical TOOLS_FILE bug (single-file → multi-week glob)

**Files:** `tools/agent-monitoring/record_events.py`, `tests/tools/test_record_events.py`

**Change:** Confirmed by direct read: `TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` at
`record_events.py:17`. `Path("agent-monitoring/tools.jsonl").exists()` is confirmed `False` in the
current working tree (that file was `git rm`'d by `TCK-20260902-MONITORING-SHARD-MIGRATION` on
2026-09-02). It is read only inside `compute_tool_stats()` (the function's real name — confirmed by
direct read at line 35; the ticket's own inherited citation of `_compute_tool_stats_by_key` is
citation drift from an ancestor investigation, not a real name — **do not rename the function**, it
is part of the module's tested public surface, imported by exact name in
`tests/tools/test_record_events.py`), at lines 58-66:

```python
# before (lines 58-66, inside compute_tool_stats)
rows_by_key: dict[tuple, list[dict]] = defaultdict(list)
if TOOLS_FILE.exists():
    for line in TOOLS_FILE.read_text().splitlines():
        if not line:
            continue
        row = json.loads(line)
        key = (row.get("run_id"), row.get("seq"))
        if key in wanted:
            rows_by_key[key].append(row)

# after
rows_by_key: dict[tuple, list[dict]] = defaultdict(list)
for tools_path in sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl")):
    for line in tools_path.read_text().splitlines():
        if not line:
            continue
        row = json.loads(line)
        key = (row.get("run_id"), row.get("seq"))
        if key in wanted:
            rows_by_key[key].append(row)
```

Remove the module-level `TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` constant at line 17
entirely (no other reference to it exists in the file — confirmed, `compute_tool_stats()` is its
only user). The glob pattern is one wildcard segment for the week-folder name, then the literal
`tools.jsonl` filename — this matches exactly the shape Step 1 produces
(`agent-monitoring/data/<week>/tools.jsonl`, one file directly inside each week folder). Do **not**
write `agent-monitoring/data/*/tools/*.jsonl` — that shape does not exist anywhere in this design;
it is a conflation with the prior epic's now-superseded `agent-monitoring/tools/tools-<week>.jsonl`
shard shape.

`compute_tool_stats()`'s grouping logic itself (`rows_by_key[key].append(row)`, keyed purely by the
`(run_id, seq)` tuple extracted from each row) needs no change — confirmed by direct read it has no
per-file/per-week assumption baked in, so concatenating rows from multiple week-folder files before
grouping is safe. Update the function's docstring (lines 36-49, currently says "from real
agent-monitoring/tools.jsonl rows") to describe the multi-week glob read.

**Shared-resource note — every other writer/reader of the `tools.jsonl` corpus, enumerated:**
- **Writer**: `post_tool_hook.py` (Step 1) is the only writer of any `agent-monitoring/data/<week>/
  tools.jsonl` file, one `write_line()` append per tool call, serialized per-target-file by
  `writer.py`'s lock. This step's glob is read-only against that corpus — it never writes to any
  `tools.jsonl` file, so there is no write/write race to reason about here, only a read racing a
  concurrent append. A `record_events.py` invocation's glob-and-read can interleave with an
  in-flight `post_tool_hook.py` append to the *same* file it's reading; `write_line()`'s lock
  guarantees no interleaved/truncated *line* is ever produced (confirmed at `writer.py:107-134`),
  so the glob read either sees a completed line or doesn't see it yet — never a corrupt partial
  line. This is unchanged from the historical single-file design (the same race existed against
  the old monolithic `tools.jsonl`) — the multi-week glob adds no new race class, just widens the
  set of files read.
- **`(run_id, seq)` global-uniqueness contract**: confirmed via direct read of
  `seq_offset.py` and `docs/agent-monitoring/schema.md` line 145 that `(run_id, seq)` is globally
  unique post-`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` — a resumed session's `seq`
  numbering continues past the max already recorded for that `run_id`, so no two tool-call rows
  across any two week folders can collide on the same `(run_id, seq)` key and get double-counted
  by this glob-and-group logic. This is the load-bearing fact that makes the glob safe rather than
  merely convenient.
- **No other code reads `TOOLS_FILE`/`compute_tool_stats()`'s output** — this function's return
  value is consumed only by `record_events.py::main()` itself (line 136), nowhere else in the
  codebase.
- **Historical-data caveat** (explicitly accepted, not a gap this step must close): this glob only
  matches `agent-monitoring/data/*/tools.jsonl`. It does **not** match the prior epic's still-present
  `agent-monitoring/tools/tools-YYYY-Www.jsonl` shards or the already-`git rm`'d monolithic file —
  those stay invisible to this read until child 2's migration. Do not extend this step's glob to
  also read those old shapes; that would reach into child 2's scope.

**Do NOT touch:** `writer.py` (confirmed fully generic, no changes needed — the ticket's own
Acceptance Criteria requires zero functional diff there), the function name `compute_tool_stats`,
the `wanted` set computation (lines 50-54), or `main()`'s use of the returned dict (lines 136-141).

**Verify:** This is the highest-priority verification in the entire ticket. Must pass, exactly as
designed in `staging_artifacts/TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY/test_plan.md`'s New
Tests Required #5:
`test_tool_call_count_correct_for_tool_rows_in_a_non_current_week_folder` in
`tests/tools/test_record_events.py` — seeds tool-call rows for `(run_id="TCK-CROSS-WEEK-TEST",
seq=4)` in `agent-monitoring/data/2026-W20/tools.jsonl` (a deliberately non-current week), plus
unrelated rows in `agent-monitoring/data/2026-W21/tools.jsonl`, then writes a matching event via
`record_events.py`'s real CLI and asserts `tool_call_count == 2` / `cost_proxy_score > 0.0` read
back from wherever the event itself landed (the real current week). **Do not substitute a weaker
same-week-only variant of this test** — a narrower current-week-only fix would pass a weaker test
but must fail this exact cross-week design, per the ticket's own framing of this as the highest-
priority acceptance criterion. Also verify (companion, recommended):
`test_tool_call_count_sums_rows_across_multiple_weeks_for_same_key` (test_plan.md New Tests #6).
Also update per test_plan.md's Regression Surface: the `_write_tools_jsonl(tmp_path, rows)` helper
(lines 175-181 in the current test file) must write into
`tmp_path / "agent-monitoring" / "data" / "<week>" / "tools.jsonl"` instead of the old
`tmp_path / "agent-monitoring" / "tools.jsonl"`, and every test depending on it
(`test_cost_proxy_score_and_tool_call_count_computed_from_real_tools_jsonl_not_passthrough`,
`test_cost_proxy_score_absent_when_no_tools_jsonl_exists`,
`test_compute_tool_stats_only_targets_implement_ticket_workflow`) updated alongside it.
`test_implement_epic_and_create_tickets_records_unaffected_no_sidecar` and
`test_vocabulary_warning_never_raises_or_exits`-style tests that never reach the file-read branch
need no update — re-run them explicitly as anti-drift guards per test_plan.md.

---

### Step 5 — .gitattributes: add the unified-glob merge=union entry

**Files:** `.gitattributes`

**Change:** Confirmed current exact state by direct read (4 lines plus a comment block, no other
content):

```
agent-monitoring/runs.jsonl merge=union
agent-monitoring/events.jsonl merge=union
agent-monitoring/tools/*.jsonl merge=union
tickets/working_log.csv merge=union
```

Add one new line for the unified glob, keeping all 4 existing lines untouched and in place:

```
agent-monitoring/data/*/*.jsonl merge=union
```

Insert it adjacent to the 3 existing `agent-monitoring/` lines (e.g. immediately after the
`agent-monitoring/tools/*.jsonl merge=union` line, before `tickets/working_log.csv merge=union`),
so the file reads as 5 `merge=union` lines total after this step, plus the existing comment block
unchanged.

**Shared-resource note:** `.gitattributes` is read by `git merge`/`git rebase` machinery, not
written by any runtime code in this repo — there is no concurrent-writer race to reason about here,
only the merge-semantics concern the file's own existing comment documents (every consumer of these
JSONL files reads by explicit `ts`/`seq`/`run_id` fields, never physical line position, so
line-level unioning across two branches' independent appends is safe). The new
`agent-monitoring/data/*/*.jsonl` glob covers all three of `runs.jsonl`, `events.jsonl`, and
`tools.jsonl` under every week folder in one line, since all three now share the same
`agent-monitoring/data/<week>/` directory shape.

**Do NOT touch:** The 3 legacy lines (`agent-monitoring/runs.jsonl merge=union`,
`agent-monitoring/events.jsonl merge=union`, `agent-monitoring/tools/*.jsonl merge=union`) — these
stay in place until child 2 (migration) retires the old paths they cover; a concurrent branch that
has not yet picked up this ticket's cutover may still be appending to the legacy paths, and losing
these lines would silently break merge behavior for that branch. The `tickets/working_log.csv
merge=union` line and the `docs/REGISTRY.yaml`-exclusion comment block are unrelated to this
ticket — leave both untouched.

**Verify:** No pytest test exists for `.gitattributes` (test_plan.md notes this explicitly). Verify
phase check: `grep -c 'merge=union' .gitattributes` should read 5 (was 4); confirm via `git diff
.gitattributes` that the diff is purely additive (one new line), with no line removed or reordered.

---

### Step 6 — docs/agent-monitoring/schema.md: update per-source write-path prose + fix the worked join example

**Files:** `docs/agent-monitoring/schema.md`

**Change:** Five locations, all confirmed present at these exact line numbers by direct read in
this session (matching investigation.md's citations exactly, no drift):

1. **Lines 111-120 ("Historical Corrections" under `## agent-monitoring/runs.jsonl`)**: currently
   states `"runs.jsonl` is append-only for all *new* writes... every writer (`record_run.py`) only
   ever `open(RUNS_FILE, "a")`s..." — `RUNS_FILE` as a fixed single-file constant no longer exists
   after Step 2. Add a short opening paragraph before "Historical Corrections", parallel in
   structure to the `tools.jsonl` section's existing treatment (see item 3 below), describing:
   since this ticket, new run records are appended to `agent-monitoring/data/<ISO-week>/runs.jsonl`
   (one file per UTC ISO week, `%G-W%V`, computed at write time when `record_run.py` is invoked —
   not from the record's own `start_ts`). Update the "Historical Corrections" paragraph's
   `open(RUNS_FILE, "a")` phrasing to describe the write-time-computed path instead of a fixed
   constant; the append-only guarantee itself (never rewrites a line) is unchanged and still true.

2. **Lines 124-126 (`## agent-monitoring/events.jsonl` section opening)**: confirmed by direct read
   this section currently has *no* write-path prose at all — it opens directly with "One record per
   agent call within a workflow run. FK: `run_id → runs.jsonl`." followed by the JSON example. Add
   a short paragraph (same treatment as `tools.jsonl`'s existing lines 344-style paragraph)
   describing the new `agent-monitoring/data/<ISO-week>/events.jsonl` write-time target, and noting
   that a batch of events from one `record_events.py --data` call always lands together in one
   target file (`iso_week` computed once per invocation, per Step 3).

3. **Lines 340-344 (`## agent-monitoring/tools.jsonl` section's opening paragraph)**: currently
   documents the prior epic's shape (`agent-monitoring/tools/tools-YYYY-Www.jsonl`) as current.
   Replace with a paragraph describing the new `agent-monitoring/data/<ISO-week>/tools.jsonl`
   target (still one file per UTC ISO week, still `%G-W%V`, still computed at write time — only the
   directory shape changed, not the sharding granularity). Keep the existing sentence about
   `TCK-20260902-MONITORING-SHARD-MIGRATION` retiring the historical monolithic
   `agent-monitoring/tools.jsonl` (still true and still useful history) but make clear this
   ticket's cutover is a second, distinct move (prior-epic shard shape → this-epic unified shape),
   not a repeat of the same migration.

4. **Line 382 (the "How tool calls are attributed to agent events" paragraph)**: confirmed at the
   exact line the ticket cites, describing `record_events.py::compute_tool_stats()` as counting
   records "per `(run_id, seq)`" without naming a specific read path in this sentence — but the
   surrounding section (particularly the "Write locking" paragraph at line 378 and the general
   framing) implies a single `tools.jsonl` read. Update this paragraph (and/or the sentence
   immediately preceding it if needed for the read to make sense standalone) to state explicitly
   that `compute_tool_stats()` reads the **union of every week folder's** `tools.jsonl`
   (`agent-monitoring/data/*/tools.jsonl`, sorted glob, concatenated) — this is Step 4's fix and is
   the fact this paragraph must now document, per the ticket's own citation of this line as part of
   the "documented contract" this ticket's bug fix must keep satisfying.

5. **Lines 429-459 ("Join Example" section)**: per the ratified Decision 7 above, fix in this
   ticket. The current snippet reads:
   ```python
   Path('agent-monitoring/runs.jsonl')
   Path('agent-monitoring/events.jsonl')
   Path('agent-monitoring/tools').glob('tools-*.jsonl')
   ```
   Update all three to the new unified shape:
   ```python
   import json
   from pathlib import Path
   from collections import defaultdict

   runs = {json.loads(l)['run_id']: json.loads(l)
           for shard in sorted(Path('agent-monitoring/data').glob('*/runs.jsonl'))
           for l in shard.read_text().splitlines() if l}

   events_by_run = defaultdict(list)
   for shard in sorted(Path('agent-monitoring/data').glob('*/events.jsonl')):
       for line in shard.read_text().splitlines():
           if line:
               e = json.loads(line)
               events_by_run[e['run_id']].append(e)

   tools_by_event = defaultdict(list)
   for shard in sorted(Path('agent-monitoring/data').glob('*/tools.jsonl')):
       for line in shard.read_text().splitlines():
           if line:
               t = json.loads(line)
               if t.get('run_id') and t.get('seq') is not None:
                   tools_by_event[(t['run_id'], t['seq'])].append(t)

   # Full run with events and per-event tool calls:
   run = runs['TCK-20260607-...']
   events = sorted(events_by_run[run['run_id']], key=lambda e: e['seq'])
   for event in events:
       tools = tools_by_event[(run['run_id'], event['seq'])]
       print(f"  {event['phase']} ({event['agent']}): {len(tools)} tool calls")
   ```
   (The `runs` dict-comprehension needs to change shape slightly from a one-line comprehension to a
   nested-loop form since it must now glob multiple week-folder files rather than read one — this
   is a genuine, not cosmetic, code-shape change the path unification forces.)

**Shared-resource note:** `docs/agent-monitoring/schema.md` is a documentation file, not a runtime
resource with concurrent writers — no production code path writes to it. Per CLAUDE.md's
Authoritative Mechanics Rule / doc-parity discipline, this step's edits are the doc-side half of
the same-session parity requirement the code changes in Steps 1-4 create; no separate ticket or
session boundary applies here since this is explicitly in this ticket's own scope (not deferred to
child 7, per the ticket's own scope text: "Update the write-path language in
`docs/agent-monitoring/schema.md`'s per-source sections").

**Do NOT touch:** Any other section of `schema.md` (the field tables, the status-enum table at
lines 100-109, the shadow-call-site provenance note around lines 330-337, the "Write locking"
paragraph's locking-mechanism description at line 378, the "Known Limitations" section starting at
line 463) — none of these describe write-path shape and are out of this step's scope. The broader
docs/CLAUDE.md/skill sweep is explicitly child 7's scope, not this ticket's.

**Verify:** No automated test covers doc prose. Verify phase check: `grep -n
'agent-monitoring/tools/tools-\|agent-monitoring/runs.jsonl\x27)\|agent-monitoring/events.jsonl\x27)'
docs/agent-monitoring/schema.md` should return no hits describing a *current* write target (a
historical-context sentence referencing the old shape, e.g. "since `TCK-20260902-...`, ... no
longer appended to a single file", is fine to keep as history — only *current-state* claims must be
updated). Manually re-read the 5 edited locations against the actual post-Step-1/2/3/4 code to
confirm no drift.

## Scope Guards

- Do not migrate or delete any existing data: `agent-monitoring/runs.jsonl` (395KB),
  `agent-monitoring/events.jsonl` (3.2MB), `agent-monitoring/tools/tools-*.jsonl` (13 weekly shards
  W24-W36 plus `tools-unknown-week.jsonl`) all stay present, frozen, receiving no new appends after
  this ticket's cutover — that is child 2's job.
- Do not touch any other consumer's read path: `build_index.py`, `generate_retro.py`,
  `manifest.py`, `seq_offset.py`, `weight_sensitivity_check.py`, `retro_nudge_hook.py`,
  `done_ticket_monitoring_coverage.py`, `validate.py`, `query.py`, `done_checker_static.py`,
  `agent_ops_dashboard/ingest.py` — children 3 and 4. The transient gap (new rows invisible to
  those readers until children 3/4 land) is explicitly accepted by the ticket.
- Do not touch `tools/agent_replay_codex/monitoring_shards.py` or its call sites — child 5.
- Do not build referential-integrity verification tooling — child 6.
- Do not sweep CLAUDE.md or any skill file for path references beyond `schema.md`'s per-source
  write-path paragraphs — child 7 (except the Step 6/Decision 7 worked-example fix, ratified above
  as in-scope because it lives in the same file/same concern this ticket's scope item already
  covers).
- Do not modify `tools/agent-monitoring/writer.py` in any way — Acceptance Criteria requires zero
  functional diff there; confirm via `git diff --stat tools/agent-monitoring/writer.py` showing no
  output after implementation.
- Do not rename `compute_tool_stats()` — the ticket's inherited `_compute_tool_stats_by_key`
  citation is drift from an ancestor investigation, not a real request; the function's actual,
  correct, tested public name is `compute_tool_stats`.
- Do not extend Step 4's glob to also read `agent-monitoring/tools/tools-*.jsonl` (prior epic's
  shape) or any recovered historical monolithic file — that is child 2's migration scope.
- Do not drop any of the 3 callers' own pre-`write_line`/`write_lines`
  `mkdir(parents=True, exist_ok=True)` calls — load-bearing per the `_acquire_lock`-before-internal-
  `mkdir` ordering in `writer.py`.
- Do not remove any of the 3 legacy `.gitattributes` lines.
- Do not change any of the 3 per-line record schemas (the JSON field sets themselves) — only where
  each record physically lands changes.

## Dependency Map

- Steps 1, 2, 3, 5 are independent of each other and can be implemented/verified in any order.
- Step 4 depends on Step 1 only for its regression test fixtures to be meaningful against real
  code (the test seeds synthetic `agent-monitoring/data/<week>/tools.jsonl` files directly via
  `tmp_path` fixtures, so it does not strictly require Step 1's code change to already be landed to
  run — but Step 1 establishes the path *shape* Step 4's glob targets, so implementing Step 1 first
  is the logical order to avoid the two steps disagreeing on shape).
- Step 3 and Step 4 both touch `record_events.py` but are non-overlapping regions (`EVENTS_FILE`
  block at lines 143-145 vs. `compute_tool_stats()` at lines 35-68) — implement Step 3 before Step
  4 to keep the diff easy to review incrementally, but there is no functional ordering requirement
  between them.
- Step 6 (docs) should be done last, after Steps 1-4's actual final code shape is known, so the doc
  prose describes what was actually implemented rather than what was planned.
- Step 5 (.gitattributes) has no dependency on any other step.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Test asserts `post_tool_hook.py` appends to `agent-monitoring/data/<week>/tools.jsonl`, never legacy paths | Step 1 | `test_writes_to_unified_week_folder` (post_tool_hook.py) |
| Equivalent tests for `record_run.py` (→ `data/<week>/runs.jsonl`) and `record_events.py` (→ `data/<week>/events.jsonl`) | Steps 2, 3 | `test_writes_to_unified_week_folder` (record_run.py), `test_writes_to_unified_week_folder` (record_events.py) |
| Writes in two different mocked ISO weeks land in two distinct week folders, all 3 sources | Steps 1, 2, 3 | `test_two_different_iso_weeks_write_to_two_distinct_week_folders` (one per file) |
| Regression test: cross-week tool-row glob produces correct nonzero `tool_call_count`/`cost_proxy_score` | Step 4 | `test_tool_call_count_correct_for_tool_rows_in_a_non_current_week_folder` (must not be a weaker same-week-only variant) |
| Existing single-writer/concurrent-writer/fail-silent tests for all 3 scripts still pass against new paths | Steps 1, 2, 3, 4 | Full regression surface listed in test_plan.md, path-updated |
| `.gitattributes` contains new unified-glob `merge=union`; 3 legacy lines remain | Step 5 | Manual grep/diff check (no pytest coverage for this file) |
| `docs/agent-monitoring/schema.md`'s per-source sections describe new per-ISO-week write path | Step 6 | Manual re-read against implemented code (no automated doc test) |
| No functional change to `tools/agent-monitoring/writer.py` | N/A (not touched by any step) | `git diff --stat tools/agent-monitoring/writer.py` shows no output |

## Anti-Drift Notes

- **Fail-silent contract is the single highest-priority invariant in Step 1.** The new
  `Path("agent-monitoring/data") / iso_week / "tools.jsonl"` construction and its `mkdir` call must
  stay textually inside `post_tool_hook.py`'s existing outer `try: ... except Exception: pass`
  (spanning lines 47/163-164) — this hook fires on literally every tool call across every
  concurrent session in this repo, exactly as the prior epic's analogous ticket
  (`TCK-20260902-MONITORING-SHARD-WRITE-PATH`) treated this same invariant. Any refactor that moves
  the path computation to module scope, a separate function called outside the `try`, or anywhere
  that could raise before entering the `try` block would break tool-call recording repo-wide on any
  unexpected exception (e.g. a future `strftime` format change, an unexpected `None` in the
  payload) — do not do this even for readability.
- **The critical bug fix (Step 4) must be verified by the exact cross-week regression test
  test_plan.md designed** (`test_tool_call_count_correct_for_tool_rows_in_a_non_current_week_
  folder`), not a weaker same-week-only test. A narrower current-week-only fix (e.g. reading only
  `agent-monitoring/data/<today's-week>/tools.jsonl`) would still pass every *other* test in the
  regression surface (they all use same-week fixtures) and would look superficially correct, but
  would silently reintroduce a variant of the exact bug this ticket exists to fix for any
  paused/resumed session whose tool-call rows land in an earlier week than the event being
  recorded — the scenario `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` already proved is
  real.
- **`(run_id, seq)` global uniqueness is the load-bearing safety fact for Step 4's glob**, not an
  incidental detail — it is what makes concatenating rows from multiple week-folder files safe
  against double-counting. Do not weaken or bypass this assumption (e.g. by deduplicating on some
  other key, or by trusting file modification order over the `(run_id, seq)` tuple) without
  re-verifying `seq_offset.py`'s contract still holds.
- **`mkdir` ordering hazard applies identically to all 3 writers**, at one level deeper nesting than
  the prior epic's `agent-monitoring/tools/` shape (`agent-monitoring/data/<week>/` is two levels
  deep from `agent-monitoring/`). `mkdir(parents=True)` handles arbitrary depth identically — no
  additional risk from the extra nesting level, but the caller-side `mkdir` call itself must not be
  dropped as "apparently redundant" during the path-string edit in any of Steps 1, 2, or 3.
- **Test-helper drift risk**: `_tools_lines()` in `test_post_tool_hook.py` and
  `_write_tools_jsonl()` in `test_record_events.py` both hardcode the OLD path shape today and must
  be updated in lockstep with the corresponding source change (Steps 1 and 4 respectively) — an
  easy place to update the source but leave the test helper stale, producing tests that silently
  stop testing anything real. This is exactly the class of bug this ticket itself is fixing at the
  production-code level; do not reintroduce it at the test level.
- **Do not widen `compute_tool_stats()`'s scope**: `test_implement_epic_and_create_tickets_records_
  unaffected_no_sidecar` must keep asserting `stats == {}` for non-`implement-ticket` run_id
  prefixes regardless of what Step 4's glob finds on disk — the glob change must not accidentally
  make other workflows start getting `tool_call_count`/`cost_proxy_score` computed.
