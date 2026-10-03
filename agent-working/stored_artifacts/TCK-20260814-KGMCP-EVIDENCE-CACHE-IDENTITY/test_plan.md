---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY
artifact_type: test_plan
tags: [ai, schema, process-improvement]
---

# Test Plan — TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY

## Regression Surface

Existing tests that must keep passing, unmodified — this ticket is contract/design-doc-only and
must not touch `tools/retrieval_cache.py` or its test file.

**Unit**
- `tests/tools/test_retrieval_cache.py` — all classes (`TestIndexCache`, `TestQueryCache`,
  `TestPacketCache`, `TestMayListEnforcement`, `TestStaticGuards`, `TestPrune`,
  `TestRetrievalVersionAndManifest`). Must pass byte-for-byte unchanged since AC5 requires the
  existing marker-only tables' callers/tests to remain untouched until migrated.
- `tests/tools/test_knowledge_gateway_contract_schemas.py` — the sibling
  `KGMCP-CONTRACT-SCHEMAS` ticket's test file. This ticket's new schema/contract files must not
  break any assertion in here (e.g. `test_gateway_enums_are_disjoint_from_frontmatter_and_parity_
  enums`, `test_schema_file_parses_and_has_schema_version`) — in particular, any new schema file
  this ticket adds under `docs/engine/contracts/knowledge_gateway_mcp/` must not collide with that
  file's parametrized schema-path fixture list in an unintended way (confirm the fixture there is
  scoped to specific filenames, not a directory glob, before adding new files).
- `tests/tools/test_parity_ledger_schema.py` — regression guard that `docs/parity_ledger/
  schema.json`'s structure (no `schema_version` field, `allOf` conditional count, etc.) stays
  exactly as this investigation observed it; this ticket makes no edits there, so this test is a
  pure "did I accidentally touch parity_ledger" tripwire.

**Integration** — none identified; no live cache read/write path exists to integration-test at
Phase 0 (contract-only).

**Architecture guard** — none of the existing architecture-tagged tests reference this ticket's
code areas; this ticket's own new architecture-style guards are listed under New Tests Required.

## New Tests Required

All new tests live in a new file, `tests/tools/test_evidence_cache_identity_contract.py`, mirroring
`tests/tools/test_knowledge_gateway_contract_schemas.py`'s pattern: hand-parse the new JSON/Markdown
contract artifacts and assert structural facts — no `jsonschema` library, no live cache code
imports (none exists to import at Phase 0).

1. **`test_lookup_and_validity_identity_are_structurally_distinct`**
   - Category: architecture guard
   - Verifies: the new `evidence_cache_identity_contract.md` (or its accompanying schema file, if
     the identity shapes are also captured as JSON) defines lookup-identity fields and
     validity-identity fields as two non-overlapping field sets — asserts the two sets share no
     field name, matching AC1's "no shared code path treats a lookup hit as proof of validity."
   - Location: `tests/tools/test_evidence_cache_identity_contract.py`

