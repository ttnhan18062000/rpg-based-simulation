---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY
phase: done
date: 2026-08-14
tags: [ai, schema, process-improvement]
---

# TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY

## Title
Define evidence identity kinds and freeze separate cache-lookup vs. evidence-validity identity
contracts (Knowledge Gateway Phase 0)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §11.1 states the central architectural rule that
must be contract-frozen before any caching code exists: cache **lookup** identity ("which cached
result might satisfy this request") and evidence **validity** identity ("is that candidate still
safe to return") are separate contracts and must never be one overloaded key. §12.1 requires a
closed, versioned set of evidence identity kinds with provider-qualified normalization. §12.3
requires repository/branch/working-tree cache-identity rules. §10.1 requires a migration plan that
evolves the existing `knowledge-index/retrieval_cache.db` rather than creating a second database.

## Scope
- Freeze the lookup-identity contract (§11.2): `normalized intent + resolved entity IDs + filters +
  budget class + routing-policy version + repository/branch compatibility scope`, using
  deterministic identity forms first (`symbol:<qualified-name>`, `ticket:<ticket-id>`,
  `parity:<entry-id>`, `doc:<registry-id>`, `subsystem:<registered-name>`).
- Freeze the evidence-validity-identity contract (§11.1): direct evidence identities/fingerprints,
  validated search scopes for negative claims, adapter versions, working-tree overlap, and
  provider generation as the fallback-only dependency.
- Define the closed, versioned set of evidence identity kinds from §12.1's table (`DOCUMENT`,
  `DOCUMENT_SECTION`, `FILE`, `SYMBOL`, `TICKET`, `PARITY_ENTRY`, `REGISTRY_ENTRY`,
  `PROVIDER_GENERATION`), each with its stable-identity example and preferred fingerprint, and
  define normalization for renamed paths, deleted records, duplicate symbol names, and provider
  schema/version changes.
- Define repository, branch, HEAD, and working-tree-fingerprint cache scope (§12.3), including the
  changed-paths-intersected-with-cached-evidence-paths approach so the gateway does not hash the
  entire working tree per request.
- Write the migration plan that adds the Level 1/Level 2 payload and dependency tables (§10.1,
  §10.3) to the existing gitignored `knowledge-index/retrieval_cache.db`, preserving the current
  marker-only tables (`retrieval_query_cache_rows`, per `tools/retrieval_cache.py`) until their
  callers/tests move, with `schema_version`, ordered migrations, and a rebuild-from-scratch command
  (§19).

## Out of Scope
- Implementing the cache reads/writes themselves — Phase 0 is contract-only; Phase 2/3 implement
  against this contract.
- MCP request/response schemas and provider capability descriptors —
  `TCK-20260814-KGMCP-CONTRACT-SCHEMAS`'s scope.
- Redaction/retention policy, GC defaults, SQLite operating limits (max DB size, WAL/busy-timeout
  defaults) — `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`'s scope, though this ticket's
  migration plan must be compatible with that policy once both land.
- Level 3 (verified reusable knowledge) — explicitly deferred past Phase 0 per §10.2.

## Acceptance Criteria
- [x] A written contract shows lookup identity and evidence-validity identity as two distinct,
      separately-testable structures — no shared code path treats a lookup hit as proof of
      validity.
- [x] The 8 evidence identity kinds in §12.1 are each defined with stable-identity form and
      preferred fingerprint, plus normalization rules for rename/delete/duplicate-name/schema-
      version-change cases.
- [x] `PROVIDER_GENERATION` is documented and tested as the fallback dependency only — a fixture
      test demonstrates a `SYMBOL`/`FILE`-backed result is not invalidated by an unrelated
      corpus-wide generation bump.
- [x] Repository/branch/working-tree cache scope is defined such that a new commit alone is not
      automatically a cache miss (per §12.3), but a feature-branch packet cannot be reused on
      `main`.
- [x] A migration design document exists for evolving `knowledge-index/retrieval_cache.db` in place
      (not a second database), preserving existing marker-only table callers/tests until migrated,
      with a documented rebuild-from-scratch path.
