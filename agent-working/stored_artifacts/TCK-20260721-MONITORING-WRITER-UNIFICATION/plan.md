---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260721-MONITORING-WRITER-UNIFICATION
artifact_type: plan
tags: [monitoring, writer, unification]
---

# Implementation Plan — TCK-20260721-MONITORING-WRITER-UNIFICATION

## Summary

Extract the lock-file mechanics proven by `tests/tools/test_monitoring_writer_lockfile_candidate.py`
into a new production module, `tools/agent-monitoring/writer.py`, exposing two public functions —
`write_line()` (single record) and `write_lines()` (batch, one lock acquisition) — that never raise
to their caller: any lock-acquire or write failure is caught internally, recorded to a new
out-of-band diagnostic sidecar file (`agent-monitoring/.writer_health.jsonl`, written via a
lock-free best-effort `O_APPEND`, never through the writer's own locked path), and reported back to
the caller as a plain `bool`. `post_tool_hook.py`, `record_run.py`, and `record_events.py` each
migrate their append step (and only their append step — pre-write validation/CLI exit-code
contracts are untouched) to call this shared module instead of their 3 current ad hoc
implementations (`fcntl.flock`, unlocked single write, unlocked batch write respectively). Per the
Execution Identity Model in `docs/architecture/agent_orchestration_contract.md` (lines 150-156),
this plan treats `execution_id`, `provider`, and `ticket_id` as one indivisible additive field set —
an explicit amendment to the ticket's AC text, which names only 2 of the 3 (see Acceptance Criteria
Map) — applied additively to new records in all three corpus files (`runs.jsonl`, `events.jsonl`,
`tools.jsonl`), with every legacy record shape remaining readable through the existing tolerant
`validate.py::load_jsonl`. `src/api/agent_ops_dashboard/ingest.py` and `models.py` gain
provider/execution_id/ticket_id filtering and an explicit `"legacy"`/`"unknown"` label for records
that predate this migration — additive only, no change to `query.py`, `validate.py`, or
`generate_retro.py`. The entry and exit criteria are enforced by `tools/agent-monitoring/manifest.py`'s
existing `capture_lines()`/`assert_prefix_preserved()` pair, consumed read-only, snapshotted before
any writer-file change and diffed after all implementation work.

## Amendment to Ticket AC (Decision #1)

The ticket's AC text and Scope section name only `execution_id` and `provider` as the two additive
fields. Per `docs/architecture/agent_orchestration_contract.md:150-156`, the ADR treats
`execution_id`/`provider`/`ticket_id` as one indivisible Execution Identity Model, already consumed
verbatim by the dependent `agent-monitoring-derived-index` batch's `monitoring-schema.yaml`.
Implementing only 2 of the 3 fields would leave the schema half-migrated against the higher-authority
ADR this epic is built from. **This plan amends the AC's field list to all 3 fields
(`execution_id`, `provider`, `ticket_id`)** for every step and test below. This is a documented,
flagged amendment (mirrors ticket 3/7's own mid-plan Related-Code-Areas amendment precedent cited by
the launcher), not a silent scope change — it is called out again in the Acceptance Criteria Map.

## Steps

### Step 1 — Entry-criterion manifest snapshot

**Files:** none changed (read-only procedure); output written to a scratch path outside the repo
(e.g. the session scratchpad, not committed).

**Change:** Before touching any writer file, run `tools/agent-monitoring/manifest.py::capture_lines(Path("agent-monitoring"))`
(import, do not re-implement) against the real `agent-monitoring/` directory and serialize the
returned `dict[str, list[str]]` to a scratch JSON file outside the repo
(e.g. `/tmp/.../tck-20260721-writer-unification-entry-manifest.json`). This is the entry-criterion
snapshot the ticket's Scope requires be checked against, and the baseline for Step 11's exit diff.
Keep the scratch file until Step 11 completes, then discard it — it must never be committed.

**Do NOT touch:** `tools/agent-monitoring/manifest.py` itself (read-only reuse only, per Anti-Drift
Hazards) — no new manifest-tooling function is required, per investigation Risk #4.

**Verify:** Manual procedure check — confirm the scratch file exists and contains exactly the 3 keys
`runs.jsonl`/`events.jsonl`/`tools.jsonl`, each a non-empty list of raw lines matching the real
files' current line counts. No pytest test corresponds to this step; it is a Plan/Implement-phase
procedure gate, matching Test Plan item 10's framing.

---

### Step 2 — Build the shared writer's core lock-file mechanics (raise-on-failure)

**Files:** `tools/agent-monitoring/writer.py` (new), `tests/tools/test_monitoring_writer.py` (new).

**Change:** Create `tools/agent-monitoring/writer.py` as new production code (never importing from
`tests/tools/test_monitoring_writer_lockfile_candidate.py`) reusing the candidate's mechanics
verbatim:
- Constants: `STALE_AFTER_S = 5.0`, `MAX_RETRIES = 200`, `RETRY_SLEEP_S = 0.005`.
- `_lock_path_for(target_path: Path) -> Path` → `target_path.with_name(target_path.name + ".lock")`
  (sibling `<target>.lock` naming, matches candidate).
- `_acquire_lock(lock_path, stale_after_s=STALE_AFTER_S, max_retries=MAX_RETRIES, retry_sleep_s=RETRY_SLEEP_S) -> None`
  — `os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)` / `os.close(fd)` loop, stale-mtime
  removal, `time.sleep(retry_sleep_s)` backoff, `raise TimeoutError(...)` after `max_retries`
  exhausted — copied mechanics, **without** the candidate's `_assert_not_real_corpus` guard (which
  inverts the intended target for production use — explicitly excluded per launcher instruction).
