---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261007-SESSION-PER-ROLE-WORKTREES
phase: open
date: 2026-10-07
tags: [ai, process-improvement]
---

# TCK-20261007-SESSION-PER-ROLE-WORKTREES

## Title
Give every designer and planner its own worktree so commit, push and open_pr work without racing the implementer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner-directed (agent-working-planner dispatch, 2026-10-07). `TCK-20261007-SESSION-GUARD-CRITICAL-ONLY-ASKS` empties `forbidden` for designers and planners, but the writer lease on a shared worktree still blocks them (two sessions committing into one worktree is a real race: `index.lock`, monitoring shards). Each designer and planner gets its own worktree and branch and lands its own PR. Depends on that ticket (PR #410) being merged; implement only after it.

## Scope
1. `registries/session_roles.yaml`: add 8 worktrees named after the roles (`rpg-designer`, `rpg-planner`, `agent-working-designer`, `agent-working-planner`, `testing-designer`, `testing-planner`, `codebase-designer`, `codebase-planner`), each `{writer: <same role>}`; point each designer and planner `placement.worktree` at its own; rewrite the `worktrees:` comment (it says the holder must be an implementer). Implementer worktrees (`rpg`, `agent-working`, `testing`, `codebase`) are unchanged.
2. `tools/sessions/validate.py`: relax "worktree writer must have the implementer function" to "a worktree's writer must be a role placed in that worktree"; also check that no worktree is shared by two writer-capable roles unless one is its writer.
3. `tools/sessions/launch.py`: first-launch bootstrap. When a role's worktree is missing and no branch is recorded it refuses today. Add an explicit path, with the dry run printing it: `git worktree add .claude/worktrees/<role> -b <role>-<topic> origin/main`. The topic comes from a `--branch` argument (no dates or phase numbers in branch names); never auto-create without it. Keep the spent-branch guard (fix C of `TCK-20261007-LAUNCHER-RELAUNCH-FIXES`).
4. `tools/sessions/session_start_hook.py`: confirm the lease is taken by a designer or planner in its own worktree (`wt.writer == role.role`), and that the first-instance rule (fix D) still holds; add a test.
5. Cards: regenerate; the "Worktree X" line changes for the 8 roles; keep the 400-token cap.
6. Docs: `docs/plans/agent_infrastructure/session_layer_working_process.md` (sections 3, 4: placement and writer slot) and `docs/guidelines/session_roles/` say each designer and planner works in its own worktree and branch and lands its own PR. Run `make knowledge-index-update`.
7. Tests (`tests/tools`): the manifest validates with the 8 new worktrees; the old "writer must be an implementer" case is gone; a launch dry run for a planner with a missing worktree plus `--branch` prints the add command and without `--branch` refuses; the hook takes the lease for a planner in its own worktree; the guard allows a planner commit in its own worktree and still denies one in the implementer's worktree (lease).

## Out of Scope
- Creating the 8 worktrees on disk and moving the live sessions (the owner's step after merge, one relaunch per role).
- Pruning old worktrees (a separate owner decision).
- Any change to implementer placement.

## Acceptance Criteria
- [ ] The manifest validates with the 8 new worktrees; the implementer-only writer check is gone
- [ ] `launch.py --dry-run --branch <topic>` for a planner with a missing worktree prints the `git worktree add` command; without `--branch` it refuses
- [ ] The hook takes the writer lease for a planner or designer in its own worktree
- [ ] A planner commit in its own worktree is allowed; in the implementer's worktree it is denied by the lease
- [ ] Cards regenerated within the 400-token cap; docs and knowledge index updated
- [ ] `pytest tests/tools -k "session or guard or classify"` green

## Related Tickets
- TCK-20261007-SESSION-GUARD-CRITICAL-ONLY-ASKS (PR #410; prerequisite)
- TCK-20261007-LAUNCHER-RELAUNCH-FIXES (fixes C and D this builds on)

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md`; `docs/guidelines/session_roles/`; `docs/guides/agent_session_reset_boundaries.md`

## Related Stored Artifacts
None yet (plan.md, investigation.md and test_plan.md are written when implementation starts; the planner reviews plan.md first).

## Related Code Areas
- `registries/session_roles.yaml`, `tools/sessions/{validate,launch,session_start_hook}.py`, `.claude/agents/session-*.md`, `tests/tools/`

## Assumptions / Open Questions
- Disk cost: one full checkout per role, 8 more.
- Should the designer and planner of one domain share a single non-implementer worktree instead? The owner asked for separate ones, so that is the default.
- Hand-orchestrated by default; a `Workflow` run needs the owner's opt-in.

## Implementation Notes
Not started.

## Test Summary
Not started.

## Files Changed
This ticket file only.

## Completion Summary
Not started.
