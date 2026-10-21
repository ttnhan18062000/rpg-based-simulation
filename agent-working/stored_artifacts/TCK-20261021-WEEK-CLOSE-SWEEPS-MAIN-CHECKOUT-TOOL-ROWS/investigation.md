---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS
artifact_type: investigation
tags: [agent-monitoring, data-quality, hooks]
---

# Investigation — TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS

Evidence ported from the superseded PR #705 (TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH was closed by #703 on host
u24desktop). Measured on host ubuntu with `measure.py` and `unknown_durations.py` (this folder; per-session output in `sessions.csv`)
at `origin/main` 5a31b50f0.

## Where this agrees and differs from #703's u24 measurement
- **Agree:** the earlier "no trace of post_tool_hook.py in the transcript" test is not a measure of whether the hook ran (a transcript
  records hook events, not command text, and the monitoring hook is silent); late rows are a larger share than a quarter; a
  reminder is cheap and report-only.
- **Differ (counts):** u24 classed 19 W41 sessions with a transcript as 8 rows-in-an-unmerged-worktree-shard, 6 with no hook event at
  all, and 5 with hook events but no row anywhere. Here, 21 W41-W43 no-row sessions with a transcript (18 distinct) had **0** without
  hook events and **0** outside the repo; **all 18** have their rows, in the main checkout's `main.tools.jsonl` (found on the
  unmerged branch `lead-planner-monitoring-shards`). u24 searched worktrees and the main checkout's working tree but not other git
  refs, so rows that exist only on a branch ref looked absent; its "5 hook events, no row" class is consistent with this one.
- **Why the two hosts differ:** they are different machines and different sessions (lead and planners launched in the main checkout
  here; u24's were worktree sessions). The 6 no-hook sessions at u24 are not contradicted by 0 here; they are a different population.
- **What #703 does not cover:** a main-checkout session never commits through a PR branch, so a reminder cannot get its
  `main.tools.jsonl` rows into `main`. That is what this ticket's sweep does.

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
