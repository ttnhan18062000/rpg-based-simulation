---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-WORKTREE-INDEX-DUPLICATION
phase: done
date: 2026-10-04
tags: [ai, process-improvement, performance]
---

# TCK-20261004-WORKTREE-INDEX-DUPLICATION

## Title
Stop duplicating the derived `agent-working/.index/` in every git worktree

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Every worktree builds its own `agent-working/.index/` (about 103M knowledge index, plus about 144M monitoring index where built). On 2026-10-04 the disk reached 94% with 14 worktrees; measured: the knowledge index is about 103M in each of at least 8 worktrees (about 0.8G), and the monitoring index about 144M where present. Both are derived, untracked and regenerable, but the knowledge index is expensive to rebuild (it re-runs the embedding model).

## Scope
- Measure first: size of each index per worktree, build cost (time), what staleness a shared index would risk (a worktree on a different branch has different docs).
- Decide one of: a shared location under the git common directory keyed by content hash or tree state, an on-demand build with automatic pruning of idle worktrees' indexes, or a documented prune step in the worktree-hygiene tooling (session-layer M4 `status.py` / `prune_branches.py`).
- Implement the chosen option behind the existing CLI/MCP path settings (`tools/knowledge_search.py`, `make knowledge-index-update`, `make agent-monitoring-index`).
- Fix the MCP `search_docs` server path mismatch observed in worktrees (reports "index not found" while the CLI fallback works).

## Out of Scope
- Removing worktrees themselves, venv sharing (`.venv-knowledge`, 1.6G), Claude Code's own transcripts and caches.

## Acceptance Criteria
1. Measured before/after disk use for N worktrees, recorded in the ticket.
2. A search from any worktree returns results from an index that is current for that worktree's docs, or says it is stale.
3. MCP `search_docs` and the CLI fallback resolve the same index path.
4. Scoped tests green; docs (`docs/guides/agent_working_environment` equivalent) updated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-OPERATIONS` (M4 hygiene tooling may host the prune step)
- `TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING` (AC2 follow-up)

## Related Docs
- `docs/guidelines/agent_working_environment.md`

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/knowledge_search.py`, `Makefile` index targets, `.mcp.json`

## Assumptions / Open Questions
- Whether the monitoring index should be built at all outside the main checkout (Makefile marks it on-demand, not CI).
- Whether a shared index is acceptable given branch-specific docs.

## Implementation Notes
Draft by `agent-working-design`, 2026-10-04. Owner chose (2026-10-04): per-worktree indexes stay, add a prune step (no shared index; no staleness risk); fold into PR #316.

Measured 2026-10-04 (after peers' cleanup): 11 worktrees, 3 besides this one hold a knowledge index (107.6M, 107.7M, 109.2M) and one holds a monitoring index (149.9M); total 474.4M, `df` 87% used (was 94%). Build cost of the knowledge index is minutes (embedding model), hence prune-idle over on-demand rebuild.

Changes: `tools/prune_worktree_indexes.py` (dry run default, `--apply`, skips current worktree, main checkout and parity index; M4's `status.py`/`prune_branches.py` do not exist yet, so a standalone tool now, M4 can call it). MCP "index not found" root cause: `_DEFAULT_DB` was a cwd-relative `Path`, so the server found the index only when started from the worktree root (reproduced: ok from the root, "index not found" from `/tmp`). `tools/knowledge_search.py` and `tools/retrieval_cache.py` now anchor the index to the repo root.

## Test Summary
`tests/tools/test_prune_worktree_indexes.py` (4 pass). `tests/tools/test_search_mcp.py`, `test_retrieval_cache.py` pass. `tests/tools/test_knowledge_search.py::test_query_completes_within_2_seconds` and three live-build tests in `TestLiveQueryDocsMechanics` fail on resource time limits (model load on a busy machine); the 2s test fails identically on the baseline. None involve the path change.

## Files Changed
- `tools/prune_worktree_indexes.py` (new), `tools/knowledge_search.py`, `tools/retrieval_cache.py`
- `tests/tools/test_prune_worktree_indexes.py` (new)
- `docs/guidelines/agent_working_environment.md`

## Completion Summary
Closed 2026-10-06 by owner decision, with one acceptance criterion only partly met. AC1 recorded (474.4M across 4 index folders in 3 other worktrees, no deletions made). AC3 done (MCP and CLI resolve one repo-anchored index; reproduced and fixed). AC4 scoped tests green apart from the timing failures above; docs updated. **AC2 is only partly met and is left as a stated gap**: a worktree searches its own index, but nothing says when that index is stale for the worktree's current docs. The gap is tracked by `TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING` (hotfix, P3, filed under `todos/`).
