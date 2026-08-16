---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS

## Summary

Implement the frozen `cache_migration_plan.md` design as real code inside `tools/retrieval_cache.py`:
a new `retrieval_cache_schema_version` constant, a new single-row `retrieval_cache_generation`
metadata table, and one new `CREATE TABLE IF NOT EXISTS`-only migration function,
`migration_001_add_level1_tables(conn)`, that adds a new Level 1 provider-result payload table
(`retrieval_provider_result_cache_rows`). The new table's columns reuse
`evidence_cache_identity_contract.md` §1/§2's literal field names verbatim for every concept those
sections name, and invent new names only for the `docs/plans/knowledge-gateway-mcp-proposal.md`
§10.2 concepts that have no contract-literal counterpart (keyed hash, provider name/adapter
version/generation as write-time provenance, result payload, source IDs/paths, timestamps, hit
counter). The three existing marker-only tables and every existing public function are left
byte-for-byte behaviorally unchanged — no `ALTER TABLE`, no new call site into `_get_connection()`'s
or any `check_*_cache()`/`write_*_cache()` function's existing hot paths. A pre-existing, now-stale
test assertion in `tests/tools/test_kgmcp_measurement_baseline.py` (written before this ticket
existed, when no future ticket had legitimate reason to touch `tools/retrieval_cache.py`) is
narrowed to drop that one path from its "must stay untouched" list, with a comment explaining why,
while keeping its guarantee for the other four paths intact.

## Design Decisions

### DD1 — Frozen design confirmed consistent with `tools/retrieval_cache.py`'s existing patterns

