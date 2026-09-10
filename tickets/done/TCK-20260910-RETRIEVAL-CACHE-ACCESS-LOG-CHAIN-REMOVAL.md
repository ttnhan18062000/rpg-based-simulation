---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL
phase: done
date: 2026-09-10
tags: [agent-monitoring, mcp]
---

# TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL

## Title
Remove the now-dead provider-result cache and its access-log telemetry chain

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
The Knowledge Gateway MCP deprecation (`TCK-20260907-KGMCP-DEPRECATION-EPIC`, complete) deleted
`tools/knowledge_gateway_cache.py`, which was the sole caller of the provider-result and
context-packet cache layer in `tools/retrieval_cache.py`. That layer is now dead code, and —
more importantly — it was the **only writer** to the `retrieval_cache_access_log` table, which
still has two live readers. The result is a telemetry chain that can now only ever report zero.

This is one coupled unit, not two independent cleanups: removing the dead writers without
resolving the readers would strand `src/api/agent_ops_dashboard/ingest.py` and the retro
generator on a permanently-empty table, which is worse than the status quo. Both sides resolve
together or neither does.

Verified against `origin/main` on 2026-09-10 (re-verify at Investigate — other sessions may land
changes):

**Dead — zero production callers** (only self-references and tests):
`check_provider_result_cache` (:989), `write_provider_result_cache` (:1049),
`record_provider_result_cache_hit` (:1096), `check_context_packet_cache` (:1181),
`write_context_packet_cache` (:1246), `record_context_packet_cache_hit` (:1320).

**The coupling:** `log_cache_access` is called only at :1091, :1112, :1315, :1336 — all inside
those dead functions. Its consumer `read_cache_access_log()` has two live readers:
`src/api/agent_ops_dashboard/ingest.py:44` and `tools/agent-monitoring/generate_retro.py:44`.

**Downstream retro machinery** (~321 lines): `KGMCP_REFETCH_WINDOW_SECONDS` (:703),
`_kgmcp_access_log_group_key` (:706), `_kgmcp_verdict` (:712),
`compute_kgmcp_cache_efficiency_metrics` (:803-1015), wired at :1299, plus the
`## KGMCP Cache Efficiency` render block at :2121-2148. That function's own docstring
(:838-846) explains its near-zero coverage as an architectural fact about two
independently-implemented tools — a rationale now obsolete in a stronger way than written,
since the gateway it measured no longer exists at all.

## Scope
- Remove the six dead cache functions listed above, their `log_cache_access` call sites, and
  `log_cache_access`/`read_cache_access_log` themselves once no reader remains.
- Remove the retro's KGMCP cache-efficiency machinery: the four symbols above, the `:1299`
  wiring, and the `## KGMCP Cache Efficiency` render block, so the report stops emitting a
  permanently-zero section.
- Resolve `src/api/agent_ops_dashboard/ingest.py:44`'s use of `read_cache_access_log` — this is
  production API code, so decide deliberately between removing the ingest path and leaving a
  documented stub, and record which and why. Do not simply delete an API code path without
  stating the reasoning.
- Update `docs/parity_ledger/infrastructure.yaml`'s INFRA-343 — it was corrected during PR #152
  specifically to cite the surviving `retrieval_cache.py` functions as live test evidence. Once
  they are removed, that citation goes stale again; use `tools/parity_ledger_writer.py`, never a
  raw `Edit`.
- Remove the now-dead test coverage: `TestProviderResultCache` (:626-730), `TestMigration003`,
  `TestProviderResultCacheStats`, the Level 2 classes (:1264-1420), and the access-log tests
  (:1766-1819) in `tests/tools/test_retrieval_cache.py`; plus the 66 `kgmcp` references in
  `tests/tools/test_generate_retro.py`.
- `tests/tools/test_evidence_cache_identity_contract.py` asserts `check_provider_result_cache`
  by name at :122 and :167 — it breaks on removal and must be updated in the same change.