- [x] Tests mirror the existing `tests/tools/test_retrieval_cache.py` patterns.

## Related Tickets
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (parent)
- TCK-20260814-KGMCP-CONTRACT-SCHEMAS (sibling; this ticket's identity contracts reference that
  ticket's frozen `freshness`/`verification` enums)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (BACKLOG; owns the existing
  `retrieval_cache.db`/`ContextPacket` substrate this ticket's migration plan must evolve, not
  replace)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10, §11, §12, §19

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/retrieval_cache.py`
- `tests/tools/test_retrieval_cache.py`
- `knowledge-index/retrieval_cache.db` (gitignored; schema evolves, not the repo file itself)

## Assumptions / Open Questions
- Whether migrations are hand-written SQL or use a lightweight migration library already present
  in this repo's dependency set — Investigate should check for existing migration tooling
  precedent (e.g. how `docs/parity_ledger/schema.json`-derived `parity-index/parity.db` versions
  itself) before introducing a new one.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY/plan.md`'s 7 ordered
steps, with zero edits to `tools/retrieval_cache.py` (confirmed via `git diff --stat --
tools/retrieval_cache.py` returning empty after implementation).

- **Steps 1-2** (`evidence_cache_identity_contract.md` §1/§2): froze the lookup-identity tuple
  (`normalized_intent`, `resolved_entity_ids`, `filters`, `budget_class`, `routing_policy_version`,
  `repo_branch_scope`) and the evidence-validity-identity field set (`evidence_fingerprints`,
  `validated_negative_scopes`, `adapter_version_at_validation`, `working_tree_overlap`,
  `provider_generation_at_validation`) as two zero-overlap field sets, cited against
  `tools/retrieval_cache.py`'s existing `_normalize_query()`/`_hash_filters()`
  normalization primitives without importing/editing that module. Added an explicit `## 3.
  Non-collapse rule` subsection.
- **Step 3** (`evidence_identity_kinds.schema.json`): defined the closed 8-kind set (`DOCUMENT`,
  `DOCUMENT_SECTION`, `FILE`, `SYMBOL`, `TICKET`, `PARITY_ENTRY`, `REGISTRY_ENTRY`,
  `PROVIDER_GENERATION`), each with `stable_identity_form`, `preferred_fingerprint`, and a
  `normalization_rules` object covering all 4 required cases (rename/delete/duplicate_name/
  schema_version_change).
- **Step 4** (`evidence_cache_identity_contract.md` §4 + fixture test): documented
  `PROVIDER_GENERATION` as fallback-only (consulted only when no finer kind-specific fingerprint is
  available); the fixture test (`test_provider_generation_is_fallback_only_...`) asserts
  structurally, against the documented rule and the schema's `preferred_fingerprint` table, that a
  `SYMBOL`/`FILE`-backed record survives an unrelated generation bump while a
  `PROVIDER_GENERATION`-only record does not — no live invalidation function exists to call, per
  investigation Risk 5, so the test operates on plain-dict fixtures and a test-only helper function
  modeling the documented rule.
- **Step 5** (`evidence_cache_identity_contract.md` §5): defined repository/branch/working-tree
  cache scope — same-repo/same-branch new commits are not automatically a miss; branch identity is
  a hard partition (cross-branch reuse rejected unconditionally); working-tree fingerprinting uses
  the changed-paths-intersected-with-cached-evidence-paths approach, citing the already-frozen
  `changed_paths` request field by name.
