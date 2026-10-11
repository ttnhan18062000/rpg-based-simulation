---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES
artifact_type: test_plan
tags: [ai, knowledge-store, process-improvement]
---

# test_plan — TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES

## Cases
- link helper: fresh worktree gets a link resolving to the main graph; real directory untouched; existing symlink (even to elsewhere) untouched; broken symlink untouched; main checkout never linked; no main graph -> no link; idempotent.
- hook condition: the command string from `.claude/settings.json` run in a tmp dir with a fake `graphify` on PATH: not run when `graphify-out` is a symlink, run when it is a real directory with `graph.json`, not run for a non-src path.
- prune: fixture graph with nodes for a deleted file removes those nodes, every link touching them and their hyperedge membership; everything else equal; second run removes nothing and leaves bytes identical; dry-run writes nothing; a symlinked graph path is not written; size warning above threshold, never a failing exit.
- `.graphifyignore` lists the three folders; `route.py .graphifyignore` names agent-working; validate 0 findings; cards within budget; `git check-ignore` covers a symlink named graphify-out.
- launcher/hook integration: SessionStart in a linked worktree creates the link (real git worktree, tmp main checkout with a stub graph).

## Proof Plan
- level: unit/integration over real git worktrees (tmp repos)
- proof kind: behavioural tests plus a dry run on a copy of the real graph
- oracle source: the ticket's acceptance criteria 1-6 and the shipped `.claude/settings.json` hook command text
- expected effect: linked worktrees resolve the main graph; the edit hook skips symlinked `graphify-out`; prune removes only stale nodes and their links, idempotently
- selected commands: `python -m pytest -q tests/tools/test_graphify_link_and_prune.py tests/tools/test_session_*.py`; `python3 -m tools.sessions.validate`; `python3 tools/graphify_prune.py --graph <copy> --root <main> --dry-run`
