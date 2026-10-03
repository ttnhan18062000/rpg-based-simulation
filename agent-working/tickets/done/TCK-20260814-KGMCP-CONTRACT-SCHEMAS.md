---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-CONTRACT-SCHEMAS
phase: done
date: 2026-08-14
tags: [ai, schema, process-improvement]
---

# TCK-20260814-KGMCP-CONTRACT-SCHEMAS

## Title
Freeze MCP request/response JSON Schemas and provider adapter/capability contracts (Knowledge
Gateway Phase 0)

## Status
DONE

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
- [x] Versioned JSON Schemas exist for the `knowledge_context` request, response (success/partial/
      error), `knowledge_status` response, and the `status`/`freshness`/`verification`/statement-
      classification enums, each with a `schema_version`.
- [x] The schemas keep `status`, `freshness`, and `verification` as three distinct fields — no test
      or schema collapses them into one confidence score.
- [x] A provider adapter invocation contract (timeout, cancellation, version, fixture-test
      requirement) is written down and both existing candidate adapters (Context Search, Graphify)
      are checked against it.
- [x] A tested `ProviderCapabilities` descriptor is populated for the Context Search and Graphify
      adapters, with tests asserting the router cannot claim a capability the descriptor does not
      advertise (§8.1's stated consequence).
- [x] The public request schema does not expose provider weights, cache-level selection, semantic
      thresholds, provider forcing, or ranking-policy switches.
- [x] Tests are added under `tests/tools/` mirroring existing schema/contract test patterns in this
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
Implemented all 9 steps of `staging_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/plan.md` as
written, no deviations from the plan's structural decisions (D1–D4). Sequence followed:

1. `docs/engine/contracts/knowledge_gateway_mcp/shared_enums.schema.json` — the four closed enums
   (`status`, `freshness`, `verification`, `statement_classification`), draft-07,
   `schema_version: 1`.
2. `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json` — the 12-field
   `ProviderCapabilities` shape, `additionalProperties: false`.
3. `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json` —
   `additionalProperties: false`, forbidden fields (`provider_weights`, `cache_level`,
   `semantic_threshold`, `provider_forcing`/`force_provider`, `ranking_policy`) absent by
   construction.
4. `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json` —
   `status`/`freshness`/`verification` as three separate `$ref`'d properties (never collapsed),
   `statements[]`/`context[]`/`evidence[]`/`conflicts[]`, `provenance_providers[]`/
   `providers_consulted_this_call[]`, an `allOf`/`if`/`then` conditional requiring `error` when
   `status == "ERROR"`. No top-level `additionalProperties: false` (Design Decision D4 —
   intentional, documented inline).
5. `docs/engine/contracts/knowledge_gateway_mcp/knowledge_status_response.schema.json` —
   `additionalProperties: false`, `reported_schema_version` distinct from the file's own
   `schema_version`.
6. `docs/engine/contracts/knowledge_gateway_mcp_contract.md` — prose adapter invocation contract
   (timeout/cancellation/version/fixture-test table for both adapters), `ProviderCapabilities`
   semantics + `capability_allows()` contract description, per-field evidence writeup for both
   populated descriptors, Design Decision D1 writeup, cross-references.
7/8. `provider_capabilities_context_search.json` and `provider_capabilities_graphify.json` —
   populated instances. Evidence for the Graphify instance was independently re-verified in this
   session (not just cited from the plan): `graphify --version` → `graphify 0.8.39`; `graphify -h`
   confirmed no `--timeout` flag on `query` or any subcommand and no cancel/kill subcommand;
   `graphify-out/graph.json` confirmed to carry `built_at_commit`, `nodes`/`links`/`hyperedges`
   keys, path-derived node `id`s, and `links`/`hyperedges` `confidence` values of exactly
   `{"EXTRACTED", "INFERRED"}` (31,422 nodes total) — matching every value the plan set.
9. `tests/tools/test_knowledge_gateway_contract_schemas.py` — all 12 test_plan.md tests
   implemented (19 collected items after parametrization). `capability_allows()` defined inline in
   the test module only, per the plan's explicit instruction not to add a new `tools/` module.

One implementation-level deviation from the plan's Step 7 prose (not a scope/behavior deviation,
recorded in staging_artifacts/plan.md's Deviations section): the plan's Step 7 text describes
citing evidence inline in a `_evidence` block; the plan's own Step 2 schema sets
`"additionalProperties": false` on `provider_capabilities.schema.json`, and Design Decision text
for Step 8 says field justifications belong in `knowledge_gateway_mcp_contract.md`, "never
asserted from the field name alone" but does not literally say where. To keep the two populated
`.json` data files honest instances of the closed schema (no ad hoc keys), all evidence citations
were placed in `knowledge_gateway_mcp_contract.md` §3 instead of inline in the JSON files
themselves; the JSON instances carry only `schema_version` + the 12 declared capability fields.
Test 9 (`test_provider_capabilities_instance_has_all_fields_with_valid_enum_values`) asserts this
exact closed key set.

Pre-existing, unrelated test failures observed in the regression run (confirmed via `git diff` —
neither file was touched by this ticket): `tests/tools/test_search_mcp.py::TestMcpJson::
test_command_is_python3` and `::test_args_point_to_search_mcp` (fail because `.mcp.json`'s
`knowledge-search` entry now shells through `tools/start_search_mcp.sh` rather than invoking
`search_mcp.py` directly — a change from an earlier, unrelated ticket), and
`tests/tools/test_validate_frontmatter.py::TestPreviouslyFrontmatterMissingDocs::...
[docs/mechanics/content_usage_matrix.md]` (that doc is missing its frontmatter block). Both are
out of this ticket's scope and were not introduced by it.

Also registered the `mcp` tag (`registries/tag_registry.jsonl`, category `subsystem-topic`) —
`staging_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/{plan,investigation,test_plan}.md` already
carried `tags: [ai, schema, mcp]` from the Plan/Investigate phases, and `mcp` was not yet in the
registry, which would have failed `validate_frontmatter.py` at Finalize. `python3
tools/tag_registry.py add mcp --category subsystem-topic --note "..."` fixed this; all three
staging artifacts now pass `validate_frontmatter.py --content-type artifact`.

Ran `graphify update .` (tests/ file added — no code-graph topology changes detected) and `make
knowledge-index-update` (docs/ files added — 2 files re-embedded incrementally) per the workflow
rule's proactive-tool-use requirements.

## Test Summary
`pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v` — 19/19 passed (12 test
functions, 7 additional parametrized cases across the two `ProviderCapabilities` instances and the
five schema files).

`pytest tests/tools/test_search_mcp.py tests/tools/test_hybrid_retrieval.py
tests/tools/test_parity_ledger_schema.py tests/tools/test_context_packet_assembler.py
tests/tools/test_validate_frontmatter.py -v` — 129 passed, 3 failed. All 3 failures are
pre-existing and unrelated to this ticket (see Implementation Notes) — confirmed via `git diff
--stat -- .mcp.json docs/mechanics/content_usage_matrix.md` showing zero changes from this
session.

## Files Changed
- `docs/engine/contracts/knowledge_gateway_mcp/shared_enums.schema.json` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_status_response.schema.json` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_graphify.json` (new)
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (new)
- `tests/tools/test_knowledge_gateway_contract_schemas.py` (new)
- `registries/tag_registry.jsonl` (modified — registered `mcp` tag, `subsystem-topic` category)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (modified — annotated Phase 0's three
  Contract-and-Measurement-Baseline bullets in §20 with "Done (TCK-20260814-KGMCP-CONTRACT-SCHEMAS)"
  pointers to the frozen schema/contract files)
- `tickets/inprogress/TCK-20260814-KGMCP-CONTRACT-SCHEMAS.md` (this file, updated)
- `knowledge-index/` (regenerated incrementally by `make knowledge-index-update`; not
  hand-edited)
- `graphify-out/` (checked by `graphify update .`; no topology changes written)

## Completion Summary
Froze the Knowledge Gateway MCP's Phase 0 wire and provider-adapter contracts as documentation-
grade artifacts under `docs/engine/contracts/knowledge_gateway_mcp/` (five `schema_version: 1`
JSON Schema files plus two populated `ProviderCapabilities` instances) and a sibling prose
contract, `docs/engine/contracts/knowledge_gateway_mcp_contract.md`, describing the provider
adapter invocation contract and citing direct evidence (re-verified this session) for every
Context Search and Graphify capability value. `status`/`freshness`/`verification` are frozen as
three distinct, non-collapsible fields; the public `knowledge_context` request schema excludes all
named provider-internal routing controls via `additionalProperties: false`. All 12
`test_plan.md`-required tests were added in `tests/tools/test_knowledge_gateway_contract_schemas.py`
(19 collected cases, all passing) with no `jsonschema` dependency added, mirroring
`tests/tools/test_parity_ledger_schema.py`'s hand-rolled structural-assertion pattern. No
gateway, routing, or live MCP tool code was implemented — Phase 0 stays contract-only, enforced
by the test suite's own scope guard.
