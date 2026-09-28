---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE
phase: done
date: 2026-09-28
tags: [agent-monitoring, data-quality]
---

# TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE

## Title

Every workflow's sidecar "clear" writes only the shared `.claude/current_run`, but the post-tool
hook reads only the per-session `.claude/current_run.<session_id>` file. So no clear has any effect,
and a finished run keeps absorbing tool calls.

## Status

DONE

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

- Verified the core claim directly before implementing: read `post_tool_hook.py` lines 112-136 —
  confirmed `sidecar_path` resolves to the scoped file whenever `session_id` is truthy (both the
  "exists" and "write null sentinel" branches), and the unscoped file is used only in the
  defensive "no session_id at all" branch. Confirmed `implement-ticket.js`'s own two pre-existing
  clears (line ~75, writeMonitoring's former Step 0 ~396) both only touch the shared file.
- Added one `clearSidecar()` helper per workflow file (no shared module exists between these
  standalone `.claude/workflows/*.js` files — matches the established `truncateSummary`/
  `captureTs`-style local-duplicate convention), dual-writing `{}` to both `.claude/current_run`
  and `.claude/current_run.$CLAUDE_CODE_SESSION_ID`, with the same exit-code-marker failure
  visibility as `writeSidecar()` (`CLEARSIDECAR_EXIT`, `log()` WARNING on failure, fail-open).
- `implement-ticket.js`: placed `clearSidecar` right after `resolveSeqOffset` (before its own
  first use site, the `else` branch — it could not be placed after `writeSidecar`'s own
  definition further down the file, a temporal-dead-zone `const` ordering bug caught before
  committing). Replaced both the `else`-branch inline clear and writeMonitoring's own agent-prompt
  "Step 0" text with `await clearSidecar()`, called orchestrator-side before the `agent()`
  dispatch in the writeMonitoring case (the ticket's own instruction: never put the clear inside
  an `agent()` prompt, whose shell isn't guaranteed to see the same `$CLAUDE_CODE_SESSION_ID`).
- `create-tickets.js`: same replacement for its own writeMonitoring Step 0 (added earlier by
  `TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED`, now corrected).
- `implement-epic.js`: had no clear at all. Added `clearSidecar()` calls at its 3 real exit
  points reached after any `writeSidecar()` write — the `EPIC_CREATED` return, the
  `NOTHING_TO_DO` return, and the final `DONE`/`STOPPED` return. The very first return
  (`INVALID_ARGS`) is correctly excluded — it fires before Discover's own `writeSidecar()` ever
  runs.
- Corrected the `create-tickets.js` write-sequence comment's own "permanently orphaned" claim
  (from `TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED`): before this ticket's own
  `pushEvent` fix, write-sequence and link-epic shared one `seq` value (no `pushEvent` ran between
  their two `writeSidecar()` calls), so write-sequence's rows were silently absorbed into Link's
  own event when an epic was linked, and genuinely orphaned only when it wasn't. Added the same
  correction as an addendum on the closed ticket itself.

## Test Summary

- New `tests/tools/test_sidecar_clear_reaches_scoped_file.py` — 5 tests, the real AC1 proof: runs
  each workflow's own real `clearSidecar()` shell command (extracted textually from the actual
  `.js` source, not re-implemented) against a `tmp_path` with a pre-populated stale scoped
  sidecar and `CLAUDE_CODE_SESSION_ID` set, then feeds a synthetic payload through the real
  `post_tool_hook.py` as a subprocess and asserts `run_id: null`. A parametrized case covers all
  3 workflows. A second test proves the OLD pre-fix command (shared file only) does **not** clear
  attribution against the identical setup — the real regression proof this ticket's own AC1 asks
  for. A third confirms the real command still also empties the shared file (no regression to the
  one legitimate fallback path).
- `tests/tools/test_current_run_sidecar_orchestrator.py` — 2 tests corrected: one pin updated
  (the `else`-branch literal), one rewritten from asserting the *broken* "Step 0" text was present
  to asserting the real orchestrator-side `clearSidecar()` call precedes the `agent()` dispatch.
- `tests/tools/test_create_tickets_sidecar_reset_and_failure_visibility.py` — same rewrite for
  create-tickets.js's own writeMonitoring, plus one new test pinning `clearSidecar()`'s dual-write
  shape.
- `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` — 4 new tests: the helper's own
  shape, and each of implement-epic.js's 3 new call sites (ordering relative to their own return).
- `node --check` on all 3 workflow files — exit 0.
- AC4: bare `pytest tests/tools/ -m "not slow and not extra_slow"`, run from the worktree — 3190
  passed, 25 skipped, 28 deselected, 1 xfailed, 0 failed.

## Files Changed

- `.claude/workflows/implement-ticket.js` — new `clearSidecar()` helper; both pre-existing
  shared-only clears replaced with it.
- `.claude/workflows/create-tickets.js` — new `clearSidecar()` helper; writeMonitoring's Step 0
  replaced with an orchestrator-side call; write-sequence comment corrected.
- `.claude/workflows/implement-epic.js` — new `clearSidecar()` helper; 3 new call sites (none
  existed before).
- `tests/tools/test_sidecar_clear_reaches_scoped_file.py` — new file, 5 behavioural tests.
- `tests/tools/test_current_run_sidecar_orchestrator.py` — 2 tests corrected.
- `tests/tools/test_create_tickets_sidecar_reset_and_failure_visibility.py` — 1 test rewritten, 1
  new test added.
- `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` — 4 new tests.
- `tickets/done/TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED.md` — Completion Summary
  addendum: AC3 was not actually met by that ticket, delivered here instead.
- `agent-monitoring/retro/RETRO-2026-W39.md` — regenerated (this ticket touches workflow prompts).
- `docs/REGISTRY.yaml` — regenerated (`make docs-registry`); no manual edits.

## Completion Summary

All 4 acceptance criteria met. The real defect — every workflow's sidecar "clear" only emptied
the file `post_tool_hook.py` doesn't read, a silent no-op inherited from `implement-ticket.js`'s
own pre-existing (and previously unverified) precedent — is fixed with one shared `clearSidecar()`
pattern per workflow, dual-writing both files exactly like `writeSidecar()` already does. Proven
behaviourally, not just by text pin: a real subprocess test runs each workflow's actual shell
command through the real `post_tool_hook.py` and confirms `run_id: null`, and confirms the old
command fails the identical test. `implement-epic.js`, which had no clear at all, now has one at
all 3 of its real exit points. The `CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED` ticket's AC3 claim
is corrected via addendum rather than silently rewritten. No known material gap left unstated.
