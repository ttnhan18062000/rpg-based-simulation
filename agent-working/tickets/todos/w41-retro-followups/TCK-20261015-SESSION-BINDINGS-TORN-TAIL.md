---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261015-SESSION-BINDINGS-TORN-TAIL
phase: open
date: 2026-10-15
tags: [hooks, data-quality]
---

# TCK-20261015-SESSION-BINDINGS-TORN-TAIL

## Title
A torn last line in a session-roles bindings.jsonl must not silence SessionStart; repair the torn rpg-implementer file

## Status
OPEN

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
(filled during work)

## Test Summary
(filled during work)

## Files Changed
(filled during work)

## Completion Summary
(filled at close)
