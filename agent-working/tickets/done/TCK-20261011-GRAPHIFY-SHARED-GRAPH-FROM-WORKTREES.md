---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES
phase: done
date: 2026-10-11
tags: [ai, knowledge-store, process-improvement]
---

# TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES

## Title
`graphify query` works from every git worktree against the main checkout's graph, the graph is written only from the main checkout, and nodes for deleted files are pruned

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
GitHub issue #498 (finding from lead-planner, with three measured updates). `graphify-out/` is
gitignored, so a new worktree has no `graph.json` and `graphify query` fails with
`error: graph file not found: <worktree>/graphify-out/graph.json`. CLAUDE.md makes `graphify query` the
required second step of every investigation, so sessions in worktrees cannot follow that rule. It failed
in 8 of 11 worktrees on host ubuntu (2026-10-10) and reproduces on host u24desktop in
`.claude/worktrees/agent-working-planner` (2026-10-11). This is the graphify counterpart of the
search-MCP worktree fix in #482 (TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION).

Interim on host ubuntu only: hand-made symlinks `graphify-out -> <main checkout>/graphify-out` plus
`/graphify-out` in `.git/info/exclude`. Host u24desktop has no workaround.

Further findings on the issue:
- The graph was 527 MB / 58,687 nodes / 1.56M links; a query took 21.7 s and 1.7 GB RSS. 21% of nodes came
  from the untracked root `reviews/` dumps (now deleted with owner approval); `scratch/` and
  `experiments/` are indexed too.
- `graphify update .` and `--force` never drop nodes whose source file is gone. lead-planner pruned them by
  hand (owner-approved, 2026-10-10): 62 MB, 46,547 nodes, 110,336 links, 2.0 s / 226 MB per query.
- `.graphifyignore` is tracked but routes to no domain.
- The PostToolUse hook in `.claude/settings.json` runs `graphify update .` after any `src/`/`tests/` edit
  when `graphify-out/graph.json` exists. Through a symlink, that would write one branch's code into the
  shared graph.

## Scope
1. **Resolution from a worktree.** `graphify query|explain|path` from any worktree reads the main
   checkout's `graphify-out/graph.json` with no hand step. Preferred design: the session launcher
   (`tools/sessions/launch.py`) and SessionStart create an idempotent relative-or-absolute symlink
   `graphify-out -> <main checkout>/graphify-out` in a worktree that has no `graphify-out` of its own
   (resolve the main checkout as `tools/handover_home.py::main_checkout_root` does). Never replace a real
   `graphify-out/` directory (`rpg-perf` and `rpg-aseprite-mcp` keep their own). A wrapper/`--graph`
   design is acceptable if the plan shows it is simpler; record the choice in plan.md.
2. **Ignore the link.** Add `/graphify-out` to `.gitignore` so the symlink never shows as untracked.
3. **Writes only from the main checkout.** A worktree session never rewrites the shared graph: the edit
   hook's `graphify update .` runs only when `graphify-out` is a real directory, not a symlink. The
   shared graph is rebuilt from the main checkout (on main). Document this in CLAUDE.md's Graphify
   Integration section.
4. **Prune deleted files.** A small tool (for example `tools/graphify_prune.py`) removes nodes whose
   `source_file` no longer exists under the graph's root, plus their links, and leaves no dangling link.
   It runs after `graphify update` in the documented refresh step. It reports the counts it removed.
5. **Ignore list and owner.** Add `scratch/`, `experiments/` and `reviews/` to `.graphifyignore`.
   Give `.graphifyignore` an owner in `registries/session_roles.yaml` (agent-working, alongside the
   context tooling). Stay within the 400-token card budget; do not raise it.
6. **Size report.** The prune tool prints `graph.json` size, node and link counts, and warns above a
   threshold set in the plan (for example 150 MB). Report only; it never fails a step.

## Out of Scope
- Changes to graphify itself (the upstream CLI).
- Deleting any untracked folder in the main checkout (owner decision, already done for `reviews/`).
- A CI job that builds the graph.
- Host ubuntu's existing hand-made symlinks: the new code must accept them as they are.