Verified directly, not inferred: `_init_schema()` (`tools/retrieval_cache.py:108-152`) issues three
`conn.execute(CREATE TABLE IF NOT EXISTS ...)` calls followed by one `conn.commit()` — exactly the
shape `cache_migration_plan.md` §2 (`docs/engine/contracts/knowledge_gateway_mcp/
cache_migration_plan.md:96-101`) specifies each migration function must reuse. `_get_connection()`
(`tools/retrieval_cache.py:96-105`) unconditionally calls `_init_schema(conn)` on every connect and
never deletes/unlinks the file — this is the "cheap no-op when already applied" precedent the frozen
plan's future `migrate` entry point (not built by this ticket) is designed to mirror
(`cache_migration_plan.md:105-109`). No migration library exists in this repo's dependency files
(confirmed by the frozen plan's own investigation, `cache_migration_plan.md:79-82`) — hand-written
SQL functions are the only consistent approach, matching what this ticket implements.

### DD2 — No PRAGMA/busy_timeout/chmod/`import os` anywhere in `tools/retrieval_cache.py`

Read directly: `tests/docs/test_redaction_retention_policy_doc.py:107-125`
(`test_sqlite_defaults_not_silently_implemented`) does exactly four checks against
`tools/retrieval_cache.py`'s real source text/AST: `"PRAGMA" not in source`,
`"busy_timeout" not in source`, `"os.chmod" not in source` and `"chmod" not in source` (both
literal-substring checks, so `"chmod"` alone bans any spelling), and `"os" not in imported_modules`
(AST-derived from `ast.Import`/`ast.ImportFrom` nodes only — not a substring check, so a variable or
string merely containing the letters "os" is fine, only a real `import os` / `from os import ...`
statement trips it). **Design implication:** `migration_001_add_level1_tables(conn)` must use only
`conn.execute(...)` and `conn.commit()` (the same primitives `_init_schema()` already uses,
`tools/retrieval_cache.py:108-152`) — no `conn.execute("PRAGMA ...")` call, no `sqlite3.connect(...,
timeout=...)` change (that keyword is unrelated to the banned string `"busy_timeout"` and is not
touched), no file-permission code, no `import os`. Timestamps use `time.time()` (already imported at
`tools/retrieval_cache.py:37`), identical to every existing `write_*_cache()` function.

### DD3 — `test_kgmcp_measurement_baseline.py`'s stale assumption is corrected, not routed around

Read directly: `test_no_live_gateway_code_or_search_mcp_edits_introduced`
(`tests/tools/test_kgmcp_measurement_baseline.py:343-357`) runs `git diff --stat HEAD` and asserts a
fixed 5-path tuple — `tools/search_mcp.py`, `tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`,
`tools/context_packet_assembler.py`, `tools/retrieval_events.py` — is absent from the diff, with
message `f"{banned_path} must never be edited by this ticket (Out of Scope)"`. That assertion was
correct for the ticket it was written for
(`TCK-20260814-KGMCP-MEASUREMENT-BASELINE`, whose own scope explicitly excluded all five files) but
has no ticket-window awareness — it unconditionally diffs the live working tree against `HEAD` every
run. This ticket's own approved Scope is to edit exactly one of those five paths
(`tools/retrieval_cache.py`). Per CLAUDE.md's hard rule against editing an artifact merely to make a
gate pass — this is the reverse case, a stale ticket-scoped assertion genuinely outdated by this
ticket's own approved Scope, ruled on explicitly by Architecture Review rather than assumed —
**Step 6 below removes only `"tools/retrieval_cache.py"` from that tuple, with an inline comment
citing this ticket ID and
explaining why, and leaves the other four paths (`search_mcp.py`, `hybrid_retrieval.py`,
`context_packet_assembler.py`, `retrieval_events.py`) in the tuple unchanged** — none of those four
are touched by this ticket's scope, so the test's real remaining guarantee (those four still never
get silently edited by a mis-scoped future change) is preserved undiminished.

### DD4 — `cache_migration_plan.md`'s §10.1/§10.3 citation is left uncorrected

Read directly: `cache_migration_plan.md:86-94` cites `migration_001_add_level1_tables` as "per §10.1
of the proposal" and `migration_002_add_level2_tables` as "per §10.3." Reading
`docs/plans/knowledge-gateway-mcp-proposal.md` directly, §10.1 is "Storage" (the evolve-in-place
directive) and §10.2 is "Cache Levels" (containing the actual Level 1 row-shape bullet list this
ticket implements) — the frozen plan's inline citation is off-by-one against the proposal's real
section numbers. `cache_migration_plan.md` is a frozen contract from a DONE ticket
(`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`); this ticket does not edit it. This plan and its
implementer cite proposal §10.2 (not §10.1) as the authoritative source for the Level 1 row shape
throughout. **Docs-to-update note for Document-Update phase:** whether to fix the citation inside the
frozen doc itself is that phase's call, not this plan's — see "Docs to Update" below for the
reasoning either way.

### DD5 — Level 1 table column mapping: proposal §10.2 bullets → contract §1/§2 literal names → new columns

`docs/plans/knowledge-gateway-mcp-proposal.md` §10.2's Level 1 row shape is a *categorical* bullet
list, not literal SQL column names (confirmed: no `docs/plans/` file defines SQL DDL). Where a §10.2
concept has a literal name in `evidence_cache_identity_contract.md` §1 (lookup identity,
`docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md:36-46`) or §2
(evidence-validity identity, same file `:80-88`), that literal name is used verbatim as the column
name — per this ticket's own Related Tickets note that
`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s Scope already commits to reusing
`normalized_intent, resolved_entity_ids, filters, budget_class, routing_policy_version,
repo_branch_scope` for real lookup logic, so shipping any other name now would force a rename later
for no reason. §3's Non-collapse rule (`evidence_cache_identity_contract.md:100-121`) explicitly
allows a single row to carry both families ("a table row *may* carry both lookup-identity and
validity-identity fields ... the proposal's own §10.2 Level 1 row shape does") provided no column
name is shared between the two families — verified below, zero overlap.

Two §10.2 concepts — "adapter version" and "provider generation" — are **not** the same thing as the
contract's `adapter_version_at_validation` / `provider_generation_at_validation` (§2 fields, computed
at a later validity-check step, per §2's own "at validation" naming and §4's fallback-rule framing).
The Level 1 row's own write-time provenance stamp (what adapter/generation produced *this* cached
result) is a distinct concept from the check-time value a later validity check will compare against
it — collapsing them into one column would violate the exact Non-collapse principle
`evidence_cache_identity_contract.md` §3 exists to enforce, just one level removed (a write-time
provenance value silently standing in for a check-time verdict). This plan therefore adds **both**:
a Plan-invented `adapter_version` / `provider_generation` pair (write-time provenance, no
contract-literal name exists for this) **and** the contract-literal
`adapter_version_at_validation` / `provider_generation_at_validation` pair (reserved for the
read-write-wiring ticket to populate at check time) as separate columns.

Full mapping (this table is authoritative for the Step 2/Step 4 "matches §10.2 exactly" test — see
Acceptance Criteria Map):

| §10.2 bullet | Column(s) | Source of name |
|---|---|---|
| keyed query hash | `query_hash` | Plan-invented; precedent naming from `retrieval_query_cache_rows.query_hash` (`tools/retrieval_cache.py:126`), different table so no SQL collision |
| deterministic intent | `normalized_intent` | contract §1, verbatim |
| resolved provider-native entity IDs | `resolved_entity_ids` | contract §1, verbatim |
| filters | `filters` | contract §1, verbatim |
| (repository/branch scope, listed separately below, doubles as part of the lookup tuple) | `repo_branch_scope` | contract §1, verbatim |
| (lookup tuple's remaining 2 fields, not individually named in §10.2's bullets but part of the same lookup-identity tuple §10.2's prose describes) | `budget_class`, `routing_policy_version` | contract §1, verbatim |
| provider name | `provider_name` | Plan-invented, no contract-literal name |
| adapter version | `adapter_version` | Plan-invented write-time provenance value, distinct from `adapter_version_at_validation` (see above) |
| result payload | `result_payload` | Plan-invented, no contract-literal name |
| source IDs and paths | `source_ids`, `source_paths` | Plan-invented, split into two JSON-array columns for future changed-paths intersection use (contract §5) |
| evidence hashes | `evidence_fingerprints` | contract §2, verbatim |
| provider generation | `provider_generation` | Plan-invented write-time provenance value, distinct from `provider_generation_at_validation` (see above) |
| repository/branch scope | `repo_branch_scope` | contract §1, verbatim (same column as above — one bullet, one field) |
| (validity tuple's remaining fields, reserved for the read-write-wiring ticket, present now per contract §3's explicit allowance) | `validated_negative_scopes`, `adapter_version_at_validation`, `working_tree_overlap`, `provider_generation_at_validation` | contract §2, verbatim |
| timestamps | `created_at`, `last_hit_at` | Plan-invented; `created_at` matches the existing 3-table naming convention exactly (e.g. `tools/retrieval_cache.py:118`) |
| hit counters | `hit_count` | Plan-invented |

Every column in the new table traces to exactly one row of this table — no extraneous column, no
§10.2 concept left unmapped. This mapping is the literal content of the `LEVEL1_CACHE_COLUMNS`
allowlist constant Step 2 adds, and it is the exact assertion Step 4's structural test checks against.

### DD6 — `_get_connection()` and `_init_schema()` are not modified; the Level 1 table does not
survive a raw file delete until `migration_001` is re-run

`cache_migration_plan.md` §5 (`cache_migration_plan.md:145-165`) freezes both `migrate` and
`rebuild` as design-only, explicitly "not added... by this ticket." If `migration_001_add_level1_
tables` were folded into `_init_schema()` (called unconditionally by `_get_connection()` on every
connect, `tools/retrieval_cache.py:96-105`), that would functionally build the `migrate` entry
point's auto-apply-on-connect behavior under a different name — the exact scope creep §5 forbids, and
it would make `migration_001_add_level1_tables` pointless as an independently-callable, separately
gated function per §2's own function-list design. **Decision:** `_init_schema()` keeps creating only
the three existing marker-only tables, unchanged. `migration_001_add_level1_tables(conn)` is a
separate function, never called from `_get_connection()`, `_init_schema()`, or any
`check_*_cache()`/`write_*_cache()`/`prune()` function. Consequence, and the exact behavior Step 5's
new crash-recovery test asserts: after `rc.CACHE_DB_PATH.unlink()` followed by `rc._get_connection()`
(today's only rebuild path), the three marker-only tables reappear (as today) but the Level 1 table
and `retrieval_cache_generation` do **not** — they stay absent until `migration_001_add_level1_
tables` is explicitly invoked again. This is intentional, not a gap: a `migrate`-on-every-connect
policy is exactly what §5 defers to a future ticket.

### DD7 — Table name and non-membership in `_TABLE_NAME_BY_ALIAS`/`MAY_LIST_COLUMNS`

New table name: `retrieval_provider_result_cache_rows`, following the existing
`retrieval_<level>_cache_rows` naming convention (`retrieval_index_cache_rows`,
`retrieval_query_cache_rows`, `retrieval_packet_cache_rows`, all confirmed at
`tools/retrieval_cache.py:111,125,141`). It is **not** added to `_TABLE_NAME_BY_ALIAS`
(`tools/retrieval_cache.py:399-403`, backs `prune --table` choices and `cmd_stats`'s iteration) and
its columns are **not** added to `MAY_LIST_COLUMNS` (`tools/retrieval_cache.py:70-89`, the
write-path-validation allowlist scoped to the 3 marker-only tables under
`retrieval_retention_redaction_policy.md` Decision C) — both per this ticket's Out of Scope (no
read/write logic, no lifecycle/GC policy decided yet for the new table) and confirmed as the correct
behavior by `TestMayListEnforcement.test_all_three_cache_tables_expose_only_may_list_columns`'s
existing iteration-scope (`tests/tools/test_retrieval_cache.py:161-174`, iterates
`_TABLE_NAME_BY_ALIAS.values()` only) and `TestPrune`'s existing 3-table-only scope
(`tests/tools/test_retrieval_cache.py:251-300`).

## Steps

### Step 1 — Add the `retrieval_cache_schema_version` module constant

**Files:** `tools/retrieval_cache.py`

**Change:** Add, immediately after `RETRIEVAL_VERSION: int = 1` (`tools/retrieval_cache.py:45`), a
new module-level constant:

```python
# DDL/table-shape version for this module's migrations (cache_migration_plan.md §1) — distinct
# from RETRIEVAL_VERSION above (cache-key-derivation logic) and from
# tools/retrieval_events.py::retrieval_event_schema_version (event-field shape). Bumped once per
# new migration function added, never aliased to either sibling constant.
retrieval_cache_schema_version: int = 1
```

This mirrors the distinctness comment `tools/retrieval_events.py:43-46` already uses for
`retrieval_event_schema_version` when explaining its own separation from `RETRIEVAL_VERSION` — same
pattern, third axis. Per `cache_migration_plan.md:26-48` (§1), the name must be exactly
`retrieval_cache_schema_version`, never `schema_version`.

**Do NOT touch:** `RETRIEVAL_VERSION` (line 45) or its value; `tools/retrieval_events.py`'s
`retrieval_event_schema_version` (line 46 of that file) — read-only citation only, no edit to that
file (it is not in this ticket's Related Code Areas and no change to event-field shape is in scope).

**Verify:** `test_retrieval_cache_schema_version_constant_is_distinct_from_the_other_three_version_
axes` (Step 4).

### Step 2 — Add the `LEVEL1_CACHE_COLUMNS` allowlist constant documenting the new table's column set

**Files:** `tools/retrieval_cache.py`

**Change:** Add a new module-level frozenset constant, placed near `MAY_LIST_COLUMNS`
(`tools/retrieval_cache.py:70-89`) but clearly separated with its own comment block, listing every
column of the new `retrieval_provider_result_cache_rows` table per DD5's mapping table above:

```python
# Column set for the new Level 1 provider-result cache table (retrieval_provider_result_cache_rows),
# mapped 1:1 onto docs/plans/knowledge-gateway-mcp-proposal.md §10.2's Level 1 row-shape bullets and
# evidence_cache_identity_contract.md §1/§2's literal field names — see plan.md DD5 for the full
# per-column provenance table. NOT a write-path validation allowlist (unlike MAY_LIST_COLUMNS) —
# this ticket ships no write function for this table; this constant exists so the structural test
# below and the later read-write-wiring ticket have one documented source of truth for the column
# set, not two.
LEVEL1_CACHE_COLUMNS: frozenset[str] = frozenset(
    {
        "query_hash",
        "normalized_intent",
        "resolved_entity_ids",
        "filters",
        "budget_class",
        "routing_policy_version",
        "repo_branch_scope",
        "provider_name",
        "adapter_version",
        "result_payload",
        "source_ids",
        "source_paths",
        "provider_generation",
        "evidence_fingerprints",
        "validated_negative_scopes",
        "adapter_version_at_validation",
        "working_tree_overlap",
        "provider_generation_at_validation",
        "created_at",
        "last_hit_at",
        "hit_count",
    }
)
```

**Do NOT touch:** `MAY_LIST_COLUMNS` itself (`tools/retrieval_cache.py:70-89`) — do not add any of
these 21 names into it; that frozenset's write-path-validation role is scoped to the 3 marker-only
tables only (DD7).

**Verify:** `test_new_table_column_set_matches_proposal_section_10_2_row_shape` (Step 4) — asserts
`PRAGMA table_info(retrieval_provider_result_cache_rows)` returns exactly `LEVEL1_CACHE_COLUMNS`.

### Step 3 — Implement `migration_001_add_level1_tables(conn)`

**Files:** `tools/retrieval_cache.py`

**Change:** Add a new function, placed after `_init_schema()` (`tools/retrieval_cache.py:108-152`)
under a new `# Migrations (Level 1 provider-result cache, TCK-20260815-KGMCP-P2-CACHE-SCHEMA-
MIGRATIONS)` section header:

```python
def migration_001_add_level1_tables(conn: sqlite3.Connection) -> None:
    """Adds the Level 1 provider-result cache table plus the retrieval_cache_generation metadata
    table, per cache_migration_plan.md §1/§2. CREATE TABLE IF NOT EXISTS only — additive, never
    touches the three existing marker-only tables. Idempotent: safe to call again on a database
    that already has this migration applied. Not called by _get_connection(), _init_schema(), or
    any check_*_cache()/write_*_cache()/prune() function (see plan.md DD6) — must be invoked
    directly.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_cache_generation (
            retrieval_cache_schema_version INTEGER NOT NULL,
            migrated_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_provider_result_cache_rows (
            query_hash TEXT NOT NULL,
            normalized_intent TEXT NOT NULL,
            resolved_entity_ids TEXT NOT NULL,
            filters TEXT NOT NULL,
            budget_class TEXT,
            routing_policy_version TEXT NOT NULL,
            repo_branch_scope TEXT NOT NULL,
            provider_name TEXT NOT NULL,
            adapter_version TEXT NOT NULL,
            result_payload TEXT NOT NULL,
            source_ids TEXT NOT NULL,
            source_paths TEXT NOT NULL,
            provider_generation TEXT NOT NULL,
            evidence_fingerprints TEXT NOT NULL,
            validated_negative_scopes TEXT,
            adapter_version_at_validation TEXT,
            working_tree_overlap TEXT,
            provider_generation_at_validation TEXT,
            created_at REAL NOT NULL,
            last_hit_at REAL,
            hit_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (query_hash, repo_branch_scope)
        )
        """
    )
    conn.execute("DELETE FROM retrieval_cache_generation")
    conn.execute(
        "INSERT INTO retrieval_cache_generation "
        "(retrieval_cache_schema_version, migrated_at) VALUES (?, ?)",
        (retrieval_cache_schema_version, time.time()),
    )
    conn.commit()
