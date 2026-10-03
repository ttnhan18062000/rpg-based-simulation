---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [ai, process-improvement, governance]
---

# Agent-working path map (pre-move to live)

On 2026-10-03 the agent-working state moved under one `agent-working/` root. Closed history is frozen and
still cites the pre-move paths; this page says how to resolve such a citation.

| Pre-move citation starts with | Live location |
|---|---|
| `tickets/` | `agent-working/tickets/` |
| `stored_artifacts/` | `agent-working/stored_artifacts/` |
| `staging_artifacts/` | `agent-working/staging_artifacts/` |
| `agent-monitoring/` (the data folder) | `agent-working/agent-monitoring/` |
| `agent-orchestration/` | `agent-working/agent-orchestration/` |
| `pilot_requests/` | `agent-working/pilot_requests/` |
| `reviews/` | `agent-working/reviews/` |
| `agent-monitoring-index/`, `knowledge-index/`, `parity-index/` (generated, untracked) | `agent-working/.index/<name>/` |

Rule: the move is prefix-only, so a live path is the old path with `agent-working/` in front. Folders that did
not move: `registries/`, `tools/` (including `tools/agent-monitoring/`, the tool scripts), `experiments/`,
`docs/` (including `docs/agent-monitoring/`).

Frozen, still citing pre-move paths: `agent-working/tickets/done/**`, `agent-working/stored_artifacts/**`,
`docs/archive/**`, `agent-working/tickets/working_log.csv` rows, past monitoring shards.

Code never spells these roots: import the constants from `tools/agent_working_paths.py`. To resolve a
pre-move citation in code, call `resolve_legacy_citation(citation)` from the same module (pure string mapping;
a citation that does not start with a pre-move root, or already carries the new prefix, is returned unchanged).
`tests/tools/test_agent_working_paths_guard.py` fails on a hardcoded root in live Python.

## Cleaning up pre-move residue

A worktree that had files at an old root before it merged #289 can still hold them. Old-root files are never tracked
on main, so they are residue, but check before deleting:
- Index folders (`knowledge-index/`, `agent-monitoring-index/`, `parity-index/`) are generated and git-ignored at the
  old root; delete them and rebuild under `agent-working/.index/` (`make knowledge-index-update`).
- A monitoring shard left at the old path (`agent-monitoring/data/<week>/<branch>.tools.jsonl`) is NOT necessarily a
  subset of the new one: a tool can write a row before the merge that the rename does not carry. Diff the contents
  by row; append only the rows whose exact content is absent from `agent-working/agent-monitoring/data/<week>/`
  (never copy the whole file: the duplicate-run ratchet counts duplicates), then delete the old file.
- Never `git add -A` in a worktree that still has old-root residue; review `git status --porcelain` first.

`tests/tools/test_no_tracked_old_root_files.py` fails if any file is tracked under an old root. The seven
non-index old roots are deliberately not git-ignored: a file appearing there means a tool still writes the old path.
