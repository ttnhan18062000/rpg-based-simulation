---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL
artifact_type: plan
tags: [agent-monitoring, mcp]
---

# Implementation Plan — TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL

## Summary

Remove the dead KGMCP Level 1/Level 2 provider-result and context-packet cache chain that the
Knowledge Gateway MCP deprecation orphaned: the six dead cache functions and the
`log_cache_access`/`read_cache_access_log` access-log chain in `tools/retrieval_cache.py`, the
retro's KGMCP Cache Efficiency machinery in `generate_retro.py`, and — per the repository owner's
final decision on the ticket's one open design question — a full-stack removal (Option A) of the
`kgmcp_cache_efficiency` field and its 5 supporting model classes from `src/api/agent_ops_dashboard/`
and the React dashboard (`dashboard-frontend/`). `migration_001_add_level1_tables` and
`migration_005_add_cache_access_log_table` are retained as pure, standalone, still-tested schema
functions (no production caller survives, but they remain as append-only migration history, same
treatment as every other migration in this file). The broader family of functions that also lose
their only production caller as a side effect (`provider_result_cache_stats`,
`context_packet_cache_stats`, `migration_002/003/004`, both `_get_level{1,2}_connection`/
`_ensure_level{1,2}_schema_for_read` pairs, both `*Lookup` dataclasses, `read_current_run_sidecar`)
is explicitly left standing — not in this ticket's Scope, and expanding into it would be scope
creep beyond what the ticket asked for. Work proceeds in dependency order: verify → remove
production code → remove/update tests → remove retro machinery → remove/update retro tests →
remove the API/UI surface → update the parity ledger → update docs → final full-lane verification.

## Steps

### Step 1 — Final pre-delete consumer re-verification
**Files:** none changed (verification only).
**Change:** Re-run the whole-repo greps investigation.md already ran, immediately before starting
deletions, to catch any drift from other concurrent sessions since 2026-09-10:
- Confirm zero production (non-test, non-docstring) callers remain for `check_provider_result_cache`,
  `write_provider_result_cache`, `record_provider_result_cache_hit`, `check_context_packet_cache`,
  `write_context_packet_cache`, `record_context_packet_cache_hit` outside
  `tools/retrieval_cache.py` itself.
- Confirm `read_cache_access_log`'s only two live readers are still exactly
  `src/api/agent_ops_dashboard/ingest.py:44` and `tools/agent-monitoring/generate_retro.py:44-51`
  (import) / `:2278` (call site).
- Confirm no other consumer of `GET /api/stats/agent-monitoring` exists besides
  `dashboard-frontend` (grep the literal route path across `.py`/`.ts`/`.tsx`/`.md`).
**Do NOT touch:** no files are modified in this step.
**Verify:** Grep output matches investigation.md's confirmed findings exactly. If it doesn't (new
callers appeared), stop and re-scope before proceeding — do not silently absorb new callers into
the deletion.

### Step 2 — Remove the access-log chain from `tools/retrieval_cache.py`
**Files:** `tools/retrieval_cache.py`.
**Change:** Delete, by symbol name (line numbers drift — locate by name):
- The six dead functions: `check_provider_result_cache` (:989-1034), `write_provider_result_cache`
  (:1049-1093), `record_provider_result_cache_hit` (:1096-1114), `check_context_packet_cache`
  (:1181-1226), `write_context_packet_cache` (:1246-1315), `record_context_packet_cache_hit`
  (:1318-1336) — confirmed exact via `investigation.md`'s "Current Behavior" section, re-verified
  at Step 1.