- **Step 6** (`cache_migration_plan.md`): specified (not executed) ordered, idempotent migration
  function placeholders (`migration_001_add_level1_tables`, `migration_002_add_level2_tables`)
  under the scoped constant `retrieval_cache_schema_version` — explicitly distinct from
  `tools/retrieval_cache.py:45`'s `RETRIEVAL_VERSION` and `tools/retrieval_events.py:46`'s
  `retrieval_event_schema_version`. Documented why this is an additive, in-place evolution (not a
  `parity_index.py`-style full-rebuild-and-atomic-swap), and a documented-only `rebuild` CLI
  fallback (no subcommand actually added to `tools/retrieval_cache.py`'s `_COMMAND_DISPATCH`).
- **Step 7**: assembled all 12 tests into `tests/tools/test_evidence_cache_identity_contract.py`
  (structured like `test_knowledge_gateway_contract_schemas.py` — raw `json.loads()`/
  `Path.read_text()`/`ast.parse()`, no `jsonschema`). Added optional cross-reference entries to
  `knowledge_gateway_mcp_contract.md` §5 pointing at the three new files, without altering any of
  that document's existing content.

One implementation-time deviation from the test plan's literal wording, recorded in `plan.md`'s
Deviations section: `test_no_migration_library_dependency_introduced` initially scanned
`cache_migration_plan.md`'s own text for the forbidden library names (`alembic`, etc.), which
false-failed because the design doc legitimately *names* those libraries to document that none is
introduced (the same "cite the anti-pattern to rule it out" precedent
`stored_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/investigation.md` used for `jsonschema`). The
test was corrected to check `requirements.txt`/`requirements-knowledge.txt`/`pyproject.toml` for an
actual dependency declaration, and to check the design doc for its explicit "no migration library"
disclaimer instead of scanning for the absence of forbidden library names in prose.

## Test Summary
- `.venv/bin/python3 -m pytest tests/tools/test_evidence_cache_identity_contract.py -v` — 19
  passed (12 test functions, 3 parametrized: 8 kinds for Test #3, 2 provider-capability instances
  not applicable here — parametrization is solely Test #3's 8-kind sweep plus scalar tests).
- `.venv/bin/python3 -m pytest tests/tools/test_retrieval_cache.py
  tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_parity_ledger_schema.py -v`
  — 45 passed, 0 failed (full regression surface per test_plan.md, confirming zero unintended impact
  on the untouched `tools/retrieval_cache.py` and the sibling `KGMCP-CONTRACT-SCHEMAS` contract
  files).
- `python3 tools/validate_frontmatter.py` run against all three new/edited `.md` files — all pass.

## Files Changed
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` (new)
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (edited — added 3 cross-reference
  bullets to §5, no other content changed)
- `tests/tools/test_evidence_cache_identity_contract.py` (new — 12 test functions, 19 collected
  test cases)
- `tickets/inprogress/TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY.md` (this ticket — status,
  acceptance criteria, implementation notes, test summary, files changed, completion summary)
- `staging_artifacts/TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY/plan.md` (Deviations section added)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (edited by Document-Update — added 4 "Done
  (TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY)" annotations to §20's evidence-identity-kinds,
  lookup-vs-validity-identity, repo/branch/working-tree cache-identity, and retrieval_cache.db
  migration Phase 0 bullets, citing this ticket's 3 new contract docs)

`tools/retrieval_cache.py` was NOT edited — confirmed via `git diff --stat -- tools/retrieval_cache.py`
returning empty, and via this ticket's own `test_migration_plan_preserves_existing_marker_only_tables_and_does_not_edit_retrieval_cache_py`
static guard.

## Completion Summary
Froze the Knowledge Gateway MCP's evidence-identity and cache-lookup-identity contracts as three
new Phase-0 documents under `docs/engine/contracts/knowledge_gateway_mcp/`:
`evidence_cache_identity_contract.md` (lookup identity vs. evidence-validity identity as disjoint
field sets, a non-collapse rule, the PROVIDER_GENERATION fallback-only rule, and repository/branch/
working-tree cache scope), `evidence_identity_kinds.schema.json` (the closed 8-kind evidence
identity taxonomy with stable-identity forms, preferred fingerprints, and normalization rules), and
`cache_migration_plan.md` (a migration *design*, naming the scoped `retrieval_cache_schema_version`
constant and specifying — but not executing — ordered idempotent migration functions and a
documented rebuild-from-scratch fallback). All 12 new tests in
`tests/tools/test_evidence_cache_identity_contract.py` pass, alongside the full existing regression
surface (`test_retrieval_cache.py`, `test_knowledge_gateway_contract_schemas.py`,
`test_parity_ledger_schema.py`), and `tools/retrieval_cache.py` itself received zero edits, matching
this ticket's Phase-0 contract-only scope.
