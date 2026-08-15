---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY
artifact_type: investigation
tags: [ai, schema, process-improvement]
---

# Investigation — TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY

## Current Behavior

**`tools/retrieval_cache.py`** (the existing gitignored `knowledge-index/retrieval_cache.db` this
ticket's migration plan must evolve, not replace):

- Module docstring (`:1-28`) explicitly states "What this is: three independently-invalidatable
  SQLite tables ... each with a narrow MAY-list-only write path ... and a `check(...)` function
  returning hit / miss / stale-rejected plus a reason code." **Confirmed marker-only**: reading the
  actual `_init_schema()` (`:108-152`), all three tables — `retrieval_index_cache_rows`
  (`:111-122`), `retrieval_query_cache_rows` (`:125-138`), `retrieval_packet_cache_rows`
  (`:141-150`) — store only hashes/IDs/version numbers/status/reason codes/scores/latency/
  `created_at`, never a payload, answer, excerpt, or raw text field. `MAY_LIST_COLUMNS`
  (`:70-89`) is the closed allowlist; `_validate_may_list_kwargs()` (`:155-168`) is the single
  shared enforcement point raising `ValueError` on any write attempting a column outside that set.
  This directly confirms the ticket's own characterization of the existing tables.
- No `schema_version` field, table, or column exists anywhere in this file — confirmed by reading
  the complete `_init_schema()` body. `_get_connection()` (`:96-105`) always calls `_init_schema()`
  with three `CREATE TABLE IF NOT EXISTS` statements; there is no migration function, no schema
  metadata table, no version check of any kind. `_get_connection()`'s own docstring (`:97-101`)
  states it "Never deletes/unlinks any existing file" and only removes rows via explicit per-row
  eviction (`write_index_cache`'s stale-row `DELETE`, `:231-235`) or the manual `prune`
  subcommand (`:406-428`) — never a whole-file rewrite. This means today's module has **no
  precedent whatsoever for adding a new column/table to an existing on-disk file** other than
  `CREATE TABLE IF NOT EXISTS`, which is safe for wholly new tables but does not by itself version
  or migrate existing table shapes.
- `RETRIEVAL_VERSION: int = 1` (`:45`) is a *cache-key* versioning constant ("Manually bumped on
  breaking changes to this module's own key-derivation or invalidation logic"), not a schema/DDL
  version — confirmed distinct by `tools/retrieval_events.py:43-46`'s own comment: "Distinct from
  `tools/retrieval_cache.py::RETRIEVAL_VERSION` (the cache *key*-versioning constant...) This
  constant versions the retrieval-event *field shape itself* — a different concept." This ticket's
  new `schema_version` (DDL/table-shape versioning) is a third, still-different concept from both.
- `_corpus_generation()` (`:183-191`) is a read-only proxy over `knowledge-index/manifest.json`'s
  `built_at` field, with an explicit `_NO_MANIFEST` sentinel (`:51`) rather than a fabricated
  timestamp — the sentinel-over-fabrication pattern this ticket's own evidence-kind normalization
  rules (renamed/deleted/duplicate-name cases) should follow.
- CLI surface (`:435-527`): `stats`, `check-index`, `check-query`, `check-packet`, `prune` —
  no `migrate` or `rebuild` subcommand exists today. §19's required "rebuild command" is net-new.

**`tests/tools/test_retrieval_cache.py`** (351 lines total — confirmed via full read):
- Isolates the DB per-test via an autouse fixture (`_isolated_cache_db`, `:33-37`) that
  `monkeypatch.setattr`s `rc.CACHE_DB_PATH`/`rc._MANIFEST_PATH` to `tmp_path` — no shared/real
  gitignored DB file is ever touched by tests. This is the pattern this ticket's own test file must
  mirror per AC6.
- `TestMayListEnforcement` (`:161-209`) and `TestStaticGuards` (`:216-244`) are the two test
  classes most directly relevant to this ticket's identity-contract tests: the former proves no
  raw text leaks into a stored row (a "lookup identity may not smuggle validity payload"-adjacent
  guard), the latter proves import-isolation and naming-collision boundaries via `ast.parse`.
- The module docstring's "Duration-is-not-behavior guard" (`:7-12`) is a hard test-writing
  constraint precedent: no test may assert eviction purely from elapsed time outside the three
  `test_prune_*` tests. This ticket's own `PROVIDER_GENERATION`-fallback-only fixture test (AC3)
  must use a hash/version-mismatch-shaped construction, not a time-based one.

**Migration-tooling precedent — `tools/parity_index.py`** (the repo's only existing
SQLite-schema-versioning precedent, per the ticket's own Assumptions section):
- `SCHEMA_VERSION = 1` (`:66`), `IMPORTER_VERSION = "1.0.0"` (`:67`) — bare module-level int/str
  constants, not a library-managed version.
- `_create_schema()` (`:153-`) creates a `ledger_generation` table whose first column is literally
  `schema_version INTEGER` (`:157`), written once per build (`:468-490` inserts
  `SCHEMA_VERSION`/`IMPORTER_VERSION`/`built_at`/`source_manifest_hash` into that row).
  `_EXPECTED_COLUMNS["ledger_generation"]` (`:109-112`) enumerates that row's full column set —
  the closed-allowlist-of-expected-columns pattern this ticket's own schema-version design should
  mirror.
- **This is a full-rebuild pattern, not an in-place ALTER-TABLE migration**: `build()` (`:530`)
  and `_atomic_replace_db()` (`:504`) construct the entire DB fresh and atomically swap it in —
  there is no "add a column to an existing populated table" code path anywhere in this file.
  `health()` (`:661`) reads back `schema_version, built_at, shard_count, entry_count,
  fts5_available` (`:696-701`) as the "detect unsupported/corrupt schema" check §19 requires.
  **Consequence for this ticket**: `parity_index.py` is the right precedent for *how to name and
  store* `schema_version` (a bare integer, in a small metadata/generation table, read back by a
  health check), but it is *not* a precedent for in-place additive migration of a
  file that must preserve existing rows across upgrades — `retrieval_cache.db` cannot do a
  drop-and-rebuild the way `parity.db` does, because §10.1/AC5/Scope explicitly require preserving
  the existing marker-only tables' rows and callers in place, not regenerating the file from an
  authoritative source shard set the way `parity.db` regenerates from `docs/parity_ledger/*.yaml`.
  This is a **materially different migration shape** the plan phase must not gloss over by citing
  `parity_index.py` as if it solves the same problem.
- `_probe_fts5()` (`:144-150`) is the closest existing "capability probe before schema build"
  precedent, relevant if the new Level 1/2 tables want an optional FTS index later — out of this
  ticket's scope (Phase 0 is contract-only) but worth flagging for the plan phase.

**No Python migration library dependency exists in this repo.** Confirmed by direct grep of
`requirements.txt`, `requirements-knowledge.txt`, and `pyproject.toml` (`[project.dependencies]`,
`[project.optional-dependencies]` — `dev`, `knowledge`, `search-mcp`): no `alembic`,
`yoyo-migrations`, `sqlite-migrate`, or similar package appears anywhere. A repo-wide grep for
`alembic|yoyo[-_]?migrations` across `.py`/`.txt`/`.toml`/`.cfg` files returned zero matches. This
answers the ticket's own Assumptions/Open Questions item directly: **hand-written SQL migrations,
following the `SCHEMA_VERSION`-integer-constant + ordered-function-list pattern already used by
`tools/parity_index.py`, is the only option consistent with existing repo conventions** — adding a
migration library would be a new, unprecedented dependency for a single ticket, the same
anti-pattern the sibling ticket's investigation flagged for `jsonschema`
(`stored_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/investigation.md`, Anti-Drift Hazards).

**`docs/parity_ledger/schema.json`** — confirmed to have **no `schema_version` field** (grep
returns zero matches inside the file), reconfirming the sibling ticket's own investigation finding
under `TCK-20260814-KGMCP-CONTRACT-SCHEMAS`. The real in-repo precedent for an explicit additive
integer version field is **`tools/retrieval_events.py:46`**:
`retrieval_event_schema_version: int = 1`, with a scoped (not bare) name explicitly chosen to
avoid colliding with `retrieval_cache.RETRIEVAL_VERSION` (see comment at `:43-45`) — documented in
prose at `docs/agent-monitoring/schema.md:276-277`. This ticket's new `schema_version` for
`retrieval_cache.db`'s DDL should likewise use a scoped name
(e.g. `retrieval_cache_schema_version`) to avoid the same three-way collision risk
(`RETRIEVAL_VERSION` / `retrieval_event_schema_version` / a new schema-DDL version) that already
exists in this codebase's vocabulary.

**Frozen Phase 0 contracts this ticket must reference, not redefine** —
`docs/engine/contracts/knowledge_gateway_mcp/shared_enums.schema.json` (just frozen by
`TCK-20260814-KGMCP-CONTRACT-SCHEMAS`, now in `tickets/done/`): defines `freshness`
(`FRESH`/`NEEDS_REVALIDATION`/`STALE`/`UNKNOWN`) and `verification`
(`VERIFIED`/`SUPPORTED`/`INFERRED`/`UNVERIFIED`) as closed enums, plus `status` and
`statement_classification`, each with its own `schema_version: 1` field (`:5`) — this file is
itself an example of the exact "bare `schema_version` field in a frozen `.schema.json`" pattern
this ticket's own new evidence-identity-kinds schema file should follow structurally.
`docs/engine/contracts/knowledge_gateway_mcp_contract.md` explicitly states (`:17-19`): "Evidence
identity, cache-lookup identity, and redaction/retention policy are covered by sibling tickets
(`KGMCP-EVIDENCE-CACHE-IDENTITY`, `KGMCP-REDACTION-RETENTION-POLICY`), not this document" —
confirming this ticket owns the identity-contract content and should cross-reference, not
duplicate, the frozen enums.

## Mechanics / Engine Constraints

This ticket is agent-orchestration/retrieval tooling, not simulation logic — no `docs/mechanics/`
chapter or `docs/engine/` runtime contract (kernel, pipeline, combat, economy) constrains what this
ticket may do, matching the same posture the sibling `KGMCP-CONTRACT-SCHEMAS` investigation
established for this doc family (`context_packet_contract.md` §4's `support_boundary` precedent).
The only "engine constraint" in the CLAUDE.md sense is the Durable State Rule: the migration design
must not leave a durable table with no lifecycle/inspection path (the exact finding that already
forced `prune()` to be added to `retrieval_cache.py` in its own architecture-review pass — see
`docs/parity_ledger/infrastructure.yaml` INFRA-295's `text` field, which records this history
directly).

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`: new prose
  contract (parallel to `knowledge_gateway_mcp_contract.md`) documenting the lookup-identity vs.
  evidence-validity-identity split (§11.1/§11.2), the 8 evidence identity kinds with normalization
  rules (§12.1), and repository/branch/working-tree cache scope (§12.3) — this is this ticket's
  primary deliverable and no such document exists yet.
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json`: new frozen
  schema (structural sibling to `shared_enums.schema.json`) enumerating the 8 closed evidence kinds
  (`DOCUMENT`, `DOCUMENT_SECTION`, `FILE`, `SYMBOL`, `TICKET`, `PARITY_ENTRY`, `REGISTRY_ENTRY`,
  `PROVIDER_GENERATION`) with stable-identity form and preferred fingerprint per §12.1's table —
  no such file exists yet.
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`: new migration design
  document per §10.1/§19/AC5 — `schema_version` field name/location, ordered migration function
  list, preserved-marker-table plan, and rebuild-from-scratch command — no such document exists
  yet, and this is an explicit, named acceptance criterion.
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md`: its §5 "Cross-references" list
  (`:161-174`) should gain entries for the three new files above once frozen, the same way it
  already cross-references `shared_enums.schema.json` and the request/response schemas — keeps the
  Phase 0 contract family internally navigable.
- `docs/plans/knowledge-gateway-mcp-proposal.md`: §20's Phase 0 checklist bullets covering
  "define evidence dependency granularity," "define lookup vs. validity identity," and "write the
  migration plan" should get a cross-reference to the new contract docs once this ticket lands,
  mirroring the optional follow-up the sibling ticket's investigation recommended for its own §20
  bullets — not a hard requirement of this ticket, but the same class of housekeeping update.

## Parity Ledger Overlap

- `INFRA-295` (`docs/parity_ledger/infrastructure.yaml`, status: `verified`, priority: `P2`,
  `test_path: tests/tools/test_retrieval_cache.py`) — the entry covering
  `tools/retrieval_cache.py`'s current 3-table marker-only design. **This ticket does not change
  its status**: Scope/Out of Scope explicitly excludes implementing the cache reads/writes
  themselves, so `retrieval_cache.py`'s actual code and this entry's `v2_evidence` remain accurate
  as written. Flag for the future Phase 2/3 implementation ticket: once the migration plan produced
  here is executed (schema_version table + Level 1/2 tables added), INFRA-295's `text`/`v2_evidence`
  will need a follow-up update to describe the expanded schema — do not update it in this ticket,
  since no code changes.
- No other `docs/parity_ledger/*.yaml` entry references `knowledge_gateway`, `evidence identity`,
  or `cache lookup identity` by text search across all shards.
- Per the sibling `KGMCP-CONTRACT-SCHEMAS` investigation and `context_packet_contract.md` §4's
  precedent, this ticket's own new contract docs (being agent-orchestration/retrieval tooling, not
  simulation behavior) do not themselves require a new `docs/parity_ledger/` entry.

## Prior Work

- `stored_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/` (`investigation.md`, `plan.md`,
  `test_plan.md`) — the immediately preceding sibling ticket in this epic. Its investigation
  independently confirmed (a) `docs/parity_ledger/schema.json` has no `schema_version` field, (b)
  `tools/retrieval_events.py:46`'s `retrieval_event_schema_version: int = 1` is the real
  additive-versioning precedent, (c) no `jsonschema` library dependency exists and none should be
  added, (d) the hand-rolled-Python-validation + JSON-structural-parsing test pattern
  (`tools/parity_ledger_writer.py::validate_entry`, `tests/tools/test_parity_ledger_schema.py`) is
  the pattern to mirror for any new frozen `.schema.json` file. All four findings independently
  re-confirmed by this investigation's own source reads — no discrepancy found.
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` and its four sibling `.schema.json`
  files (frozen by the ticket above) — this ticket's identity contracts must reference
  `shared_enums.schema.json`'s `freshness`/`verification` enums, not redefine them (per this
  ticket's own Related Tickets note and the contract doc's `:17-19` explicit statement).
- `TCK-20260729-RETRIEVAL-CACHE-LEVELS` (`stored_artifacts/TCK-20260729-RETRIEVAL-CACHE-LEVELS/`)
  — built the current `tools/retrieval_cache.py` this ticket must evolve. Its own investigation
  established the MAY-list/marker-only design and the `prune()` Durable-State-Rule addition after
  an architecture-review `NEEDS_CHANGES` finding (also recorded in INFRA-295's `text` field) —
  relevant precedent that a lifecycle/inspection path is a hard requirement for any new durable
  table this ticket's migration plan adds, not an optional nicety.
- `docs/observability/retrieval_retention_redaction_policy.md` (Decision C) — the category-name
  and MAY-list-field precedent `retrieval_cache.py` itself implements; the sibling
  `KGMCP-REDACTION-RETENTION-POLICY` ticket (still in `tickets/todos/`) owns GC defaults/limits
  that this ticket's migration plan must stay compatible with, per this ticket's own Out of Scope
  note — no conflict found during this investigation, but not yet reconciled since that ticket
  has not started (see Risks).

## Risks and Open Questions

1. **`parity_index.py` is a full-rebuild precedent, not an in-place-migration precedent** (see
   Current Behavior). The plan phase must design genuine ordered ALTER/CREATE-based migrations
   (idempotent `CREATE TABLE IF NOT EXISTS` for wholly new tables is safe and already the existing
   pattern; anything requiring a column added to an *existing populated* table needs an explicit
   migration step, since SQLite's `ALTER TABLE ADD COLUMN` is the only forward-compatible primitive
   without a full table rebuild). This ticket's own Scope only requires *adding* new tables
   (Level 1/2 payload + dependency tables) alongside the untouched marker-only tables, so a
   column-migration step may not actually be needed yet — confirm this reading against the plan
   phase's exact table list before assuming any `ALTER TABLE` is required at all.
2. **`schema_version` naming collision risk is real, not hypothetical** — this codebase already
   has `retrieval_cache.RETRIEVAL_VERSION` (cache-key versioning) and
   `retrieval_events.retrieval_event_schema_version` (event-field-shape versioning). A third,
   undistinguished `schema_version` name in the same cache module risks exactly the confusion
   `retrieval_events.py`'s own comment (`:43-45`) was written to prevent. Recommend a scoped name
   (e.g. `retrieval_cache_schema_version` or `CACHE_SCHEMA_VERSION`) — flagged here as a naming
   decision the plan phase should make explicitly, not an open blocker.
3. **Redaction/retention policy ticket has not started** (`TCK-20260814-KGMCP-REDACTION-RETENTION-
   POLICY` is still in `tickets/todos/knowledge-gateway-mcp/`, per `SEQUENCE.md` item 4, gated to
   run parallel-with/after this ticket). This ticket's migration plan must be "compatible with"
   that policy once both land (per this ticket's own Out of Scope note), but GC defaults, TTLs, and
   max-DB-size limits are that ticket's content, not this one's — do not invent them here. Not a
   blocker for this ticket's own acceptance criteria, but the plan phase should avoid hard-coding
   any GC/eviction number that ticket is meant to own.
4. **Whether new Level 1/2 tables belong in the *same* `retrieval_cache.db` file as the existing
   marker-only tables, versus a new file, is already answered by §10.1/Scope ("evolve... rather
   than creating a second database... Do not create a second gateway database unless Phase 0
   demonstrates an incompatible lifecycle or locking requirement") — this investigation found no
   evidence of such an incompatible requirement (no WAL-mode conflict, no differing writer-process
   model observed), so the migration design should default to same-file evolution and only deviate
   with an explicit, evidenced justification.
5. Ticket AC3 requires "a fixture test demonstrates a `SYMBOL`/`FILE`-backed result is not
   invalidated by an unrelated corpus-wide generation bump" — since Phase 0 is contract-only (no
   live cache-check code exists for evidence-kind-scoped invalidation yet), this fixture test must
   be written against the *documented* normalization/invalidation rules (e.g. a table-driven test
   over the contract doc's own worked examples) rather than against real `check_*_cache()` code,
   mirroring how the sibling ticket's `test_knowledge_gateway_contract_schemas.py` tests hand-parsed
   JSON structure rather than live routing code. Confirm this reading with the planner before
   writing tests that import functions that do not exist yet.

## Anti-Drift Hazards

- **Do not implement any live cache read/write code for the new identity contracts.** Out of Scope
  is explicit ("Implementing the cache reads/writes themselves — Phase 0 is contract-only"). A
  migration *design* document and frozen evidence-kind schema must not grow into actual
  `ALTER TABLE`/`CREATE TABLE` execution against the real `knowledge-index/retrieval_cache.db`.
- **Do not touch `tools/retrieval_cache.py`'s existing three tables, `MAY_LIST_COLUMNS`, or
  `_init_schema()`.** AC5 requires "preserving existing marker-only table callers/tests until
  migrated" — any edit to the current schema or its callers in this ticket is a scope violation.
- **Do not collapse lookup identity and validity identity into one key or one table.** This is the
  ticket's central architectural rule (§11.1) and its first Acceptance Criterion — the most likely
  accidental violation is designing a single migration table that stores both a lookup hash and a
  freshness/validity field on the same row keyed by the same primary key without a documented
  separation of *which* code path is permitted to treat a hit on that key as proof of validity.
- **Do not invent a migration-library dependency.** No `alembic`/`yoyo-migrations`/similar exists in
  this repo (confirmed above); adding one for this ticket alone repeats the exact anti-pattern the
  sibling ticket's investigation flagged for `jsonschema`.
- **Do not redefine `freshness`/`verification` enum values.** `shared_enums.schema.json` is frozen;
  this ticket's evidence-validity-identity contract must reference those enum names, not restate
  them with different values or add a competing enum with overlapping semantics.
- **Do not treat `PROVIDER_GENERATION` as a primary dependency for kinds that have a finer-grained
  fingerprint available.** AC3 is explicit that it is fallback-only — a design that defaults every
  evidence kind to `PROVIDER_GENERATION` for simplicity would silently violate §12.1's core
  requirement and the acceptance criterion built to test it.
- **Do not hard-code redaction/retention GC numbers** (TTLs, max DB size, WAL/busy-timeout
  defaults) — those belong to the sibling `KGMCP-REDACTION-RETENTION-POLICY` ticket, per this
  ticket's own Out of Scope line.
