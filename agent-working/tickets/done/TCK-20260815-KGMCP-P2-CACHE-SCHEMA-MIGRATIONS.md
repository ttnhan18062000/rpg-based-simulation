---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS
phase: done
date: 2026-08-15
tags: [ai, mcp]
---

# TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS

## Title
Implement the Level 1 provider-result cache SQLite schema and migrations, per the frozen
cache_migration_plan.md design

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` (frozen by
`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`) already designed — but explicitly did not
implement — the `retrieval_cache_schema_version` constant and an ordered `migration_00N_*`
function list for evolving `knowledge-index/retrieval_cache.db` in place. This ticket is where
that design becomes real code: the actual SQLite table(s) for proposal §10.2's "Level 1:
Provider-result cache" row shape, added via real migration functions, never a parallel database.

## Scope
- Implement `retrieval_cache_schema_version` as a real, versioned constant in
  `tools/retrieval_cache.py` (or the module `cache_migration_plan.md` specifies — verify against
  the real frozen doc, don't assume).
- Implement the ordered `migration_00N_*` functions the frozen plan already designed, adding the
  new provider-result cache table(s) with exactly the columns §10.2 specifies: keyed query hash,
  deterministic intent, resolved provider-native entity IDs, filters, provider name, adapter
  version, result payload, source IDs and paths, evidence hashes, provider generation,
  repository/branch scope, timestamps, hit counters.
- Preserve the existing marker-only tables (`MAY_LIST_COLUMNS`-governed) unmodified during and
  after migration — this ticket adds a new table, it does not alter or replace the existing ones.
- Migrations must be idempotent and safe to run against both a fresh (nonexistent) database and an
  existing one with only the legacy marker-only tables.
- Real tests: migrations apply cleanly from a fresh DB; migrations apply cleanly on top of the
  existing legacy schema without data loss; the new table's column set matches §10.2 exactly;
  `retrieval_cache_schema_version` is queryable and correctly reflects the current schema state.

## Out of Scope
- Any actual read/write logic against the new table from the gateway — this ticket only builds
  the schema; wiring the gateway to use it is `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`.
- Redaction/secret-scanning/size-cap enforcement at write time — that's
  `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`'s job; this ticket's schema may include the
  columns those rules operate on (e.g. a `redaction_policy_version` column), but does not itself
  enforce anything.
- Evidence-fingerprint validation logic — schema only; validation logic is a later ticket.
- Any change to `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
  or `tools/knowledge_gateway_mcp.py` — this ticket only touches the cache database layer.
- Level 2/3 cache tables (context-packet cache, verified knowledge) — Phase 3/6.

## Acceptance Criteria
- [x] `retrieval_cache_schema_version` is a real, versioned constant, distinct from and never
      confused with `RETRIEVAL_VERSION`/`retrieval_event_schema_version`/`redaction_policy_version`
      (the 4 genuinely distinct version axes `redaction_retention_policy.md` §6 already names).
- [x] The new provider-result cache table's columns match proposal §10.2's row shape exactly —
      verified by a test asserting the real schema's column set.
- [x] Migrations apply cleanly and idempotently against both a fresh DB and the existing legacy
      schema, with zero data loss to the preserved marker-only tables — verified by real tests, not
      just documentation.
- [x] `knowledge-index/retrieval_cache.db` remains the single cache database file — no second
      database created.
- [x] `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, and
      `tools/knowledge_gateway_mcp.py` remain byte-unchanged.

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC (parent)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (DONE; froze `cache_migration_plan.md`'s design this
  ticket implements)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10.1, §10.2, §10.3

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/retrieval_cache.py` (existing marker-only cache module this ticket extends)
- `knowledge-index/retrieval_cache.db` (the file to migrate)

