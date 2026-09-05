---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE
phase: open
date: 2026-09-04
tags: [ai, hooks, agent-monitoring]
---

# TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE

## Title
Migrate settings.json PreToolUse hook to session-scoped sidecar reads

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE added a session-scoped `.claude/current_run.<SESSION_ID>` variant because the old unscoped file was silently overwritten by concurrent sessions, misattributing `tools.jsonl` rows, and left two consumers explicitly reading the old unscoped file. Investigation found this framing is now stale: `tools/retrieval_cache.py`'s `read_current_run_sidecar()` was already migrated by TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY (closed 2026-08-24), so only one real straggler remains — `.claude/settings.json`'s inline `Edit|Write` PreToolUse hook (line 88), which still reads `.claude/current_run` directly via `python3 -c` with no session scoping. This ticket is scoped down to that single file to avoid duplicate effort on the already-fixed consumer.

## Scope
- Update `.claude/settings.json`'s `Edit|Write` PreToolUse hook (inline `python3 -c` one-liner, line 88) to read the scoped sidecar file `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` first (via `os.environ.get`), falling back to the unscoped `.claude/current_run` when the scoped file doesn't exist — same preference order as `read_current_run_sidecar()`/`post_tool_hook.py`
- Verify a synthetic two-session scenario (two distinct scoped files with different run_ids, plus a stale/foreign unscoped file) resolves RUN_ID to the calling session's own value, not the foreign one
- Add a new regression-guard test mirroring `test_current_run_sidecar_orchestrator.py`'s static-source-string pattern that asserts the exact updated command string in `.claude/settings.json`

## Out of Scope
- `tools/retrieval_cache.py` — already migrated by TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY; do not re-touch
- Any changes to monitoring write semantics beyond the settings.json hook's read source (must remain fail-open, preserving the existing `2>/dev/null || true`)
- Resolving the shared-file coordination with TCK-20260904-BASH-SECRET-SCAN-HOOK and TCK-20260904-TEST-SCOPER-HANG-GUARD's own hooks-block additions to `.claude/settings.json` beyond an additive merge/rebase — no sequencing dependency is created

## Acceptance Criteria
- [ ] The Edit|Write PreToolUse hook's inline `python3 -c` one-liner in `.claude/settings.json` reads `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` (via `os.environ.get`) when that scoped file exists, falling back to the unscoped `.claude/current_run` when it doesn't
- [ ] A synthetic two-session scenario (two scoped files with different run_ids plus a stale/foreign unscoped file) demonstrates the hook resolves RUN_ID to the calling session's own value
- [ ] `tools/retrieval_cache.py` is left untouched (already correct) — the ticket's Scope explicitly states this
- [ ] A new regression-guard test (mirroring `test_current_run_sidecar_orchestrator.py`'s static-source-string pattern) asserts the exact updated command string in `.claude/settings.json`

## Related Tickets
- TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE
- TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY
- TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/settings.json
- tools/retrieval_cache.py
- tools/agent-monitoring/post_tool_hook.py
- .claude/workflows/implement-ticket.js
- tests/tools/test_current_run_sidecar_orchestrator.py
- tests/tools/test_retrieval_cache.py
- tests/tools/test_post_tool_hook.py

## Assumptions / Open Questions
- The original concern's "2 remaining stragglers" framing is factually stale — only 1 (settings.json) remains unmigrated; this must be stated explicitly in the ticket rather than silently corrected
- This hook fires in a bare shell/`python3 -c` context with no hook-payload `session_id` field (unlike `post_tool_hook.py`), so it must read `CLAUDE_CODE_SESSION_ID` directly from the environment, the same forced approach `retrieval_cache.py` already took
- This hook is purely advisory — a stale/wrong RUN_ID degrades to a missing or wrong reminder, not data corruption, which bounds the blast radius of any residual edge case

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
