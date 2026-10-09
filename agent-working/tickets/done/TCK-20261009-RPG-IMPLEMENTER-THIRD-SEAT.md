---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-IMPLEMENTER-THIRD-SEAT
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-RPG-IMPLEMENTER-THIRD-SEAT

## Title
`rpg-implementer` allows only two sessions, so the owner's third rpg lane (`rpg-implementer-3`, Lane C) cannot launch

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
On 2026-10-09 the owner asked, relayed by rpg-planner and confirmed directly to agent-working-planner, for a third rpg implementer seat that launches with `python3 tools/sessions/launch.py rpg-implementer-3`. rpg's first Lane C work (two P1 bugs on the M0 gate path) waits on this seat. Today `launch.py rpg-implementer-3 --dry-run` fails with `unknown role 'rpg-implementer-3'` because `registries/session_roles.yaml` gives `rpg-implementer` `max_sessions: 2`. Instance names come from `tools/sessions/resolve.py::instance_ids()`, which yields `<role>-2 .. <role>-N`, so raising the cap is the whole mechanism. The new seat shares the role card, the authority (dispatch from user and rpg-planner, `may_write: ["**"]`) and the Needs-the-user list. Its role-state directory is keyed by its instance id.

## Scope
- `registries/session_roles.yaml`: change the `rpg-implementer` placement from `max_sessions: 2` to `max_sessions: 3`.
- Run `python3 tools/sessions/generate_agents.py` and commit whatever it regenerates. The card does not read `max_sessions` today, so no diff is expected; confirm that.
- Find any doc or guide under `docs/guidelines/session_roles/` or `docs/guides/` that says rpg has two implementer seats or lanes, and update it to three. If there are none, say so in Implementation Notes.
- Add a test in `tests/tools/test_session_launch.py` (or `test_session_resolve_and_hook.py`) over the real roster: `rpg-implementer-3` resolves to role `rpg-implementer` with instance `rpg-implementer-3`, and `rpg-implementer-4` is still unknown.
- Find out how the handover path is chosen for an instance beyond the first (`launch.py` and `tools/handover_home.py`), and record in Implementation Notes which path `rpg-implementer-3` reads, so rpg-planner seeds the right file. If instances 2 and later share `.claude/handover/rpg-implementer.md`, report it and do not change it in this ticket; it would be a follow-up.

## Out of Scope
- Seeding the handover note (rpg-planner does it); creating rpg worktrees; launching the session.
- Any change to the role card's text or authority.

## Acceptance Criteria
- AC1: `python3 tools/sessions/launch.py rpg-implementer-3 --dry-run` prints a launch plan (`--name rpg-implementer-3`, `SESSION_ROLE=rpg-implementer-3`, agent `session-rpg-implementer`) instead of "unknown role".
- AC2: the new test passes, and `pytest tests/tools/test_session_launch.py tests/tools/test_session_resolve_and_hook.py tests/tools/test_session_guard.py` is green.
- AC3: `python3 tools/sessions/settings_freshness.py .` and the generate_agents check report no drift.
- AC4: the handover path for instance 3 is written in Implementation Notes.
- AC5: closure by `record_hand_orchestrated_closure.py` (path reason `small_change`). Ships as its own one-ticket PR (owner decision 2026-10-09; it does not wait for a batch).

## Related Tickets
None.

## Related Docs
- `docs/guidelines/session_roles/` (generated cards and guides)

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `registries/session_roles.yaml`
- `tools/sessions/resolve.py`, `tools/sessions/launch.py`, `tools/sessions/roster.py`
- `tests/tools/test_session_launch.py`

## Assumptions / Open Questions
- Assumes nothing else hard-codes two rpg instances. The guard tests use `rpg-implementer-2` only as an example lease holder.

## Implementation Notes
- `registries/session_roles.yaml`: `rpg-implementer` `max_sessions` 2 -> 3. `generate_agents.py` rewrote the cards with no diff (confirmed; `--check` reports 0 drift).
- No doc or guide names two rpg implementer seats; `docs/guides/agent_session_reset_boundaries.md` only states the generic `<role>-2 .. <role>-N` rule.
- Handover path: `launch.py` uses `handover_base(root) / role.handover` for every instance, so `rpg-implementer-3` reads (and gets a stub at) the SAME note as instance 1 and 2: `<main checkout>/.claude/handover/rpg-implementer.md`. Not changed here; per-instance notes would be a follow-up.
- FINDING (not changed): all instances share `placement.worktree: rpg` (dry-run cwd `.claude/worktrees/rpg`), so the three seats would share one worktree, against the one-writer-per-worktree rule. A follow-up is needed for per-instance worktrees if Lane C is to run concurrently.

## Test Summary
New `test_the_real_roster_gives_rpg_implementer_three_seats_and_no_fourth`; test_session_launch + resolve_and_hook + guard: 237 passed. `settings_freshness.py .` matches. `launch.py rpg-implementer-3 --dry-run --allow-stale` prints the plan (`--name rpg-implementer-3`, `SESSION_ROLE=rpg-implementer-3`, agent `session-rpg-implementer`); without `--allow-stale` it refuses because other seats' agent cards differ from origin/main in this tree (unrelated to this change).

## Files Changed
`registries/session_roles.yaml`, `tests/tools/test_session_launch.py`, this ticket.

## Completion Summary
rpg-implementer now has three seats; `rpg-implementer-3` resolves, `-4` does not.