- `_release_lock(lock_path) -> None` — `os.remove(lock_path)`, tolerating `FileNotFoundError`.
- `write_line(target_path: Path, line: str) -> None` and `write_lines(target_path: Path, lines: list[str]) -> None`
  — at this step, both **raise on failure** (mirroring the candidate's `_write_record_lockfile`
  exactly): acquire lock, open `target_path` in `"a"`, write `line + "\n"` (or each line in `lines`
  joined with `"\n"` + trailing `"\n"`, all under one lock acquisition for `write_lines`), release
  lock in a `finally` block regardless of whether the write raised. `line`/each element of `lines` is
  a pre-serialized JSON string (no trailing newline) — serialization stays the caller's
  responsibility, matching today's 3 call sites' existing `json.dumps(record, separators=(",", ":"))`
  pattern.
- Ensure `target_path.parent.mkdir(parents=True, exist_ok=True)` before opening, matching all 3
  existing call sites' current behavior.

This step deliberately does **not** yet implement the "never raises to caller" contract or the
diagnostic sidecar — that is Step 3, kept separate so each step changes one thing.

**Do NOT touch:** `tests/tools/test_monitoring_writer_lockfile_candidate.py` (leave as-is; its 3
tests may stay self-contained evidence-gathering tests per Test Plan, not modified or deleted here).

**Verify:** New tests in `tests/tools/test_monitoring_writer.py`, promoted from 2 of the candidate's
3 tests, targeting the real module:
- `test_single_writer_produces_one_well_formed_line` (via `write_line`, using `tmp_path`) — asserts
  exactly one well-formed JSON line, no `.lock` file left behind after success.
- `test_malformed_partial_line_is_rejected_by_downstream_reader` — promoted verbatim in spirit from
  the candidate.

---

### Step 3 — Add the diagnostic/health-file sidecar mechanism and the non-raising contract

**Files:** `tools/agent-monitoring/writer.py`, `tests/tools/test_monitoring_writer.py`.

**Change:** Implements Decisions #2 and #4.
- Add `_diagnostic_path_for(target_path: Path) -> Path` → `target_path.parent / ".writer_health.jsonl"`
  — a sidecar file living alongside the 3 corpus files under `agent-monitoring/`, never one of the 3
  primary corpus filenames, clearly named as a diagnostic file (leading dot, `_health` in the name).
- Add `_write_diagnostic(target_path: Path, stage: str, error: BaseException) -> None`: builds one
  JSON line — `{"ts": <UTC ISO8601>, "target": target_path.name, "stage": stage, "error_type": type(error).__name__, "error_message": str(error)[:500]}`
  (`stage` is one of `"lock_acquire"`, `"write"`, `"lock_release"`, see the **structural
  classification** rule below). **Review-phase required fix — committed atomicity technique**: append
  it via `fd = os.open(str(diagnostic_path), os.O_APPEND | os.O_CREAT | os.O_WRONLY); os.write(fd, line.encode("utf-8")); os.close(fd)`
  — a single `os.write()` syscall to an `O_APPEND`-opened fd, **not** Python's buffered `open(..., "a")`
  (which may issue multiple underlying `write()` syscalls and is not guaranteed atomic). One diagnostic
  line is always well under 4KB (fixed fields + `error_message` capped at 500 chars), so a single
  `os.write()` call is atomic against concurrent unlocked writers on Linux local filesystems — this is
  the specific atomicity commitment the diagnostic sidecar relies on, not merely "best-effort." The
  entire body of `_write_diagnostic` is wrapped in a broad `try: ... except Exception: pass` so a
  diagnostic-write failure (e.g. disk full) can never itself raise or cascade into blocking the caller
  — the diagnostic surface is best-effort at the "did it get recorded" level, but atomic at the
  "single-line-never-interleaves" level.
- Change `write_line`/`write_lines`'s bodies: wrap **each of the three regions separately** — lock
  acquisition, the file write, lock release — in its own `try/except Exception as e:`, so `stage` is
  determined **structurally by which region's `try` block caught the exception**, never by matching the
  exception's type. **Review-phase required fix**: do NOT classify by `isinstance(e, TimeoutError)` —
  Step 8's own test forces `os.open` to raise a plain `OSError` for `.lock`-suffixed paths, which fires
  inside `_acquire_lock`'s lock-acquisition loop but is not a `TimeoutError` (it isn't caught by
  `_acquire_lock`'s own `except FileExistsError:` clause either, so it propagates out of
  `_acquire_lock` immediately) — under a type-matching rule this would be misclassified or fall through
  unclassified. The correct structure:
  ```python
  def write_line(target_path: Path, line: str) -> bool:
      lock_path = _lock_path_for(target_path)
      try:
          _acquire_lock(lock_path)
      except Exception as e:
          _write_diagnostic(target_path, "lock_acquire", e)
          return False
      try:
          target_path.parent.mkdir(parents=True, exist_ok=True)
          with open(target_path, "a") as f:
              f.write(line + "\n")
      except Exception as e:
          _write_diagnostic(target_path, "write", e)
          return False
      finally:
          try:
              _release_lock(lock_path)
          except Exception as e:
              _write_diagnostic(target_path, "lock_release", e)
              # do not return False here if the write itself already succeeded —
              # a lock-release failure after a successful write is a diagnostic-worthy
              # event, not a reason to report the whole operation as failed
      return True
  ```
  (`write_lines` follows the identical three-region structure, writing all lines under one `open()`
  call inside the middle `try`.) This guarantees any exception raised anywhere in `_acquire_lock`
  (regardless of its exact type — `TimeoutError`, `OSError`, or anything else `os.open`/`os.close`
  might raise) is classified `"lock_acquire"` by virtue of *where* it was caught, not *what* it is.

