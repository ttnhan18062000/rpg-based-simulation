---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL
phase: open
date: 2026-09-10
tags: [agent-monitoring, mcp]
---

# TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL

## Title
Remove the now-dead provider-result cache and its access-log telemetry chain

## Status
OPEN

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
- [ ] The six dead cache functions and the access-log write/read chain are removed, with no
      remaining reference from live code.
- [ ] `migration_001_add_level1_tables` is retained and `migration_005` still works — proven by a
      test exercising the migration path, not by inspection alone.
- [ ] The retro no longer emits a KGMCP cache-efficiency section, and `generate_retro.py` runs
      clean end to end.
- [ ] `src/api/agent_ops_dashboard/ingest.py`'s resolution is implemented and its reasoning
      recorded in Implementation Notes.
- [ ] INFRA-343 updated via `tools/parity_ledger_writer.py` to reflect that its cited evidence no
      longer exists.
- [ ] `tests/tools/test_evidence_cache_identity_contract.py` updated; full `tests/tools/` and
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
(filled in during implementation)

## Test Summary
(filled in during implementation)

## Files Changed
(filled in during implementation)

## Completion Summary
(filled in at close)
