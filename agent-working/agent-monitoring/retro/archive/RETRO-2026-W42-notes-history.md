
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