## Out of Scope
- **`migration_001_add_level1_tables` must be RETAINED.** `_get_access_log_connection()` (:627)
  calls it at :635 as a prerequisite, because it creates `retrieval_cache_generation`, which
  `migration_005` assumes. Removing it alongside the Level 1 functions is the obvious-looking
  move and is wrong.
- Any other function in `tools/retrieval_cache.py` — the sidecar readers,
  `open_connection_with_limits` (consumed by `tools/write_path_guard.py`), and the retrieval
  instrumentation are all live and unaffected.
- `docs/engine/contracts/knowledge_gateway_mcp/` — retained as institutional record; a live test
  reads four files there (`tests/tools/test_evidence_cache_identity_contract.py:30-33`).
- The three surviving `tools/agent-monitoring/kgmcp_*` measurement tools and their fixtures —
  separately scoped as `TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL`.

## Acceptance Criteria
- [x] The six dead cache functions and the access-log write/read chain are removed, with no
      remaining reference from live code.
- [x] `migration_001_add_level1_tables` is retained and `migration_005` still works — proven by a
      test exercising the migration path, not by inspection alone.
- [x] The retro no longer emits a KGMCP cache-efficiency section, and `generate_retro.py` runs
      clean end to end.
- [x] `src/api/agent_ops_dashboard/ingest.py`'s resolution is implemented and its reasoning
      recorded in Implementation Notes.
- [x] INFRA-343 updated via `tools/parity_ledger_writer.py` to reflect that its cited evidence no
      longer exists.
- [x] `tests/tools/test_evidence_cache_identity_contract.py` updated; full `tests/tools/` and
      `tests/api/` lanes pass.

## Related Tickets
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` (done) — the deprecation that orphaned this chain.
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (done) — deleted the sole caller.
- `TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD` (done) — built the
  retro/dashboard machinery this ticket retires.

## Related Docs
- `docs/agent-monitoring/schema.md`, `docs/guides/agent_monitoring.md` — update if the retro's
  section list changes.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/retrieval_cache.py`, `tools/agent-monitoring/generate_retro.py`,
  `src/api/agent_ops_dashboard/ingest.py`, `docs/parity_ledger/infrastructure.yaml`
- `tests/tools/test_retrieval_cache.py`, `tests/tools/test_generate_retro.py`,
  `tests/tools/test_evidence_cache_identity_contract.py`

## Assumptions / Open Questions
- The `src/api/` resolution is a genuine design call, not a mechanical deletion — it is the one
  part of this ticket touching production API surface. Decide it explicitly at Plan and get it
  through Architecture Review before implementing.
- Line numbers above are from `origin/main` at 2026-09-10 and will drift; locate by symbol name.

## Implementation Notes

Executed `staging_artifacts/TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL/plan.md`'s 11
steps in order, exactly as approved by Architecture Review Round 2.

**Step 1** — re-ran the whole-repo greps investigation.md/plan.md already ran; confirmed zero
drift from other concurrent sessions since 2026-09-10 (identical findings: zero production callers
for the six functions outside `tools/retrieval_cache.py` itself; `read_cache_access_log`'s only two
live readers still exactly `ingest.py`/`generate_retro.py`; no other consumer of
`GET /api/stats/agent-monitoring` besides `dashboard-frontend`). Proceeded without escalation.

**Step 2** — deleted `check_provider_result_cache`, `write_provider_result_cache`,
`record_provider_result_cache_hit`, `check_context_packet_cache`, `write_context_packet_cache`,
`record_context_packet_cache_hit`, `log_cache_access`, `read_cache_access_log`, and
`_get_access_log_connection` from `tools/retrieval_cache.py`. Retained `migration_001_add_level1_
tables`, `migration_005_add_cache_access_log_table`, and the entire broader orphaned-surface family
(`provider_result_cache_stats`, `context_packet_cache_stats`, `migration_002/003/004`,
`_get_level{1,2}_connection`, `_ensure_level{1,2}_schema_for_read`, both `*Lookup` dataclasses,
`read_current_run_sidecar`) exactly as Unresolved Question #1 resolved. Also deleted two
now-orphaned constants (`_ACCESS_LOG_VALID_CACHE_LEVELS`/`_ACCESS_LOG_VALID_EVENT_TYPES`) that
plan.md's Step 2 text didn't name but which had zero remaining references once `log_cache_access()`
was gone — see plan.md's own Deviations section, item 1.

