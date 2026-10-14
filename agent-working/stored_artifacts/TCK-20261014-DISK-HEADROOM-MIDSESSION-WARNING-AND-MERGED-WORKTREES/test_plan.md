---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES
artifact_type: test_plan
tags: [ai, process-improvement]
---

# test_plan — TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES

## Cases
- no line at or above the threshold; a line below it naming free GB and both commands
- no second statvfs inside the 10-minute window; repeat at most every 30 minutes; the below-2-GB escalation warns once at once
- independent sessions; a statvfs exception, an unwritable state dir and a corrupt state file never raise; stale state files are swept; a hostile session id stays inside the state dir
- the hook prints a PostToolUse additionalContext, still writes its monitoring record, and is silent inside the window
- the report lists a merged-head worktree, not a unique-commits one; lists clean detached worktrees as "detached, check"; lists nothing when gh is unavailable or the classifier fails

## Proof Plan
- level: unit tests with fakes for statvfs, gh and git, one subprocess test of the hook, and a read-only run on the real worktrees
- proof kind: behavioural tests and a recorded real run
- oracle source: ticket acceptance criteria AC1-AC4
- expected effect: the warning reaches a running session, adds no per-call syscall, and removes nothing
- selected commands: `pytest tests/tools/test_disk_warning.py tests/tools/test_disk_headroom.py tests/tools/test_post_tool_hook.py tests/tools/test_session_prune_branches.py`; `python3 tools/sessions/disk_headroom.py`
