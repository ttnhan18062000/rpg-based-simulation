---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS
phase: done
date: 2026-08-16
tags: [ai, mcp]
---

# TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS

## Title
Implement the Level 2 assembled context-packet cache SQLite schema and migration, per the
already-reserved `migration_002_add_level2_tables` design

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` already reserves ordinal 2 —
`migration_002_add_level2_tables(conn: sqlite3.Connection) -> None` — for "the Level 2
(dependency-tracking) tables per §10.3," explicitly stating this ordinal "must never be reused or
stubbed by a later migration." Migration 3 (`migration_003_add_redaction_policy_version_column`)
already landed at ordinal 3 during Phase 2, confirming ordinal 2 is still open and reserved. This
ticket is where that reservation becomes real code: the actual SQLite table(s) for proposal §10.2's
"Level 2: Assembled context-packet cache" and §10.3's conceptual `CachedPacket` row shape, added via
`migration_002_add_level2_tables`, never a parallel database and never a different ordinal.

## Scope
- Implement `migration_002_add_level2_tables(conn: sqlite3.Connection) -> None` in
  `tools/retrieval_cache.py`, using the exact reserved name and ordinal from
  `cache_migration_plan.md` — verify the current real function/ordinal state in the file before
  writing (migration_003 already exists; do not renumber it or collide with it).
- Add a NEW real content-bearing table (name TBD by this ticket's own Investigate phase, e.g.
  `retrieval_context_packet_cache_rows`) with columns matching §10.2's Level 2 row-shape bullets
  and §10.3's conceptual `CachedPacket` field list: `packet_id`, `normalized_intent`,
  `query_key_hash`, `entity_ids`, `answer`, `statements`, `context_items`, `evidence`, `conflicts`,
  `evidence_dependencies`, `provenance_providers`, `providers_consulted_this_call`, `repository_id`,
  `branch`, `head_commit`, `working_tree_fingerprint`, `provider_generations`, `policy_version`,
  `schema_version`, `budget_requested`, `budget_returned`, `status`, `freshness`, `verification`,
  `lifecycle`, `created_at`, `last_validated_at`, `hit_count` — reconciled against real SQLite
  column-type constraints and this repo's existing JSON-serialization-for-structured-fields
  convention (as Level 1's `LEVEL1_CACHE_COLUMNS` already does for its own array/dict-shaped
  columns).
- Preserve the existing marker-only `retrieval_packet_cache_rows` table (owned by the separate,
  unrelated, BACKLOG-tier `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`) completely unmodified —
  this ticket adds a new table, it does not alter, extend, or replace that one.
- Preserve `retrieval_provider_result_cache_rows` (Level 1) and its `migration_003`-added
  `redaction_policy_version` column completely unmodified.
- Migration must be idempotent and safe to run against a fresh (nonexistent) database, an existing
  database with only the legacy marker-only tables, and an existing database that already has
  Level 1's tables (migration_001 + migration_003 applied).
- Real tests: migration applies cleanly from a fresh DB; migration applies cleanly on top of the
  existing Level 1 + legacy schema without data loss to any of those tables; the new table's column
  set matches §10.2/§10.3 exactly; `retrieval_cache_schema_version` correctly reflects the new
  schema state after this migration.

## Out of Scope
- Any actual read/write logic against the new Level 2 table from the gateway — this ticket only
  builds the schema; wiring is `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`.
- Deduplication logic, budget-enforcement logic, or packet-assembly changes — that is
  `TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT`'s job; this ticket's schema may include
  the columns that logic later populates, but does not itself compute or enforce anything.
- Packet dependency-record semantics or targeted-invalidation logic beyond the raw
  `evidence_dependencies` column existing in the schema — the invalidation behavior itself is
  `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION`'s job.
- Redaction/secret-scanning/size-cap enforcement at write time for Level 2 payloads — schema only;
  whether Level 1's existing enforcement automatically covers Level 2 is the wiring ticket's own
  verification job, not decided or assumed here.
- Any change to `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
  or `tools/knowledge_gateway_mcp.py` — this ticket only touches the cache database layer.
- Modifying `retrieval_packet_cache_rows` or any code path that reads/writes it today.
- Level 3 (verified reusable knowledge) tables — Phase 6.

## Acceptance Criteria
- [x] `migration_002_add_level2_tables(conn: sqlite3.Connection) -> None` exists in
      `tools/retrieval_cache.py`, using the exact reserved name from `cache_migration_plan.md`, at
      ordinal 2 (immediately before the already-landed `migration_003_...`) — verified by a real
      test asserting the function name and its position relative to `migration_001`/`migration_003`
      in whatever ordering mechanism the module uses.
