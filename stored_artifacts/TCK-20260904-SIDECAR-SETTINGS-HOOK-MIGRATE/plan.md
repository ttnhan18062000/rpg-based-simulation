---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE
artifact_type: plan
tags: [ai, hooks, agent-monitoring]
---

# Implementation Plan — TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE

## Summary

Replace the single unscoped `RUN_ID=$(...)` subshell inside `.claude/settings.json`'s `Edit|Write`
PreToolUse hook (`hooks.PreToolUse[3].hooks[0].command`) with the scoped-then-unscoped-fallback
read order already shipped in `tools/retrieval_cache.py::read_current_run_sidecar()`
(`tools/retrieval_cache.py:555-622`, confirmed by investigation.md and re-confirmed live below).
Nothing else in the command string changes. Two test additions cover the change: three new
structural (`json.loads()` + exact-substring) tests appended to the existing
`tests/tools/test_settings_json_hooks_wiring.py`, and six new subprocess-execution integration
tests in a new sibling file, `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py`,
which extract the inner `python3 -c` snippet via regex and run it directly against synthetic
`tmp_path` sidecar files to prove session-scoped resolution. One new parity ledger entry
(`INFRA-410`) documents the change; `INFRA-382`'s own historical text is left untouched.

## Steps

### Step 1 — Update the RUN_ID segment in `.claude/settings.json`

**Files:** `.claude/settings.json`

**Change:** In `hooks.PreToolUse[3].hooks[0].command` (the `"matcher": "Edit|Write"` entry),
replace only the substring:

```
RUN_ID=$(python3 -c \"import json; print(json.load(open('.claude/current_run')).get('run_id') or '')\" 2>/dev/null || true)
```

with:

```
RUN_ID=$(python3 -c \"import json,os; sid=os.environ.get('CLAUDE_CODE_SESSION_ID',''); path='.claude/current_run.'+sid if sid and os.path.exists('.claude/current_run.'+sid) else '.claude/current_run'; print(json.load(open(path)).get('run_id') or '')\" 2>/dev/null || true)
```

This is the exact replacement investigation.md already worked out and verified re-mirrors
`read_current_run_sidecar()`'s preference order (`tools/retrieval_cache.py:555-622`, read and
confirmed during Investigate: scoped file wins only if `session_id` is non-empty **and** the
scoped file exists; otherwise falls back to the unscoped file — no null-sentinel write, unlike
`tools/agent-monitoring/post_tool_hook.py:96-131`'s different, payload-sourced preference order).

Confirmed live immediately before writing this plan (`python3 -c` read of the real file, current
worktree state): `hooks.PreToolUse[3]` is exactly the `Edit|Write` entry investigation.md quoted,
byte-for-byte, with `len(hooks["PreToolUse"]) == 4` and `len(hooks["PostToolUse"]) == 4` (the
`SubagentStop` entry from `TCK-20260904-TEST-SCOPER-HANG-GUARD` is already merged in and must stay
untouched). No other pending edit to this file is currently live: `TCK-20260904-BASH-SECRET-SCAN-HOOK`
(the sibling ticket flagged in investigation.md as a shared-file risk) is `tickets/inprogress/`
but its own frontmatter reads `phase: blocked` and body `## Status: BLOCKED` — it has not yet
touched `hooks.PreToolUse` (confirmed: no Bash-matcher entry or secret-scan reference exists in the
live file today), so there is no live conflict to merge around at this step. Re-run
`git status`/`git diff -- .claude/settings.json` immediately before editing anyway, per the
repo's shared-worktree hard rule, in case that ticket's block was lifted between plan-writing and
implementation.

**Other writers to this file (enumerated, since `.claude/settings.json` is a shared resource):**
- `TCK-20260904-TEST-SCOPER-HANG-GUARD` — already landed (`tickets/done/`), added the
  `SubagentStop` entry and is not touched by this edit (`test_existing_hook_writers_untouched`
  guards its `len(...) == 4` counts on both arrays; this step preserves both counts).
- `TCK-20260904-BASH-SECRET-SCAN-HOOK` — BLOCKED, not currently live in the file (see above); if
  it unblocks and lands first, this step's edit is additive/non-overlapping (different
  `PreToolUse` array entry, matcher `Bash` vs. `Edit|Write`) and should merge cleanly — no
  sequencing dependency either direction.