## Acceptance Criteria
1. In a fresh worktree created by the launcher, `graphify query "<topic>"` returns results with no hand step.
2. A worktree that already has a real `graphify-out/` directory is left untouched; an existing symlink is accepted.
3. `git status` in a linked worktree does not list `graphify-out`.
4. Editing `src/`/`tests/` in a linked worktree does not run `graphify update` against the shared graph
   (test the hook's condition); in the main checkout it still runs.
5. The prune tool, on a fixture graph with nodes for a deleted file, removes those nodes and every link
   touching them, keeps everything else byte-identical in meaning, and is idempotent.
6. `.graphifyignore` lists `scratch/`, `experiments/` and `reviews/`; `route.py .graphifyignore` names
   agent-working; `python3 -m tools.sessions.validate` reports 0 findings.
7. The owner confirms the literal diffs of the governing files (`.claude/settings.json`, CLAUDE.md,
   `registries/session_roles.yaml`) in the batch PR.

## Related Tickets
- TCK-20261010-SEARCH-MCP-WORKTREE-VENV-RESOLUTION (#482, the search-MCP counterpart)
- TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP
- TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD (launcher, same folder)
- GitHub issue #498

## Related Docs
- CLAUDE.md ("Graphify Integration", "Context Scan")
- docs/engine/contracts/knowledge_gateway_mcp_contract.md (graphify provider)

## Related Stored Artifacts
`agent-working/stored_artifacts/TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES/{plan,investigation,test_plan}.md`

## Related Code Areas
- tools/sessions/launch.py, tools/sessions/session_start_hook.py
- tools/handover_home.py (main_checkout_root)
- .claude/settings.json (PostToolUse graphify hook)
- .gitignore, .graphifyignore
- registries/session_roles.yaml

## Assumptions / Open Questions
- Planner's design call for issue ask 2: a worktree reads the shared graph and never writes it. Branch code
  reaches the graph when it merges and the main checkout refreshes.
- The launcher edits overlap TCK-20261010-SESSION-LEASE-TAKEN-ON-LAUNCH-CWD-NOT-MANIFEST-WORKTREE and PR #491
  (`session_start_hook.py`, `launch.py`); implement after them in the batch.

## Implementation Notes
Design: symlink, not a `--graph` wrapper (plan.md). `tools/graphify_link.py::link_shared_graph` is called by `launch.py` (before exec) and the SessionStart hook; it links only when nothing exists at `graphify-out` (a real directory, any symlink, even a broken one, is left alone), the worktree is not the main checkout, and the main checkout has a `graph.json`. `/graphify-out` added to `.gitignore`. The PostToolUse hook now needs `[ ! -L graphify-out ]` before `graphify update .`, so only the main checkout refreshes the shared graph. `tools/graphify_prune.py` removes nodes whose `source_file` is gone, every link touching them and their hyperedge membership (top-level and `graph.hyperedges`; a hyperedge left under two members is dropped), writes atomically, refuses to write through a symlinked `graphify-out`, prints counts and size and warns above 150 MB, always exits 0. On a copy of the real graph (61.3 MB) a dry run reports 795 stale nodes, 888 links, 3 hyperedges. `.graphifyignore` gains `scratch/`, `experiments/`, `reviews/` and is owned by agent-working. The agent-working planner card went to 404 tokens, so two domain-text phrases were shortened (`docs/guidelines/session_roles/domains/agent-working.md`: now 380/397/386, budget 400). Governing-file diffs for the owner: `.claude/settings.json` (hook condition), `CLAUDE.md` (one Graphify Integration bullet), `registries/session_roles.yaml` (`.graphifyignore` in owns). NOT done: running the prune on the real shared graph (that rewrites a gitignored file in the main checkout; after merge, run it there) and a fresh-launch end-to-end `graphify query` from a launcher-made worktree; the link and the hook path are covered with real git worktrees instead.

## Test Summary
New tests/tools/test_graphify_link_and_prune.py (12): fresh worktree linked and idempotent; real dir / foreign / broken symlink untouched; main checkout never linked; no main graph -> no link; git status ignores the link; SessionStart wiring; the real settings.json hook command run with a fake `graphify` (not run in a linked worktree, run in the main checkout); prune removes nodes, links and hyperedge members, idempotent byte-for-byte, dry-run and symlink write nothing, size warning exit 0, clean graph unchanged; `.graphifyignore` entries and route to agent-working. Related suites: session tools + handover transit 665 passed; tests that mention settings.json/CLAUDE.md/.gitignore 1077 passed, 36 skipped. validate 0 findings (17 roles), generate_agents 0 drift.

## Files Changed
`tools/graphify_link.py`, `tools/graphify_prune.py`, `tools/sessions/launch.py`, `tools/sessions/session_start_hook.py`, `.claude/settings.json`, `.gitignore`, `.graphifyignore`, `CLAUDE.md`, `registries/session_roles.yaml`, `docs/guidelines/session_roles/domains/agent-working.md`, regenerated `.claude/agents/*`, `tests/tools/test_graphify_link_and_prune.py`.

## Completion Summary
Worktrees read the main checkout's graph through a link made by the launcher and SessionStart, only the main checkout writes it, a prune tool drops stale nodes, and `.graphifyignore` has an owner.
