---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS

## Regression Surface

All existing tests in `tests/tools/test_retrieval_cache.py` must keep passing unmodified in
behavior (one test, `TestCrashRecovery::test_deleted_cache_db_rebuilds_clean_marker_only_schema`,
is explicitly flagged by its own docstring as needing extension by this ticket — see New Tests
Required, not a behavior change to the existing assertions).

- unit (`tests/tools/test_retrieval_cache.py`):
  - `TestIndexCache` (4 tests) — embedding/index cache hit/miss/stale-eviction, unaffected by an
    additive new table.
  - `TestQueryCache` (4 tests) — query-result cache hit/stale-rejected reason codes.
  - `TestPacketCache` (5 tests) — context-packet cache hit/stale-rejected reason codes.
  - `TestMayListEnforcement` (3 tests) — including
    `test_all_three_cache_tables_expose_only_may_list_columns`, which iterates
    `rc._TABLE_NAME_BY_ALIAS.values()` (the 3 marker-only tables only) — must keep passing
    unchanged; the new table is deliberately NOT added to `_TABLE_NAME_BY_ALIAS` by this ticket
    (that dict backs `prune`'s `--table` CLI choices and `cmd_stats`, both scoped to the existing
    3 tables only, per this ticket's Out of Scope on wiring).
  - `TestStaticGuards` (3 tests) — no banned class name, no banned import, cache DB path distinct
    from `knowledge_search.py`'s DB. Must keep passing; the new migration code must not introduce a
    banned import.
  - `TestPrune` (3 tests) — manual eviction backstop for the 3 existing tables only.
  - `TestRetrievalVersionAndManifest` (2 tests) — `_corpus_generation()` sentinel/manifest read
    behavior, unrelated to schema migrations.
  - `TestCrashRecovery` (1 test, to be extended — see below).
- integration/cross-module (must also be run — each directly reads or diffs `tools/retrieval_cache.py`'s
  real source, confirmed via `grep -rl "retrieval_cache" tests/`, not merely mentions it):
  - `tests/tools/test_context_packet_assembler.py` —
    `TestWorkflowIsolationGuards::test_assembler_does_not_import_contextpacket_from_retrieval_cache`
    (lines 418-425) parses `tools/retrieval_cache.py`'s real AST and asserts no `ContextPacket`
    class/import exists in it. Must keep passing — the new migration code must not define or import
    a `ContextPacket` class.
  - `tests/docs/test_redaction_retention_policy_doc.py` —
    `test_sqlite_defaults_not_silently_implemented` (lines 107-125) parses `tools/retrieval_cache.py`'s
    real source/AST and asserts `"PRAGMA"`/`"busy_timeout"`/`"chmod"`/`"os.chmod"` are absent from
    the source text and `"os"` is absent from its imports. **This is the load-bearing regression
    test for the §9-out-of-scope finding in investigation.md** — any migration code that opens a
    connection with a `PRAGMA` statement, sets a busy timeout, or imports `os` to `chmod` the DB
    file will fail this test, correctly.
  - `tests/tools/test_kgmcp_measurement_baseline.py` —
    `test_no_live_gateway_code_or_search_mcp_edits_introduced` (lines 343-356) runs `git diff --stat
    HEAD` and asserts `"tools/retrieval_cache.py"` is absent from the diff. **This test WILL fail
    once this ticket's real edit to `tools/retrieval_cache.py` exists in the working tree/diff —
    this is a known, pre-existing test-suite conflict, not a new regression introduced by this
    ticket's design.** See investigation.md Risks and Open Questions #1. Run it anyway as part of
    the scoped regression pass so the failure is observed and reported honestly (per CLAUDE.md's
    rule against silently routing around a failing gate), not skipped or silently patched to pass.
  - `tests/tools/test_retrieval_events.py` — exercises `wrap_retrieval_cache_check()`
    (`tools/retrieval_events.py`), which imports `HIT`/`MISS`/`STALE_REJECTED`/category constants
    from `tools/retrieval_cache.py` by name. None of those constants change in this ticket; run to
    confirm the import surface those wrappers depend on is untouched.
  - `tests/tools/test_evidence_cache_identity_contract.py` — structural fixture assertions about the
    contract *documents* (§1-§4 field-family split), not about `tools/retrieval_cache.py`'s real
    schema. Not required to change behavior for this ticket, but worth a sanity run since this
    ticket's new columns should be designed to keep those contract field names available for the
    later read/write-wiring ticket to reuse verbatim (see investigation.md Risk 4).
- arena-combat: not applicable — this subsystem is agent-orchestration tooling, no
  simulation/combat code path is affected.

## New Tests Required

All new tests belong in `tests/tools/test_retrieval_cache.py`, following the existing file's
established conventions exactly:
- Reuse the autouse `_isolated_cache_db(tmp_path, monkeypatch)` fixture (lines 33-37) — it already
  monkeypatches `rc.CACHE_DB_PATH` and `rc._MANIFEST_PATH` to `tmp_path`, so every new test gets an
  isolated, empty DB path per test with zero extra setup.
- Follow the file's "Duration-is-not-behavior guard" convention (top-of-file docstring) — none of
  these new tests concern time-based eviction, so it does not constrain them, but no new test should
  introduce a duration-based assertion either.
- New tests exercise `migration_001_add_level1_tables(conn)` (and, if Plan decides to add it,
  `retrieval_cache_schema_version`-reading helper functions) directly via `rc._get_connection()` /
  raw `sqlite3.Connection`, mirroring how existing tests call `conn.execute(...)` directly
  (e.g. `TestIndexCache.test_recompute_on_chunking_version_change`, lines 70-83).

1. **`test_migration_applies_cleanly_to_a_fresh_database`**
   - Category: unit
   - Verifies: calling the migration path against a brand-new (nonexistent-until-now) DB file
     creates both the pre-existing 3 marker-only tables (via `_init_schema()`, already called by
     `_get_connection()`) AND the new Level 1 table(s) AND `retrieval_cache_generation`, with no
     exception raised.
   - Location: `tests/tools/test_retrieval_cache.py`, new `TestMigrations` class.

2. **`test_migration_applies_cleanly_on_top_of_existing_legacy_schema_with_zero_data_loss`**
   - Category: unit
   - Verifies: seed a DB via the *existing* `_get_connection()`/`_init_schema()` path (i.e. only the
     3 marker-only tables), write at least one real row into each of the 3 existing tables (via
     `write_index_cache`/`write_query_cache`/`write_packet_cache`, exactly as
     `TestCrashRecovery`'s existing test does at lines 330-332), then run the migration. Assert:
     (a) migration succeeds without exception, (b) all 3 previously-written rows are still present
     and byte-identical (re-`SELECT *` and compare), (c) the new Level 1 table now exists and is
     empty. This is the concrete "zero data loss" proof the ticket's Acceptance Criteria require —
     not just "the migration ran," but "nothing already there was lost."
   - Location: `tests/tools/test_retrieval_cache.py`, `TestMigrations`.

3. **`test_new_table_column_set_matches_proposal_section_10_2_row_shape`**
   - Category: unit (structural/architecture guard)
   - Verifies: `PRAGMA table_info(<new_table_name>)` returns exactly the column set Plan's chosen
     schema commits to, mapped 1:1 against §10.2's categorical row-shape bullets (keyed query hash,
     deterministic intent, resolved provider-native entity IDs, filters, provider name, adapter
     version, result payload, source IDs and paths, evidence hashes, provider generation,
     repository/branch scope, timestamps, hit counters) — every bullet has at least one
     corresponding column, and no extraneous column exists outside that mapping. Model this test
     directly on the existing
     `TestMayListEnforcement.test_all_three_cache_tables_expose_only_may_list_columns` pattern
     (lines 162-174: `PRAGMA table_info` + set-comparison against a documented allowlist) — the new
     table should get its own equivalent allowlist constant (name TBD by Plan, e.g.
     `LEVEL1_CACHE_COLUMNS`), asserted the same way.
   - Location: `tests/tools/test_retrieval_cache.py`, `TestMigrations` (or a dedicated
     `TestLevel1Schema` class if Plan prefers separating structural assertions from migration-
     mechanics assertions).

4. **`test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration`**
   - Category: unit
   - Verifies: after running the migration against a fresh DB, `SELECT retrieval_cache_schema_version
     FROM retrieval_cache_generation` returns exactly `1` (the first migration's target version,
     matching `migration_001`'s ordinal), and `migrated_at` is a real, recent `time.time()`-shaped
     float (non-null, not a placeholder/sentinel). Also assert exactly one row exists in
     `retrieval_cache_generation` after a single migration run (not accumulating one row per
     migration call — confirms "updated in place," per `cache_migration_plan.md` §1's explicit
     divergence from `parity_index.py`'s append-style pattern).
   - Location: `tests/tools/test_retrieval_cache.py`, `TestMigrations`.

5. **`test_migration_is_idempotent_when_run_twice`**
   - Category: unit
   - Verifies: running the migration function twice in a row against the same DB (a) raises no
     exception the second time, (b) leaves `retrieval_cache_generation` at exactly one row with the
     same `retrieval_cache_schema_version` value (not two rows, not an incremented value from a
     second no-op application), (c) leaves the new table's schema (`PRAGMA table_info`) byte-
     identical between the two runs, (d) preserves any rows already written to the new table (write
     one row after the first migration call, run the migration again, assert the row still exists
     unchanged).
   - Location: `tests/tools/test_retrieval_cache.py`, `TestMigrations`.

6. **`test_migration_does_not_alter_existing_marker_only_table_column_sets`**
   - Category: unit (architecture guard)
   - Verifies: `PRAGMA table_info()` for each of `retrieval_index_cache_rows`,
     `retrieval_query_cache_rows`, `retrieval_packet_cache_rows`, taken before vs. after running the
     migration, are byte-identical (same column names, types, order, PK flags). This directly
     proves the "no `ALTER TABLE ADD COLUMN` against existing tables" acceptance criterion at the
     schema-introspection level, not just "the existing tests still pass" (which only proves
     behavior, not schema shape).
   - Location: `tests/tools/test_retrieval_cache.py`, `TestMigrations`.

7. **`test_retrieval_cache_schema_version_constant_is_distinct_from_the_other_three_version_axes`**
   - Category: unit (naming/architecture guard, directly proves AC1)
   - Verifies: `rc.retrieval_cache_schema_version` (or wherever Plan places the constant) is a
     distinct Python identifier from `rc.RETRIEVAL_VERSION`, has a different value or is at minimum
     never assigned from/aliased to it (`retrieval_cache_schema_version is not RETRIEVAL_VERSION`
     as objects is trivially true for ints — assert instead that they are declared as two separate
     module-level names, e.g. via `ast`-parsing the source, matching the existing
     `TestStaticGuards` pattern of AST-based structural assertions at lines 216-239), and that
     `tools/retrieval_events.py::retrieval_event_schema_version` is untouched (import it and assert
     its value/location is unchanged from before this ticket — a simple existing-value snapshot
     comparison is sufficient, no need to re-derive the whole module).
   - Location: `tests/tools/test_retrieval_cache.py`, `TestMigrations` or `TestStaticGuards`.

8. **Extend `TestCrashRecovery::test_deleted_cache_db_rebuilds_clean_marker_only_schema`** (modify,
   not purely additive) — its own docstring (lines 322-329) already commits to this: "A future
   ticket that adds payload tables must extend this test, not treat it as already covering that
   case." Add a sibling test,
   **`test_deleted_cache_db_rebuild_does_not_silently_resurrect_level1_payload_rows`**, that: writes
   into the new Level 1 table (after migrating), deletes `rc.CACHE_DB_PATH`, calls
   `rc._get_connection()` (today's rebuild path, which only re-runs `_init_schema()` — confirm
   whether `_get_connection()` also needs to run the migration for the new table to reappear after a
   raw delete, and assert whichever real behavior is correct: either the new table is simply gone
   post-delete-and-reconnect until `migration_001` is explicitly re-run, or `_get_connection()` is
   changed by this ticket to also apply migrations on every connect — Plan must decide which, and
   this test must assert the decided behavior, not assume one silently).
   - Category: unit (regression-prevention / crash-recovery)
   - Location: `tests/tools/test_retrieval_cache.py`, `TestCrashRecovery`.

## Scoped Pytest Commands

```
pytest tests/tools/test_retrieval_cache.py tests/tools/test_context_packet_assembler.py \
  tests/docs/test_redaction_retention_policy_doc.py tests/tools/test_retrieval_events.py \
  tests/tools/test_evidence_cache_identity_contract.py -v
```

Run `tests/tools/test_kgmcp_measurement_baseline.py` separately and report its result honestly
rather than folding it into the main scoped command's pass/fail signal, since
`test_no_live_gateway_code_or_search_mcp_edits_introduced` is expected to fail once this ticket's
real diff exists (see Regression Surface above) — this is a known pre-existing conflict to surface
to Plan/Verify, not a signal this ticket's own new tests are broken:

```
pytest tests/tools/test_kgmcp_measurement_baseline.py -v
```

If Plan's implementation touches `tools/parity_index.py`'s naming precedent in any way (it should
not — read-only citation per the frozen design), additionally run:

```
pytest tests/tools/test_parity_index.py -v
```

Never `pytest tests/` (unscoped) and never `pytest -m "not slow"` alone — this ticket's affected
surface is a single, fast, dependency-free file plus a handful of tests in other files that read its
source; the scoped commands above are sufficient and should complete in well under a few seconds per
the existing suite's current profile (no ML dependency, no heavy network I/O beyond the one bounded
live-search smoke test already inside `test_kgmcp_measurement_baseline.py`, no `time.sleep`).

## Anti-Drift Test Guards

- `TestMayListEnforcement.test_all_three_cache_tables_expose_only_may_list_columns` (existing,
  unmodified) — iterates only `rc._TABLE_NAME_BY_ALIAS.values()`. If a future edit accidentally adds
  the new Level 1 table's name into `_TABLE_NAME_BY_ALIAS`, this existing test's iteration silently
  starts checking the new table's columns against `MAY_LIST_COLUMNS` (which does not, and should
  not, contain the new table's column names) and would start failing loudly — this is by design; do
  not "fix" it by adding the new table's columns into `MAY_LIST_COLUMNS`, since that frozenset is
  specifically scoped to the 3 marker-only tables' MAY-list contract with
  `retrieval_retention_redaction_policy.md`'s Decision C, a different (already-shipped, unrelated)
  policy document from the one that governs the new table.
- `TestStaticGuards.test_no_import_from_out_of_scope_modules` (existing, unmodified) — the migration
  code must not import `src.observability.reporting.retention`, `src.core.retention`, or
  `src.engine.world_index`. Since this ticket adds new code to the same file, re-running this test
  is the direct proof the new code didn't accidentally reach for one of those.
- New: **`test_migration_001_function_is_never_called_from_any_check_or_write_function`** — mirrors
  `TestPrune.test_prune_is_not_invoked_by_any_check_or_write_function`'s pattern (inspect
  `inspect.getsource()` of each `check_*_cache`/`write_*_cache` function and assert
  `"migration_001"` does not appear) — guards against a future edit accidentally auto-triggering a
  schema migration from a hot cache-check path, which would violate the "no read/write logic against
  the new table" Out-of-Scope boundary and could introduce a surprising write-amplification/locking
  cost on every cache check.
- New: **`test_no_migrate_or_rebuild_subcommand_added_to_cli`** — asserts `"migrate"` and
  `"rebuild"` are not keys in `rc._COMMAND_DISPATCH` and do not appear as subparser names in
  `rc._build_parser()`'s subparsers — directly guards the Anti-Drift Hazard above (§5 of
  `cache_migration_plan.md` freezes both as design-only; a well-meaning implementer wiring them "for
  completeness" is exactly the drift this test exists to catch).
- New: **`test_new_table_and_generation_table_absent_from_prune_table_alias_map`** — asserts
  `"retrieval_cache_generation"` and the new Level 1 table's name are not present in
  `rc._TABLE_NAME_BY_ALIAS`'s values, so `prune --table all` cannot accidentally start deleting rows
  from the new table under a lifecycle policy this ticket never defined (GC defaults for the new
  table are a later ticket's job per `redaction_retention_policy.md` §10).
- `tests/tools/test_evidence_cache_identity_contract.py` (existing, out of this ticket's Regression
  Surface but worth a manual sanity check, not a required scoped-command run) — its structural
  fixture assertions about the lookup/validity field-family split are about the *contract document*,
  not about `tools/retrieval_cache.py`'s real schema yet; this ticket does not need to make that file
  pass differently, but if Plan's real column names diverge from the contract's literal field names
  (§1/§2) without a documented reason, that divergence should be visible when
  `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` later tries to wire real lookup logic against
  whatever column names this ticket actually ships.
