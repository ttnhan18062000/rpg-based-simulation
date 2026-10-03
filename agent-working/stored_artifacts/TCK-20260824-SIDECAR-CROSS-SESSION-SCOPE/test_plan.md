# Test Plan — TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE

## New tests

`tests/tools/test_post_tool_hook.py`:
- `test_scoped_sidecar_preferred_over_stale_unscoped_sidecar` — write a stale/foreign unscoped
  `.claude/current_run` AND a matching-session-id scoped `.claude/current_run.<sid>` with different
  values; assert the hook's output row matches the scoped file, not the unscoped one.
- `test_two_concurrent_sessions_each_attributed_correctly` — write two distinct scoped sidecar files
  for two different session_ids; run the hook once per session_id; assert each resulting row matches
  its own session's scoped values, not the other's.
- `test_foreign_scoped_sidecar_not_read_by_different_session` — a scoped file exists for session
  "sess-other"; a hook invocation with `session_id="sess-1"` (no matching scoped file, unscoped file
  present) must fall back to the unscoped file, never read "sess-other"'s file.
- `test_stale_scoped_sidecar_pruned` — create a scoped sidecar file with `mtime` set >24h in the
  past; run the hook; assert the file no longer exists afterward.
- `test_fresh_scoped_sidecar_not_pruned` — same but with current mtime; assert it survives.

`tests/tools/test_current_run_sidecar_orchestrator.py`:
- `test_write_sidecar_also_writes_session_scoped_copy` — asserts the new
  `os.environ.get('CLAUDE_CODE_SESSION_ID', '')` / `.claude/current_run.' + sid` lines are present in
  `writeSidecar()`'s body, additive to (not replacing) the existing unscoped write.
- `test_scope_resume_branch_also_writes_session_scoped_copy` — same assertion for the Scope-phase
  `if (ticketId) { ... }` branch.
- All 15 pre-existing tests in this file re-run unmodified (no edits to any existing assertion).

New regression-guard (append to `tests/tools/test_current_run_sidecar_orchestrator.py`, since it
already imports/greps monitoring source files):
- `test_record_run_events_seq_offset_never_read_sidecar` — greps
  `tools/agent-monitoring/record_run.py`, `record_events.py`, `seq_offset.py` source text for
  `"current_run"`; asserts zero matches in all three.

## Scoped pytest commands

```
pytest tests/tools/test_post_tool_hook.py tests/tools/test_current_run_sidecar_orchestrator.py -v
pytest tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_seq_offset.py -q
pytest tests/docs/ -k "agent_monitoring or schema" -q
```

## Out of scope for testing

- No test exercises `retrieval_cache.py`'s sidecar read (deferred, unchanged).
- No test exercises `implement-epic.js`/`create-tickets.js` (no sidecar coverage there, unchanged,
  out of scope).