```

The `DELETE` + `INSERT` pair (rather than `UPDATE`) keeps `retrieval_cache_generation` at exactly
one row regardless of how many times the function runs, satisfying `cache_migration_plan.md:62-70`'s
"updated in place... once per successfully-applied migration" divergence from `parity_index.py`'s
append-style `ledger_generation` pattern — confirmed by reading `cache_migration_plan.md:50-70`
directly, not inferred.

**Other writers to this same file/connection (enumerated, per fact-verification requirement):**
`_get_connection()` is the sole opener of `CACHE_DB_PATH`
(`tools/retrieval_cache.py:96-105`), called from 8 existing sites:
`check_index_cache`, `write_index_cache`, `check_query_cache`, `write_query_cache`,
`check_packet_cache`, `write_packet_cache`, `prune`, `cmd_stats`. Every one of these opens its own
connection, does its own `conn.execute`/`conn.commit()`, and closes via its own `finally: conn.close()`
— none of them call `migration_001_add_level1_tables`, and this step adds no call from any of them
into it (confirmed no edit to any of those 8 functions). Because each function opens and closes its
own connection and SQLite's default `sqlite3.connect()` uses a normal on-disk file with the
library's default locking, a `migration_001_add_level1_tables(conn)` call and any of these 8
functions' calls are never in-flight on the *same* connection object, and neither this ticket nor
any existing function introduces threading/multiprocessing — so no new race condition is introduced
beyond what the existing `_get_connection()`-per-call pattern already tolerates for the 3 existing
tables. `tools/retrieval_events.py::wrap_retrieval_cache_check()` imports `HIT`/`MISS`/
`STALE_REJECTED` by name (`tools/retrieval_cache.py:60-62`) — untouched by this step, no interaction.

**Do NOT touch:** `_init_schema()` (do not add the new `CREATE TABLE` statements there — see DD6);
`retrieval_index_cache_rows`, `retrieval_query_cache_rows`, `retrieval_packet_cache_rows` (no
`ALTER TABLE` against any of them); no `PRAGMA`, `busy_timeout`, `chmod`, or `import os` anywhere in
this function or file (DD2).

**Verify:** `test_migration_applies_cleanly_to_a_fresh_database`,
`test_migration_applies_cleanly_on_top_of_existing_legacy_schema_with_zero_data_loss`,
`test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration`,
`test_migration_is_idempotent_when_run_twice`,
`test_migration_does_not_alter_existing_marker_only_table_column_sets` (all Step 4).

### Step 4 — Add the `TestMigrations` test class

**Files:** `tests/tools/test_retrieval_cache.py`

**Change:** Add a new `class TestMigrations:` block (placed after `TestPrune`,
`tests/tools/test_retrieval_cache.py:251-300`, before `TestRetrievalVersionAndManifest`), containing
these tests, each following the file's existing conventions exactly (autouse `_isolated_cache_db`
fixture at `tests/tools/test_retrieval_cache.py:33-37` already isolates `rc.CACHE_DB_PATH` per test —
no extra setup needed; call `rc._get_connection()` / raw `sqlite3.Connection` directly, mirroring
`TestIndexCache.test_recompute_on_chunking_version_change`'s direct-`conn.execute` pattern):

1. `test_migration_applies_cleanly_to_a_fresh_database` — call `rc._get_connection()` (creates the 3
   marker tables via `_init_schema`), then `rc.migration_001_add_level1_tables(conn)` on that same
   connection; assert no exception, and that `sqlite_master` lists all 3 marker tables plus
   `retrieval_provider_result_cache_rows` plus `retrieval_cache_generation`.
2. `test_migration_applies_cleanly_on_top_of_existing_legacy_schema_with_zero_data_loss` — seed via
   `rc.write_index_cache(...)`, `rc.write_query_cache(...)`, `rc.write_packet_cache(...)` (same calls
   `TestCrashRecovery`'s existing test already uses, `tests/tools/test_retrieval_cache.py:330-332`),
   run `rc.migration_001_add_level1_tables(conn)` on a fresh connection to the same DB file, then
   re-`SELECT *` all 3 marker tables and assert every previously-written row is still present,
   byte-identical; assert `retrieval_provider_result_cache_rows` exists and is empty.
3. `test_new_table_column_set_matches_proposal_section_10_2_row_shape` — `PRAGMA table_info
   (retrieval_provider_result_cache_rows)` after migration; assert the resulting column-name set
   equals `rc.LEVEL1_CACHE_COLUMNS` exactly (not merely a subset), modeled directly on
   `TestMayListEnforcement.test_all_three_cache_tables_expose_only_may_list_columns`
   (`tests/tools/test_retrieval_cache.py:162-174`).
4. `test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration` — after migrating
   a fresh DB, `SELECT retrieval_cache_schema_version, migrated_at FROM retrieval_cache_generation`
   returns exactly one row, `retrieval_cache_schema_version == 1`, `migrated_at` is a real recent
   float (`abs(migrated_at - time.time()) < 5`).
5. `test_migration_is_idempotent_when_run_twice` — call `rc.migration_001_add_level1_tables(conn)`
   twice on the same connection; assert no exception on the second call, exactly one row in
   `retrieval_cache_generation` with the same `retrieval_cache_schema_version` value, `PRAGMA
   table_info(retrieval_provider_result_cache_rows)` identical before/after the second call, and a
   row manually inserted into the new table between the two migration calls still present afterward.
6. `test_migration_does_not_alter_existing_marker_only_table_column_sets` — capture `PRAGMA
   table_info()` for all 3 marker tables before running the migration and again after; assert
   byte-identical (same names, types, order, PK flags) for each of the 3.
7. `test_retrieval_cache_schema_version_constant_is_distinct_from_the_other_three_version_axes` —
   AST-parse `tools/retrieval_cache.py`'s source (mirroring `TestStaticGuards`'s existing AST pattern,
   `tests/tools/test_retrieval_cache.py:216-239`) and assert `retrieval_cache_schema_version` and
   `RETRIEVAL_VERSION` are declared as two separate module-level assignment targets; separately,
   `import tools.retrieval_events as re_mod` and assert `re_mod.retrieval_event_schema_version == 1`
   is unchanged from its pre-ticket value (a simple snapshot comparison, no re-derivation).
8. `test_migration_001_function_is_never_called_from_any_check_or_write_function` — mirrors
   `TestPrune.test_prune_is_not_invoked_by_any_check_or_write_function`
   (`tests/tools/test_retrieval_cache.py:288-300`): `inspect.getsource()` each of the 6
   `check_*_cache`/`write_*_cache` functions and assert `"migration_001"` does not appear in any of
   them.
9. `test_no_migrate_or_rebuild_subcommand_added_to_cli` — assert `"migrate"` and `"rebuild"` are not
   keys in `rc._COMMAND_DISPATCH` (`tools/retrieval_cache.py:515-521`) and do not appear as
   subparser names added inside `rc._build_parser()`.
10. `test_new_table_and_generation_table_absent_from_prune_table_alias_map` — assert
    `"retrieval_cache_generation"` and `"retrieval_provider_result_cache_rows"` are not present in
    `rc._TABLE_NAME_BY_ALIAS.values()` (`tools/retrieval_cache.py:399-403`).

**Do NOT touch:** any existing test class or test method in this file (`TestIndexCache`,
`TestQueryCache`, `TestPacketCache`, `TestMayListEnforcement`, `TestStaticGuards`, `TestPrune`,
`TestRetrievalVersionAndManifest`) — all must keep passing unmodified.

**Verify:** running
`pytest tests/tools/test_retrieval_cache.py -v` (all tests, including the 10 new ones above, pass).

### Step 5 — Extend `TestCrashRecovery` with the Level 1 payload-row test

**Files:** `tests/tools/test_retrieval_cache.py`

**Change:** Add a new test method to the existing `class TestCrashRecovery:`
(`tests/tools/test_retrieval_cache.py:321-353`), sibling to
`test_deleted_cache_db_rebuilds_clean_marker_only_schema` — do not modify that existing test's body,
only add alongside it (its own docstring at lines 322-329 already anticipates this extension):

```python
def test_deleted_cache_db_rebuild_does_not_silently_resurrect_level1_payload_rows(self, tmp_path):
    """Per plan.md DD6: migration_001_add_level1_tables is never called from _get_connection()/
    _init_schema(), so after a raw file delete, reconnecting via _get_connection() brings back
    only the 3 marker-only tables (today's existing behavior) — the Level 1 table stays absent
    until migration_001_add_level1_tables is explicitly re-run. This is the decided, correct
    behavior, not an oversight: cache_migration_plan.md §5 defers any auto-apply-on-connect
    ('migrate') policy to a future ticket.
    """
    conn = rc._get_connection()
    rc.migration_001_add_level1_tables(conn)
    conn.execute(
        "INSERT INTO retrieval_provider_result_cache_rows "
        "(query_hash, normalized_intent, resolved_entity_ids, filters, routing_policy_version, "
        "repo_branch_scope, provider_name, adapter_version, result_payload, source_ids, "
        "source_paths, provider_generation, evidence_fingerprints, created_at, hit_count) "
        "VALUES ('h1','intent','[]','{}', 'rp-v1', 'repo:main', 'prov', 'av1', 'payload', '[]', "
        "'[]', 'gen-1', '[]', ?, 0)",
        (time.time(),),
    )
    conn.commit()
    conn.close()

    rc.CACHE_DB_PATH.unlink()

    conn = rc._get_connection()
    try:
        table_names = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()

    assert "retrieval_provider_result_cache_rows" not in table_names
    assert "retrieval_cache_generation" not in table_names
    for table_name in rc._TABLE_NAME_BY_ALIAS.values():
        assert table_name in table_names
