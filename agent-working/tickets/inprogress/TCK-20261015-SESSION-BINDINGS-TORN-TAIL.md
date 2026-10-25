---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261015-SESSION-BINDINGS-TORN-TAIL
phase: inprogress
date: 2026-10-15
tags: [hooks, data-quality]
---

# TCK-20261015-SESSION-BINDINGS-TORN-TAIL

## Title
A torn last line in a session-roles bindings.jsonl must not silence SessionStart; repair the torn rpg-implementer file

## Status
INPROGRESS

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
Source: RETRO-2026-W41 final note (PR #605), W41/W42 deep investigation 2026-10-15, finding 4. `.git/session-roles/rpg-implementer/bindings.jsonl` (main checkout's common git dir) is exactly
8192 bytes, and its line 14 (2026-10-11T06:04:55Z compact record) is torn and has no newline; likely a short write when the
disk filled on 2026-10-11. `tools/sessions/state.py::read_bindings` (around L283-290) raises `StateError` on any bad line;
`session_start_hook.py` calls it unconditionally in `bind()` (around L166), and `main()` fails open silently (around
L267-271). So every future rpg-implementer start gets no card, no handover note and no warning.
`append_binding` (around L266-275) would also glue the next record onto the torn line. `instance.json` still names the dead
pid 964593 as holder.

## Scope
1. `read_bindings` tolerates an unparseable LAST line: skip it and report it (one warning line in the hook output);
   an unparseable line elsewhere still raises.
2. `append_binding` writes a leading newline when the file doesn't end in one.
3. On `StateError` the hook still injects the role card and handover note, and says the history could not be read.
4. One-time repair of the rpg-implementer file: move the torn tail into a `bindings.jsonl.torn-2026-10-11` sidecar next to
   it, and record the action in the ticket. Tell rpg-planner before touching it (their seat's state).

## Out of Scope
- Changing the bindings format.
- Clearing the stale holder in instance.json by hand (the hook's own dead-pid handling covers it; verify it, don't hand-edit).

## Acceptance Criteria
- Tests: a fixture bindings file with a torn last line still binds, the hook prints card and note plus one warning; a
  torn middle line still raises; append after a torn tail starts on a new line.
- After the repair, the next rpg-implementer SessionStart (or a dry run of the hook with its binding) shows card and note.

## Related Tickets
- TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START
- TCK-20261006-SESSION-START-CLEAR-FALSE-LIVE-HOLDER-WARNING

## Related Docs
- docs/plans/agent_infrastructure/session_layer_working_process.md

## Related Stored Artifacts
- agent-working/agent-monitoring/retro/RETRO-2026-W41.md (final note, runs=281)

## Related Code Areas
- tools/sessions/state.py, tools/sessions/session_start_hook.py
- .git/session-roles/rpg-implementer/ (runtime state, main checkout)

## Assumptions / Open Questions
- The repair touches runtime state under the main checkout .git: tell rpg-planner and the owner in the PR body.

## Implementation Notes
`tools/sessions/state.py`: `read_bindings_report()` skips an unparseable LAST line and returns a one-line warning; any other bad line, and a last line that parses as JSON but is not a binding, still raises `StateError`. `read_bindings()` delegates to it. `append_binding()` moves a torn tail into a `bindings.jsonl.torn-<UTC time>` sidecar under the same lock and cuts the file back to its last complete line before appending (planner review of #612: a newline alone would have turned the fragment into a middle line, a hard error on every later start), so the tolerance does not wear off. `tools/sessions/session_start_hook.py`: a torn tail adds one warning line; an unreadable history (`StateError`) no longer costs the card or the handover note, it says the history could not be read and skips only the manifest-change comparison. The one-time repair of `.git/session-roles/rpg-implementer/bindings.jsonl` is NOT done: my attempt was denied by the permission classifier (Modify Shared Resources) and I did not work around it. rpg-planner agreed to the timing and the move (only the torn tail). The owner runs it with a script (the commands, with byte checks, were sent to agent-working-planner on 2026-10-16): the file is 8192 bytes, 13 complete lines plus a torn 14th of 529 bytes with no newline; the move goes to `bindings.jsonl.torn-2026-10-11`; the file plus the sidecar must sum to 8192 and the file must keep 13 lines.

Planner note 2026-10-26 (agent-working-planner; batch assigned by the owner, #715 issuecomment-6401480227): the code landed in #612 (a8157c7ef). What remains is the one-time repair, and it may have happened by itself: `append_binding()` now moves a torn tail into a `bindings.jsonl.torn-<UTC time>` sidecar on the next append. On host ubuntu there is no `.git/session-roles/rpg-implementer/` (lead-planner, 2026-10-25), so the cited file is on u24desktop. Remaining work: get from u24 (via lead-planner -> lead-planner-u24) whether `.git/session-roles/rpg-implementer/bindings.jsonl` ends in a newline, its line count, and any `bindings.jsonl.torn-*` sidecar with its size. If a sidecar exists and the file is clean, record that as the repair and close. If the file is still torn, the owner runs the 2026-10-16 script on u24. No hand edit from host ubuntu.

## Test Summary
`tests/tools/test_session_state.py` (8 new: torn last line skipped and reported, intact file no warning, torn middle line raises, JSON-but-not-a-binding last line raises, append after a torn tail moves the fragment to a sidecar and keeps the history readable, a file that is only a fragment is emptied into the sidecar, two tears in one second lose neither, clean append adds no blank line) and `tests/tools/test_session_resolve_and_hook.py` (2 new: torn tail gives card, note and one warning and the next start is clean; unreadable history gives card, note and says so). Session suites pass.

## Files Changed
tools/sessions/state.py, tools/sessions/session_start_hook.py, tests/tools/test_session_state.py, tests/tools/test_session_resolve_and_hook.py

## Completion Summary
OPEN: code fix done. The repair of the rpg-implementer file and the check that its next SessionStart shows card and note are pending the owner's run; this ticket stays in inprogress/ until then and is left out of `Closes:`.

Note: the batch's other tickets are closed in `agent-working/tickets/done/`, and the batch folder (SEQUENCE.md) is already in `agent-working/tickets/done/w41-retro-followups/`; this ticket stays here, in `inprogress/`, only until the owner's repair of rpg-implementer's file is confirmed.

Update 2026-10-16 (planner's note): with the self-healing `append_binding`, rpg-implementer's torn file repairs itself on its next SessionStart that runs this code (the tail goes to a `bindings.jsonl.torn-<time>` sidecar), so the owner's manual repair is now optional. The ticket closes once a start of that seat is seen to show card and note AND the sidecar exists, whichever way the file got repaired. That start needs a worktree with this batch's code merged (`rpg` lags origin/main; see TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START).
