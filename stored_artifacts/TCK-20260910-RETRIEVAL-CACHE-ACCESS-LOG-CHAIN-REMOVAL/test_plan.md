---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL
artifact_type: test_plan
tags: [agent-monitoring, mcp]
---

# Test Plan — TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL

## Regression Surface

**Unit — `tools/retrieval_cache.py` (must keep passing, untouched by this ticket):**
- `TestIndexCache` (:63-105), `TestQueryCache` (:106-141), `TestPacketCache` (:142-173) — the
  live, unrelated 3-level index/query/packet cache.
- `TestMayListEnforcement` (:174-228), `TestStaticGuards` (:229-270), `TestPrune` (:271-326).
- `TestMigrations` (:327-518) — general migration-ordinal/idempotency tests; confirmed it exercises
  `migration_001` directly (not via the dead functions), stays valid since `migration_001` is
  retained.
- `TestRetrievalVersionAndManifest` (:519-532).
- `TestCrashRecovery` (:533-624) — confirmed its
  `test_deleted_cache_db_rebuild_does_not_silently_resurrect_level1_payload_rows` test (INFRA-341's
  cited evidence) calls `migration_001_add_level1_tables()` directly via raw SQL, not through any
  of the six dead functions. Must still pass unmodified.
- `TestMigration005CacheAccessLog` (:1489-1568) — **mostly retained**, see New Tests Required below;
  5 of its 6 tests already call `migration_001` then `migration_005` directly (never through
  `_get_access_log_connection()`/`log_cache_access()`), so they already satisfy the "migration_005
  still works, proven by a test" acceptance criterion as-is.
