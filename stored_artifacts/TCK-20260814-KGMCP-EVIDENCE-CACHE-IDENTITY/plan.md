---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY
artifact_type: plan
tags: [ai, schema, process-improvement]
---

# Implementation Plan — TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY

## Summary

This is a Phase 0 contract-only ticket: no live code changes to `tools/retrieval_cache.py` and no
new database migrations are executed. The plan produces three new frozen artifacts under
`docs/engine/contracts/knowledge_gateway_mcp/` — a prose contract
(`evidence_cache_identity_contract.md`) that freezes the lookup-identity vs. evidence-validity-
identity split (§11.1/§11.2) and the repository/branch/working-tree cache-scope rules (§12.3), a
frozen schema (`evidence_identity_kinds.schema.json`) enumerating the 8 closed evidence identity
kinds from §12.1 with normalization rules, and a migration *design document*
(`cache_migration_plan.md`) that specifies — but does not execute — hand-written, ordered,
idempotent migration functions for adding new tables to `knowledge-index/retrieval_cache.db` in
place. It also adds one new test file, `tests/tools/test_evidence_cache_identity_contract.py`,
mirroring `tests/tools/test_knowledge_gateway_contract_schemas.py`'s hand-parse-and-assert pattern
(no `jsonschema`, no live cache-code imports beyond static/AST inspection of the existing,
untouched `tools/retrieval_cache.py`). Cross-cutting design decision, confirmed rather than left
open: migrations will be hand-written SQL functions following the `SCHEMA_VERSION`-integer-
constant + ordered-function-list pattern already used by `tools/parity_index.py`, under a scoped
name (`retrieval_cache_schema_version`) distinct from `RETRIEVAL_VERSION` and
`retrieval_event_schema_version` — no migration library is introduced.

## Steps

### Step 1 — Freeze the lookup-identity contract (§11.2)

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` (new)

**Change:** Create the contract doc's `## 1. Lookup identity` section. Define the lookup-identity
tuple exactly as the ticket's Scope states: `normalized intent + resolved entity IDs + filters +
budget class + routing-policy version + repository/branch compatibility scope`. Enumerate the
deterministic identity forms named in Scope: `symbol:<qualified-name>`, `ticket:<ticket-id>`,
`parity:<entry-id>`, `doc:<registry-id>`, `subsystem:<registered-name>`. Ground the "filters" and
"query normalization" language against the real, already-existing normalization primitives in
`tools/retrieval_cache.py`: `_normalize_query()` (`tools/retrieval_cache.py:175-176`, lowercases and
collapses whitespace) and `_hash_filters()` (`tools/retrieval_cache.py:179-180`, `json.dumps` with
`sort_keys=True` then SHA-256 via `_hash_text()` at `:171-172`) — cite these as the existing
normalization precedent the lookup-identity contract's "normalized intent" and "filters" fields
should be consistent with, without importing or modifying that code. State explicitly that lookup
identity is a cache **routing** key only — it selects *which* cached candidate to examine next, and
carries no claim about whether that candidate is still valid.

**Do NOT touch:** `tools/retrieval_cache.py`'s `_normalize_query`/`_hash_filters`/
`_hash_text`/`MAY_LIST_COLUMNS`/`_init_schema` — read-only citation only, no edits.

**Verify:** `tests/tools/test_evidence_cache_identity_contract.py::test_lookup_and_validity_identity_are_structurally_distinct` (New Test #1, partial — asserts the lookup field set exists and is well-formed; full pass requires Step 2's validity field set too).

### Step 2 — Freeze the evidence-validity-identity contract as a separate structure (§11.1)

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` (same file, new `## 2. Evidence-validity identity` section)

