---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-WORKTREE-INDEX-DUPLICATION
artifact_type: plan
tags: [ai, process-improvement]
---

# Plan: prune idle worktree indexes, anchor the index path

Owner chose on 2026-10-04: per-worktree indexes stay, add a prune step, no shared index (no staleness risk). Shipped in #316:
1. `tools/prune_worktree_indexes.py`: dry run by default, `--apply` deletes; skips the current worktree, the main checkout and the parity index.
2. Anchor `_DEFAULT_DB` in `tools/knowledge_search.py` and `tools/retrieval_cache.py` to the repo root so MCP and CLI resolve one index.
3. Document the prune step in `docs/guidelines/agent_working_environment.md`.

Not done: a stale-index warning (AC2). Tracked by `TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING`.
