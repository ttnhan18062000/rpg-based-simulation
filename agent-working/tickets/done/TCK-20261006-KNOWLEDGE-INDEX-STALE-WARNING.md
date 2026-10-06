---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING
phase: done
date: 2026-10-06
tags: [ai, knowledge-store, process-improvement]
---

# TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING

## Title
A knowledge search says when its worktree's index is stale

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P3

## Request Summary
`TCK-20261004-WORKTREE-INDEX-DUPLICATION` (PR #316) left AC2 only partly met. A worktree now searches its own
repo-anchored index, but nothing says when that index no longer matches the worktree's docs and tickets. A
worktree on another branch, or one whose docs changed since the last `make knowledge-index-update`, silently gets
results from an older corpus. The owner chose on 2026-10-06 to close the parent and file this gap separately.

## Scope
- At query time, compare `manifest.json` (source path → mtime, written by `_write_manifest`) with the current
  corpus. Use the same file walk as `cmd_build_incremental` and stat only, with no embedding and no file reads.
  Count changed, new and removed files.
- When any count is above zero, the CLI `query` prints one stderr line: counts plus `run make knowledge-index-update`.
  MCP `search_docs` adds a `stale` field to its result (`{"changed": n, "new": n, "removed": n}`, or absent when
  current). Results are still returned; the warning does not block.
- Share one helper between `tools/knowledge_search.py` and `tools/search_mcp.py`, so the two paths cannot disagree
  (the same reason the parent anchored both to one index path).

## Out of Scope
- Rebuilding automatically, and changing how the index is built or where it lives (the owner decided on
  2026-10-04 that per-worktree indexes stay).
- The "index not found" case. It already has its own message.
- The monitoring index and the parity index.

## Acceptance Criteria
1. With an index built and one corpus file touched afterwards, CLI `query` prints a stale line naming 1 changed
   file, and MCP `_run_search` returns results plus `stale.changed == 1`.
2. With a file added and another removed, `new` and `removed` are each counted as 1.
3. With a current index, there is no stale line and no `stale` field.
4. The check adds under 200 ms for the real corpus on a warm cache. Measure and record the number in the ticket.
5. A missing or unreadable `manifest.json` reports "staleness unknown" and does not raise.
6. Scoped tests are green (`tests/tools/test_knowledge_search.py` excluding the known timing tests,
   `tests/tools/test_search_mcp.py`). The search section of `docs/guidelines/agent_working_environment.md` says
   what the warning means.

## Related Tickets
- `TCK-20261004-WORKTREE-INDEX-DUPLICATION` (parent; AC2 gap, closed alongside this one being filed)

## Related Docs
- `docs/guidelines/agent_working_environment.md`

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/knowledge_search.py` (`_write_manifest`, `_load_manifest`, `cmd_build_incremental`, `cmd_query`)
- `tools/search_mcp.py` (`_ensure_loaded`, `_run_search`)

## Assumptions / Open Questions
- mtime is good enough. Incremental build already trusts it, and a branch switch rewrites the mtimes of the
  files it changes.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06.

## Test Summary
`tests/tools/test_knowledge_index_staleness.py` (14 pass): a touched file is 1 changed, an added and a removed file are counted apart, a docs/archive file never counts, the stat walk covers exactly the paths a build indexed, a current index is silent, a missing, unparseable or malformed manifest is `unknown` and never raises, CLI `query` prints one stale line, MCP `_run_search(with_staleness=True)` returns results plus `stale`, a current index and a call without the flag return the bare list, an error dict is never wrapped. `test_search_mcp.py` and `test_knowledge_search.py` stay green (108 pass, 35 skipped for missing embedding packages). AC4: measured against a real built index (another worktree's, 4,630 corpus files, warm cache): 80-95 ms, after replacing `Path.glob` with `os.scandir` (the first version took about 220 ms).

## Files Changed
- `tools/knowledge_search.py` (`_iter_doc_files` shared with the build, `_corpus_source_paths`, `index_staleness`, `stale_warning`, `cmd_query`)
- `tools/search_mcp.py` (`_run_search(with_staleness=)`, `search_docs` passes it)
- `tests/tools/test_knowledge_index_staleness.py` (new)
- `docs/guidelines/agent_working_environment.md`

## Completion Summary
Closed 2026-10-06. All six acceptance criteria met; AC4 measured at 80-95 ms warm. One shape choice: `_run_search` returns a bare list, so `stale` rides in `{"results": [...], "stale": {...}}` only when the index is stale or unknown and only when `search_docs` asks (`with_staleness=True`); a current index still returns the bare list, so existing callers are unaffected. A file that yields no document (empty body, a ticket with no Request Summary) can count as `new` indefinitely. Not done: auto-rebuild, the monitoring and parity indexes (out of scope).
