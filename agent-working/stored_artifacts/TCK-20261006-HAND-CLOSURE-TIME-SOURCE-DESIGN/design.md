# Design — hand-closure time source, join key and schema delta

Ticket: `TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN` (child 1 of the real-time-and-cost epic).
Measured from git ref `origin/main` 7ddcd4526 plus the local worktree branch, over **every** `execution_mode: "hand"` run
in `agent-working/agent-monitoring/data/2026-W40` and `2026-W41`: 238 closures (W40 181, W41 57; W37-W39 hold none, so
the window was not extended). Per-run values with run_ids: `coverage_by_run.csv`. Reproduce: `measure_sources.py`.

## 1. Measured coverage

Baseline: 224 of the 238 hand closures (167/181 in W40, 57/57 in W41) record `duration_s = 0`.

| Source | Dates how many of 238 | Spread of the value | Main failure modes |
|---|---|---|---|
| **C. declared** (`--start-ts`/`--end-ts` passed) | 14 (5.9%): W40 14, W41 0 | measured by the closer; 201 s to 27,246 s | closers almost never pass it. Zero use in W41 |
| **A. tool activity** (`tools.jsonl` rows of the worktree shard, contiguous block, gap <= 1800 s, ending at the closure) | 130 (54.6%): W40 112/181, W41 18/57 | p10/p50/p90 = 150 / 1,185 / 5,596 s | 102 closures have **no tools shard at all** (the worktree never committed one); 6 more have a shard with no row in the window. 99 of the 130 share a 30-minute block with another hand closure (double attribution if claimed naively). 73 of 130 span more than one session |
| **B. git** (commit subjects citing the ticket ID; start = commit adding the file under `inprogress/`, else the first citing commit; end = last non-squash commit) | 235 (98.7%) | p10/p50/p90 = 0 / 729 / 54,387 s | `inprogress/` entry found for only 44 (18.5%): tickets often live untracked first. Squash merge leaves only the PR title: 2 closures are squash-only. At closure time the final commits do not exist yet, so B's end would have to be the closure time. Batch closes share one commit time, so the span is 0 for many (p10 = 0) |

Agreement, closures with both A and B dated and B > 0 (88): A/B ratio p10/p50/p90 = 0.003 / 0.54 / 13.6, and A <= B in 55.
The two sources do not measure the same thing: A is tool activity, B is calendar span including queue time and waiting.
So no cross-source tie-break can be trusted, and no value is ever averaged across sources.

## 2. Decision: time source

**Precedence at closure time: declared (C) > tool activity (A) > unknown.**

- Rejected B (git span) as a duration source: calendar time including waiting and untracked-file periods, 18.5%
  start coverage, and its end does not exist at closure time. It stays a cross-check in `measure_sources.py`, not a recorder input.
- A is chosen over B because it is evidence of work (not of waiting), is available at closure time, and is the same
  data the cost join needs, so one claim algorithm yields both time and cost.
- A's ceiling is 54.6% on past data, because many worktrees never commit `tools.jsonl`. The other closures record
  `unknown`. That is the intended outcome: **unknown, never zero.**

### Claim algorithm for A (also the cost join, child 3)

1. Candidate rows: `tools.jsonl` rows with `session_id == $CLAUDE_CODE_SESSION_ID` of the closing session, `ts <= end_ts`,
   and `run_id` null (rows already carrying a sidecar `run_id` keep that attribution and are never claimed).
2. Window lower bound: the latest of (a) the end of the previous hand closure recorded by the same session,
   (b) the start of the current activity block, where a gap > 1800 s (`PAUSE_THRESHOLD_SECONDS` in `duration_utils.py`) ends a block.
3. Claimed rows are exactly the rows in (lower bound, end_ts]. Because each closure's lower bound is the previous closure's end,
   a row is claimed by at most one closure: **no double attribution** (the sequential partition). `start_ts` = first claimed row's `ts`.
