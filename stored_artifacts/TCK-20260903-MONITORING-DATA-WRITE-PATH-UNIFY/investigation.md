---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY
artifact_type: investigation
tags: [agent-monitoring, observability, hooks, data-quality]
---

# Investigation — TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY

## Current Behavior

### `tools/agent-monitoring/post_tool_hook.py`
Top-level script (not importable — reads `sys.stdin` at module scope), executed by Claude Code's
`PostToolUse` hook. Already computes the ISO-week values exactly as the ticket claims:

- `now_dt = datetime.now(timezone.utc)` — line 54
- `now = now_dt.isoformat().replace("+00:00", "Z")` — line 55
- `iso_week = now_dt.strftime("%G-W%V")` — line 56, with an inline comment already noting it
  mirrors `generate_retro.py::iso_week()`'s format (duplicated on purpose, not imported, to keep
  this hot-path hook's import graph stdlib-only — precedent recorded in
  `stored_artifacts/TCK-20260902-MONITORING-SHARD-WRITE-PATH/plan.md` Decision 3).

Write target (lines 159-161, prior epoch's shape from `TCK-20260902-MONITORING-SHARD-WRITE-PATH`):
```python
tools_file = Path("agent-monitoring/tools") / f"tools-{iso_week}.jsonl"
tools_file.parent.mkdir(parents=True, exist_ok=True)
write_line(tools_file, json.dumps(record, separators=(",", ":")))
```
**Confirmed: only the path template needs to change.** No other logic in the file references
`tools_file`/`iso_week`/the shard shape. The full record-building logic above (lines 47-158,
sidecar read/scope/prune, `_input_summary`, status derivation) is untouched by this ticket. The
whole block sits inside one outer `try: ... except Exception: pass` (lines 47/163-164) — the fix
must stay inside that block so a path-computation failure keeps degrading silently, per the
ticket's explicit "preserve fail-silent contract" scope item.

New target per ticket scope:
```python
tools_file = Path("agent-monitoring/data") / iso_week / "tools.jsonl"
```

### `tools/agent-monitoring/record_run.py`
`RUNS_FILE = Path("agent-monitoring/runs.jsonl")` — line 13, module-level constant. Used in exactly
two places:
- `RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)` — line 86
- `write_line(RUNS_FILE, ...)` — line 87

No other reference anywhere in the file (`validate_record`, `compute_duration_s` don't touch it).
This is a CLI script (`argparse`, `--data '<json>'`) invoked via `bash()` from
`.claude/workflows/implement-ticket.js` (Step 3 of `writeMonitoring`, line 390) and equivalently
from `implement-epic.js`, `create-tickets.js`, `simq-audit.js`. It IS directly importable
(`tests/tools/test_record_run.py` does `import record_run` and calls `record_run.main()` /
`compute_duration_s` / `validate_record` directly) — no subprocess shim needed for logic tests,
only for full CLI/process-boundary tests, which the existing test file already does via
`subprocess.run`.

Design for the fix, mirroring `post_tool_hook.py`'s pattern (write-time, UTC, `%G-W%V`), added
inside `main()` right before the `RUNS_FILE.parent.mkdir(...)` call (module-level constant becomes
a locally-computed path per invocation, since a module-level constant can't reflect "now" at
import time):
```python
iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
runs_file = Path("agent-monitoring/data") / iso_week / "runs.jsonl"
runs_file.parent.mkdir(parents=True, exist_ok=True)
ok = write_line(runs_file, json.dumps(record, separators=(",", ":")))
```
Note: `record_run.py` currently imports `from datetime import datetime` only (no `timezone`) —
the fix needs `from datetime import datetime, timezone` (or `datetime.utcnow()`, but this repo's
established convention throughout `agent-monitoring/` is explicit `datetime.now(timezone.utc))`,
matching `post_tool_hook.py`; use that, not `utcnow()`, for consistency and because `utcnow()` is
deprecated as of Python 3.12).

### `tools/agent-monitoring/record_events.py`
Two module-level constants (lines 16-17):
```python
EVENTS_FILE = Path("agent-monitoring/events.jsonl")
TOOLS_FILE = Path("agent-monitoring/tools.jsonl")
```
`EVENTS_FILE` used at line 143 (`EVENTS_FILE.parent.mkdir(...)`) and line 145
(`write_lines(EVENTS_FILE, lines)`) — same two-call pattern as `record_run.py`.

`TOOLS_FILE` used only inside `compute_tool_stats()` (lines 35-68) — **note: the ticket text (and
the prior epic's own investigation.md it cites) refers to this function as
`_compute_tool_stats_by_key()`; the actual current name in the file is `compute_tool_stats()`,
public (no leading underscore). This is a naming drift between the ticket's inherited references
and the real code — not a blocker, just noted so the implementer doesn't go looking for a
non-existent private helper.** Exact read logic (lines 58-66):
```python
rows_by_key: dict[tuple, list[dict]] = defaultdict(list)
if TOOLS_FILE.exists():
    for line in TOOLS_FILE.read_text().splitlines():
        if not line:
            continue
        row = json.loads(line)
        key = (row.get("run_id"), row.get("seq"))
        if key in wanted:
            rows_by_key[key].append(row)
```
This is a single-file, all-or-nothing read (`.exists()` / `.read_text()`) — it currently reads
`agent-monitoring/tools.jsonl`, which `TCK-20260902-MONITORING-SHARD-MIGRATION` `git rm`'d on
2026-09-02. `Path("agent-monitoring/tools.jsonl").exists()` is confirmed `False` in the current
working tree (verified directly: `ls agent-monitoring/` shows `events.jsonl`, `runs.jsonl`,
`tools/` dir, `README.md`, `retro/`, `.writer_health.jsonl` — no `tools.jsonl`). Every
`implement-ticket` event written since then has silently gotten `tool_call_count=0` /
`cost_proxy_score=0.0` because `wanted` is still populated correctly but `rows_by_key` stays empty
for every key — this is exactly the "silent degrade, not a crash" the ticket describes; confirmed
by direct code read, not just taken on the ticket's word.

Fix design — replace the single-file read with a sorted glob over all week folders, concatenating
every matching file's lines before grouping:
```python
TOOLS_GLOB = "agent-monitoring/data/*/tools.jsonl"
...
for tools_path in sorted(Path(".").glob(TOOLS_GLOB)):
    for line in tools_path.read_text().splitlines():
        if not line:
            continue
        row = json.loads(line)
        key = (row.get("run_id"), row.get("seq"))
        if key in wanted:
            rows_by_key[key].append(row)
```
(`Path(".").glob("agent-monitoring/data/*/tools.jsonl")` and `Path("agent-monitoring/data").glob("*/tools.jsonl")` are equivalent for this purpose — either form works with `pathlib.Path.glob`; the ticket's exact scope text writes it as "a glob over `agent-monitoring/data/*/tools.jsonl`", i.e. one wildcard segment for the week-folder name, then the literal filename. Confirmed this is the correct pattern for the shape this same ticket's own write-path fix produces (`agent-monitoring/data/<week>/tools.jsonl`, one file directly inside each week folder — NOT a `tools/` subdirectory under the week folder). `agent-monitoring/data/*/tools/*.jsonl` would be wrong — that shape doesn't exist anywhere in this design; it was the OLD (pre-unification) `agent-monitoring/tools/tools-<week>.jsonl` shape, a single flat directory keyed by filename, not a per-week directory containing a `tools/` subfolder.)

`EVENTS_FILE` gets the same write-time `iso_week` treatment as `RUNS_FILE`, targeting
`agent-monitoring/data/<week>/events.jsonl`. The ticket's scope text is explicit that this is
write-time (not the record's own `ts` field) — not left open like the `runs.jsonl` question. This
matters because `record_events.py`'s `main()` can receive a JSON array (a batch) of multiple
records in one call, each with potentially different `ts` values (though in the one real call site,
`implement-ticket.js` Step 2, all records in a batch are written together at Finalize with `ts`
values captured moments apart during the same phase — still, "one batch → one lock acquisition →
one contiguous block of lines in one target file" per `writer.py`'s own docstring is only coherent
if the whole batch shares one target path, which requires computing `iso_week` once per `main()`
call rather than per-record).

### `(run_id, seq)` global-uniqueness confirmation
Read `tools/agent-monitoring/seq_offset.py` in full. Its own docstring describes the exact failure
mode the ticket's design note is protecting against: before `TCK-20260728-MONITORING-PAUSE-RESUME-
SEQ-COLLISION`'s fix, a resumed session's `seq` numbering (both `pushEvent`'s and every
`writeSidecar` call site's `events.length + 1` expression) restarted at 1 from the resumed
session's own empty in-memory `events` array, "silently aliasing the new session's tool-call
attribution onto the prior session's `(run_id, seq)` buckets in `tools.jsonl`." The fix
(`compute_seq_offset(run_id, events)`, called at Scope-phase resume) looks up the max `seq` already
recorded for that `run_id` in `agent-monitoring/events.jsonl` (the 1:1 authoritative per-agent-call
record) and continues numbering past it. **Confirmed: post-fix, `(run_id, seq)` is the schema's
own contract for global uniqueness** (`docs/agent-monitoring/schema.md` line 145: "`seq` — 1-based
call order within the run. Monotonically increasing") — the pause/resume scenario is precisely the
case that could have broken this without `seq_offset.py`'s fix, and it's already fixed upstream of
this ticket.

`compute_tool_stats()`'s own logic (re-confirmed by direct read above) has **no per-file/per-week
assumption baked in** — it groups purely by the `(run_id, seq)` tuple key extracted from each row,
regardless of which physical file the row came from. Concatenating rows from multiple week-folder
files before grouping is safe and behavior-preserving versus the historical single-file read, as
long as no physical row is double-counted (i.e., no file is matched by the glob twice, and a given
tool-call row is written to exactly one week's file — true by construction, since
`post_tool_hook.py` computes `iso_week` once per invocation and appends to exactly one target
file). This restores the original pre-sharding read scope (a full-corpus read), which is what the
ticket's design note claims and what this investigation independently confirms from the code, not
just from the ticket's own assertion.

One caveat worth flagging (not a blocker, a residual/transient-gap point): this ticket's own fix
only glob-matches `agent-monitoring/data/*/tools.jsonl`. Immediately after this ticket lands (before
child 2's migration), that glob will only match whatever week-folders accumulate from THIS ticket's
own cutover forward — the pre-existing `agent-monitoring/tools/tools-YYYY-Www.jsonl` shards (prior
epic's shape, still present, still un-migrated) and the historical monolithic `agent-monitoring/
tools.jsonl` (already git-rm'd, recoverable only via `git log --follow`) are NOT visible to the new
glob. So `tool_call_count`/`cost_proxy_score` for any event whose matching tool-call rows were
written *before* this ticket's cutover will still compute as `0`/`0.0` until child 2's migration
moves that historical data into the new per-week-folder shape. This is consistent with — not a new
gap beyond — the ticket's own Out-of-Scope section ("A known, accepted transient gap: after this
ticket alone lands, new rows are invisible to those readers until children 3/4 land"), but it's
worth being explicit that the bug fix's *practical* effect is scoped to newly-written data going
forward, not a retroactive repair of already-broken historical events. The regression test
(Acceptance Criteria bullet 4) tests the glob mechanism itself with synthetic multi-week fixtures,
which is correct and sufficient to prove the mechanism works — it does not (and should not) attempt
to prove historical real data gets repaired, since that's explicitly child 2's job.

### `tools/agent-monitoring/writer.py` — confirmed unmodified-but-load-bearing
Read in full. `write_line()`/`write_lines()` are fully generic on `target_path` — no hardcoded
paths anywhere in the module; `_lock_path_for()`/`_diagnostic_path_for()` both derive from
`target_path.parent`/`target_path.name`. Confirmed `mkdir(parents=True, exist_ok=True)` correctly
creates an arbitrarily deep new nested directory in one call — this is standard `pathlib` behavior
and not itself in question.

**The subtlety that matters (already discovered and documented by the prior epic — re-confirmed
here by direct read, not assumed):** `write_line()`'s internal `target_path.parent.mkdir(...)`
call (line 120) runs *after* `_acquire_lock(lock_path)` (line 115, called first). `_acquire_lock`
does `os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)` (line 53) — this requires
`lock_path`'s parent directory to already exist; if it doesn't, `os.open` raises `FileNotFoundError`,
which is NOT caught by `_acquire_lock`'s own `except FileExistsError` clause (line 56) and instead
propagates up to `write_line`'s outer `except Exception as e: _write_diagnostic(...); return False`
(lines 116-118) — meaning the very first write to a brand-new, not-yet-existing target directory
would silently fail (return `False`, diagnostic-only) if nothing else pre-creates the directory
first. This is why all 3 callers already do their OWN `target_path.parent.mkdir(parents=True,
exist_ok=True)` call *before* invoking `write_line`/`write_lines`
(`post_tool_hook.py:160`, `record_run.py:86`, `record_events.py:143`) — `writer.py`'s own internal
mkdir at line 120/150 is a secondary safety net for the actual file-open, not what makes first-write
directory creation work. **Confirmed: the fix must keep each caller's own pre-`write_line` mkdir
call, updated to the new nested `agent-monitoring/data/<week>/` path** — dropping it and relying
solely on `write_line`'s internal mkdir would silently break first-write-of-a-new-week for all 3
sources. This exact reasoning is already documented almost verbatim in
`stored_artifacts/TCK-20260902-MONITORING-SHARD-WRITE-PATH/plan.md` (search "Keep the
`tools_file.parent.mkdir(parents=True, exist_ok=True)` call") for the prior epic's one-level-deeper
case; this ticket's `agent-monitoring/data/<week>/` is two levels deep from `agent-monitoring/`
(vs. the prior epic's one-level `agent-monitoring/tools/`), but `mkdir(parents=True)` handles
arbitrary depth identically — no additional risk from the extra nesting level.

### Existing tests — patterns confirmed
- `tests/tools/test_post_tool_hook.py`: hook is NOT importable directly (top-level `sys.stdin`
  read executes on import) — every test drives it via `subprocess.run` against a real script file,
  with a `_run_hook_with_frozen_now()` helper that builds a **source-shim** (prepends a
  monkeypatched `datetime.now` classmethod override, then the hook's own source text, to a temp
  `.py` file, then subprocess-runs that shim) to freeze "now" for ISO-week tests. This exact
  pattern is reused by `test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl` and
  `test_two_different_iso_weeks_write_to_two_distinct_shard_files` — both directly reference the
  OLD shard path (`agent-monitoring/tools/tools-<week>.jsonl`) and must be updated to the new
  `agent-monitoring/data/<week>/tools.jsonl` path as part of this ticket, not left pointing at a
  path that will no longer be written.
- `tests/tools/test_record_run.py` and `tests/tools/test_record_events.py`: **both files ARE
  directly importable** (`import record_run`, `import record_events`) — no subprocess shim needed
  for pure-function tests (`validate_record`, `compute_duration_s`, `compute_tool_stats`,
  `warn_vocabulary_drift`). Full CLI-path tests use `subprocess.run([sys.executable,
  str(_RECORD_PATH), "--data", ...], cwd=tmp_path)` and then read back
  `tmp_path / "agent-monitoring" / "runs.jsonl"` / `"events.jsonl"` directly (no ISO-week
  subdirectory in the assertion today) — these read-back paths need updating to
  `tmp_path / "agent-monitoring" / "data" / "<week>" / "runs.jsonl"` (etc.), and since neither
  file currently freezes "now" anywhere, new tests need either a frozen-clock shim (matching
  `post_tool_hook.py`'s subprocess-shim pattern, since these ARE subprocess-invoked for the CLI
  tests) or — since both are directly importable — a simpler `monkeypatch` on `datetime` within an
  in-process call to `record_run.main()` / `record_events.main()` (as
  `test_append_failure_is_non_blocking` in both files already does via `monkeypatch.setattr(sys,
  "argv", ...)` + calling `.main()` directly, no subprocess). The in-process monkeypatch route is
  simpler and more idiomatic for these two files specifically, since they don't have
  `post_tool_hook.py`'s "not importable" constraint — recommend using it for the new ISO-week
  tests on `record_run.py`/`record_events.py`, reserving the heavier subprocess-shim only where a
  test needs to also exercise the process boundary (e.g. `TestExitCodeContract`).
- `_write_tools_jsonl(tmp_path, rows)` helper in `test_record_events.py` (lines 175-181) writes
  directly to `tmp_path / "agent-monitoring" / "tools.jsonl"` — this helper (and every test that
  calls it: `test_cost_proxy_score_and_tool_call_count_computed_from_real_tools_jsonl_not_
  passthrough`, `test_cost_proxy_score_absent_when_no_tools_jsonl_exists`,
  `test_compute_tool_stats_only_targets_implement_ticket_workflow`) needs to be updated to write
  into `agent-monitoring/data/<week>/tools.jsonl` instead, to exercise the new glob-based read path
  rather than the retired single-file path — otherwise these tests would keep "passing" against a
  path `compute_tool_stats()` no longer reads, silently becoming false-positive coverage for a
  behavior that no longer exists (same class of bug as the ticket's own critical-bug narrative).

## Mechanics / Engine Constraints
This ticket is pure tooling/observability infrastructure (`agent-monitoring/`), not simulation
domain logic — no `docs/mechanics/` chapter or `docs/engine/` contract governs JSONL write-path
shape. No Mechanics Bible or engine-contract constraint applies.

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: multiple per-source paragraphs currently describe write paths
  that this ticket changes, and one describes the currently-broken read path this ticket fixes.
  Specific locations, all confirmed by direct read at their current line numbers:
  - Lines 340-344 (the `## agent-monitoring/tools.jsonl` section's opening paragraph): currently
    documents the prior epic's shape (`agent-monitoring/tools/tools-YYYY-Www.jsonl`) as the
    current write target — must be updated to describe `agent-monitoring/data/<week>/tools.jsonl`.
  - Line 382 (the "How tool calls are attributed to agent events" paragraph, confirmed at the exact
    line number the ticket cites — no drift from the ticket's own citation): describes
    `record_events.py::compute_tool_stats()` reading "`tools.jsonl`" — must be updated to describe
    the multi-week glob read (`agent-monitoring/data/*/tools.jsonl`, all weeks, concatenated).
  - Lines 113-120 ("Historical Corrections" under `## agent-monitoring/runs.jsonl`): states
    "`runs.jsonl` is append-only... every writer (`record_run.py`) only ever `open(RUNS_FILE, "a")`s"
    — `RUNS_FILE` as a fixed single-file constant no longer exists after this ticket; needs a
    parallel paragraph to the existing `tools.jsonl` section (lines 340-344) describing the new
    per-week write target, and the `open(RUNS_FILE, "a")` phrasing needs updating since the write
    now goes through the write-time-computed path.
  - Line 124-126 (`## agent-monitoring/events.jsonl` section opening): no current write-path
    prose at all (unlike the `tools.jsonl` section, which already got this treatment from the
    prior epic) — needs the same kind of short opening paragraph the `tools.jsonl` section has,
    describing the new `agent-monitoring/data/<week>/events.jsonl` target.
  - Lines 430-459 (the worked Python read-example under "Full run with events and per-event tool
    calls"): this snippet currently reads `Path('agent-monitoring/runs.jsonl')`,
    `Path('agent-monitoring/events.jsonl')`, and `Path('agent-monitoring/tools').glob('tools-*.jsonl')`
    directly — all three of these literal paths become stale/misleading (not just "the old data
    still there, new data elsewhere" but actively wrong code a reader would copy-paste and get
    nothing back for) the moment this ticket's write-path cutover lands. This is the same file
    (`schema.md`) and same "per-source write path" concern the ticket's scope item already covers,
    not a separate broader sweep — recommend including it in this ticket's targeted edit rather
    than deferring to child 7, since leaving it unedited makes the doc actively incorrect (not
    merely incomplete) about where THIS ticket's own new writes land.

## Parity Ledger Overlap
None. `docs/parity_ledger/` tracks simulation-mechanics parity (economic laws, combat, world
evolution, etc.) between the Mechanics Bible and `src/`. This ticket touches only
`tools/agent-monitoring/` infrastructure — no parity ledger subsystem (`substrate.yaml`,
`combat_movement.yaml`, `strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`,
`social_narrative.yaml`, `world_dynamics.yaml`, `infrastructure.yaml`) has an entry whose `text`
describes agent-monitoring write-path shape. `infrastructure.yaml` entries INFRA-289 through
INFRA-291 (referenced in `schema.md` line 44-45) cover the derived SQLite index's per-consumer
migration evidence, a distinct, already-shipped, read-side concern — not this ticket's write-path
scope. No P0 entries are touched.

## Prior Work
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-WRITE-PATH/` — established the exact `%G-W%V`
  ISO-week write-path pattern this ticket extends to `runs`/`events` and re-shapes for `tools`.
  Its `plan.md` Decision 3 (duplicate the `iso_week` computation rather than share a helper module)
  and its explicit reasoning for keeping the caller-side `mkdir` before `write_line` are both
  directly reusable precedent, cited above.
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-MIGRATION/` — the ticket that `git rm`'d
  `agent-monitoring/tools.jsonl`, the direct cause of this ticket's critical bug. Its own scope
  evidently did not include updating `record_events.py`'s `TOOLS_FILE` read — confirming the bug
  is a genuine cross-ticket gap (child ticket B's migration silently broke child ticket... actually
  a *different*, unrelated-at-the-time consumer, `record_events.py`, which nothing in that epic's
  scope touched) rather than a mistake within that ticket's own stated scope.
- `stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` — `writer.py`'s original design
  rationale (single shared `write_line`/`write_lines`, replacing 3 separate ad hoc lock
  implementations). Reused unmodified by this ticket, as scoped.
- `stored_artifacts/TCK-20260719-COST-PROXY-WRITE-PATH/` and
  `stored_artifacts/TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION/` — established the
  original `tool_call_count`/`cost_proxy_score` deterministic-computation contract and diagnosed
  two unrelated, now-fixed sources of `(run_id, seq)` misattribution (sidecar cross-contamination
  and `writeMonitoring`'s own bookkeeping calls self-polluting the last open phase). Useful
  background for why `(run_id, seq)` correctness is treated as a hard invariant in this subsystem,
  but neither ticket's fix is reopened by this one.
- `stored_artifacts/TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION/` (referenced via
  `tools/agent-monitoring/seq_offset.py`, read directly) — confirms cross-week-boundary
  `(run_id, seq)` matching is a real, previously-encountered scenario and that `(run_id, seq)` is
  the schema's own uniqueness contract post-fix, directly motivating and validating this ticket's
  full-corpus-glob design for `record_events.py`'s `TOOLS_FILE` read (see confirmation section
  above).

## Risks and Open Questions

- **`runs.jsonl` bucketing recommendation: write-time ("now"), confirmed sound.** Traced every
  `record_run.py` call site (`.claude/workflows/implement-ticket.js:390`, plus `implement-epic.js`,
  `create-tickets.js`, `simq-audit.js`, and the early-failure fallback paths at
  `implement-ticket.js:204` / `implement-epic.js:38,192,218`). In every real call site,
  `record_run.py` is invoked at Step 3 of `writeMonitoring`, immediately after Step 1 captures
  `end_ts` — i.e. at (or within seconds of) the run's actual end, not its start. `start_ts` is
  captured much earlier (Scope/Discover/Comprehend phase) and can diverge from "now" by the run's
  entire wall-clock duration — for a long-running or paused/resumed run (the same scenario
  `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` addresses for `seq`), `start_ts` and
  call-time `now` can legitimately land in *different* ISO weeks. Bucketing by `start_ts` would
  mean a long/paused run's record lands in the week it *started*, invisible to
  `generate_retro.py`'s retro report for the week it actually *finished* and was recorded — the
  opposite of what a "which runs completed this week" retro consumer wants. Bucketing by write-time
  "now" instead groups each run's record into whichever week's retro will actually cover it,
  consistent with `post_tool_hook.py`'s existing precedent (each tool call bucketed by when it
  physically happened, not by which run/session it belongs to) and with `record_events.py`'s
  ticket-mandated write-time behavior (not left open, unlike `runs.jsonl`). For the early-failure
  fallback paths (`SCOPE_AGENT_FAILED`, `INVALID_ARGS`, etc.), `start_ts == end_ts` (same literal
  timestamp variable used for both), so write-time and start_ts bucketing are identical there —
  zero regression risk for those cases either way. **Recommendation: confirm write-time, as the
  ticket's own default suggests** — this investigation found no call-site evidence against it, and
  positive evidence (the paused/resumed-run retro-visibility argument above) in its favor. The
  implementer should still explicitly record this decision and its reasoning in
  Implementation Notes per the ticket's requirement, not silently default to it.
- **Open question the implementer must still resolve (not this investigation's call):** should
  `record_events.py`'s write-time `iso_week` be computed once per `main()` invocation (one value
  for the whole batch, matching `write_lines`' "one lock = one contiguous block in one file"
  design) or per-record (using each record's own `ts` field, risking a batch split across two
  target files if a batch happens to straddle a week boundary)? The ticket's scope text ("the same
  write-time ISO-week computation targeting `agent-monitoring/data/<week>/events.jsonl`" — singular
  path, singular week) reads as intending the former (compute once, one target file for the whole
  batch), which is also the only interpretation compatible with `write_lines`' batch-contiguity
  guarantee as currently implemented (it takes one `target_path`, not one per line). Flagging this
  explicitly since a batch straddling midnight-UTC-on-a-Sunday (ISO week boundary) is a real,
  if rare, edge case worth a one-line comment in the implementation, not a silent assumption.
- No file listed in "Related Code Areas" is missing — all 6 exist and were read directly
  (`post_tool_hook.py`, `record_run.py`, `record_events.py`, `writer.py`, `.gitattributes`,
  `docs/agent-monitoring/schema.md`), plus all 3 test files.
- No acceptance criterion references behavior that doesn't exist yet — the ticket's scope is a
  faithful, already-well-specified description of the actual current code state; nothing needed
  to be treated as "not yet built."

## Anti-Drift Hazards

- **Do not "fix" `record_events.py`'s `compute_tool_stats` naming** (ticket text says
  `_compute_tool_stats_by_key`, actual code says `compute_tool_stats`) — this is inherited
  citation drift from an ancestor investigation, not a real rename request; renaming it is pure
  scope creep against this ticket's explicit "Out of Scope: Any change to writer.py's locking
  protocol or the 3 per-line record schemas" (the function's public name is part of the module's
  tested public surface — `tests/tools/test_record_events.py` imports it by that exact name).
- **Do not touch `writer.py`** — confirmed fully generic and correct as-is; the ticket's own
  Acceptance Criteria requires "No functional change to `tools/agent-monitoring/writer.py`," and
  this investigation independently confirms no change is needed there.
- **Do not drop the caller-side `mkdir(parents=True, exist_ok=True)` calls** in any of the 3
  writers when refactoring — see the `_acquire_lock`-runs-before-`write_line`'s-own-mkdir ordering
  confirmed above. This is easy to "clean up" as apparently redundant and would silently break
  first-write-of-a-new-week for whichever source loses it.
- **Do not remove the 3 legacy `.gitattributes` lines** (`agent-monitoring/runs.jsonl merge=union`,
  `agent-monitoring/events.jsonl merge=union`, `agent-monitoring/tools/*.jsonl merge=union`) — this
  ticket only *adds* the new unified-glob line; child 2 removes the legacy lines once old paths are
  fully retired. Confirmed current exact 3-line state (plus a 4th, unrelated
  `tickets/working_log.csv merge=union` line, and a comment block) by direct read.
- **Do not migrate or delete any existing data** (`agent-monitoring/runs.jsonl`,
  `agent-monitoring/events.jsonl`, `agent-monitoring/tools/tools-*.jsonl`) — explicitly Out of
  Scope; these stay frozen, receiving no new appends after this ticket's cutover, until child 2.
  Confirmed via direct `ls agent-monitoring/` that all of these currently exist and are non-empty
  (`events.jsonl` 3.2MB, `runs.jsonl` 395KB, `tools/` has 13 weekly shard files W24 through W36
  plus one `tools-unknown-week.jsonl` fallback file) — real, sizeable historical data that a
  careless implementation could accidentally truncate/overwrite if a write target path computation
  has a bug that collides with an old path.
- **Do not extend this ticket's `TOOLS_FILE` glob fix to also read the prior epic's
  `agent-monitoring/tools/tools-*.jsonl` shards or the historical monolithic file** — that would
  be reaching into child 2's migration scope (reading old-shape data at the new read site) rather
  than staying inside this ticket's own "point tools read/write at the new unified location" scope.
  The transient gap this creates (documented above and already accepted in the ticket's own
  Out-of-Scope section) is intentional, not an oversight to silently patch here.
- **Test-file drift risk**: the existing `_tools_lines()` helper in `test_post_tool_hook.py` and
  `_write_tools_jsonl()` helper in `test_record_events.py` both hardcode the OLD path shape and
  must be updated in lockstep with the source change — an easy place to update the source but leave
  a helper stale, producing tests that silently stop testing anything real (exactly the failure
  mode this ticket itself is fixing at the production-code level).
