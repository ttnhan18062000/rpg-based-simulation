---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-WRITE-PATH
artifact_type: investigation
tags: [agent-monitoring, observability, hooks]
---

# Investigation — TCK-20260902-MONITORING-SHARD-WRITE-PATH

## Current Behavior

### `tools/agent-monitoring/post_tool_hook.py`

Top-level script (not importable — executes on import via `json.load(sys.stdin)` at module
scope), invoked as a subprocess by Claude Code's PostToolUse hook on every tool call, in every
concurrently-running session.

- Line 10: `from writer import write_line` (only import from this module's own package; the hook's
  import graph today is otherwise stdlib-only: `json`, `sys`, `time`, `datetime`, `pathlib`).
- Line 54: `now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")` — computes the
  `ts` field as a formatted string immediately; the raw `datetime` object is **not** kept bound to
  a separate name.
- Lines 137-151: builds the 13-field `record` dict (`session_id`, `run_id`, `seq`, `phase`,
  `agent`, `ts`, `tool`, `input_summary`, `status`, `duration_ms`, `execution_id`, `provider`,
  `ticket_id`) — this ticket's Out of Scope explicitly forbids changing this shape.
- Lines 153-155 (the exact target):
  ```python
  tools_file = Path("agent-monitoring/tools.jsonl")
  tools_file.parent.mkdir(parents=True, exist_ok=True)
  write_line(tools_file, json.dumps(record, separators=(",", ":")))
  ```
  `tools_file.parent.mkdir(...)` here is redundant with `write_line`'s own identical mkdir call
  (see below) — harmless today (both resolve to `agent-monitoring/`, which already exists), and
  will still be harmless and correct after the ISO-week cutover (both would resolve to the new
  `agent-monitoring/tools/`, which `parents=True` creates). Not required to be removed by this
  ticket, but worth a one-line implementer note since it becomes visibly redundant post-cutover
  rather than invisibly redundant as today.
