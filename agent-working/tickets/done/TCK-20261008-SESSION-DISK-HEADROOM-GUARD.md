---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261008-SESSION-DISK-HEADROOM-GUARD
phase: done
date: 2026-10-08
tags: [workflows, setup]
---

# TCK-20261008-SESSION-DISK-HEADROOM-GUARD

## Title
Sessions see the disk filling before it fills: headroom check and a per-worktree run-data report

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
On 2026-10-08, /mnt/data (49 GB) reached 100% (48 KB free) in the middle of a working day. Measurement batches failed with ENOSPC, worktree creation failed, and monitoring records were torn. About 15 GB was `data/runs/` output spread over about 50 worktrees, and about 25 GB more was worktrees of already-merged branches. No session saw the problem coming. Each found out only when a write failed, and cleanup then took a full message round across all sessions.

## Scope
- A small read-only helper (e.g. `tools/sessions/disk_headroom.py`) that reports free space on the repo's filesystem, `data/runs/` + `reports/release_proof/` size per worktree, and total worktree size. One call, with text and `--json` output.
- `launch.py` prints a warning line when free space is below a threshold (default 10 GB, configurable) and names the largest `data/runs` holders. It warns only; it never refuses.
- The SessionStart hook adds one line of context when free space is below the threshold, so every session knows before it starts a measurement batch.
- A docs line in docs/guides/agent_session_reset_boundaries.md (or the delivery guide): before a batch of N measurement runs, check headroom; after the numbers are stored, clean that batch's own run dirs with `done_checker_static.py --clean-data-runs`.

## Out of Scope
Deleting anything automatically. Removing merged worktrees (TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE). Changing where simulations write.

## Acceptance Criteria
1. The helper output matches `df` and `du` on a temp-dir fixture; `--json` is stable.
2. The launcher warns below the threshold and stays silent above it (tested with a mocked free-space value); it never changes exit code.
3. The SessionStart hook line appears only below the threshold; hook failure never blocks a session.
4. Scoped tests under tests/tools pass.

## Related Tickets
TCK-20261008-MONITORING-SHARD-TORN-WRITE-ON-DISK-FULL, TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE

## Related Docs
docs/guides/agent_session_reset_boundaries.md, CLAUDE.md "After Work" (data-runs cleanup by run id)

## Related Stored Artifacts
agent-working/agent-monitoring/retro/RETRO-2026-W41.md (Addendum 2026-10-08)

## Related Code Areas
tools/sessions/launch.py, tools/sessions/session_start_hook.py, tools/gate_checks/done_checker_static.py

## Assumptions / Open Questions
The 10 GB default is a guess sized to about 10 measurement batches of about 1 GB; the implementer may propose another value with evidence.

## Implementation Notes
New `tools/sessions/disk_headroom.py` (read-only; `free_bytes` is one statvfs, `measure` walks the worktrees). `launch.py::disk_warning` and `session_start_hook.py::_disk_line` wire it in; the launcher walks only when free space is below the threshold. Doc section added to `docs/guides/agent_session_reset_boundaries.md`. Plan, investigation and test plan are in stored_artifacts.

## Test Summary
`pytest tests/tools/test_disk_headroom.py test_session_launch.py test_session_resolve_and_hook.py test_session_start_handover_hook.py`: 108 passed (11 new).

## Files Changed
tools/sessions/disk_headroom.py, tools/sessions/launch.py, tools/sessions/session_start_hook.py, tests/tools/test_disk_headroom.py, docs/guides/agent_session_reset_boundaries.md

## Completion Summary
All four acceptance criteria met. Warn only; nothing is deleted or refused.
