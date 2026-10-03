---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261003-OLD-ROOT-RESIDUE-GUARD
phase: done
date: 2026-10-03
tags: [ai, governance]
---

# TCK-20261003-OLD-ROOT-RESIDUE-GUARD

## Title
Ignore pre-move index residue at the old roots and guard against tracking anything under an old root

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
#289 rewrote the three generated-index `.gitignore` rules to `agent-working/.index/<name>/`. A worktree that built an index before the move still holds `knowledge-index/`, `agent-monitoring-index/`, `parity-index/` at the old root, untracked and unignored, so `git add -A` would commit them (~107 MB seen in one worktree). Origin/main tracks 0 files under those roots.

## Scope
- `.gitignore`: three root-anchored ignore rules for the old index roots.
- Guard test: `git ls-files` shows nothing under any old root (positive control included).
- `docs/guides/agent_working_path_map.md`: "Cleaning up pre-move residue" section.

## Out of Scope
Ignoring the seven old non-index roots: a file there means a tool still writes the old path and must stay loud.

## Acceptance Criteria
1. `git check-ignore -v knowledge-index/x` (and the other two) matches the new rules.
2. The guard test passes on the tree and fails on a seeded fixture with a file at `tickets/x.md`.
3. The path-map doc has the cleanup section, including the by-row shard-diff rule.

## Related Tickets
TCK-20261003-AGENT-WORKING-ROOT-MOVE

## Related Docs
docs/guides/agent_working_path_map.md

## Related Stored Artifacts
(none)

## Related Code Areas
.gitignore, tests/tools/

## Assumptions / Open Questions
Drafted by agent-working-design from a report by rpg-feature-planning; claims re-verified against origin/main 243e798ad (ignore rules rewritten, 0 tracked files at old index roots).

## Implementation Notes
Guard test reuses `LEGACY_ROOT_NAMES` / `LEGACY_INDEX_NAMES` from `tools/agent_working_paths.py`; matches the leading path component only, so `tools/agent-monitoring/` and `docs/agent-monitoring/` are not flagged.

## Test Summary
tests/tools/test_no_tracked_old_root_files.py: 2 passed (tree clean + seeded-fixture positive control). `git check-ignore -v knowledge-index/x` matches the new rule.

## Files Changed
.gitignore, tests/tools/test_no_tracked_old_root_files.py, docs/guides/agent_working_path_map.md

## Completion Summary
Three root-anchored ignore rules for the old index roots, a guard test over `git ls-files`, and a residue-cleanup section in the path map. The seven non-index old roots stay un-ignored on purpose.