```

**Do NOT touch:** `test_deleted_cache_db_rebuilds_clean_marker_only_schema` itself — its existing
assertions (marker tables empty and present after delete+reconnect, no stray files outside the cache
dir) remain exactly as-is; this step only adds a new sibling method.

**Verify:** `pytest tests/tools/test_retrieval_cache.py::TestCrashRecovery -v`.

### Step 6 — Correct `test_kgmcp_measurement_baseline.py`'s stale banned-path assumption

**Files:** `tests/tools/test_kgmcp_measurement_baseline.py`

**Change:** In `test_no_live_gateway_code_or_search_mcp_edits_introduced`
(`tests/tools/test_kgmcp_measurement_baseline.py:343-357`), remove `"tools/retrieval_cache.py"` from
the 5-path tuple, replacing it with a comment explaining the removal:

```python
def test_no_live_gateway_code_or_search_mcp_edits_introduced():
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    for banned_path in (
        "tools/search_mcp.py",
        "tools/hybrid_retrieval.py",
        # tools/retrieval_cache.py intentionally removed from this list by
        # TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS: this ticket's own approved Scope is to
        # edit that file (adding the Level 1 cache schema/migration). This assertion was correct
        # for TCK-20260814-KGMCP-MEASUREMENT-BASELINE's own scope boundary but does not have
        # ticket-window awareness; the other 4 paths below remain unedited by this ticket and this
        # guard still protects them.
        "tools/context_packet_assembler.py",
        "tools/retrieval_events.py",
    ):
        assert banned_path not in result.stdout, (
            f"{banned_path} must never be edited by this ticket (Out of Scope)"
        )
