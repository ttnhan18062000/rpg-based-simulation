---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
artifact_type: test_plan
tags: [observability, testing, bug]
---

# Test Plan — TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD

## Scope

Backend (`tools/retrieval_cache.py`, `tools/agent-monitoring/generate_retro.py`,
`src/api/agent_ops_dashboard/{models,ingest}.py`) and frontend
(`dashboard-frontend/src/{api.ts,views/StatsView.tsx}`) test coverage, plus real, non-mocked
end-to-end verification against the live repo corpus.

## `tests/tools/test_retrieval_cache.py`

- **`TestMigration005CacheAccessLog`**: fresh-DB apply, idempotency (run twice, no duplicate
  generation row), `retrieval_cache_generation` stamped to version 3, no mutation of existing
  marker-only/L1 tables (`sqlite_sequence` excepted — a real SQLite `AUTOINCREMENT` side effect,
  not a migration output), column-set matches the documented shape, never called from any
  `check_*`/`write_*` function (source-text AST guard).
- **`TestReadCurrentRunSidecar`**: absent sidecar -> all-`None`/not-stale; real sidecar fields read
  correctly; malformed JSON fails silently to all-`None`; `sidecar_stale=True` reproduces the live
  observed bug (sidecar points at a `tickets/done/` ticket); not stale when genuinely
  `tickets/inprogress/`; not stale for ad-hoc work with no ticket id at all (a different, honest
  "unattributed" case); explicit `ticket_id` field takes precedence over `run_id` inference.
- **`TestLogCacheAccess`**: rejects unknown `cache_level`/`event_type` silently (no raise, no row);
  logs real L1 hit with `query_hash`/`repo_branch_scope`; logs real L2 write with `packet_id`;
  never raises when the sidecar path/directory doesn't exist; never raises when
  `_get_access_log_connection()` itself raises (CLAUDE.md's "monitoring write failure must never
  fail the workflow" hard rule, directly tested); `read_cache_access_log()` returns `[]` on a
  never-migrated DB, orders by `ts`.
- **`TestCacheAccessLogInstrumentation`**: the 4 real call sites
  (`write_provider_result_cache`/`record_provider_result_cache_hit`/
  `write_context_packet_cache`/`record_context_packet_cache_hit`) each produce a real access-log
  row through the actual cache read/write path (not just `log_cache_access()` called directly); a
  bare `check_provider_result_cache()` lookup logs nothing (DD9 Non-collapse rule); a direct test
  that a parent row's `hit_count` really is wiped to 0 by a repeat `INSERT OR REPLACE` write while
  the access log still retains the full 4-event history — the concrete motivating gap from the
  ticket's own Request Summary, proven, not just asserted.

## `tests/tools/test_generate_retro.py`

- `compute_kgmcp_cache_efficiency_metrics()`: empty input -> `NO DATA`; search activity with zero
  cache events -> `NOT IN USE`; real hit/write counts and reuse rate; repeated-refetch detection
  within/outside the window; dead-write detection (including the "last write, no subsequent event"
  case); `unattributed` bucketing for missing ticket/agent; `stale_attribution_count`; has a
  `derivation` field; never touches `CACHE_DB_PATH`/`_get_connection`/`_get_access_log_connection`
  (pure-function guard, mirroring the file's existing purity-test convention).
- `compute_retro_metrics()`: `skill_usage`/`kgmcp_cache_efficiency` populated when `tools`/
  `kgmcp_access_log` supplied; the documented-keys test updated to include both new keys.
- `generate()`: reads `su`/`kce` from `compute_retro_metrics()`'s own dict, not a second
  `build_skill_usage_section()` call (monkeypatch call-count regression guard); "## KGMCP Cache
  Efficiency" always renders, even on empty input; renders the real verdict/table with populated
  data.
- The two existing byte-identical fixed-corpus report tests updated to include the new,
  always-rendered section's real text (captured directly from a real `generate()` call against the
  fixture, not hand-typed).

## `tests/tools/test_agent_ops_dashboard_stats.py`

- `skill_usage` populated from real `tools.jsonl` Skill-tool rows via a real `DashboardCache`
  instance; empty when no Skill calls exist.
- `kgmcp_cache_efficiency` populated from a monkeypatched `read_cache_access_log()` (the real
  function reads a fixed relative path, not `DashboardCache`'s own `repo_root` — see plan.md's
  Assumptions) with real hit/write/reuse-rate/verdict values; `NO DATA` verdict on an empty log.
- Source-text anti-drift guard: `ingest.py` imports `read_cache_access_log` from `retrieval_cache`,
  never redefines it.

## Frontend (`dashboard-frontend/src/test/StatsView.test.tsx`, `App.test.tsx`)

- `makeAgentStats()`'s fixture (and `App.test.tsx`'s separate inline fixture) extended with real
  `skill_usage`/`kgmcp_cache_efficiency` shapes — both required fields, TypeScript would reject an
  incomplete object.
- New tests: Skill Usage section renders real per-skill counts and an empty state; KGMCP section
  renders the real verdict text, headline stat tiles, and per-ticket/per-agent rows; a `NOT IN USE`
  verdict renders distinctly (real coverage numbers in the explanation text, not a generic string).

## Real, non-mocked verification actually run (not merely described)

1. `python3 -c "... rc.write_provider_result_cache(...); rc.record_provider_result_cache_hit(...)"`
   against a real tmp-path SQLite DB with a real `.claude/current_run`-shaped sidecar file ->
   confirmed 2 real access-log rows with correct attribution.
2. `python3 -c "print(rc.read_current_run_sidecar())"` against this session's REAL, unmodified
   `.claude/current_run` -> confirmed `sidecar_stale: True` for the real, live
   `TCK-20260817-HOTFIX-DECISION-TRACE-SELECTED-MOCK-SCORE` (already in `tickets/done/`) sidecar.
3. `python3 tools/agent-monitoring/generate_retro.py --all` against the real 1149-run,
   6829-event, 121207-tool-row corpus -> real `RETRO-ALL.md` with a real `NOT IN USE` verdict (0
   cache events vs. 2605 real search calls) and a real, non-empty Skill Usage table (245 total
   invocations).
4. `DashboardCache().get_agent_monitoring_stats(all_time=True)` called directly against the real
   repo -> `skill_usage.total_skill_invocations == 245`, `kgmcp_cache_efficiency.verdict == "NOT IN
   USE"`.
5. Real `uvicorn src.api.agent_ops_dashboard.main:app` process started, `GET
   /api/stats/agent-monitoring` fetched via `curl` -> confirmed both new top-level JSON keys
   present with the same real, non-fabricated values as step 4, proving the full HTTP path (not
   just direct Python calls).
6. `npm run build` (Vite production build) and `npx tsc -b` -> both clean, no type errors.
7. `npx vitest run` (full frontend suite, 15 files) -> 145/145 passing after fixing a fixture gap
   this ticket's new required model fields exposed in `App.test.tsx`'s own separate inline mock.
8. No real browser was loaded to visually confirm the Stats tab — disclosed honestly (no browser
   automation tool available to this agent in this environment); verification instead relies on
   real backend HTTP data (step 5) plus real jsdom component-render tests (step 7), which is
   real proof the two sections render with real data, short of an actual pixel-level visual check.

## Full scoped-suite run at completion

`pytest tests/tools/test_retrieval_cache.py tests/tools/test_generate_retro.py
tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_api.py
tests/tools/test_agent_ops_dashboard_glossary.py tests/tools/test_skill_usage_metric.py` — 316
passed, 0 failed. `npx vitest run` (dashboard-frontend) — 145 passed, 0 failed.