- [x] The new Level 2 table's columns match proposal §10.2's Level 2 bullets and §10.3's
      `CachedPacket` field list exactly — verified by a test asserting the real schema's column set
      against an explicit allowlist constant (mirroring `LEVEL1_CACHE_COLUMNS`'s own pattern).
- [x] The migration applies cleanly and idempotently against a fresh DB, an existing legacy-only DB,
      and an existing DB with Level 1's tables already migrated — with zero data loss to any
      preserved table, verified by real tests.
- [x] `retrieval_packet_cache_rows` (the existing marker-only table) is byte-for-byte unmodified by
      this ticket — verified by a test comparing its column set/schema before and after the
      migration runs.
- [x] `retrieval_provider_result_cache_rows` (Level 1) and its columns remain unmodified by this
      ticket.
- [x] `knowledge-index/retrieval_cache.db` remains the single cache database file — no second
      database created.
- [x] `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, and
      `tools/knowledge_gateway_mcp.py` remain byte-unchanged.
- [x] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added for this
      ticket's own behavior change, per this repo's own governance rule (unaffected by "Parity
      Ledger not required until Phase 4," which concerns the gateway's own routing behavior only —
      see the epic's naming-collision clarification). **Done** — `INFRA-346` added (status=verified,
      priority=P1, proof_type=regression), written through
      `tools/parity_ledger_writer.py::write_entry()`; `python3 tools/parity_index.py build` re-run
      afterward. This same Parity pass also found and corrected stale `tools/retrieval_cache.py`
      line-number citations in `INFRA-341` and `INFRA-343` (both drifted by this ticket's own
      `migration_002_add_level2_tables` insertion between `migration_001` and `migration_003`);
      `INFRA-345` was checked and confirmed to cite only `tools/knowledge_gateway_redaction.py`,
      so it needed no correction.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC (parent)
- TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS (DONE; the Level 1 schema/migration_001 precedent
  this ticket's migration_002 mirrors the pattern of)
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DONE; added migration_003, confirming ordinal 2
  remains open/reserved for this ticket)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (DONE; froze `cache_migration_plan.md`'s
  `migration_002_add_level2_tables` reservation this ticket implements)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (BACKLOG; owns the existing marker-only
  `retrieval_packet_cache_rows` table this ticket must leave untouched)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` (reserves
  `migration_002_add_level2_tables`)
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10.2 (Level 2 row shape), §10.3 (Conceptual
  Cached Packet Schema)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/retrieval_cache.py` (existing Level 1 schema/migration module this ticket extends;
  `LEVEL1_CACHE_COLUMNS`, `migration_001_add_level1_tables`, `migration_003_add_redaction_policy_version_column`
  are the real, already-landed precedent to follow)
- `knowledge-index/retrieval_cache.db` (the file to migrate)

## Assumptions / Open Questions
- Exact name of the new Level 2 table is not decided here — Investigate should check whether
  `cache_migration_plan.md` or `evidence_cache_identity_contract.md` names it explicitly anywhere
  beyond "the Level 2 tables"; if not, choose a name consistent with the existing
  `retrieval_provider_result_cache_rows`/`retrieval_packet_cache_rows` naming convention.
- Whether the Level 2 row needs one table or more than one (e.g. a separate dependency-junction
  table for `evidence_dependencies`, given the later dependency-invalidation ticket's needs) is not
  decided here — Investigate/Plan should coordinate with what
  `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION` will need, without scope-creeping into
  that ticket's own invalidation logic.
- Exact SQL representation for array/dict-shaped `CachedPacket` fields (`entity_ids`, `statements`,
  `context_items`, `evidence`, `conflicts`, `evidence_dependencies`, `provenance_providers`,
  `providers_consulted_this_call`, `provider_generations`) is not decided here — follow whatever
  JSON-text-column convention Level 1's `LEVEL1_CACHE_COLUMNS` already established for its own
  array/dict-shaped columns (e.g. `resolved_entity_ids`, `filters`, `evidence_fingerprints`), unless
  investigation finds a documented reason to diverge.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS/plan.md`
(Architecture-Review-corrected, Pass 1 `NEEDS_CHANGES` resolved):

- **Step 1**: Added `LEVEL2_CACHE_COLUMNS` (28-entry frozenset) to `tools/retrieval_cache.py`,
  immediately after `LEVEL1_CACHE_COLUMNS`, per DD5's column-mapping table.
- **Step 2**: Added `migration_002_add_level2_tables(conn)`, inserted textually between
  `migration_001_add_level1_tables` and `migration_003_add_redaction_policy_version_column` in
  source order (verified by `TestLevel2Migrations::test_migration_002_function_exists_with_reserved_name_and_ordinal`'s
  AST source-position check). Creates `retrieval_context_packet_cache_rows`
  (`CREATE TABLE IF NOT EXISTS`, 28 columns matching `LEVEL2_CACHE_COLUMNS`), then stamps
  `retrieval_cache_generation` with its own hardcoded literal `2`.
- **Step 3**: `migration_001_add_level1_tables`'s INSERT changed to hardcode literal `1` (was: the
  live `retrieval_cache_schema_version` module constant) — decouples its on-disk stamp from a
  constant other migrations bump; value-neutral (constant was already `1`). Module constant
  `retrieval_cache_schema_version` bumped `1` -> `2`.