```

**Other writers to this same test file (enumerated):** no other in-flight ticket in
`tickets/inprogress/` is known to touch `tests/tools/test_kgmcp_measurement_baseline.py`'s
`test_no_live_gateway_code_or_search_mcp_edits_introduced` function — this is the only step in this
plan that edits this file, and it edits only this one function's tuple literal. The file's other
tests (`test_context_tokens_still_reports_unavailable_for_live_telemetry`,
`test_baseline_corpus_module_imports_no_live_gateway_code`, and others) are untouched.

**Do NOT touch:** the other 4 entries in the tuple (`tools/search_mcp.py`,
`tools/hybrid_retrieval.py`, `tools/context_packet_assembler.py`, `tools/retrieval_events.py`) — they
must remain banned; do not weaken the assertion itself (`assert banned_path not in result.stdout`)
or the failure message; do not touch any other test function in this file, in particular
`test_baseline_corpus_module_imports_no_live_gateway_code`
(`tests/tools/test_kgmcp_measurement_baseline.py:360-369`), which has a separately-scoped
`banned` set that already excludes `retrieval_cache` from *its* import-ban list for unrelated reasons
— do not conflate the two or edit that set.

**Verify:** `pytest tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_
search_mcp_edits_introduced -v` passes after this ticket's own `tools/retrieval_cache.py` edits are
in the working tree; `pytest tests/tools/test_kgmcp_measurement_baseline.py -v` (full file) also run
and reported per test_plan.md's Scoped Pytest Commands section.

## Scope Guards

- No `PRAGMA`, `busy_timeout`, `chmod`, or `import os` anywhere in `tools/retrieval_cache.py` (DD2;
  hard-enforced by `tests/docs/test_redaction_retention_policy_doc.py::
  test_sqlite_defaults_not_silently_implemented`).
- No `ALTER TABLE` against `retrieval_index_cache_rows`, `retrieval_query_cache_rows`, or
  `retrieval_packet_cache_rows` — additive-only, new tables only.
- No edit to `_init_schema()`'s existing 3 `CREATE TABLE` statements or its function body beyond
  what Step 3 explicitly leaves untouched (DD6).
- No edit to `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, or
  `tools/knowledge_gateway_mcp.py` — not read, not opened, not imported by any step in this plan.
