---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261009-PR-RENDER-RAW-PROBE-OUTPUT-ADVISORY
phase: done
date: 2026-10-09
tags: [delivery, data-quality]
---

# TCK-20261009-PR-RENDER-RAW-PROBE-OUTPUT-ADVISORY

## Title
pr_render warns when a PR adds raw probe output under stored_artifacts/**/probes/ above a size threshold

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P3

## Request Summary
Measured on origin/main on 2026-10-09: `agent-working/stored_artifacts/**/probes/` holds 414 files (5.3 MB) across 32
tickets, about 11% of all stored_artifacts. Most of it is raw run output: 61 `.jsonl` files total 4.2 MB, plus about
0.5 MB of `.out`/`.json`/`.gz`. PR #457 alone added about 590 KB more. The rpg domain agreed (2026-10-09, rpg-planner) on
a rule: commit probe scripts plus summary tables, and no raw per-run output unless a ticket cites it. It is pruning
what is already on main, and it asked agent-working for a NON-BLOCKING size check, so that the rule does not depend on
memory alone.

## Scope
- `tools/delivery/pr_render.py` computes, from the PR's changed files (`discover_changed_files`, added or modified
  against the base ref), the raw probe files under `agent-working/stored_artifacts/**/probes/`. A file counts as raw
  output when its extension is not one of `.py`, `.sh`, `.md`, `.txt`. Sizes come from the working tree.
- When their total is above the threshold (a named constant, 200 KB to start; state it in the code comment), the
  rendered body gets one warning in the existing discovery-warnings line. The warning gives the count, the total size
  and up to 5 of the largest paths, and says: "raw probe output: keep only files a ticket cites; summarize the rest in
  investigation.md".
- Report only: no exit code, title or lint change. `pr_body_lint` does not start requiring anything.
- Tests: below the threshold gives no warning; above it gives exactly one warning with count, size and the top paths;
  scripts and summaries never count; a probe file outside `stored_artifacts` is ignored.

## Out of Scope
- Pruning existing files (the rpg domain's cleanup PR).
- Checking whether a raw file is cited. The warning asks the author to check; parsing citations is a later step if the
  warning proves noisy.
- A blocking gate, or a CI job.

## Acceptance Criteria
1. A PR adding more than 200 KB of raw probe output renders one warning naming the count, the size and the largest paths.
2. A PR adding only probe scripts or summaries, or less than the threshold, renders no such warning.
3. pr_render's exit behavior and existing output are unchanged otherwise. Existing pr_render tests pass.

## Related Tickets
- PR #428 (pr_render records exclusions on the ticketless path; same discovery-warnings channel)

## Related Docs
- docs/guides/delivery_process.md ("PR Lifecycle"): add one line naming the advisory.

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- tools/delivery/pr_render.py (`discover_changed_files`, `_render_section` warnings)
- tests/tools/ (pr_render tests)

## Assumptions / Open Questions
- PR #457 (rpg-batch-d36-d32) would trip it at about 590 KB; that is the intended first catch.
- `search_docs` index not built, graphify graph missing in this worktree: the duplicate scan used the ticket folders
  and grep. No open ticket covers this.

## Implementation Notes
Requested by rpg-planner 2026-10-09 in reply to agent-working-planner's probe-prune request (owner's ask).
Hand-orchestrated hotfix on `agent-working-small-fixes-batch`, with no PR of its own.

## Test Summary
tests/tools/test_delivery_pr_render.py: 67 passed, 5 new (above the 200 KB threshold: one warning with count, size and the 5 largest paths; at the threshold: none; `.py`/`.sh`/`.md`/`.txt` in `probes/`, a raw file outside `probes/`, and a deleted file never count; `render()` adds exactly one warning to the discovery-warnings line and leaves the title unchanged). `test_agent_working_paths_guard.py` passes (11 tests with the others: 78 passed).

## Files Changed
- tools/delivery/pr_render.py
- tests/tools/test_delivery_pr_render.py
- docs/guides/delivery_process.md

## Completion Summary
`pr_render.raw_probe_warning(files)` (threshold `RAW_PROBE_WARN_BYTES` = 200 KB, stated in the code comment) adds one non-blocking warning to the discovery warnings, for both the ticket and the ticketless render, when the PR's changed files include more than that in raw output under `agent-working/stored_artifacts/**/probes/`. It names the count, the total size and up to the 5 largest paths. No exit code, title or lint change. One line in delivery_process.md's PR Lifecycle names the advisory. Citation checking and pruning stay out of scope.
