---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
artifact_type: investigation
tags: [observability, testing, bug]
---

# Investigation — TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD

## Context Scan

`mcp__knowledge-search__search_docs` (queries: "agent ops dashboard stats API skill usage",
"KGMCP retrieval cache schema migration", "generate_retro compute_retro_metrics") and
`graphify query` (`"AgentMonitoringStats"`, `"build_skill_usage_section"`,
`"retrieval_cache_generation schema migration"`) were run first, per CLAUDE.md's mandatory Context
Scan order, before any grep/direct file read. Results confirmed the exact shape of the gap and the
migration convention to follow (see Findings below) and surfaced the related-tickets list already
present in the ticket body (`TCK-20260718-AGENTOPS-STATS-BOARD-EPIC` /
`-STATS-API` / `-STATS-TAB-FRONTEND` / `-RETRO-STATS-REFACTOR`,
`TCK-20260805-SKILL-USAGE-METRIC`, `TCK-20260810-SKILL-USAGE-RETRO-TRACKING`,
`TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS`).

## Findings

1. **`tools/retrieval_cache.py`** — the L1 (`retrieval_provider_result_cache_rows`) and L2
   (`retrieval_context_packet_cache_rows`) tables carry `hit_count`/`last_hit_at` (L1) or
   `hit_count`/`last_validated_at` (L2), but:
   - `write_provider_result_cache()`/`write_context_packet_cache()` (`INSERT OR REPLACE`, ~L781/
     ~L988) hardcode `hit_count=0, last_hit_at=NULL`/`last_validated_at=NULL` on every write —
     silently discarding prior hit history on every refresh.
   - Neither table, nor any function, carries `run_id`/`agent`/`phase`/`ticket_id` attribution —
     there is no way to answer "which ticket/agent caused this hit/write."
   - `record_provider_result_cache_hit()`/`record_context_packet_cache_hit()` (~L810/~L1025) are
     the only two real "hit" call sites (a bare `check_*_cache()` lookup is not itself a hit — DD9's
     Non-collapse rule, confirmed by that function's own docstring).
2. **Migration convention** (`docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`,
   established by `TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS`/
   `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS`): ordered `migration_00N_*(conn)`
   functions, `CREATE TABLE IF NOT EXISTS` for a wholly new table (idempotent), `ALTER TABLE ADD
   COLUMN` + `PRAGMA table_info` existence check for a column addition. Only a *new-table* migration
   (1, 2) stamps `retrieval_cache_generation` with a new `retrieval_cache_schema_version` and bumps
   the module constant — confirmed by direct read: migrations 3/4 (`ALTER TABLE`) do neither. Next
   open ordinal is 5.
3. **Sidecar mechanism** — `tools/agent-monitoring/post_tool_hook.py:46-63` reads
   `.claude/current_run` (JSON: `run_id`/`seq`/`phase`/`agent`/`execution_id`/`provider`/
   `ticket_id`, each falling back to `None`) to attribute `agent-monitoring/tools.jsonl` rows. No
   shared, importable function exists for this — it's inlined in a `try/except` block in the hook
   script. Live reproduction of the staleness bug this ticket's Scope item 6 describes: at
   investigation time, `.claude/current_run` held
   `{"run_id": "TCK-20260817-HOTFIX-DECISION-TRACE-SELECTED-MOCK-SCORE", ...}` while that exact
   ticket already lived under `tickets/done/`, not `tickets/inprogress/` — confirmed via
   `ls tickets/done/ | grep DECISION-TRACE`.
4. **`tools/agent-monitoring/generate_retro.py`**:
   - `compute_retro_metrics(runs, events, tickets_root=None)` (~L672, pre-change) is the pure
     computation backing both the CLI Markdown report and
     `DashboardCache.get_agent_monitoring_stats()` — it did not accept a `tools` param, so it could
     not see Skill invocations at all.
   - `build_skill_usage_section(tools)` (~L434) is a separate function, called only from `generate()`
     (the Markdown renderer) and `skill_usage_metric.py` — never from `compute_retro_metrics()`. This
     is the confirmed root cause of the observed dashboard gap (no Skill Usage metric visible on the
     live board).
   - `compute_retrieval_metrics(events)` is the closest existing precedent for a pure,
     already-loaded-data function feeding both the CLI report and (indirectly, via
     `compute_retro_metrics`) a future JSON consumer — followed as the template for
     `compute_kgmcp_cache_efficiency_metrics(access_log_rows, tools=None)`.
5. **`src/api/agent_ops_dashboard/ingest.py`** — `DashboardCache._rebuild()` loads
   `tools_all`/`tools_unparsed` locally but only keeps derived indexes
   (`self._tools_by_seq`/`self._tools_by_run_recent`); the raw list was discarded. `models.py`'s
   `AgentMonitoringStats` is confirmed to be a strict field-for-field mirror of
   `compute_retro_metrics()`'s dict — the established, load-bearing convention for wiring any new
   `compute_retro_metrics()` key into the API.
6. **Frontend** — `dashboard-frontend/src/views/StatsView.tsx` (`TCK-20260718-STATS-TAB-FRONTEND`)
   is the real Stats tab file (confirmed via direct file search, not guessed). Conventions
   confirmed by reading its existing sections: `StatTile` for headline numbers, `BarChart` for
   magnitude distributions, plain `<table>` (matching `TicketsView.tsx`) for per-entity breakdowns,
   `GlossaryTooltip` wrapping any agent/tier/phase-like cell value, one shared `descriptions` map
   built from `useGlossary()`.
7. **Mid-task reinforcement** — the orchestrator relayed a direct framing correction mid-implementation:
   raw hit/write counters alone don't answer "is the cache working well" — the section needed a
   glanceable verdict synthesizing reuse rate, redundant-refetch detection, dead-write
   (write-never-hit) detection, and coverage vs. real `search_docs`/`graphify` call volume. This
   was incorporated before Implement completed (see plan.md's Design Decisions).

## Real Data (verified during investigation, re-verified at implementation end)

Running `.venv/bin/python3 tools/agent-monitoring/generate_retro.py --all` against the real
1149-run corpus, then `DashboardCache.get_agent_monitoring_stats()` against the same real data,
both showed **0 KGMCP cache hit/write events against 2605 real `search_docs`/`graphify`/
`ToolSearch` calls** — i.e., the KGMCP retrieval cache is not being exercised by real agent work at
all today. This is itself the headline finding this ticket's dashboard/retro sections now surface
(verdict: `NOT IN USE`), not a fabricated example.

## Assumptions

- `retrieval_cache.py`'s cache DB path (`CACHE_DB_PATH`) is a single fixed relative path, not
  parameterized by `DashboardCache`'s own `repo_root` — an existing limitation of that module
  (every function in it reads the same module-level constant), not something this ticket
  introduces or is in scope to fix.
- Full parity-ledger-entry authorship for `docs/parity_ledger/infrastructure.yaml` (the
  exhaustive `id`/`text`/`v2_evidence`/`test_path` format used by prior `retrieval_cache.py`
  schema-migration tickets) was evaluated and deliberately deferred — see plan.md's Scope Guards
  and the ticket's own Completion Summary for the explicit disclosure.
