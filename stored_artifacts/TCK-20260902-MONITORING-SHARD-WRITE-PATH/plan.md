---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260902-MONITORING-SHARD-WRITE-PATH
artifact_type: plan
tags: [agent-monitoring, observability, hooks]
---

# Implementation Plan — TCK-20260902-MONITORING-SHARD-WRITE-PATH

## Summary

Cut over `post_tool_hook.py`'s single hardcoded append target
(`agent-monitoring/tools.jsonl`) to a per-ISO-week shard file
(`agent-monitoring/tools/tools-YYYY-Www.jsonl`), computed at write time from one captured
`datetime.now(timezone.utc)` instant shared with the existing `ts` field. The `%G-W%V` format is
duplicated locally (not imported from `generate_retro.py`) to keep the hot, every-tool-call hook's
import graph stdlib-only, with a comment cross-referencing `generate_retro.py::iso_week()` so a
future format change is caught by convention. `writer.py` is untouched — its lock-file and mkdir
logic are already fully generic on `target_path`. The plan adds four new subprocess-driven tests to
`tests/tools/test_post_tool_hook.py` (reusing the file's existing shim technique to control "now"),
adapts the file's shared `_tools_lines()` helper so the 12 pre-existing tests keep passing against
the new sharded path, adds a `merge=union` line for the new shard glob to `.gitattributes` (keeping
the legacy line), extends the existing `.gitattributes` test module (no new test module), and
updates only `docs/agent-monitoring/schema.md`'s `## agent-monitoring/tools.jsonl` section —
opportunistically correcting that section's pre-existing stale `fcntl`-locking description in the
same paragraph edit.

**Decisions locked in by this plan** (all three of the ticket's Assumptions/Open Questions items
requiring a Plan-level call):

- **Decision 3 (shared helper vs. duplicate): duplicate.** Accepting investigation's
  recommendation as-is. `generate_retro.py` is 2,344 lines and pulls in `sqlite3`, `re`, three
  cross-module imports (`tag_registry`, `tag_report`, `validate_frontmatter`) that
  `post_tool_hook.py` has no other need for — importing it into a hook that fires synchronously on
  every tool call across every concurrent session would add real per-invocation cost purely to
  reuse a one-line `strftime` call. A new shared module is ruled out too: it adds a new import edge
  to the hot path for a single stable, low-drift-risk stdlib format string (`"%G-W%V"`), and this
  file already has an on-point precedent for exactly this trade-off (`post_tool_hook.py:66-69`,
  the sidecar-reading logic deliberately not unified with `tools/retrieval_cache.py`'s
  `read_current_run_sidecar()`, "kept in sync by convention"). Extracting into `writer.py` is
  separately ruled out by this ticket's own Acceptance Criteria ("No functional change to
  `writer.py`").
- **Decision 6 (doc scope): confirmed — `docs/agent-monitoring/schema.md` only.**
  `docs/agent-monitoring/README.md`, `docs/guides/agent_monitoring.md`, and
  `docs/ai/system_overview.md` §6 all reference `tools.jsonl` only as a dataset/source name in
  report-semantics or architecture-summary prose, never as a physical-path claim a reader relies on
  for correctness — read and confirmed directly (see Step 6). They are excluded from this ticket's
  scope; touching them would be unrequested drift into child ticket 3's (reader-visibility) territory.
- **Decision 7 (pre-existing `fcntl` doc drift): fix opportunistically, same paragraph.**
  `docs/agent-monitoring/schema.md`'s "Write locking" subsection (confirmed at the paragraph
  starting "The `PostToolUse` hook (`post_tool_hook.py`) wraps its open+write block in
  `fcntl.flock(...)`") describes the pre-`TCK-20260721-MONITORING-WRITER-UNIFICATION`
  implementation; the current code (confirmed by direct read, `post_tool_hook.py:10`,
  `:153-155`) routes through `writer.py::write_line()`'s `O_CREAT|O_EXCL` lock-file protocol, no
  `fcntl` anywhere. This ticket's Scope already mandates editing this exact subsection for the
  per-ISO-week file-naming language; correcting the `fcntl` description in the same edit is
  same-paragraph, low-risk, and produces materially truer output — not scope creep into a separate
  ticket for one paragraph already being touched.

## Steps

### Step 1 — Cut over the hook's write-path computation and target, adapt the shared test-path helper

**Files:** `tools/agent-monitoring/post_tool_hook.py`, `tests/tools/test_post_tool_hook.py`
(`_tools_lines()` helper only, lines 51-53)

**Change:**
In `post_tool_hook.py`, replace line 54 (`now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")`,
confirmed by direct read) with a single captured instant deriving both `ts` and the ISO week:

```python
now_dt = datetime.now(timezone.utc)
now = now_dt.isoformat().replace("+00:00", "Z")
iso_week = now_dt.strftime("%G-W%V")  # matches generate_retro.py::iso_week() (tools/agent-monitoring/generate_retro.py:126)
                                        # and its --week current-week default (generate_retro.py:152).
                                        # Duplicated (not imported) to keep this hot hook's import
                                        # graph stdlib-only — see Decision 3 in plan.md. If this
                                        # format ever changes, update generate_retro.py::iso_week() too.
```

Replace lines 153-155 (`tools_file = Path("agent-monitoring/tools.jsonl")` /
`tools_file.parent.mkdir(...)` / `write_line(tools_file, ...)`, confirmed by direct read) with:

```python
tools_file = Path("agent-monitoring/tools") / f"tools-{iso_week}.jsonl"
tools_file.parent.mkdir(parents=True, exist_ok=True)
write_line(tools_file, json.dumps(record, separators=(",", ":")))
```

**Keep the `tools_file.parent.mkdir(parents=True, exist_ok=True)` call — do not drop it as
"redundant" with `write_line`'s own internal mkdir.** Confirmed by direct read of `writer.py`:
`write_line` (`writer.py:107-134`) calls `_acquire_lock(lock_path)` (`writer.py:115`) — which does
`os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)` (`writer.py:53`) — **before** its
own `target_path.parent.mkdir(...)` at `writer.py:120`. On a truly fresh checkout with no
`agent-monitoring/tools/` directory yet, if the hook's own pre-emptive mkdir were removed, the
first `_acquire_lock` call's `os.open` for the lock file would raise `FileNotFoundError` (no such
directory) rather than the `FileExistsError` its retry loop special-cases (`writer.py:56`); that
`FileNotFoundError` is still caught by `write_line`'s own outer `except Exception as e:`
(`writer.py:116`), routed to `_write_diagnostic(..., "lock_acquire", e)`, and returns `False` — so
this would not break the fail-silent contract, but it would spuriously log a `lock_acquire`
diagnostic failure on every process's first-ever write to a new week's directory. Keeping the
hook's own mkdir (running before `write_line` is called at all) avoids this entirely.

