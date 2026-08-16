---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS

## Architecture-Review Correction (Pass 1)

Architecture Review's first-pass `NEEDS_CHANGES` ruling found that the corrected DD2 mechanism (see
`plan.md`'s "Architecture-Review Corrections" section) requires bumping the module-level
`retrieval_cache_schema_version` constant, which affects a third test outside this test plan's
original scope: `tests/tools/test_knowledge_gateway_redaction.py:482`
(`TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`), which
asserts `rc.retrieval_cache_schema_version == 1`. This file is added below to the Regression Surface
and Scoped Pytest Commands accordingly. This is a Review-mandated correction, not an
implementer-discovered deviation.

## Regression Surface

All existing tests in `tests/tools/test_retrieval_cache.py` must keep passing, in particular
(unit, module-local, no ML/live dependency, per the file's own docstring):

- `TestIndexCache`, `TestQueryCache`, `TestPacketCache` (AC1-AC3 marker-only-table behavior,
  unchanged by this ticket).
- `TestLifecycle` / prune-related tests (`test_prune_deletes_rows_older_than_threshold_across_all_
  three_tables`, `test_prune_leaves_rows_newer_than_threshold_untouched`,
  `test_prune_is_not_invoked_by_any_check_or_write_function`) — the new table is intentionally not
  added to `_TABLE_NAME_BY_ALIAS`/`prune()` by this ticket (schema only; lifecycle/GC wiring is a
  later ticket's job per `redaction_retention_policy.md` §10), so these must be unaffected.
- `TestMigrations` (all of `test_migration_applies_cleanly_to_a_fresh_database`,
  `test_migration_applies_cleanly_on_top_of_existing_legacy_schema_with_zero_data_loss`,
  `test_new_table_column_set_matches_proposal_section_10_2_row_shape`,
  `test_migration_is_idempotent_when_run_twice`,
  `test_migration_does_not_alter_existing_marker_only_table_column_sets`,
  `test_retrieval_cache_schema_version_constant_is_distinct_from_the_other_three_version_axes`,
  `test_migration_001_function_is_never_called_from_any_check_or_write_function`) — **especially**
  `test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration` (hardcodes
  `schema_version == 1` after a `migration_001`-only run) and `test_migration_is_idempotent_when_
  run_twice` (hardcodes `generation_rows == [(1,)]`) — these are the two tests directly exposed to
  the version-bump coupling risk flagged in investigation.md's Risk 1. Implement must not make these
  fail as a side effect of however `migration_002` stamps its own version.
- `tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_
  introduced` — confirmed (investigation.md, Prior Work) that `tools/retrieval_cache.py` is already
  excluded from this test's banned-edit-path list; must remain excluded/passing, not re-added.
- `tests/docs/test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_implemented`
  — asserts `"PRAGMA"`/`"busy_timeout"`/`"chmod"` and `import os` are absent from
  `tools/retrieval_cache.py`'s source; this ticket's migration code must not introduce any of these.
- `tests/tools/test_context_packet_assembler.py::TestWorkflowIsolationGuards::
  test_assembler_does_not_import_contextpacket_from_retrieval_cache` — must remain passing; this
  ticket must not define or import a `ContextPacket` class into `tools/retrieval_cache.py`.
- `tests/docs/` doc-parity/frontmatter tests that assert `docs/parity_ledger/infrastructure.yaml`
  remains schema-valid (whatever the repo's standard `validate_frontmatter.py`/parity-schema check
  suite is, run as part of this ticket's own Parity phase, not enumerated file-by-file here since it
  is a cross-cutting repo-wide gate, not specific to this module).
- **`tests/tools/test_knowledge_gateway_redaction.py::TestRedactionPolicyVersion::
  test_redaction_policy_version_distinct_from_retrieval_version`** (`:479-489`) — **added per
  Architecture-Review-mandated correction (see "Architecture-Review Correction" above), was missing
  from the original scope.** This test asserts `rc.retrieval_cache_schema_version == 1` directly
  against the live module constant. Per plan.md's corrected DD2/Step 3, this ticket bumps that
  constant to `2`; plan.md's Step 4 updates this single assertion to `== 2`. The test's other three
  `assert ... == 1` lines (`kgr.redaction_policy_version`, `rc.RETRIEVAL_VERSION`,
  `re_mod.retrieval_event_schema_version`) and its five `not in dir(...)` lines are unaffected and
  must remain unedited — this ticket touches none of those three constants.

Category: unit (all of the above — pure SQLite/file-local, no network, no ML model, no live gateway
call).

## New Tests Required

All new tests live in `tests/tools/test_retrieval_cache.py`, in a new `TestLevel2Migrations` class
(mirroring the existing `TestMigrations` class's structure/naming style), unless noted otherwise.

1. **`test_migration_002_function_exists_with_reserved_name_and_ordinal`**
   Category: unit / architecture guard.
   Verifies: `rc.migration_002_add_level2_tables` exists, is callable, takes exactly one
   `conn: sqlite3.Connection` positional parameter (via `inspect.signature`), and — using the same
   `ast`-based module-level-statement-order technique already used by
   `test_retrieval_cache_schema_version_constant_is_distinct_from_the_other_three_version_axes` (or
   equivalent source-position comparison) — that its definition appears after
   `migration_001_add_level1_tables` and before `migration_003_add_redaction_policy_version_column`
   in the file's real source order, satisfying the ticket's own AC ("ordinal 2, immediately before
   the already-landed `migration_003_...`").
   Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

2. **`test_migration_002_applies_cleanly_to_a_fresh_database`**
   Category: unit.
   Verifies: calling `migration_002_add_level2_tables(conn)` against a brand-new (never-migrated)
   connection creates the new Level 2 table (by whatever name Plan/Implement settles on, e.g.
   `retrieval_context_packet_cache_rows`) alongside the 3 pre-existing marker-only tables, with no
   error, mirroring `test_migration_applies_cleanly_to_a_fresh_database`'s existing shape (checks
   `sqlite_master` table-name set via `>=` superset assertion).
   Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

3. **`test_migration_002_applies_cleanly_on_top_of_legacy_only_schema_with_zero_data_loss`**
   Category: unit.
   Verifies: seed the 3 marker-only tables with rows (via `write_index_cache`/`write_query_cache`/
   `write_packet_cache`, exactly as the Level 1 precedent's own
   `test_migration_applies_cleanly_on_top_of_existing_legacy_schema_with_zero_data_loss` does), snapshot
   all rows, run `migration_002_add_level2_tables` alone (no `migration_001`), assert every
   pre-existing table's rows are byte-identical before/after, and the new Level 2 table exists and is
   empty. Satisfies the ticket's own required "existing database with only the legacy marker-only
   tables" scenario.
   Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

4. **`test_migration_002_applies_cleanly_on_top_of_level1_already_migrated_schema_with_zero_data_loss`**
   Category: unit.
   Verifies: run `migration_001_add_level1_tables` first, seed a
   `retrieval_provider_result_cache_rows` row via `write_provider_result_cache(...)`, snapshot it, then
   run `migration_002_add_level2_tables` on the same connection; assert the Level 1 row and its
   column set are unchanged, and the new Level 2 table now also exists. Satisfies the ticket's own
   required "existing database that already has Level 1's tables (migration_001 + migration_003
   applied)" scenario — extend to also run `migration_003_add_redaction_policy_version_column` first
   to cover the full stated 3-migration-chain case.
   Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

5. **`test_new_level2_table_column_set_matches_proposal_section_10_3_cachedpacket_field_list`**
   Category: unit.
   Verifies: after running `migration_002_add_level2_tables`, `PRAGMA table_info(<new_table_name>)`'s
   column-name set equals an explicit new allowlist constant (e.g. `LEVEL2_CACHE_COLUMNS`,
   mirroring `LEVEL1_CACHE_COLUMNS`'s existing pattern) containing all 28 fields from proposal §10.3's
   `CachedPacket` schema (with whatever disambiguated names Plan chooses for `repository_id`/
   `branch`/`head_commit`/`working_tree_fingerprint` and the `schema_version`-naming-collision flag
   from investigation.md Risk 3) — mirrors
   `test_new_table_column_set_matches_proposal_section_10_2_row_shape`'s exact assertion style
   (`assert columns == rc.LEVEL2_CACHE_COLUMNS`).
   Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

6. **`test_migration_002_is_idempotent_when_run_twice`**
   Category: unit.
   Verifies: run `migration_002_add_level2_tables` twice on the same connection with a seeded row in
   between; assert the table's schema is unchanged and the seeded row still exists exactly once (not
   duplicated or dropped) — mirrors `test_migration_is_idempotent_when_run_twice`'s exact shape.
   Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

7. **`test_migration_002_does_not_alter_existing_marker_only_or_level1_table_column_sets`**
   Category: unit / anti-drift guard.
   Verifies: snapshot `PRAGMA table_info(...)` for all 4 pre-existing tables
   (`retrieval_index_cache_rows`, `retrieval_query_cache_rows`, `retrieval_packet_cache_rows`,
   `retrieval_provider_result_cache_rows`) before and after `migration_002_add_level2_tables` runs
   (with `migration_001`/`migration_003` already applied); assert byte-identical column sets —
   mirrors `test_migration_does_not_alter_existing_marker_only_table_column_sets` but extended to
   cover the Level 1 table too, since this ticket's own AC explicitly calls out both
   `retrieval_packet_cache_rows` and `retrieval_provider_result_cache_rows` as must-remain-unmodified.
   Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

8. **`test_retrieval_cache_schema_version_correctly_reflects_new_schema_state_after_migration_002`**
   Category: unit — directly targets the ticket's own explicit acceptance criterion and
   investigation.md's Risk 1.
   Verifies: whatever version-stamping mechanism Plan/Implement chooses (see investigation.md Risk 1
   — this test's exact assertions depend on that Plan decision, but at minimum): (a) after running
   the full migration chain (`migration_001` → `migration_003` → `migration_002`, or whatever order
   Plan settles on) on a fresh DB, `retrieval_cache_generation` holds a value that genuinely reflects
   Level 2 having been applied (not silently still reporting the pre-Level-2 value); (b) running
   `migration_001_add_level1_tables` **alone**, in isolation, on a separate fresh connection, still
   yields exactly the value the two existing regression tests
   (`test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration`,
   `test_migration_is_idempotent_when_run_twice`) already hardcode — i.e. this new test is written
   specifically to catch the regression flagged in investigation.md Risk 1, not merely to assert a
   new happy path.
   Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

9. **`test_evidence_dependencies_column_is_json_text_and_supports_set_intersection_like_the_existing_
   marker_only_packet_table`**
   Category: unit / anti-drift guard (protects the Open-Question-2 design decision from silent
   regression to a different shape later).
   Verifies: write a row with `evidence_dependencies` as a `json.dumps([...])`-serialized string,
   read it back via `PRAGMA table_info` + direct `SELECT`, `json.loads()` it, and assert a Python
   `set()`-style comparison works exactly as `check_packet_cache()` already does against
   `cited_hashes_json` on the pre-existing marker-only table — proves the schema decision (single
   JSON column, no junction table) is genuinely usable by the future dependency-invalidation ticket
   without redesign.
   Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

10. **`test_new_level2_table_name_does_not_collide_with_existing_marker_only_packet_table`**
    Category: unit / architecture guard.
    Verifies: the new table's real name is not `"retrieval_packet_cache_rows"`, and both tables
    coexist in `sqlite_master` simultaneously after migration with distinct row sets — directly
    guards the ticket's own hard AC that the existing marker-only table remains untouched and
    unambiguous.
    Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

11. **`test_no_actual_read_write_functions_added_for_the_new_level2_table`**
    Category: architecture guard / anti-scope-creep.
    Verifies: no `check_*`/`write_*`-style function exists yet for the new table (e.g. assert no
    module attribute matching a `check_context_packet_cache`/`write_context_packet_cache`-style name
    exists, or equivalently that `tools/retrieval_cache.py`'s module dict has no new public callable
    beyond the migration function and the column-allowlist constant) — guards this ticket's own Out
    of Scope against a future/self-drifting implementer adding "just a little" read/write logic
    "to prove the schema works."
    Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

12. **`test_no_pragma_busy_timeout_chmod_or_os_import_introduced_by_level2_migration`**
    Category: architecture guard (belt-and-suspenders alongside the existing
    `test_sqlite_defaults_not_silently_implemented` doc-level guard).
    Verifies: `tools/retrieval_cache.py`'s source text (post-implementation) still contains none of
    `"PRAGMA"`, `"busy_timeout"`, `"chmod"`, and `import os` is still absent from its imported-module
    set — same assertion shape as the existing doc-level test, added here as a module-local guard so
    a failure surfaces directly against this ticket's own diff, not only against the separate
    `tests/docs/` file.
    Where: `tests/tools/test_retrieval_cache.py::TestLevel2Migrations`.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_retrieval_cache.py -v
.venv/bin/python3 -m pytest tests/tools/test_kgmcp_measurement_baseline.py -v
.venv/bin/python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -v
.venv/bin/python3 -m pytest tests/tools/test_context_packet_assembler.py -v
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_redaction.py -v
```

Never `pytest tests/`. All five files above are scoped to the exact modules/contracts this ticket's
schema change can plausibly affect (the module under change, its measurement-baseline banned-edit-
path guard, its SQLite-operational-limits doc guard, its `ContextPacket`-import isolation guard, and
— added per Architecture-Review-mandated correction — the redaction module's own version-axis-
independence guard, which reads `retrieval_cache_schema_version` directly and is affected by this
ticket's corrected DD2 constant bump).

## Anti-Drift Test Guards

- Test 7 and the existing `test_migration_does_not_alter_existing_marker_only_table_column_sets`
  together guard against the single highest-value scope-creep vector for this ticket: quietly
  widening `retrieval_provider_result_cache_rows` or any marker-only table's columns "while we're in
  here."
- Test 8 is the direct regression guard for investigation.md's Risk 1 (the shared
  `retrieval_cache_schema_version` module-constant coupling) — without it, a naive "just bump the
  constant to 2" implementation would pass every *new* test while silently breaking two *existing*
  ones, which a scoped-command run would still catch, but Test 8 makes the specific failure mode
  explicit and intentional rather than an incidental side effect discovered late.
- Test 9 guards the Open Question 2 design decision (single JSON column, no junction table) against
  silent redesign by a later ticket that might otherwise "helpfully" normalize
  `evidence_dependencies` into a relational shape without re-confirming the JSON-column contract this
  ticket establishes.
- Test 10 guards the table-naming collision hazard explicitly, since a name collision with the
  existing `retrieval_packet_cache_rows` table would be a silent, extremely hard-to-detect data-
  corruption risk (two logically distinct concepts sharing one table) rather than an obvious error.
- Test 11 guards the Out-of-Scope boundary between this ticket and
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING` — catches an implementer who adds "just a
  stub" read/write function to demonstrate the schema works, which would blur that boundary exactly
  as investigation.md's Anti-Drift Hazards section warns against.
- Test 12 is a second, module-local line of defense for the already-existing
  `tests/docs/test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_implemented`
  guard, so a regression here is caught by the scoped command list above even if a future change to
  `tests/docs/` accidentally weakens or skips that file.
