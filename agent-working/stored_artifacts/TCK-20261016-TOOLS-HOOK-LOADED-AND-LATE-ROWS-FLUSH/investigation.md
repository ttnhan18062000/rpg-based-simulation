---
status: historical
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

## Finding 4: reconciliation with the retro's duration coverage (W43)
`unknown_durations.py` (this folder) replays `hand_closure_time.resolve()` offline for every W43 run row at `origin/main`
(53 rows, all with a session id; 41 `duration_source: unknown`, 12 `tool_activity`), with every tool row known now.
Why the 41 are unknown:

| reason | runs |
|---|---|
| the session has no tool rows anywhere | 17 (15 of them one session, no transcript on this host) |
| the activity block ending at the closure has < 3 rows, no earlier closure in it | 11 |
| the session has unattributed rows, none before this closure | 5 |
| back-to-back closure: fewer than 3 rows after the session's previous closure | 4 |
| the replay now derives `tool_activity` (rows were not on the closer's disk at closure time) | 4 |

Of the 24 unknown runs whose session has rows before the closure, 10 closed more than 30 minutes (`PAUSE_THRESHOLD_SECONDS`) after the
session's last row, so the activity block is empty; 9 closed within the threshold. Every row of these sessions is unattributed
(`run_id` null), so sidecar attribution is not the cause. The planner's back-to-back hypothesis explains 4 of 41.

State plainly: scope 2(c) improves **row coverage**, not the retro's duration coverage. It could only help the 4 runs where rows
were not on the closer's disk in time, plus part of the 17 with no rows if their session is a main-checkout one. The derivation
rules (3 rows minimum, the pause threshold, claim-after-previous-closure) are the larger cause and are **not** changed here; the
planner takes that to the owner as a follow-up.

## Consequence for the scope
- Scope 1 (say when the hook is not loaded): the data gives it no measured case on this host. It stays cheap and report-only
  (a new line in the freshness check), but it would not have changed W41-W43's coverage.
- Scope 2 (late rows) carries the gap. Fix candidates below, in the plan.

## Re-measure (after the change)
Owner decision 2026-10-21: back-fill is **W43 only**; W41 and W42 are not re-closed and keep their numbers. Lead restored the 809 W43
rows into the main checkout's `main.tools.jsonl` (now ~1394 lines); the side branch `lead-planner-monitoring-shards` is not merged
or read. W43 is not yet a finished week, so its close has not run; the table is what that close gives (sweep simulated by reading
the same file the sweep reads).

| week | closing sessions | rows on `origin/main` today | rows after the W43 close sweeps the main checkout |
|---|---|---|---|
| W41 | 41 | 15 (unchanged, no re-close) | 15 |
| W42 | 29 | 14 committed (+3 local) (unchanged) | 14 |
| W43 | 12 | 8 | 11 (the 12th is the session with no transcript or rows anywhere) |

The earlier 27% (11 of 41, W41, from the ticket) is 15 of 41 (37%) on today's `origin/main`, the difference being later merges;
the sweep does not change W41. W43 goes from 8 of 12 (67%) to 11 of 12 (92%). This is row coverage; the retro's duration coverage is
unchanged (finding 4).

## Limits
Only transcripts still on this host; sessions of host u24desktop and purged ones are unclassified (18 closing sessions). Closures
carry no session id on 80 W41 run rows, so those are not in the counts. The 4,000+ rows per week on the side branch were not
re-attributed to individual sessions beyond the 18.
