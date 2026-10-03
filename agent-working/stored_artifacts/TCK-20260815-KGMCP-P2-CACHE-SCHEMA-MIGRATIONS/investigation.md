---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS

## Current Behavior

### `tools/retrieval_cache.py` (the module this ticket extends)
A standalone, dependency-free SQLite module owning `knowledge-index/retrieval_cache.db`
(`CACHE_DB_PATH`, line 53), deliberately isolated from `knowledge-index/knowledge.db` because
`knowledge_search.py`'s rebuild functions unconditionally `unlink()` that file.

- `RETRIEVAL_VERSION: int = 1` (line 45) — cache-key-derivation-logic version. **Not** the constant
  this ticket implements.
- `MAY_LIST_COLUMNS` (lines 70-89) — the exact frozenset of column names any `write_*_cache()` call
  may ever pass. `_validate_may_list_kwargs()` (lines 155-168) raises `ValueError` on anything
  outside it, and rejects `created_at` as a caller-supplied kwarg (stamped internally).
- `_get_connection()` (lines 96-105) opens the DB (creating the parent dir), unconditionally calls
  `_init_schema(conn)` on every connect, and never deletes/unlinks the file.
- `_init_schema()` (lines 108-152) issues three `CREATE TABLE IF NOT EXISTS` statements — the three
  marker-only tables below — followed by one `conn.commit()`. This is the exact idempotent pattern
  `cache_migration_plan.md` §2 says the new `migration_00N_*` functions must reuse.
- Three tables, confirmed identical between source (`_init_schema()`) and the real, on-disk
  `knowledge-index/retrieval_cache.db` (inspected directly via `sqlite_master`, 2026-08-15):
  - `retrieval_index_cache_rows(content_hash, embedding_version, chunking_version, source_id,
    cache_status, reason_code, created_at)`, PK `(content_hash, embedding_version,
    chunking_version)`.
  - `retrieval_query_cache_rows(query_hash, filters_hash, corpus_generation, retrieval_version,
    cache_status, reason_code, score, latency_ms, created_at)`, PK `(query_hash, filters_hash,
    corpus_generation, retrieval_version)`.
  - `retrieval_packet_cache_rows(packet_key_hash [PK], cited_hashes_json, corpus_generation,
    policy_version, cache_status, reason_code, created_at)`.
  This is the precise "preserve unmodified" baseline this ticket must diff against after the
  migration runs.
- `_TABLE_NAME_BY_ALIAS`, `prune()`, and the 5-subcommand CLI (`stats`, `check-index`, `check-query`,
  `check-packet`, `prune`; `_COMMAND_DISPATCH`, lines 515-521) are the only other module-level
  surface. No `migrate`/`rebuild` subcommand exists today — confirmed against `_build_parser()`.

### `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` (the frozen design)
Design-only; `git diff tools/retrieval_cache.py` was empty as of that ticket, and remains the
pre-migration baseline today (module content read above matches the plan's line citations
verbatim).

- §1 names the new constant **`retrieval_cache_schema_version`** (not `schema_version`, not
  `RETRIEVAL_VERSION`, not `retrieval_event_schema_version`) and specifies its storage shape as a
  new single-row-per-migration metadata table:
  ```sql
  CREATE TABLE IF NOT EXISTS retrieval_cache_generation (
      retrieval_cache_schema_version INTEGER NOT NULL,
      migrated_at REAL NOT NULL
  )
  ```
  modeled on `tools/parity_index.py`'s `ledger_generation` table naming precedent only — explicitly
  **not** a full-rebuild precedent (§3). Updated in place, once per successfully applied migration
  (not once per full rebuild, unlike `parity_index.py`).
