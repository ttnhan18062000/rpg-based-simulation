---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START
phase: done
date: 2026-10-15
tags: [hooks, process-improvement]
---

# TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START

## Title
SessionStart warns when the worktree it runs from has stale session code or session registries, so a lagging worktree cannot inject the wrong role or handover note

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Source: RETRO-2026-W41 final note (PR #605), W41/W42 deep investigation 2026-10-15, finding 4. The SessionStart hook runs `python3 tools/sessions/session_start_hook.py` relative to the
session's own cwd, so it runs the worktree's copy. On 2026-10-15 a cleared rpg-implementer-2 (binding correct:
`.git/session-roles/rpg-implementer-2/instance.json`, source clear) was given `.claude/handover/rpg-implementer.md`. The `rpg`
worktree (`rpg-seat`, 108 commits behind origin/main) lacks #491's per-instance handover code. The same cause bound an
`rpg-implementer-3` launch as `rpg-implementer` on 2026-10-09. `tools/sessions/settings_freshness.py` compares only
`.claude/settings.json` and `.claude/agents/`, and only `launch.py` calls it, so a plain `claude --resume` and `/clear` skip it.

## Scope
1. Extend `settings_freshness.py` to also compare `tools/sessions/**`, `tools/handover_home.py`,
   `tools/agent-monitoring/session_start_handover_hook.py` and `registries/session_{roles,authority}.yaml` against
   origin/main (content compare, offline-safe: use the local origin/main ref, never fetch inside the hook).
2. `session_start_hook.py` runs that check on startup, resume and clear, and injects ONE warning line naming the stale
   paths and the fix ("sync this worktree to origin/main"). It must never fail the session (fail open, but say so).
3. Update the launcher/guide text that says freshness is checked only at launch.

## Out of Scope
- Running the hook from the main checkout's copy instead (weaker; mention it in the plan as rejected or deferred).
- Syncing any worktree (each seat syncs its own; the rpg worktree is rpg's).
- Editing `.claude/settings.json` (owner's file); if the hook command must change, put the literal diff in the PR for the owner.

## Acceptance Criteria
- A test with a fixture worktree whose `tools/sessions/session_start_hook.py` differs from origin/main gets the warning
  line in the SessionStart output; an identical one gets none.
- The check adds no network call and stays under the hook's time budget (measured, stated in Test Summary).
- `launch.py`'s preflight still refuses on a mismatch, as today.

## Related Tickets
- TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS
- TCK-20261009-PER-INSTANCE-HANDOVER-NOTE (#491)
- TCK-20261015-SESSION-BINDINGS-TORN-TAIL

## Related Docs
- docs/plans/agent_infrastructure/session_layer_working_process.md (section 5, 6)
- docs/guides/agent_session_reset_boundaries.md

## Related Stored Artifacts
- agent-working/agent-monitoring/retro/RETRO-2026-W41.md (final note, runs=281)

## Related Code Areas
- tools/sessions/settings_freshness.py, tools/sessions/session_start_hook.py, tools/sessions/launch.py
- tests/tools/ (session tests)

## Assumptions / Open Questions
- Open: compare by content hash or by `git diff --quiet origin/main -- <paths>`? The plan picks one; the hook must stay fast.

## Implementation Notes
`tools/sessions/settings_freshness.py`: `SESSION_CODE_PATHS` (tools/sessions, tools/handover_home.py, session_start_handover_hook.py, registries/session_{roles,authority}.yaml), `stale_session_code()` (one `merge-base`, one `diff --name-only <base> <ref> -- <paths>`, offline, never a fetch; None when it cannot tell) and `session_code_line()` (one line, fail-open and says so). The hook adds the line on startup, resume and clear (not compact). The plan's open question (content hash or `git diff --quiet`) is decided as: compare against the merge base, not the ref's content. A content compare would call every branch that edits session code stale, including this very batch, so the launch-time settings check keeps its content compare and this per-start check does not. Rejected, as the ticket allows: running the hook from the main checkout's copy. Time: 14 ms measured on this repo (state in the test file: three git calls, none a fetch). `launch.py`'s preflight is untouched (its tests pass). Guide updated.

## Test Summary
`tests/tools/test_session_settings_freshness.py` (6 new: current gives no line; behind names the stale file in one line; an ahead-only branch is not stale; no ref or no repo says it could not verify; a crash fails open and says so; offline and fast, three git calls) and `tests/tools/test_session_resolve_and_hook.py` (1 new: the hook line on startup, resume and clear, not compact).

## Files Changed
tools/sessions/settings_freshness.py, tools/sessions/session_start_hook.py, tests/tools/test_session_settings_freshness.py, tests/tools/test_session_resolve_and_hook.py, docs/guides/agent_session_reset_boundaries.md

## Completion Summary
SessionStart warns, in one line, when the session code or registries it runs from lag the local origin/main, naming up to four files. Measured 14 ms, no network.
