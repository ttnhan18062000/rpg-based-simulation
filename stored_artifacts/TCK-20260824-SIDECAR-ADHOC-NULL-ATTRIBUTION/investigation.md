# Investigation — TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION

## Current behavior (tools/agent-monitoring/post_tool_hook.py, pre-fix)

Per-tool-call attribution logic: if a scoped sidecar (`.claude/current_run.<session_id>`) exists
for the calling session, read it; otherwise unconditionally fall back to the shared unscoped
`.claude/current_run` file, whatever it currently holds.

## Are there real call sites that need the unscoped-fallback for legitimate non-null attribution?

Checked every sidecar-writer call site in `.claude/workflows/implement-ticket.js`:
- The resume branch (existing `ticketId` known at Scope start) writes BOTH the scoped and
  unscoped files together, immediately, before any other tool call in that phase.
- The new-ticket branch (no `ticketId` yet) clears the UNSCOPED file to `{}` (empty) — no scoped
  file exists yet, but the unscoped file is also empty, so any read during this window already
  yields null, not a foreign value.
- `writeSidecar()` (used by every subsequent phase transition) writes both files together,
  unconditionally, on every call.
- `.claude/skills/implement-ticket/SKILL.md`'s hand-orchestration instructions (updated by
  TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE) already require writing both files together for
  every `writeSidecar(seq, phase, agent)` call site.

Conclusion: in the current, real code, there is no remaining call site where a real ticket
workflow session exists with an in-progress ticket but relies on the unscoped-fallback for a
*real* (non-null) value. The window before a session's first real write is not "real workflow,
not yet scoped" in any way that needs non-null attribution — there IS no real attribution to
report yet at that point, for any session, ad-hoc or not. This significantly simplifies the
original ticket's own flagged design tension: no unreliable "is this session doing real ticket
work" signal (e.g. checking `tickets/inprogress/*.md`, already flagged unreliable by the
investigation) is needed.

## Existing test conflict

`test_foreign_scoped_sidecar_not_read_by_different_session` currently asserts the OLD behavior
(fall back to the unscoped file's real value when no scoped file exists) — this is exactly the
bug this ticket fixes, so the assertion is stale, not a durable invariant to preserve.

Three more tests (`test_phase_and_agent_included_when_sidecar_present`,
`test_execution_identity_fields_included_when_sidecar_present`,
`test_phase_and_agent_default_to_none_on_partial_sidecar`) also set up an UNSCOPED-only sidecar
with real values and session_id="sess-1" (the `_payload()` default) with no scoped file — under
the new behavior this would also read null, breaking these three. Their actual testing *purpose*
(validating phase/agent/execution-identity field extraction and partial-sidecar-content
tolerance) is orthogonal to ad-hoc-vs-real-workflow attribution — updated to write to the scoped
path (`current_run.sess-1`) instead of the unscoped path, preserving their original purpose while
tracking the new file-preference convention.