- Line 157: the entire body (from line 47's `try:` through line 155) is wrapped in one outer
  `except Exception: pass` — this is the exact fail-silent boundary the ticket requires the new
  ISO-week computation to sit inside. Whatever line replaces line 153 must be textually between
  line 47 (`try:`) and line 157 (`except Exception: pass`), which it naturally will be if inserted
  adjacent to line 153/154 — no separate try/except needed around just the ISO-week computation.

### `tools/agent-monitoring/writer.py` — confirmed read-only reference, zero changes needed

- `write_line(target_path: Path, line: str) -> bool` (line 107) — signature takes a generic
  `Path`, not a hardcoded filename. Never raises; returns `True`/`False`.
- `_lock_path_for(target_path)` (line 37): `return target_path.with_name(target_path.name +
  ".lock")` — **confirmed fully generic on `target_path`**. For the new path
  `agent-monitoring/tools/tools-2026-W36.jsonl` this correctly derives
  `agent-monitoring/tools/tools-2026-W36.jsonl.lock` — i.e., locking becomes naturally
  per-shard-file once the write path is sharded, with zero code change. No cross-shard lock
  contention is introduced or removed by this ticket.
- `write_line`'s own `target_path.parent.mkdir(parents=True, exist_ok=True)` (line 120, inside the
  `try:` that opens and appends) — **confirmed present and correct**. Traced directly (not
  assumed): on first write to `agent-monitoring/tools/tools-2026-W36.jsonl`, `target_path.parent`
  is `agent-monitoring/tools/`, which does not exist yet on a fresh checkout/worktree;
  `mkdir(parents=True, exist_ok=True)` creates it (and any missing ancestor) without error,
  exactly the same way it already handles a fresh `agent-monitoring/` directory today for
  `runs.jsonl`/`events.jsonl`. This mkdir happens *inside* `write_line`'s own lock-acquired
  region, after `_acquire_lock(lock_path)` has already succeeded — so the lock file itself
  (`agent-monitoring/tools/tools-2026-W36.jsonl.lock`) is created via `os.open(...,
  O_CREAT|O_EXCL|O_WRONLY)` in `_acquire_lock` (line 53) *before* the target directory is
  guaranteed to exist. This is not a bug today (parent-mkdir logic is identical for the
  already-nested-vs-not-nested case), but it does mean: on a truly fresh checkout with no
  `agent-monitoring/tools/` directory yet, the very first `_acquire_lock` call's `os.open` for the
  lock file will raise `FileNotFoundError` (no such directory) rather than `FileExistsError`
  (lock contention) — `_acquire_lock`'s except clause only special-cases `FileExistsError`
  (line 56); `FileNotFoundError` is not caught there, so it propagates up through
  `_acquire_lock`'s `try/except Exception` — wait: re-checking the code, `_acquire_lock`'s loop
  wraps only the `os.open`/`os.close` pair in a bare `try: ... except FileExistsError:`, with no
  outer `except Exception` inside the loop itself; a `FileNotFoundError` from `os.open` (parent
  dir missing) would propagate out of `_acquire_lock` uncaught by that function, but `write_line`
  itself wraps `_acquire_lock(lock_path)` in `try: ... except Exception as e:` (line 114-118),
  so it is still caught there and correctly routed to `_write_diagnostic(..., "lock_acquire",
  e)`, returning `False` — never raising to the hook, and the hook's own outer `except Exception:
  pass` would swallow it in the (already-impossible-in-practice) case it somehow did propagate.
  **Net effect: on the very first write to a brand-new `agent-monitoring/tools/` directory in a
  given process's lifetime, if `agent-monitoring/tools/` does not yet exist, the lock-acquire step
  could theoretically fail once with `FileNotFoundError`** before the post_tool_hook.py's own
  line-154-equivalent `tools_file.parent.mkdir(...)` (called *before* `write_line`) has already
  created it. In practice this is moot: `post_tool_hook.py` line 154 (`tools_file.parent.mkdir(...)`)
  runs *before* `write_line` is called at all, so `agent-monitoring/tools/` is guaranteed to exist
  by the time `_acquire_lock` runs. This is exactly why that seemingly-redundant mkdir call in the
  hook is not actually removable/skippable once the path gains a new subdirectory — it is now
  doing real, load-bearing work (pre-creating the directory before the lock file's own `os.open`),
  not just harmless redundancy. **Flagging this for Plan/Implement: keep the hook's own
  `tools_file.parent.mkdir(parents=True, exist_ok=True)` call — do not drop it as "redundant" when
  updating line 153-154, it is now the mechanism that prevents a first-write lock-acquire race
  against a not-yet-existing `agent-monitoring/tools/` directory.**
- `_diagnostic_path_for(target_path)` (line 41): `return target_path.parent /
  ".writer_health.jsonl"`. **Side effect worth flagging (not a defect, not required to be fixed by
  this ticket):** today, all 3 writer.py callers (`post_tool_hook.py`, `record_run.py`,
  `record_events.py`) write directly under `agent-monitoring/`, so all diagnostic failures land in
  one shared `agent-monitoring/.writer_health.jsonl`. After this ticket, `post_tool_hook.py`'s own
  write failures will diagnostic-log to `agent-monitoring/tools/.writer_health.jsonl` — a
  **second, separate** diagnostic file — while `record_run.py`/`record_events.py` continue writing
  to the original `agent-monitoring/.writer_health.jsonl`. No doc or code currently asserts "all
  writer.py diagnostics land in one file" as a load-bearing claim (checked
  `docs/ai/codex_posttool_adapter_activation_fragment.md` and
  `tools/codebase_health_snapshot.py` — both only reference `.writer_health.jsonl` generically in
  prose/messages, neither reads it programmatically), so this is not a doc-update requirement, but
  is noted under Anti-Drift Hazards below since a future consumer of "the" diagnostic sidecar could
  miss the new split location.
- No other function in `writer.py` references a filename or path literal anywhere — confirmed by
  full read of the file (163 lines). **Zero functional changes to `writer.py` are required or
  recommended by this ticket**, matching its Acceptance Criteria and Out of Scope.

### `tools/agent-monitoring/generate_retro.py::iso_week()` — exact format to match

```python
def iso_week(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%G-W%V")
    except Exception:
        return "unknown"
```
(lines 123-128). Takes an ISO-8601 string and re-parses it; on any parse failure returns the
literal string `"unknown"` rather than raising.

A second, independent UTC-`now`-based ISO-week computation already exists in the same file at
line 152: `datetime.now(timezone.utc).strftime("%G-W%V")` (used for `generate_retro.py`'s own
`--week` default-to-current-week CLI behavior) — this is the closer structural analog to what
`post_tool_hook.py` needs (compute-from-now, not parse-from-string), and confirms the exact format
string to duplicate is `"%G-W%V"`, timezone UTC, with no additional formatting/rounding logic.
Both `iso_week()` and this line 152 usage are UTC-based, consistent with `post_tool_hook.py`'s own
existing `datetime.now(timezone.utc)` usage for the `ts` field — no timezone mismatch risk.

## Shared-Helper-vs-Duplicate Recommendation

**Recommendation: duplicate the 2-line `strftime("%G-W%V")` computation locally in
`post_tool_hook.py`, reusing the already-computed `datetime.now(timezone.utc)` object rather than
calling `datetime.now()` a second time.**

Concretely: change line 54 from
```python
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
```
to capture the raw datetime once and derive both values from it, e.g.:
```python
now_dt = datetime.now(timezone.utc)
now = now_dt.isoformat().replace("+00:00", "Z")
iso_week = now_dt.strftime("%G-W%V")
```
This avoids a theoretical (if vanishingly rare) two-call clock-read race where a second
`datetime.now()` call could observe a different instant than the one used for `ts`, misfiling a
record by one ISO week if the two calls straddle a week boundary at exactly midnight UTC on a
Monday. Reusing one captured instant for both eliminates this edge case entirely rather than just
accepting it as negligible.

Rationale, in order of weight:

1. **`generate_retro.py` is a genuinely heavy module to pull into a hot, every-tool-call path.**
   Confirmed by direct read: 2,344 lines, and its own import block pulls in `sqlite3`,
   `statistics`, `re`, plus three cross-module imports —
   `from tag_registry import load_registry`, `from tag_report import categorize_tag,
   collect_completed_tickets`, `from validate_frontmatter import (...)` — none of which
   `post_tool_hook.py` needs for anything else. `post_tool_hook.py` today imports only `writer`
   (163 lines, stdlib-only). Importing `generate_retro.py` merely to reuse a 2-line `strftime`
   call would add real per-invocation import/module-init cost to a hook that fires synchronously
   on literally every tool call across every concurrent session — directly contradicting the
   ticket's own scope language that the hook "must stay lightweight/fail-silent."
2. **The Acceptance Criteria rules out option (a)'s "into `writer.py`" variant.** AC explicitly
   states "No functional change to `tools/agent-monitoring/writer.py`" — adding a new ISO-week
   helper function to `writer.py` (even one unrelated to its locking protocol) is still a
   functional change to that file, and would also blur `writer.py`'s documented single
   responsibility ("Single production implementation of the O_CREAT|O_EXCL lock-file protocol" —
   its own module docstring). This leaves only "(a) a new small module both files import" or
   "(b) duplicate" as live options.
3. **A brand-new shared module is not meaningfully lighter than duplication, and adds a new import
   edge to the hot path for a one-liner.** `"%G-W%V"` is a standard, stable strftime directive —
   there is negligible drift risk in duplicating it, unlike e.g. a project-specific formula that
   could legitimately diverge.
4. **This file already has a directly on-point precedent for exactly this trade-off**, in its own
   comments (lines 66-69): `post_tool_hook.py`'s sidecar-reading logic is explicitly **not**
   unified into a shared helper with `tools/retrieval_cache.py`'s `read_current_run_sidecar()` —
   "deliberately NOT unified into a shared helper ... but kept in sync by convention; check it
   when changing this block." The same idiom applies directly here: duplicate the 2-line
   computation, add a comment cross-referencing `generate_retro.py::iso_week()`'s
   `"%G-W%V"` format and its `--week` line-152 UTC-now usage, so a future format change to one is
   flagged for review of the other by convention, not by import coupling.

Plan should finalize this as the concrete implementation choice; investigation surfaces the
evidence but does not itself constitute the decision.

## Mechanics / Engine Constraints

None. This is pure `tools/` infrastructure (agent-monitoring hook plumbing), not simulation logic —
no `docs/mechanics/` chapter or `docs/engine/` contract governs hook write-path behavior. No
divergence from Mechanics Bible/Engine Contracts is created or resolved by this ticket.

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: the `## agent-monitoring/tools.jsonl` section's write-path
  language (including its "Write locking" subsection) must describe the new per-ISO-week
  `agent-monitoring/tools/tools-YYYY-Www.jsonl` file naming/location, per this ticket's explicit
  Scope and Acceptance Criteria. See "Pre-existing doc/code drift found" below — the current text
  of that subsection is already stale independent of this ticket, which Plan/Implement should be
  aware of while touching it.

The `docs/agent-monitoring/README.md` navigation-table description of `tools.jsonl` (path:
`docs/agent-monitoring/README.md`, line 19 and the schema.md link table at line 148) is not
required to change for this ticket: it only names `tools.jsonl` as one of the 3 append-only
sources feeding retro/dashboard metrics, without asserting a specific physical file path or write
mechanism — that description stays true (the historical file still exists, is still readable, and
new shard rows are a transient, accepted, reader-invisible gap per this ticket's own Out of Scope
language, closed by child ticket 3 in the same batch).

The `docs/guides/agent_monitoring.md` guide (path: `docs/guides/agent_monitoring.md`) is not
required to change for this ticket: its `tools.jsonl` mentions (Tool Safety Audit section, Parity
Index Read-Path Usage section) describe report semantics computed over the joined dataset, not the
on-disk write path or file layout — unaffected by where new rows physically land.

`docs/ai/system_overview.md` §6 (path: `docs/ai/system_overview.md`) is not required to change for
this ticket: its one relevant sentence ("Agent activity is recorded in 3 append-only JSONL files
under `agent-monitoring/`...") is a high-level architecture summary, not a literal physical-path
claim that consumers rely on for correctness. It becomes very slightly imprecise the moment new
tool-call rows start landing one directory deeper (`agent-monitoring/tools/...`) instead of
directly under `agent-monitoring/`, but this ticket's own Out of Scope section explicitly accepts
a transient reader/consumer gap after this ticket alone lands, on the basis that child tickets 2
and 3 land immediately after in the same batch — the same acceptance applies to this one summary
sentence in an architecture overview doc, not just to the 4 named reader scripts. If child tickets
2/3 do not land promptly (batch is interrupted), this sentence would be worth revisiting, but that
is a batch-sequencing risk, not something this ticket alone should preemptively rewrite ahead of
the consumers actually changing.

**Pre-existing doc/code drift found (not required by this ticket, but directly adjacent to the
section this ticket must edit):** `docs/agent-monitoring/schema.md`'s "Write locking" subsection
(lines 371-373) currently reads: *"The `PostToolUse` hook (`post_tool_hook.py`) wraps its
open+write block in `fcntl.flock(f, fcntl.LOCK_EX)` (released via `fcntl.flock(f, fcntl.LOCK_UN)`
after the write)..."* — this describes the **pre-`TCK-20260721-MONITORING-WRITER-UNIFICATION`**
implementation. The current code (confirmed above) no longer uses `fcntl` at all; it routes
through `writer.py::write_line()`'s `O_CREAT|O_EXCL` lock-file protocol. This appears to be a doc
gap left over from `TCK-20260721-MONITORING-WRITER-UNIFICATION` not updating this specific prose
paragraph when it migrated the locking mechanism (that ticket's own investigation/plan in
`stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` should confirm this). Since this
ticket's own Scope already mandates touching this exact subsection to describe per-ISO-week
naming, flagging this pre-existing inaccuracy for Plan's judgment call: fixing the `fcntl` →
`write_line`/lock-file description while already in this paragraph is a natural, low-risk
opportunistic fix (not scope creep — same subsection, same edit, materially truer output) versus
leaving it for a separate ticket. Recommend Plan decide explicitly rather than silently going
either way.

## Parity Ledger Overlap

None found. Searched `docs/parity_ledger/infrastructure.yaml` (the subsystem file covering
"Replay, telemetry, observability, workers") for any entry whose `text` asserts the physical
`agent-monitoring/tools.jsonl` write path/location as its parity claim — none exists. The one
entry referencing a `tools.jsonl`-path constant (`DEFAULT_TOOLS_FILE = Path("agent-monitoring/
tools.jsonl")`, near line 6390) is about `generate_retro.py`'s own read-side default, which stays
literally accurate post-cutover (it still reads the frozen historical file; child ticket 3 updates
it to also read shards). Confirmed by checking whether either directly-related prior ticket
(`TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`, `TCK-20260721-MONITORING-WRITER-UNIFICATION`)
added a new INFRA-* entry for itself — neither did; both are only referenced as evidence text
inside other, unrelated entries. This is consistent with this repo's established pattern: pure
agent-monitoring tooling-infrastructure tickets (as opposed to simulation-engine/mechanics
tickets) do not get their own parity ledger entries. No P0 entries are touched.

## Prior Work

- `stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` (investigation.md, plan.md,
  test_plan.md) — the design rationale for `write_line()`/`write_lines()` and the lock-file
  protocol this ticket relies on unmodified. Confirms `_lock_path_for` was deliberately designed
  generic on `target_path` from the start (not a later generalization), supporting this ticket's
  "zero changes to `writer.py`" plan.
- `tickets/done/TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK.md` — original `fcntl`-based
  locking directly in `post_tool_hook.py`, superseded by the writer-unification ticket above. Its
  test file, `tests/tools/test_post_tool_hook.py`, is the one this ticket's Acceptance Criteria
  says must keep passing (single-writer, concurrent-writer, fail-silent tests) — read in full, see
  Test Plan.
- `tickets/done/TCK-20260719-LIVE-PHASE-AGENT-LABEL.md` — established the current 13-field record
  shape (`phase`/`agent` added), which this ticket must not alter.
- `tickets/todos/agent-monitoring-weekly-sharding/SEQUENCE.md` — confirms this ticket
  (`TCK-20260902-MONITORING-SHARD-WRITE-PATH`) is ordered first with no in-batch dependencies;
  child tickets `TCK-20260902-MONITORING-SHARD-MIGRATION` (2) and
  `TCK-20260902-MONITORING-SHARD-CONSUMERS` (3) explicitly depend on this ticket's cutover having
  already happened before they can run meaningfully (migration needs a real current-week shard to
  merge into; consumer tests need real multi-shard files to test against).
- No `docs/REGISTRY.yaml` entries beyond the three named directly in this ticket's own Related
  Tickets section were found relevant by tag/code-area overlap (`agent-monitoring`, `observability`,
  `hooks` — matches this ticket's own tags).

## Risks and Open Questions

- **Ticket's own open question (not resolved here, per instructions — Plan/implementer's call):**
  whether to extract a shared helper or duplicate. This investigation recommends duplication with
  specific rationale above; the ticket text itself defers the final call to the implementer's
  judgment.
- **New, concrete finding for Plan to weigh in on:** the pre-existing `fcntl` vs. `write_line`
  documentation drift in schema.md's "Write locking" subsection (see "Docs Requiring Update"
  above) — fix opportunistically while editing this subsection, or leave for a separate ticket?
  Recommend fixing opportunistically since it's the exact same paragraph this ticket must already
  touch, but this is a judgment call, not something to assume without Plan's sign-off.
- **Redundant-but-now-load-bearing mkdir call**: `post_tool_hook.py`'s own
  `tools_file.parent.mkdir(parents=True, exist_ok=True)` (currently line 154) must be preserved
  when the path changes — it is what guarantees `agent-monitoring/tools/` exists before
  `write_line`'s internal `_acquire_lock` call tries to create the lock file inside it (see
  "Current Behavior" above for the full trace). Do not drop it as apparent redundancy with
  `write_line`'s own mkdir.
