# Implementation Sequence — agent-monitoring-unified-weekly-data

Tickets must be implemented in this order. `implement-epic` reads this file to override alphabetical
order.

## Order

1. TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY  (no deps in this batch)
2. TCK-20260903-MONITORING-DATA-MIGRATION  (depends on: TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY)
3. TCK-20260903-MONITORING-DATA-CONSUMERS-CORE  (depends on: TCK-20260903-MONITORING-DATA-MIGRATION)
4. TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD  (depends on: TCK-20260903-MONITORING-DATA-MIGRATION)
5. TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION  (depends on: TCK-20260903-MONITORING-DATA-MIGRATION)
6. TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY  (depends on: TCK-20260903-MONITORING-DATA-MIGRATION)
7. TCK-20260903-MONITORING-DATA-DOCS-SWEEP  (depends on: TCK-20260903-MONITORING-DATA-MIGRATION; should
   run last, see below)

## Why This Order Matters

- **Ticket 1 (write-path unification) must land first**: it determines what week-folder shape exists
  and is actively being written for the current in-progress week, for all 3 sources, and fixes the
  critical `record_events.py` ground-truth-read bug that has been silently zeroing out
  `tool_call_count`/`cost_proxy_score` on every real event since the prior epic's migration landed
  (2026-09-02). This bug fix is bundled into ticket 1 rather than split into a separate hotfix
  precisely because both changes touch the same call site (`record_events.py`'s `tools`-source
  read) — see ticket 1's own Request Summary for the "not a side note" framing the requester asked
  for.
- **Ticket 2 (historical migration) must land second**: it needs ticket 1's cutover to have already
  happened so its merge-into-current-week-folder logic doesn't assume every week folder starts empty
  (same reasoning the prior epic's own `SHARD-WRITE-PATH` → `SHARD-MIGRATION` ordering used). Ticket
  2 also physically relocates the prior epic's already-correctly-bucketed
  `agent-monitoring/tools/tools-YYYY-Www.jsonl` shards into the new `data/<week>/tools.jsonl` shape,
  alongside re-bucketing the still-monolithic `runs.jsonl`/`events.jsonl`.
- **Tickets 3, 4, 5, and 6 are mutually file-disjoint** (core `tools/agent-monitoring/` consumers vs.
  `done_checker_static.py`/`agent_ops_dashboard/ingest.py` vs. the separate
  `tools/agent_replay_codex/`/`tools/agent_codex_*` subsystem vs. a brand-new referential-integrity
  script) and each depends only on ticket 2's real multi-week data existing on disk — not on each
  other. They are listed sequentially here because `implement-epic` executes this batch's tickets in
  list order, but there is no dependency reason they couldn't be reordered among themselves (3-6) if
  a future run wants to; they were kept in this order to match the epic's own child-ticket numbering
  and the relative risk/review-care ordering (core tooling, then gate/production-API code, then the
  more isolated codex subsystem, then new referential-integrity tooling).
- **Ticket 7 (docs/CLAUDE.md/`.gitattributes`/skill sweep) is sequenced last**: it has no hard
  file-level dependency on tickets 3-6 (it touches disjoint doc/config files), but accurately
  documenting "the current consumer state" is only true once those consumers have actually migrated
  — running it earlier risks describing an aspirational state that then needs a second edit pass.
  This also matches the requester's own suggested ordering ("referential-integrity verification and
  the docs sweep can likely run in parallel near the end").

Running alphabetically would attempt tickets before their dependencies are in place. Re-run
`/implement-epic` with the same folder after any gate failure — already-done tickets are skipped
automatically.

## Cross-Batch Note

This batch corrects and extends `tickets/done/agent-monitoring-weekly-sharding/` (parent epic
`TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC`, 3 children + 1 follow-up hotfix, all DONE, on open PR
#112 which has not yet merged to `main`). This batch's work lands on the same branch
(`worktree-monitoring-tools-weekly-sharding`) / same PR, per this repo's "push to open PR, not new
stacked PR" convention — it is not a standalone new PR.
