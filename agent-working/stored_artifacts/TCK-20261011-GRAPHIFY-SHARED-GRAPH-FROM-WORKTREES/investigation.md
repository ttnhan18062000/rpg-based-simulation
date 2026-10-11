---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES
artifact_type: investigation
tags: [ai, knowledge-store, process-improvement]
---

# investigation — TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES

## Findings
- `graphify query|explain|path` read `./graphify-out/graph.json`; `graphify-out/*` is gitignored, so a fresh worktree has none. The main checkout is `git rev-parse --git-common-dir`'s parent (`tools/handover_home.py::main_checkout_root`).
- The shared graph (61 MB, 42,208 nodes, 120,788 links) is indent=2 JSON with keys `directed, multigraph, graph, nodes, links, hyperedges, built_at_commit`. Nodes carry `source_file` (repo-relative) and `id`; links carry `source`, `target` (node ids) and their own `source_file`; hyperedges (top-level and under `graph.hyperedges`) list member node ids.
- The only write path in the repo is the PostToolUse hook (`.claude/settings.json`): `[ -f graphify-out/graph.json ] && graphify update .` after any `src/` or `tests/` edit. Through a symlink it would write a branch's code into the shared graph.
- `.gitignore` has `graphify-out/*` (matches the directory's contents, not a symlink named `graphify-out`), so a symlink shows as untracked unless `/graphify-out` is added.
- `.graphifyignore` exists, tracked, and routes to no domain.
- The launcher already resolves the role worktree (`launch.py default_worktree_path`) and SessionStart already knows the session's physical worktree; both can call one helper.
## Constraints
Never replace a real `graphify-out/` directory (`rpg-perf`, `rpg-aseprite-mcp`); accept existing symlinks (host ubuntu); worktrees never write the shared graph; cards stay within 400 tokens.
