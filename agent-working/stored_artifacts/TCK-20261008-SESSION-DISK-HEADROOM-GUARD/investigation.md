---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261008-SESSION-DISK-HEADROOM-GUARD
artifact_type: investigation
tags: [workflows, setup]
---

# Investigation

- 2026-10-08: the data disk (49 GB) hit 100%. About 15 GB was `data/runs/` across ~50 worktrees and ~25 GB worktrees of merged branches; no session noticed until a write failed.
- Seams: `launch.py::main` (prints notes before building the command), `session_start_hook.py::build_context` (fails open in `main`), `prune_branches.py` (separate ticket).
- Measured: a du-style walk of ~47 worktrees on this disk takes tens of seconds, so the launcher and hook read free space with one `statvfs` and walk only below the threshold. After cleanup the live helper reports 22 GB free, 47 worktrees, 43 GB, run data 2.7 GB.
- Sizes use `st_blocks * 512` (what `du` reports) so the numbers agree with `du`/`df`.
- The 10 GB default stays as proposed (about 10 batches of about 1 GB; 20% of this disk); `SESSION_DISK_THRESHOLD_GB` overrides it.
