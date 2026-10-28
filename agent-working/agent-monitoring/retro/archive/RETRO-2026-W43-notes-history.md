
## RETRO-2026-W43: note stamped at 40 runs

<!-- retro-note runs=40 -->
**W43 to date, 2026-10-20 (agent-working-planner, host ubuntu).** 40 runs: all DONE, all hand-closed, 0 pipeline, 0
native. Data is at `d3a0e4843` plus this host's unmerged shards. `agent-monitoring-validate`: OK, 2477 runs and 15909
events, with 3 W40+ warnings (done-without-working_log). The cadence hook counted 58 runs since the W42 report; this
report covers the 40 that fall in W43.

1. **What failed most?** The Finalize self-check again: 19 blocking verdicts out of 75. 12 were fixed and rerun, 4 rerun
   with no change, 1 overridden, and 2 have no outcome yet (`gv-7ab2fbdc5d10421b` starvation-threat, rpg;
   `gv-46a9d6f22b8c41d0` websocket-observability flake, rpg). By condition: `registry_entry_regenerated` 15,
   `migration_complete` 5, `working_log_exactly_one_row` 4, `ticket_finalized` 1.
   - The ledger stores only `PASS`/`FAIL` per condition, so it can't say why `registry_entry_regenerated` fails 15 times.
     The Finalize path regenerates the registry itself, so a failure there is either a non-zero `generate_registry()` or
     a ticket that is not yet in `done/`.
   - Action (candidate ticket, owner's go): have the self-check record a short reason class next to each failing
     condition, then size the `registry_entry_regenerated` cause from one week of data.
   - Action (no ticket): the two closing rpg seats record outcomes for their two open verdicts.
2. **What was slow?**
   - No run is over 30 min. The derived average is 28 min (n=10).
   - Durations are known for 10 of 40 runs (25%). 29 of the 40 run shards have no tools shard. All of them come from
     testing, rpg (except 3 batches), codebase and asset batches. That's the same 27% coverage that
     TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS measured on W41.
   - Action: no new ticket. `TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH` (todos, OPEN, P2) is the filed fix and
     hasn't been dispatched yet. Proposal: dispatch it next for agent-working, because coverage hasn't moved in two weeks
     and it also blocks the watchlist metric below.
3. **What to change?**
   - `agent_count` on hand closures counts recorded phase events (6 or 8 per run), not agent calls: the average is 6.5 and
     there are 262 "claude" calls for 40 runs. The folded-phase rows are excluded since #690, but artifact-derived
     Investigate/Plan events and the six base phases still count. The schema says agent calls.
     - Action (candidate ticket, owner's go): set hand closures' `agent_count` to null or `unknown`, as for durations,
       and exclude them from "Avg agents per run".
   - Paths: on the hand path, standard runs still show Review, Document-Update and Architecture-Verify as omitted (12 of
     12). Every one predates #690 (merged 2026-10-20), which records folded phases as `skipped`. Recheck in the next
     report before treating them as routing candidates.
   - `role_boundary`: 1 `edit_outside_owns`, from platform-planner-u24 writing its own ticket's
     `agent-working/staging_artifacts/<ticket>/investigation.md`. Planner `may_write` covers `agent-working/tickets/**`
     but not `agent-working/staging_artifacts/**`, while standard dispatch requires the planner to start those
     artifacts. That's a false-positive class.
     - Action (small candidate ticket, owner's go): add `agent-working/staging_artifacts/**` to planner `may_write` in
       `registries/session_roles.yaml`.
   - 14 summaries are truncated (>200 chars). That's minor; it has no action.
4. **What worked?**
   - All three W42 actions landed. The Gate failures row now cites the ledger (TCK-20261018-RETRO-GATE-FAILURES-ROW-CITES-LEDGER).
     `make agent-monitoring-index` runs without a local venv (TCK-20261018-MAKE-AGENT-MONITORING-INDEX-WORKS-WITHOUT-LOCAL-VENV).
     Hand closures record folded phases as `skipped` (#690).
   - `path_reason` is never unstated, every `skip_reason` is `condition_false`, and no run is failed or blocked.
   - The `-u24` roles keep their own shards (`platform-implementer-u24` 2 runs), so cross-host shard collisions are gone.

- **Measurement Watchlist (`TCK-20260924-DELIVERY-COST-MEASUREMENT`):** still not checkable.
  - `delivery_cost_measurement.py --ref origin/main --since-week 2026-W42 --through-week 2026-W43` (main `c35648e75`)
    sees 195 gh calls but only 2 `gh pr create`, which gives 97.5 per PR. That's a coverage artefact, not a cost.
  - Recheck after TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH lands. The watchlist row is updated.
