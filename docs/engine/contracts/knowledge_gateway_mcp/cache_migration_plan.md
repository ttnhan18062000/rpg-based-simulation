---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, schema, mcp]
---

# Knowledge Gateway MCP — Cache Migration Plan (Design Only)

This document is a **migration design specification**, not an implementation. No migration
function body is written, and no `CREATE TABLE`/`ALTER TABLE` statement is executed against the
real, gitignored `knowledge-index/retrieval_cache.db` by this ticket
(`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`). `tools/retrieval_cache.py` itself is not edited —
verify with `git diff tools/retrieval_cache.py` (must be empty). Function names below are named
placeholders; their bodies are explicitly Phase 2/3 work, out of this ticket's scope. This document
specifies, per §10.1/§19 of `docs/plans/knowledge-gateway-mcp-proposal.md`, how those future
migrations must evolve `knowledge-index/retrieval_cache.db` **in place** — the same file, not a
second database — while preserving the three existing marker-only tables
(`retrieval_index_cache_rows`, `retrieval_query_cache_rows`, `retrieval_packet_cache_rows`,
`tools/retrieval_cache.py:111-150`) and their current callers/tests unchanged until a later ticket
migrates them.

---

## 1. Schema-version constant: `retrieval_cache_schema_version`

The new DDL/table-shape version constant for this module's future migrations is named
**`retrieval_cache_schema_version`** — a scoped name, deliberately not the bare, ambiguous string
`schema_version`. This repo already has two other, genuinely different "version" concepts living in
this exact vocabulary:

- `tools/retrieval_cache.py:45`'s `RETRIEVAL_VERSION: int = 1` — a **cache-key** versioning
  constant, "manually bumped on breaking changes to this module's own key-derivation or
  invalidation logic" (per its own comment).
- `tools/retrieval_events.py:46`'s `retrieval_event_schema_version: int = 1` — an **event-field-
  shape** versioning constant, explicitly commented (`tools/retrieval_events.py:43-45`) as "distinct
  from `tools/retrieval_cache.py::RETRIEVAL_VERSION`... This constant versions the retrieval-event
  *field shape itself* — a different concept."

`retrieval_cache_schema_version` is a genuine third concept: it versions the **DDL/table shape** of
`retrieval_cache.db` itself, independent of both the cache-key derivation logic
(`RETRIEVAL_VERSION`) and the event-emission field shape (`retrieval_event_schema_version`). Naming
it with the same bare `schema_version` string that either of those two already-scoped names was
written to avoid would reintroduce exactly the ambiguity `retrieval_events.py`'s own comment exists
to prevent. `retrieval_cache_schema_version` must never be confused with, aliased to, or
substituted for `RETRIEVAL_VERSION` or `retrieval_event_schema_version` — all three remain separate
constants, each versioning a different axis of change.

**Storage location design:** following the naming/storage-shape precedent already used by
`tools/parity_index.py`'s `ledger_generation` table (`tools/parity_index.py:156-166`, whose first
column is literally `schema_version INTEGER`, populated once per build at `:468-490`), a new,
single-row metadata table stores `retrieval_cache_schema_version` inside `retrieval_cache.db`
itself:

```sql
CREATE TABLE IF NOT EXISTS retrieval_cache_generation (
    retrieval_cache_schema_version INTEGER NOT NULL,
    migrated_at REAL NOT NULL
)
```

Note the deliberate divergence from `parity_index.py`'s pattern: `parity_index.py`'s
`ledger_generation` table is written once per full-rebuild `build()` call
(`tools/parity_index.py:504`, `:530`, an atomic-replace-the-whole-file build). This module's
`retrieval_cache_generation` table is instead updated **in place**, once per successfully-applied
migration, because `retrieval_cache.db` preserves existing rows across upgrades rather than being
rebuilt from an authoritative source-of-truth shard set the way `parity.db` is. `parity_index.py` is
cited here only for its naming/metadata-table-shape precedent, never as a full-rebuild precedent
for this module — see §3.

---

## 2. Ordered migration functions (design only — bodies deferred to Phase 2/3)

Migrations are hand-written SQL functions, following the `SCHEMA_VERSION`-integer-constant +
ordered-function-list pattern already established by `tools/parity_index.py`
(`SCHEMA_VERSION = 1`, `tools/parity_index.py:66`). No migration library
(`alembic`/`yoyo-migrations`/`sqlite-migrate`, or similar) is introduced — none exists anywhere in
this repo's `requirements.txt`, `requirements-knowledge.txt`, or `pyproject.toml` dependency sets
today, and adding one for this single module would repeat the exact new-single-purpose-dependency
anti-pattern the sibling ticket's investigation flagged for `jsonschema`.