- `log_cache_access()` (:640-697) and `read_cache_access_log()` (:700-722).
- `_get_access_log_connection()` (:627-637). Read directly (`tools/retrieval_cache.py:627-637`):
  its docstring states it is called only to open a connection for `log_cache_access()`, and it is
  itself called from nowhere else in production code (confirmed by investigation.md's "Current
  Behavior": "is itself called only from `log_cache_access()`"). Once `log_cache_access()` is
  deleted, this private (`_`-prefixed) helper has zero callers anywhere and is not part of the
  broader orphaned-family list this plan deliberately leaves standing (that list — see Scope
  Guards — names `_get_level1_connection`/`_get_level2_connection`, not
  `_get_access_log_connection`). It is scoped as part of "the access-log write/read chain" the
  ticket's own title and Scope item name, not the separate Level 1/Level 2 cache family.
- Do NOT delete `read_current_run_sidecar()` (:557-626), even though it loses its only production
  caller (`log_cache_access()`) in this step. It is deliberately retained — see Unresolved
  Questions resolution #1 below and Scope Guards. `tests/tools/test_retrieval_cache.py`'s
  `TestReadCurrentRunSidecar` (:1569-1674) continues to call it directly and must keep passing
  unmodified.
**Do NOT touch:** `migration_001_add_level1_tables` (:271-323), `migration_005_add_cache_access_log_table`
(:445-506) — both retained as code, per ticket Out of Scope and Unresolved Question #2 resolution
below. `migration_002/003/004`, `_get_level1_connection`/`_get_level2_connection`,
`_ensure_level1_schema_for_read`/`_ensure_level2_schema_for_read`, `ProviderResultCacheLookup`/
`ContextPacketCacheLookup`, `provider_result_cache_stats()`, `context_packet_cache_stats()` — all
left standing per Unresolved Question #1 resolution. The live, unrelated 3-level index/query/packet
cache (`check_index_cache`/`check_query_cache`/`check_packet_cache`, `write_*` counterparts,
`HIT`/`MISS`/`STALE_REJECTED`, `INDEX_CACHE_CATEGORY`/`QUERY_CACHE_CATEGORY`/`PACKET_CACHE_CATEGORY`)
— do not touch despite superficially similar `check_*_cache`/`write_*_cache` naming.
`open_connection_with_limits` (consumed by `tools/write_path_guard.py`) — untouched.
**Verify:** `python3 -c "import tools.retrieval_cache"` (or the module's existing import path)
succeeds with no leftover reference to the deleted names. Full test-suite verification happens in
Step 3 after test files are updated to match (the module will not import cleanly under the old test
file until Step 3 lands, so these two steps are tightly coupled and should land in the same commit
if the pipeline requires a green test gate at each step).

### Step 3 — Update `tests/tools/test_retrieval_cache.py`
**Files:** `tests/tools/test_retrieval_cache.py`.
**Change:** Read directly (`tests/tools/test_retrieval_cache.py`, `grep -n "^class Test"` at plan
time) to get the exact, current class boundaries — the ticket's own cited line numbers have drifted
from the actual file structure; the following mapping is fact-checked against the real file, not
the ticket's approximate ranges:
- Remove `TestProviderResultCache` (:625-759) — tests the 3 deleted provider-result functions.
- Remove `TestMigration003` (:760-826) — explicitly named in the ticket's own Scope text for
  removal (this is a settled ticket decision, not part of the broader-family open question, even
  though the underlying `migration_003_add_redaction_policy_version_column()` function itself is
  left standing per Unresolved Question #1 — see Anti-Drift Notes).
- Remove `TestProviderResultCacheStats` (:1179-1196) — same: explicitly named in ticket Scope,
  removed even though `provider_result_cache_stats()` itself is left standing.
- Remove `TestContextPacketCache` (:1263-1450) — this is the "Level 2 classes (:1264-1420)" the
  ticket's Scope names (confirmed match: real boundaries 1263-1450 vs. ticket's approximate
  1264-1420); tests the 3 deleted context-packet functions.
- Remove `TestLogCacheAccess` (:1675-1759) and `TestCacheAccessLogInstrumentation` (:1760-1832) —
  both test `log_cache_access()`/`read_cache_access_log()` and the 6 deleted functions' access-log
  instrumentation directly. Correction to the ticket's own citation: the ticket's Scope text cites
  only "the access-log tests (:1766-1819)," which maps to `TestCacheAccessLogInstrumentation` alone
  — `TestLogCacheAccess` (starting 91 lines earlier, at :1675) also directly exercises
  `log_cache_access`/`read_cache_access_log` by name and must be removed too, or the file fails to
  import (`AttributeError` on `rc.log_cache_access`). Both are within the ticket's stated intent
  ("remove ... the access-log tests"); this is a line-range correction, not a scope expansion.
- Remove the now-dead module-level test helper `_write_row()` (:609-624, immediately before
  `TestProviderResultCache`). Confirmed by grep (`grep -n "_write_row("
  tests/tools/test_retrieval_cache.py`): every call site is inside the five classes removed above
  (`TestProviderResultCache`, `TestMigration003`, `TestProviderResultCacheStats`,
  `TestLogCacheAccess`, `TestCacheAccessLogInstrumentation`) — none remain in a kept class, so it
  becomes dead code and must go with them.
- Do NOT remove `_write_level2_row()` (:1245-1262) or `_write_sidecar()` (:1473-1488) — both are
  still used by classes this plan keeps standing (`_write_level2_row` by
  `TestContextPacketCacheStats` at :1461-1462; `_write_sidecar` by `TestReadCurrentRunSidecar` at
  :1578-1661). Confirmed by grep — do not delete these helpers even though some of their other call
  sites (inside the classes removed above) disappear.
- In `TestMigration005CacheAccessLog` (:1489-1568), remove only the 6th test,
  `test_migration_005_never_called_from_check_or_write_functions` (:1558-1567) — it imports the 6
  deleted function names by reference and will `AttributeError` otherwise. Keep the other 5 tests
  (`test_migration_applies_cleanly_to_a_fresh_database`, `test_migration_is_idempotent_when_run_twice`,
  `test_migration_stamps_generation_table_with_version_3`,
  `test_migration_does_not_touch_existing_marker_only_or_level1_tables`,
  `test_access_log_column_set_matches_documented_shape`) unchanged — read directly
  (`tests/tools/test_retrieval_cache.py:1490-1557`) confirms each calls
  `rc.migration_001_add_level1_tables(conn)` then `rc.migration_005_add_cache_access_log_table(conn)`
  directly via a raw `rc._get_connection()`, never through `_get_access_log_connection()` or
  `log_cache_access()` — these 5 tests already satisfy the ticket's Acceptance Criterion "migration_005
  still works — proven by a test exercising the migration path." No new test is needed for this AC.
**Do NOT touch:** `TestIndexCache` (:63-105), `TestQueryCache` (:106-141), `TestPacketCache`
(:142-173), `TestMayListEnforcement`, `TestStaticGuards`, `TestPrune`, `TestMigrations` (:327-518,
exercises `migration_001` directly via raw SQL, stays valid), `TestRetrievalVersionAndManifest`,
`TestCrashRecovery` (:533-624, INFRA-341's evidence, calls `migration_001_add_level1_tables()`
directly), `TestLevel2Migrations` (:827-1178, tests `migration_002`, INFRA-346's evidence — left
standing per Unresolved Question #1), `TestMigration004` (:1197-1262, left standing, same reason),
`TestContextPacketCacheStats` (:1451-1488, tests `context_packet_cache_stats()`, left standing),
`TestReadCurrentRunSidecar` (:1569-1674, left standing).
**Verify:**
```
pytest tests/tools/test_retrieval_cache.py -v
```
All retained classes pass; no `AttributeError`/`ImportError` on any deleted name.

### Step 4 — Update `tests/tools/test_evidence_cache_identity_contract.py`
**Files:** `tests/tools/test_evidence_cache_identity_contract.py`.
**Change:** In the two loops at :120-124 and :165-168 (per ticket Scope and test_plan.md's "New
Tests Required" — read directly to confirm exact tuple contents before editing), drop
`"check_provider_result_cache"` from both tuples. The remaining three names
(`check_index_cache`, `check_query_cache`, `check_packet_cache`) are the live, unrelated 3-level
cache's lookup functions and must stay unchanged.
**Do NOT touch:** the file's other in-scope-adjacent-but-out-of-scope content —
`_IDENTITY_CONTRACT_MD`, `_MIGRATION_PLAN_MD`, and the other file reads under
`docs/engine/contracts/knowledge_gateway_mcp/` (:30-33) — that doc directory is explicitly retained
per the ticket's Out of Scope. Edit only the two named tuples; do not do a full-file rewrite that
risks perturbing these adjacent, still-valid assertions.
**Verify:**
```
pytest tests/tools/test_evidence_cache_identity_contract.py -v
```

### Step 5 — Remove the retro's KGMCP Cache Efficiency machinery from `generate_retro.py`
**Files:** `tools/agent-monitoring/generate_retro.py`.
**Change:** Read directly and confirmed exact (offsets from today's re-verification, correcting the
ticket's own approximate figures):
- Delete `KGMCP_REFETCH_WINDOW_SECONDS` (:703), `_kgmcp_access_log_group_key()` (:706-709),
  `_kgmcp_verdict()` (:712-~800), `compute_kgmcp_cache_efficiency_metrics()` (:803-1011, ending
  immediately before `compute_retro_metrics` starts at :1014 — the ticket's cited `:1015` is off by
  one function boundary).
- In `compute_retro_metrics()` (:1014-1013+N): remove the `kgmcp_access_log=None` keyword parameter
  from its signature and the `"kgmcp_cache_efficiency": compute_kgmcp_cache_efficiency_metrics(...)`
  key from its returned dict (:1299-1301, confirmed the sole wiring point of this function — no
  other production caller exists).
- In `generate()` (:1565-…): remove the `kgmcp_access_log=None` keyword parameter, the
  `kgmcp_access_log=kgmcp_access_log` pass-through to `compute_retro_metrics()`, the `kce =
  metrics["kgmcp_cache_efficiency"]` local (:1607), and the `## KGMCP Cache Efficiency` render block
  — confirmed real boundaries :2121-2214 (not the ticket's approximate :2121-2148, which is only the
  heading + verdict callout; the real block continues through the summary table, `### Per-Ticket`,
  `### Per-Agent`, `### Repeated Refetches`, `### Dead Writes` subsections and the derivation footer,
  ending immediately before the unrelated `## Skill Usage` heading at :2216).
- In `main()` (:2267-…): remove the `all_kgmcp_access_log = read_cache_access_log()` call (:2278)
  and the `kgmcp_access_log=all_kgmcp_access_log` argument passed into `generate()` (:2305-2308).
- Drop `read_cache_access_log` from the `from retrieval_cache import (...)` block at
  `generate_retro.py:44-51` — confirmed that block's other 6 names (`HIT`, `MISS`,
  `STALE_REJECTED`, `INDEX_CACHE_CATEGORY`, `QUERY_CACHE_CATEGORY`, `PACKET_CACHE_CATEGORY`) belong
  to the live, unrelated 3-level cache and must stay in the import.
**Do NOT touch:** every other section-computing function in this file (`compute_retrieval_metrics`,
`compute_shadow_baseline_comparison`, `compute_tool_safety_metrics`,
`compute_search_investigation_trend`, `compute_parity_index_readpath_call_count`,
`build_skill_usage_section`, `compute_zero_invocation_skill_flags`) and their render blocks —
confirmed by reading the file that the `## Parity Index Read-Path Usage` and `## Skill Usage`
blocks sit immediately adjacent to the deleted block and must not shift or be touched beyond the
KGMCP block's own removal.
**Verify:** `tests/tools/test_generate_retro.py` (Step 6) exercises this; also confirm by direct
read that after this step, `read_cache_access_log` has zero remaining readers anywhere in the repo
outside `tests/` — satisfying the ticket's own "once no reader remains" condition for having removed
`log_cache_access`/`read_cache_access_log` in Step 2.

### Step 6 — Update `tests/tools/test_generate_retro.py`
**Files:** `tests/tools/test_generate_retro.py`.
**Change:**
- Remove `compute_kgmcp_cache_efficiency_metrics` from the `from generate_retro import (...)` block
  (:25) and every kgmcp-referencing test (confirmed 78 case-insensitive `kgmcp` matches in the file
  today via `grep -c` — the ticket's own cited count of 66 has drifted; locate by name/content at
  implementation time, don't rely on either count). This includes the dedicated
  `test_compute_kgmcp_cache_efficiency_metrics_*` test group (`:2706` onward) and any
  kgmcp-referencing assertions embedded in other tests (e.g. tests constructing a
  `kgmcp_access_log=` argument to `generate()`/`compute_retro_metrics()`/`main()`).
- Regenerate `_FIXED_CORPUS_EXPECTED_REPORT` (:1217) — the golden fixture consumed by
  `test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` (:1346, also
  referenced at :1803 — INFRA-379's cited test evidence) — by calling the real, post-removal
  `generate()` against the existing `_FIXED_CORPUS_RUNS`/`_FIXED_CORPUS_EVENTS` fixtures and
  capturing its actual output. Do not hand-edit the existing golden string. Diff the regenerated
  text against the pre-change golden text and confirm the *only* difference is the disappearance of
  the `## KGMCP Cache Efficiency` block (:2121-2214 per Step 5) — no stray blank line left behind at
  the boundary, and nothing in the surrounding `## Parity Index Read-Path Usage`/`## Skill Usage`
  sections shifts unexpectedly.
**Do NOT touch:** every non-kgmcp test in this file — `compute_retrieval_metrics`,
`compute_shadow_baseline_comparison`, `compute_tool_safety_metrics`,
`compute_search_investigation_trend`, `compute_parity_index_readpath_call_count`,
`build_skill_usage_section`/`compute_zero_invocation_skill_flags` tests, and
`test_normalize_phase_agent_and_flag_outliers_untouched` (an unrelated source-hash guard) — all stay
unmodified. INFRA-379's own parity-ledger `test_path` entry does not change (same test file/name);
only the fixture content inside the test changes.
**Verify:**
```
pytest tests/tools/test_generate_retro.py -v
```
All non-kgmcp tests pass unmodified; the golden-fixture test passes against the regenerated
`_FIXED_CORPUS_EXPECTED_REPORT`.

### Step 7 — Full-stack Option A removal (`src/api/agent_ops_dashboard/`, `dashboard-frontend/`)
**Files:** `src/api/agent_ops_dashboard/models.py`, `src/api/agent_ops_dashboard/ingest.py`,
`dashboard-frontend/src/api.ts`, `dashboard-frontend/src/views/StatsView.tsx`,
`dashboard-frontend/src/test/StatsView.test.tsx`, `dashboard-frontend/src/test/App.test.tsx`.
**Change:** Per the repository owner's final decision (Option A — full removal, not open for
reconsideration):
- `models.py`: delete `KgmcpCacheTicketStats`, `KgmcpRepeatedRefetchEntry`, `KgmcpDeadWriteEntry`,
  `KgmcpCoverageStats`, `KgmcpCacheEfficiencyStats` (confirmed by direct read,
  `src/api/agent_ops_dashboard/models.py:218-272`, including the "KGMCP Cache Efficiency" comment
  block immediately preceding them) and drop the `kgmcp_cache_efficiency:
  KgmcpCacheEfficiencyStats` field from `AgentMonitoringStats` (confirmed at `models.py:290`, the
  last of 15 fields on that model — the other 14 are untouched by this change).
- `ingest.py`: remove the `from retrieval_cache import read_cache_access_log` import (confirmed at
  `ingest.py:44`), the 5 `Kgmcp*` imports from `.models` (confirmed at `ingest.py:66-70`), the
  `kgmcp_access_log=read_cache_access_log()` argument to `compute_retro_metrics(...)` inside
  `DashboardCache.get_agent_monitoring_stats()` (confirmed at `ingest.py:874-880`), and the
  `kgmcp_cache_efficiency=KgmcpCacheEfficiencyStats(...)` field construction in that method's
  `AgentMonitoringStats(...)` return (confirmed at `ingest.py:931-962`, field-for-field unpacking
  from `metrics["kgmcp_cache_efficiency"]`). **Other writers/readers to note:** `get_agent_monitoring_stats()`
  is a read-only in-memory-cache rebuild method (module docstring: "never writes to tickets/**,
  agent-monitoring/*.jsonl, or any other durable source"); the other 14 fields in its
  `AgentMonitoringStats(...)` return statement are interleaved in one large return (confirmed at
  `ingest.py:895-963`) — edit only the `kgmcp_cache_efficiency=...` block, leave the other 14
  field constructions byte-identical. `main.py:103-109`'s `GET /api/stats/agent-monitoring` route
  registration itself needs no change — it returns whatever shape `AgentMonitoringStats` now has.
- `dashboard-frontend/src/api.ts`: delete the 5 `Kgmcp*` TypeScript interfaces (confirmed at
  `api.ts:230-277`: `KgmcpCacheTicketStats`, `KgmcpRepeatedRefetchEntry`, `KgmcpDeadWriteEntry`,
  `KgmcpCoverageStats`, `KgmcpCacheEfficiencyStats`) and the `kgmcp_cache_efficiency:
  KgmcpCacheEfficiencyStats` field from the `AgentMonitoringStats` interface (confirmed at
  `api.ts:292`, last of 15 fields — matches `models.py`'s shape exactly).
- `dashboard-frontend/src/views/StatsView.tsx`: remove the `type KgmcpCacheTicketStats` import
  (confirmed at `StatsView.tsx:9`), the local `interface KgmcpTicketRow` (:168-172), the
  `kgmcpTicketRows()` helper (:175-179), the `kgmcpVerdictColorClass()` helper (:185-195), and the
  rendered `<div data-testid="stats-section-kgmcp-cache-efficiency">` section (confirmed spanning
  roughly :514-601 — the verdict callout `data-testid="kgmcp-verdict"`, 6 `StatTile`s, and the
  conditional `kgmcp-per-ticket-table`/`kgmcp-per-agent-table` tables). Confirmed by grep that
  `kgmcpTicketRows`/`kgmcpVerdictColorClass` have no call sites outside this section (lines 522,
  558, 583 — all inside the block being removed), so both helpers become dead code and must be
  deleted with it, not left orphaned.
- `dashboard-frontend/src/test/StatsView.test.tsx`: remove all 14 `kgmcp`-referencing lines
  (confirmed via `grep -n kgmcp`: lines 61, 65, 199, 406, 408, 409, 412, 413, 419, 433, plus
  surrounding fixture/assertion lines in the same blocks) — the fixture objects that build
  `kgmcp_cache_efficiency: {...}` mock data and the assertions against
  `stats-section-kgmcp-cache-efficiency`/`kgmcp-verdict`/`kgmcp-per-ticket-row-*`/
  `kgmcp-per-agent-row-*` test IDs.
- `dashboard-frontend/src/test/App.test.tsx`: remove the `kgmcp_cache_efficiency: {...}` fixture
  object (confirmed at `App.test.tsx:86`) from whatever mocked `AgentMonitoringStats` response it's
  part of — required so the mocked response still type-checks against the now-smaller
  `AgentMonitoringStats` interface.
**Do NOT touch:** any other field in `AgentMonitoringStats` (`run_summary` through `skill_usage` on
both the Python and TypeScript sides), any other `StatsView.tsx` section (Skill Usage, Ticket
Corpus, etc. — confirmed the `## Ticket Corpus` section begins immediately after the removed block,
at the same indentation level, and must be left exactly as-is), `main.py`'s route registration
itself, and every other `dashboard-frontend/src/test/*.test.tsx` file (confirmed only
`StatsView.test.tsx` and `App.test.tsx` reference `kgmcp` anywhere).
**Verify:**
```
pytest tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_api_boundary.py \
       tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -v
```
(after Step 8 removes the now-obsolete kgmcp-specific tests from `test_agent_ops_dashboard_stats.py`
— these two steps are tightly coupled, same as Steps 2/3)
```
cd dashboard-frontend && npm test
```

### Step 8 — Update `tests/tools/test_agent_ops_dashboard_stats.py`
**Files:** `tests/tools/test_agent_ops_dashboard_stats.py`.
**Change:** Remove the 3 kgmcp-specific tests, confirmed present by name at these exact locations
(`grep -n "def test_stats_endpoint_.*kgmcp\|def test_stats_endpoint_uses_real_read_cache_access_log"`):
`test_stats_endpoint_includes_kgmcp_cache_efficiency_from_real_access_log` (:321-352),
`test_stats_endpoint_kgmcp_cache_efficiency_empty_access_log_returns_no_data_verdict` (:355-368),
`test_stats_endpoint_uses_real_read_cache_access_log_not_reimplemented` (:371-378) — all three
assert on a field this ticket deletes and will fail with `AttributeError`/`KeyError` otherwise.
**Do NOT touch:** every other test in this file, e.g.
`test_stats_endpoint_includes_skill_usage_from_real_tools_jsonl`,
`test_stats_endpoint_skill_usage_empty_when_no_skill_tool_calls`,
`test_slow_run_and_duration_outlier_carry_active_idle_split` — must keep passing unmodified, and
serve as the scoped-diff proof that `AgentMonitoringStats`'s other 14 fields are unaffected by Step
7's edit to the interleaved return statement. `tests/tools/test_agent_ops_dashboard_api_boundary.py`
— confirmed zero `kgmcp` references — must stay at zero kgmcp coupling; do not add any
kgmcp-specific assertion there even if it seems like a natural boundary check, since that file's own
purpose is general API-boundary shape checks, not this ticket's specific concern.
**Verify:**
```
pytest tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_api_boundary.py \
       tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -v
```

### Step 9 — Update `docs/parity_ledger/infrastructure.yaml`'s INFRA-343 and INFRA-379
**Architecture-Review finding, fixed here**: the original submission of this plan updated only
INFRA-343 and explicitly listed INFRA-379 under Step 9's "Do NOT touch" list on the reasoning that
"its `test_path` does not change." That reasoning checked only the `test_path` field. Independently
re-verified directly against `docs/parity_ledger/infrastructure.yaml`: INFRA-379's entire `text`
and `v2_evidence` describe the `compute_kgmcp_cache_efficiency_metrics()`/`_kgmcp_verdict()`
docstring-caveat feature this ticket's Step 5 deletes wholesale — `v2_evidence` cites
`generate_retro.py:783-846`, `:994-997`, `:1573-1576` (all inside code Step 5 removes) and 4 named
tests (`test_compute_kgmcp_cache_efficiency_metrics_coverage_rate_window_matched_via_all_tools`,
`test_compute_kgmcp_cache_efficiency_metrics_coverage_rate_never_capped_even_when_over_one`,
`test_compute_retro_metrics_threads_all_tools_into_coverage_denominator`,
`test_generate_kgmcp_coverage_uses_all_tools_denominator_not_period_scoped_tools` — all four removed
by Step 6's own "remove ... the dedicated `test_compute_kgmcp_cache_efficiency_metrics_*` test
group ... and any kgmcp-referencing assertions embedded in other tests"). INFRA-379 is in the same
situation as INFRA-343 and requires the same same-session update, per CLAUDE.md's Authoritative
Mechanics Rule. Added to this step below.

**Files:** `docs/parity_ledger/infrastructure.yaml` (write via `tools/parity_ledger_writer.py`, never
a raw `Edit`).
**Change:** `tools/parity_ledger_writer.py` has no CLI — confirmed by reading the file
(`tools/parity_ledger_writer.py:90-119`): it exposes one function, `write_entry(shard_filename: str,
entry: dict, ledger_dir=None, db_path=None) -> dict`, which validates the full entry then **upserts
by replacing the whole entry** (`entries[index] = entry`, not a field-level merge — confirmed at
`parity_ledger_writer.py:103-106`). The implementer must therefore construct the **complete** updated
INFRA-343 entry dict (all fields: `id`, `text`, `status`, `priority`, `legacy_evidence`,
`v2_evidence`, `proof_type`, `divergence_note`, `test_path`), preserving every field unchanged except
`v2_evidence`, `test_path`, and `divergence_note`, then call
`write_entry("infrastructure.yaml", updated_entry)` from a one-off Python invocation (e.g.
`python3 -c "from tools.parity_ledger_writer import write_entry; write_entry('infrastructure.yaml', {...})"`
run from repo root with `tools/` on `sys.path`, matching how `.claude/agents/parity-updater.md`
already invokes it).
- Keep `status: unsupported` (confirmed current value at `docs/parity_ledger/infrastructure.yaml:9380`)
  — this entry's claim was already about live wiring into the (permanently deleted) KGMCP gateway,
  which remains false; nothing about this ticket's own removal changes that verdict.
- Set `test_path` to `null` (confirmed current value cites exactly
  `tests/tools/test_retrieval_cache.py::TestProviderResultCache,tests/tools/test_retrieval_cache.py::
  TestMigration003,tests/tools/test_retrieval_cache.py::TestProviderResultCacheStats` at
  `infrastructure.yaml:9382` — all three classes are deleted by Step 3, so this citation must not
  survive).
- Update `v2_evidence` to state plainly that the previously-cited "tested as orphaned, unreachable
  dead code" functions (`check_provider_result_cache`, `write_provider_result_cache`,
  `record_provider_result_cache_hit`, `provider_result_cache_stats`, `_get_level1_connection`,
  `ProviderResultCacheLookup`) named in the prior correction (PR #152) are now deleted (three of the
  six) or retained-but-untested (`provider_result_cache_stats`, `_get_level1_connection`,
  `ProviderResultCacheLookup` — left standing per Unresolved Question #1, but with no test coverage
  left after `TestProviderResultCacheStats`'s removal), and reference this ticket
  (`TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL`) as the change that did so.
- Append a short `divergence_note` addendum (not a full rewrite) noting this correction's date and
  ticket, following the same pattern as the two prior corrections already recorded in this entry's
  `divergence_note`.
- **INFRA-379** (second entry updated by this step, same mechanism): its `text`/`v2_evidence` are
  entirely about the `compute_kgmcp_cache_efficiency_metrics()`/`_kgmcp_verdict()` docstring-caveat
  feature and its `## KGMCP Cache Efficiency` render-block paragraph — all deleted by Step 5. Its
  `v2_evidence` cites 3 now-deleted `generate_retro.py` line ranges (`:783-846`, `:994-997`,
  `:1573-1576`) and 4 now-deleted tests (`test_compute_kgmcp_cache_efficiency_metrics_coverage_rate_
  window_matched_via_all_tools`, `test_compute_kgmcp_cache_efficiency_metrics_coverage_rate_never_
  capped_even_when_over_one`, `test_compute_retro_metrics_threads_all_tools_into_coverage_
  denominator`, `test_generate_kgmcp_coverage_uses_all_tools_denominator_not_period_scoped_tools` —
  all removed by Step 6). Only its `test_path`
  (`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus`, the golden-
  fixture test, unrelated to the caveat feature itself) survives untouched — this is the one field
  the original plan checked, which is why the entry was initially missed. Construct the complete
  updated entry: change `status` from `verified` to `unsupported` (the entire feature this entry
  documents no longer exists — matching the same status this ticket already gives INFRA-343 for the
  identical "feature deleted" situation), set `test_path` to `null` (the golden-fixture test doesn't
  actually prove this entry's own caveat-text claim — it was always an indirect/adjacent citation,
  and with the caveat feature itself gone there is no direct evidence left), rewrite `v2_evidence` to
  state the caveat feature and all 4 of its proof tests were removed by this ticket
  (`TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL`), and append a `divergence_note` addendum
  in the same style as INFRA-343's.
**Do NOT touch:** INFRA-341 (already confirmed unaffected — its cited test calls `migration_001`
directly, never through the deleted functions), INFRA-346 and INFRA-390 (both left as-is per
Unresolved Question #1's resolution — their cited tests, `TestLevel2Migrations` and
`TestReadCurrentRunSidecar::test_scoped_sidecar_wins_over_stale_unscoped_when_both_exist`, are both
untouched by this plan), INFRA-349 (already carries no live-evidence claim). No other
`docs/parity_ledger/*.yaml` file is touched.
**Verify:**
```
pytest tests/tools/test_parity_ledger_writer.py -v
```
Confirm the shard file re-parses as valid YAML and `tools/parity_index.py`'s derived SQLite index
rebuilds cleanly (both happen automatically inside `write_entry()` — confirmed at
`parity_ledger_writer.py:112`).

### Step 10 — Update the two dashboard docs
**Files:** `docs/observability/agent_ops_dashboard_contract.md`,
`docs/guides/agent_ops_dashboard.md`.
**Change:**
- `docs/observability/agent_ops_dashboard_contract.md`: remove the `kgmcp_cache_efficiency:
  KgmcpCacheEfficiencyStats` field-for-field contract text (confirmed present at :73, :82, :89-91)
  and the "KGMCP cache efficiency" UI-subsection description (confirmed present at :312, :317,
  :320-323) — both must be edited to reflect that the field and section no longer exist, consistent
  with Option A.
- `docs/guides/agent_ops_dashboard.md`: remove the "KGMCP cache efficiency" bullet (confirmed
  present at :130) and its cross-reference to the contract doc's `kgmcp_cache_efficiency` field
  (confirmed present at :140).
**Do NOT touch:** `docs/agent-monitoring/schema.md` — confirmed by investigation.md that its
`retrieval_version`/`cache_level`/`cache_status` field docs (:310-327) document the separate,
unrelated general 3-level retrieval cache (`cache_level` documented there as
`index | query | packet`, never `level1_provider_result | level2_context_packet`), not this ticket's
dead chain. `docs/guides/agent_monitoring.md` — confirmed by investigation.md that its `## Report
Sections` table already has no row for "KGMCP Cache Efficiency" (a pre-existing gap predating this
ticket), so no edit is needed there. `docs/engine/contracts/knowledge_gateway_mcp/` — explicitly
retained per ticket Out of Scope; do not delete or edit any file under this directory.
**Verify:** Manual read-through confirming no remaining `kgmcp_cache_efficiency`/KGMCP-cache-related
claim in either doc that no longer matches the post-removal code. If `docs/` files changed, run
`make knowledge-index-update` per CLAUDE.md's After Work rule (part of ticket close, not this step
alone, but note it here so Finalize doesn't miss it).

### Step 11 — Final full-lane verification
**Files:** none (verification only).
**Change:** Run every scoped test lane from test_plan.md's "Scoped Pytest Commands" section, plus
the frontend suite, in full:
```
pytest tests/tools/test_retrieval_cache.py tests/tools/test_evidence_cache_identity_contract.py \
       tests/tools/test_generate_retro.py -v

pytest tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_api_boundary.py \
       tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -v

pytest tests/tools/test_parity_ledger_writer.py -v

pytest tests/tools/ -m "not slow"
```
```
cd dashboard-frontend && npm test
```
Also re-run Step 1's greps one final time to confirm zero remaining references anywhere in
production code to any of the 6 deleted functions, `log_cache_access`, `read_cache_access_log`,
`_get_access_log_connection`, `compute_kgmcp_cache_efficiency_metrics`, `KgmcpCacheEfficiencyStats`
(and its 4 sibling classes/interfaces), and `kgmcp_cache_efficiency`.
**Do NOT touch:** nothing new here — this step is pure verification. Never run the bare `pytest
tests/` repo-wide suite (CLAUDE.md Testing Rule).
**Verify:** All commands above exit 0. This step is the final gate for every Acceptance Criterion —
see the Acceptance Criteria Map below.

## Scope Guards

- Do not touch the live, unrelated 3-level index/query/packet cache
  (`check_index_cache`/`check_query_cache`/`check_packet_cache`, their `write_*` counterparts,
  `HIT`/`MISS`/`STALE_REJECTED`, `INDEX_CACHE_CATEGORY`/`QUERY_CACHE_CATEGORY`/`PACKET_CACHE_CATEGORY`,
  and `TestIndexCache`/`TestQueryCache`/`TestPacketCache`) — shares this file and loosely similar
  naming with the dead KGMCP functions; easy to delete the wrong set.
- Do not delete `migration_001_add_level1_tables` or `migration_005_add_cache_access_log_table` —
  both retained as pure, standalone, still-tested schema functions (ticket Out of Scope +
  Unresolved Question #2 resolution below).
- Do not remove `migration_002_add_level2_tables`, `migration_003_add_redaction_policy_version_column`
  (the function itself — its dedicated test class `TestMigration003` IS removed per ticket Scope,
  but the function stays), `migration_004_add_level2_write_path_columns`,
  `_get_level1_connection`/`_get_level2_connection`, `_ensure_level1_schema_for_read`/
  `_ensure_level2_schema_for_read`, `ProviderResultCacheLookup`/`ContextPacketCacheLookup`,
  `provider_result_cache_stats()` (function stays; its test class `TestProviderResultCacheStats` IS
  removed per ticket Scope), `context_packet_cache_stats()`, or `read_current_run_sidecar()` — all
  left standing per Unresolved Question #1's resolution (do not expand this ticket into a second,
  larger cleanup).
- Do not delete `docs/engine/contracts/knowledge_gateway_mcp/` — retained per ticket Out of Scope; a
  live test (`test_evidence_cache_identity_contract.py:30-33`) reads 4 files there.
- Do not touch `docs/agent-monitoring/schema.md` or `docs/guides/agent_monitoring.md` — confirmed by
  investigation.md that neither requires an edit for this ticket, for two distinct reasons (see Step
  10).
- Do not touch `tests/tools/test_agent_ops_dashboard_api_boundary.py` — confirmed zero `kgmcp`
  references; must stay that way.
- Do not touch the three surviving `tools/agent-monitoring/kgmcp_*` measurement tools and their
  fixtures — separately scoped as `TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL`.
- Do not hand-edit `_FIXED_CORPUS_EXPECTED_REPORT` — regenerate it from a real `generate()` call and
  diff (Step 6).
- Do not edit `docs/parity_ledger/infrastructure.yaml` with a raw `Edit`/`Write` — use
  `tools/parity_ledger_writer.py::write_entry()` only (Step 9).

## Dependency Map

- Step 1 (verification) has no dependencies; run first.
- Step 2 (production removal in `retrieval_cache.py`) depends on Step 1's confirmation.
- Step 3 (test updates in `test_retrieval_cache.py`) depends on Step 2 — the module must already
  reflect the new shape before its tests are edited to match; land in the same commit as Step 2.
- Step 4 (`test_evidence_cache_identity_contract.py`) depends on Step 2 (asserts the function is
  gone) but is independent of Step 3 — can run in parallel with Step 3.
- Step 5 (`generate_retro.py` production removal) depends on Step 2 (removes the
  `read_cache_access_log` import it consumes) but is otherwise independent of Steps 3/4.
- Step 6 (`test_generate_retro.py`) depends on Step 5 — land together.
- Step 7 (full-stack Option A removal) depends on Step 5 (removes `compute_kgmcp_cache_efficiency_metrics`,
  which `ingest.py` transitively relies on via `compute_retro_metrics()`) — must land after Step 5,
  otherwise `ingest.py` would still import a function whose caller was just removed leaving a
  half-migrated state. Frontend changes (`api.ts`, `StatsView.tsx`) within Step 7 have no dependency
  on the Python side and could be done in parallel, but are grouped here since they must land
  together as one coherent full-stack change per the ticket's "both sides resolve together" framing.
- Step 8 (`test_agent_ops_dashboard_stats.py`) depends on Step 7 — land together.
- Step 9 (INFRA-343 and INFRA-379) depends on Step 3 (INFRA-343's three cited test classes must
  actually be gone) and Step 6 (INFRA-379's four cited tests must actually be gone) before the
  parity ledger is updated to say so.
- Step 10 (docs) depends on Step 7 (must describe the post-removal API/UI shape accurately).
- Step 11 (final verification) depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| The six dead cache functions and the access-log write/read chain are removed, with no remaining reference from live code. | Steps 2, 5 | Step 1/11 greps; `pytest tests/tools/test_retrieval_cache.py tests/tools/test_generate_retro.py -v` |
| `migration_001_add_level1_tables` is retained and `migration_005` still works — proven by a test exercising the migration path, not by inspection alone. | Step 2 (retention), Step 3 (keeps 5 existing `TestMigration005CacheAccessLog` tests) | `pytest tests/tools/test_retrieval_cache.py::TestMigration005CacheAccessLog -v` |
| The retro no longer emits a KGMCP cache-efficiency section, and `generate_retro.py` runs clean end to end. | Step 5 | `pytest tests/tools/test_generate_retro.py -v` (golden-fixture test, Step 6) |
| `src/api/agent_ops_dashboard/ingest.py`'s resolution is implemented and its reasoning recorded in Implementation Notes. | Step 7 (Option A, decided by repository owner) | `pytest tests/tools/test_agent_ops_dashboard_stats.py -v` (Step 8); implementer records the Option A rationale in the ticket's Implementation Notes section at close |
| INFRA-343 updated via `tools/parity_ledger_writer.py` to reflect that its cited evidence no longer exists. | Step 9 | `pytest tests/tools/test_parity_ledger_writer.py -v` + manual YAML re-read |
| INFRA-379 updated via `tools/parity_ledger_writer.py` — not named in the ticket's own AC text, found by Architecture Review; its entire subject (the KGMCP cache-efficiency caveat text) is deleted by this same ticket. | Step 9 | `pytest tests/tools/test_parity_ledger_writer.py -v` + manual YAML re-read |
| `tests/tools/test_evidence_cache_identity_contract.py` updated; full `tests/tools/` and `tests/api/` lanes pass. | Step 4 | `pytest tests/tools/test_evidence_cache_identity_contract.py -v`; Step 11's `pytest tests/tools/ -m "not slow"` |

## Anti-Drift Notes

- **The `check_*_cache`/`write_*_cache` naming collision is the single biggest risk in this ticket.**
  `tools/retrieval_cache.py` hosts both the dead KGMCP Level 1/Level 2 functions and the live,
  unrelated index/query/packet cache with nearly identical naming conventions. `TestIndexCache`/
  `TestQueryCache`/`TestPacketCache` passing unmodified is the clearest tripwire that the wrong set
  wasn't touched.
- **The ticket's own cited line numbers have all drifted** (confirmed during this plan's fact-check
  pass): `TestProviderResultCache` at :625 not :626, `record_context_packet_cache_hit` at :1318 not
  :1320, `compute_kgmcp_cache_efficiency_metrics` ending at :1011/1014-boundary not :1015, the render
  block ending at :2214 not the ticket's approximate :2148, and — the most material correction — "the
  access-log tests (:1766-1819)" in the ticket's Scope text actually names only
  `TestCacheAccessLogInstrumentation`; `TestLogCacheAccess` (:1675-1759) must also be removed or the
  test file fails to import. Locate everything by symbol name at implementation time, not by line
  number.
- **A subtlety in the ticket's own Scope text, corrected by Architecture Review**: it names
  `TestMigration003` and `TestProviderResultCacheStats` as test classes to remove, even though their
  underlying production functions (`migration_003_add_redaction_policy_version_column`,
  `provider_result_cache_stats`) are *not* being removed (per Unresolved Question #1's resolution
  below). The original version of this note claimed this "leaves those two functions in production
  code with no dedicated unit test afterward," treating both symmetrically — that claim is only true
  for one of them. Independently re-verified via `grep -n
  "migration_003_add_redaction_policy_version_column(" tests/tools/test_retrieval_cache.py`, mapped
  to class boundaries: `migration_003_add_redaction_policy_version_column` is also called directly
  at lines 382 (`TestMigrations`, :327-518) and 942/1038/1064 (`TestLevel2Migrations`, :827-1178) —
  **both classes are kept standing by this plan** (see Do NOT touch, Step 3), so this function
  genuinely retains real test coverage after `TestMigration003` is removed; it does not lose
  coverage at all. `provider_result_cache_stats()`, by contrast, is called only at lines 1181 and
  1188, both inside `TestProviderResultCacheStats` — no other call site exists anywhere in the file
  (line 1457 is a comment mentioning the function, not a call) — so it genuinely does lose all test
  coverage, exactly as the original claim said, just not `migration_003_add_redaction_policy_
  version_column` as well. This is still the ticket's own explicit instruction to remove both test
  classes regardless (confirmed: INFRA-343's `test_path` already cited all three classes as
  jointly-doomed evidence) — do not "fix" the accurate half of this finding (`provider_result_cache_
  stats()`'s real coverage loss) by restoring `TestProviderResultCacheStats` or deleting the function
  either would exceed this ticket's scope in a different direction. Only the stated *reasoning* was
  corrected, not the plan's actions.
- **`_write_row()` and the deleted test classes are tightly coupled** — deleting the 5 classes that
  use it without also deleting the now-dead helper leaves an obviously-orphaned function; deleting
  it without first confirming (via grep, done in Step 3's Change text) that no *kept* class still
  calls it would break `TestProviderResultCacheStats` and friends. Both directions were checked
  before writing this plan.
- **`ingest.py`'s edit is inside a single large interleaved return statement** (:895-963) — 15 fields
  built in one `AgentMonitoringStats(...)` call. Removing the `kgmcp_cache_efficiency=...` block is
  easy to get right in isolation but easy to accidentally perturb an adjacent field while doing it;
  the non-kgmcp tests in `test_agent_ops_dashboard_stats.py` (kept unmodified per Step 8) are the
  proof these 14 other fields are untouched.

## Unresolved Questions — Resolutions

Both open questions the investigation flagged for Plan to resolve are decided below; neither is left
open for Architecture-Review or human input.

**1. The broader orphaned-surface family** (`provider_result_cache_stats()`,
`context_packet_cache_stats()`, `migration_002/003/004`, both `_get_level{1,2}_connection`/
`_ensure_level{1,2}_schema_for_read` pairs, both `*Lookup` dataclasses, `read_current_run_sidecar()`)
— **resolution: leave this family standing**, unchanged in production code, exactly like
`migration_001`/`migration_005`. Reasoning: the ticket's own Scope section names exactly six
functions plus the access-log chain; its Out-of-Scope section protects only `migration_001` by name.
None of this broader family is named anywhere in the ticket's Scope. Per this planner role's own
rule ("Never plan more work than the ticket scope... note adjacent problems as future tickets — do
not add them to this plan"), expanding into this family — which would additionally touch
`TestLevel2Migrations`, `TestMigration004`, `TestContextPacketCacheStats`, and INFRA-346/INFRA-390's
parity-ledger citations — is a materially larger, separate cleanup. It should be filed as its own
follow-up ticket if the team decides this dormant infrastructure isn't worth keeping (mirroring how
`TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL` was already split out as a sibling rather than
folded in here), not decided unilaterally inside this plan.

**2. `migration_005_add_cache_access_log_table`'s own fate** — **confirmed: retained**, exactly as
investigation.md concluded. Reasoning: the ticket's Out-of-Scope text grounds `migration_001`'s
retention explicitly in "`migration_005` assumes [`retrieval_cache_generation`] exists," which only
makes sense if `migration_005` itself also survives as code. The Acceptance Criteria's explicit
requirement that "migration_005 still works — proven by a test" reinforces this: a test proving a
deleted function "still works" would be incoherent. Both `migration_001` and `migration_005` are
retained as pure, standalone, still-tested functions with zero production caller after this ticket
(their only production path, `log_cache_access()` → `_get_access_log_connection()` → `migration_001`
→ `migration_005`, is removed in Step 2) — consistent with treating SQLite migrations as an
append-only historical record, never retroactively deleted once their consuming feature is gone.
`TestMigration005CacheAccessLog`'s 5 surviving tests (Step 3) already call both migrations directly,
satisfying the AC without any new test.

No other question remains open. This plan is ready for Architecture-Review / Implement.

## Review Round 1 (Architecture Review, 2026-09-10)

**Verdict on first submission: NEEDS_CHANGES.** Two findings, both independently re-verified before
accepting:

1. **INFRA-379 was missed.** The original Step 9 updated only INFRA-343 and explicitly listed
   INFRA-379 under "Do NOT touch," reasoning that its `test_path` doesn't change. That check missed
   that INFRA-379's entire `text`/`v2_evidence` describe the KGMCP cache-efficiency caveat-text
   feature this ticket's Step 5/6 delete wholesale, including 4 named tests Step 6 removes. Fixed:
   INFRA-379 added to Step 9 (status `verified` → `unsupported`, `test_path` → `null`, `v2_evidence`
   rewritten), the Dependency Map and Acceptance Criteria Map both updated to reflect the addition.
2. **The Anti-Drift Notes' migration_003 claim was factually wrong.** The original note claimed
   `migration_003_add_redaction_policy_version_column` loses all test coverage once `TestMigration003`
   is removed, symmetrically with `provider_result_cache_stats()`. Independently re-verified via
   `grep`: `migration_003_add_redaction_policy_version_column` is also called directly by
   `TestMigrations` and `TestLevel2Migrations`, both of which this plan already keeps standing — it
   does not lose coverage. Only `provider_result_cache_stats()` genuinely loses all coverage (its
   only call sites are inside the removed `TestProviderResultCacheStats`). Fixed: the Anti-Drift Note
   corrected to state this precisely — no change to which test classes get removed, only to the
   stated reasoning about which underlying function is actually left untested.

Everything else in the plan (Option A full-stack removal, the API-boundary defensibility analysis,
migration_001/migration_005 retention, the broader-orphaned-family scope decision, all sampled
line-number/class-boundary claims) was independently re-verified against the real repo files and
confirmed accurate — no other changes required.

## Deviations (Implement, 2026-09-10)

Four small deviations from this plan's literal text, discovered while implementing and running
tests — none expand scope beyond the ticket's own named six functions plus the access-log chain;
all are mechanical fixes required to keep genuinely-kept code/tests self-consistent and green.

1. **Two now-orphaned constants in `tools/retrieval_cache.py` not named by Step 2.**
   `_ACCESS_LOG_VALID_CACHE_LEVELS`/`_ACCESS_LOG_VALID_EVENT_TYPES` (originally :520-521) existed
   solely to validate `log_cache_access()`'s own kwargs. Once `log_cache_access()` was deleted per
   Step 2, these two constants had zero remaining references anywhere in the repo (confirmed by
   grep, including in tests). They sit squarely within "the access-log write/read chain" the
   ticket's own title and Scope item name — not the broader orphaned-surface family Unresolved
   Question #1 deliberately leaves standing — so they were deleted alongside `log_cache_access()`
   rather than left as dead code, consistent with CLAUDE.md's "no half-finished implementations"
   rule. `_CURRENT_RUN_SIDECAR_PATH` (same block) was NOT touched — it is still used by
   `read_current_run_sidecar()`, which Step 2 explicitly retains.

2. **`TestLevel2Migrations::test_check_and_write_functions_now_exist_for_the_new_level2_table`
   (inside a class Step 3 explicitly lists under "Do NOT touch") directly asserted the existence
   of `check_context_packet_cache`/`write_context_packet_cache` and a full module-level
   check_*/write_* name-set including `check_provider_result_cache`/`write_provider_result_cache`
   — all four deleted by Step 2.** This is a real gap in the plan's own class-by-class mapping: it
   verified the *other* four removed classes' contents but did not check whether any *kept* class's
   test bodies referenced the six doomed functions by name. Fixed by rewriting the one test method
   (renamed `test_check_and_write_functions_no_longer_exist_for_the_removed_level2_table`) to
   assert absence instead of presence — restoring its original pre-P3 premise, per its own updated
   docstring — rather than deleting it or leaving the class broken. No other test in this class was
   touched.

3. **`TestContextPacketCacheStats` (also explicitly "left standing" — tests
   `context_packet_cache_stats()`, itself retained per Unresolved Question #1) depends on
   `_write_level2_row()`, whose body called the now-deleted `write_context_packet_cache()`, and on
   `test_context_packet_cache_stats_reflects_real_rows_and_hits` calling the now-deleted
   `record_context_packet_cache_hit()`.** Unlike Level 1 (where the equivalent stats test class,
   `TestProviderResultCacheStats`, is explicitly removed by the ticket's own Scope text, so this
   problem never arises), the ticket's Scope does not remove `TestContextPacketCacheStats` — the
   plan's own Do-Not-Touch list keeps it standing with real, non-trivial row/hit assertions, which
   is only possible if rows can still be created and hit-counted without the deleted functions.
   Fixed by rewriting `_write_level2_row()` to perform the equivalent `INSERT OR REPLACE` directly
   via `rc._get_level2_connection()` (mirroring the exact SQL the deleted `write_context_packet_
   cache()` used to run), and the test's hit-increment to a raw `UPDATE ... SET hit_count =
   hit_count + 1` via `rc._get_connection()`. Neither restores any deleted production function or
   changes what `context_packet_cache_stats()` itself does — only how the test populates its own
   fixture data.
4. **`tests/tools/test_evidence_cache_identity_contract.py`'s explanatory comment (not just the
   tuple Step 4 named) needed updating.** The comment immediately above the second `check_*_cache`
   tuple specifically narrated *why* `check_provider_result_cache` was in the loop ("added post-hoc
   ... by Architecture-Verify's own review of this ticket") — leaving that sentence in place after
   removing the name from the tuple would have been a stale, misleading claim about code that no
   longer exists. Rewrote the comment to state plainly that the function was briefly in the loop
   between TCK-20260816 and this ticket, which removed it.

All four were run through the full scoped test lanes (Step 11) after the fix — 2467 passed / 17
skipped / 28 deselected (slow) / 1 pre-existing xfail across `tests/tools/ -m "not slow"`, plus 145
passed across the frontend `npm test` lane. No production behavior changed as a result of any of
these four fixes — they are test-infrastructure-only corrections.
