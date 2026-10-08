
## RETRO-2026-W40: note stamped at 10 runs

<!-- retro-note runs=10 -->
_Written by agent-working-design, 2026-09-29. Checked against `agent-working/agent-monitoring/data/*/runs.jsonl`
on origin/main `4512eae30` plus this branch's W40 shards (`28c75d168`)._

- **All 10 runs this window are hand-orchestrated closures, not pipeline runs, so most of the
  per-run metrics above measure the recording tool, not the work.** Every W40 run has
  `start_ts == end_ts`, `agent_count == 6` (the 6 phase events passed to
  `record_hand_orchestrated_closure.py`), and every event has `agent: claude`. So "Avg duration
  0 min", "Avg agents per run 6.0", and the single-row Agent Status table are artifacts of that
  tool's documented defaults, not observations:
  - identical start/end when wall-clock time wasn't tracked (module docstring, around lines 26–30);
  - `--workflow` defaults to `implement-ticket` (line 267);
  - `--agent` defaults to `claude`.
  Don't read them as "fast, cheap runs".
- **The same pattern goes back further than this week, which changes how the W37–W39 retros read.**
  `implement-ticket` runs with zero duration (the hand-closure signature) vs timed (real pipeline):

  | Week | zero-duration | timed |
  |---|---|---|
  | W33–W35 | 0 | 334 |
  | W36 | 30 | 68 |
  | W37 | 106 | 9 |
  | W38 | 83 | 6 |
  | W39 | 64 | 6 |
  | W40 | 10 | 0 |

  Since ~2026-09-06, about 94% of "implement-ticket" runs are hand closures that share the real
  pipeline's workflow label. This matches the same-date collapse of `implement-epic` (0 runs
  W37–W40) and `create-tickets` (2 runs W37–W40) found on 2026-09-29. Delivery moved to planner
  sessions dispatching to an implementer session that hand-orchestrates. Per-agent metrics (gate
  failures by agent, architecture-reviewer coverage, doc-updater/parity-updater usage) have
  therefore been mostly empty for four weeks without the retro saying so.
- **Candidate action (for the user to decide, not filed):** make the two populations separable in
  the report. Either the closure tool records a distinct `workflow` value (e.g.
  `hand-orchestrated`, which W36 already used for 20 runs), or the retro splits the Run Summary by
  the zero-duration signature. Recording a distinct value is cleaner. It is NOT a request to gate
  or discourage hand closure (agent-tooling checks stay proportionate); it only stops the report
  from blending two different things. Check the recorded rationale for the `implement-ticket`
  default first (TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP) before changing it.
- **Data-integrity incident this window, now fixed on this branch:**
  TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS. Three closed tickets' working_log
  rows had silently moved into other checkouts' CSVs, because consolidation read shards from the
  script's own checkout but wrote to the cwd's CSV. It was found by reading origin/main after a
  merge, not by any check. `done_checker_static`'s `working_log_exactly_one_row` would have caught
  it per ticket, but nothing runs it against main after a merge.
- **Spend proxy covers 8 of 58 events (13.8%).** That's expected for hand closures: there's no live
  sidecar during the work, so there are no `cost_proxy_score` keys, by design. The 1101.0 Scope
  total is 4 events and isn't a trend.
- **Parity skipped 8 of 8.** This is normal for hotfix-tier tickets with no Mechanics Bible impact.
  It isn't a gap.
- **Read-to-search ratio 11.5 (46 reads / 4 searches)** is high, but with 10 small hotfixes it
  isn't a signal on its own. Revisit it only if it holds across a larger window.
- **Carry-forward:** `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION` stays BLOCKED, since
  there were zero `implement-epic` runs and no post-fix `create-tickets` run.
  TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER (on this branch) adds a rule to offer
  both workflows, which is the only in-flight change likely to unblock it.

## RETRO-2026-W40: note stamped at 18 runs

