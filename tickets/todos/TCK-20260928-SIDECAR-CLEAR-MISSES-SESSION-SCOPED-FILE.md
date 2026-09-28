---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE
phase: open
date: 2026-09-28
tags: [agent-monitoring, data-quality]
---

# TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE

## Title

Every workflow's sidecar "clear" writes only the shared `.claude/current_run`, but the post-tool
hook reads only the per-session `.claude/current_run.<session_id>` file. So no clear has any effect,
and a finished run keeps absorbing tool calls.

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

Found reviewing `TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED` (PR #253, `d1ad0008f`).
That ticket fixed its anomaly 3 (a 4-hour tail of tool rows on a finished `create-tickets` run) by
adding `printf '{}' > .claude/current_run` as writeMonitoring Step 0, mirroring
`implement-ticket.js`. The mirror carries the same defect as the original.

`tools/agent-monitoring/post_tool_hook.py` (lines ~119-136 on the PR branch): when the hook payload
has a `session_id`, which real Claude Code hooks always supply, it reads **only**
`.claude/current_run.<session_id>`. If that file is missing, it writes a null sentinel there. It
never falls back to the shared `.claude/current_run` (TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE).
Every workflow's `writeSidecar` writes both files, using `CLAUDE_CODE_SESSION_ID`. Attribution
therefore runs entirely through the scoped file, and a clear that writes only the shared file is a
no-op.

Affected clears on `origin/ticket-corpus-guard-test-scope-map`:
- `.claude/workflows/implement-ticket.js`: line ~75 (`printf '{}' > .claude/current_run`) and
  writeMonitoring Step 0 (line ~396). Both touch only the shared file.
- `.claude/workflows/create-tickets.js`: the new writeMonitoring Step 0 (`d1ad0008f`), same.
- `.claude/workflows/implement-epic.js`: has **no clear at all**, only `writeSidecar` writes.

That explains anomaly 3, and very plausibly the earlier live observation that a closed ticket kept
absorbing tool-call rows for two days after it closed. The new pin
`test_write_monitoring_clears_the_sidecar_before_any_other_step` asserts the shared-file literal
is present, so it passes while the clear has no effect.

## Scope

1. Give all three workflows one clear shape that empties the file the hook reads. Run it on the
   orchestrator side via `bash()`, the same channel and environment as `writeSidecar`, so
   `CLAUDE_CODE_SESSION_ID` resolves to the same session whose scoped file `writeSidecar` wrote.
   Don't put it in an `agent()` prompt, whose shell may not see the same session ID. The shape:
   write `{}` to `.claude/current_run` and, when `CLAUDE_CODE_SESSION_ID` is set, to
   `.claude/current_run.$CLAUDE_CODE_SESSION_ID`. Keep it fail-open (monitoring must never fail
   the workflow), with a visible warning on failure, like the new `writeSidecar`.
2. Call it where each workflow's run ends: before its monitoring write, and on every exit path.
   That covers implement-ticket (replacing both shared-only clears), create-tickets (replacing the
   new Step 0 prompt text, or leaving it but adding the real clear before the agent call), and
   implement-epic (new: after its final phase and on early-return paths).
3. Tests in `tests/tools/`. These must be behavioural, not just text pins: run the clear command
   in a `tmp_path` cwd with `CLAUDE_CODE_SESSION_ID` set and a pre-populated scoped sidecar, then
   feed a synthetic hook payload through `post_tool_hook.py`'s resolution and assert the
   resulting row has `run_id` null. Show that the pre-fix command (shared file only) fails the
   same test. Also add per-workflow pins that each exit path calls the shared clear.
4. Fix the text in `TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED` (already closed):
   - Add a Completion Summary addendum that its AC3 claim was not met by `d1ad0008f` and is
     delivered here.
   - Correct the `create-tickets.js` comment on the new write-sequence `pushEvent`. Before it,
     write-sequence and link-epic both wrote the sidecar as `events.length + 1` with no push
     between them, so they **shared** a seq. write-sequence's rows were therefore counted into
     the Link event, and orphaned only when there was no epic link, not "permanently orphaned"
     in every batch. The new push is still right, because it separates the two; only the stated
     rationale is wrong.
5. Retro cadence: this changes workflow prompts, so regenerate the current week's retro before
   the prompt commit.

## Out of Scope

- Changing `post_tool_hook.py`'s resolution order. Its no-fallback rule is a deliberate fix for
  cross-session contamination (TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE). The clears must target
  the file it reads, not the other way round.
- Rewriting historical misattributed rows.
- The `pipeline()` fan-out exclusions (deliberate).

## Acceptance Criteria

- AC1: After each workflow's end-of-run clear, a hook call from the same session records
  `run_id: null`. This is proven by the behavioural test, which fails on the pre-fix command.
- AC2: implement-ticket, create-tickets and implement-epic each call the shared clear on every
  exit path, pinned per workflow.
- AC3: The `CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED` addendum and the write-sequence comment
  correction are in place.
- AC4: The retro is regenerated before the prompt commit, and bare `pytest tests/tools/` passes
  from the worktree.

## Related Tickets

- `TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED`: where this was found. Its AC3 is
  delivered here.
- `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`: introduced the scoped file and the no-fallback read.
- `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`: the original reason for clearing.
- `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION`: needs this fixed before a new
  `create-tickets`/`implement-epic` run can confirm clean attribution.

## Related Docs

- `docs/agent-monitoring/README.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED/investigation.md`

## Related Code Areas

- `.claude/workflows/implement-ticket.js`, `.claude/workflows/create-tickets.js`,
  `.claude/workflows/implement-epic.js`
- `tools/agent-monitoring/post_tool_hook.py` (read-only reference)
- `tests/tools/`

## Assumptions / Open Questions

- Assumes the Workflow `bash()` helper's environment carries `CLAUDE_CODE_SESSION_ID`, because
  `writeSidecar` relies on the same assumption and attribution demonstrably works through the
  scoped file. If the investigation shows otherwise, stop and report rather than guessing a
  session ID.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