- No `migrate` or `rebuild` CLI subcommand added to `_build_parser()`/`_COMMAND_DISPATCH`
  (`cache_migration_plan.md` §5 freeze; DD6).
- No `migration_002_add_level2_tables` function, stub, or placeholder added — Level 2/3 tables are
  explicitly out of scope; only `migration_001_add_level1_tables` is implemented.
- No read/write logic (`check_provider_result_cache`/`write_provider_result_cache`-style functions)
  against the new table — schema only.
- No redaction/secret-scanning/size-cap enforcement logic — the `result_payload` column is added,
  but nothing checks, truncates, or stamps a real value into it.
- No class named `ContextPacket` defined or imported in `tools/retrieval_cache.py` (guarded by
  `tests/tools/test_context_packet_assembler.py::TestWorkflowIsolationGuards::
  test_assembler_does_not_import_contextpacket_from_retrieval_cache`).
- No edit to `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` or
  `evidence_cache_identity_contract.md` — both frozen, both left byte-unchanged by this ticket (DD4).
- No new column added into `MAY_LIST_COLUMNS`, and the new table's name is never added to
  `_TABLE_NAME_BY_ALIAS` (DD7).
- No lookup-identity column name reused for a validity-identity concept or vice versa (Non-collapse
  rule) — verified by DD5's mapping table: all 21 new columns are pairwise distinct names, and none
  collides with an existing column name's *meaning* in a different table (`filters` here is the raw
  JSON filter set per contract §1, never named `filters_hash` — that name stays exclusively
  `retrieval_query_cache_rows`'s existing, differently-scoped column).