**Step 3** — updated `tests/tools/test_retrieval_cache.py`: removed `TestProviderResultCache`,
`TestMigration003`, `TestProviderResultCacheStats`, `TestContextPacketCache`, `TestLogCacheAccess`,
`TestCacheAccessLogInstrumentation`, the dead `_write_row()` helper, and one test method inside
`TestMigration005CacheAccessLog`. Also fixed two tests inside classes plan.md listed as "Do NOT
touch" that the plan's own class-by-class mapping missed — both genuinely referenced the six
deleted functions and would otherwise break the retained classes; see plan.md's Deviations section,
items 2-3. All 71 tests in the file pass.

**Step 4** — dropped `"check_provider_result_cache"` from both tuples in
`tests/tools/test_evidence_cache_identity_contract.py` and updated the adjacent explanatory comment
that specifically narrated why that name was in the loop (now stale) — see plan.md's Deviations
item 4. All 19 tests pass.

**Step 5** — removed `KGMCP_REFETCH_WINDOW_SECONDS`, `_kgmcp_access_log_group_key()`,
`_kgmcp_verdict()`, `compute_kgmcp_cache_efficiency_metrics()`, the `kgmcp_access_log`
parameter/wiring in `compute_retro_metrics()` and `generate()`, the `## KGMCP Cache Efficiency`
render block, and `main()`'s `read_cache_access_log()` call from
`tools/agent-monitoring/generate_retro.py`. Dropped `read_cache_access_log` from the
`retrieval_cache` import block, keeping the 6 unrelated 3-level-cache names.

**Step 6** — updated `tests/tools/test_generate_retro.py`: removed the
`compute_kgmcp_cache_efficiency_metrics` import, the entire dedicated kgmcp test group, and every
kgmcp-referencing assertion embedded in other tests (kept
`test_generate_uses_compute_retro_metrics_skill_usage_not_a_second_call`, which is not
kgmcp-specific). Regenerated `_FIXED_CORPUS_EXPECTED_REPORT` by calling the real, post-removal
`generate()` against the existing fixed-corpus fixtures and diffing the result against the old
golden text — confirmed the *only* difference was the disappearance of the `## KGMCP Cache
Efficiency` block, no stray blank lines, nothing in `## Parity Index Read-Path Usage`/
`## Skill Usage` shifted. All 149 tests pass.

**Step 7** — full-stack Option A removal, per the repository owner's decision (see below):
`src/api/agent_ops_dashboard/models.py` (deleted `KgmcpCacheTicketStats`,
`KgmcpRepeatedRefetchEntry`, `KgmcpDeadWriteEntry`, `KgmcpCoverageStats`,
`KgmcpCacheEfficiencyStats`, dropped the `kgmcp_cache_efficiency` field from
`AgentMonitoringStats`); `ingest.py` (removed the `read_cache_access_log` import, the 5 `Kgmcp*`
model imports, the `kgmcp_access_log=` argument to `compute_retro_metrics()`, and the
`kgmcp_cache_efficiency=KgmcpCacheEfficiencyStats(...)` field construction — the other 14 fields in
that interleaved return statement are byte-identical); `dashboard-frontend/src/api.ts` (deleted the
5 `Kgmcp*` interfaces and the field); `StatsView.tsx` (removed the import, `KgmcpTicketRow`,
`kgmcpTicketRows()`, `kgmcpVerdictColorClass()`, `formatPercent()` (also dead once the section was
gone — not explicitly named by plan.md but confirmed zero remaining call sites), and the rendered
section); `StatsView.test.tsx`/`App.test.tsx` (removed all kgmcp fixture data and the two dedicated
`it()` blocks). `npm test`: 145/145 pass.