- **Step 4**: `tests/tools/test_knowledge_gateway_redaction.py:482`
  (`TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`)
  corrected `rc.retrieval_cache_schema_version == 1` -> `== 2`. No other assertion in that test
  touched.
- **Step 5**: Added `TestLevel2Migrations` (12 tests) to `tests/tools/test_retrieval_cache.py`,
  placed after `TestMigration003` and before `TestProviderResultCacheStats`, per test_plan.md's
  "New Tests Required" spec (with two of the twelve — tests 2 and 3 — adapted to run
  `migration_001` before `migration_002`; see Deviations below).
- **Step 6**: Added `docs/guidelines/intentional_divergences.md` §2.44 ("Level 2 Packet-Cache
  Freshness/Verification Column Co-location") plus its §1 summary row — rationale class
  `Bounded`, verification path naming `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s
  future obligation, per Architecture Review's DD4 ruling (option (b)).

**Deviations from the plan (see `staging_artifacts/.../plan.md`'s own "Deviations" section for full
detail) — four items, none altering DD1-DD6 or Steps 1-6, all narrow corrections to pre-existing
test assertions invalidated by this ticket's approved design landing:**
1. `TestMigration003::test_migration_002_name_never_reused_or_stubbed` (pre-existing ordinal-2
   reservation guard, asserted `"migration_002" not in source`) renamed to
   `test_migration_002_landed_with_the_reserved_name_not_stubbed_or_renamed` and updated to assert
   the function now exists, correctly named, exactly once.
2. Step 5 tests 2 and 3 run `migration_001` before `migration_002` (test_plan.md's literal
   "alone (no migration_001)"/"brand-new (never-migrated) connection" wording was inconsistent
   with Step 2/DD2's own explicit, reasoned design — `migration_002` assumes
   `retrieval_cache_generation` already exists, by construction, and raises
   `sqlite3.OperationalError` otherwise; Step 2's plan text says this is intentional). Resolved in
   favor of Step 2/DD2 (the more authoritative, twice-reviewed artifact that directly anticipated
   this exact scenario). AC3's three required starting-state scenarios remain each covered.
3. `tests/tools/test_evidence_cache_identity_contract.py::test_no_shared_code_or_table_conflates_lookup_hit_with_validity_proof`
   (pre-existing blanket "freshness"/"verification" not-in-source guard, predates this ticket's
   Architecture-Review-ruled DD4 exception) narrowed to check only the three `check_*_cache`
   lookup functions' own source — the actual thing the rule (and this test's own section title)
   protects — since DD4 permits the columns on the new table's schema, where no lookup function
   reads them.
4. `tests/tools/test_kgmcp_phase2_baseline_recomparison.py::test_no_frozen_kgmcp_dependency_edited`
   still listed `tools/retrieval_cache.py` in its banned-edit-path tuple (a different file from
   `test_kgmcp_measurement_baseline.py`, which already excludes it). Removed with a documenting
   comment mirroring the file's own existing precedent for `tools/knowledge_gateway_redaction.py`.

None of these four required any additional change to `tools/retrieval_cache.py` itself beyond
Steps 1-3, and none weaken a check's real substantive protection.

## Test Summary
All scoped commands from `test_plan.md` plus the two additionally-discovered regression files
(items 3-4 above) pass, 0 failures:
- `tests/tools/test_retrieval_cache.py` — 67 passed (54 pre-existing + 13 `TestLevel2Migrations`,
  including `test_migration_002_never_creates_a_second_database_file` added post-Test-phase to
  close a real coverage gap — see below)
- `tests/tools/test_kgmcp_measurement_baseline.py` — 23 passed
- `tests/docs/test_redaction_retention_policy_doc.py` — 7 passed
- `tests/tools/test_context_packet_assembler.py` — 16 passed
- `tests/tools/test_knowledge_gateway_redaction.py` — 66 passed (incl. corrected Step 4 assertion)
- `tests/tools/test_evidence_cache_identity_contract.py` — 19 passed (incl. narrowed guard, Deviation 3)
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py` — 17 passed (incl. fixed guard, Deviation 4)
- Broader sweep of every other test file in `tests/` referencing `tools.retrieval_cache`
  (`test_knowledge_gateway_packet_assembly.py`, `test_generate_retro.py`,
  `test_knowledge_gateway_mcp.py`, `test_knowledge_gateway_failure_semantics.py`,
  `test_kgmcp_phase1_baseline_comparison.py`, `test_knowledge_gateway_cache.py`,
  `test_knowledge_gateway_router.py`, `test_retrieval_events.py`) — **299 passed**, 0 failures
  (corrected from an initial arithmetic error of "335" — independently re-run twice, by
  Architecture-Verify and again after the Deviation 3 fix below; 299 is the real, confirmed count).

Total: **514 tests across 15 files, 0 failures** (corrected from an initial "549"; +1 from the
post-Test-phase AC6 gap fix below), independently re-confirmed via a fresh full 15-file run.

**Post-Architecture-Verify fix**: the 1st Architecture-Verify pass found `check_provider_result_cache`
(Level 1's own real lookup function) was missing from Deviation 3's narrowed guard loop in
`tests/tools/test_evidence_cache_identity_contract.py` — added to both the existence-check loop and
the freshness/verification-in-source loop. Re-ran that file after the fix: still 19 passed (the fix
adds coverage, not new test cases).

**Post-Test-phase fix (AC6 coverage gap)**: the Test phase independently found AC6 ("single cache
database file, no second database created") had no dedicated test — `migration_002_add_level2_tables`
takes a connection, not a path, so it structurally cannot open a second file, but that's an
implementation-shape argument, not an independent behavioral check. Added
`test_migration_002_never_creates_a_second_database_file` to `TestLevel2Migrations`: runs
`migration_001`+`migration_002` against the isolated `tmp_path`-scoped `CACHE_DB_PATH`, then asserts
no other file exists in that directory besides the single cache DB (and any same-file sidecar).
Passes. Re-ran the full 15-file scoped suite after this addition: **514 passed, 0 failed**
(514 = 513 + 1 new test).

## Files Changed
- `tools/retrieval_cache.py` — `LEVEL2_CACHE_COLUMNS`, `migration_002_add_level2_tables`,
  `migration_001_add_level1_tables`'s INSERT literal, `retrieval_cache_schema_version` constant
  value.
- `tests/tools/test_retrieval_cache.py` — new `TestLevel2Migrations` class (12 tests); renamed/
  updated `TestMigration003::test_migration_002_name_never_reused_or_stubbed`; added `import sqlite3`.
- `tests/tools/test_knowledge_gateway_redaction.py` — corrected one literal (line 482, `== 1` ->
  `== 2`).
- `tests/tools/test_evidence_cache_identity_contract.py` — narrowed the freshness/verification
  source-text guard to four lookup functions' own source (Deviation 3; a 4th,
  `check_provider_result_cache`, added post-hoc after the 1st Architecture-Verify pass found it
  missing).
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py` — removed `tools/retrieval_cache.py`
  from the banned-edit-path tuple, with a documenting comment (Deviation 4).
- `docs/guidelines/intentional_divergences.md` — new §1 summary row + §2.44 detailed record.
- `staging_artifacts/TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS/plan.md` — added
  "Deviations" section documenting the four items above.
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` — annotated §2's
  `migration_002_add_level2_tables` bullet as now real, implemented code (mirroring migration 3's
  existing landing annotation), citing `tools/retrieval_cache.py:310-364` and the new
  `retrieval_context_packet_cache_rows` table; corrected the adjacent migration-3 sentence that
  previously (and, as of migration_001's earlier landing, already inaccurately) described
  "migrations 1 and 2" as design-only placeholders.
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-346` entry (status=verified, priority=P1,
  proof_type=regression) added via `tools/parity_ledger_writer.py::write_entry()`, citing
  `LEVEL2_CACHE_COLUMNS`, `migration_002_add_level2_tables`, `migration_001_add_level1_tables`'s
  decoupled INSERT, and the bumped `retrieval_cache_schema_version` constant by real line number;
  also corrected stale `tools/retrieval_cache.py` line-number citations in the pre-existing
  `INFRA-341` and `INFRA-343` entries (both drifted by this ticket's `migration_002` insertion
  between `migration_001` and `migration_003`) — `INFRA-345` checked and confirmed to need no
  correction (it cites only `tools/knowledge_gateway_redaction.py`). `tools/parity_index.py build`
  re-run afterward as a separate step.
- `docs/plans/knowledge-gateway-mcp-proposal.md` — **not edited**. §20 Phase 3's 4 bullets
  ("Assemble deduplicated multi-provider packets.", "Store and return actual packet payloads.",
  "Enforce caller budgets using measured output size.", "Add packet dependency records and
  targeted invalidation.") are correctly still unmarked, since this ticket is schema-only
  prerequisite work satisfying none of them. The doc has no existing convention for a partial/
  prerequisite-progress note on a not-yet-Done bullet anywhere across its 7 phases (checked Phases
  0–6): every bullet is strictly binary — blank, or `**Done** (ticket-id) — description`; the two
  places that mention "un-started future ticket" work do so only inside an already-Done bullet's
  own description, never on an incomplete one. Forcing a new annotation style here for this ticket
  alone would misrepresent the doc's own convention rather than honestly reflect status, so per this
  ticket's own instruction, the file was left untouched.

## Completion Summary
Implemented `migration_002_add_level2_tables` at the reserved ordinal 2 in
`tools/retrieval_cache.py`, adding the new `retrieval_context_packet_cache_rows` Level 2 table
(28 columns per proposal §10.2/§10.3, one disambiguating rename per DD3) with its own
`LEVEL2_CACHE_COLUMNS` allowlist, applied the Architecture-Review-mandated DD2 correction
decoupling `migration_001`'s version stamp from the shared module constant, bumped that constant
to 2, and recorded the `freshness`/`verification` Non-collapse-rule divergence in
`docs/guidelines/intentional_divergences.md` §2.44 with a verification obligation for the
follow-on read-write-wiring ticket. All critical invariants (marker-only table untouched, Level 1
table/migration_003 untouched, single cache DB file, three live-gateway files byte-unchanged, no
read/write function or dependency-invalidation logic added) verified directly via git diff/grep
and passing tests, including a broader sweep beyond `test_plan.md`'s five scoped files that
surfaced and fixed two additional pre-existing regression tests invalidated by this ticket's
approved design.

Document-Update: `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` §2 now
annotates `migration_002_add_level2_tables` as landed real code (mirroring migration 3's existing
precedent) and corrects the adjacent sentence that previously mischaracterized migrations 1 and 2
as still design-only. `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 3 was deliberately
left unmarked — none of its 4 bullets are satisfied by this schema-only ticket, and the doc has no
existing convention for a partial-progress note on an incomplete bullet (see Files Changed for the
full rationale).

Parity-Update: added `docs/parity_ledger/infrastructure.yaml` entry `INFRA-346`
(status=verified, priority=P1, proof_type=regression) via
`tools/parity_ledger_writer.py::write_entry()`, citing `LEVEL2_CACHE_COLUMNS` (:144-185),
`migration_002_add_level2_tables` (:310-364), `migration_001_add_level1_tables`'s decoupled
INSERT (:255-307, INSERT itself :302-306), and the bumped `retrieval_cache_schema_version`
constant (:62, now `2`) by real, directly-verified line number in the current
`tools/retrieval_cache.py`; `support_boundary` states the schema/migration-only scope and cites
`docs/guidelines/intentional_divergences.md` §2.44 by reference for the known, formally-recorded
Non-collapse-rule divergence and its inherited verification obligation. `python3
tools/parity_index.py build` re-run as a separate step afterward. While writing this entry, found
and corrected drifted `tools/retrieval_cache.py` line-number citations in the pre-existing
`INFRA-341` (Level 1 schema/migration) and `INFRA-343` (cache read/write wiring) entries — both
were shifted by this ticket's own `migration_002_add_level2_tables` insertion between
`migration_001` and `migration_003` — via the same validating writer (whole-entry upsert by id,
preserving every other field verbatim, only the stale line-number substrings and a documenting
addendum changed). `INFRA-345` (size-cap hotfix) was checked directly and confirmed to cite only
`tools/knowledge_gateway_redaction.py`, never `tools/retrieval_cache.py` by line number, so it
required no correction. AC for the parity ledger entry is now satisfied. Verify (`done-checker`)
independently re-ran the full 15-file scoped suite (514 passed, 0 failed), byte-checked the
`INFRA-346` entry and the corrected `INFRA-341`/`INFRA-343` citations against the live file,
confirmed the 3 live-gateway files and the 2 preserved tables remain untouched, confirmed the
`intentional_divergences.md` §2.44 entry matches what Review approved, and confirmed all 8
Acceptance Criteria and all 13 DoD conditions PASS — verdict READY_TO_CLOSE. This ticket is now
finalized and moved to `tickets/done/`.