- No other ticket or automated process writes to `.claude/settings.json`.

**Do NOT touch:** the `FILE=$(...)` extraction, the `case "$FILE" in ... esac` matcher list, the
`ls tickets/inprogress/*.md` guard, the `if [ -z "$RUN_ID" ]` check, the `echo` JSON reminder text,
or either subshell's trailing `2>/dev/null || true`. Do not add a new `hooks.PreToolUse` array
entry — this must be an in-place edit to the existing entry's `command` string only. Do not touch
`tools/retrieval_cache.py` (already migrated, confirmed out of scope) or
`tools/agent-monitoring/post_tool_hook.py` (different, payload-sourced preference order — not the
pattern being mirrored here).

**Verify:** `tests/tools/test_settings_json_hooks_wiring.py::test_existing_hook_writers_untouched`
(pre-existing, must keep passing) plus the new tests added in Step 2.

---

### Step 2 — Extend `tests/tools/test_settings_json_hooks_wiring.py` with structural guards

**Files:** `tests/tools/test_settings_json_hooks_wiring.py`

**Change:** Append three new test functions, reusing the file's existing `_load_settings()` helper
(`tests/tools/test_settings_json_hooks_wiring.py:20-21`, confirmed present) and the same
`_SETTINGS_PATH`/`_REPO_ROOT` module constants — no new imports needed beyond what the file already
has (`json`, `pathlib.Path`).

