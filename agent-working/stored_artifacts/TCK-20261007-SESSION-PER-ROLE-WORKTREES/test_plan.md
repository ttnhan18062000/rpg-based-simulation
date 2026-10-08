---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261007-SESSION-PER-ROLE-WORKTREES
phase: open
date: 2026-10-07
tags: []
---

# Test plan

All in `tests/tools/` (run with `/mnt/data/Working/rpg-based-simulation/.venv/bin/python -m pytest tests/tools -k "session or guard or classify"`).
1. Manifest: the real `registries/session_roles.yaml` validates with 0 findings; each of the 8 roles has its own worktree with itself as writer.
2. Validator: a synthetic roster with a designer as writer validates; the old `writer-not-implementer` case is removed; a worktree whose writer is placed elsewhere still gives `worktree-writer`; a worktree with a second placed role gives `worktree-shared` (per Q1).
3. Launch: planner, worktree missing, no recorded branch: with `--branch topic --dry-run` prints `git worktree add <path> -b agent-working-planner-topic origin/main`; without `--branch` refuses and names `--branch`; a bad topic (date, phase number, uppercase) is refused; a recorded merged branch still refuses (fix C); an existing worktree ignores `--branch`.
4. Hook: a planner started in its own worktree takes the lease; `<role>-2` does not (fix D).
5. Guard: planner commit in its own worktree allowed; a planner commit in the implementer's worktree denied by the lease.
6. Cards: regeneration is a no-op diff after commit; every card within 400 tokens.

## Proof Plan
Each acceptance criterion maps to one of cases 1-6; the PR body quotes the dry-run output of case 3 and the validator run.