- `TestReadCurrentRunSidecar` (:1569-1674) — tests `read_current_run_sidecar()` directly; stays
  valid regardless of this ticket unless Plan expands scope to remove that function too (see
  investigation.md Risk #2).

**Unit — `tools/agent-monitoring/generate_retro.py` (must keep passing, untouched sections):**
- Everything not `kgmcp`-prefixed: `compute_retrieval_metrics`, `compute_shadow_baseline_
  comparison`, `compute_tool_safety_metrics`, `compute_search_investigation_trend`,
  `compute_parity_index_readpath_call_count`, `build_skill_usage_section`,
  `compute_zero_invocation_skill_flags`, the whole `## Parity Index Read-Path Usage`/`## Skill
  Usage` render blocks that sit immediately adjacent to the block being removed.
- `test_normalize_phase_agent_and_flag_outliers_untouched` — an unrelated source-hash guard, stays
  valid.

**Integration — `src/api/agent_ops_dashboard/`:**
- `tests/tools/test_agent_ops_dashboard_stats.py` — all non-`kgmcp` tests (e.g.
  `test_stats_endpoint_includes_skill_usage_from_real_tools_jsonl`,
  `test_stats_endpoint_skill_usage_empty_when_no_skill_tool_calls`,
  `test_slow_run_and_duration_outlier_carry_active_idle_split`, etc.) must keep passing unmodified.
- `tests/tools/test_agent_ops_dashboard_api_boundary.py` — confirmed zero `kgmcp` references; must
  keep passing unmodified regardless of which `ingest.py` option Plan picks.

**Frontend — `dashboard-frontend/` (vitest, `npm test` = `vitest run`):**
- `dashboard-frontend/src/test/App.test.tsx` — all non-kgmcp-fixture assertions must keep passing;
  the one `kgmcp_cache_efficiency` fixture object at :86 needs updating in step with whichever
  `ingest.py` option is chosen (removed, or replaced with a minimal/null placeholder, to keep the
  mocked response type-checking).
- Every other `dashboard-frontend/src/test/*.test.tsx` file with zero `kgmcp` references
  (confirmed only `StatsView.test.tsx` and `App.test.tsx` reference it) is unaffected.

## New Tests Required

- **Name:** `test_migration_005_still_works_after_log_cache_access_removal` (or fold into
  `TestMigration005CacheAccessLog` as a new method if that class survives, per this ticket's own
  AC).
  **Category:** unit (architecture/regression guard).
  **What it verifies:** the ticket's own AC — "`migration_001_add_level1_tables` is retained and
  `migration_005` still works — proven by a test exercising the migration path, not by inspection
  alone." Concretely: open a fresh `sqlite3.Connection`, call `rc.migration_001_add_level1_tables
  (conn)` then `rc.migration_005_add_cache_access_log_table(conn)` directly (mirroring the existing
  5 surviving tests in `TestMigration005CacheAccessLog`), assert `retrieval_cache_access_log` and
  `retrieval_cache_generation` both exist and are correctly stamped (`retrieval_cache_schema_
  version == 3`). This should be a genuinely new addition only if `TestMigration005CacheAccessLog`'s
  existing 5 tests are judged insufficient by Plan/Architecture-Review — as investigated, they
  already exercise exactly this path with no dependency on `log_cache_access`/`read_cache_access_
  log`, so this may be satisfiable by simply *keeping* those 5 tests rather than writing new ones.
  If kept, only `test_migration_005_never_called_from_check_or_write_functions` (:1558-1567, the
  6th test in that class) needs removal, since it references the deleted function names by import.
  **Where it lives:** `tests/tools/test_retrieval_cache.py::TestMigration005CacheAccessLog`.

- **Name:** `test_no_reference_to_check_or_write_provider_result_or_context_packet_cache_functions`
  (architecture guard, new or folded into an existing `TestStaticGuards`-style class).
  **Category:** architecture guard.
  **What it verifies:** none of the six removed function names (`check_provider_result_cache`,
  `write_provider_result_cache`, `record_provider_result_cache_hit`, `check_context_packet_cache`,
  `write_context_packet_cache`, `record_context_packet_cache_hit`) remain importable from `tools.
  retrieval_cache`, and a repo-wide source grep for each name outside `tests/`/historical
  `stored_artifacts/`/`tickets/done/` prose returns nothing.
  **Where it lives:** `tests/tools/test_retrieval_cache.py` (new function/class) or
  `tests/tools/test_evidence_cache_identity_contract.py` (already the closest existing home for
  "does this function still exist" AST-level assertions — but note that file's own two references
  need to change from *asserting presence* to *asserting absence*, see below).

- **Name:** a rewritten/renamed version of `tests/tools/test_evidence_cache_identity_contract.py`'s
  two loops at :120-124 and :165-168.
  **Category:** unit (existing test, required update — ticket AC item).
  **What it verifies:** both loops currently assert `check_provider_result_cache` is present in
  `tools/retrieval_cache.py`'s AST and carries no freshness/verification leakage in its own source.
  Once the function is deleted, drop `"check_provider_result_cache"` from both tuples (`:120-123`
  and `:165-168`) — the remaining three (`check_index_cache`, `check_query_cache`,
  `check_packet_cache`) are the live, unrelated 3-level cache's lookup functions and must stay.
  **Where it lives:** `tests/tools/test_evidence_cache_identity_contract.py` (existing file, in
  place).

- **Name:** golden-fixture regeneration for
  `test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus`.
  **Category:** unit (existing test, required content update — not new logic, but the fixture
  itself must be regenerated deliberately).
  **What it verifies:** `generate()`'s full rendered Markdown output for `_FIXED_CORPUS_RUNS`/
  `_FIXED_CORPUS_EVENTS` still matches `_FIXED_CORPUS_EXPECTED_REPORT` byte-for-byte — but that
  golden string must be regenerated from a real post-removal `generate()` call (not hand-edited) so
  it no longer contains the `## KGMCP Cache Efficiency` section (real end boundary confirmed at
  :2214, not the ticket's approximate :2148 — see investigation.md).
  **Where it lives:** `tests/tools/test_generate_retro.py` (existing test/fixture, in place).

- **Name:** ingest.py resolution test(s) matching whichever option Plan/Architecture-Review picks
  for `src/api/agent_ops_dashboard/ingest.py`'s `read_cache_access_log` usage.
  **Category:** integration.
  **What it verifies:** depends on the chosen option (see investigation.md's Risks/Open Questions
  #1) — e.g. under full removal (Option A), a test that `AgentMonitoringStats` no longer has a
  `kgmcp_cache_efficiency` field and `GET /api/stats/agent-monitoring` returns cleanly without it;
  under a stub (Option B), a test asserting the endpoint always returns the fixed retired-verdict
  stub regardless of `retrieval_cache.db` state; under Optional-and-null (Option C), a test
  asserting the field is present but `null`. This test's exact shape cannot be finalized until
  Plan/Architecture-Review resolves the design question — flagged here as required, not
  pre-written, per the investigation's instruction not to assume an answer.
  **Where it lives:** `tests/tools/test_agent_ops_dashboard_stats.py`, replacing
  `test_stats_endpoint_includes_kgmcp_cache_efficiency_from_real_access_log` (:321-352),
  `test_stats_endpoint_kgmcp_cache_efficiency_empty_access_log_returns_no_data_verdict` (:355-368),
  and `test_stats_endpoint_uses_real_read_cache_access_log_not_reimplemented` (:371-378).

- **Name:** frontend equivalent of the above, matching the same chosen option.
  **Category:** integration (frontend, vitest).
  **What it verifies:** `StatsView.tsx` either no longer renders `data-testid="stats-section-kgmcp-
  cache-efficiency"` (Option A), always renders a static retired-state banner regardless of API
  response content (Option B), or conditionally omits the section when the field is `null` (Option
  C) — replacing the 14 `kgmcp`-referencing assertions in `StatsView.test.tsx` accordingly, and
  updating `App.test.tsx:86`'s fixture to match the new (or removed) field shape.
  **Where it lives:** `dashboard-frontend/src/test/StatsView.test.tsx`,
  `dashboard-frontend/src/test/App.test.tsx`.

## Scoped Pytest Commands

```
# Retrieval cache module + its two direct dependents' test suites
pytest tests/tools/test_retrieval_cache.py tests/tools/test_evidence_cache_identity_contract.py \
       tests/tools/test_generate_retro.py -v

# Agent Ops Dashboard API surface (backend)
pytest tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_api_boundary.py \
       tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -v

# Parity ledger writer / registry sanity (touched via tools/parity_ledger_writer.py for INFRA-343)
pytest tests/tools/test_parity_ledger_writer.py -v

# Full tools/ regression lane (broader net, still scoped — never pytest tests/)
pytest tests/tools/ -m "not slow"
```

```
# Frontend (dashboard-frontend/), run from that directory
cd dashboard-frontend && npm test
```

Never run the bare `pytest tests/` repo-wide suite per CLAUDE.md's Testing Rule — scope to
`tools/`, `src/api/agent_ops_dashboard/`, and `dashboard-frontend/` as above.

## Anti-Drift Test Guards

- **`TestIndexCache`/`TestQueryCache`/`TestPacketCache` must all still pass unmodified** — the
  clearest tripwire if an implementer accidentally deletes/edits the live, unrelated 3-level
  index/query/packet cache instead of (or in addition to) the dead Level 1/Level 2 KGMCP cache,
  given the superficially similar `check_*_cache`/`write_*_cache` naming pattern.
- **`test_migration_005_never_called_from_check_or_write_functions` must be *removed*, never
  quietly left in place and passing-by-accident** — if the six dead functions are removed but this
  test is forgotten, it will `AttributeError` (import failure on `rc.check_provider_result_cache`
  etc.) rather than silently pass, which is the correct fail-loud behavior, but confirm it's
  actually gone rather than just currently red.
- **`docs/engine/contracts/knowledge_gateway_mcp/` file reads in
  `test_evidence_cache_identity_contract.py` must keep passing untouched** — that test file has
  both in-scope changes (the two `check_provider_result_cache` name-presence assertions) and
  out-of-scope contract-doc reads (`_IDENTITY_CONTRACT_MD`, `_MIGRATION_PLAN_MD`, etc.) in the same
  file; a careless full-file rewrite risks breaking the latter while fixing the former.
- **`_FIXED_CORPUS_EXPECTED_REPORT` must be regenerated from a real call, not hand-trimmed** — a
  guard against silently baking a rendering bug (stray blank line, wrong section-boundary) into the
  new golden fixture; diff the regenerated text against the old one and confirm the *only* change is
  the disappearance of the `## KGMCP Cache Efficiency` block (:2121-2214) and nothing else in the
  surrounding `## Parity Index Read-Path Usage`/`## Skill Usage` sections shifts unexpectedly.
- **Whichever `ingest.py` option is chosen, `AgentMonitoringStats`'s other 14 fields (run_summary,
  gate_failure_breakdown, tag_breakdown_*, tier_distribution, ..., skill_usage) must be provably
  unaffected** — a scoped diff/test confirming `get_agent_monitoring_stats()`'s non-kgmcp fields are
  byte-identical before/after, since this method's own construction (:895-963) interleaves the
  kgmcp block with 13 other fields in one large return statement, and it would be easy to
  accidentally perturb an adjacent field while editing the kgmcp block in place.
- **`tests/tools/test_agent_ops_dashboard_api_boundary.py` (zero kgmcp references today) must stay
  at zero kgmcp coupling** — if implementation work starts adding kgmcp-specific boundary
  assertions there instead of to `test_agent_ops_dashboard_stats.py`, that's a sign the change is
  drifting into that file's actual purpose (general API-boundary shape checks) rather than this
  ticket's specific concern.
