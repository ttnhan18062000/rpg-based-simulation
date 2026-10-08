---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE
artifact_type: investigation
tags: [delivery, workflows]
---

# Investigation

- 2026-10-08 disk incident: a one-off script removed 24 merged worktrees (about 12 GB); six were refused by git because the "ignore monitoring shards" filter had hidden uncommitted files. Branch mode of `prune_branches.py` skips every checked-out branch, which is exactly the merged-worktree case.
- Reused: `PrData`/`fetch_prs`, `_git`, `worktree_entries` (launch.py), `state.read_lease`/`read_instance`/`liveness`, roster `worktree` fields.
- Found while testing: `git status --porcelain` collapses an untracked directory to `dir/`, which would hide a shard's file name; the status call uses `--untracked-files=all`.
- Live dry run (47 worktrees): 3 removable (1.7 GB), 44 kept: main checkout, 8+ detached HEADs, seats, leases, dirty (shards and a `zprobes/` dir named), unmerged, open PR. Nothing was executed (owner-run action).
- `python3 tools/sessions/prune_branches.py` run as a script fails on `import tools` (pre-existing); the documented form is `python3 -m tools.sessions.prune_branches`.