Ordered migration function list (names are placeholders; bodies are Phase 2/3 work):

1. `migration_001_add_level1_tables(conn: sqlite3.Connection) -> None` — adds the Level 1 (direct
   evidence payload/dependency) tables per §10.1 of the proposal. Wholly new tables alongside the
   untouched marker-only ones, so `CREATE TABLE IF NOT EXISTS` — the same idempotent pattern
   `_init_schema()` already uses (`tools/retrieval_cache.py:108-152`) — is sufficient and safe; no
   `ALTER TABLE ADD COLUMN` against an existing populated table is required for this migration,
   confirmed by this ticket's own investigation (Risk 1) that Scope adds only new tables.
2. `migration_002_add_level2_tables(conn: sqlite3.Connection) -> None` — adds the Level 2
   (dependency-tracking) tables per §10.3. Same `CREATE TABLE IF NOT EXISTS` idempotency guarantee
   as migration 001; no column addition to an existing table. Like migration 3 below, this
   migration's body is now real, implemented code — added by
   `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS`, creating the new
   `retrieval_context_packet_cache_rows` table (28 columns, `LEVEL2_CACHE_COLUMNS`, per proposal
   §10.2/§10.3); `tools/retrieval_cache.py:310-364`. **Read/write logic against this table is now
   real, implemented code too** — added by `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`
   (`check_context_packet_cache()`/`write_context_packet_cache()`/
   `record_context_packet_cache_hit()`/`context_packet_cache_stats()`, `tools/retrieval_cache.py`),
   orchestrated by `perform_context_packet_cache_lookup()`/`perform_context_packet_cache_write()`
   (`tools/knowledge_gateway_cache.py`) and wired into the live `_run_knowledge_context()` call path,
   checked before Level 1 — superseding this sentence's earlier "no read/write logic... yet"
   framing.