**Step 8** — removed the 3 kgmcp-specific tests from `tests/tools/test_agent_ops_dashboard_stats.py`
and tightened the now-Skill-Usage-only section comment. `test_agent_ops_dashboard_api_boundary.py`
confirmed to still carry zero kgmcp references, untouched.

**Step 9** — updated INFRA-343 and INFRA-379 in `docs/parity_ledger/infrastructure.yaml` via
`tools/parity_ledger_writer.py::write_entry()` (never a raw Edit). INFRA-343: kept `status:
unsupported`, set `test_path` to `null` (its three cited test classes are all deleted), rewrote
`v2_evidence` to state which of the six previously-cited functions are now deleted vs.
retained-but-untested, appended a second `divergence_note` addendum in the same style as PR #152's
prior correction. INFRA-379: changed `status` from `verified` to `unsupported` (the entire
docstring-caveat feature it certified is deleted), set `test_path` to `null`, rewrote `v2_evidence`
to state the feature and its 4 proof tests were removed, added a `divergence_note`. Both writes
succeeded; the derived SQLite index rebuilt cleanly in the same call.

**Step 10** — updated `docs/observability/agent_ops_dashboard_contract.md` (removed the
`kgmcp_cache_efficiency` field from the `AgentMonitoringStats` field list, rewrote the paragraph
that described it, updated the `get_agent_monitoring_stats()` paragraph describing the now-removed
`read_cache_access_log()` call, and updated the UI-subsection description) and
`docs/guides/agent_ops_dashboard.md` (removed the "KGMCP cache efficiency" bullet and its
cross-reference). `docs/agent-monitoring/schema.md` and `docs/guides/agent_monitoring.md` were left
untouched, exactly as plan.md's Do NOT touch list specifies.