**Do NOT touch:** Do not route `_write_diagnostic`'s own write through `write_line`/`write_lines` —
that would recurse on the same failure condition that triggered it (explicitly called out in the
ticket's Scope and Test Plan item 6).

**Verify:** New tests in `tests/tools/test_monitoring_writer.py`:
- `test_forced_lock_acquire_failure_returns_false_and_writes_diagnostic` — monkeypatch `os.open` to
  raise `OSError` for any path ending in `.lock` (matching Step 8's actual technique, not a
  `TimeoutError`-specific mock); assert `write_line(...)` returns `False` (does not raise) and
  `.writer_health.jsonl` gains exactly one line with `stage == "lock_acquire"` — proving the structural
  classification works regardless of exception type.
- `test_forced_write_failure_returns_false_and_writes_diagnostic` — monkeypatch `open`/the file-write
  step to raise `OSError`; assert `write_line(...)` returns `False`, no exception propagates, the
  lock file is not left behind (released in `finally` regardless), and `.writer_health.jsonl` gains
  one line with `stage == "write"`.
- `test_diagnostic_write_failure_itself_never_raises` — monkeypatch `os.open` to raise when called with
  the diagnostic path specifically; assert calling `_write_diagnostic(...)` directly raises nothing.
- `test_concurrent_diagnostic_writes_do_not_interleave` (**Review-phase required addition**) — spawn
  multiple threads/processes each calling `_write_diagnostic()` with a distinct `error_message`
  concurrently (mirrors Step 7's mixed-population concurrency test, but targeting the diagnostic
  sidecar itself); assert every resulting line in `.writer_health.jsonl` is valid, complete JSON with
  no truncated/merged lines — proving the single-`os.write()`-call atomicity commitment holds under
  real concurrent unlocked writers, the exact scenario (multiple writers failing together, e.g. disk
  full) where this file is most likely to receive concurrent writes.

---

### Step 4 — Migrate `post_tool_hook.py` to the new writer

**Files:** `tools/agent-monitoring/post_tool_hook.py`, `tests/tools/test_post_tool_hook.py` (field-set
assertions updated here, per Decision #5/#1 amendment; the `test_locking_failure_does_not_propagate`
rewrite is Step 8).

**Change:**
- Remove `import fcntl`.
- Add `sys.path.insert(0, str(Path(__file__).resolve().parent))` (mirrors `record_events.py`'s
  existing pattern) and `from writer import write_line`.
- Extend the existing sidecar-read block (current lines 43-55, reading `run_id`/`seq`/`phase`/`agent`
  from `.claude/current_run`) to also read `execution_id`, `provider`, `ticket_id` with the exact same
  `sidecar.get(...) or None` pattern already used for the other 4 fields — no new file, no new
  generation logic, purely additive keys read from the same sidecar dict that already exists.
- Add `execution_id`, `provider`, `ticket_id` to the `record` dict (alongside the existing 10 keys,
  making 13 total).
- Replace the `with open(tools_file, "a") as f: fcntl.flock(...); f.write(...); fcntl.flock(...)`
  block with: `tools_file.parent.mkdir(parents=True, exist_ok=True)` (kept) followed by
  `write_line(tools_file, json.dumps(record, separators=(",", ":")))`. The return value is not
  checked — `post_tool_hook.py`'s outer `try: ... except Exception: pass` already guarantees the
  script never raises regardless, and `write_line` never raises either now, so this is
  belt-and-suspenders by design, not a gap.

**Do NOT touch:** The outer `try: ... except Exception: pass` wrapper (lines 24-86) stays exactly as
today — it is a second, independent safety net, not made redundant by the writer's own
exception-swallowing (both may coexist). Do not add any stderr output here (the hook's own contract
is zero diagnostic output today; that stays unchanged — the new diagnostic file is the surface, not
stderr, per Decision #4 and `.claude/settings.json:90`'s existing `2>/dev/null` suppression).

**Verify:**
- `tests/tools/test_post_tool_hook.py::test_single_writer_produces_one_well_formed_line`,
  `test_phase_and_agent_included_when_sidecar_present`,
  `test_phase_and_agent_default_to_none_on_partial_sidecar`,
  `test_concurrent_writers_produce_no_interleaved_or_truncated_lines` — all 4 updated in this step to
  assert the new 13-key `_RECORD_FIELDS` set (adding `execution_id`, `provider`, `ticket_id`) instead
  of the old 10-key set, and to assert the 3 new fields default to `None` when absent from the
  sidecar (same pattern as `run_id`/`seq`/`phase`/`agent`).
- A new test `test_execution_identity_fields_included_when_sidecar_present`, extending the sidecar
  fixture used by `test_phase_and_agent_included_when_sidecar_present` to also include
  `execution_id`/`provider`/`ticket_id`, asserting they appear verbatim in the written record.

---

### Step 5 — Migrate `record_run.py` to the new writer

**Files:** `tools/agent-monitoring/record_run.py`, `tests/tools/test_record_run.py`.

**Change:**
- Add `sys.path.insert(0, str(Path(__file__).resolve().parent))` + `from writer import write_line`.
- Replace `with open(RUNS_FILE, "a") as f: f.write(json.dumps(record, separators=(",", ":")) + "\n")`
  with: `RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)` (kept) then
  `ok = write_line(RUNS_FILE, json.dumps(record, separators=(",", ":")))`.
- If `ok` is `False`, print `f"WARNING: append failed for run_id={record['run_id']}, see agent-monitoring/.writer_health.jsonl"`
  to stderr but **do not** `sys.exit(1)` — the process still exits 0 and still prints the existing
  `DONE:` line, since an append-layer failure must stay non-blocking to the calling workflow
  (Decision #2 / ticket AC). This is new behavior at this one call site only.
- No change to `REQUIRED`, `validate_record()`, `compute_duration_s()`, or the argparse/JSON-parsing
  error paths (lines 46-60) — those all still `sys.exit(1)` with `ERROR:`-prefixed stderr exactly as
  today, and run entirely before `write_line` is ever called.
- No new code is needed to "add" `execution_id`/`provider`/`ticket_id` — `record` is already an
  arbitrary caller-supplied dict from `--data`'s JSON (not filtered to a fixed key set anywhere in
  this file), so any of the 3 fields present in the caller's `--data` payload already flow through to
  the written line unchanged, both before and after this migration.

**Do NOT touch:** `REQUIRED`, `validate_record()`, `compute_duration_s()`, the CLI's `--data`
JSON-parse error handling, or the `ERROR:`/`sys.exit(1)` contract for any validation failure.

**Verify:**
- `tests/tools/test_record_run.py` — all existing tests must still pass unmodified (CLI
  exit-code/validation contract, `duration_s` computation).
- New test `test_execution_identity_fields_pass_through_unchanged` — call the CLI with `--data`
  including `execution_id`/`provider`/`ticket_id`, assert the written `runs.jsonl` line contains all
  3 verbatim.
- New test `test_append_failure_is_non_blocking` — monkeypatch (via the source-injection subprocess
  shim pattern already used by `test_post_tool_hook.py`, or a direct import-level monkeypatch since
  `record_run.py` is importable, unlike the hook) `writer.write_line` to return `False`; assert the
  process still exits 0 and a `WARNING:` line appears on stderr, distinguishing it from the
  `ERROR:`/exit-1 validation-failure path.

---

### Step 6 — Migrate `record_events.py` to `write_lines()`

**Files:** `tools/agent-monitoring/record_events.py`, `tests/tools/test_record_events.py`.

**Change:**
- Add `from writer import write_lines` (module is already on `sys.path` via the existing
  `sys.path.insert(0, str(Path(__file__).resolve().parent))` at line 9).
- Replace the batch-write block (`with open(EVENTS_FILE, "a") as f: for record in records: f.write(...)`)
  with: `EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)` (kept) then
  `lines = [json.dumps(record, separators=(",", ":")) for record in records]` then
  `ok = write_lines(EVENTS_FILE, lines)`. This preserves today's implicit "one batch write =
  contiguous lines in the file" property (Decision #3) — `write_lines` holds one lock acquisition for
  the whole batch, so this batch's N lines cannot interleave with a concurrent process's write.
  **Review-phase acknowledged tradeoff**: holding one lock for the whole batch means a large `records`
  payload increases the window in which a concurrent `post_tool_hook.py` single-line write could hit
  `_acquire_lock`'s `TimeoutError` ceiling (`MAX_RETRIES=200` × `RETRY_SLEEP_S=0.005` ≈ 1s) and fall
  through to the diagnostic-only path instead of writing. This is accepted, not silently ignored,
  because real `record_events.py` batches are small in practice — confirmed by inspecting this
  session's own real invocations against `agent-monitoring/events.jsonl`, consistently single-digit to
  low-teens records per call (one batch per ticket-pipeline-phase-sequence, not per individual event) —
  so realistic lock-hold time for `write_lines` is bounded by a handful of `f.write()` calls' disk I/O,
  not by an unbounded N. No artificial batch-size cap is added in this ticket (out of scope — would be
  a `record_events.py` CLI-contract change, not a writer-module change), but this tradeoff must be
  documented in `writer.py`'s own module docstring so a future caller passing a very large batch
  understands the starvation risk it introduces for concurrent single-line writers.
- If `ok` is `False`, print `f"WARNING: append failed for {len(records)} event record(s), see agent-monitoring/.writer_health.jsonl"`
  to stderr but do not `sys.exit(1)` — same non-blocking pattern as Step 5.
- No change to `validate_record()`, `compute_tool_stats()`, `warn_vocabulary_drift()`, or the
  per-record validation/summary-truncation loop in `main()` (lines 98-125) — all run and can still
  `sys.exit(1)` with `ERROR:` stderr before `write_lines` is ever reached.
- No new code needed for `execution_id`/`provider`/`ticket_id` passthrough, same reasoning as Step 5
  (`records` are arbitrary caller-supplied dicts, not filtered to a fixed key set).

**Do NOT touch:** `validate_record()`, `compute_tool_stats()`, `warn_vocabulary_drift()`,
`vocabulary.py` (explicitly out of scope, zero provider-awareness needed), or the existing
`ERROR:`/`sys.exit(1)` validation contract.

**Verify:**
- `tests/tools/test_record_events.py` — all existing tests must still pass unmodified.
- New test `test_execution_identity_fields_pass_through_unchanged` — batch `--data` including
  `execution_id`/`provider`/`ticket_id` on one or more records, assert verbatim passthrough.
- New test `test_batch_write_holds_contiguous_lines_under_concurrent_writer` — write an N-record
  batch via `record_events.py` concurrently with a separate direct `writer.write_line` call targeting
  the same file from another thread/process; assert the batch's own N lines remain contiguous in the
  file (not interleaved by the concurrent single-line write), proving `write_lines`'s one-lock-for-the-batch
  property.
- New test `test_append_failure_is_non_blocking` — same shape as Step 5's, monkeypatching
  `writer.write_lines` to return `False`.

---

### Step 7 — Promote/extend candidate concurrency-stress and stale-lock-recovery tests

**Files:** `tests/tools/test_monitoring_writer.py`.

**Change:** Add the two heaviest test cases, now that both the core mechanics (Step 2) and the
diagnostic/non-raising contract (Step 3) exist:
- `test_concurrent_writers_produce_no_interleaved_or_truncated_lines` — promoted from the candidate's
  `test_concurrent_writers_lockfile_produce_no_interleaved_or_truncated_lines` (10 threads × 20
  iterations = 200 invocations), but extended per Test Plan item 2 to simulate a **mixed** population:
  some invocations call `write_line` with a `post_tool_hook.py`-shaped record, some call `write_lines`
  with a small batch shaped like `record_events.py`'s output, all targeting the same `target_path`
  directly through the writer module (not through any of the 3 CLI/hook wrappers) — proving the
  shared module's correctness independent of any one caller's shape. Assert 0 corrupted/lost/duplicated/interleaved
  lines and no leftover `.lock` file.
- `test_stale_lock_is_removed_and_superseded` — create an abandoned `<target>.lock` file, backdate its
  `mtime` via `os.utime` to `time.time() - STALE_AFTER_S - 1` (never `time.sleep(STALE_AFTER_S + ...)`
  in the test), then call `write_line`. Assert, in this order: (a) the stale lock file is detected and
  removed (check `os.path.exists` transitions, not just end-to-end success), (b) a fresh lock is
  acquired and released normally, (c) the record is appended correctly, and (d) if a prior "abandoned
  write" is simulated (a pre-existing valid line written before the stale lock was abandoned), that
  line's content is untouched/not corrupted by the recovery.

**Do NOT touch:** `tests/tools/test_monitoring_writer_lockfile_candidate.py` — its 3 tests remain
as independent evidence-gathering tests, not deleted or modified (per Test Plan: either retiring or
keeping is acceptable, and this plan chooses to keep, since it costs nothing and preserves the
original evidence trail).

**Verify:** The 2 new tests above, both passing under the scoped pytest command
(`pytest tests/tools/test_monitoring_writer.py -v`).

---

### Step 8 — Rewrite `test_locking_failure_does_not_propagate`; finalize field-set assertions

**Files:** `tests/tools/test_post_tool_hook.py`.

**Change:**
- Rewrite `test_locking_failure_does_not_propagate` (currently a source-string-injection shim that
  monkeypatches `fcntl.flock`, which becomes a no-op once `post_tool_hook.py` no longer imports
  `fcntl` after Step 4). New version: keep the source-injection subprocess technique (the hook remains
  non-importable, so this remains the correct testing strategy per this test file's own documented
  pattern), but change what is shimmed — inject a shim that monkeypatches `os.open` to raise `OSError`
  whenever the target path ends in `.lock` (forcing a failure inside `_acquire_lock`'s lock-acquisition
  loop — per Step 3's structural classification, this is caught by `write_line`'s `"lock_acquire"`
  region regardless of the exception's type; it is **not** the `TimeoutError` `_acquire_lock` itself
  would raise after exhausting `MAX_RETRIES`, since the injected `OSError` propagates out of
  `_acquire_lock` immediately on its first `os.open` call, never reaching that point), executed before
  the hook body runs. Assert `result.returncode == 0` and
  `result.stderr == ""` (both unchanged expectations — the hook's outer `except Exception: pass` and
  the writer's own non-raising contract both still guarantee this), and additionally assert
  `agent-monitoring/.writer_health.jsonl` under the test's `cwd` gained exactly one diagnostic line
  with `stage == "lock_acquire"` — proving the failure was actually exercised and actually
  suppressed, not merely that the shim was a no-op again.
- Confirm (from Step 4) all 4 exact-field-set assertions (`test_single_writer_produces_one_well_formed_line`,
  `test_phase_and_agent_included_when_sidecar_present`,
  `test_phase_and_agent_default_to_none_on_partial_sidecar`,
  `test_concurrent_writers_produce_no_interleaved_or_truncated_lines`) now check the updated 13-key
  `_RECORD_FIELDS` constant (10 original + `execution_id`/`provider`/`ticket_id`), as exact-set
  equality — never loosened to `.issubset()`/`.issuperset()` (Test Plan Anti-Drift Test Guard).

**Do NOT touch:** Any other test in this file beyond the 5 named (4 field-set assertions from Step 4
+ this rewritten one) — the remaining test in the file needs no change.

**Verify:** `pytest tests/tools/test_post_tool_hook.py -v` — all 6 tests pass, including the rewritten
one proving suppression against the real new failure surface.

---

### Step 9 — Legacy-shape regression fixture + test

**Files:** `tests/tools/test_agent_ops_dashboard_ingest.py` (new test added).

**Change:** Add one new test, e.g. `test_load_jsonl_handles_all_legacy_shapes_plus_new_execution_identity_format`:
- Read the 6 existing real-corpus-extracted fixture files verbatim from
  `tests/fixtures/agent_monitoring/` (`shape1_started_finished_notes.jsonl` through
  `shape6_type_checker_exception.jsonl`) — do **not** add a 7th file to that directory (see Do NOT
  touch below).
- Construct one additional line **inline in the test** (a Python dict, not a fixture file) carrying
  the new-format execution-identity fields, e.g.
  `{"run_id": "TCK-FAKE-NEW-FORMAT", "workflow": "implement-ticket", "tier": "standard", "final_status": "DONE", "start_ts": "2026-07-22T00:00:00Z", "end_ts": "2026-07-22T00:05:00Z", "execution_id": "claude-TCK-FAKE-NEW-FORMAT-1234567890-abcd1234", "provider": "claude", "ticket_id": "TCK-FAKE-NEW-FORMAT"}`,
  serialized with `json.dumps(..., separators=(",", ":"))`.
- Write all 7 lines (6 real + 1 synthetic) to a `tmp_path` file and call `validate.load_jsonl` (via
  `ingest.load_jsonl`, the same function object) against it. Assert exactly 7 records are returned
  and zero exceptions are raised.
- Also assert `ingest.py`'s `load_jsonl_counted` wrapper reports `unparsed_lines == 0` for this
  fixture (none of the 6 legacy shapes nor the new-format line should be misclassified as unparsed).

**Do NOT touch:** `tests/fixtures/agent_monitoring/PROVENANCE.md` or add any new file to
`tests/fixtures/agent_monitoring/` — that directory's own documented rule
(`tests/fixtures/agent_monitoring/PROVENANCE.md`) is "every file is a byte-for-byte copy of one real
corpus line... do not hand-edit... never type the JSON out by hand." A synthetic execution-identity
line does not exist anywhere in the real corpus yet (this ticket is what introduces the shape), so it
must be constructed inline in the test file, never added to that fixture directory. Do not modify any
of the 6 existing fixture files.

**Verify:** The new test, plus confirming the existing `test_agent_monitoring_legacy_reader.py`
fixture-backed tests still pass unmodified (they read the same 6 files independently and are
unaffected by this addition).

---

### Step 10 — `ingest.py` + `models.py` extension for provider/execution_id/ticket_id

**Files:** `src/api/agent_ops_dashboard/models.py`, `src/api/agent_ops_dashboard/ingest.py`,
`tests/tools/test_agent_ops_dashboard_ingest.py`.

**Change:**

In `models.py`:
- Add to `RunSummary` (inherited by `RunDetail`): `provider: Optional[str] = None`,
  `execution_id: Optional[str] = None`, `ticket_id: Optional[str] = None` (raw passthrough values,
  `None` for any record that doesn't carry them — legacy or not-yet-migrated), plus one new computed
  field `identity_provenance: str` (never `None` — always one of `"native"` or `"legacy"`; see
  `ingest.py` change below for the resolver).

In `ingest.py`:
- Add `_resolve_identity_provenance(rec: dict) -> str`, placed next to `_resolve_final_status()`
  (line 187) as a sibling following the identical "prefer new field, fall back through legacy, never
  raise" pattern documented in that function's own docstring:
  ```python
  def _resolve_identity_provenance(rec: dict) -> str:
      """'native' if the record carries the new execution-identity fields (this
      migration or later); 'legacy' for any pre-migration record — mirrors
      _resolve_final_status's fallback-without-raising shape, but for identity
      rather than completion status."""
      return "native" if rec.get("execution_id") is not None else "legacy"
  ```
- Extend `_build_run_summary()` (line 332) to populate the 4 new `RunSummary` fields from `record`
  when `record is not None`: `provider=record.get("provider")`, `execution_id=record.get("execution_id")`,
  `ticket_id=record.get("ticket_id")`, `identity_provenance=_resolve_identity_provenance(record)`.
  For the inferred-active branch (`record is None`), set all 3 raw fields to `None` and
  `identity_provenance="legacy"` (an inferred-active run has no record at all yet, so it cannot be
  "native" — it simply has no identity data to report).
- Extend `get_runs()`'s (line 613) filter signature and body with 3 new optional keyword parameters —
  `provider: Optional[str] = None`, `execution_id: Optional[str] = None`, `ticket_id: Optional[str] = None`
  — each following the exact existing `if x is not None and field != x: continue` guard pattern
  already used for `status`/`workflow`/`since` (lines 630-635), applied against
  `summary.provider`/`summary.execution_id`/`summary.ticket_id`.
- No change to `_rebuild()`'s loading/grouping logic itself (`_group_runs_by_id`, `tools_by_seq`,
  etc.) — filtering happens at `get_runs()` read time against already-built `RunSummary` objects,
  consistent with how `status`/`workflow`/`since` already work; no new grouping structure is needed.

**Do NOT touch:** `query.py`, `validate.py` (`load_jsonl` read-only reuse only), `generate_retro.py`,
the SQLite index, or any code under `tickets/todos/agent-monitoring-derived-index/` — this step is a
dashboard-only additive read extension, not a general provider-aware read-side migration (that is the
explicitly out-of-scope dependent batch). Do not change `_resolve_final_status()` itself, only add a
sibling function next to it.

**Verify:**
- New test `test_run_summary_carries_provider_execution_id_ticket_id_when_present` — a fixture record
  with all 3 fields set, assert `_build_run_summary()`'s resulting `RunSummary` carries them verbatim
  and `identity_provenance == "native"`.
- New test `test_run_summary_labels_legacy_record_as_legacy_not_none_silently` — a fixture record
  using one of the 6 legacy shapes (reuse `tests/fixtures/agent_monitoring/shape2_final_status_no_end_ts.jsonl`'s
  content), assert `provider`/`execution_id`/`ticket_id` are `None` **and** `identity_provenance == "legacy"`
  (proving the label is explicit, not silently absent).
- New test `test_get_runs_filters_by_provider_and_execution_id` — a fixture corpus mixing legacy and
  new-format records, assert `get_runs(provider="claude")` and `get_runs(execution_id="...")` each
  return only the matching subset, and an unfiltered call still returns both legacy and new-format
  runs (never dropped or erroring).
- Guard test `test_ingest_load_jsonl_is_validate_load_jsonl` (if not already present in this file) —
  `assert ingest.load_jsonl is validate.load_jsonl`, proving this step did not fork read-side logic
  instead of reusing it (Test Plan Anti-Drift Test Guard, out-of-scope boundary check).
- Full existing suite: `pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py -v`
  must still pass unmodified (additive-only change).

---

### Step 11 — Exit-criterion manifest diff + final scoped verification pass

**Files:** none changed (read-only/verification procedure).

**Change:**
1. Run `tools/agent-monitoring/manifest.py::capture_lines(Path("agent-monitoring"))` again against
   the real `agent-monitoring/` directory (post-implementation state).
2. Load Step 1's entry-criterion scratch snapshot and call
   `manifest.assert_prefix_preserved(entry_snapshot, exit_snapshot)`. It must raise nothing. If any
   real writes landed in `agent-monitoring/*.jsonl` during this ticket's own test runs (it should
   not — all tests target `tmp_path`, per the Scope Guards below), this is where that regression
   would be caught.
3. Confirm no stray `.lock` file exists anywhere under the real `agent-monitoring/` directory
   (`ls agent-monitoring/*.lock` should find nothing).
4. Confirm whether `agent-monitoring/.writer_health.jsonl` exists in the real directory — it should
   not, unless a real writer failure genuinely occurred during this session's own tool use (in which
   case that is legitimate, expected behavior of the new diagnostic surface, not a bug).
5. Run the full scoped pytest command set from `test_plan.md`:
   ```
   pytest tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py -v
   pytest tests/tools/test_monitoring_writer_lockfile_candidate.py -v
   pytest tests/tools/test_monitoring_writer.py -v
   pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py -v
   ```
6. Discard the Step 1 scratch snapshot file (it must never be committed).

**Do NOT touch:** Nothing is edited in this step — it is pure verification.

**Verify:** All pytest commands above pass; `assert_prefix_preserved` raises nothing; no stray
`.lock` file; the ticket's own exit criterion is satisfied.

## Scope Guards

- Do not touch `tools/agent-monitoring/query.py`, `tools/agent-monitoring/validate.py` (except
  reading `load_jsonl`, never modifying it), or `tools/agent-monitoring/generate_retro.py` — owned by
  the dependent `agent-monitoring-derived-index` batch.
- Do not modify `tools/agent-monitoring/legacy_reader.py` or `tools/agent-monitoring/manifest.py` —
  read-only reuse only (`capture_lines`, `assert_prefix_preserved`, `classify_provenance`).
- Do not modify `tools/agent-monitoring/vocabulary.py` — zero provider-awareness needed, out of
  scope.
- Do not change `record_run.py`/`record_events.py`'s pre-write CLI validation/exit-code/stderr
  contract (`REQUIRED`, `validate_record()`, JSON-parse error handling) — only the append step
  changes.
- Do not let the new lock-file protocol leave a stray `.lock` file behind on the real
  `agent-monitoring/` directory under any test or crash scenario — every test in
  `tests/tools/test_monitoring_writer.py` must target `tmp_path`, never a path resolving under the
  real repo's `agent-monitoring/` directory (test-side guard, mirroring the candidate's inverted
  `_assert_not_real_corpus` precedent, enforced in the test suite rather than production code).