4. Fewer than `MIN_CLAIMED_ROWS = 3` claimed rows -> `unknown` (a batch's later tickets usually land here).
5. `claim_peers` = number of other hand closures by this session whose end falls inside the same activity block. It lets
   a retro exclude batch-shared windows, where the first ticket takes the whole block.

### Join key (rejected alternatives)

**`session_id` plus time window.** `record_hand_orchestrated_closure.py` already reads `CLAUDE_CODE_SESSION_ID`
(:280, :332) and the hook stamps the same id on every row (`post_tool_hook.py:73,160`).
- Rejected: ticket ID plus window. `tools.jsonl` rows carry `ticket_id: null` for hand work, so the ticket ID cannot select rows.
- Rejected: shard (worktree) plus window, which is what the measurement had to use. It mixes concurrent sessions in one worktree.

## 3. Schema delta (all optional on read; old rows stay valid and mean "unlabelled: predates the field")

| Where | Field | Type | Nullable | Values / meaning |
|---|---|---|---|---|
| runs | `duration_source` | string | optional | `declared` \| `tool_activity` \| `unknown`. Hand closures always write one. `measured` is reserved for pipeline runs and is not written by this epic |
| runs | `session_id` | string | yes | `CLAUDE_CODE_SESSION_ID` of the closing session, null when unset |
| runs | `claim_peers` | int >= 0 | optional | only with `tool_activity`; see claim step 5 |
| runs | `start_ts` | ISO 8601 | no (unchanged) | declared: as passed; tool_activity: first claimed row; **unknown: equal to `end_ts`** (the field is required, so it cannot be null) |
| runs | `duration_s` | int | yes (unchanged) | **null when `duration_source` is `unknown`**; otherwise `end - start` by `compute_duration_s`; a negative span stays null |
| events | `session_id` | string | yes | same value as the run |
| events | `ts` | ISO 8601 | no (unchanged) | stays the closure time unless the closer passed `ts` on the event; per-event times are not derived |
| events | `cost_source` | string | optional | `sidecar` (today's attribution) \| `session_window` (derived, this design). Absent = legacy. Written next to `tool_call_count` and `cost_proxy_score`, which keep their current location and the unchanged `cost_proxy.py` formula |

## 4. Owner decision to record in Implementation Notes

Do **derived** durations (`duration_source = tool_activity`) count in retro averages?

**Recommendation: no. Show them beside measured ones, never inside the headline average.** Retros report three groups: measured (pipeline,
declared), derived (`tool_activity`, with `claim_peers = 0` as the cleaner subset), and unknown (counted, never averaged).
Reasons: A covers only 54.6% and the missing 45% is not random (worktrees that do not commit tools shards), so a derived average is
biased; A and B disagree by up to three orders of magnitude, so the number is evidence of activity, not of elapsed time; and mixing
would silently change what every earlier retro's average meant.
If the owner answers "yes, count them", child 4 must label the average with its coverage ("n of N") and keep the derived-only column.

## 5. First two acceptance criteria per child

**Child 2, `TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS`**
1. A hand closure with no declared times and fewer than 3 claimable rows writes `duration_source: "unknown"`, `duration_s: null`, `start_ts == end_ts`. Tested.
2. A fixture `tools.jsonl` with 5 rows of the closing session writes `duration_source: "tool_activity"`, `start_ts` = the first row's `ts`, and `duration_s` = the span; a row with another `session_id` or a non-null `run_id` is ignored. Tested.

**Child 3, `TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION`**
1. Two hand closures by one session in one block: the rows before the first closure's end are claimed by it, the later rows by the second, and the union has no repeated row. Tested.
2. Claimed events carry `cost_source: "session_window"`; sidecar-attributed events carry `cost_source: "sidecar"` or no field, and a row with a sidecar `run_id` is never in a claim. Tested.

**Child 4, `TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE`** (starts only after the owner's answer in section 4)
1. The retro's Run Summary reports hand closures grouped by `duration_source` (declared / tool_activity / unknown / unlabelled) with counts. Tested.
2. The headline average duration follows the owner's recorded answer; with "no", a run with `duration_source` other than measured or declared is excluded from it and appears only in the derived group. Tested.
