---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-LAUNCH-RESUME-MISSING-WORKTREE-REFUSE
phase: done
date: 2026-10-18
tags: [ai, bug, workflows]
---

# TCK-20261018-LAUNCH-RESUME-MISSING-WORKTREE-REFUSE

## Title
`launch.py` crashes with FileNotFoundError on `os.chdir` when the manifest worktree is missing and not recreated

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
GitHub #620 part 2, claimed on #634 (host ubuntu, approved by lead-planner on 2026-10-18).

Repro: `python3 tools/sessions/launch.py asset-implementer --action resume` on host ubuntu.
- `ensure_worktree()` prints "worktree … is missing or prunable; recorded branch `main` is merged … not recreated" and returns notes only. This happens at `tools/sessions/launch.py` L225/L233/L229 for these cases:
  - no branch is recorded;
  - the branch is gone;
  - the branch is spent.
- `main()` carries on: `plan_launch`, `preflight(wt)`, `link_shared_graph(wt)`, then `os.chdir(wt)` at about L483 raises `FileNotFoundError`.

Every seat on ubuntu hits this, because seats there launch from the main checkout and work in `~/Work/rpg-*` worktrees, so the manifest paths under `.claude/worktrees/` don't exist. The owner's workaround today is `SESSION_ROLE=<role> claude --resume <id> --name <role> --agent session-<role>` from the main checkout.

## Scope
- After `ensure_worktree()`, and in dry-run as well, if `wt` is still not a directory:
  1. if `--worktree` wasn't given and `st.read_bound_worktree(sroot, target.instance)` names an existing directory, use that path as `wt`. Print one line naming the fallback (`manifest worktree <p> missing; using the recorded bound worktree <q>`);
  2. otherwise refuse with `EXIT_REFUSED`, with no traceback. Print the reason plus a fix hint with the **real role and instance filled in**: `cd <main checkout> && SESSION_ROLE=<instance> claude --resume <session-id or '<id>' only if unknown> --name <instance> --agent session-<role>`, plus the `--branch <topic>` alternative.
     - Never print a literal `<role>`.
     - When `plan_launch` resolves a session id, use it.
- The guard sits before `preflight`, `link_shared_graph`, `write_bound_worktree` and `os.chdir`, so nothing is written for a refused launch.
- Tests in `tests/tools/` (extend the existing launch tests) cover:
  - a missing worktree with an existing bound worktree → falls back, and the exec target cwd is the bound path;
  - a missing worktree with no bound path, or a bound path that doesn't exist → exits non-zero (`EXIT_REFUSED`), stdout/stderr contain the hint with the real role name, there's no `<role>` literal and no traceback;
  - an explicit `--worktree` that is missing → refuses, with no silent fallback;
  - the existing worktree path is unchanged (regression).

## Out of Scope
- #620 part 1 (host-suffixed roles: the owner chose option (a)). That's a separate batch-2 ticket.
- Recording each role's real worktree beyond today's `write_bound_worktree`.
- Changing `ensure_worktree`'s self-heal rules.

## Acceptance Criteria
- `launch.py <role> --action resume` with a missing manifest worktree never raises. It either launches in the existing bound worktree or exits `EXIT_REFUSED` with a filled-in hint.
- The tests above pass, and the `tests/tools` launch tests stay green.

## Related Tickets
- TCK-20261010-SESSION-LEASE-TAKEN-ON-LAUNCH-CWD-NOT-MANIFEST-WORKTREE
- TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD
- TCK-20261004-SESSION-LAYER-M2C-LAUNCHER-RECOVERY-AND-WORKTREE-SELF-HEAL

## Related Docs
- docs/guidelines/session_roles/ (launcher section, if it describes resume)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/sessions/launch.py (`main`, `ensure_worktree`)
- tools/sessions/state.py (`read_bound_worktree`)

## Assumptions / Open Questions
- The bound worktree is trusted only if it exists and is a git worktree of this repo (`git -C <q> rev-parse` succeeds).

## Implementation Notes
New `resolve_missing_worktree()` in `tools/sessions/launch.py`, called from `main()` after `plan_launch` and before `preflight`, `link_shared_graph`, `write_bound_worktree` and `os.chdir`. Skipped only for a dry run with `--branch` (it prints the worktree it would create). On a resume (a session id is resolved) the dead holder's own worktree comes first, since `claude --resume` only finds a transcript from the cwd it was written in (planner review). A bound worktree is accepted only if it is a directory and `git rev-parse --git-dir` succeeds there. The fallback keeps the bound record's own `explicit` flag.

## Test Summary
`tests/tools/test_session_launch.py`: 60 passed (7 new test functions, 8 cases): fallback to the bound worktree, refusal with no or gone bound path (non-zero exit, filled hint on stderr, no `<role>`, no traceback, nothing exec'd or written), session id in the hint, a resume prefers the holder's worktree over the bound one, explicit `--worktree` never falls back, dry run refuses, existing worktree unchanged.

## Files Changed
- tools/sessions/launch.py
- tests/tools/test_session_launch.py

## Completion Summary
`launch.py <role> --action resume` with a missing manifest worktree no longer raises `FileNotFoundError`: it launches in the existing bound worktree or exits `EXIT_REFUSED` with the real role/instance in the fix hint.