## Assumptions / Open Questions
- Exact SQL migration mechanism (raw `ALTER TABLE`/`CREATE TABLE` statements vs. a lightweight
  migration-runner pattern) is not decided here — Investigate should check what
  `cache_migration_plan.md` §2's already-frozen function signatures imply and follow that, not
  invent a new convention.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS/plan.md`'s
6 ordered steps, no deviations:

1. Added `retrieval_cache_schema_version: int = 1` module constant to `tools/retrieval_cache.py`
   immediately after `RETRIEVAL_VERSION`, with the distinctness comment the plan specified.
2. Added the `LEVEL1_CACHE_COLUMNS: frozenset[str]` allowlist constant (21 columns) next to
   `MAY_LIST_COLUMNS`, listing every column of the new `retrieval_provider_result_cache_rows` table
   per plan.md DD5's mapping table — contract-literal names reused verbatim
   (`normalized_intent`, `resolved_entity_ids`, `filters`, `budget_class`,
   `routing_policy_version`, `repo_branch_scope`, `evidence_fingerprints`,
   `validated_negative_scopes`, `adapter_version_at_validation`, `working_tree_overlap`,
   `provider_generation_at_validation`) plus 10 plan-invented columns (`query_hash`,
   `provider_name`, `adapter_version`, `result_payload`, `source_ids`, `source_paths`,
   `provider_generation`, `created_at`, `last_hit_at`, `hit_count`).
3. Implemented `migration_001_add_level1_tables(conn)` after `_init_schema()`, under its own
   "Migrations" section header. Two `CREATE TABLE IF NOT EXISTS` statements
   (`retrieval_cache_generation`, `retrieval_provider_result_cache_rows`) followed by a
   `DELETE FROM retrieval_cache_generation` + `INSERT` pair (keeps exactly one generation row) and
   one `conn.commit()`. Uses only `conn.execute(...)`/`conn.commit()`/`time.time()` — no `PRAGMA`,
   `busy_timeout`, `chmod`, or `import os` anywhere (confirmed via `grep`, zero matches). The
   function is standalone: not called from `_get_connection()`, `_init_schema()`, or any
   `check_*_cache()`/`write_*_cache()`/`prune()` function — confirmed by both a direct read of
   those 8 call sites and the new
   `test_migration_001_function_is_never_called_from_any_check_or_write_function` test.
4. Added `class TestMigrations:` to `tests/tools/test_retrieval_cache.py` (after `TestPrune`,
   before `TestRetrievalVersionAndManifest`) with all 10 tests plan.md Step 4 specifies: fresh-DB
   apply, zero-data-loss-on-existing-legacy-schema, column-set-matches-`LEVEL1_CACHE_COLUMNS`-
   exactly, schema-version-queryable-and-correct, idempotency (including a manually-inserted row
   surviving a second migration call), marker-only-table column sets byte-identical before/after,
   constant-distinctness from `RETRIEVAL_VERSION` (AST-based, mirroring `TestStaticGuards`) and
   snapshot-check against `tools.retrieval_events.retrieval_event_schema_version`, never-called-
   from-hot-paths, no `migrate`/`rebuild` CLI subcommand, and absence from
   `_TABLE_NAME_BY_ALIAS`. One minor test-only addition beyond the plan's literal snippets: added
   `import argparse` to the test file's imports so
   `test_no_migrate_or_rebuild_subcommand_added_to_cli` could reference
   `argparse._SubParsersAction` directly instead of via `__import__("argparse")` — cosmetic only,
   no behavior difference from what the plan's pseudocode implied.
5. Added `test_deleted_cache_db_rebuild_does_not_silently_resurrect_level1_payload_rows` as a
   sibling method inside the existing `TestCrashRecovery` class, verbatim per plan.md Step 5 — does
   not modify `test_deleted_cache_db_rebuilds_clean_marker_only_schema`.
6. Narrowed the banned-path tuple in
   `tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_introduced`,
   removing `"tools/retrieval_cache.py"` and replacing it with an inline comment citing this ticket
   ID and the reasoning (Architecture-Review-ruled stale ticket-scoped assertion, not a
   routed-around gate). The other 4 paths (`search_mcp.py`, `hybrid_retrieval.py`,
   `context_packet_assembler.py`, `retrieval_events.py`) are untouched in the tuple, and no other
   test in that file was edited.

Verified manually beyond the test suite: `grep -n "CACHE_DB_PATH" tools/retrieval_cache.py` shows
exactly one assignment (unchanged, AC4); `git diff --stat HEAD -- tools/knowledge_gateway_router.py
tools/knowledge_gateway_packet_assembly.py tools/knowledge_gateway_mcp.py` is empty (AC5);
`git status --short` confirms only 3 files touched in total
(`tools/retrieval_cache.py`, `tests/tools/test_retrieval_cache.py`,
`tests/tools/test_kgmcp_measurement_baseline.py`).

No conflicts with the plan were found during implementation; no architectural issues surfaced.
Per plan.md's explicit deferral, this Implement pass does NOT write the `INFRA-341` parity ledger
entry, does NOT edit `cache_migration_plan.md`'s citation discrepancy, and does NOT edit
`evidence_cache_identity_contract.md` — those are this ticket's own later Parity and
Document-Update phases' jobs, not yet run as of this Implement pass.

## Test Summary
Ran the exact scoped commands test_plan.md specifies:

```
pytest tests/tools/test_retrieval_cache.py tests/tools/test_context_packet_assembler.py \
  tests/docs/test_redaction_retention_policy_doc.py tests/tools/test_retrieval_events.py \
  tests/tools/test_evidence_cache_identity_contract.py -v
