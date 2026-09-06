---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE
artifact_type: test_plan
tags: [ai, hooks, agent-monitoring]
---

# Test Plan — TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE

## Regression Surface

Existing tests that must keep passing (none of these should need behavior changes — they cover the *other* three PreToolUse/PostToolUse/SubagentStop hook groups and the two already-migrated sidecar consumers, none of which this ticket touches):

**unit / structural (`.claude/settings.json` itself):**
- `tests/tools/test_settings_json_hooks_wiring.py` — all 4 existing tests, in particular `test_existing_hook_writers_untouched` (`len(settings["hooks"]["PreToolUse"]) == 4`, `len(settings["hooks"]["PostToolUse"]) == 4`) — the edit changes only the `command` string content of the existing `Edit|Write` entry, never the array shape.

**unit (already-migrated sidecar consumers — must stay untouched, per Out of Scope):**
- `tests/tools/test_retrieval_cache.py` — especially the `TestReadCurrentRunSidecar` class (7+ cases per `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY`'s own Test Summary).
- `tests/tools/test_post_tool_hook.py` — all sidecar-scoping tests (`test_scoped_sidecar_preferred_over_stale_unscoped_sidecar`, `test_two_concurrent_sessions_each_attributed_correctly`, `test_foreign_scoped_sidecar_not_read_by_different_session`, `test_second_call_in_ad_hoc_session_reads_own_sentinel_not_unscoped_file`, `test_real_writesidecar_overwrites_earlier_ad_hoc_sentinel`, prune tests).

**integration / orchestrator-source (unaffected by this ticket — no `.claude/workflows/implement-ticket.js` changes are in scope, but they exercise the same sidecar convention and should be re-run as adjacent-system confirmation):**
- `tests/tools/test_current_run_sidecar_orchestrator.py` — all 20 tests (writeSidecar helper shape, scoped-copy writes, Scope-phase resume branch).
- `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py`.

**arena-combat:** none — this ticket has zero overlap with combat/simulation domains.

## New Tests Required

1. **`test_edit_write_hook_reads_scoped_sidecar_via_env_var`**
   - Category: unit / structural (static string assertion, mirroring `test_current_run_sidecar_orchestrator.py`'s literal-substring pattern, adapted to `json.loads()` navigation since `.claude/settings.json` is real JSON rather than free-form JS source text)
   - Verifies: `settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]` (the `Edit|Write` matcher entry) contains, verbatim, the new `RUN_ID=$(...)` segment proposed in investigation.md — specifically asserts these substrings are all present in the command string:
     - `"os.environ.get('CLAUDE_CODE_SESSION_ID','')"` (or the exact quoting the implementer lands on — pin to whatever literal string plan.md finalizes)
     - `".claude/current_run.'+sid"` (scoped-path construction)
     - `"os.path.exists("` (existence check gating the scoped-vs-unscoped choice)
     - `"else '.claude/current_run'"` (unscoped fallback preserved)
   - Also asserts the OLD unscoped-only substring is gone: `"json.load(open('.claude/current_run')).get('run_id')"` with no preceding scoped-path branch must NOT appear as the sole RUN_ID computation (i.e., assert the new multi-branch form replaced it, not that it was merely appended alongside).
   - Where it lives: `tests/tools/test_settings_json_hooks_wiring.py` (extend the existing file — same `_load_settings()` helper, same file this ticket's own precedent research identifies as the closer match than `test_current_run_sidecar_orchestrator.py`).

2. **`test_edit_write_hook_still_fail_open_and_advisory`**
   - Category: unit / structural
   - Verifies: the `RUN_ID=$(...)` subshell still ends in `2>/dev/null || true`, and the outer `FILE=$(...)` subshell's own `2>/dev/null || true` is unchanged — i.e., the fail-open wrapper survives the edit, and no `|| true` was accidentally dropped or moved. Also asserts the `echo` JSON payload text (`"sidecar-check: tickets/inprogress/..."`) is byte-identical to before (this ticket must not alter the reminder message itself).
   - Where it lives: `tests/tools/test_settings_json_hooks_wiring.py`.

3. **`test_edit_write_hook_json_still_valid_after_edit`**
   - Category: unit / structural (regression guard against a malformed edit)
   - Verifies: `.claude/settings.json` still parses as valid JSON at all (`json.loads(_SETTINGS_PATH.read_text())` does not raise) and the top-level shape (`permissions`, `hooks.PreToolUse`, `hooks.PostToolUse`, `hooks.SubagentStop`) is unchanged. This is largely already covered by `_load_settings()` succeeding in every other test in the file, but an explicit test makes the JSON-validity guarantee a named, intentional assertion rather than an implicit side effect of other tests happening to call `json.loads()` first.
   - Where it lives: `tests/tools/test_settings_json_hooks_wiring.py`.

4. **`test_run_id_resolution_prefers_scoped_over_unscoped_when_scoped_exists`** (AC2, part 1 — normal flow)
   - Category: integration (synthetic subprocess execution — see "Practical Test Approach for AC2" below)
   - Verifies: with a scoped sidecar file (`.claude/current_run.<session>`) present holding `run_id=TCK-REAL` and a *different*, foreign unscoped file (`.claude/current_run`) holding `run_id=TCK-STALE-FOREIGN`, extracting and directly executing the hook's inner `python3 -c` RUN_ID snippet — with `CLAUDE_CODE_SESSION_ID` set to the scoped file's own session suffix and `cwd` pointed at the synthetic tmp dir — prints `TCK-REAL`, not `TCK-STALE-FOREIGN`.
   - Where it lives: new file `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py` (or extend `test_settings_json_hooks_wiring.py` — implementer's call; a new file is slightly cleaner since it needs `subprocess`/`os.environ` machinery the existing structural-only file doesn't otherwise use).

5. **`test_run_id_resolution_falls_back_to_unscoped_when_scoped_absent`** (edge case)
   - Category: integration (synthetic subprocess execution)
   - Verifies: with NO scoped file for the calling session but a real unscoped file present (`run_id=TCK-UNSCOPED`), the extracted snippet with `CLAUDE_CODE_SESSION_ID` set to a session with no matching scoped file prints `TCK-UNSCOPED` — confirming the fallback path (not a null/empty result) exactly matches `read_current_run_sidecar()`'s own fallback behavior, deliberately NOT `post_tool_hook.py`'s null-sentinel behavior.
   - Where it lives: same new file as #4.

6. **`test_run_id_resolution_empty_when_both_absent`** (edge case, matches today's pre-fix behavior)
   - Category: integration
   - **Technique note:** this test must NOT use the extract-and-execute-bare-snippet technique
     used by tests #4/#5/#7/#8 above. With neither scoped nor unscoped file present, the bare
     extracted `python3 -c` snippet's own `open(path)` call raises an uncaught `FileNotFoundError`
     when executed directly via `subprocess.run(["python3", "-c", extracted_code], ...)` — there is
     no shell-level `2>/dev/null || true` around a bare extracted snippet to catch it; that wrapper
     only exists in the FULL command string one layer up (confirmed live by direct execution against
     this exact no-sidecar-files scenario: nonzero returncode, traceback on stderr). This test must
     instead use the same full-command `bash -c` technique as test #9
     (`test_malformed_or_missing_sidecar_json_degrades_to_empty_not_traceback`): build
     `full_command = settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]` (unextracted),
     create `tmp_path/tickets/inprogress/fake.md` first (satisfies the `ls tickets/inprogress/*.md`
     guard so the RUN_ID branch executes), run via
     `subprocess.run(["bash", "-c", full_command], input=json.dumps({"tool_input": {"file_path": "a/src/foo.py"}}), cwd=tmp_path, env=env, capture_output=True, text=True)`
     with `CLAUDE_CODE_SESSION_ID` present but no scoped or unscoped sidecar file anywhere under
     `tmp_path`.
   - Verifies: `result.returncode == 0` (the full bash construct's `2>/dev/null || true` wrapper
     around the `RUN_ID=$(...)` subshell genuinely swallows the inner `python3 -c` call's
     `FileNotFoundError`/traceback — no exception, no traceback on stderr, no nonzero exit) and the
     documented reminder text (`"sidecar-check: tickets/inprogress/ has an active ticket but
     .claude/current_run has no run_id."`) appears in `result.stdout` — this is the hook's normal
     behavior when RUN_ID resolves empty (the `if [ -z "$RUN_ID" ]` branch fires). Same
     graceful-degradation contract as today's unscoped-only version when `.claude/current_run`
     doesn't exist, now proven via the full command rather than the (inapplicable) bare snippet.
   - Where it lives: same new file as #4.

7. **`test_run_id_resolution_empty_when_session_id_env_var_unset`** (edge case)
   - Category: integration
   - Verifies: with `CLAUDE_CODE_SESSION_ID` absent from the subprocess environment entirely (not just empty-string) and only an unscoped file present, the snippet still falls back to the unscoped file correctly (mirrors `retrieval_cache.py`'s `os.environ.get(..., "")` default-empty-string handling, which the ticket explicitly calls out as "the same forced approach").
   - Where it lives: same new file as #4.

8. **`test_two_concurrent_sessions_resolve_to_their_own_run_id`** (AC2, part 2 — the ticket's named "synthetic two-session scenario")
   - Category: integration (architecture guard for the cross-session isolation property)
   - Verifies: given two distinct scoped files (`current_run.sess-a` → `TCK-A`, `current_run.sess-b` → `TCK-B`) plus a stale/foreign unscoped file (`current_run` → `TCK-STALE-FOREIGN`), running the extracted snippet once with `CLAUDE_CODE_SESSION_ID=sess-a` prints `TCK-A`, and once with `CLAUDE_CODE_SESSION_ID=sess-b` prints `TCK-B` — neither ever prints `TCK-STALE-FOREIGN`. This is the direct executable proof for AC2's literal wording ("resolves RUN_ID to the calling session's own value, not the foreign one").
   - Where it lives: same new file as #4.

9. **`test_malformed_or_missing_sidecar_json_degrades_to_empty_not_traceback`** (failure mode)
   - Category: integration
   - Verifies: if the scoped file exists but contains invalid JSON (or is missing the `run_id` key), the snippet's own `2>/dev/null || true` wrapper (exercised at the full-command level, not just the extracted snippet) still yields an empty `RUN_ID` and the overall hook command exits 0 with no stderr noise reaching the harness. This directly exercises the fail-open contract this ticket must preserve.
   - Where it lives: same new file as #4 (this one may need to invoke the FULL bash command via `subprocess.run(["bash", "-c", full_command], ...)` rather than the extracted snippet alone, to prove the outer wrapper's fail-open behavior end-to-end).

## Practical Test Approach for AC2

No existing test in this repo drives an embedded bash one-liner from `.claude/settings.json` end-to-end through a shell (the closest precedent, `tests/tools/test_post_tool_hook.py`, subprocess-executes a standalone `.py` *script*, not a JSON-embedded shell snippet). Two complementary techniques, both needed because the full hook's only externally-observable signal is a binary "did the reminder JSON print, or not" — it never echoes the resolved `RUN_ID` value itself, so a test cannot distinguish "resolved to the right ticket" from "resolved to some other non-empty value" by observing the full hook's stdout alone:

1. **Extract-and-execute the inner snippet directly** (tests 4, 5, 7, 8 above): regex- or `json.loads()`-navigate to the `command` string, extract the substring between `RUN_ID=$(python3 -c "` and the matching closing `"` before ` 2>/dev/null`, then run `subprocess.run(["python3", "-c", extracted_code], cwd=tmp_path, env={**os.environ, "CLAUDE_CODE_SESSION_ID": ...}, capture_output=True, text=True)` and assert on `result.stdout.strip()`. This gives a real value to assert equality against (`"TCK-A"`, `"TCK-REAL"`, `""`, etc.) — the only way to positively prove AC2's "the calling session's own value, not the foreign one," since the snippet itself already `print()`s the resolved run_id as its sole stdout output. This technique only works when the sidecar file(s) the snippet's `open(path)` call needs actually exist somewhere on the resolution path (scoped or unscoped) — with no sidecar file present at all, the bare snippet's `open()` raises an uncaught `FileNotFoundError` with no shell wrapper to catch it, so it is NOT used for test 6 (see below).
2. **Execute the full command via `bash -c`** for the fail-open/failure-mode cases (tests 6 and 9): `subprocess.run(["bash", "-c", full_command], input=json.dumps({"tool_input": {"file_path": "tickets/foo.md"}}), cwd=tmp_path, ...)` with a `tickets/inprogress/*.md` file present in `tmp_path`, asserting `returncode == 0` and no unexpected reminder text when a real `run_id` should have resolved (test 9), or the documented empty-RUN_ID reminder text when no sidecar file exists at all (test 6). This is the only way to prove the *outer* `case`/`ls`/`if` wiring still gates correctly and the fail-open wrapper genuinely catches the inner `python3 -c` call's exception, since the extracted-snippet technique above only covers the inner `python3 -c` body in isolation, with no wrapper around it.

Both techniques avoid needing a live Claude Code hook invocation — they operate on the real `.claude/settings.json` file content (loaded once per test via the same `_load_settings()` pattern already established in `test_settings_json_hooks_wiring.py`) plus real subprocess execution, which is the closest hermetic equivalent to "driving the actual configured hook."

## Scoped Pytest Commands

```
pytest tests/tools/test_settings_json_hooks_wiring.py tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py -v
```

Broader regression surface (adjacent sidecar-consumer confirmation, per this ticket's own Out-of-Scope constraint that these must stay untouched):

```
pytest tests/tools/test_retrieval_cache.py tests/tools/test_post_tool_hook.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_epic_create_tickets_sidecar_orchestrator.py -q
```

Never: `pytest tests/` (unscoped, forbidden by CLAUDE.md's Testing Rule).

## Anti-Drift Test Guards

- **`test_existing_hook_writers_untouched`** (already exists in `test_settings_json_hooks_wiring.py`) — re-run as-is; if this ticket's edit ever grows into adding a new hooks-array entry instead of an in-place `command` string edit, this test catches the array-length drift immediately.
- **New guard: assert the `FILE=$(...)` extraction substring and the `case` matcher pattern list are byte-identical before/after** — prevents the implementer from "cleaning up" or refactoring the surrounding bash while fixing the RUN_ID segment (explicitly out of scope per investigation.md's Anti-Drift Hazards).
- **New guard: assert the `echo` JSON reminder text is byte-identical before/after** — prevents an accidental rewording of the advisory message while touching an adjacent line in the same command string.
- **Re-run `tests/tools/test_retrieval_cache.py::TestReadCurrentRunSidecar` and `tests/tools/test_post_tool_hook.py`'s scoped-sidecar tests unmodified** — proves this ticket did not accidentally touch `tools/retrieval_cache.py` or `tools/agent-monitoring/post_tool_hook.py` (both explicitly Out of Scope; `retrieval_cache.py` doubly so, per its own prior ticket's completion).
- **New guard: assert the hook's fix does NOT introduce a file-write side effect** — run the extracted snippet (or full command) against a `tmp_path` with no scoped file present, then assert no new file was created under `tmp_path/.claude/` as a result (distinguishing this hook's chosen behavior from `post_tool_hook.py`'s null-sentinel-write pattern, which this ticket must NOT adopt).
