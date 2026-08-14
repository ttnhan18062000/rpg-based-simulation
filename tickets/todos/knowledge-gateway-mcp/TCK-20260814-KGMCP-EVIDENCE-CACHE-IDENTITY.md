---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY
phase: open
date: 2026-08-14
tags: [ai, schema, process-improvement]
---

# TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY

## Title
Define evidence identity kinds and freeze separate cache-lookup vs. evidence-validity identity
contracts (Knowledge Gateway Phase 0)

## Status
OPEN

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
- [ ] A written contract shows lookup identity and evidence-validity identity as two distinct,
      separately-testable structures — no shared code path treats a lookup hit as proof of
      validity.
- [ ] The 8 evidence identity kinds in §12.1 are each defined with stable-identity form and
      preferred fingerprint, plus normalization rules for rename/delete/duplicate-name/schema-
      version-change cases.
- [ ] `PROVIDER_GENERATION` is documented and tested as the fallback dependency only — a fixture
      test demonstrates a `SYMBOL`/`FILE`-backed result is not invalidated by an unrelated
      corpus-wide generation bump.
- [ ] Repository/branch/working-tree cache scope is defined such that a new commit alone is not
      automatically a cache miss (per §12.3), but a feature-branch packet cannot be reused on
      `main`.
- [ ] A migration design document exists for evolving `knowledge-index/retrieval_cache.db` in place
      (not a second database), preserving existing marker-only table callers/tests until migrated,
      with a documented rebuild-from-scratch path.
- [ ] Tests mirror the existing `tests/tools/test_retrieval_cache.py` patterns.

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
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
