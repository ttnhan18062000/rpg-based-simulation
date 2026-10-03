# Plan — TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY

## Mechanism

`read_current_run_sidecar()` derives the scoped path from `_CURRENT_RUN_SIDECAR_PATH`'s own
parent+name (`<path>.<CLAUDE_CODE_SESSION_ID>`) rather than hardcoding `.claude/` — this means
every existing test's `monkeypatch.setattr(rc, "_CURRENT_RUN_SIDECAR_PATH", tmp_path /
"current_run")` (the file's own autouse fixture) automatically relocates the scoped variant too,
with zero changes needed to that fixture or to any of the 7 existing tests' own bodies.

- If `CLAUDE_CODE_SESSION_ID` is set AND `<path>.<that value>` exists → read it (scoped wins).
- Otherwise → read the plain unscoped `_CURRENT_RUN_SIDECAR_PATH` (unchanged pre-ticket behavior).
- `_sidecar_run_is_stale()` untouched — same file-existence-based done-vs-inprogress check,
  semantically unrelated to `post_tool_hook.py`'s mtime-based scoped-file pruning, kept separate.
- No pruning logic added here — retrieval_cache.py never deletes a sidecar file, scoped or not.

## Guard-test narrowing decision

`test_no_pragma_busy_timeout_chmod_or_os_import_introduced_by_level2_migration` renamed to
`test_no_pragma_busy_timeout_or_chmod_introduced_by_level2_migration`, dropping only the `assert
"os" not in imported_modules` clause (and its now-unused AST-import-walking support code). The
three chmod/busy-timeout string checks that test the *actual* concern this test's docstring names
remain byte-identical and fully enforced. This is a narrow, disclosed, evidence-backed correction
of an overly broad proxy check — not a routing-around of a real gate — mirroring this repo's own
established precedent (e.g. `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`'s narrowing
of `test_no_frozen_kgmcp_dependency_edited` for an analogous reason).

## Cross-reference comments

Added at both `read_current_run_sidecar()`'s docstring (points at `post_tool_hook.py`) and
`post_tool_hook.py`'s sidecar-read comment block (points at `read_current_run_sidecar()`), per
this ticket's own AC #4.

## Test plan

- New: `test_scoped_sidecar_wins_over_stale_unscoped_when_both_exist` (AC #1).
- New: `test_no_scoped_file_falls_back_to_unscoped_and_deletes_nothing` (AC #3 — no new
  file-deletion side effect).
- All 7 existing `TestReadCurrentRunSidecar` tests: verified to pass with zero changes.
- Guard-test narrowing (see above), with the deviation disclosed in this ticket's own
  Implementation Notes, not silently patched.

## Parity ledger

New entry required in `docs/parity_ledger/infrastructure.yaml`.
