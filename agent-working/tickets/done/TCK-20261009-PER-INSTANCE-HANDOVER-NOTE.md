---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-PER-INSTANCE-HANDOVER-NOTE
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-PER-INSTANCE-HANDOVER-NOTE

## Title
Every instance of a multi-session role reads and writes the same handover note, so `rpg-implementer`, `-2` and `-3` overwrite each other's notes

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by TCK-20261009-RPG-IMPLEMENTER-THIRD-SEAT (PR #467). `launch.py` (lines 366 and 470) and the SessionStart hook resolve the handover path as `handover_base(root) / role.handover`, which is keyed by ROLE. Role-state directories are keyed by INSTANCE. So `rpg-implementer`, `rpg-implementer-2` and `rpg-implementer-3` all read and write `<main checkout>/.claude/handover/rpg-implementer.md`. The stub text even formats `role=target.instance` into that shared file. The owner asked for the third seat to have its own `.claude/handover/rpg-implementer-3.md`.
The same ticket also found that every instance shares `placement.worktree: rpg`. rpg's rule already has each piece cut its own worktree from origin/main, and the guard's worktree lease refuses a second writer. So the shared launch worktree is a launch cwd, not a write location. This ticket checks that, and changes code only if the lease does not cover it.

## Scope
- One helper (e.g. in `tools/sessions/roster.py` or `launch.py`) gives an instance's handover path: the role's `handover` for the first instance, and `<stem>-N<suffix>` beside it for `<role>-N`. Use it at every site that reads or writes the note: `launch.py` (stub creation, evidence, `--dry-run` print), `session_start_hook.py` injection, and the reset-boundary/handover tooling that names the path. Find them with `grep -rn "\.handover\b" tools/`.
- The generated session card and system prompt text: check whether they name the role's handover path literally ("main-checkout `.claude/handover/<role>.md`"). If so, say in the card that instance N reads `<role>-N.md`, through `generate_agents.py`, not by hand.
- Tests: instance 1 keeps the role path; `rpg-implementer-3` gets `.claude/handover/rpg-implementer-3.md`, and the stub is created there; the hook injects the instance's own note.
- Worktree point: read `tools/sessions/guard.py`'s lease logic and write in Implementation Notes whether two live instances launched into `.claude/worktrees/rpg` can both commit there. If the lease already refuses the second writer, record that and change nothing. If not, report it to agent-working-planner before changing anything.

## Out of Scope
- Moving any existing note. `rpg-implementer.md` stays instance 1's. Instance 2's state in that shared file is for rpg-planner to split out by hand if needed.
- Per-instance worktrees in `session_roles.yaml`.

## Acceptance Criteria
- AC1: `launch.py rpg-implementer-3 --dry-run` prints `.claude/handover/rpg-implementer-3.md` as the handover note; `launch.py rpg-implementer --dry-run` still prints `rpg-implementer.md`.
- AC2: the SessionStart hook for `SESSION_ROLE=rpg-implementer-3` injects `rpg-implementer-3.md`, tested.
- AC3: `generate_agents.py` check shows no drift after regeneration; `pytest tests/tools/test_session_*.py` green.
- AC4: the worktree-lease finding is written in Implementation Notes.
- AC4b (planner amendment): an existing `<role>-N.md` is read unchanged and never overwritten by the stub; the path is exactly `<role>-N.md`. Tested with a pre-existing `rpg-implementer-2.md` (byte-identical after a launch).
- AC5: closure by `record_hand_orchestrated_closure.py` (`small_change`).

## Related Tickets
- TCK-20261009-RPG-IMPLEMENTER-THIRD-SEAT (PR #467; found this)

## Related Docs
- `docs/guidelines/session_roles/`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tools/sessions/launch.py`, `tools/sessions/session_start_hook.py`, `tools/sessions/roster.py`, `tools/sessions/guard.py`, `tools/handover_home.py`, `tools/sessions/generate_agents.py`

## Assumptions / Open Questions
- Naming `<role>-N.md` matches the instance id, which is what rpg-planner already expects (`.claude/handover/rpg-implementer-3.md`).

## Implementation Notes
- New `roster.handover_rel(role, instance_id)`: the role's note for instance 1, `<stem>-N<suffix>` beside it for `<role>-N`. Used by `launch.py` (evidence, dry-run print, stub), `session_start_hook._handover_text` (injection and its messages) and the card line (`instance N of <role> reads <role>-N.md`, only for roles with max_sessions > 1, via generate_agents). `--dry-run` now always prints the path (with "none yet" when absent). `tools/agent-monitoring/session_start_handover_hook.py` only globs `*.md` and needed no change. `validate.py` checks the role's own `handover`, unchanged.
- Worktree lease finding (guard.py + session_start_hook): only the role's FIRST instance takes the writer lease (`instance_id == role.role`). The guard refuses commit/push/open_pr when a lease exists and `lease_role != caller.instance`, so while `rpg-implementer` (instance 1) is live in `.claude/worktrees/rpg`, instances 2 and 3 are refused there. Gaps: (a) with instance 1 not running no lease exists and "no lease at all is not a denial", so `-2` and `-3` launched into `rpg` together are NOT refused; (b) instances 2/3 never take a lease themselves. Per the rule, no change; reported to agent-working-planner. In practice rpg's rule cuts per-piece worktrees from origin/main so the shared launch cwd is not a write location.

## Test Summary
New tests: per-instance path + dry-run print, stub at instance path, existing -2 note byte-identical, hook injects rpg-implementer-3.md. tests/tools/test_session_*.py: 587 passed (before the AC4b test; test_session_launch 48 passed after). generate_agents --check: 0 drift.

## Files Changed
`tools/sessions/{roster,launch,session_start_hook,card}.py`, `.claude/agents/session-rpg-implementer.md` (regenerated), `tests/tools/test_session_launch.py`, `tests/tools/test_session_resolve_and_hook.py`.

## Completion Summary
Each instance reads and gets its stub at `<role>-N.md`; instance 1 keeps the role path.