<!-- retro-note runs=18 -->
- **Addendum (agent-working-implementer, 2026-09-29, after this retro's "18 runs" regen):** 3 more
  runs landed on this same `scripts-tools-governance` branch since the note above was written —
  `TCK-20260929-RETIRE-SCRIPTS-DIR`, `TCK-20260929-TOOLS-ORPHAN-FILE-CHECK`, and the closing
  `TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC` — all via `record_hand_orchestrated_closure.py`,
  same documented pattern above (zero-duration, `agent_count: 6` or `2` for the epic's shorter
  Scope/Finalize-only event set). No new gate failures, no new spend-proxy coverage (same 0
  live-sidecar-during-hand-work limitation). Nothing here changes the note above's analysis or
  its candidate action — flagging only so the run count discrepancy (the note's "10 runs" vs.
  this regen's 18) isn't mistaken for drift in a future read.

## RETRO-2026-W40: note stamped at 38 runs

<!-- retro-note runs=38 -->
- **Addendum (agent-working-implementer, 2026-09-30, regen at 38 runs / 278 events, origin/main
  `833b60306`; `make agent-monitoring-validate` OK, 35 pre-existing resume-collision warnings):**
  - **What failed most:** `done-checker` (3 of 7 calls `failed`, the only source of the 3
    `dod_condition_failed` reason codes) and `test-scoper` (2 of 6). All 3 done-checker blocks
    were checker-side, not substance: a stale-`OPEN` Status plus `docs/REGISTRY.yaml` undeclared
    (RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS), `investigation.md` explanatory bullets misparsed as
    required-doc declarations (COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY), and a live-modified
    tracked doc the ticket claimed reverted (MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING, the one
    real finding). Both test-scoper failures were pre-existing, unrelated tests confirmed by
    revert-and-rerun. Two PR #261 hotfixes (`DONE-CHECKER-TESTS-WRITE-TRACKED-FILES`,
    `DONE-CHECKER-POST-CLOSURE-FALSE-FAILS`) target this class; W41 will show whether done-checker
    failures drop.
  - **What was slow:** 4 runs over 30 min. `FOLDER-tickets-todos-systemic-world-first-wave` (130
    min) was 100% idle (waiting on a human), so not a work-speed signal. `NATURAL-AGING-DEATH-DUAL-
    WRITER-RACE` was 67 active / 35 idle. 3 of the 5 cost-proxy outliers are `test-scoper` Test
    phases (up to 4.9x the phase median), so test-scope breadth is the recurring spend driver.
  - **What to change (one action, not filed):** no action on the test-scoper outliers yet; three
    in one week is a pattern worth watching, not a verdict. Re-check at the next retro whether the
    same agent still dominates before touching its prompt.
  - **What worked (don't revert):** the candidate action in the note above shipped in PR #257. The
    Run Summary now splits by execution mode (Hand-closed 13, Native workflow 1, Unlabelled 24),
    so the blended-population problem is gone and the 1 native-workflow run (6 min, the
    `create-tickets` pilot) is now visible as its own row. "Pipeline 0" remains true: no run used
    `implement-ticket.js` this week, matching the carry-forward above.

## RETRO-2026-W40: note stamped at 61 runs

<!-- retro-note runs=61 -->
- **Addendum (agent-working-design, 2026-10-01, regen at 61 runs / 420 events; PR #268 merged):**
  - **What failed most:** unchanged in kind. `done-checker` is still the only source of failures
    (3 of 7 calls, all 3 `dod_condition_failed`; every Gate failure count is 0), and `test-scoper`
    is 2 of 6. The run count grew 18 to 61 without a new failure class. Test (2 failed) and
    Verify (3 failed) are the only phases with any `failed`.
  - **What was slow:** the same 4 slow runs as the 38-run regen; none were added by the 23 new
    runs. The 130 min `systemic-world-first-wave` is 100% idle, so it isn't a work-speed signal.
    `test-scoper` still owns 3 of the 5 cost-proxy outliers (up to 4.9x the phase median),
    unchanged since the last addendum, so the "watch, don't act" call stands.
  - **What to change:** nothing new. The two follow-ups this retro motivates are already filed as
    drafts: `TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT` and
    `TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION`. Pipeline is still 0 runs,
    Native workflow is 1 (the `create-tickets` pilot), so the epic port is what can add a second
    native row.
  - **What worked:** the execution-mode split keeps the populations separable at 61 runs
    (Hand-closed 36, Native 1, Unlabelled 24). Parity skipped 49 of 51 and Security-Review skipped
    6 of 6, which is expected for hotfix/test-heavy work, not a gap.
  - **Caveats:** the spend proxy covers 18.3% of events (77 of 420), so cost conclusions above are
    partial. Measurement Watchlist: the one row (`TCK-20260924-DELIVERY-COST-MEASUREMENT`) was not
    re-measured here, so it stays.
