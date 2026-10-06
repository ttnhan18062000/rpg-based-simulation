---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-WORKTREE-INDEX-DUPLICATION
artifact_type: test_plan
tags: [ai, process-improvement]
---

# Test plan

- `tests/tools/test_prune_worktree_indexes.py`: dry run deletes nothing, `--apply` deletes idle indexes, current worktree and main checkout are skipped, parity index is kept (4 pass).
- `tests/tools/test_search_mcp.py` and `test_retrieval_cache.py`: pass with the repo-anchored path.
- Known timing failures on a busy machine, unrelated to the path change: `test_knowledge_search.py::test_query_completes_within_2_seconds` (fails identically on the baseline) and three live-build tests in `TestLiveQueryDocsMechanics`.
- Not covered: stale-index detection (follow-up ticket).
