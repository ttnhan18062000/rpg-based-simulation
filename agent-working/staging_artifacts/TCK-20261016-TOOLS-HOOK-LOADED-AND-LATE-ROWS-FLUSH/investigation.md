---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH
artifact_type: investigation
tags: [agent-monitoring, hooks, data-quality]
---

# investigation — TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH

## Method
`measure.py` (this folder; per-session output in `sessions.csv`, run at `origin/main` 5a31b50f0 on host ubuntu, read-only) takes the
distinct `session_id` of every run row (`runs.jsonl`, any shard) of W41, W42 and W43. Per session it counts tool rows in the committed
shards at the ref plus every local worktree's and the main checkout's data folder (tracked or not). For a session with none it opens its
transcript and records: the project dir, the cwd class of every tool call (repo root / repo subdir / outside), and whether any project
hook ever reported through the transcript (`hook_success` attachments). Then every local and remote branch ref was searched for the
session's id in a `*tools.jsonl`.

## Finding 1: the earlier "no trace of post_tool_hook.py in the transcript" test cannot detect an unloaded hook
`post_tool_hook.py` prints nothing on a normal call (only a low-disk line), and a transcript records a hook only through a
`hook_success` attachment, which exists for hooks that produced output. So a session where the hook ran looks the same as one where it
did not. The 14-of-19 reading in the ticket's Request Summary rested on that test and does not stand.

## Finding 2: on this host, no measurable closing session lacked the hook
| week | closing sessions (run rows with a session id) | rows reached `origin/main` or a local file | no rows, transcript on this host | no rows, no transcript here |
|---|---|---|---|---|
| W41 | 41 | 15 | 10 | 16 |
| W42 | 29 | 17 | 11 | 1 |
| W43 (partial) | 12 | 11 | 0 | 1 |

All 21 no-row sessions with a transcript (18 distinct; three span W41 and W42): 0 ran outside the repo, 0 ran from a repo subdirectory,
and every one has hundreds of project-hook events in its transcript (`PreToolUse`, `PostToolUse` retro/epic hooks, `SessionStart`).
Project settings were loaded in all 21. The earlier "outside the repo" class (17 sessions, TCK-20261006) is real but is not in the
W41-W43 closing sessions with transcripts here. The 18 closing sessions with no transcript on this host (16 in W41) cannot be classified.

## Finding 3: all 21 have their rows; they sit in the main checkout's `main.tools.jsonl`, which no PR commits
Every one of the 18 distinct sessions has its rows in `main.tools.jsonl` on the unmerged branch `lead-planner-monitoring-shards`
(efc7b043f, 2026-10-20, "stage the main checkout's agent-monitoring shards (W41-W43)"): 5295 rows for W42, 809 for W43, the W41 file
too. These are lead and planner sessions launched in the main checkout (`placement: launch: main-checkout`), whose branch is `main`,
so the hook keys their rows to `main.tools.jsonl`. A PR branch never contains that file, `origin/main` has no `main.tools.jsonl`
for any week, and W43's file (558 rows now) is on disk only. The rows are not lost; they never reach a PR. This is the "late rows"
class of the ticket, and it is the whole measurable gap, not a quarter of it.

## Consequence for the scope
- Scope 1 (say when the hook is not loaded): the data gives it no measured case on this host. It stays cheap and report-only
  (a new line in the freshness check), but it would not have changed W41-W43's coverage.
- Scope 2 (late rows) carries the gap. Fix candidates below, in the plan.

## Limits
Only transcripts still on this host; sessions of host u24desktop and purged ones are unclassified (18 closing sessions). Closures
carry no session id on 80 W41 run rows, so those are not in the counts. The 4,000+ rows per week on the side branch were not
re-attributed to individual sessions beyond the 18.