1. `test_edit_write_hook_reads_scoped_sidecar_via_env_var` (AC #1, AC #4) — load settings, navigate
   to `settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]`, assert all of these substrings
   are present verbatim:
   - `"os.environ.get('CLAUDE_CODE_SESSION_ID','')"`
   - `".claude/current_run.'+sid"`
   - `"os.path.exists("`
   - `"else '.claude/current_run'"`
   and assert the OLD single-branch form is gone — specifically assert
   `"json.load(open('.claude/current_run')).get('run_id')"` does NOT appear as a standalone
   substring unless immediately preceded by the new `else path=` branch (simplest robust check:
   assert the literal old full substring
   `"RUN_ID=$(python3 -c \"import json; print(json.load(open('.claude/current_run')).get('run_id') or '')\""`
   is absent — this exact string can only match the old single-branch form, not the new one, since
   the new form's `-c` body starts with `"import json,os; sid=..."`).

2. `test_edit_write_hook_still_fail_open_and_advisory` (regression guard from test_plan.md #2) —
   assert the command string still contains `RUN_ID=$(...)... 2>/dev/null || true)` (both subshells
   keep their trailing fail-open wrapper — check both the `FILE=$(...)` and `RUN_ID=$(...)`
   segments independently via two separate substring assertions) and assert the `echo` JSON
   reminder text is byte-identical to its current form: assert the literal substring
   `"sidecar-check: tickets/inprogress/ has an active ticket but .claude/current_run has no run_id."`
   is still present unchanged (this English sentence intentionally still refers to
   `.claude/current_run` — it is describing the *symptom* to the reader, not the resolved path,
   and Step 1 does not change this string).

3. `test_edit_write_hook_json_still_valid_after_edit` (regression guard from test_plan.md #3) —
   assert `_load_settings()` succeeds (already implicit via the two tests above, but assert
   explicitly with a bare call) and assert top-level keys unchanged: `"permissions" in settings`,
   `"allow" in settings["permissions"]`, `{"PreToolUse","PostToolUse","SubagentStop"} <= set(settings["hooks"])`.

**Do NOT touch:** the four existing test functions in this file (`test_new_hook_event_key_not_previously_wired`,
`test_subagent_stop_command_not_suffixed_with_swallowing_fallback`,
`test_subagent_stop_hook_references_script_that_exists`, `test_existing_hook_writers_untouched`) —
append only, do not reorder or edit their bodies.

**Verify:** `pytest tests/tools/test_settings_json_hooks_wiring.py -v` — all 7 tests (4 existing + 3
new) pass.

---

### Step 3 — Add synthetic two-session integration tests in a new file

**Files:** `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py` (new)

**Change:** New test module, imports `json`, `os`, `re`, `subprocess`, `pathlib.Path`, plus pytest's
`tmp_path` fixture (no explicit import needed). Module-level helpers:

```python
_REPO_ROOT = Path(__file__).parent.parent.parent
_SETTINGS_PATH = _REPO_ROOT / ".claude" / "settings.json"

def _load_settings() -> dict:
    return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))

def _extract_run_id_snippet() -> str:
    settings = _load_settings()
    command = settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]
    # After json.loads(), `command` already contains real `"` characters (JSON's own \" escaping
    # is resolved by the parser) -- the snippet's own body uses only single-quoted Python string
    # literals (per investigation.md), so it contains no embedded `"`, making this regex
    # unambiguous: it matches the shortest run from `-c "` to the next `"` that precedes
    # ` 2>/dev/null`.
    match = re.search(
        r'RUN_ID=\$\(python3 -c "(.*?)" 2>/dev/null \|\| true\)', command
    )
    assert match is not None, "RUN_ID snippet not found in settings.json command string"
    return match.group(1)

def _write_sidecar(base: Path, name: str, run_id: str) -> None:
    claude_dir = base / ".claude"
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / name).write_text(json.dumps({"run_id": run_id}), encoding="utf-8")

def _run_snippet(cwd: Path, env: dict) -> str:
    result = subprocess.run(
        ["python3", "-c", _extract_run_id_snippet()],
        cwd=cwd, env=env, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()
```

Isolation note: the extracted snippet only ever opens **relative** paths
(`.claude/current_run.<sid>` / `.claude/current_run>`), so pointing `cwd=tmp_path` at a pytest
`tmp_path` fixture fully isolates every test from this session's own real `.claude/current_run` —
no real sidecar file is ever read or written by these tests. Build `env` per test as
`{**os.environ, "CLAUDE_CODE_SESSION_ID": "<value>"}` (present) or
`{k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}` (fully absent, for the
unset-var edge case — distinct from present-but-empty).

Six test functions (names taken verbatim from test_plan.md, which already fully specified their
assertions — implement exactly as described there, **except test #3 below**, which test_plan.md's
own item #6 described using the same bare-snippet technique as tests #1/#2/#4/#5; that description
is factually wrong and is corrected here — see the note under test #3):

1. `test_run_id_resolution_prefers_scoped_over_unscoped_when_scoped_exists` (AC #2, part 1) —
   `_write_sidecar(tmp_path, "current_run.sess-1", "TCK-REAL")`,
   `_write_sidecar(tmp_path, "current_run", "TCK-STALE-FOREIGN")`, run with
   `CLAUDE_CODE_SESSION_ID=sess-1`, assert result `== "TCK-REAL"`.
2. `test_run_id_resolution_falls_back_to_unscoped_when_scoped_absent` — only unscoped file present
   (`run_id=TCK-UNSCOPED`), run with `CLAUDE_CODE_SESSION_ID=sess-nomatch` (no scoped file for that
   session), assert result `== "TCK-UNSCOPED"`.
3. `test_run_id_resolution_empty_when_both_absent` — **does NOT use `_run_snippet()` /
   `_extract_run_id_snippet()`.** With no sidecar files present at all, the bare extracted
   `python3 -c` snippet's own `open(path)` call raises an uncaught `FileNotFoundError` when run
   directly via `subprocess.run(["python3", "-c", snippet], ...)` — there is no shell-level
   `2>/dev/null || true` around the bare snippet to catch it (that wrapper only exists in the FULL
   command string, one layer up). Confirmed live by directly executing the bare-snippet form
   against a no-sidecar-files scenario: nonzero returncode, traceback on stderr. So this test must
   use the same full-command `bash -c` technique as test #6
   (`test_malformed_or_missing_sidecar_json_degrades_to_empty_not_traceback`), not the
   extract-and-run-bare-snippet technique used by tests #1/#2/#4/#5:
   - `settings = _load_settings()`; `full_command = settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]`
     (the unextracted whole command — do not regex-extract the inner snippet for this test).
   - Create `tmp_path/tickets/inprogress/fake.md` first (satisfies the `ls tickets/inprogress/*.md`
     guard so the RUN_ID branch actually executes rather than short-circuiting on an empty glob).
   - No `.claude/current_run*` file of any kind exists under `tmp_path`.
   - `env = {**os.environ, "CLAUDE_CODE_SESSION_ID": "sess-none"}` (present but no matching scoped
     or unscoped file anywhere).
   - `result = subprocess.run(["bash", "-c", full_command], input=json.dumps({"tool_input": {"file_path": "a/src/foo.py"}}), cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10)`.
   - Assert `result.returncode == 0` — this time the assertion is actually true: the full bash
     construct's `2>/dev/null || true` wrapper around the `RUN_ID=$(...)` subshell genuinely
     swallows the inner `python3 -c` call's `FileNotFoundError`/traceback, leaving `RUN_ID` empty
     and the command still exits 0.
   - Assert the expected reminder text appears in stdout: the literal substring
     `"sidecar-check: tickets/inprogress/ has an active ticket but .claude/current_run has no run_id."`
     is present in `result.stdout` (this is the hook's normal behavior when RUN_ID resolves empty —
     the `if [ -z "$RUN_ID" ]` branch fires and echoes this reminder). Do not additionally assert
     anything about the bare snippet's own stdout/return value for this test — the core point
     ("no traceback, no nonzero exit, degrades to the documented reminder") is fully covered by the
     `returncode`/stdout checks above; keep the fix minimal.
4. `test_run_id_resolution_empty_when_session_id_env_var_unset` — only unscoped file present,
   `CLAUDE_CODE_SESSION_ID` fully absent from env (not empty string), assert result
   `== "TCK-UNSCOPED"` (or whatever unscoped value was written) — proves the `os.environ.get(...,
   '')` default-empty-string path still falls through correctly.
5. `test_two_concurrent_sessions_resolve_to_their_own_run_id` (AC #2, part 2 — the ticket's named
   scenario) — write `current_run.sess-a` → `TCK-A`, `current_run.sess-b` → `TCK-B`, and
   `current_run` → `TCK-STALE-FOREIGN`, all in the same `tmp_path`; run once with
   `CLAUDE_CODE_SESSION_ID=sess-a` (assert `== "TCK-A"`) and once with
   `CLAUDE_CODE_SESSION_ID=sess-b` (assert `== "TCK-B"`); assert neither run's output is
   `"TCK-STALE-FOREIGN"`.
6. `test_malformed_or_missing_sidecar_json_degrades_to_empty_not_traceback` (failure mode) — this
   one exercises the **full** command (not just the extracted snippet) via
   `subprocess.run(["bash", "-c", full_command], input=json.dumps({"tool_input": {"file_path": "a/src/foo.py"}}), cwd=tmp_path, env=env, capture_output=True, text=True)`,
   where `full_command = settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]` (unextracted),
   `tmp_path/tickets/inprogress/fake.md` is created first (satisfies the `ls
   tickets/inprogress/*.md` guard), and the scoped sidecar file for the given session contains
   invalid JSON (e.g. `"{not valid json"`) or is entirely absent alongside no unscoped file either.
   Assert `result.returncode == 0` and that no Python traceback appears on `result.stderr`
   (`2>/dev/null` inside the subshell already suppresses it into the subshell's own stderr, but the
   outer `bash -c` invocation's stderr should still be clean since nothing outside the suppressed
   subshells writes to stderr).

**Do NOT touch:** any real file under this session's own `.claude/` directory — every sidecar file
these tests create must live under `tmp_path`, never `_REPO_ROOT / ".claude"`.

**Verify:** `pytest tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py -v` — all 6 new
tests pass. This is also the direct proof for AC #2's literal wording.

---

### Step 4 — Add new parity ledger entry `INFRA-410`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Current max entry id in this file, confirmed live via
`grep -oE 'INFRA-[0-9]+' docs/parity_ledger/infrastructure.yaml | sort -t- -k2 -n | uniq | tail -1`
immediately before writing this plan: **`INFRA-409`**. This supersedes investigation.md's own
"as of the last-landed sibling ticket" snapshot — use **`INFRA-410`** as the next id. Re-check this
same command again at Implement time in case another ticket lands an entry in between (same
renumbering risk `INFRA-382`'s own text already documents happening to it once).

Append a new entry (following the exact YAML shape read from `INFRA-382`,
`docs/parity_ledger/infrastructure.yaml:11359-11380`, and validated against the required-field
`allOf` rules in `docs/parity_ledger/schema.json` — status `verified` requires both `v2_evidence`
and `test_path` as non-null strings; `priority: P2` carries no additional required-field rule):

```yaml
- id: INFRA-410
  text: 'Migrate .claude/settings.json''s Edit|Write PreToolUse hook''s inline RUN_ID=$(...)
    python3 -c snippet from an unscoped-only read of .claude/current_run to the same
    scoped-then-unscoped-fallback preference order as tools/retrieval_cache.py::read_current_run_sidecar()
    (INFRA-390): reads CLAUDE_CODE_SESSION_ID via os.environ.get (no hook-payload session_id
    field is available in this bash-embedded context, unlike post_tool_hook.py), prefers
    .claude/current_run.<session_id> when that file exists, falling back to the unscoped
    .claude/current_run otherwise. This is the second and final straggler INFRA-382''s own
    text named as "deferred not migrated" alongside tools/retrieval_cache.py (already migrated
    by INFRA-390) -- INFRA-382''s own historical record is left unedited; this is a new entry
    documenting the follow-up, not a retroactive rewrite. Deliberately does NOT adopt
    post_tool_hook.py''s null-sentinel-on-absence write behavior (INFRA-389) -- this is a
    read-only advisory hook with no justified write side effect. No other segment of the
    command (FILE=$(...) extraction, case matcher list, ls tickets/inprogress/*.md guard,
    echo JSON reminder text, or either subshell''s trailing 2>/dev/null || true fail-open
    wrapper) changed.'
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: '.claude/settings.json (hooks.PreToolUse[3].hooks[0].command, Edit|Write matcher entry)'
  test_path: 'tests/tools/test_settings_json_hooks_wiring.py::test_edit_write_hook_reads_scoped_sidecar_via_env_var, tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py::test_two_concurrent_sessions_resolve_to_their_own_run_id'
  divergence_note: null
  proof_type: regression
```

Use `tools/parity_ledger_writer.py` (or equivalent sanctioned schema-validating tool) to append
this entry rather than a raw `Edit`/ad-hoc script rewrite of the whole file — per this project's
own documented hazard around full-file YAML rewrites corrupting the ledger.

**Do NOT touch:** `INFRA-382`'s existing entry (its "deferred not migrated" text stays as
historical record of what it fixed at the time — do not edit it to describe this ticket's work),
`INFRA-389`, or `INFRA-390`.

**Verify:** the ledger still validates against `docs/parity_ledger/schema.json` (whatever
validator/test this repo already runs over the parity ledger — confirm it passes after the
append), and the new entry's two `test_path` tests (from Steps 2 and 3) actually pass.

## Scope Guards

- Do not adopt `post_tool_hook.py`'s null-sentinel-on-absence behavior (`tools/agent-monitoring/post_tool_hook.py:96-131`)
  for the settings.json hook — no file-write side effect may be added to this read-only advisory
  PreToolUse hook.
- Do not touch the `FILE=$(...)` extraction, the `case "$FILE" in ... esac` matcher list, the
  `ls tickets/inprogress/*.md` guard, or the `echo` JSON reminder text in the hook's command
  string — only the `RUN_ID=$(...)` subshell's inner `python3 -c` body changes.
- Keep the trailing `2>/dev/null || true` on both the `FILE=$(...)` and `RUN_ID=$(...)` subshells
  exactly as-is — the hook must remain fail-open.
- Do not re-touch `tools/retrieval_cache.py` — already migrated by
  `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY`, confirmed correct, out of scope.
- Do not touch `tools/agent-monitoring/post_tool_hook.py` — different, payload-sourced preference
  order; not the pattern being mirrored.
- Do not add a new `hooks.PreToolUse` array entry — `len(settings["hooks"]["PreToolUse"])` must
  stay `4` (guarded by the pre-existing `test_existing_hook_writers_untouched`).
- Do not edit `INFRA-382`'s existing parity ledger entry text.
- Do not attempt to resolve or unblock `TCK-20260904-BASH-SECRET-SCAN-HOOK` — it is a separate,
  currently-BLOCKED ticket; this plan only needs to avoid colliding with it at merge time.
- Do not run `pytest tests/` unscoped — use the scoped commands from test_plan.md.

## Dependency Map

Steps 1, 2, 3, and 4 are independent of each other in principle (each touches a different file),
but in practice:
- Step 2's new tests assert against the command string Step 1 produces — implement Step 1 first,
  or the new assertions in Step 2 will fail against the old string.
- Step 3's tests extract and execute the snippet Step 1 produces — same ordering requirement.
- Step 4 references the test paths added in Steps 2 and 3 in its own `test_path` field — write
  Step 4 last, after both test files exist and pass, so the referenced test names are real and
  green.

Recommended order: Step 1 → Step 2 → Step 3 → Step 4.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: hook reads `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` via `os.environ.get` when it exists, falling back to unscoped otherwise | Step 1 | `test_settings_json_hooks_wiring.py::test_edit_write_hook_reads_scoped_sidecar_via_env_var` (Step 2); `test_settings_json_edit_write_hook_sidecar_scope.py::test_run_id_resolution_prefers_scoped_over_unscoped_when_scoped_exists` and `::test_run_id_resolution_falls_back_to_unscoped_when_scoped_absent` (Step 3) |
| AC2: synthetic two-session scenario resolves RUN_ID to the calling session's own value, not the foreign one | Step 1 (behavior), Step 3 (test) | `test_settings_json_edit_write_hook_sidecar_scope.py::test_two_concurrent_sessions_resolve_to_their_own_run_id` |
| AC3: `tools/retrieval_cache.py` left untouched | N/A (explicitly no step touches this file) | `tests/tools/test_retrieval_cache.py::TestReadCurrentRunSidecar` (pre-existing, re-run unmodified as regression confirmation) |
| AC4: new regression-guard test asserts the exact updated command string | Step 2 | `test_settings_json_hooks_wiring.py::test_edit_write_hook_reads_scoped_sidecar_via_env_var` |

## Anti-Drift Notes

- This hook fires in a bare shell/`python3 -c` context with no hook-payload `session_id` field
  (unlike `post_tool_hook.py`, which reads `session_id` from its JSON stdin payload) — it must read
  `CLAUDE_CODE_SESSION_ID` from the process environment directly, exactly as
  `tools/retrieval_cache.py::read_current_run_sidecar()` already does. Do not attempt to parse a
  `session_id` out of the hook's stdin JSON — that payload only carries `tool_input`/`file_path`.
- This hook is purely advisory — a stale/wrong RUN_ID degrades to a missing or wrong reminder, not
  data corruption. This bounds the blast radius of any residual edge case and is why the fail-open
  wrapper must be preserved exactly.
- The two prior-art preference orders in this codebase are NOT identical:
  `read_current_run_sidecar()` (`tools/retrieval_cache.py:555-622`) falls back to the unscoped file
  when no scoped file exists; `post_tool_hook.py` (`tools/agent-monitoring/post_tool_hook.py:96-131`)
  instead writes a null-valued sentinel to the scoped path and never falls back to the unscoped
  file. This ticket's Scope text matches the first pattern exactly — do not conflate the two or
  "helpfully" adopt the second one's sentinel-write behavior.
- `INFRA-382`'s own text is the historical record of what that ticket fixed at the time (introducing
  the scoped-sidecar convention while explicitly deferring both `retrieval_cache.py` and this
  settings.json hook) — it must stay factually accurate to that moment, not be retroactively edited
  to describe this later ticket's work. A new ledger entry (`INFRA-410`) is the correct mechanism.
- Confirmed no other file needs to change for this ticket's scope beyond: `.claude/settings.json`
  (Step 1), `tests/tools/test_settings_json_hooks_wiring.py` (Step 2, extended),
  `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py` (Step 3, new),
  `docs/parity_ledger/infrastructure.yaml` (Step 4, new entry appended), and the ticket file itself
  (`tickets/inprogress/TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE.md`, updated at ticket-closure
  time per the standard workflow — not a distinct implementation step). `docs/mechanics/`,
  `docs/engine/`, and `docs/guides/agent_monitoring.md` are confirmed not requiring changes
  (investigation.md's reasoning holds: this is harness tooling, not simulation-domain logic, and
  the sidecar hook's documented *purpose* — not its internal read-path selection — is what that
  guide describes).

## Unresolved Questions

None. Every design decision investigation.md flagged as a "test-design decision" (not a blocking
open question) is now fully specified above: the test file split (extend
`test_settings_json_hooks_wiring.py` for structural checks, new
`test_settings_json_edit_write_hook_sidecar_scope.py` for subprocess-execution integration checks),
the exact regex-based extraction mechanics for the inner `python3 -c` snippet, the `tmp_path`-based
isolation approach for synthetic sidecar files, and the new parity ledger entry's id (`INFRA-410`,
confirmed as the true current max + 1 at plan-writing time) and full field content.
