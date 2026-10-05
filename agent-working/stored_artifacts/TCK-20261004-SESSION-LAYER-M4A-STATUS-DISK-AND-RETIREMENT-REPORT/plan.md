---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-SESSION-LAYER-M4A-STATUS-DISK-AND-RETIREMENT-REPORT
phase: open
date: 2026-10-05
tags: [ai]
---

# plan — TCK-20261004-SESSION-LAYER-M4A-STATUS-DISK-AND-RETIREMENT-REPORT

One module plus tests, no schema change beyond the confirmed owns line.

`tools/sessions/status.py` (read-only; git runs with `--no-optional-locks`). Per worktree: branch, dirty count, git operation in progress (reuses `launch.git_operation_in_progress`), open PR via `gh` (`unknown` on any failure), size (`du -sk`), last commit/activity, commits not in main. Per seat: staffing and instance state from M2a's role-state directory (`unknown (M2 not present)` when the directory is absent, `none` only when it exists with no instance). Flags a worktree lease whose role is not the manifest writer and a session holding two live seats. Disk warning at `DISK_WARN_FRACTION = 0.85`; retirement uses `RETIRE_IDLE_DAYS = 14` and requires no PR (unknown counts as a PR), no unique commits, clean, no operation, no live seat, and either unowned/unstaffed or idle. The command to run is printed; nothing is removed.