**Change:** Define the validity-identity field set as required by Scope: direct evidence
identities/fingerprints, validated search scopes for negative claims, adapter versions,
working-tree overlap, and provider generation as the fallback-only dependency. This field set MUST
share zero field names with Step 1's lookup-identity field set (e.g. do not reuse `filters_hash` or
`query_hash` as a validity field name) — this is the concrete, testable form of AC1's "no shared
code path treats a lookup hit as proof of validity." Reference (do not restate) the frozen
`freshness` (`FRESH`/`NEEDS_REVALIDATION`/`STALE`/`UNKNOWN`) and `verification`
(`VERIFIED`/`SUPPORTED`/`INFERRED`/`UNVERIFIED`) enums, confirmed at
`docs/engine/contracts/knowledge_gateway_mcp/shared_enums.schema.json:11-18`, by name/`$ref`-style
cross-reference only — do not copy the enum value lists into prose in a way that could silently
drift; if the value lists are quoted for readability, they must be quoted verbatim and Step 6's
disjointness/exact-match test enforces this. Add an explicit "## 3. Non-collapse rule" subsection
stating in imperative terms: no function, table row, or schema object may expose both a
lookup-identity field and a validity-verdict field keyed by the same primary identity such that a
lookup hit is read as a validity result without a separate, explicit validity check step.

**Do NOT touch:** `shared_enums.schema.json` itself (frozen by the sibling ticket
`TCK-20260814-KGMCP-CONTRACT-SCHEMAS`, now in `tickets/done/`) — reference only, no edits, no
redefinition of its enum values (confirmed current values: `status` = `OK`/`PARTIAL`/`CONFLICTED`/
`UNVERIFIED`/`ERROR`; `freshness` = `FRESH`/`NEEDS_REVALIDATION`/`STALE`/`UNKNOWN`; `verification`
= `VERIFIED`/`SUPPORTED`/`INFERRED`/`UNVERIFIED`; `statement_classification` = `FACT`/`INFERENCE`/
`DECISION` — read directly from `shared_enums.schema.json:6-23`).