- **Diagnostic sidecar split**: after this ticket, `post_tool_hook.py`'s own write failures log to
  a new, second `.writer_health.jsonl` under `agent-monitoring/tools/`, separate from
  `record_run.py`/`record_events.py`'s existing `agent-monitoring/.writer_health.jsonl`. Not a
  required fix (no doc/code currently depends on a single unified file), but worth a one-line
  awareness note if Implement or a future ticket touches diagnostic tooling.
- **Timezone/week-boundary edge case**: already called out in the ticket's own Assumptions
  section — UTC is confirmed correct (matches every existing UTC usage in both files), the only
  residual risk is a record written in the last instant of one ISO week potentially landing in the
  "wrong" shard relative to some other UTC-derived value if two separate clock reads were used;
  mitigated by the single-`now_dt`-capture recommendation above.

## Anti-Drift Hazards

- **Do not touch `writer.py`.** The Acceptance Criteria explicitly requires zero functional
  changes to it; the shared-helper option that would have required touching it is ruled out by
  that same AC (see Recommendation above).
- **Do not touch readers.** `query.py`, `generate_retro.py`, `validate.py`, `build_index.py` are
  explicitly out of scope (child ticket 3) — resist the temptation to "just also" make
  `generate_retro.py::DEFAULT_TOOLS_FILE` or similar glob the new shard directory; that is
  deliberately deferred so ticket 2's migration can run against a clean, well-defined cutover
  point first (per `SEQUENCE.md`'s stated ordering rationale).
- **Do not touch the historical `agent-monitoring/tools.jsonl` file's content.** It stays present,
  frozen (no more appends after cutover), until child ticket 2 migrates it. Do not delete it, do
  not append the new shard's first records into it "for continuity," and do not remove its
  `.gitattributes` `merge=union` line (ticket text explicitly says keep it).
- **Do not widen the 13-field record schema.** Explicitly out of scope; this ticket only changes
  *where* the same-shaped record is written, never its shape.
- **Do not weaken the fail-silent contract.** The ISO-week computation must be inside the same
  outer `try/except Exception: pass` as everything else in the hook — a clock/format edge case
  must never propagate and block a real tool call. Verify this with a dedicated test (see Test
  Plan) rather than assuming it from code inspection alone, since `test_locking_failure_does_not_
  propagate` already established the precedent that this exact class of regression needs its own
  test, not just code review.
- **Preserve `tests/tools/test_post_tool_hook.py`'s existing invocation pattern.** All new tests
  must drive the hook as a subprocess with `cwd` pointed at `tmp_path`, matching every existing
  test in that file — do not introduce a direct-import test style, which the file's own module
  docstring explicitly says won't work (`sys.stdin` executes at import time).