```
Result: 114 passed, 0 failed (includes all 11 new tests: 10 in `TestMigrations` + 1 new
`TestCrashRecovery` sibling test, plus the pre-existing 103 tests in this scoped set — all
unmodified and still passing).

```
pytest tests/tools/test_kgmcp_measurement_baseline.py -v
```
Result: 23 passed, 0 failed. `test_no_live_gateway_code_or_search_mcp_edits_introduced` now passes
against the live working tree (with this ticket's real, uncommitted `tools/retrieval_cache.py` edit
present) because that one path was legitimately removed from its banned tuple in Step 6 — the other
22 tests in the file, including the other 4 banned-path assertions inside the same test function,
are unaffected.

No unscoped `pytest tests/` run, per test_plan.md's explicit instruction and CLAUDE.md's testing
rule.

## Files Changed
- `tools/retrieval_cache.py` — added `retrieval_cache_schema_version` constant,
  `LEVEL1_CACHE_COLUMNS` constant, `migration_001_add_level1_tables(conn)` function.
- `tests/tools/test_retrieval_cache.py` — added `import argparse`; added `class TestMigrations:`
  (10 tests); added 1 new test method to the existing `TestCrashRecovery` class.
- `tests/tools/test_kgmcp_measurement_baseline.py` — narrowed the banned-path tuple in
  `test_no_live_gateway_code_or_search_mcp_edits_introduced`, removing
  `"tools/retrieval_cache.py"` with an inline justifying comment.
- `docs/plans/knowledge-gateway-mcp-proposal.md` — §20 Phase 2's "Add SQLite schema and
  migrations" bullet annotated Done (Document-Update phase). `cache_migration_plan.md` and
  `evidence_cache_identity_contract.md` deliberately left untouched, per the plan's own Scope
  Guards barring edits to those 2 frozen docs.
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-341` entry, via `write_entry()`; also
  corrected `INFRA-295`'s drifted line-number citations in place (substantive claims unchanged),
  Parity phase.

## Completion Summary
Implementation (Implement phase) is complete and all steps from the approved plan have landed:
the `retrieval_cache_schema_version` constant, the `LEVEL1_CACHE_COLUMNS` allowlist, and the
standalone `migration_001_add_level1_tables(conn)` function were added to `tools/retrieval_cache.py`,
creating a new additive-only Level 1 provider-result cache table
(`retrieval_provider_result_cache_rows`) plus a `retrieval_cache_generation` metadata table, with
zero changes to the 3 existing marker-only tables or their write paths. 11 new tests were added
across `TestMigrations` (new class) and `TestCrashRecovery` (1 new sibling method), and the stale
`test_kgmcp_measurement_baseline.py` banned-path assertion was narrowed per Architecture Review's
ruling. All 5 acceptance criteria are satisfied and checked above. All 137 tests across the 6
scoped test files (114 + 23) pass. Document-Update has since annotated
`knowledge-gateway-mcp-proposal.md` §20's "Add SQLite schema and migrations" bullet Done, and
deliberately left `cache_migration_plan.md`/`evidence_cache_identity_contract.md` untouched per
the plan's own frozen-doc Scope Guards. Parity has since added `INFRA-341`, re-verified 11/11
test_path pass, and corrected `INFRA-295`'s drifted line-number citations in place (its
substantive claims unchanged). Verify (`done-checker`) independently re-ran the full scoped test
suite (60 passed, 0 failed across `test_retrieval_cache.py` + `test_kgmcp_measurement_baseline.py`),
cross-checked every `INFRA-341`/`INFRA-295` line citation against the live file, confirmed the 3
Phase 1 gateway files remain byte-unchanged, confirmed no `PRAGMA`/`busy_timeout`/`chmod`/`import os`
anywhere in `tools/retrieval_cache.py`, and confirmed all 13 DoD conditions PASS — verdict
READY_TO_CLOSE. This ticket is now finalized and moved to `tickets/done/`.