- Do not implement the SQLite index or any `query.py`/`validate.py`/`generate_retro.py`
  provider-aware read migration.
- Do not change `.claude/settings.json`'s `2>/dev/null` wiring for the `PostToolUse` hook — the
  diagnostic surface must work despite that suppression, not require removing it.
- Do not add a synthetic execution-identity line to `tests/fixtures/agent_monitoring/` or edit its
  `PROVENANCE.md` — that directory holds only byte-for-byte real-corpus extractions per its own
  documented rule; the new-format regression line is constructed inline in the test file instead.
- Do not import from `tests/tools/test_monitoring_writer_lockfile_candidate.py` in production code —
  `writer.py` is new code that reuses only the mechanics (constants, O_CREAT|O_EXCL sequence), never
  the candidate module itself, and never carries forward its `_assert_not_real_corpus` guard.
- Do not rewrite, reorder, or delete any pre-existing line in `agent-monitoring/runs.jsonl`,
  `events.jsonl`, or `tools.jsonl` — append-only, enforced by Steps 1 and 11's manifest diff.

## Dependency Map

- Step 1 has no dependencies; must run first (entry criterion).
- Step 2 depends on Step 1 only in ordering (no writer-file change before the entry snapshot) —
  otherwise independent.
- Step 3 depends on Step 2 (extends the same module's functions).
- Steps 4, 5, 6 each depend on Step 3 (need the finished `write_line`/`write_lines` public contract)
  but are independent of each other — any order among them is fine, and each is independently
  verifiable via its own test file.
- Step 7 depends on Step 3 (needs the diagnostic/non-raising contract in place to test the mixed
  population and stale-lock recovery against the real public API).
- Step 8 depends on Step 4 (rewrites a test that only makes sense once `post_tool_hook.py` no longer
  imports `fcntl`, and finalizes the field-set assertions Step 4 already updated).
- Step 9 is independent of Steps 2-8 — it only exercises `validate.load_jsonl` against fixture text,
  not the writer module itself. Can run any time after Step 1.
- Step 10 is independent of Steps 2-9 in mechanism (it's a pure read-side dashboard change) but
  logically follows Step 9 since its own tests reuse the same fixture-composition approach.
- Step 11 depends on all prior steps being complete (final verification and exit criterion).

## Acceptance Criteria Map

| AC from ticket (amended per Decision #1 to include `ticket_id`) | Implemented by step(s) | Verified by test |
|---|---|---|
| Entry criterion satisfied via `TCK-20260721-BASELINE-MONITORING-MANIFEST`'s manifest tool run against pre-migration corpus | Step 1 | Manual procedure check (Step 1 Verify); no pytest equivalent |
| Single shared Linux-only writer module used by all 3 call sites, not 3 ad hoc implementations | Steps 2, 3, 4, 5, 6 | New AST/import-graph guard test, `tests/tools/test_monitoring_writer_single_source.py` (added as part of Step 4-6's combined verification — asserts none of the 3 call sites imports `fcntl` or calls `os.open(..., O_CREAT \| O_EXCL ...)` directly, and all 3 import `writer.write_line`/`write_lines`) |
| Concurrency+crash-recovery stress test, 0 corrupted/interleaved/lost lines | Step 7 | `test_concurrent_writers_produce_no_interleaved_or_truncated_lines` in `tests/tools/test_monitoring_writer.py` |
| Simulated stale-lock recovery scenario passes | Step 7 | `test_stale_lock_is_removed_and_superseded` |
| New records carry additive `execution_id` + `provider` + `ticket_id` (amended); every legacy record shape still loads via `load_jsonl` with zero exceptions | Steps 4, 5, 6 (field passthrough/population), 9 (regression fixture) | Step 4's `test_execution_identity_fields_included_when_sidecar_present`; Steps 5/6's `test_execution_identity_fields_pass_through_unchanged`; Step 9's `test_load_jsonl_handles_all_legacy_shapes_plus_new_execution_identity_format` |
| `ingest.py` groups/filters by `provider`/`execution_id` (amended: + `ticket_id`), visibly labels legacy/unknown records | Step 10 | `test_get_runs_filters_by_provider_and_execution_id`, `test_run_summary_labels_legacy_record_as_legacy_not_none_silently` |
| Writer failures non-blocking; recorded via out-of-band diagnostic surface, never re-entering the writer | Steps 3 (mechanism), 4/5/6 (call-site integration) | Step 3's `test_forced_lock_acquire_failure_returns_false_and_writes_diagnostic`, `test_forced_write_failure_returns_false_and_writes_diagnostic`, `test_diagnostic_write_failure_itself_never_raises`; Step 8's rewritten `test_locking_failure_does_not_propagate`; Steps 5/6's `test_append_failure_is_non_blocking` |
| Exit criterion: manifest diff shows only new appends, zero rewrites/reorders/deletions | Step 11 | `manifest.assert_prefix_preserved()` procedure (Step 11 Verify) |
| Scope disambiguated from SQLite index / derived-index batch: no changes to `query.py`/`validate.py`/`generate_retro.py` | All steps (Scope Guards enforced throughout) | Step 10's `test_ingest_load_jsonl_is_validate_load_jsonl` guard; absence of any diff to those 3 files, checked at Implement/Verify time |

## Anti-Drift Notes

- **`_assert_not_real_corpus` inversion**: the candidate's test-safety guard must never appear in
  `writer.py` (Step 2) — its entire purpose in production is to write under the real
  `agent-monitoring/` directory. The equivalent safety property is enforced in the opposite place: a
  test-side guard in `tests/tools/test_monitoring_writer.py` (and `test_post_tool_hook.py`,
  `test_record_run.py`, `test_record_events.py`) confirming no test ever targets a path resolving
  under the real repo's `agent-monitoring/` directory.
- **Two independent exception-safety nets are not redundant, and both must remain**:
  `post_tool_hook.py`'s outer `except Exception: pass` (unchanged, Step 4) and `writer.py`'s own
  catch/diagnostic/return-`bool` contract (Step 3) are deliberately layered — do not remove either
  one on the theory that the other makes it unnecessary.
- **`record_run.py`/`record_events.py`'s two failure modes must stay visibly distinct**: a
  *validation* failure is still `ERROR:` + `sys.exit(1)`, exactly as today, and happens before
  `write_line`/`write_lines` is ever called; an *append* failure (post-validation) is a new
  `WARNING:` + exit 0 path. A future change that collapses these into one code path or one message
  prefix would silently break the existing subprocess-based CLI-contract tests.
- **`tools.jsonl` gaining `execution_id`/`provider`/`ticket_id` is a real, intentional schema change**
  to the fixed 10-key set that 4 tests in `test_post_tool_hook.py` previously asserted exactly — this
  is expected and must be reflected in `_RECORD_FIELDS`, not treated as unrelated collateral damage
  discovered later.
- **`write_lines`'s one-lock-per-batch property is load-bearing for `record_events.py`**, preserving
  today's implicit "one batch write = contiguous lines" property (Decision #3) — do not let a future
  refactor of `record_events.py` call `write_line` in a loop instead, which would silently reintroduce
  the interleaving-across-processes risk this step was designed to avoid.
- **The diagnostic sidecar (`agent-monitoring/.writer_health.jsonl`) is not a 4th corpus file** — it
  is explicitly out of scope for `ingest.py`/`query.py`/`validate.py`/`generate_retro.py` to ever
  read or display; it exists solely for a human or a future tooling pass to inspect directly.
- **Ticket AC amendment (Decision #1) must be visible in the final ticket update**: when this ticket
  moves to `tickets/done/`, its own AC checklist text should be updated (or annotated) to reflect that
  `ticket_id` was added to the additive-field scope, consistent with how this plan documents the
  amendment — this is an Implementer/Finalize-phase note, not a Plan-phase file change.

## Deviations (recorded at Implement phase)

- **Steps 2 and 3 were implemented as a single pass, not two incremental edits.** `writer.py` was
  written directly in its final Step-3 shape (non-raising, three-region try/except, structural
  exception classification, diagnostic sidecar with the single-`os.write()` atomicity commitment).
  Step 2's intermediate "raise on failure" shape described in the plan was never separately
  materialized as a commit/edit — only the cumulative end state matters for a single Implement
  session, and that end state matches Step 3's corrected code exactly, including the literal
  `write_line` structure quoted in the plan.
- **Step 8's rewritten `test_locking_failure_does_not_propagate` needed an additional `sys.path`
  fix the plan did not anticipate.** The existing source-string-injection technique (read
  `post_tool_hook.py`'s source as text, prepend a monkeypatch shim, write the combined source to a
  new file in `tmp_path`, execute that file) breaks `post_tool_hook.py`'s own
  `sys.path.insert(0, str(Path(__file__).resolve().parent))` line once the hook imports a sibling
  module (`from writer import write_line`, added in Step 4): `__file__` inside the shim resolves to
  the shim's `tmp_path` location, not the real `tools/agent-monitoring/` directory, so `writer.py`
  is not found there. Fixed by having the test's shim source insert the real
  `tools/agent-monitoring/` directory into `sys.path` itself (position 0, ahead of the hook's own
  now-redundant-but-harmless insert of the shim's tmp_path) before the hook source runs. This is a
  test-file-only fix (`tests/tools/test_post_tool_hook.py`); no production code was affected. The
  monkeypatch target itself (`os.open` raising for `.lock`-suffixed paths) matches the plan exactly.
- **`_write_diagnostic` builds its JSON line via `json.dumps(record, separators=(",", ":"))`
  instead of manual string formatting/escaping.** The plan's prose described the record's shape but
  did not mandate a specific construction technique; `json.dumps` is safer against escaping bugs
  (e.g. an `error_message` containing a literal quote or backslash) and the required atomicity
  property is unaffected — the line is still written via exactly one `os.write()` syscall on an
  `O_APPEND`-opened fd.
- **No other deviations.** File layout, package boundaries, Scope Guards, and the Acceptance
  Criteria Map were all followed as written.
