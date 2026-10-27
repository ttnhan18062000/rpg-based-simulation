
## RETRO-2026-W42: note stamped at 56 runs

<!-- retro-note runs=56 -->
**W42 to date, 2026-10-15 (agent-working-planner).** 56 runs: all DONE, all hand-closed, 0 pipeline. The full two-week
investigation is the final note of RETRO-2026-W41; this note covers only what is specific to W42.
- **Better than W41:**
  - `session_role` unresolved: 2 of 56 (W41: 113 of 281).
  - `path_reason` unstated: 0; all 53 `skip_reason` values are `condition_false`.
  - No precheck-after-close false blocks.
- **Run Summary is misleading:** it says "Gate failures 0", but the Gates section shows 22 blocking Finalize verdicts (6
  overridden for missing staging artifacts, all platform, 1 unresolved). The summary line counts run final_status only.
- **Duration and cost known for 11 of 56 (20%), and only for agent-working sessions.** The other roles leave no tools shard,
  and no closer passes `--start-ts`.
- **Before W42 closes:** void the pending working_log row of the dropped `TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS`
  (2026-W42/platform-implementer-step1-closure.working_log.jsonl).
- **Time-gated epics:** GATE-OVERRIDE-LEDGER, HAND-CLOSURE-REAL-TIME-AND-COST and TICKET-PATH-RECORD can be closed on or
  after 2026-10-19 by citing this week's Gates, Run Summary coverage and Paths sections.

## RETRO-2026-W42: note stamped at 81 runs

<!-- retro-note runs=81 -->
**W42 refresh, 2026-10-18 (agent-working-planner, host ubuntu).** 81 runs: all DONE, all hand-closed, 0 pipeline, 0
native. Data is at `origin/main` 760f5ac9d plus this host's unmerged shards. `agent-monitoring-validate`: OK, 2368 runs and
15243 events, with 1 W40+ warning (done-without-working_log).

1. **What failed most?** The Finalize self-check (`done_checker_static.run_finalize_selfcheck`): 27 blocking verdicts out of
   108. Of those, 15 were fixed and rerun, 5 rerun with no change, and 6 overridden; 1 is still unresolved. The Run
   Summary still prints "Gate failures 0", because it counts `final_status` only. The 56-run note already flagged that
   this misleads, and it is unchanged.
   - Action: the summary row should cite the ledger's blocking count next to it. That's a candidate agent-working ticket,
     to be filed with the owner's go.
2. **What was slow?**
   - No run is over 30 min. The derived average is 22 min (n=15).
   - Durations are still known for only 15 of 81 runs (19%, down from 20% at 56), because closers outside agent-working
     neither leave a tools shard nor pass `--start-ts`.
   - Action: keep this under the existing hand-closure cost epic's follow-up rather than open a new ticket. That epic's
     children are all done, and its closure is proposed in the 2026-10-18 triage to lead-planner.
3. **What to change?**
   - Paths: on the hand path, standard tickets omit Review, Document-Update and Architecture-Verify in 54 of 54 runs, and
     hotfixes omit Document-Update in 23 of 23. So these are routing candidates by the report's rule.
   - These phases are not dead. The hand path folds them into Implement/Verify without recording them.
   - Action: record Document-Update/Review as `skipped` with a reason in `record_hand_orchestrated_closure.py --events`,
     not omit them, so the next retro can tell "folded" from "missing". That's a closer-convention change; it needs a ticket.
   - 11 summaries are truncated (>200 chars). That's minor; it has no action this week.
4. **What worked?**
   - `session_role` is unresolved in only 2 of 81 runs, and `path_reason` is never unstated.
   - Every `skip_reason` is `condition_false`.
   - The `TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS` void that the 56-run note asked for was recorded on 2026-10-16
     (`agent-working-w41-retro-followups.working_log.jsonl`), so that item is closed.

- **Epics:** this note confirms the 56-run note. GATE-OVERRIDE-LEDGER, HAND-CLOSURE-REAL-TIME-AND-COST and
  TICKET-PATH-RECORD (plus SESSION-LEAD-PLANNER) have every child done and can be closed on or after 2026-10-19. The
  triage table went to lead-planner for the owner on 2026-10-18 (#634).
- **Measurement Watchlist (`TCK-20260924-DELIVERY-COST-MEASUREMENT`):** not yet checkable.
  - `delivery_cost_measurement.py --ref origin/main --since-week 2026-W42 --through-week 2026-W42` reports 0 gh calls and
    0 `gh pr create`. So it doesn't see this week's per-batch shards before the week is closed, and most seats' tools
    shards aren't committed.
  - Recheck after the W42 close-week.
- **Tooling nit:**
  - `make agent-monitoring-index` fails in a worktree without `.venv`: the `$(shell for py in …)` picks nothing, so make
    tries to exec the `.py` and gets "Permission denied".
  - Validate still ran against the existing index.
  - This is a small agent-working fix for a later batch.