3. `migration_003_add_redaction_policy_version_column(conn: sqlite3.Connection) -> None` — adds a
   `redaction_policy_version` column to the existing `retrieval_provider_result_cache_rows` table, so
   a cache row can carry an on-disk record of which version of
   `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §6's redaction/
   allowlist/secret-scan/size-cap rules wrote it. Unlike migrations 1 and 2 above, this is an `ALTER
   TABLE ... ADD COLUMN` against a table that may already hold rows, not a `CREATE TABLE IF NOT
   EXISTS` against a wholly new table — idempotency is instead guaranteed by an explicit `PRAGMA
   table_info(retrieval_provider_result_cache_rows)` existence check before altering (SQLite has no
   `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`). Ordinal 3, immediately after migration 2 above, per
   this document's own reservation that ordinal 2 belongs to the Level 2/Phase 3 tables and must
   never be reused or stubbed by a later migration. Migration 3's body is real, implemented code —
   added by `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`, Architecture-Review-approved (DD3,
   option b); `tools/retrieval_cache.py:265-283`. (Migrations 1 and 2 above are likewise real,
   implemented code as of `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` — see migration
   2's own annotation above; no migration in this ordered list remains a design-only placeholder.)
4. `migration_004_add_level2_write_path_columns(conn: sqlite3.Connection) -> None` — adds
   `redaction_policy_version INTEGER`, `budget_truncated INTEGER`, `omitted_statement_count
   INTEGER`, `provider_failures TEXT` to the existing `retrieval_context_packet_cache_rows` table
   (closing the same `redaction_policy_version`-persistence gap migration 3 closed for Level 1, plus
   3 further write-fidelity columns needed for a Level 2 hit to faithfully reconstruct a response).
   Same `ALTER TABLE ... ADD COLUMN` idempotency pattern as migration 3 — a `PRAGMA table_info`
   existence check per column, guarded, never touching migrations 1–3 or `LEVEL1_CACHE_COLUMNS`.
   Ordinal 4, the next open ordinal after migration 3. Migration 4's body is real, implemented
   code — added by `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`;
   `tools/retrieval_cache.py`. No migration in this ordered list remains a design-only placeholder.

Each migration function:
- Is idempotent and individually re-runnable (safe to call again on a database that already has the
  migration applied — `CREATE TABLE IF NOT EXISTS` naturally satisfies this for both migrations
  above).
- Runs inside the same connection/transaction pattern `_init_schema()` already uses
  (`conn.execute(...)` calls followed by a single `conn.commit()`).
- On successful application, updates `retrieval_cache_generation` with the new
  `retrieval_cache_schema_version` value and the current timestamp.

A future `migrate` entry point applies every migration whose ordinal exceeds the database's current
stored `retrieval_cache_schema_version`, in ascending order, in a single connection — mirroring how
`_get_connection()` already unconditionally calls `_init_schema()` on every connect
(`tools/retrieval_cache.py:96-105`), so a `migrate` step would run the same way: unconditionally
attempted, cheap to no-op when already applied.

**No `ALTER TABLE ADD COLUMN` is required by this ticket's own scope.** Both migrations above add
wholly new tables; neither modifies the three existing marker-only tables' columns. If a future
ticket needs to widen an existing populated table's shape, that migration must be designed
separately at that time — SQLite's `ALTER TABLE ADD COLUMN` is the only forward-compatible primitive
for that case without a full-table rebuild, and no such requirement exists in this ticket's Scope.

---

## 3. Why this is not a full-rebuild-and-atomic-swap

`tools/parity_index.py`'s `build()`/`_atomic_replace_db()` (`tools/parity_index.py:504`, `:530`)
construct an entirely fresh database from `docs/parity_ledger/*.yaml` shards and atomically swap it
into place — the right approach for `parity.db`, which is fully derived from an authoritative
source-of-truth outside itself. `retrieval_cache.db` has no equivalent external source of truth: its
existing marker-only rows (`retrieval_index_cache_rows` / `retrieval_query_cache_rows` /
`retrieval_packet_cache_rows`) are live cache state, not derived from a shard set that could
regenerate them. §10.1/AC5 explicitly require preserving those rows and their current callers/tests
in place, not regenerating the file from scratch. The migration functions in §2 are therefore
additive, in-place `CREATE TABLE IF NOT EXISTS` operations against the existing file — never a
drop-and-rebuild.

---

## 4. Same file, not a second database

Per §10.1/Scope ("evolve... rather than creating a second database... Do not create a second
gateway database unless Phase 0 demonstrates an incompatible lifecycle or locking requirement"),
this design keeps the new Level 1/2 tables in the same `knowledge-index/retrieval_cache.db` file as
the existing marker-only tables. This ticket's investigation found no evidence of an incompatible
requirement — no WAL-mode conflict, no differing writer-process model between the marker-only tables
and the planned new tables — so no justification exists to deviate from the same-file default.

---

## 5. Rebuild-from-scratch fallback path (documented, not implemented)

`tools/retrieval_cache.py`'s current CLI dispatch table (`_COMMAND_DISPATCH`,
`tools/retrieval_cache.py:515-521`) has five subcommands today: `stats`, `check-index`,
`check-query`, `check-packet`, `prune`. No `migrate` or `rebuild` subcommand exists. This ticket adds
neither — both remain design-only, documented here:

- **`migrate`** (future): applies every pending ordered migration from §2 against the existing file
  in place, per the ascending-ordinal rule above.
- **`rebuild`** (future): a documented, not-implemented fallback for the case where the on-disk
  `retrieval_cache_schema_version` is unrecognized or the file is otherwise judged corrupt/
  unmigratable. `rebuild` drops and recreates `retrieval_cache.db` from scratch (fresh
  `_init_schema()` plus every migration applied from ordinal 1), analogous in spirit to
  `parity_index.py`'s full-rebuild approach (§3) but scoped only to this module's own eventual
  `rebuild` command — a deliberate, explicit, operator-invoked action, never an automatic fallback a
  `check_*_cache()`/`write_*_cache()` call would trigger silently. `rebuild` necessarily loses all
  existing cache rows (by design — this is the last-resort path, not the normal migration path in
  §2), which is acceptable because every row this module stores is a cache entry, recomputable from
  the corpus, never a source of truth.

Neither `migrate` nor `rebuild` is added to `_build_parser()`/`_COMMAND_DISPATCH` by this ticket.

---

## 6. Compatibility with the not-yet-started redaction/retention policy ticket

This document hard-codes no redaction/retention/GC number — no TTL, no max-DB-size limit, no
WAL/busy-timeout default. Those belong to the sibling, not-yet-started
`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY` ticket. The migration design above is compatible
with that ticket's eventual scope by construction: new tables added via §2's migrations are subject
to the same `prune()`-style manual eviction backstop
(`tools/retrieval_cache.py:406-428`) precedent the existing marker-only tables already use, and
nothing in this design assumes a retention policy that has not yet been written.

---

## 7. Cross-references

- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` — the
  lookup-identity/evidence-validity-identity split and repository/branch/working-tree cache scope
  these future tables must respect.
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json` — the 8 evidence
  identity kinds the Level 1/2 tables' rows will reference.
- `tools/retrieval_cache.py` — the existing module this plan evolves; read-only citation throughout,
  zero edits by this ticket.
- `tools/parity_index.py` — cited for its `schema_version`-naming and metadata-table-shape
  precedent only (§1), never as a full-rebuild precedent for this module (§3).
