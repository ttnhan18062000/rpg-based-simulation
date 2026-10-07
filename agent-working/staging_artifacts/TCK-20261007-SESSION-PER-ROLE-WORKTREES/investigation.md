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

# Investigation

- Manifest: 12 roles, 4 worktrees (`rpg`, `agent-working`, `testing`, `codebase`), each writer an implementer; designers and planners share the implementer's worktree (`registries/session_roles.yaml` 200-203).
- `validate.py::_check_worktrees` (l.140-156): writer must be an implementer (`writer-not-implementer`) and placed in that worktree. This is the only implementer-specific check.
- `launch.py::ensure_worktree` (l.155-183): missing worktree + no recorded branch -> prints "create the worktree yourself", never creates. `main` (l.345+) has no `--branch`. `default_worktree_path` uses `role.worktree`, so a per-role worktree name flows through unchanged.
- `session_start_hook.py` l.147: lease taken iff `wt.writer == role.role and instance_id == role.role`, so it already works once the manifest names the designer as its own worktree's writer.
- Guard: the writer-lease deny keys on the worktree's lease holder; with distinct worktrees no lease conflict arises between roles.
- Knowledge index is missing in this worktree (`search_docs` "index not found"); graphify graph also absent; findings above come from direct reads after those two tools returned nothing.
- Risk: governing-file edit (`session_roles.yaml`): owner confirms the diff first. Card token cap (400) with a longer worktree name.