**Verify:** `test_lookup_and_validity_identity_are_structurally_distinct` (New Test #1, full pass);
`test_no_shared_code_or_table_conflates_lookup_hit_with_validity_proof` (New Test #2 — this test
inspects `tools/retrieval_cache.py` via `ast.parse` per the `TestStaticGuards` precedent at
`tests/tools/test_retrieval_cache.py:216-250`, confirming none of `check_index_cache`/
`check_query_cache`/`check_packet_cache` (`tools/retrieval_cache.py:204-218`, `:266-288`,
`:335-362`) return anything beyond the existing `status`/`reason_code` dataclass fields — no
validity/freshness verdict is smuggled into today's lookup-check return shape); `test_evidence_
contract_references_not_redefines_frozen_freshness_and_verification_enums` (New Test #12).

**Note (shared-writer enumeration, Fact-Verification Requirement #2):** `retrieval_cache.py`'s
three `check_*_cache()` functions are the only code paths that currently read these tables; the
three `write_*_cache()` functions (`write_index_cache:221-253`, `write_query_cache:291-322`,
`write_packet_cache:365-392`) are the only writers, gated exclusively through
`_validate_may_list_kwargs()` (`:155-168`). This step adds no new writer and does not change that
enforcement point — Step 2's contract prose is additive documentation only, consumed by no runtime
code yet, so there is no double-write or ordering hazard to resolve at this step.

### Step 3 — Define the 8 evidence identity kinds (§12.1)

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json` (new)

**Change:** Create a frozen `.schema.json` file structurally mirroring
`shared_enums.schema.json`'s shape (confirmed pattern: `$schema`, `title`, `description`,
`schema_version: 1`, `definitions` — `shared_enums.schema.json:1-6`). Define exactly 8 evidence
identity kinds as a closed set: `DOCUMENT`, `DOCUMENT_SECTION`, `FILE`, `SYMBOL`, `TICKET`,
`PARITY_ENTRY`, `REGISTRY_ENTRY`, `PROVIDER_GENERATION` — matching the ticket's Scope list verbatim
(no reordering, no additions). For each kind, define two required string fields:
`stable_identity_form` (e.g. `SYMBOL` → `symbol:<qualified-name>`, consistent with Step 1's
deterministic identity forms) and `preferred_fingerprint` (a non-empty description of the strongest
available fingerprint for that kind — e.g. content hash for `FILE`, entry-id + `canonical_
fragment_hash` for `PARITY_ENTRY` since `docs/parity_ledger/schema.json`'s `entries` shape carries
that field per `tools/parity_index.py:116` (`_EXPECTED_COLUMNS["entries"]` includes
`canonical_fragment_hash`), and — critically — for `PROVIDER_GENERATION` specifically, document it
as having no finer-grained fingerprint available (that is *why* it is fallback-only; see Step 4).
Add a `normalization_rules` object per kind covering the four required cases from AC2: renamed
path, deleted record, duplicate symbol/name, provider schema/version change — each with a named
resolution strategy (e.g. rename → follow via secondary lookup key where the underlying provider
supports one, else treat as delete+create; delete → tombstone with `PROVIDER_GENERATION` fallback;
duplicate name → require full qualification, e.g. `symbol:<module>.<qualified-name>` not a bare
name; schema/version change → treat as a new `PROVIDER_GENERATION` epoch, invalidating only kinds
that have no finer fingerprint).

**Do NOT touch:** `docs/parity_ledger/schema.json` itself — read `_EXPECTED_COLUMNS` in
`tools/parity_index.py:108-123` for the `canonical_fragment_hash` field name only as a citation
source; do not edit either file.

**Verify:** `test_all_eight_evidence_kinds_defined_with_identity_and_fingerprint` (New Test #3,
parametrized over the 8 kinds); `test_normalization_rules_cover_rename_delete_duplicate_schema_
version_change` (New Test #4); `test_new_schema_file_parses_and_has_own_schema_version` (New Test
#11).

### Step 4 — PROVIDER_GENERATION fallback-only fixture test (AC3)

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` (new
`## 4. Provider-generation fallback rule` section, cross-referencing Step 3's schema); `tests/tools/test_evidence_cache_identity_contract.py` (new file, fixture test)

**Change:** In the contract doc, state explicitly: `PROVIDER_GENERATION` is consulted only when an
evidence record's own kind-specific fingerprint (per Step 3's table) is unavailable or already
known-stale by a finer signal; a `SYMBOL`- or `FILE`-backed record must never be invalidated by an
unrelated corpus-wide `PROVIDER_GENERATION` bump alone. In the test file, per investigation Risk 5
(confirmed: no live invalidation function exists yet at Phase 0), write the fixture as a
table-driven assertion against the *documented* rule, not against `tools/retrieval_cache.py` code
— construct two fixture records as plain dicts: (a) a `SYMBOL`-kind record with an unchanged
`stable_identity_form` value and unchanged kind-specific fingerprint, paired with a *different*
`PROVIDER_GENERATION` value than a second reference record, asserted (against the doc's stated
rule, parsed structurally, e.g. by checking the doc names `SYMBOL`/`FILE` in its
"finer-fingerprint-available" list) to remain valid; (b) a `PROVIDER_GENERATION`-only-backed record
(no finer fingerprint available per Step 3's table for that kind) that IS invalidated by the same
generation bump. This mirrors the sibling ticket's `test_context_search_descriptor_matches_real_
run_health_shape` pattern (`tests/tools/test_knowledge_gateway_contract_schemas.py:237-252`) of
asserting documented/descriptor claims against structurally-parsed fixtures, not live runtime
behavior.

**Do NOT touch:** No live invalidation code is written or imported — this is a documentation-and-
fixture-only test per investigation Risk 5's explicit caution.

**Verify:** `test_provider_generation_is_fallback_only_symbol_result_survives_unrelated_generation_bump` (New Test #5 — the direct AC3 acceptance test).

### Step 5 — Repository/branch/working-tree cache scope (§12.3)

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` (new
`## 5. Repository/branch/working-tree cache scope` section)

**Change:** Define cache-scope compatibility rules per AC4/§12.3: a new commit on the *same*
repository identity and *same* branch, with unchanged direct-evidence fingerprints, is compatible
(not automatically a cache miss). A packet cached on a feature branch is never reused when the
current scope is a different branch (e.g. `main`), even if evidence fingerprints are identical —
branch identity is a hard partition, not a soft signal. Define the working-tree-fingerprint method
as the changed-paths-intersected-with-cached-evidence-paths approach: rather than hashing the
entire working tree per request, the gateway intersects the caller-supplied changed-paths set
(confirmed as an existing, already-frozen request field: `changed_paths` — array of strings — per
`docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json`, asserted at
`tests/tools/test_knowledge_gateway_contract_schemas.py:178` `props["changed_paths"]["type"] ==
"array"`) against the set of file paths a cached packet's evidence actually depends on; only an
intersection hit forces re-validation of that packet, everything else is presumed compatible
without a full-tree hash. Cross-reference `knowledge_context_request.schema.json`'s `changed_paths`
field by name rather than redefining it.

**Do NOT touch:** `knowledge_context_request.schema.json` — frozen by the sibling ticket, reference
only.

**Verify:** `test_new_commit_alone_is_not_a_cache_miss_but_cross_branch_reuse_is_rejected` (New Test
#6); `test_changed_paths_intersected_with_cached_evidence_paths_approach_is_documented` (New Test
#7).

### Step 6 — Migration design document (§10.1/§19/AC5)

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` (new)

**Change:** Write the migration *design* document (no execution). Confirm and document the
migration-mechanism decision from the ticket's own Assumptions/Open Questions section: hand-written
SQL migration functions, following the pattern already used by `tools/parity_index.py`'s
`SCHEMA_VERSION = 1` bare module-level int constant (`tools/parity_index.py:66`) and its
`ledger_generation` metadata table whose first column is `schema_version INTEGER`
(`tools/parity_index.py:156-166`) — confirmed via direct read of `_create_schema()` — but explicitly
note this is **not** a full-rebuild-and-atomic-swap (as `parity_index.py`'s `build()`/`_atomic_
replace_db()` do at `:530`/`:504`, per investigation) since AC5 requires preserving the existing
`retrieval_index_cache_rows`/`retrieval_query_cache_rows`/`retrieval_packet_cache_rows` rows and
callers in place, not regenerating from a source-of-truth shard set. Name the new schema-DDL
version constant `retrieval_cache_schema_version` (scoped, not bare `schema_version`) — confirmed
distinct from `tools/retrieval_cache.py:45`'s `RETRIEVAL_VERSION` (cache-key versioning, per its
own comment at `:43-44`) and `tools/retrieval_events.py:46`'s `retrieval_event_schema_version`
(event-field-shape versioning, per its own comment at `:43-45`) — a genuine third concept in this
codebase's vocabulary, per investigation Risk 2. Document that the Level 1/Level 2 payload and
dependency tables (§10.1/§10.3) are wholly *new* tables, so `CREATE TABLE IF NOT EXISTS` (the
existing idempotent pattern already used by `_init_schema()`, `tools/retrieval_cache.py:108-152`)
is sufficient and safe for their creation — confirm no `ALTER TABLE ADD COLUMN` is required by this
ticket's own scope, since Scope only adds tables alongside the untouched marker-only ones
(investigation Risk 1's own conclusion, restated here explicitly as the plan's resolved position).
List migration functions as an ordered list (`migration_001_add_level1_tables`,
`migration_002_add_level2_tables`, etc., placeholders — actual bodies are Phase 2/3 work, out of
this ticket's scope) each idempotent and individually re-runnable. Document a `rebuild` CLI
subcommand design (net-new per investigation: no `migrate`/`rebuild` subcommand exists today in
`tools/retrieval_cache.py`'s CLI dispatch table, confirmed at `:515-521`) as a documented, not
implemented, fallback path — drop and recreate the whole file from scratch when a schema mismatch
is detected, analogous in spirit to `parity_index.py`'s full-rebuild approach but scoped to this
module's own eventual `rebuild` command, not built in this ticket. State the same-file-not-second-
database decision explicitly (per §10.1/Scope, reconfirmed by investigation Risk 4: no evidence of
an incompatible locking/lifecycle requirement was found).

**Do NOT touch:** `tools/retrieval_cache.py` itself — no `CREATE TABLE`, `ALTER TABLE`, or any other
DDL is executed against the real `knowledge-index/retrieval_cache.db` by this ticket. No `migrate`
or `rebuild` subcommand is added to the actual CLI dispatch table
(`tools/retrieval_cache.py:515-521`) in this ticket — this step is a design document only.

**Verify:** `test_migration_design_doc_declares_schema_version_ordered_migrations_and_rebuild_command` (New Test #8); `test_migration_plan_preserves_existing_marker_only_tables_and_does_not_edit_retrieval_cache_py` (New Test #9); `test_no_migration_library_dependency_introduced` (New Test #10).

### Step 7 — Cross-reference update and new test file assembly

**Files:** `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (optional §5 addition);
`tests/tools/test_evidence_cache_identity_contract.py` (new — assembles all 12 new tests from Steps
1-6)

**Change:** Optionally add the three new files (`evidence_cache_identity_contract.md`,
`evidence_identity_kinds.schema.json`, `cache_migration_plan.md`) to
`knowledge_gateway_mcp_contract.md`'s `## 5. Cross-references` list (`:161-174`), the same way that
section already lists `shared_enums.schema.json` and the request/response schemas — this is
housekeeping, not a hard requirement (per investigation's Docs Requiring Update note), and must not
alter any of that document's existing content, tested assertions, or the `:17-19` statement that
this sibling ticket owns evidence/cache-lookup identity content. Assemble the new test file at
`tests/tools/test_evidence_cache_identity_contract.py`, structured exactly like
`tests/tools/test_knowledge_gateway_contract_schemas.py` (raw `json.loads()` / `Path.read_text()` /
`ast.parse()` — no `jsonschema` import, confirmed absent from this repo's dependency set by
investigation). Confirm before adding `evidence_identity_kinds.schema.json` that it does not
collide with `test_knowledge_gateway_contract_schemas.py`'s `_ALL_SCHEMA_FILES` list — confirmed by
direct read (`tests/tools/test_knowledge_gateway_contract_schemas.py:35-41`) that this is an
explicit 5-item Python list of `Path` objects, not a directory glob, so a new schema file added
under the same directory is never picked up by that sibling test file's parametrization; no edit to
that file is needed or permitted.

**Do NOT touch:** `tests/tools/test_knowledge_gateway_contract_schemas.py` — read-only citation for
its `_ALL_SCHEMA_FILES` list shape; zero edits.

**Verify:** Full run of `tests/tools/test_evidence_cache_identity_contract.py` (all 12 tests) plus
the full regression run of `tests/tools/test_retrieval_cache.py`,
`tests/tools/test_knowledge_gateway_contract_schemas.py`, `tests/tools/test_parity_ledger_schema.py`
per the test plan's Scoped Pytest Commands.

## Scope Guards

- No `ALTER TABLE`/`CREATE TABLE` execution against the real `knowledge-index/retrieval_cache.db` —
  the migration design document (Step 6) specifies functions but none are implemented or run.
- No edits to `tools/retrieval_cache.py`'s existing three `CREATE TABLE` statements, `MAY_LIST_COLUMNS`, `_validate_may_list_kwargs`, or any `check_*_cache`/`write_*_cache` function signature.
- No new `migrate`/`rebuild` CLI subcommand actually added to `tools/retrieval_cache.py`'s
  `_build_parser()`/`_COMMAND_DISPATCH` (`:477-521`) — documented as a design in Step 6 only.
- No MCP request/response schema edits — `knowledge_context_request.schema.json`,
  `knowledge_context_response.schema.json`, `knowledge_status_response.schema.json`,
  `provider_capabilities.schema.json` and its two instances are the sibling
  `TCK-20260814-KGMCP-CONTRACT-SCHEMAS` ticket's scope (already DONE) — reference by name only,
  never edit.
- No redaction/retention policy, GC defaults, TTLs, or SQLite operating limits (max DB size,
  WAL/busy-timeout defaults) — `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`'s scope (not yet
  started); do not hard-code any such number in `cache_migration_plan.md`.
- No Level 3 (verified reusable knowledge) design work — explicitly deferred past Phase 0 per §10.2.
- No redefinition of `freshness`/`verification`/`status`/`statement_classification` enum values —
  `shared_enums.schema.json` is frozen; reference its `$ref` path or exact value list only.
- No `docs/parity_ledger/` entry added or `INFRA-295` status changed — this ticket makes no code
  changes, so `INFRA-295`'s `v2_evidence` remains accurate as-is (flagged for a future Phase 2/3
  ticket, not touched here).
- No migration-library dependency (`alembic`, `yoyo-migrations`, `sqlite-migrate`, or similar) added
  to `requirements.txt`, `requirements-knowledge.txt`, or `pyproject.toml`.

## Dependency Map

- Step 1 and Step 2 are sequential within the same file (`evidence_cache_identity_contract.md`) —
  Step 2 must exist before Step 6's non-collapse cross-check test (#1/#2) can fully pass, but both
  are otherwise independent of Steps 3-6's content.
- Step 3 (evidence kinds schema) is a prerequisite for Step 4 (PROVIDER_GENERATION fallback rule
  references Step 3's "finer-fingerprint-available" table) — Step 4 depends on Step 3.
- Step 5 (repository/branch/working-tree scope) is independent of Steps 1-4; can be done in
  parallel.
- Step 6 (migration design doc) is independent of Steps 1-5 in content, but shares the same target
  directory — no ordering dependency, can be done in parallel with any other step.
- Step 7 (test file assembly + optional cross-reference) depends on all of Steps 1-6 being complete,
  since it assembles tests against every prior step's artifacts and closes the loop on the
  fixture-collision check.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — lookup identity and evidence-validity identity are two distinct, separately-testable structures; no shared code path treats a lookup hit as proof of validity | Steps 1, 2 | New Test #1 `test_lookup_and_validity_identity_are_structurally_distinct`; New Test #2 `test_no_shared_code_or_table_conflates_lookup_hit_with_validity_proof` |
| AC2 — 8 evidence identity kinds each defined with stable-identity form and preferred fingerprint, plus normalization rules for rename/delete/duplicate-name/schema-version-change | Step 3 | New Test #3 `test_all_eight_evidence_kinds_defined_with_identity_and_fingerprint`; New Test #4 `test_normalization_rules_cover_rename_delete_duplicate_schema_version_change`; New Test #11 `test_new_schema_file_parses_and_has_own_schema_version` |
| AC3 — PROVIDER_GENERATION documented and tested as fallback dependency only; fixture test proves SYMBOL/FILE-backed result not invalidated by unrelated corpus-wide generation bump | Step 4 | New Test #5 `test_provider_generation_is_fallback_only_symbol_result_survives_unrelated_generation_bump` |
| AC4 — repository/branch/working-tree cache scope defined so a new commit alone is not automatically a cache miss but a feature-branch packet cannot be reused on main | Step 5 | New Test #6 `test_new_commit_alone_is_not_a_cache_miss_but_cross_branch_reuse_is_rejected`; New Test #7 `test_changed_paths_intersected_with_cached_evidence_paths_approach_is_documented` |
| AC5 — migration design document exists for evolving retrieval_cache.db in place, preserving existing marker-only table callers/tests until migrated, with a documented rebuild-from-scratch path | Step 6 | New Test #8 `test_migration_design_doc_declares_schema_version_ordered_migrations_and_rebuild_command`; New Test #9 `test_migration_plan_preserves_existing_marker_only_tables_and_does_not_edit_retrieval_cache_py`; New Test #10 `test_no_migration_library_dependency_introduced` |
| AC6 — tests mirror the existing tests/tools/test_retrieval_cache.py patterns | Step 7 (all steps' tests assembled into `tests/tools/test_evidence_cache_identity_contract.py`) | Full run of the new test file; regression run of `test_retrieval_cache.py`, `test_knowledge_gateway_contract_schemas.py`, `test_parity_ledger_schema.py` |

## Anti-Drift Notes

- **Do not implement any live cache read/write code.** Out of Scope is explicit. Steps 1, 2, 5, 6
  produce prose/schema design only; Step 4's fixture test operates on plain-dict fixtures and
  parsed-doc assertions, never on a real `check_*_cache()`/`write_*_cache()` call.
- **Do not touch `tools/retrieval_cache.py`'s existing three tables, `MAY_LIST_COLUMNS`, or
  `_init_schema()`.** New Test #9 is the hard regression guard against this — it fails loudly if
  the file changes at all.
- **`parity_index.py` is cited only for its `schema_version`-naming and metadata-table-shape
  pattern, never as a full-rebuild precedent for this ticket's migration design** — Step 6's design
  doc must explicitly state the additive-tables-only, preserve-existing-rows approach, not a
  drop-and-rebuild `_atomic_replace_db()`-style swap.
- **Naming collision risk is real:** this codebase already has `RETRIEVAL_VERSION`
  (`tools/retrieval_cache.py:45`, cache-key versioning) and `retrieval_event_schema_version`
  (`tools/retrieval_events.py:46`, event-field-shape versioning). Step 6's new constant must be
  named `retrieval_cache_schema_version` (or equally distinct), never a bare `schema_version`, and
  New Test #8 explicitly checks the name is not the bare ambiguous string.
- **`PROVIDER_GENERATION` must never be documented or tested as a default fallback for every kind.**
  AC3 requires it be fallback-only for kinds lacking a finer fingerprint; Step 3's table must show
  which kinds have finer fingerprints available, and Step 4's fixture must exercise both the
  "has finer fingerprint, survives bump" and "no finer fingerprint, is invalidated" cases.
- **Do not hard-code any redaction/retention GC number** (TTL, max DB size, WAL/busy-timeout
  defaults) anywhere in `cache_migration_plan.md` — those belong to the not-yet-started sibling
  `KGMCP-REDACTION-RETENTION-POLICY` ticket.
- **`_ALL_SCHEMA_FILES` in `test_knowledge_gateway_contract_schemas.py` is a fixed 5-item list, not
  a glob** (confirmed `tests/tools/test_knowledge_gateway_contract_schemas.py:35-41`) — adding
  `evidence_identity_kinds.schema.json` to the same directory is safe and requires no edit to that
  sibling test file.
- Since Phase 0 has no live invalidation function yet, Step 4's fixture test must assert against
  the *documented* rule text/structure, not import or call any function that does not exist —
  confirm this reading matches investigation Risk 5 before writing the test body.

## Deviations

- **New Test #10** (`test_no_migration_library_dependency_introduced`): the test_plan.md wording
  ("regression guard against the Anti-Drift Hazard identified in investigation") was implemented
  first as a raw text scan of `cache_migration_plan.md` for the forbidden library names
  (`alembic`/`yoyo-migrations`/`sqlite-migrate`), which false-failed the moment the design doc
  legitimately *named* those libraries to state that none is introduced — the identical
  cite-the-anti-pattern-to-rule-it-out move `stored_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/
  investigation.md` used for `jsonschema`. Corrected during implementation: the test now (a) scans
  `requirements.txt`/`requirements-knowledge.txt`/`pyproject.toml` for an actual dependency
  declaration (the real regression surface a library addition would touch), and (b) asserts
  `cache_migration_plan.md` contains its explicit "no migration library" disclaimer, rather than
  scanning the design doc's prose for the absence of the library names themselves. No change to
  which files this ticket touches or to any acceptance criterion — purely a test-construction
  correction, recorded here per the Workflow Rule's "never silently deviate."
