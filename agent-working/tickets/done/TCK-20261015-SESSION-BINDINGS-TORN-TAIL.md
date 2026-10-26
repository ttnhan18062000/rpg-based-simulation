---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261015-SESSION-BINDINGS-TORN-TAIL
phase: done
date: 2026-10-15
tags: [hooks, data-quality]
---

# TCK-20261015-SESSION-BINDINGS-TORN-TAIL

## Title
A torn last line in a session-roles bindings.jsonl must not silence SessionStart; repair the torn rpg-implementer file

## Status
DONE

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

Evidence for the repair, 2026-10-26: lead-planner-u24's read-only output from u24desktop, relayed by lead-planner. In u24's main checkout `.git/session-roles/rpg-implementer/bindings.jsonl` is 13,779 bytes, 23 lines, and ends in `0a`; beside it is `bindings.jsonl.torn-20261017T152456Z`, 529 bytes, matching the ticket's 529-byte torn 14th line. That is #612's `append_binding` moving the tail aside on the next append, so no manual repair is needed. (The rpg-implementer file of this host was not touched: `.git/session-roles` is not edited from here.) Full `tests/tools` + `tests/docs` + `tests/codebase/test_repo_root_allowlist.py`, serial, on the tree merged with origin/main 3533fde71 (2026-10-26, MemoryMax 3G): 5338 passed, 58 skipped, 2 xfailed, 4 failed in 32 min. These 4 are load timeouts, not passes (60 s `--resource-budget medium` limit, host loadavg 3-4): `test_session_agent_generator.py::test_committed_files_have_no_drift`, `test_session_roster.py::test_real_registry_validates`, `test_session_u24_twins.py::test_row1_the_roster_validates_with_the_five_twins` (all three slow because `tools.sessions.validate` took 50 s; after TCK-20261026-VALIDATE-SPLIT-GLOBS-EXPANDED-ONCE the same tests pass, 86 passed in one rerun) and `test_wall_clock_inventory.py::test_cli_runs_are_byte_identical_and_do_not_import_src` (parses all of src/ twice; untouched by this batch; passed in one 4-test rerun, then timed out at 60 s twice under load, so it stays a known load-sensitive failure). Same-load comparison, back to back, 2026-10-27 (MemoryMax 3G, loadavg ~3): `test_wall_clock_inventory.py` alone on origin/main (exported, branch-free): 1 failed, 15 passed in 71 s, the CLI test at 60.02 s (timeout); on this branch: 1 failed, 15 passed in 76 s, the CLI test at 60.05 s. An earlier branch run passed that test at 62 s. So origin/main behaves the same: slow, at the 60 s edge, not caused by this batch. After the lint fix, `tests/tools/test_session_*.py`, `test_graphify_shim.py` and the paths guard: 836 passed.

## Files Changed
tools/sessions/state.py, tools/sessions/session_start_hook.py, tests/tools/test_session_state.py, tests/tools/test_session_resolve_and_hook.py

## Completion Summary
Done: the code landed in #612; the one-time repair happened by itself on u24desktop (13,779-byte file, 23 lines, ends in a newline, 529-byte torn sidecar `bindings.jsonl.torn-20261017T152456Z`; source: lead-planner-u24's read of 2026-10-26, relayed by lead-planner). Closed in the graphify and card-fold batch.

