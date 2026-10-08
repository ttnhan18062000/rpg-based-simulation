---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261007-SESSION-PER-ROLE-WORKTREES
artifact_type: plan
tags: [ai, process-improvement]
---

# Plan: per-role worktrees

## Order (one branch `agent-working-per-role-worktrees`, one PR)
1. `registries/session_roles.yaml` (governing file: the owner confirms the literal diff via AskUserQuestion BEFORE the edit)
   - add 8 worktrees `{writer: <same role>}`: rpg-designer, rpg-planner, agent-working-designer, agent-working-planner, testing-designer, testing-planner, codebase-designer, codebase-planner.
   - each designer/planner `placement.worktree` -> its own name; implementer worktrees unchanged.
   - rewrite the `worktrees:` comment (the writer slot belongs to the worktree; a worktree hosts only its writer).
2. `tools/sessions/validate.py`: drop `writer-not-implementer` (code, docstring line 14); keep `worktree-writer` (writer is a role placed in that worktree). New finding `worktree-shared`: see Q1.
3. `tools/sessions/launch.py`: `--branch <topic>` argument; `ensure_worktree(..., new_branch=)`. With no recorded branch and the worktree missing: if `--branch` given, plan/run `git worktree add <path> -b <role>-<topic> origin/main` (dry run prints it); if not, refuse as today (message names `--branch`). Spent-branch guard (fix C) and "branch no longer exists" paths unchanged. The topic is validated: `[a-z0-9-]+`, no date or phase-number patterns (reject `\d{8}`, `phase-?\d`).
4. `tools/sessions/session_start_hook.py`: no code change expected (`wt.writer == role.role and instance_id == role.role` already holds for a designer/planner in its own worktree); add tests only. Change code only if a test shows otherwise.
5. Regenerate cards (`tools/sessions/generate_agents.py`); check 400-token cap on all 12 cards.
6. Docs: `session_layer_working_process.md` sections 3 and 4; `docs/guidelines/session_roles/`; `make knowledge-index-update`.
7. Tests under `tests/tools/` (see test_plan.md).

## Scope guards
- No change to implementer placement, to `guard.py`, to `session_authority.yaml`.
- No worktree is created on disk (owner step after merge).
- No `Workflow` run; hand-orchestrated closure via `record_hand_orchestrated_closure.py`.

## Questions for the planner
- Q1: the ticket says "no worktree shared by two writer-capable roles unless one is its writer". Every role can be placed, so that is satisfied today (rpg hosts designer, planner, implementer) and the check would be vacuous. Proposal: stricter and testable, every worktree hosts exactly one role, its writer (`worktree-shared` finding when a worktree has any placed role other than its writer). Any reason to allow sharing later?
- Q2: `interim_holder` seats (codebase-*, testing-designer, agent-working-planner) get worktrees too, as the ticket lists; the interim holder launches into that role's worktree. OK?
- Q3: branch name `<role>-<topic>` for e.g. `agent-working-planner-foo`. The repo's existing branches use `agent-working-<topic>` (the domain prefix). OK to follow `<role>-<topic>` as the ticket says?
