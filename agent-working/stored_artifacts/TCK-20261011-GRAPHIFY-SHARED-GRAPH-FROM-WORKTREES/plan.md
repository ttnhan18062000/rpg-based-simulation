---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES
artifact_type: plan
tags: [ai, knowledge-store, process-improvement]
---

# plan — TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES

## Design choice
Symlink, not a `--graph` wrapper: `graphify` has no stable flag we own, and a link also makes `GRAPH_REPORT.md` and the cache visible to every existing hook and doc that says `graphify-out/`. Recorded per scope item 1.
## Changes
1. `tools/graphify_link.py` (stdlib only): `link_shared_graph(worktree)` creates absolute symlink `<worktree>/graphify-out -> <main checkout>/graphify-out` only when the worktree is not the main checkout, nothing exists at that name (`lexists`, so a broken link counts as existing), and the main checkout has a `graphify-out/graph.json`. Returns a status string; never raises.
2. Called from `launch.py` (after the worktree exists, before exec, also in the self-heal path's normal flow) and `session_start_hook.py` (for the session's physical worktree; one short note only when a link was made).
3. `.gitignore`: add `/graphify-out`.
4. `.claude/settings.json` PostToolUse graphify hook: add `[ ! -L graphify-out ] &&` so only a real directory (the main checkout) runs `graphify update .`.
5. `tools/graphify_prune.py`: `--graph` (default `graphify-out/graph.json`), `--root` (default the graph directory's parent), `--dry-run`, `--warn-mb` (default 150). Removes nodes whose string `source_file` no longer exists under root, every link touching a removed id, and removed ids from hyperedge member lists (top-level and `graph.hyperedges`; a hyperedge left with fewer than 2 members is dropped). Writes atomically (temp file + `os.replace`) with the file's indent=2 style, only when something is removed and the graph path is not reached through a symlinked `graphify-out` (worktrees never write). Prints counts removed, graph size, node and link counts, and warns above the threshold; always exits 0 on report-only conditions.
6. `.graphifyignore`: add `scratch/`, `experiments/`, `reviews/`. `registries/session_roles.yaml`: `.graphifyignore` into agent-working `owns`; compact other globs if the card exceeds 400 tokens.
7. CLAUDE.md Graphify Integration: worktrees read the shared graph through the link, never write it; refresh from the main checkout with `graphify update .` then `python3 tools/graphify_prune.py`.
## Out of scope
Upstream graphify, deleting untracked folders, CI graph build.