- §2 names exactly two ordered migration function signatures (bodies are this ticket's job):
  1. `migration_001_add_level1_tables(conn: sqlite3.Connection) -> None` — the Level 1
     provider-result cache table(s) this ticket implements.
  2. `migration_002_add_level2_tables(conn: sqlite3.Connection) -> None` — Level 2 context-packet
     cache. **Out of scope for this ticket** per the ticket's own Out of Scope list ("Level 2/3
     cache tables ... Phase 3/6"). Do not implement its body; the name may be stubbed/declared only
     if Plan finds a reason to, otherwise simply not added yet.
  Both are `CREATE TABLE IF NOT EXISTS` only — no `ALTER TABLE ADD COLUMN` is in scope for either
  migration (§2, explicit). Each migration commits via the same `conn.execute(...)` +
  single-`conn.commit()` shape `_init_schema()` already uses, and on success updates
  `retrieval_cache_generation` with the new version + `time.time()`-style timestamp.
  A future `migrate` entry point (not built by this ticket, but its *behavior* is frozen) applies
  every migration whose ordinal exceeds the DB's current stored version, ascending, in one
  connection — unconditionally attempted, cheap no-op when already applied, mirroring
  `_get_connection()`'s unconditional `_init_schema()` call today.
- §3/§4: same file, in-place, additive-only — never a second DB, never a full rebuild-and-swap (that
  approach is `parity_index.py`'s pattern, explicitly rejected here because the marker-only rows are
  live cache state with no external source of truth to regenerate from).
- §5: a `rebuild` fallback command is **documented, not implemented** — do not add a `rebuild`
  subcommand to `_build_parser()`/`_COMMAND_DISPATCH`; neither `migrate` nor `rebuild` is added by
  this ticket per the plan's explicit closing sentence. This directly conflicts with a literal
  reading of the ticket's own Scope bullet ("Implement the ordered `migration_00N_*` functions") if
  that were taken to mean "and wire them into the CLI" — it does not. **The migration *functions*
  are implemented; the `migrate` CLI subcommand that calls them is not**, per §5's explicit freeze.
  Flagged under Anti-Drift Hazards below.

**Citation discrepancy (non-blocking, but worth recording):** `cache_migration_plan.md` §2 cites
`migration_001_add_level1_tables` as "per §10.1 of the proposal" and `migration_002_add_level2_tables`
as "per §10.3." Reading the actual `docs/plans/knowledge-gateway-mcp-proposal.md` directly: §10.1 is
titled "Storage" (the evolve-in-place/no-second-database directive), §10.2 is "Cache Levels" (which
contains the itemized Level 0/1/2/3 definitions, including the exact Level 1 row-shape bullet list
that is word-for-word identical to this ticket's own Scope section), and §10.3 is "Conceptual Cached
Packet Schema" (the `CachedPacket` field list, which is closer to Level 2's packet shape than
Level 1's). The plan's inline section citations for migration_001/002 appear to be off-by-one
against the proposal's real section numbers. This does not change what to build — the ticket's own
Scope text and this investigation's Related Docs citation (§10.2) are unambiguous and internally
consistent with the proposal doc — but Plan should not "fix" `cache_migration_plan.md`'s citation as
part of this ticket (it's frozen; out of scope) and should cite proposal §10.2 (not §10.1) as the
authoritative source for the Level 1 row shape in its own documentation.

### `docs/plans/knowledge-gateway-mcp-proposal.md` §10.1-10.3
- §10.1 (Storage): evolve `knowledge-index/retrieval_cache.db` in place via migrations; preserve
  marker-only tables during migration; no second database absent an incompatible-lifecycle finding
  (none found — §4 of the plan already confirms this).
- §10.2 (Cache Levels) — **Level 1: Provider-result cache** row shape (this ticket's exact target),
  verbatim: "keyed query hash, deterministic intent, resolved provider-native entity IDs, and
  filters; provider name and adapter version; result payload; source IDs and paths; evidence hashes;
  provider generation; repository/branch scope; timestamps and hit counters." Explicitly called out
  as materially different from `retrieval_query_cache_rows`, "which stores only a key and metrics."
  (Level 0 — provider/index metadata — reuses existing index manifests/Graphify metadata, not a new
  table; Level 2 — assembled context-packet cache — is migration_002, out of scope; Level 3 is
  deferred indefinitely.)
- §10.3 (Conceptual Cached Packet Schema): the `CachedPacket` field list is the Level 2 packet shape
  (`packet_id`, `answer`, `statements[]`, `evidence_dependencies[]`, etc.) — relevant to
  `migration_002`, not to this ticket's `migration_001`. Confirms raw prompts/free text are never
  persisted — only a keyed query hash plus extracted entities/intent/filters, consistent with
  `retrieval_cache.py`'s existing MAY-list philosophy.

### `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`
Defines two **disjoint** field sets the new table's columns must be able to hold without ever
sharing a field name between them (§3, Non-collapse rule):
- §1 Lookup identity (routing key only): `normalized_intent`, `resolved_entity_ids`, `filters`,
  `budget_class`, `routing_policy_version`, `repo_branch_scope`.
- §2 Evidence-validity identity (freshness/safety check, computed as a separate step): 
  `evidence_fingerprints`, `validated_negative_scopes`, `adapter_version_at_validation`,
  `working_tree_overlap`, `provider_generation_at_validation`.
- §3 Non-collapse rule: a table row *may* carry both lookup-identity and validity-identity fields
  (the proposal's own §10.2 Level 1 row shape does — "keyed query hash ... resolved ... entity IDs,
  and filters" alongside "evidence hashes"), but no *function* may return a validity verdict from a
  bare lookup, and no column name may be reused across the two field families. This is a schema
  *naming* constraint this ticket owns (distinct column names for lookup vs. validity fields); the
  *behavioral* non-collapse enforcement (a lookup hit never being read as validity-proven) is
  `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s job, confirmed by that ticket's own Scope
  ("Implement evidence-validity checking per §2/§3's non-collapse rule ... as genuinely separate
  steps").
- §4 fallback rule: `PROVIDER_GENERATION` is coarsest/fallback-only; `SYMBOL`/`FILE`-backed evidence
  must never be invalidated by a bare generation bump alone when a finer fingerprint exists. Schema
  implication: the new table needs to store both a fine-grained `evidence_fingerprints`-style column
  and a `provider_generation`-style column as genuinely separate fields, never collapsed into one.
- §5: repo/branch/working-tree cache scope — branch identity is a hard partition (never
  cross-branch reuse); a new commit alone is not a miss if evidence fingerprints are unchanged;
  working-tree fingerprinting is changed-paths-intersection, not whole-tree hash. Schema
  implication: `repository_id`/`branch` (or equivalent `repo_branch_scope`) must be a real column(s)
  on the new table, not folded into another field.

## Mechanics / Engine Constraints

This is agent-orchestration/retrieval tooling, not simulation logic — no Mechanics Bible chapter or
`docs/engine/` kernel/pipeline contract governs it (same category `docs/parity_ledger/
infrastructure.yaml`'s INFRA-281 through INFRA-297 entries already establish for every sibling
module in this subsystem: "no simulation behavior, Mechanics Bible chapter, or engine contract
governs this module's semantics"). The governing "laws" for this ticket are the Knowledge Gateway
MCP's own frozen contracts (`docs/engine/contracts/knowledge_gateway_mcp/*`), not the Mechanics
Bible.

Directly-binding contracts:
- `cache_migration_plan.md` §1-§5 (constant name/location, migration function signatures, same-file
  rule, additive-only rule, rebuild-is-design-only rule) — see Current Behavior above.
- `evidence_cache_identity_contract.md` §1-§5 (field-family separation, non-collapse rule,
  provider-generation fallback rule, repo/branch/working-tree scope) — the new table's *column set*
  must be shaped to hold these fields distinctly even though this ticket does not implement the
  read/write logic that populates or validates them.
- `redaction_retention_policy.md` §6 (the 4-version-axis rule: `retrieval_cache_schema_version`
  (this ticket) ≠ `RETRIEVAL_VERSION` (existing, cache-key logic) ≠ `retrieval_event_schema_version`
  (existing, event-field shape) ≠ `redaction_policy_version` (a future ticket's write-time policy
  stamp) — AC1 of this ticket directly restates this rule and is the acceptance test for it).
- `redaction_retention_policy.md` §9 (SQLite Operational Limits — WAL mode, `busy_timeout=5000`,
  0600 file permissions, 256 MB size ceiling, per-key stampede guard): explicitly labeled
  "documented defaults; ... not implemented in `tools/retrieval_cache.py` by this ticket
  [`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`]. Implementation is deferred to a future ticket."
  This is **not merely an open question — it is hard-enforced by an existing, currently-passing
  test**: `tests/docs/test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_
  implemented` (lines 107-125) asserts directly against the real `tools/retrieval_cache.py` source
  that `"PRAGMA" not in source`, `"busy_timeout" not in source`, `"os.chmod" not in source`,
  `"chmod" not in source`, and `"os" not in imported_modules`. Its own docstring: "Anti-scope-creep
  guard: this ticket documents SQLite defaults but must never wire them into
  `tools/retrieval_cache.py`. Fails loudly if any drifting implementer adds PRAGMA/busy_timeout/
  chmod code to that module under cover of satisfying AC4." This resolves the "is §9 in scope"
  question definitively: no. The new migration code must not introduce `PRAGMA`, `busy_timeout`,
  `chmod`, or `import os` anywhere in `tools/retrieval_cache.py` — see Test Plan Regression Surface.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: two changes needed here, not one. (1) A new entry
  (next ID after the current max, `INFRA-340`, i.e. `INFRA-341`) describing the new
  `retrieval_cache_schema_version` constant, `retrieval_cache_generation` table, and
  `migration_001_add_level1_tables()` / new Level-1 table(s) this ticket ships. (2) The *existing*
  `INFRA-295` entry's `v2_evidence` line-range citations (currently `:53`, `:70-88`, `:108-151`,
  `:155-169`, `:183-192`, `:204-259`, `:266-328`, `:335-403`, `:406-433`, `:435-531`) will drift once
  new constants/functions are inserted into `tools/retrieval_cache.py` above/below the cited ranges
  — these must be re-verified against the live file during this ticket's own Parity phase, exactly
  as `INFRA-297`'s own precedent note already documents happening to it after
  `TCK-20260804-EXPANSION-RATE-WIRING` shifted its wrapper functions' line numbers. This is not
  optional busywork — a stale, unverified line citation in a `verified`-status P2 entry is itself a
  parity violation.
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`: this document is explicitly
  frozen design-only and this ticket does not edit it (per its own header, and per
  `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY` being DONE) — **do not** edit it to mark the
  migrations "implemented." If the migration functions' real bodies diverge from the design in any
  material way (e.g. an extra index, a differently-named column), that divergence belongs in
  `docs/guidelines/intentional_divergences.md`, not a silent edit to the frozen plan doc.

None of the Mechanics Bible chapters (`docs/mechanics/`) or core engine contracts (`docs/engine/
kernel.md`, `authoritative_pipeline.md`, etc.) require any change — this subsystem is explicitly
outside their scope (see Mechanics / Engine Constraints above).

## Parity Ledger Overlap

- `INFRA-295` (`docs/parity_ledger/infrastructure.yaml`) — status `verified`, priority `P2`,
  `test_path: tests/tools/test_retrieval_cache.py`. Covers the existing 3-table marker-only schema,
  `RETRIEVAL_VERSION`, `MAY_LIST_COLUMNS`, `_init_schema()`, `prune()`, and the CLI. Not a P0 entry —
  no pre-existing test_path gate beyond "keep it passing." This ticket's new code is added to the
  *same file* `INFRA-295` cites, so its line-range evidence needs re-verification (see Docs
  Requiring Update above), even though none of the *behavior* `INFRA-295` describes changes.
- `INFRA-297` (retrieval-event field family) — references `tools/retrieval_cache.py`'s
  `HIT`/`MISS`/`STALE_REJECTED` constants and `RETRIEVAL_VERSION` by name via
  `wrap_retrieval_cache_check()` in `tools/retrieval_events.py`. Not touched by this ticket's scope
  (no change to those constants or to `retrieval_events.py`), but cited here because it is the
  entry that already demonstrates the "line ranges must be re-verified after a same-file follow-on
  ticket, not carried over stale" pattern this ticket's own Parity phase must repeat for `INFRA-295`.
- No `docs/parity_ledger/*.yaml` entry exists yet for
  `docs/engine/contracts/knowledge_gateway_mcp/*` design docs themselves —
  `evidence_cache_identity_contract.md`'s own §6 cross-references note explicitly states "No
  `docs/parity_ledger/` entry accompanies this document — this subsystem is agent-orchestration/
  retrieval tooling ... not requiring a parity ledger entry" for the *contract* docs. Only the real
  *code* (`tools/retrieval_cache.py`) gets a parity entry, which is `INFRA-295`/new `INFRA-341`.
- No P0 entries are touched by this ticket's scope.

## Prior Work

- `TCK-20260729-RETRIEVAL-CACHE-LEVELS` (done) — built the original 3-level marker-only cache module
  this ticket extends. Its stored artifacts define the MAY-list philosophy, the `prune()` lifecycle
  backstop (added after an architecture-review `NEEDS_CHANGES` finding for a Durable State Rule
  violation — the same rule this ticket's new table must also satisfy: it needs a lifecycle path,
  not permanently-unbounded rows, even though GC/TTL specifics remain a later ticket's job per
  `redaction_retention_policy.md` §10).
- `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY` (done) — froze `cache_migration_plan.md` and
  `evidence_cache_identity_contract.md`, the two documents this ticket implements against. Its own
  investigation's "Risk 1" (referenced by `cache_migration_plan.md` §2's "confirmed by this ticket's
  own investigation (Risk 1) that Scope adds only new tables") is the origin of the "no `ALTER TABLE
  ADD COLUMN` required" conclusion this ticket inherits.
- `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY` (done) — ratified `redaction_retention_policy.md`,
  defining the 4th version axis (`redaction_policy_version`) and the §9/§10 operational-limits/GC
  policy that is explicitly *not* implemented by this ticket (see Mechanics/Engine Constraints).
- `tools/parity_index.py` — cited by `cache_migration_plan.md` §1 only for its
  `schema_version`-column-naming and single-row-metadata-table shape (`ledger_generation`,
  lines 156-166, populated at lines 468-490); explicitly **not** a precedent for
  `retrieval_cache.db`'s full-rebuild behavior (§3) — `parity_index.py`'s `_atomic_replace_db()`
  pattern must not be copied here.
- `tests/tools/test_retrieval_cache.py`'s `TestCrashRecovery::test_deleted_cache_db_rebuilds_
  clean_marker_only_schema` (lines 321-353) contains its own forward-looking note: "A future ticket
  that adds payload tables must extend this test, not treat it as already covering that case." This
  ticket is that future ticket — see Test Plan.

## Risks and Open Questions

1. **A pre-existing, unconditional test will fail once this ticket legitimately edits
   `tools/retrieval_cache.py` — flag for Plan/Verify, do not route around it.**
   `tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_
   introduced` (lines 343-356) runs `git diff --stat HEAD` against the live working tree and asserts
   `"tools/retrieval_cache.py"` (among 4 other paths) does not appear in that diff, with the failure
   message `"{banned_path} must never be edited by this ticket (Out of Scope)"`. That test was
   written for `TCK-20260814-KGMCP-MEASUREMENT-BASELINE`'s own scope boundary (its own investigation/
   plan), not ticket-scoped at runtime — it unconditionally diffs current-working-tree-vs-HEAD every
   time it runs, with no awareness of which ticket is currently active. This ticket's entire purpose
   is to edit `tools/retrieval_cache.py`, so once that edit exists uncommitted (or committed after
   this ticket's own HEAD), running this specific test will fail with a message that reads as if this
   ticket violated an out-of-scope rule it never agreed to. **This is not this ticket's violation** —
   it is a stale, overly-broad regression test whose git-diff-based check doesn't distinguish "edited
   by the measurement-baseline ticket" from "edited by any later, legitimate ticket." Per CLAUDE.md's
   hard rule against editing an artifact just to make a gate pass: do not weaken, delete, or
   ticket-scope-bypass this test as part of this ticket's own changes without an explicit decision —
   flag it to Plan/Verify as a known, real test-suite conflict this ticket's own Files-Changed diff
   will trigger, for a human or the workflow's own Verify phase to decide whether the test itself
   needs a follow-up fix (e.g. scoping its git-diff check to a specific commit range or ticket
   window) rather than silently editing it under cover of this ticket's schema work.
2. **§9 SQLite operational limits are out of scope, confirmed by an existing enforced test** — see
   Mechanics/Engine Constraints above; not restated as an open question since it is now resolved.
3. **`migration_002_add_level2_tables` stub or omit?** The plan names both migration functions in one
   ordered list, but this ticket's Out of Scope explicitly excludes Level 2/3 tables. Building
   `migration_001` alone (and leaving `migration_002` for the Level-2 ticket) is consistent with the
   ticket's own Scope/Out-of-Scope split; adding an empty/placeholder `migration_002` function body
   now is not requested and would risk conflicting with whatever that later ticket's own Investigate
   phase decides its real body should be. Recommend: implement only `migration_001_add_level1_tables`
   in this ticket.
4. **Exact final column list/types for the new table(s)** is a Plan-phase decision, not resolved
   here — `docs/plans/knowledge-gateway-mcp-proposal.md` §10.2 gives a *categorical* row shape
   (bulleted concepts: "keyed query hash," "evidence hashes," etc.), not literal SQL column names.
   `evidence_cache_identity_contract.md` §1/§2 gives literal field names for the lookup/validity
   split (`normalized_intent`, `resolved_entity_ids`, `evidence_fingerprints`, etc.) that should
   likely become the literal column names for those parts of the row, since
   `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s own Scope commits to using exactly those field
   names for the real lookup logic ("Implement cache-lookup identity per
   `evidence_cache_identity_contract.md` §1 (normalized_intent, resolved_entity_ids, filters,
   budget_class, routing_policy_version, repo_branch_scope) as the real key"). Using different
   column names in this ticket's schema would force a rename in that later ticket for no reason —
   Plan should map §10.2's proposal bullets directly onto §1/§2's literal contract field names,
   plus `provider name`/`adapter version`/`result payload`/`source IDs and paths`/`provider
   generation`/`timestamps and hit counters` for the parts §10.2 lists that have no contract-literal
   name yet (those need names Plan invents, informed by existing naming conventions in
   `retrieval_cache.py`, e.g. `provider_generation` echoing `corpus_generation`).
5. **Whether the new table needs its own `created_at`/lifecycle column** per the Durable State Rule
   (every durable row needs a defined lifecycle) — §10.2 explicitly lists "timestamps and hit
   counters" as part of the row shape, so this is already answered by the proposal itself, not an
   open question; noted here only to confirm it maps onto the same `prune()`-extension pattern
   `redaction_retention_policy.md` §10 anticipates ("subject to the same `prune()`-style manual
   eviction backstop... precedent the existing marker-only tables already use").

## Anti-Drift Hazards

- **Do not add a `migrate` or `rebuild` CLI subcommand.** `cache_migration_plan.md` §5 explicitly
  freezes both as design-only, not-this-ticket's-job. A literal reading of the ticket's Scope
  ("Implement the ordered `migration_00N_*` functions") could tempt wiring them into
  `_build_parser()`/`_COMMAND_DISPATCH` "for completeness" — that is scope creep against an
  explicitly frozen decision. The migration function(s) may exist and be directly callable/testable
  without any CLI entry point.
- **Do not touch `retrieval_index_cache_rows` / `retrieval_query_cache_rows` /
  `retrieval_packet_cache_rows`'s columns.** No `ALTER TABLE` against them; the acceptance criteria
  and `cache_migration_plan.md` §2 are both explicit that this migration is additive-only.
- **Do not implement any read/write logic against the new table.** This ticket ships schema only;
  `check_*`/`write_*`-style functions for the new table are `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-
  WIRING`'s job. A schema-only migration function that also happens to insert/query rows "to prove it
  works" beyond what tests require would blur that boundary.
- **Do not implement redaction/secret-scanning/size-cap enforcement**, even though the new table may
  (per the ticket's own Out-of-Scope note) include a `redaction_policy_version` column. Adding the
  column is in scope; writing anything that checks or stamps a real value into it is
  `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`'s job.
- **Do not reuse a lookup-identity field name for a validity-identity concept, or vice versa** (the
  Non-collapse rule, `evidence_cache_identity_contract.md` §3) — e.g. do not name a column
  `filters_hash` if it's meant to hold something from the validity family; that exact field name is
  already claimed by `retrieval_query_cache_rows` in a different, existing meaning too, so a
  collision here would be doubly confusing.
- **Do not touch `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
  or `tools/knowledge_gateway_mcp.py`** — explicit Out of Scope and an explicit Acceptance Criterion
  (byte-unchanged). These files were not read for this investigation because they are out of scope;
  do not open them expecting to wire anything in.
- **Do not add a `PRAGMA`, `busy_timeout`, `chmod`, or `import os` to `tools/retrieval_cache.py`.**
  Hard-enforced by the existing `tests/docs/test_redaction_retention_policy_doc.py::
  test_sqlite_defaults_not_silently_implemented` — see Risks and Open Questions.
- **Do not define a class named `ContextPacket` or import one into `tools/retrieval_cache.py`.**
  Guarded by the existing `tests/tools/test_context_packet_assembler.py::
  TestWorkflowIsolationGuards::test_assembler_does_not_import_contextpacket_from_retrieval_cache`
  (lines 418-425, reads `tools/retrieval_cache.py`'s own source directly via `rc.__file__`).
- **Do not edit `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` or
  `evidence_cache_identity_contract.md`.** Both are frozen contracts from a DONE ticket. If real
  implementation reveals the frozen design needs to change, that is a new ticket's decision (or a
  documented divergence), not a same-ticket edit.
- **Keep `retrieval_cache_schema_version` spelled exactly that way** everywhere (module constant
  name AND column name in `retrieval_cache_generation`) — the whole point of AC1 is that this name
  is never aliased to or confused with the other 3 version axes already living in this file's
  vocabulary (`RETRIEVAL_VERSION`, `retrieval_event_schema_version` in a different file,
  `redaction_policy_version` in a future ticket).