2. **`test_no_shared_code_or_table_conflates_lookup_hit_with_validity_proof`**
   - Category: architecture guard
   - Verifies: `tools/retrieval_cache.py` (the only real code this ticket's contract references)
     contains no function that returns a validity/freshness verdict directly from a lookup-table
     hit without a separate check — since Phase 0 adds no code, this is effectively a "confirm the
     existing module still separates `check_*_cache` (lookup) from any would-be validity check,"
     protecting the contract's central rule from being silently pre-violated by unrelated future
     drift.
   - Location: `tests/tools/test_evidence_cache_identity_contract.py`

3. **`test_all_eight_evidence_kinds_defined_with_identity_and_fingerprint`** (parametrized over the
   8 kinds: `DOCUMENT`, `DOCUMENT_SECTION`, `FILE`, `SYMBOL`, `TICKET`, `PARITY_ENTRY`,
   `REGISTRY_ENTRY`, `PROVIDER_GENERATION`)
   - Category: unit
   - Verifies: the new `evidence_identity_kinds.schema.json` (or contract doc table) defines each
     kind with a non-empty stable-identity form and preferred-fingerprint description, and that the
     kind set is closed (exactly 8, no extras, no omissions) — parses the file directly, no
     `jsonschema` dependency.
   - Location: `tests/tools/test_evidence_cache_identity_contract.py`

4. **`test_normalization_rules_cover_rename_delete_duplicate_schema_version_change`**
   - Category: unit
   - Verifies: the contract doc/schema defines normalization behavior for all four required cases
     from AC2 (renamed path, deleted record, duplicate symbol name, provider schema/version
     change) — asserts each case has a documented resolution, not just a bare mention.
   - Location: `tests/tools/test_evidence_cache_identity_contract.py`

5. **`test_provider_generation_is_fallback_only_symbol_result_survives_unrelated_generation_bump`**
   - Category: unit (fixture test, per AC3's explicit wording)
   - Verifies: given a fixture `SYMBOL`- or `FILE`-backed evidence record with an unrelated
     `PROVIDER_GENERATION` bump (different snapshot ID, unchanged symbol/file fingerprint), the
     documented invalidation rule set (asserted against directly, since no live invalidation
     function exists yet at Phase 0 — see investigation Risk 5) does NOT mark the record invalid;
     a second fixture proves a `PROVIDER_GENERATION`-only-backed record (no finer fingerprint
     available) IS invalidated by the same generation bump. This is the direct AC3 acceptance test.
   - Location: `tests/tools/test_evidence_cache_identity_contract.py`

6. **`test_new_commit_alone_is_not_a_cache_miss_but_cross_branch_reuse_is_rejected`**
   - Category: unit
   - Verifies §12.3/AC4 directly: two fixture cache-scope records sharing repository identity and
     branch, differing only in HEAD commit with unchanged direct evidence fingerprints, are
     documented as compatible (no forced miss); a second pair sharing repository identity but
     differing branch (e.g. `feature/x` vs `main`) is documented as incompatible even with
     identical evidence fingerprints.
   - Location: `tests/tools/test_evidence_cache_identity_contract.py`

7. **`test_changed_paths_intersected_with_cached_evidence_paths_approach_is_documented`**
   - Category: unit
   - Verifies the migration/identity contract documents the §12.3 changed-paths-intersection
     approach (not whole-working-tree hashing per request) as the working-tree-fingerprint method —
     a documentation-completeness assertion, not a behavioral one, since no code exists yet.
   - Location: `tests/tools/test_evidence_cache_identity_contract.py`

8. **`test_migration_design_doc_declares_schema_version_ordered_migrations_and_rebuild_command`**
   - Category: architecture guard
   - Verifies: `cache_migration_plan.md` explicitly names a `schema_version` field (scoped name per
     investigation Risk 2 — asserts it is NOT the bare, ambiguous string `schema_version` colliding
     with neither `retrieval_cache.RETRIEVAL_VERSION` nor
     `retrieval_events.retrieval_event_schema_version`), lists ordered migration steps, and
     documents a rebuild-from-scratch command — the direct AC5 acceptance test.
   - Location: `tests/tools/test_evidence_cache_identity_contract.py`

9. **`test_migration_plan_preserves_existing_marker_only_tables_and_does_not_edit_retrieval_cache_py`**
   - Category: architecture guard
   - Verifies: `git diff`/file-content check (via `ast.parse` on `tools/retrieval_cache.py`, same
     technique as `TestStaticGuards` in `test_retrieval_cache.py`) that this ticket's landing made
     no functional change to `retrieval_cache.py`'s existing three `CREATE TABLE` statements or
     `MAY_LIST_COLUMNS` — a hard regression guard against Out-of-Scope creep (Scope's "preserving
     the current marker-only tables ... until their callers/tests move").
   - Location: `tests/tools/test_evidence_cache_identity_contract.py`

10. **`test_no_migration_library_dependency_introduced`**
    - Category: architecture guard
    - Verifies: `requirements.txt`, `requirements-knowledge.txt`, and `pyproject.toml` contain no
      `alembic`/`yoyo-migrations`/`sqlite-migrate`-style dependency — regression guard against the
      Anti-Drift Hazard identified in investigation (mirrors the sibling ticket's
      `test_no_live_gateway_tool_code_or_mcp_registration_introduced`-style static guard).
    - Location: `tests/tools/test_evidence_cache_identity_contract.py`

11. **`test_new_schema_file_parses_and_has_own_schema_version`** (if the evidence-kind table is
    expressed as a `.schema.json`, mirroring `shared_enums.schema.json`'s own `schema_version: 1`
    field)
    - Category: unit
    - Verifies: the new file is valid JSON, has a `schema_version` integer field starting at 1,
      matching the structural pattern `test_knowledge_gateway_contract_schemas.py::
      test_schema_file_parses_and_has_schema_version` already established for the sibling ticket's
      files.
    - Location: `tests/tools/test_evidence_cache_identity_contract.py`

12. **`test_evidence_contract_references_not_redefines_frozen_freshness_and_verification_enums`**
    - Category: architecture guard
    - Verifies: the new contract does not restate `FRESH`/`NEEDS_REVALIDATION`/`STALE`/`UNKNOWN` or
      `VERIFIED`/`SUPPORTED`/`INFERRED`/`UNVERIFIED` as a locally-defined enum with different or
      overlapping values — either by cross-reference-only text, or (if duplicated for readability)
      an exact-match assertion against `shared_enums.schema.json`'s live values, so any future
      drift between the two files fails loudly instead of silently diverging.
    - Location: `tests/tools/test_evidence_cache_identity_contract.py`

## Scoped Pytest Commands

```bash
# This ticket's own new tests
.venv/bin/python3 -m pytest tests/tools/test_evidence_cache_identity_contract.py -v

# Regression surface: existing retrieval-cache and sibling KGMCP contract tests must still pass
.venv/bin/python3 -m pytest tests/tools/test_retrieval_cache.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_parity_ledger_schema.py -v

# Combined scoped run for this ticket's domain
.venv/bin/python3 -m pytest tests/tools/test_evidence_cache_identity_contract.py tests/tools/test_retrieval_cache.py tests/tools/test_knowledge_gateway_contract_schemas.py -v
```

Never run `pytest tests/` — scope stays within `tests/tools/` for this ticket's domain, per the
Testing Rule.

## Anti-Drift Test Guards

- **`test_migration_plan_preserves_existing_marker_only_tables_and_does_not_edit_retrieval_cache_py`**
  (New Test #9) is the primary guard against this ticket quietly turning into Phase 2/3
  implementation work — it fails loudly if `tools/retrieval_cache.py` changes at all.
- **`test_no_migration_library_dependency_introduced`** (New Test #10) catches the most likely
  silent-dependency-creep failure mode: someone reaching for `alembic` because "that's what
  migrations normally use," contradicting this repo's confirmed hand-rolled-SQL convention.
- **`test_evidence_contract_references_not_redefines_frozen_freshness_and_verification_enums`**
  (New Test #12) and **`test_provider_generation_is_fallback_only_...`** (New Test #5) together
  guard the ticket's two most scope-critical acceptance criteria (AC1/§11.1's identity separation
  and AC3's fallback-only rule) against being satisfied only in prose while the underlying design
  quietly collapses the distinction — both assert against concrete artifacts, not narrative text.
- Because this ticket touches no live code, the existing `tests/tools/test_retrieval_cache.py`
  suite run unmodified (Regression Surface) is itself an anti-drift guard: any accidental edit to
  `retrieval_cache.py`'s schema, `MAY_LIST_COLUMNS`, or `check_*_cache`/`write_*_cache` signatures
  during this ticket's work will surface as a failure there before it reaches Finalize.
- `tests/tools/test_knowledge_gateway_contract_schemas.py`'s
  `test_gateway_enums_are_disjoint_from_frontmatter_and_parity_enums` run as part of the Regression
  Surface additionally guards against this ticket's new evidence-kind vocabulary accidentally
  colliding with `AUTHORITY_VALUES`/`STATUS_VALUES`/parity `status`/`priority` enums.
