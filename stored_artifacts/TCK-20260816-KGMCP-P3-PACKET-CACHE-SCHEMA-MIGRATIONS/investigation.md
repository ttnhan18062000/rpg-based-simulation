---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS

## Current Behavior

### `tools/retrieval_cache.py` (the module this ticket extends) — real, current state confirmed by direct read
- Module docstring (lines 1-28) is stale — still describes only the original "3-level SQLite
  retrieval cache" and does not mention the Level 1 provider-result cache or `migration_003`. Not
  this ticket's job to fix (source-code comment, not a `docs/` path), flagged only for awareness.
- `RETRIEVAL_VERSION: int = 1` (line 56) — cache-key-derivation-logic version axis. Not touched by
  this ticket.
- `retrieval_cache_schema_version: int = 1` (line 62) — the DDL/table-shape version constant this
  ticket's migration must correctly advance. **Still `1` today** — it was never bumped when
  `migration_003_add_redaction_policy_version_column` landed (that migration widens an existing
  table via `ALTER TABLE`, not a new-table `CREATE TABLE`, and its own docstring never claims a
  version bump). See Risks below — this is directly relevant to this ticket's own acceptance
  criterion ("`retrieval_cache_schema_version` correctly reflects the new schema state after this
  migration").
- Three pre-existing marker-only tables, confirmed unchanged since the Level 1 precedent ticket
  (`_init_schema()`, lines 161-205): `retrieval_index_cache_rows`, `retrieval_query_cache_rows`,
  `retrieval_packet_cache_rows` (packet_key_hash PK, `cited_hashes_json` TEXT column — **this is the
  existing, unrelated, BACKLOG-tier marker-only table this ticket must leave byte-for-byte
  untouched**; its name is already taken and must never be reused for the new Level 2 table).
- `migration_001_add_level1_tables(conn)` (lines 212-262) — **DONE**, Level 1. Creates
  `retrieval_cache_generation` (single-row metadata table: `retrieval_cache_schema_version INTEGER
  NOT NULL, migrated_at REAL NOT NULL`) and `retrieval_provider_result_cache_rows`
  (`CREATE TABLE IF NOT EXISTS` only), then does an unconditional `DELETE FROM
  retrieval_cache_generation` + `INSERT ... VALUES (?, ?)` using the **live module-level
  `retrieval_cache_schema_version` constant** (not a hardcoded literal `1`) and `time.time()`.
  **This is a load-bearing implementation detail for this ticket** — see Risks below.
- `migration_003_add_redaction_policy_version_column(conn)` (lines 265-283) — **DONE**, ordinal 3,
  landed by `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`. `ALTER TABLE ... ADD COLUMN`, guarded
  by an explicit `PRAGMA table_info` existence check. Confirms ordinal 2 is genuinely open/unclaimed
  — no `migration_002_*` function exists anywhere in the file today (confirmed by direct read of the
  full 829-line file).
- `LEVEL1_CACHE_COLUMNS` (lines 115-142) — 22 columns (21 original + `redaction_policy_version`
  added by migration_003). Every array/dict-shaped Level 1 field is represented as a plain `TEXT`
  SQL column holding a JSON-serialized string: `resolved_entity_ids`, `filters`, `source_ids`,
  `source_paths`, `evidence_fingerprints`, `validated_negative_scopes`,
  `adapter_version_at_validation`, `working_tree_overlap` — all declared `TEXT` (some `NOT NULL`,
  some nullable) in `migration_001`'s literal `CREATE TABLE` DDL (lines 230-254), and
  `write_provider_result_cache()`'s own parameter names confirm the caller-side contract: every one
  of `resolved_entity_ids_json`, `filters_json`, `provider_name_json`, `adapter_version_json`,
  `source_ids_json`, `source_paths_json`, `evidence_fingerprints_json`,
  `adapter_version_at_validation_json`, `working_tree_overlap_json` is an **already-`json.dumps()`-
  serialized string supplied by the caller**, stored verbatim as `TEXT`, deserialized via
  `json.loads()` only where the code needs to inspect it (e.g. `check_packet_cache()`'s
  `json.loads(stored_hashes_json)` against the pre-existing marker-only `retrieval_packet_cache_rows`
  table, lines 486-488 — direct proof this exact JSON-text-column + Python-side set-comparison
  pattern already works for packet-shaped invalidation logic in this module).
- No `Connection`-returning helper this ticket should reuse for writes exists yet at Level 2 scope —
  `_get_level1_connection()` (lines 598-607) is Level-1-specific (calls
  `knowledge_gateway_redaction.open_connection_with_limits()` plus `migration_001`/`migration_003`);
  this ticket does not need to create or touch a Level-2 write path, per its own Out of Scope.

### `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` (frozen design, read in full)
- §2 reserves exactly `migration_002_add_level2_tables(conn: sqlite3.Connection) -> None` at ordinal
  2, "adds the Level 2 (dependency-tracking) tables per §10.3. Same `CREATE TABLE IF NOT EXISTS`
  idempotency guarantee as migration 001; no column addition to an existing table." **Nowhere in this
  document is any literal new table name given** — it says only "the Level 2 tables" (plural,
  generically) throughout §2-§4. This directly answers Open Question 1 (see below).
- §2 also states, for every migration: "On successful application, updates
  `retrieval_cache_generation` with the new `retrieval_cache_schema_version` value and the current
  timestamp." This is the plan's own stated intent that each successfully-applied migration should
  leave the generation table holding a value reflecting the newest applied ordinal — directly
  relevant to the version-bump risk below.
- §5 confirms no `migrate`/`rebuild` CLI subcommand exists or should be added by this ticket
  (unchanged since the Level 1 precedent; `_COMMAND_DISPATCH` still has 5 entries, confirmed by
  direct read).
- This document's own header states it is frozen/design-only and is not edited by any implementing
  ticket; this ticket must not edit it (mirrors the Level 1 precedent's own Anti-Drift Hazard).

### `docs/plans/knowledge-gateway-mcp-proposal.md` §10.2/§10.3 (read in full)
- §10.2 "Level 2: Assembled context-packet cache" — categorical bullets only (answer/task summary,
  deduplicated context items, conflicts, complete evidence dependencies, routing plan, token budget
  and returned estimate, policy and schema versions, scope/freshness metadata) — no literal column
  names, exactly like Level 1's own §10.2 bullets before the Level 1 ticket mapped them onto
  contract-literal names.
  Note (carried over from the Level 1 precedent's own citation-discrepancy finding, unchanged and
  reconfirmed by this investigation's own direct read): `cache_migration_plan.md` §2 cites
  `migration_002_add_level2_tables` as "per §10.3," but the proposal's real §10.3 is "Conceptual
  Cached Packet Schema" (the `CachedPacket` field list) while §10.2 is "Cache Levels" (the
  Level 0-3 categorical descriptions, including Level 2's own bullet list). Both actually describe
  the same target — §10.2's Level 2 bullets and §10.3's `CachedPacket` fields are two views of one
  schema — so this is the same harmless off-by-one citation quirk the Level 1 investigation already
  found and explicitly declined to "fix" (the frozen doc is out of scope to edit). This ticket's own
  Scope text already correctly cites both §10.2 and §10.3 together.
- §10.3 `CachedPacket` — the literal 28-field conceptual schema (`packet_id`, `normalized_intent`,
  `query_key_hash`, `entity_ids[]`, `answer`, `statements[]`, `context_items[]`, `evidence[]`,
  `conflicts[]`, `evidence_dependencies[]`, `provenance_providers[]`,
  `providers_consulted_this_call[]`, `repository_id`, `branch`, `head_commit`,
  `working_tree_fingerprint`, `provider_generations{}`, `policy_version`, `schema_version`,
  `budget_requested`, `budget_returned`, `status`, `freshness`, `verification`, `lifecycle`,
  `created_at`, `last_validated_at`, `hit_count`) — this ticket's own Scope section already
  transcribes this list verbatim, confirmed field-for-field against the real doc text.
  **Important structural difference from Level 1's own row shape**: §10.3 lists repo/branch scope as
  **four separate fields** (`repository_id`, `branch`, `head_commit`, `working_tree_fingerprint`),
  not Level 1's single collapsed `repo_branch_scope` TEXT column
  (`evidence_cache_identity_contract.md` §1's contract-literal name). This is not a free naming
  choice — §10.3 is explicit and the ticket's own Scope already reflects it — so the new table
  cannot simply reuse Level 1's `repo_branch_scope` column shape here; it needs the four separate
  columns §10.3 names.
- Raw user prompts/free text are explicitly never persisted (§10.3 closing paragraph) — consistent
  with the existing MAY-list philosophy this module already enforces elsewhere.

### `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` (read in full)
- §1/§2 field-family split (lookup identity vs. evidence-validity identity) is Level-1-scoped by its
  own literal field names (`normalized_intent`, `resolved_entity_ids`, `filters`, `budget_class`,
  `routing_policy_version`, `repo_branch_scope` / `evidence_fingerprints`,
  `validated_negative_scopes`, `adapter_version_at_validation`, `working_tree_overlap`,
  `provider_generation_at_validation`) — none of these literal names collide with any of §10.3's
  Level 2 field names, so no Non-collapse-rule (§3) column-naming violation exists between the two
  levels' schemas as scoped.
- §3 Non-collapse rule, read carefully: "A lookup-table row (or its equivalent) may carry
  lookup-identity fields and, at most, a status used purely for cache bookkeeping ... **never** a
  freshness/verification verdict about the underlying evidence's current truth," and "A function
  that performs a lookup ... must not return a freshness/verification field." **This is a real
  tension with §10.3's own literal schema**, which explicitly lists `freshness` and `verification`
  as `CachedPacket` fields. See Risks and Open Questions below — flagged, not resolved here.
- §5 (repo/branch/working-tree cache scope, `changed_paths` intersection) is the exact mechanism the
  sibling `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION` ticket will implement against
  whatever this ticket's `evidence_dependencies` column shape is. This ticket does not implement any
  invalidation logic — only needs to leave a column shape that supports set-style intersection
  cheaply, which a JSON array of path/hash strings already does (see Open Question 2 below).

### `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §5 (read in full) — the flagged payload-size-cap question
§5 states plainly: **"Each cached payload row is capped at 64 KiB (65536 bytes, measured on the
UTF-8-encoded redacted payload)."** This is stated as a per-row cap with no level-specific carve-out
or multiplier — it does not distinguish "a Level 1 row holding one provider's result" from "a Level 2
row aggregating multiple providers' results into one packet." A Level 2 packet row, by definition
(§10.2: "Stores the final bounded packet returned to an agent," aggregating potentially several
providers' `context_items`/`evidence`/`statements`), is structurally likely to be larger than any
single Level 1 row it was assembled from. **This is a real, concrete forward-looking risk**: the same
65536-byte cap that was empirically re-derived from real Level 1 single-provider payload sizes
(10,612-30,548 bytes per `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`'s own measurement)
may prove too tight once multiple such payloads are combined into one packet row. §5 gives no
per-level exception language to lean on either way. This ticket does not decide or enforce anything
about this (schema only, no redaction/size-cap enforcement is in this ticket's scope per its own Out
of Scope) — flagged here as required context for
`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING` and
`TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT`'s own future verification work, per this
ticket's own prompt.

## Resolution of the 3 Assumptions/Open-Questions flagged by the ticket itself

**1. Exact name of the new Level 2 table.** Neither `cache_migration_plan.md` nor
`evidence_cache_identity_contract.md` names it anywhere beyond generic "the Level 2 tables" (confirmed
by full read of both). Recommended name: **`retrieval_context_packet_cache_rows`** — the exact
example name the ticket's own Scope text already suggests, and the only name choice that (a) follows
the established `retrieval_<level-concept>_cache_rows` convention (`retrieval_provider_result_cache_rows`
for Level 1) and (b) cannot collide with the existing, must-remain-untouched
`retrieval_packet_cache_rows` marker-only table, whose name is already taken by a different, unrelated
concept.

**2. One table or more than one (junction table for `evidence_dependencies`)?** Recommended: **one
table**, with `evidence_dependencies` as a single JSON-text column, matching every other array-shaped
field. Evidence for this: (a) §10.3 treats `evidence_dependencies[]` as structurally identical in
kind to seven other array-shaped `CachedPacket` fields (`entity_ids[]`, `statements[]`,
`context_items[]`, `evidence[]`, `conflicts[]`, `provenance_providers[]`,
`providers_consulted_this_call[]`) — nothing in the proposal singles it out for relational treatment.
(b) `evidence_cache_identity_contract.md` §5's `changed_paths`-intersection mechanism operates on a
plain set-intersection between a request's `changed_paths` array and a cached row's dependency paths
— this is exactly the pattern the *existing* `retrieval_packet_cache_rows` marker-only table's
`check_packet_cache()` already implements today, in Python, against a JSON-text column
(`cited_hashes_json`, `set(current_cited_hashes) != set(json.loads(stored_hashes_json))`,
`tools/retrieval_cache.py:486-488`) — direct, working, in-repo proof that a JSON-array column is
sufficient for exactly this invalidation shape, with no join query required. (c) The sibling
`TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION` ticket's own Assumptions section explicitly
defers this decision to this ticket ("if the schema ticket already chose a representation, this
ticket follows it") — so this ticket is the authoritative decision point, and a JSON column carries
no forward-incompatibility: that ticket's invalidation logic can load the column, `json.loads()` it,
and intersect in Python exactly as `check_packet_cache()` already does, with no redesign needed later.
A junction table would add real relational-integrity/join-query machinery this module has never used
anywhere and that no cited doc asks for.

**3. JSON-text-column convention for array/dict fields.** Confirmed directly against `migration_001`'s
real `CREATE TABLE` DDL and `LEVEL1_CACHE_COLUMNS`/`write_provider_result_cache()`'s parameter
names (see Current Behavior above): every array/dict-shaped Level 1 field is a plain `TEXT` SQL
column holding a caller-pre-serialized `json.dumps(...)` string, deserialized via `json.loads()` only
where inspected. No documented reason to diverge was found anywhere in the three contract docs read
for this ticket. Recommendation: mirror this exactly for all 9 array/dict-shaped Level 2 fields named
in the ticket's own Assumptions section (`entity_ids`, `statements`, `context_items`, `evidence`,
`conflicts`, `evidence_dependencies`, `provenance_providers`, `providers_consulted_this_call`,
`provider_generations` — the last being dict-shaped, `{}`, same TEXT-JSON treatment as `filters` at
Level 1).

## Mechanics / Engine Constraints

Agent-orchestration/retrieval tooling, not simulation logic — no Mechanics Bible chapter or
`docs/engine/kernel.md`/`authoritative_pipeline.md`-style core engine contract governs this module's
semantics, consistent with every prior `docs/parity_ledger/infrastructure.yaml` entry in this
subsystem (INFRA-281 through INFRA-345's own `support_boundary` fields all state this explicitly).
The governing "laws" are this subsystem's own frozen contracts:
- `cache_migration_plan.md` §2 (migration ordinal/name/idempotency rules — binding on this ticket's
  own function signature and `CREATE TABLE IF NOT EXISTS` shape).
- `evidence_cache_identity_contract.md` §3 (Non-collapse rule — see the flagged tension above), §5
  (repo/branch/working-tree scope — binding on this ticket's column shape, not its logic).
- `redaction_retention_policy.md` §5 (per-row payload size cap — context only, not enforced by this
  ticket), §6 (the 4 distinct version-axis names — a 5th, `schema_version` per §10.3, is now also in
  play; see Risks below).

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: new entry required (next ID after the current real max,
  `INFRA-345`, i.e. **`INFRA-346`**, confirmed by direct grep of the live file) describing
  `migration_002_add_level2_tables()`, the new Level 2 table's real name/column set, and its
  `retrieval_cache_generation` version-stamping behavior, mirroring INFRA-341's own level of detail
  for the Level 1 precedent.
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`: **must NOT be edited** —
  explicitly frozen design-only per its own header, exactly as the Level 1 precedent's own
  Anti-Drift Hazards already established for this same document. If the real implementation diverges
  from its design in any material way, that belongs in
  `docs/guidelines/intentional_divergences.md`, not a silent edit here.

None of the Mechanics Bible chapters (`docs/mechanics/`) or core engine contracts
(`docs/engine/kernel.md`, `authoritative_pipeline.md`, etc.) require any change — this subsystem is
explicitly outside their scope (see Mechanics/Engine Constraints above).

## Parity Ledger Overlap

- `INFRA-341` (`docs/parity_ledger/infrastructure.yaml`) — status `verified`/similar, `test_path:
  tests/tools/test_retrieval_cache.py::TestMigrations,...`. Covers `migration_001_add_level1_tables`
  and `LEVEL1_CACHE_COLUMNS`. Not modified by this ticket's scope (Level 1 table/columns stay
  untouched), but its line-range citations may drift if this ticket's new code is inserted above it
  in the file — re-verify during this ticket's own Parity phase, exactly as `INFRA-295`'s own
  precedent note already documents happening once before.
- `INFRA-343` (redaction/read-write-wiring, adds `migration_003`) — same drift-re-verification
  caveat, not otherwise touched by this ticket.
- `INFRA-345` (the size-cap recalibration hotfix, `MAX_PAYLOAD_BYTES = 65536`) — cited above for the
  flagged per-row-cap-vs-Level-2-aggregation risk; not modified by this ticket.
- No P0 entries are touched by this ticket's scope (all cited entries above are non-P0, consistent
  with this subsystem's existing priority pattern).
- No `docs/parity_ledger/*.yaml` entry exists for the contract docs themselves
  (`cache_migration_plan.md`, `evidence_cache_identity_contract.md`,
  `redaction_retention_policy.md`) — each document's own cross-references section explicitly states
  this subsystem's contract docs do not require a parity ledger entry, only the real code does.

## Prior Work

- `TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS` (DONE) — the direct Level 1 precedent this
  ticket's own structure, test conventions, and parity-entry format all mirror. Its stored
  `investigation.md`/`test_plan.md`/`plan.md` were read in full; this investigation reuses its
  established patterns (JSON-text-column convention, `TestMigrations` test-class shape, three-scenario
  migration testing: fresh DB / legacy-only DB / Level-1-already-migrated DB) rather than reinventing
  them.
- `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` (DONE) — added `migration_003`, confirming ordinal
  2 remained open, and is also the ticket whose own regression test
  (`tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_
  introduced`) already had `tools/retrieval_cache.py` **deliberately removed** from its banned-edit-
  path list, with an explicit code comment citing the Level 1 schema ticket by name. **This means the
  Level 1 precedent's own Risk 1 (a stale banned-path test firing on any further edit to
  `tools/retrieval_cache.py`) does not recur for this ticket** — confirmed by direct read of the live
  test file (`tests/tools/test_kgmcp_measurement_baseline.py:335-361`); `tools/retrieval_cache.py` is
  simply not in that list anymore.
- `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY` (DONE) — froze both contract docs this ticket
  implements against.
- `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION` (DONE) — supplies the real measured
  payload-size data cited in the per-row-cap flag above.

## Risks and Open Questions

1. **`retrieval_cache_schema_version` version-bump coupling is a real, concrete regression risk —
   flagged for Plan, not resolved here.** `migration_001_add_level1_tables` stamps
   `retrieval_cache_generation` using the **live module-level `retrieval_cache_schema_version`
   constant** (currently `1`), not a hardcoded per-migration literal
   (`tools/retrieval_cache.py:256-261`). Two existing, currently-passing regression tests call
   `migration_001` in isolation and hardcode the expectation that the stamped value is exactly `1`:
   `test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration`
   (`tests/tools/test_retrieval_cache.py:375-387`, asserts `schema_version == 1`) and
   `test_migration_is_idempotent_when_run_twice` (`:389-423`, asserts
   `generation_rows == [(1,)]`). `cache_migration_plan.md` §2's own stated intent ("updates
   `retrieval_cache_generation` with the new `retrieval_cache_schema_version` value") implies
   `migration_002` should leave the generation table reflecting a newer version once applied — the
   ticket's own acceptance criteria explicitly require exactly this
   ("`retrieval_cache_schema_version` correctly reflects the new schema state after this
   migration"). **If Plan/Implement simply bumps the shared module-level constant to `2`, both of
   the above existing tests break**, because they invoke `migration_001` alone and expect `1`, not
   `2` — the two migrations do not currently have independent, per-ordinal version literals; they
   share one mutable global. This is a genuine design tension requiring an explicit Plan-phase
   decision (e.g., have `migration_002` stamp its own literal target version directly, independent
   of the shared constant, versus restructuring the stamping mechanism to accept an explicit
   per-migration version argument) — not something Investigate should silently pick, since either
   resolution touches `migration_001`'s own already-shipped, already-tested behavior and Regression
   Surface tests that this ticket must keep passing.
2. **Non-collapse rule (§3) vs. §10.3's literal `freshness`/`verification` fields — a genuine,
   unresolved tension between two frozen docs, flagged for Architecture Review.** See Mechanics/
   Engine Constraints and the field-family analysis above. The proposal's own response wire contract
   (`knowledge_context_response.schema.json`, `required: ["status", "freshness", "verification",
   ...]`) requires every response — including one served from a Level 2 cache hit — to carry these
   three fields, which operationally justifies persisting the last-computed values on the row so a
   hit can reconstruct a valid response without recomputation. But `evidence_cache_identity_contract.md`
   §3 says a lookup-table row must "never" carry "a freshness/verification verdict about the
   underlying evidence's current truth." This ticket is schema-only (adds columns, no `check_*`-style
   lookup function that could itself "return" a verdict without a validity step, per its own Out of
   Scope) — so it does not itself violate the letter of §3's function-shape rule — but the columns'
   mere existence is worth Architecture Review's explicit sign-off given §3's absolute "never"
   language, rather than assuming the schema-vs-function distinction is obviously the intended
   reading. Do not silently drop `freshness`/`verification` from the column set to sidestep this —
   the ticket's own Scope and §10.3 both require them; flag for review, don't reroute around it.
3. **§10.3's literal `schema_version` field name is a near-collision with this module's own
   `retrieval_cache_schema_version` naming-ambiguity precedent.** `cache_migration_plan.md` §1
   explicitly reserved `retrieval_cache_schema_version` as "a scoped name, deliberately not the
   bare, ambiguous string `schema_version`," specifically to avoid confusion with existing
   version-axis vocabulary in this module. §10.3's `CachedPacket.schema_version` field is a
   genuinely different, 5th concept — the per-packet wire-response-schema version, directly
   traceable to `knowledge_context_response.schema.json:5`'s own top-level `"schema_version": 1"`
   field (confirmed by direct read) — not the DDL/table-shape version. Using the bare column name
   `schema_version` verbatim on the new table would reintroduce exactly the ambiguity
   `cache_migration_plan.md` §1 was written to prevent, even though conceptually it is a legitimate,
   distinct axis. Flagged for Plan to decide a disambiguated column name (e.g.
   `response_schema_version` or `packet_schema_version`) rather than the literal bare
   `schema_version`, consistent with this module's existing 4-distinct-version-axis discipline
   (`redaction_retention_policy.md` §6).
4. **Payload size cap applies per-row with no Level-2-specific carve-out** — see Mechanics/Engine
   Constraints above. Not this ticket's job to resolve or enforce (schema only); flagged as required
   context for the read-write-wiring and dedup/budget-enforcement child tickets per this
   investigation's own prompt.
5. **Whether `evidence_dependencies` alone is sufficient, or whether `context_items`/`evidence`
   should also be considered for future join-style access patterns**, is not raised by any cited doc
   as a concern and is not flagged as open — §10.3 treats all array fields uniformly and no
   read/write logic exists yet to need anything more granular than a JSON blob (this ticket's own Out
   of Scope explicitly excludes read/write logic).

## Anti-Drift Hazards

- **Do not name the new table `retrieval_packet_cache_rows`** — that name is already permanently
  claimed by the existing, unrelated, BACKLOG-tier marker-only table this ticket must leave
  byte-for-byte unmodified. Use `retrieval_context_packet_cache_rows` (or an equally
  unambiguous name), never anything that could be mistaken for or collide with the existing table.
- **Do not implement any read/write logic against the new table** (`check_*`/`write_*`-style
  functions) — schema only, per this ticket's own explicit Out of Scope; that is
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s job.
- **Do not implement dependency-invalidation logic** beyond the raw `evidence_dependencies` column
  existing — that is `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION`'s job. Do not add a
  junction table or any relational dependency-tracking machinery "to help" that ticket; a single JSON
  column is the recommended, evidence-backed shape (see Open Question 2 resolution above) and that
  ticket's own Assumptions explicitly defer to whatever this ticket decides.
- **Do not implement redaction/secret-scanning/size-cap enforcement** for the new table's payload-
  shaped columns (`answer`, `statements`, `context_items`, `evidence`) — schema only.
- **Do not touch `retrieval_index_cache_rows` / `retrieval_query_cache_rows` /
  `retrieval_packet_cache_rows` / `retrieval_provider_result_cache_rows`'s columns** — additive-only
  migration, `CREATE TABLE IF NOT EXISTS` for the new table alone.
- **Do not touch `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
  or `tools/knowledge_gateway_mcp.py`** — explicit Out of Scope and an explicit Acceptance Criterion
  (byte-unchanged); not read for this investigation because they are out of scope.
- **Do not add a `migrate` or `rebuild` CLI subcommand** — `cache_migration_plan.md` §5 explicitly
  freezes both as design-only; `_build_parser()`/`_COMMAND_DISPATCH` still has exactly 5 entries
  today and this ticket must not grow that list.
- **Do not add `PRAGMA`, `busy_timeout`, `chmod`, or `import os` to `tools/retrieval_cache.py`** —
  hard-enforced by the existing `tests/docs/test_redaction_retention_policy_doc.py::
  test_sqlite_defaults_not_silently_implemented`, unchanged since the Level 1 precedent.
- **Do not silently bump the shared `retrieval_cache_schema_version` module constant without
  reconciling the two existing regression tests that hardcode its value after a `migration_001`-only
  run** (see Risk 1) — this is the single highest-risk implementation detail in this ticket and must
  be an explicit Plan-phase decision, not an incidental side effect of "just following the pattern."
- **Do not edit `cache_migration_plan.md` or `evidence_cache_identity_contract.md`** — both frozen,
  from DONE tickets.