- No `docs/parity_ledger/` edit as part of this plan's Steps — the new `INFRA-341` entry and
  `INFRA-295`'s line-range re-verification are explicitly deferred to this ticket's own later Parity
  phase, not written now (see "Parity Ledger — Deferred" below).
- No `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md` edits.
- No second SQLite database file created — `CACHE_DB_PATH` (`tools/retrieval_cache.py:53`) is not
  reassigned or duplicated anywhere.

## Dependency Map

- Step 1 (constant) has no dependency; can be implemented first.
- Step 2 (`LEVEL1_CACHE_COLUMNS`) has no dependency on Step 1, but is naturally implemented alongside
  it since both are new module-level constants near the top of the file.
- Step 3 (`migration_001_add_level1_tables`) depends on Steps 1 and 2 — it references
  `retrieval_cache_schema_version` (Step 1) directly, and its `CREATE TABLE` DDL must match
  `LEVEL1_CACHE_COLUMNS` (Step 2) exactly.
- Step 4 (new `TestMigrations` class) depends on Step 3 existing (tests call
  `rc.migration_001_add_level1_tables` directly) and on Step 1/2's constants existing.
- Step 5 (`TestCrashRecovery` extension) depends on Step 3 (calls `rc.migration_001_add_level1_
  tables`).
- Step 6 (measurement-baseline test correction) is independent of Steps 1-5 in mechanism, but should
  be applied last in the implementer's working session — the assertion in that test only starts
  failing once `tools/retrieval_cache.py`'s real diff exists, so fixing the test first would leave it
  silently "passing" for the wrong reason (empty diff) until Steps 1-3 land.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `retrieval_cache_schema_version` is a real, versioned constant, distinct from `RETRIEVAL_VERSION`/`retrieval_event_schema_version`/`redaction_policy_version` | Step 1 | `test_retrieval_cache_schema_version_constant_is_distinct_from_the_other_three_version_axes` (Step 4) |