**No other writers to this resource in this repo.** `agent-monitoring/tools.jsonl` /
`agent-monitoring/tools/tools-*.jsonl` has exactly one writer: this hook. (`record_run.py` writes
`agent-monitoring/runs.jsonl`; `record_events.py` writes `agent-monitoring/events.jsonl`; neither
touches the tools file — confirmed by investigation's read of `writer.py`'s three callers, and by
this file's own module docstring, `post_tool_hook.py:2`.) No ordering/race/collision concern beyond
the per-shard-file locking `writer.py` already provides generically.

In `tests/tools/test_post_tool_hook.py`, update the shared `_tools_lines(cwd)` helper
(`tests/tools/test_post_tool_hook.py:51-53`, currently hardcoded to
`cwd / "agent-monitoring" / "tools.jsonl"`) so the 12 pre-existing tests that call it (none of
which freeze "now") keep locating the correct file:

```python
from datetime import datetime, timezone  # add to the existing import block (json, subprocess, sys, ThreadPoolExecutor, Path)

def _tools_lines(cwd):
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    tools_file = cwd / "agent-monitoring" / "tools" / f"tools-{iso_week}.jsonl"
    return tools_file.read_text().splitlines()
```

This mirrors production's own computation exactly (same format string, same UTC now), so it stays
correct for every un-frozen test. `test_locking_failure_does_not_propagate`
(lines 369-415) does not call this helper — it reads `.writer_health.jsonl` directly and is
unaffected by this change.

**Do NOT touch:** `writer.py` (zero changes — AC-mandated); the record dict's 13 field
names/shape (`post_tool_hook.py:137-151`); any other test file in this suite; the sidecar-reading
block (`post_tool_hook.py:90-127`, unrelated to write-path targeting).

**Verify:** `pytest tests/tools/test_post_tool_hook.py -v` — all 12 pre-existing tests
(`test_single_writer_produces_one_well_formed_line`, `test_phase_and_agent_included_when_sidecar_present`,
`test_execution_identity_fields_included_when_sidecar_present`,
`test_phase_and_agent_default_to_none_on_partial_sidecar`,
`test_concurrent_writers_produce_no_interleaved_or_truncated_lines`, the 8 sidecar-attribution
tests, and `test_locking_failure_does_not_propagate`) pass against the new sharded path with no
behavior change.

---

### Step 2 — Add the three "correct shard targeting" tests, reusing the file's existing time-freezing shim technique

**Files:** `tests/tools/test_post_tool_hook.py` (new tests + one new shared shim helper)

**Change:** No `freezegun`-equivalent exists in this repo (confirmed: not in `requirements.txt`/
`requirements-knowledge.txt`, no test in the suite imports it). Reuse this file's own established
in-file precedent for controlling test-only behavior in a subprocess-invoked, non-importable
top-level script: `test_locking_failure_does_not_propagate`'s technique of reading
`_HOOK_PATH.read_text()` (`tests/tools/test_post_tool_hook.py:376`), prepending a small patch
block, writing the combined source to a file under `tmp_path`, and running that file as the
subprocess (`tests/tools/test_post_tool_hook.py:395-405`).

Add one new shared helper, `_run_hook_with_frozen_now(cwd, payload, frozen_iso)`, following that
exact pattern but freezing the clock instead of forcing a lock failure. Because
`post_tool_hook.py` does `from datetime import datetime, timezone` (module-level, line 6), a shim
that reassigns `datetime.datetime` (the class attribute on the *module* `datetime`, not the name
already bound in the hook's namespace) before that import statement executes will be picked up by
the hook's own `from datetime import datetime` — Python resolves `from X import Y` via
`getattr(X, "Y")` at the time the import statement runs, and the shim's patch code is textually
prepended before `hook_source`, so it runs first:

```python
def _run_hook_with_frozen_now(cwd, payload, frozen_iso):
    hook_source = _HOOK_PATH.read_text()
    shim_source = (
        f"import sys as _sys\n"
        f"_sys.path.insert(0, {str(_MONITORING_TOOLS_DIR)!r})\n"
        "import datetime as _dt_module\n"
        f"_FROZEN = _dt_module.datetime.fromisoformat({frozen_iso!r})\n"
        "class _FrozenDatetime(_dt_module.datetime):\n"
        "    @classmethod\n"
        "    def now(cls, tz=None):\n"
        "        return _FROZEN if tz is None else _FROZEN.astimezone(tz)\n"
        "_dt_module.datetime = _FrozenDatetime\n"
        "\n"
        + hook_source
    )
    shim = cwd / f"post_tool_hook_frozen_now_shim_{frozen_iso.replace(':', '')}.py"
    shim.write_text(shim_source)
    return subprocess.run(
        [sys.executable, str(shim)],
        input=json.dumps(payload),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
    )
```

(`frozen_iso` passed pre-formatted as e.g. `"2026-08-31T12:00:00+00:00"` so
`datetime.fromisoformat` parses it directly without the hook's own `Z`-suffix handling being
involved in the shim itself.)

Add three tests using this helper:

1. **`test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl`** — freeze to
   `2026-08-31T12:00:00+00:00` (ISO week `2026-W36`, confirmed via
   `datetime.fromisoformat("2026-08-31T12:00:00+00:00").strftime("%G-W%V")`). Assert
   `result.returncode == 0`; assert `(tmp_path / "agent-monitoring" / "tools" / "tools-2026-W36.jsonl").exists()`
   and its single line parses with `set(record.keys()) == _RECORD_FIELDS`; assert
   `not (tmp_path / "agent-monitoring" / "tools.jsonl").exists()` (the legacy path must never be
   created).

2. **`test_two_different_iso_weeks_write_to_two_distinct_shard_files`** — one invocation frozen to
   `2026-08-31T12:00:00+00:00` (`2026-W36`), a second frozen to `2026-09-07T12:00:00+00:00`
   (`2026-W37`, confirmed the same way). Assert both shard files exist, each contains exactly one
   line, and each line's `input_summary` matches only its own invocation's distinct `_payload(command=...)`
   value (reusing `_payload`'s existing `command` parameter, matching the concurrency test's
   established pattern of keying assertions off distinct command strings).

3. **`test_iso_week_shard_directory_created_on_first_write`** — on a `tmp_path` with no
   pre-existing `agent-monitoring/` directory (already the default for every test in this file,
   since each gets a fresh `tmp_path`), one frozen invocation must create
   `agent-monitoring/tools/` (not just `agent-monitoring/`) and the shard file inside it. This
   exercises the `parent.mkdir(parents=True, exist_ok=True)` codepath from Step 1 directly, guarding
   against a future edit dropping the hook's own pre-emptive mkdir call as apparent redundancy.

**Do NOT touch:** the existing `test_locking_failure_does_not_propagate` shim or its own inline
`os.open` patch — the new `_run_hook_with_frozen_now` helper is additive, not a replacement.

**Verify:** `pytest tests/tools/test_post_tool_hook.py -v -k "frozen_now or iso_week or shard"`
(new tests only), then the full file per Step 1's verification.

---

### Step 3 — Add the fail-silent guard test for the ISO-week computation

**Files:** `tests/tools/test_post_tool_hook.py`

**Change:** Add `test_iso_week_computation_failure_does_not_propagate`, following
`test_locking_failure_does_not_propagate`'s shim pattern but forcing the clock read itself to
raise (not the lock-acquire step). Since Step 1 makes both `ts` and `iso_week` derive from one
`now_dt = datetime.now(timezone.utc)` call, forcing `datetime.now` to raise fails the whole record
build before `write_line` is ever reached — the correct behavior to assert here, distinct from the
existing lock-failure test where the record *is* built successfully and only the write fails:

```python
def test_iso_week_computation_failure_does_not_propagate(tmp_path):
    hook_source = _HOOK_PATH.read_text()
    shim_source = (
        "import datetime as _dt_module\n"
        "class _RaisingDatetime(_dt_module.datetime):\n"
        "    @classmethod\n"
        "    def now(cls, tz=None):\n"
        "        raise RuntimeError('forced clock failure for test')\n"
        "_dt_module.datetime = _RaisingDatetime\n"
        "\n"
        + hook_source
    )
    shim = tmp_path / "post_tool_hook_clock_failure_shim.py"
    shim.write_text(shim_source)

    result = subprocess.run(
        [sys.executable, str(shim)],
        input=json.dumps(_payload()),
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert not (tmp_path / "agent-monitoring" / "tools").exists()
    assert not (tmp_path / "agent-monitoring" / "tools.jsonl").exists()
```

This does not need `sys.path.insert` for `writer` (unlike the locking-failure shim) because
`write_line` is never reached — the failure happens before line 10's import is even used.

**Do NOT touch:** the outer `try/except Exception: pass` boundary in `post_tool_hook.py` itself —
this step is test-only; if this test fails, the fix is in Step 1's placement of the `now_dt`
computation (verify it stays textually between the `try:` at line 47 and `except Exception: pass`
at line 157), not a new inner try/except around just the clock read.

**Verify:** `pytest tests/tools/test_post_tool_hook.py::test_iso_week_computation_failure_does_not_propagate -v`

---

### Step 4 — Add the `.gitattributes` shard glob entry

**Files:** `.gitattributes`

**Change:** Confirmed by direct read (`.gitattributes:1-9`): the file has exactly 4
`merge=union` lines under one comment block, including `agent-monitoring/tools.jsonl merge=union`
at line 8. Add one new line immediately after it, keeping the existing line unchanged:

```
agent-monitoring/tools.jsonl merge=union
agent-monitoring/tools/*.jsonl merge=union
```

**Other writers to this resource:** `.gitattributes` is read by `git` itself at merge time and by
exactly one test module (`tests/integrity/test_merge_union_gitattributes.py`, extended in Step 5).
No other tooling in this repo writes or regenerates `.gitattributes` (confirmed: it is not one of
the files `make docs-registry`/Finalize's post-migration self-check touches — that only rewrites
`docs/REGISTRY.yaml`, which is explicitly *not* union-merged, per this file's own trailing
comment). No collision risk from concurrent writers.

**Do NOT touch:** the `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, or
`tickets/working_log.csv` lines, or the trailing `docs/REGISTRY.yaml` comment block — none are in
scope.

**Verify:** `tests/integrity/test_merge_union_gitattributes.py::test_gitattributes_lines_present_for_all_four_union_merge_paths`
must still pass unmodified (it only asserts the original 4 lines are present, not that no others
exist), plus the new assertions added in Step 5.

---

### Step 5 — Extend the existing `.gitattributes` test module (no new test module)

**Files:** `tests/integrity/test_merge_union_gitattributes.py`

**Change:** This file already owns `.gitattributes` coverage (confirmed via test_plan's
`grep -rl gitattributes tests/` finding) — extend it, do not create a new module.

1. Add a new assertion (either inline in the existing
   `test_gitattributes_lines_present_for_all_four_union_merge_paths` test, renamed if the "four"
   in its name becomes misleading, or — preferred, to avoid an unrelated rename — a new sibling
   test `test_gitattributes_line_present_for_shard_glob`) asserting the literal line
   `agent-monitoring/tools/*.jsonl merge=union` is present in the real `.gitattributes`, using the
   same `(Path(__file__).parent.parent.parent / ".gitattributes").read_text()` +
   string-membership style the existing test already uses. Also assert the old
   `agent-monitoring/tools.jsonl merge=union` line is still present (guards against this ticket
   accidentally doing child ticket 2's job of removing it).

2. Extend the parametrized `test_concurrent_branch_appends_merge_without_conflict_markers` test's
   `tracked_filename` parametrize list with one new case,
   `"agent-monitoring/tools/tools-2026-W36.jsonl"`, to prove the real git-level union-merge
   behavior (not just the static `.gitattributes` line) resolves correctly for a path one
   directory deeper than the existing four flat paths. The existing `_init_repo_with_union_attribute`
   helper already does `target.parent.mkdir(parents=True, exist_ok=True)` — confirmed no helper
   changes needed for a nested path.

**Other writers to this resource:** none — this is a read-only test file asserting against the
real repo's `.gitattributes` (Step 4) and against synthetic git repos it constructs itself in
`tmp_path`; no shared/concurrent-write concern.

**Do NOT touch:** the other 3 parametrize cases (`agent-monitoring/runs.jsonl`,
`agent-monitoring/events.jsonl`, `tickets/working_log.csv`) or any test unrelated to
`.gitattributes`.

**Verify:** `pytest tests/integrity/test_merge_union_gitattributes.py -v`

---

### Step 6 — Update `docs/agent-monitoring/schema.md`'s `## agent-monitoring/tools.jsonl` section only

**Files:** `docs/agent-monitoring/schema.md`

**Change:** Confirmed by direct read that exactly two things in this section need updating, both
within it:

1. **File-layout framing.** The section currently documents the per-record field schema (13
   fields, `session_id` through `duration_ms`+the 3 execution-identity fields — table confirmed
   present, unchanged, do not touch) but does not currently state a physical file-naming
   convention in the excerpt read. Add a short paragraph near the top of the section stating: new
   tool-call rows are appended to `agent-monitoring/tools/tools-YYYY-Www.jsonl`, one file per UTC
   ISO week (`%G-W%V`, matching `generate_retro.py::iso_week()`'s format and the
   `agent-monitoring/retro/RETRO-YYYY-Www.md` naming convention it already documents elsewhere),
   computed at write time; the historical `agent-monitoring/tools.jsonl` (pre-cutover rows) remains
   present and unchanged, frozen, pending a future migration ticket. The per-record schema itself
   is unaffected — only where a new record physically lands changes.

2. **"Write locking" subsection — fix the pre-existing `fcntl` drift in the same edit (Decision
   7).** Confirmed by direct read: the subsection currently reads *"The `PostToolUse` hook
   (`post_tool_hook.py`) wraps its open+write block in `fcntl.flock(f, fcntl.LOCK_EX)` (released
   via `fcntl.flock(f, fcntl.LOCK_UN)` after the write) so concurrent hook invocations ... serialize
   their appends..."* — this is the pre-`TCK-20260721-MONITORING-WRITER-UNIFICATION`
   implementation; confirmed by direct read the current code has no `fcntl` import anywhere and
   routes through `writer.py::write_line()`'s `O_CREAT|O_EXCL` lock-file protocol
   (`writer.py:37-38`, `:107-134`). Rewrite this paragraph to describe the actual current
   mechanism: `write_line()` acquires a per-target-file lock (`<target>.lock`, derived generically
   from the shard's own path, so locking is naturally per-shard post-cutover) via
   `os.open(..., O_CREAT | O_EXCL | O_WRONLY)` with bounded retry and stale-lock recovery, before
   appending; a lock-acquire or write failure never propagates — it is caught, logged to
   `.writer_health.jsonl`, and the hook's own outer `try/except Exception: pass` (unchanged)
   guarantees the tool call is never blocked. Keep this subsection's existing final sentence about
   the advisory/POSIX-only nature of the guarantee — that claim is still accurate for
   `writer.py`'s lock-file mechanism (also POSIX-only, `os.open` with `O_EXCL`).

**Other writers to this resource:** `docs/agent-monitoring/schema.md` has no automated
writer/regenerator (confirmed: not touched by `make docs-registry`, `make knowledge-index-update`
only reads/indexes it, doesn't rewrite its content) — safe for a direct hand edit. Per CLAUDE.md's
"After Work" rule, `make knowledge-index-update` must still be run once this file is modified
(covered in Step 7).

**Do NOT touch:** `docs/agent-monitoring/README.md`, `docs/guides/agent_monitoring.md`,
`docs/ai/system_overview.md` §6 — confirmed by direct read (matching investigation's
classification, Decision 6 above) that none asserts a physical path claim this ticket's change
would make inaccurate; all three describe `tools.jsonl` only as a logical dataset/source name in
report-semantics or architecture-summary prose. Also do not touch the per-record field table
itself (schema/field documentation is explicitly unchanged — only file-layout framing changes),
and do not touch any other section of `schema.md` (`runs.jsonl`, `events.jsonl` sections).

**Verify:** No automated test covers doc prose content directly; verify by re-reading the edited
section against `post_tool_hook.py`'s actual post-Step-1 code and `writer.py`'s actual code for
accuracy (manual parity check, consistent with this ticket having no parity-ledger entry per
investigation's "Parity Ledger Overlap" finding — pure `tools/` infrastructure, not a Mechanics
Bible/engine-contract claim).

---

### Step 7 — Full scoped regression run + doc-index refresh

**Files:** none (verification only)

**Change:** Run the full scoped regression surface named in test_plan.md:

```
pytest tests/tools/test_post_tool_hook.py -v
pytest tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_single_source.py tests/tools/test_monitoring_writer_lockfile_candidate.py -v
pytest tests/integrity/test_merge_union_gitattributes.py -v
```

All three commands must pass with zero failures/errors before this ticket is considered complete.
Then, because Step 6 modified a file under `docs/`, run `make knowledge-index-update` per
CLAUDE.md's "After Work" rule.

**Do NOT touch:** `tests/tools/test_generate_retro.py`, `tests/tools/test_build_index.py`, any
`query.py`/`validate.py` test — explicitly out of scope (child ticket 3's readers); do not run
`pytest tests/` unscoped.

**Verify:** All listed pytest invocations exit 0; `make knowledge-index-update` completes without
error.

## Scope Guards

- Do not modify `tools/agent-monitoring/writer.py` in any way (AC-mandated: "No functional change
  to `writer.py`"). Verified in Step 1 that zero changes to it are needed.
- Do not modify `tools/agent-monitoring/generate_retro.py`, `query.py`, `validate.py`,
  `build_index.py` — all four readers are explicitly deferred to child ticket 3
  (`TCK-20260902-MONITORING-SHARD-CONSUMERS`). Do not add shard-glob awareness to
  `generate_retro.py::DEFAULT_TOOLS_FILE` or similar, even opportunistically.
- Do not delete, rename, move, or append to the historical `agent-monitoring/tools.jsonl` file. It
  stays present and frozen after cutover, pending child ticket 2
  (`TCK-20260902-MONITORING-SHARD-MIGRATION`).
- Do not remove the existing `agent-monitoring/tools.jsonl merge=union` line from
  `.gitattributes` — only add the new shard-glob line alongside it.
- Do not change the 13-field record shape written by `post_tool_hook.py`
  (`session_id`/`run_id`/`seq`/`phase`/`agent`/`ts`/`tool`/`input_summary`/`status`/`duration_ms`/
  `execution_id`/`provider`/`ticket_id`) — this ticket only changes *where* the same-shaped record
  is written.
- Do not touch `docs/agent-monitoring/README.md`, `docs/guides/agent_monitoring.md`, or
  `docs/ai/system_overview.md` §6 (Decision 6, confirmed no physical-path claim needs updating).
- Do not touch the sidecar-reading/attribution logic (`post_tool_hook.py:66-127`) or the
  `_prune_stale_scoped_sidecars()` function — unrelated to write-path targeting.
- Do not introduce a new time-mocking dependency (e.g. `freezegun`) — reuse the file's existing
  source-shim technique exclusively.
- Do not create a new test module for `.gitattributes` coverage — extend
  `tests/integrity/test_merge_union_gitattributes.py`.
- Do not add or modify any `docs/parity_ledger/` entry — investigation confirmed none exists or is
  required for this pure tooling-infrastructure ticket.

## Dependency Map

- **Step 1** has no dependencies — first step; production code change plus the one existing-test
  helper adaptation it requires to keep the pre-existing 12 tests green.
- **Step 2** depends on Step 1 (new tests assert the post-cutover shard-targeting behavior Step 1
  implements).
- **Step 3** depends on Step 1 (same reason; independent of Step 2's specific tests, could run in
  parallel with Step 2 but is listed after for narrative grouping — both touch the same test file,
  so sequence to avoid overlapping edits).
- **Step 4** is independent of Steps 1-3 (pure `.gitattributes` text change).
- **Step 5** depends on Step 4 (asserts the line Step 4 adds).
- **Step 6** is independent of Steps 1-5 (pure doc prose change), but should follow Step 1 in
  practice so the doc accurately describes the already-landed code.
- **Step 7** depends on all of Steps 1-6 (full verification pass).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Test asserts hook (subprocess, mocked "now") appends to `agent-monitoring/tools/tools-<ISO-week>.jsonl`, never `agent-monitoring/tools.jsonl` | Step 1 (production change), Step 2 | `test_writes_to_iso_week_shard_file_not_legacy_tools_jsonl` |
| Test asserts two invocations in two different ISO weeks write to two distinct shard files, each with exactly its own record | Step 1, Step 2 | `test_two_different_iso_weeks_write_to_two_distinct_shard_files` |
| Existing single-writer and concurrent-writer tests still pass against the sharded path | Step 1 | `test_single_writer_produces_one_well_formed_line`, `test_phase_and_agent_included_when_sidecar_present`, `test_execution_identity_fields_included_when_sidecar_present`, `test_phase_and_agent_default_to_none_on_partial_sidecar`, `test_concurrent_writers_produce_no_interleaved_or_truncated_lines`, plus 8 sidecar-attribution tests |
| `test_locking_failure_does_not_propagate` still passes unmodified in behavior | Step 1 (no change to that test) | `test_locking_failure_does_not_propagate` |
| `.gitattributes` contains a `merge=union` entry covering the new shard glob | Step 4 | `test_gitattributes_line_present_for_shard_glob` (or extended existing test), Step 5 |
| `docs/agent-monitoring/schema.md`'s `## agent-monitoring/tools.jsonl` section describes per-ISO-week file naming and write path | Step 6 | Manual parity check (no automated doc-content test exists) |
| No functional change to `tools/agent-monitoring/writer.py` | Step 1 (explicitly zero changes) | Full regression run, Step 7 — `writer.py` diff is empty |

Additional ticket requirement not phrased as a checkbox AC but stated in Scope — fail-silent
contract preserved for the new ISO-week computation: implemented by Step 1 (placement inside the
existing outer `try/except`), verified by Step 3's
`test_iso_week_computation_failure_does_not_propagate`.

## Anti-Drift Notes

- **Fail-silent contract is the single highest-priority invariant in this ticket.** This hook
  fires synchronously on every tool call, in every concurrently running Claude Code session, in
  this and every other worktree. A regression that lets a clock/format edge case propagate out of
  the hook would block real tool calls repo-wide, not just fail a test. Step 1's placement of
  `now_dt`/`iso_week` computation must stay textually between `post_tool_hook.py`'s line 47 `try:`
  and line 157 `except Exception: pass` — Step 3's test is the concrete guard for this, not code
  review alone (matching the precedent `test_locking_failure_does_not_propagate` already set for
  this exact class of regression).
- **Keep the hook's own pre-emptive `tools_file.parent.mkdir(...)` call.** It is not redundant
  post-cutover — it is what prevents `write_line`'s internal `_acquire_lock` from hitting
  `FileNotFoundError` (rather than the expected `FileExistsError`) on the very first write to a
  brand-new `agent-monitoring/tools/` directory. See Step 1's full trace.
- **Do not let the existing 150-invocation concurrency test
  (`test_concurrent_writers_produce_no_interleaved_or_truncated_lines`) start freezing time.** It
  intentionally runs against real, un-frozen "now" — this is pre-existing behavior, unrelated to
  this ticket, and freezing it would be scope creep. It carries a pre-existing, vanishingly rare
  theoretical flake risk (a run straddling an ISO-week boundary at exactly midnight UTC on a Monday
  could in principle split its 150 lines across two shard files instead of one) — this risk existed
  in a different form before this ticket (all writes landed in one file regardless of the moment)
  and is not something this ticket should attempt to eliminate; do not add retry/skip logic for it.
- **Diagnostic sidecar split is expected, not a bug.** After this ticket,
  `post_tool_hook.py`'s own write failures diagnostic-log to a new, second
  `agent-monitoring/tools/.writer_health.jsonl`, separate from `record_run.py`/`record_events.py`'s
  existing `agent-monitoring/.writer_health.jsonl`. No doc or code currently depends on a single
  unified diagnostic file (confirmed by investigation). Do not "fix" this by special-casing the
  diagnostic path in `write_line` — that would be a `writer.py` change, explicitly forbidden by
  this ticket's own AC.
- **Reader gap after this ticket lands alone is accepted, not a bug to route around.** Per Out of
  Scope: `generate_retro.py`/`query.py`/`validate.py`/`build_index.py` will not see new rows until
  child ticket 3 lands. Do not add any shard-glob awareness to these readers "just to close the
  gap" — that is explicitly deferred, and doing it here would undermine child ticket 2's clean
  cutover point (per `SEQUENCE.md`'s stated ordering rationale).
- **`.gitattributes`'s legacy line must survive this ticket.** Child ticket 2 removes the old
  `agent-monitoring/tools.jsonl merge=union` line once the monolithic file is retired — this ticket
  must not touch it.

## Deviations (recorded during Implement)

Two of this plan's literal test-code specifications were found to be incorrect when actually run,
both surfaced by real `pytest` failures rather than assumed — fixed rather than routed around,
since both are mechanical consequences of Step 1's own path change, not changes to production
behavior or gate-gaming:

1. **`test_locking_failure_does_not_propagate`'s diagnostic-path assertion.** Plan's Acceptance
   Criteria Map claimed this test "still passes unmodified in behavior." It does not: `writer.py`'s
   `_diagnostic_path_for(target_path)` derives `.writer_health.jsonl` from `target_path.parent`
   (`writer.py:41-42`), which — after Step 1's cutover — is `agent-monitoring/tools/` (the shard
   directory), not `agent-monitoring/` directly. This is exactly the "diagnostic sidecar split"
   investigation.md's Risks section already flagged as an accepted, expected side effect of the
   cutover; what the investigation missed was that the *existing* test's hardcoded
   `tmp_path / "agent-monitoring" / ".writer_health.jsonl"` assertion path needed the identical
   mechanical update `_tools_lines()` already got in Step 1. Fixed by updating the assertion to
   `tmp_path / "agent-monitoring" / "tools" / ".writer_health.jsonl"`, with an inline comment
   explaining why. No change to the test's fault-injection logic (the `os.open` shim for `.lock`
   paths) or to what it verifies (a lock-acquire failure is caught and diagnostic-logged, never
   propagated) — only the path it reads back from.

2. **`test_iso_week_computation_failure_does_not_propagate`'s shim, as literally specified in
   plan.md Step 3, does not work.** Plan's code and rationale claimed the shim "does not need
   `sys.path.insert` for writer (unlike the locking-failure shim) because `write_line` is never
   reached — the failure happens before line 10's import is even used." This conflates *when
   `write_line` is called* with *when the `from writer import write_line` import statement
   executes*: the import at `post_tool_hook.py:10` runs unconditionally at module-load time,
   before the `try:` block (line 47) where the frozen/raising `datetime.now()` is ever invoked —
   and it sits outside the outer `try/except Exception: pass` entirely. Because the shim file
   lives under `tmp_path`, not the real `tools/agent-monitoring/` directory, the hook's own
   `sys.path.insert(0, Path(__file__).resolve().parent)` (line 9) resolves to `tmp_path`, so
   `from writer import write_line` raised `ModuleNotFoundError` — confirmed by direct
   `pytest -v` run: `returncode == 1`, `stderr` showing exactly that traceback. Fixed by adding the
   same `sys.path.insert(0, str(_MONITORING_TOOLS_DIR))` prefix `_run_hook_with_frozen_now` and
   `test_locking_failure_does_not_propagate` already use, so the import succeeds and the test
   actually exercises what it claims to (a clock-read failure during record-building is swallowed
   by the hook's outer `try/except`, never propagating). This is an additive fix to the shim's
   setup, not a change to the assertions it makes.

Both fixes were verified by rerunning the full `pytest tests/tools/test_post_tool_hook.py -v`
suite after each change — all 18 tests (14 pre-existing + 4 new) pass. Neither fix touches
`writer.py`, the 13-field record shape, or any file outside `tests/tools/test_post_tool_hook.py`.
