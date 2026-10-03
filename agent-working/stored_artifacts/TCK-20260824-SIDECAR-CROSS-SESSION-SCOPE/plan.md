# Plan — TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE

## Design decisions (made here, per the ticket's own Assumptions requiring a judgment call)

1. **Scoping key: `CLAUDE_CODE_SESSION_ID` env var**, read inside the `python3 -c` write scripts via
   `os.environ.get('CLAUDE_CODE_SESSION_ID', '')`. Zero new races: it's a stable, process-level env
   var set once by the harness per session, not a shared mutable file. Matches the `session_id`
   `post_tool_hook.py` already extracts from its own hook payload on the read side.
2. **Additive, not replacing**: keep writing the existing unscoped `.claude/current_run` exactly as
   before (for `retrieval_cache.py` and `.claude/settings.json`'s inline sidecar-check, both
   explicitly deferred — see investigation.md), and additionally write
   `.claude/current_run.<session_id>`. `post_tool_hook.py` prefers the scoped file, falling back to
   the unscoped one when absent. This means every existing test (none of which write a scoped file)
   keeps passing unmodified — verified, not assumed (see Test Summary).
3. **Historical data**: accept as documented caveat, no backfill, no new flag — see
   investigation.md's rationale (existing repo precedent, disproportionate detector cost, append-only
   law).
4. **retrieval_cache.py / settings.json inline check**: deferred, not migrated — documented
   explicitly, not silently.
5. **Lifecycle**: `post_tool_hook.py` prunes `.claude/current_run.*` scoped files older than 24h on
   every invocation (fail-open).

## Steps

1. `tools/agent-monitoring/post_tool_hook.py`: change sidecar read to prefer
   `.claude/current_run.<session_id>`, fall back to `.claude/current_run`; add
   `_prune_stale_scoped_sidecars()` (24h threshold), called fail-open after the main write.
2. `.claude/workflows/implement-ticket.js`: extend `writeSidecar()`'s python3 script to also write
   the session-scoped copy when `CLAUDE_CODE_SESSION_ID` is set; same for the Scope-phase resume
   branch (`if (ticketId) { ... }`). The new-ticket `else` branch (`printf '{}' > .claude/current_run`)
   is left untouched — no real run_id exists yet to scope, and the existing test asserts this exact
   literal string.
3. `.claude/skills/implement-ticket/SKILL.md`: update the hand-orchestration sidecar-write
   instruction to mention the additive session-scoped write (for hand-orchestrating agents copying
   this pattern manually).
4. `docs/agent-monitoring/schema.md`: add a paragraph to "How tool calls are attributed to agent
   events" documenting the fix, the confirmed 2026-08-24 finding, and the no-backfill decision.
5. Tests:
   - `tests/tools/test_post_tool_hook.py`: new tests — scoped file present + different values than
     unscoped → scoped wins; two concurrent "sessions" (distinct session_ids, distinct scoped
     sidecar values) each produce correctly-attributed rows even with a stale/foreign unscoped file
     present; stale scoped file (mtime > 24h) gets pruned; a scoped file for a *different* session_id
     is never read by a session whose own id differs (foreign-file non-leak guarantee).
   - `tests/tools/test_current_run_sidecar_orchestrator.py`: new assertions that the additive
     session-scoped write line is present in `writeSidecar()`'s body and the Scope-phase resume
     branch, without touching any existing assertion.
   - New regression-guard test (either new test file or appended to an existing monitoring test
     file) asserting `grep -n "current_run"` on `record_run.py`/`record_events.py`/`seq_offset.py`
     stays empty.
6. `docs/parity_ledger/infrastructure.yaml`: new entry (P2, this is an observability/tooling
   correctness fix, not a gameplay-mechanics change).
7. Run scoped test suite (see test_plan.md).
8. Finalize per CLAUDE.md: move ticket to `tickets/done/`, delete from
   `tickets/todos/sidecar-cross-session-fix/`, move the now-empty folder to
   `tickets/done/sidecar-cross-session-fix/`, append `tickets/working_log.csv`, move staging
   artifacts to `stored_artifacts/`, regenerate `docs/REGISTRY.yaml` (docs changed), run
   `make knowledge-index-update`, write agent-monitoring run/event records, commit.

## Anti-drift notes

- Do NOT touch `record_run.py`, `record_events.py`, `seq_offset.py` (C3 confirmed no dependency).
- Do NOT rewrite any existing `tools.jsonl` row in place.
- Do NOT touch `tools/agent-monitoring/writer.py`'s lock-file protocol (separate, already-solved
  concurrent-append problem).
- Do NOT add sidecar coverage to `implement-epic.js`/`create-tickets.js`.
- Preserve every existing assertion in `test_current_run_sidecar_orchestrator.py` and
  `test_post_tool_hook.py` verbatim — additive changes only.