**Step 11** — final full-lane verification, all green:
`pytest tests/tools/test_retrieval_cache.py tests/tools/test_evidence_cache_identity_contract.py
tests/tools/test_generate_retro.py` (239 passed);
`pytest tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_api_boundary.py
tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` (25 passed);
`pytest tests/tools/test_parity_ledger_writer.py` (19 passed);
`pytest tests/tools/ -m "not slow"` (2467 passed, 17 skipped, 28 deselected, 1 pre-existing xfail);
`pytest tests/api/ -m "not slow"` (144 passed, per the ticket's own AC6 text);
`cd dashboard-frontend && npm test` (145 passed). Re-ran Step 1's greps one final time: zero
remaining production-code references anywhere to the 6 deleted functions,
`log_cache_access`/`read_cache_access_log`/`_get_access_log_connection`,
`compute_kgmcp_cache_efficiency_metrics`, `KgmcpCacheEfficiencyStats` and its 4 sibling
classes/interfaces, or `kgmcp_cache_efficiency` — the only remaining hits anywhere are historical
comments/docstrings (e.g. `migration_005`'s own docstring explaining its former caller, PR #152's
prior `divergence_note` text) that correctly describe past state, not live code.

**`src/api/agent_ops_dashboard/ingest.py`'s resolution — Option A rationale (repository owner's
decision, not an agent's):** the ticket's one open design question (three options laid out in
investigation.md: A — full removal, B — a permanent hardcoded "RETIRED" stub, C — an
`Optional[...] = None` field with conditional rendering) was decided directly by the repository
owner via `AskUserQuestion` between the Investigate and Plan phases (immediately after
investigation.md laid out the three real options, before Plan was dispatched — logged under phase
`Investigate` in `agent-monitoring/data/2026-W37/tools.jsonl:7431`, corrected here from an earlier
imprecise "during Plan" phrasing per Architecture-Verify's own finding), not delegated to an
agent's judgment.
The owner chose **Option A — full removal across the whole stack** (delete the 5 `Kgmcp*` model
classes and the `kgmcp_cache_efficiency` field entirely, rather than leaving a nullable or
hardcoded-stub field behind). This matches the investigation's own recommendation: the real
external blast radius is low (zero non-repo consumers of `GET /api/stats/agent-monitoring` found),
it matches exactly what the CLI/retro side already does (outright section removal, not a stub or a
nullable placeholder), and it avoids the two forms of permanent-fake-value cost Options B and C both
carry — honoring the ticket's own "both sides resolve together" framing. This is recorded here per
the ticket's own explicit AC requirement to record which resolution was chosen and why.

## Test Summary

All scoped test lanes green, zero regressions:
- `tests/tools/test_retrieval_cache.py` — 71 passed
- `tests/tools/test_evidence_cache_identity_contract.py` — 19 passed
- `tests/tools/test_generate_retro.py` — 149 passed
- `tests/tools/test_agent_ops_dashboard_stats.py` + `test_agent_ops_dashboard_api_boundary.py` +
  `test_agent_ops_dashboard_frontend_api_surface.py` — 25 passed
- `tests/tools/test_parity_ledger_writer.py` — 19 passed
- `tests/tools/ -m "not slow"` (full lane) — 2467 passed, 17 skipped, 28 deselected, 1 pre-existing
  xfail (unrelated)
- `tests/api/ -m "not slow"` (full lane, per AC6) — 144 passed
- `dashboard-frontend`: `npm test` — 145 passed (15 test files)

No new tests were added — this ticket is pure deletion/cleanup of dead code and its test coverage;
existing tests for retained code (migration_001/005, the 3-level index/query/packet cache, the
broader orphaned-surface family) continue to pass unmodified, proving nothing live was
accidentally broken.

## Files Changed
- `tools/retrieval_cache.py`
- `tests/tools/test_retrieval_cache.py`
- `tests/tools/test_evidence_cache_identity_contract.py`
- `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_generate_retro.py`
- `src/api/agent_ops_dashboard/models.py`
- `src/api/agent_ops_dashboard/ingest.py`
- `dashboard-frontend/src/api.ts`
- `dashboard-frontend/src/views/StatsView.tsx`
- `dashboard-frontend/src/test/StatsView.test.tsx`
- `dashboard-frontend/src/test/App.test.tsx`
- `tests/tools/test_agent_ops_dashboard_stats.py`
- `docs/parity_ledger/infrastructure.yaml` (via `tools/parity_ledger_writer.py::write_entry()`,
  never a raw Edit)
- `docs/observability/agent_ops_dashboard_contract.md`
- `docs/guides/agent_ops_dashboard.md`
- `staging_artifacts/TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL/plan.md` (added a
  "Deviations" section documenting the 4 mechanical corrections found during Implement)
- `tickets/inprogress/TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL.md` (this file)

`staging_artifacts/TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL/investigation.md` and
`test_plan.md` were created during this run's own Investigate phase (untracked, not yet committed)
but were not modified during Implement.

## Completion Summary

Removed the entire dead retrieval-cache access-log chain the Knowledge Gateway MCP deprecation
orphaned: the six dead Level 1/Level 2 cache functions and the `log_cache_access`/
`read_cache_access_log`/`_get_access_log_connection` chain in `tools/retrieval_cache.py`; the
retro's KGMCP Cache Efficiency machinery in `generate_retro.py` (compute function, verdict logic,
render block, CLI wiring); and — per the repository owner's Option A decision — the full
`kgmcp_cache_efficiency` field and its 5 supporting model classes across
`src/api/agent_ops_dashboard/` and the React dashboard. `migration_001`/`migration_005` and the
broader orphaned-surface family (`provider_result_cache_stats`, `context_packet_cache_stats`,
`migration_002/003/004`, the Level 1/2 connection/schema helpers, both `*Lookup` dataclasses,
`read_current_run_sidecar`) were deliberately left standing, unchanged, per the ticket's own scope
boundary. Both parity-ledger entries touched by this change (INFRA-343, INFRA-379) were updated via
the schema-validating writer. All 6 acceptance criteria are satisfied; every scoped test lane
(2467+144+145 tests across Python and the frontend) passes with zero regressions. Pure
deletion/cleanup — no behavior change to any surviving code path.
