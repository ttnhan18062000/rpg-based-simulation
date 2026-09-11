---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260910-HOTFIX-WRITE-PATH-GUARD-STALE-ARCHIVE-COMMENTS
phase: done
date: 2026-09-10
tags: [mcp, documentation]
---

# TCK-20260910-HOTFIX-WRITE-PATH-GUARD-STALE-ARCHIVE-COMMENTS

## Title
Fix two comments in `write_path_guard.py` that describe deleted files as archived

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`tools/write_path_guard.py` carries two comments asserting that certain predicates "stayed behind
in the archived `tools/archive/knowledge_gateway_redaction.py`." That file was archived by
`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`, then **hard-deleted** by
`TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`. The comments now point a reader at a path that does
not exist anywhere in the repo.

Exact locations, verified against `origin/main` on 2026-09-10:
- `tools/write_path_guard.py:22`
- `tools/write_path_guard.py:297`

A repo-wide `git grep "tools/archive"` across `tools/`, `src/`, and `.claude/` returns only these
two — `tools/retrieval_cache.py` is clean.

## Scope
- Reword both comments so they describe the symbols as *removed* rather than as living at an
  archived path, while preserving the useful historical fact (that those predicates were part of
  the original module and deliberately not carried into `write_path_guard.py`). Cite the deleting
  ticket so the trail stays followable.

## Out of Scope
- The four nearby comments at `tools/write_path_guard.py:11, :15, :17, :23`, which say "archived"
  without naming a path. They are imprecise but not inaccurate — leave them; rewriting correct
  prose is scope creep.
- Any behavior change. This is comment text only — `scan_for_secrets()` and every other symbol in
  the module stay byte-identical, including the pattern set.
- `tools/write_path_guard.py:61`'s reference to `kgmcp_phase2_baseline_recomparison_results.json`
  — that fixture still exists today and is handled by
  `TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL`; if that ticket lands first, this comment
  becomes stale too and should be swept then, not pre-emptively here.

## Acceptance Criteria
- [x] Neither `:22` nor `:297` asserts the existence of a `tools/archive/` path.
- [x] Both retain the historical explanation of why those predicates are absent from this module,
      with the deleting ticket cited.
- [x] `git grep "tools/archive" tools/ src/ .claude/` returns nothing.
- [x] `tests/tools/test_write_path_guard.py` still passes 54/54 — no behavior touched.

## Related Tickets
- `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (done) — wrote the comments, accurate at the time.
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (done) — deleted the referenced file, making them
  stale.

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- `tools/write_path_guard.py`

## Assumptions / Open Questions
None — both locations confirmed directly and the fix is textual.

## Implementation Notes
Reworded both comments (`:22`, now `:19-22` after the edit shifted lines; `:297`, now similarly
shifted) from "stayed behind in the archived `tools/archive/knowledge_gateway_redaction.py`" to
"were deliberately not carried into this module ... hard-deleted by
`TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`" — preserves the historical fact (why those symbols
are absent here) without asserting a path that no longer exists. Left the 4 nearby "archived"
comments untouched per Out of Scope (imprecise but not inaccurate). Left `:61`'s
`kgmcp_phase2_baseline_recomparison_results.json` reference untouched per Out of Scope — that
fixture still exists; handled by `TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL` if/when that
ticket lands.

## Test Summary
- `git grep "tools/archive" tools/ src/ .claude/` — no matches (AC).
- `pytest tests/tools/test_write_path_guard.py -q` — 54/54 pass, unchanged.
- Doc-staleness gate: `PASS` (`behavior_changed=False, 0 src/config/workflow path(s) flagged, 0
  docs/ path(s) present`).

## Files Changed
- `tools/write_path_guard.py` (2 comment edits, no behavior change)

## Completion Summary
Fixed two stale comments in `tools/write_path_guard.py` that described predicates as "living" in
`tools/archive/knowledge_gateway_redaction.py` — a path `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`
hard-deleted. Reworded to describe the predicates as deliberately not carried into this module,
citing the deleting ticket, with zero behavior change (`scan_for_secrets()` and every other symbol
stay byte-identical).
