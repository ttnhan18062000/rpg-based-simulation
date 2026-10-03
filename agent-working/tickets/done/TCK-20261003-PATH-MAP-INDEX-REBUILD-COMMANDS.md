---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261003-PATH-MAP-INDEX-REBUILD-COMMANDS
phase: done
date: 2026-10-03
tags: [ai, documentation]
---

# TCK-20261003-PATH-MAP-INDEX-REBUILD-COMMANDS

## Title
Name the agent-monitoring and parity index rebuild commands in the path map's pre-move residue cleanup section

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Throwaway AC9 dry run for TCK-20261003-AGENT-WORKING-ROOT-MOVE: the ticket exists to prove the implement-ticket hotfix pipeline completes with monitoring records written at the new `agent-working/` location. The content change: in `docs/guides/agent_working_path_map.md`, "Cleaning up pre-move residue", the index-folders bullet names only `make knowledge-index-update`. It should also state that `make agent-monitoring-index` and `python3 tools/parity_index.py build` rebuild the other two index folders under `agent-working/.index/`. Both commands were verified to exist: `Makefile` target `agent-monitoring-index` (line 469) and `parity-index` target invoking `python3 tools/parity_index.py build` (line 474); `.gitignore` lines 280-283 name the same commands. No registry verdict is quoted as premise.

## Scope
- Edit only the index-folders bullet in the "Cleaning up pre-move residue" section of `docs/guides/agent_working_path_map.md`, to map each index folder to its rebuild command.

## Out of Scope
- Any `src/` or `tools/` change; Makefile or `.gitignore` edits.
- Other sections of the path map; the monitoring-shard and `git add -A` bullets.
- Adding or changing tests.

## Acceptance Criteria
- [x] The index-folders bullet contains the literal strings `make agent-monitoring-index` and `python3 tools/parity_index.py build`.
- [x] The bullet still contains `make knowledge-index-update` and still says the folders rebuild under `agent-working/.index/`.
- [x] `git diff --stat` shows only `docs/guides/agent_working_path_map.md` (plus monitoring shards and regenerated `docs/REGISTRY.yaml`) changed; no `src/` files.
- `python3 tools/validate_frontmatter.py` passes for the edited doc and this ticket.
- The hotfix pipeline's run and event records exist under `agent-working/agent-monitoring/data/`.

## Related Tickets
- TCK-20261003-AGENT-WORKING-ROOT-MOVE (parent; this dry run verifies it)
- TCK-20261003-OLD-ROOT-RESIDUE-GUARD (done; wrote the section being edited)

## Related Docs
- docs/guides/agent_working_path_map.md

## Related Stored Artifacts
- None.

## Related Code Areas
- docs/guides/agent_working_path_map.md
- Makefile (read-only reference)
- tools/parity_index.py (read-only reference)

## Assumptions / Open Questions
- Layer `ai` and tags `ai`, `documentation` are registered; chosen as the agent-system docs fit.
- Throwaway dry run: the doc edit is real but low value; the ticket's main purpose is pipeline verification.
- No parity ledger entry or Mechanics Bible law covers this guide (grep of docs/parity_ledger found none).

## Implementation Notes
Rewrote the index-folders bullet in "Cleaning up pre-move residue" of `docs/guides/agent_working_path_map.md` to map each index folder to its rebuild command: `make knowledge-index-update`, `make agent-monitoring-index`, `python3 tools/parity_index.py build`. Wording still says the folders rebuild under `agent-working/.index/`. No deviations.

## Test Summary
Docs-only change; no tests added. Scoped run (tests/tools/test_agent_working_paths_guard.py, tests/tools/test_no_tracked_old_root_files.py, tests/docs): 83 passed, 1 skipped, 1 xfailed, 0 failed. Frontmatter validated by done_checker at Verify.

## Files Changed
- docs/guides/agent_working_path_map.md
- agent-working/tickets/inprogress/TCK-20261003-PATH-MAP-INDEX-REBUILD-COMMANDS.md

## Completion Summary
The index-folders bullet in the path map's pre-move residue cleanup section now names all three rebuild commands, one per index folder, while keeping the `agent-working/.index/` statement. Docs-only; no src/tools/Makefile changes.
