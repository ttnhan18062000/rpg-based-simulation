---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-SESSION-START-CLEAR-FALSE-LIVE-HOLDER-WARNING
phase: done
date: 2026-10-06
tags: [ai, hooks]
---

# TCK-20261006-SESSION-START-CLEAR-FALSE-LIVE-HOLDER-WARNING

## Title
After `/clear`, the SessionStart hook warns "another LIVE instance already holds role X" about the same process's own pre-clear session

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Reported by rpg-implementer on 2026-10-06. After a `/clear`, its SessionStart context said "session-roles: another
LIVE instance already holds role `rpg-implementer` (session af245d7d-…); two writers on one role is not
supported." Session af245d7d was the same seat before the `/clear`. rpg-feature-planning confirmed rpg-implementer
was the only holder.

Root cause, verified against `.git/session-roles/rpg-implementer/bindings.jsonl`. The bindings show sessions
95b01e4e → af245d7d → c3c03123, all with `source: clear` and all in the same pid 2366257 (same `start`). A `/clear`
gives a new `session_id` in the same Claude process. In `tools/sessions/session_start_hook.py` (around :121–124, on
origin/main `9299891a9`) the warning fires when two conditions hold:
- `prior_instance.holder.session_id != binding.session_id`, which is true after every `/clear`;
- `st.liveness(prior_instance) == LIVE`, which is true because the prior holder's recorded process is this same,
  still-running process.

So every `/clear` of a role-bound session produces this false warning. The agent-working-implementer's bindings
show the same pattern (pid 721464, `source: clear`). A seat that obeys the warning would stop work. A seat that
learns to ignore it would also ignore a real second holder.

The reporter's repro ("resume from a different cwd") is not the trigger. A real `claude --resume` starts a new
process, so the old pid is dead, the prior holder reads ORPHANED and no warning fires. The trigger is `/clear`
inside the same process.

## Scope
1. In `session_start_hook.py`, do not warn when the prior holder's recorded process equals the current process
   (same pid and same start time, i.e. `ProcessId` equality). That holder is this session's own predecessor,
   superseded in place. Keep the warning when the prior holder is a different live process.
2. Tests:
   - (a) `/clear`-style supersession: same `ProcessId`, different `session_id` → no warning;
   - (b) a different live process → warning;
   - (c) a dead prior process → no warning (existing behaviour, keep it covered).
3. Folded in by owner decision, 2026-10-06: split the retro's "Runs by session role" table. In
   `tools/agent-monitoring/session_layer_report.py::render()` (around :64–70 on origin/main), runs with no
   `session_role` key are currently counted as `unresolved`. Count them as `predates field` instead, and keep
   `unresolved` for runs stamped unresolved because no binding named the closing session. Update the footnote to
   match.

   Background: the agent-working-implementer measured 63 W41 runs on main. 33 have no `session_role` field and 30
   are stamped `unresolved`, yet RETRO-2026-W41 printed all of them as "unresolved". If
   TCK-20261006-RETRO-DARK-INSTRUMENT-SHOWN-AS-ZEROS has merged, keep its all-unresolved line consistent: it should
   fire only when every run that has the field is `unresolved`.

## Out of Scope
- The binding and lease model itself (`state.py`), and release on `/clear`. Supersession already overwrites the
  holder via `record_start`; only the warning predicate is wrong.
- Launcher behaviour (`launch.py`), which reads liveness for its own refuse/offer decision. Check whether it has
  the same predicate. If it does, record it as a finding; do not fix it here.

## Acceptance Criteria
1. The three tests above pass, using fixture `/proc` roots like the existing tests in `tests/tools/`.
2. Replaying rpg-implementer's 2026-10-06T02:26:56Z `clear` binding (pid 2366257, prior holder af245d7d on the same
   pid) through the predicate yields no warning.
3. `launch.py`'s liveness use is checked and the finding recorded in Implementation Notes.
4. A test renders a mix of runs with no field, runs stamped unresolved and runs with a role as three distinct
   rows: `predates field`, `unresolved` and the role. A test checks the footnote names both meanings.

## Related Tickets
- TCK-20261004-SESSION-LAYER-M2C (launcher, state)
- TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md`
- `docs/guides/agent_session_reset_boundaries.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `tools/sessions/session_start_hook.py`, `tools/sessions/state.py` (`liveness`, `is_live`, `ProcessId`)

## Assumptions / Open Questions
- Assumes Claude Code keeps the same OS process across `/clear`. The bindings (same pid and start across three
  `clear` sources) confirm it.

## Implementation Notes
Re-verified on origin/main 9299891a9: the warning predicate was at session_start_hook.py :121-124 (now shifted). `_same_process(recorded, current)` compares pid and start time (not the command line) and the warning is suppressed when it is true; a different live process, a dead one and an unknown process behave as before. The supersession itself (`record_start`) is unchanged and tested.
Scope 3: `session_layer_report.render` counts a run with no `session_role` key as `predates field`; a stamped `unresolved` stays `unresolved`; the footnote names both. The all-unresolved line now fires only when every run that HAS the field is unresolved (runs predating it are ignored, and a window of only such runs says nothing).
AC3 finding (launcher): `launch.py::plan_launch` refuses on a LIVE holder, but it runs in a NEW process that is by construction not the recorded holder, and a `/clear` never goes through the launcher, so it has no equivalent false positive; no change. (`_same_process` is local to the SessionStart hook.)

## Test Summary
`tests/tools/test_session_resolve_and_hook.py` (4 new: clear in the same process, a different live process, a dead process, replay of the recorded pid 2366257 binding incl. pid reuse) and `tests/tools/test_session_layer_measures.py` (2 new, 1 updated): with the launcher, state and paths-guard tests, 134 passed.

## Files Changed
`tools/sessions/session_start_hook.py`, `tools/agent-monitoring/session_layer_report.py`, `tests/tools/test_session_resolve_and_hook.py`, `tests/tools/test_session_layer_measures.py`.

## Completion Summary
A `/clear` no longer produces a false "another LIVE instance" warning, and the retro's session-role table tells runs that predate the field apart from runs with no binding.
