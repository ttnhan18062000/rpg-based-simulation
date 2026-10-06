---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-WORKTREE-INDEX-DUPLICATION
artifact_type: investigation
tags: [ai, process-improvement]
---

# Investigation: index duplication and the MCP path mismatch

Measured 2026-10-04 after peers' cleanup: 11 worktrees, 3 besides the current one hold a knowledge index (107.6M, 107.7M, 109.2M) and one holds a monitoring index (149.9M); 474.4M total, disk 87% used (94% before). Build cost of the knowledge index is minutes (embedding model), so pruning idle indexes beats on-demand rebuild.

MCP "index not found": `_DEFAULT_DB` was a cwd-relative `Path`, so the server found the index only when started from the worktree root (ok from the root, "index not found" from `/tmp`).
