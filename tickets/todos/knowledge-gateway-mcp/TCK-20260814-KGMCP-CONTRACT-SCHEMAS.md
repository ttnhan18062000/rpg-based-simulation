---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-CONTRACT-SCHEMAS
phase: open
date: 2026-08-14
tags: [ai, schema, process-improvement]
---

# TCK-20260814-KGMCP-CONTRACT-SCHEMAS

## Title
Freeze MCP request/response JSON Schemas and provider adapter/capability contracts (Knowledge
Gateway Phase 0)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 0 requires freezing the versioned
contracts the rest of the Knowledge Gateway is built against before any provider routing or caching
code is written. This ticket covers the interface-shape half of Phase 0: the MCP wire contract and
the provider adapter contract. It does not cover evidence/cache identity (that is
`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`) or the redaction/retention/operational-limits policy
(`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`).

## Scope
- Freeze versioned JSON Schemas for:
  - `knowledge_context` request (proposal §9.1 conceptual input: `query`, `mode`, `budget_tokens`,
    `changed_paths`, `include_history`, `evidence_detail`)
  - `knowledge_context` success/partial/error response (§9.1 conceptual response: `status`,
    `freshness`, `verification`, `cache`, `answer`, `statements[]`, `context[]`, `evidence[]`,
    `conflicts[]`, `provenance_providers[]`, `providers_consulted_this_call[]`, budget fields)
  - `knowledge_status` response (§9.2 field list)
  - the `status` (`OK`/`PARTIAL`/`CONFLICTED`/`UNVERIFIED`/`ERROR`), `freshness`
    (`FRESH`/`NEEDS_REVALIDATION`/`STALE`/`UNKNOWN`), and `verification`
    (`VERIFIED`/`SUPPORTED`/`INFERRED`/`UNVERIFIED`) enums as three separate, non-collapsible
    dimensions per §12 and §13
  - the `FACT`/`INFERENCE`/`DECISION` statement classification (§13)
  - the `CONFLICTED` response shape in §14
- Define the provider adapter invocation contract: timeout, cancellation-where-supported, version
  reporting, and deterministic fixture-test requirements (§7.1) that every adapter (Context Search,
  Graphify now; Parity Ledger later) must satisfy.
- Define and write tests for the `ProviderCapabilities` descriptor (§8.1: `stable_entity_ids`,
  `evidence_granularities[]`, `fine_grained_fingerprints`, `incremental_refresh`,
  `deterministic_relationships`, `historical_queries`, `negative_knowledge_support`,
  `cancellation`, `timeout`, `branch_awareness`, `generation_fingerprint`) populated for the
  existing Context Search adapter (`tools/search_mcp.py` / `tools/hybrid_retrieval.py`) and a
  Graphify query adapter.
- Confirm the public `knowledge_context` contract exposes only need-oriented caller options
  (budget, changed paths, evidence detail, history relevance) and never provider weights,
  cache-level selection, semantic thresholds, provider forcing, or ranking-policy switches (§9.1).
- Store schemas under version control with an explicit `schema_version`, matching this repo's
  existing versioned-schema precedent (`docs/parity_ledger/schema.json`).

## Out of Scope
- Implementing the gateway, routing, or any live MCP tool — Phase 0 is contract-only.
- Evidence identity kinds, cache-lookup vs. evidence-validity identity, and branch/working-tree
  cache-identity contracts — covered by `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`.
- Redaction/retention policy, token-counting method, SQLite operational limits, cache-GC defaults —
  covered by `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`.
- Parity Ledger adapter capability descriptor — deferred to Phase 4 per the proposal.

## Acceptance Criteria
- [ ] Versioned JSON Schemas exist for the `knowledge_context` request, response (success/partial/
      error), `knowledge_status` response, and the `status`/`freshness`/`verification`/statement-
      classification enums, each with a `schema_version`.
- [ ] The schemas keep `status`, `freshness`, and `verification` as three distinct fields — no test
      or schema collapses them into one confidence score.
- [ ] A provider adapter invocation contract (timeout, cancellation, version, fixture-test
      requirement) is written down and both existing candidate adapters (Context Search, Graphify)
      are checked against it.
- [ ] A tested `ProviderCapabilities` descriptor is populated for the Context Search and Graphify
      adapters, with tests asserting the router cannot claim a capability the descriptor does not
      advertise (§8.1's stated consequence).
- [ ] The public request schema does not expose provider weights, cache-level selection, semantic
      thresholds, provider forcing, or ranking-policy switches.
- [ ] Tests are added under `tests/tools/` mirroring existing schema/contract test patterns in this
      repo (e.g. `docs/parity_ledger/schema.json`'s validation tests).

## Related Tickets
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (parent)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (sibling; consumes the enums this ticket freezes)
- TCK-20260612-LOCAL-CTX-MCP (DONE; built the existing `search_mcp.py` this ticket's Context Search
  adapter contract wraps)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §7.1, §8.1, §9, §12, §13, §14
- `docs/parity_ledger/schema.json` (versioned-schema precedent)
- `docs/engine/contracts/context_packet_contract.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/search_mcp.py`
- `tools/hybrid_retrieval.py`
- `tests/tools/`

## Assumptions / Open Questions
- Whether the frozen schemas live under `docs/engine/contracts/`, `docs/plans/`, or a new
  `tools/mcp_gateway/schemas/`-style location — not decided here; Investigate should follow this
  repo's existing versioned-schema placement precedent (`docs/parity_ledger/schema.json`) unless a
  clear reason favors a different location.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