| AC2 — new table's columns match proposal §10.2's row shape exactly | Steps 2, 3 (DD5 mapping table is the authoritative definition of "exactly") | `test_new_table_column_set_matches_proposal_section_10_2_row_shape` (Step 4) |
| AC3 — migrations apply cleanly and idempotently against fresh DB and existing legacy schema, zero data loss to marker-only tables | Step 3 | `test_migration_applies_cleanly_to_a_fresh_database`, `test_migration_applies_cleanly_on_top_of_existing_legacy_schema_with_zero_data_loss`, `test_migration_is_idempotent_when_run_twice`, `test_migration_does_not_alter_existing_marker_only_table_column_sets` (Step 4) |
| AC4 — `knowledge-index/retrieval_cache.db` remains the single cache database file | Step 3 (no new `CACHE_DB_PATH` value or second connection target introduced) | Manual/Verify-phase check: `grep -n "CACHE_DB_PATH" tools/retrieval_cache.py` shows one assignment (`:53`), unchanged |
| AC5 — `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_mcp.py` remain byte-unchanged | No step touches these files (Scope Guards) | Verify-phase: `git diff --stat HEAD -- tools/knowledge_gateway_router.py tools/knowledge_gateway_packet_assembly.py tools/knowledge_gateway_mcp.py` is empty |

## Docs to Update (for Document-Update phase)

- **`cache_migration_plan.md`'s §10.1/§10.3 citation discrepancy (DD4):** recommend **leaving it
  uncorrected** for this ticket's Document-Update phase. Reasoning: the document is a frozen
  contract owned by a DONE ticket; the citation error is cosmetic (it does not misdescribe *what*
  gets built, only which proposal section number to cite for it), and this plan's own DD4/DD5 already
  establish and use the correct §10.2 citation throughout the real implementation and its docs. If
  Document-Update phase judges the cosmetic fix worth a same-session correction, that is its call to
  make, not a decision this plan pre-empts — but no Step in this plan depends on it being fixed.
- **`evidence_cache_identity_contract.md`:** no update needed. This ticket's schema is fully
  consistent with its §1/§2/§3 field names and Non-collapse rule (DD5); nothing in the contract is
  contradicted or extended by this ticket's real code.
- **New doc surface this ticket's Document-Update phase should add:** a short note (in whichever doc
  `doc-updater` judges the natural home — likely `cache_migration_plan.md`'s cross-references section
  is NOT appropriate since that doc is frozen; more likely a new or existing "Implementation Status"
  note elsewhere, or simply the parity ledger entry's own `v2_evidence` text) recording that
  `migration_001_add_level1_tables` is now real code, not design-only, and citing
  `tools/retrieval_cache.py`'s new line ranges once they're known post-implementation.

## Parity Ledger — Deferred

Not written by this plan or by Implement — flagged here for this ticket's own later Parity phase:

- **New entry `INFRA-341`** (confirmed next-available ID: real max existing ID in
  `docs/parity_ledger/infrastructure.yaml` is `INFRA-340`) describing
  `retrieval_cache_schema_version`, `LEVEL1_CACHE_COLUMNS`, `retrieval_cache_generation`, and
  `migration_001_add_level1_tables()` / `retrieval_provider_result_cache_rows`, with real
  `tools/retrieval_cache.py` line-number evidence once Steps 1-3 land.
- **`INFRA-295`'s existing `v2_evidence` line-range citations** (`docs/parity_ledger/
  infrastructure.yaml:6517` onward) will drift once new constants/functions are inserted above/below
  the cited ranges in `tools/retrieval_cache.py` — must be re-verified against the post-implementation
  file during this ticket's own Parity phase, per the same precedent `INFRA-297` already documents
  following `TCK-20260804-EXPANSION-RATE-WIRING`.

## Anti-Drift Notes

- `migration_001_add_level1_tables` must never be added as a call inside `_get_connection()`,
  `_init_schema()`, or any `check_*_cache()`/`write_*_cache()`/`prune()` function — DD6 is the
  explicit, decided reason (not an oversight) that the Level 1 table does not survive a raw DB-file
  delete without an explicit re-migration.
- Do not add `migration_002_add_level2_tables` in any form (empty stub included) — Risk 3 in
  investigation.md and this plan's Scope Guards both confirm only `migration_001` is this ticket's
  job.
- Do not add a `migrate` or `rebuild` CLI subcommand "for completeness" — explicitly frozen
  design-only by `cache_migration_plan.md` §5; guarded by
  `test_no_migrate_or_rebuild_subcommand_added_to_cli` (Step 4).
- Do not fold the new table's columns into `MAY_LIST_COLUMNS` or the new table's name into
  `_TABLE_NAME_BY_ALIAS`, even though both look like "the obvious place" by surface-level pattern
  matching — both are scoped to the 3 marker-only tables' existing write-path/prune contract, not
  extensible to a schema-only table (DD7).
- The `adapter_version`/`provider_generation` (write-time provenance) columns must never be
  conflated with or silently merged into `adapter_version_at_validation`/
  `provider_generation_at_validation` (check-time validity fields) — DD5 explains why both pairs
  exist as genuinely separate columns; an implementer who "simplifies" this to one column per concept
  would reintroduce the exact collapse the contract's Non-collapse rule (§3) forbids, one level
  removed from where the contract itself draws the line.
- `tests/tools/test_kgmcp_measurement_baseline.py`'s edit (Step 6) is a narrow, justified correction
  of a stale test assumption — not a precedent for weakening any *other* currently-failing or
  currently-passing gate. Do not use this ticket's resolution of that one conflict as license to edit
  any other test's assertions without the same direct read-and-justify process DD3 documents.
