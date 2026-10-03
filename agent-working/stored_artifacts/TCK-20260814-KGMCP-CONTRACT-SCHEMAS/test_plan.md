---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-CONTRACT-SCHEMAS
artifact_type: test_plan
tags: [ai, schema, mcp]
---

# Test Plan — TCK-20260814-KGMCP-CONTRACT-SCHEMAS

## Regression Surface

This ticket adds documentation and schema files only — no `tools/search_mcp.py` or
`tools/hybrid_retrieval.py` logic changes are in scope. The regression surface exists to confirm
nothing was accidentally touched.

Unit / tool tests (must keep passing unmodified):
- `tests/tools/test_search_mcp.py` — 15 existing tests covering `.mcp.json` schema, `_run_search`,
  `_run_health`, error-dict shapes.
- `tests/tools/test_hybrid_retrieval.py` — `hybrid_fuse_and_filter`, RRF fusion, metadata
  resolution, `UNRATED` sentinel behavior.
- `tests/tools/test_parity_ledger_schema.py` — the raw-JSON structural-parse pattern this ticket's
  new tests mirror; must still pass unmodified (`docs/parity_ledger/schema.json` is untouched).
- `tests/tools/test_context_packet_assembler.py` — confirms this ticket does not disturb the
  sibling `ContextPacket` contract/assembler this ticket's schemas must stay consistent with
  (shared `unrated`/authority-freshness vocabulary boundary).
- `tests/tools/test_validate_frontmatter.py` — the new `investigation.md`/`test_plan.md` (and any
  new `.md` contract doc) frontmatter must validate against existing `STATUS_VALUES`/
  `AUTHORITY_VALUES`/`ARTIFACT_TYPE_VALUES` enums; no enum changes are in scope for this ticket.

Integration:
- None — this ticket has no live MCP tool wiring, no `.mcp.json` change, no routing code. There is
  no arena-combat surface (not a simulation/combat-domain ticket).

## New Tests Required

Per acceptance criteria, add a new test module: `tests/tools/test_knowledge_gateway_contract_schemas.py`.

1. **Schema files exist and are valid JSON with a `schema_version`**
   - Category: unit
   - Verifies: each frozen `.schema.json` file (`knowledge_context_request`,
     `knowledge_context_response`, `knowledge_status_response`, and the shared
     `status`/`freshness`/`verification`/classification enum definitions — final filenames per the
     placement decision in `investigation.md` Risk 1) parses via `json.loads()` without error and
     contains a top-level `schema_version` field of type int, starting at `1`, mirroring
     `tools/retrieval_events.py:46`'s `retrieval_event_schema_version: int = 1` convention.
   - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

2. **`status`/`freshness`/`verification` remain three distinct, non-collapsible fields**
   - Category: unit / architecture guard
   - Verifies: the `knowledge_context` response schema declares `status`, `freshness`, and
     `verification` as three separate top-level properties, each with its own independent enum
     (`status`: `OK`/`PARTIAL`/`CONFLICTED`/`UNVERIFIED`/`ERROR`; `freshness`:
     `FRESH`/`NEEDS_REVALIDATION`/`STALE`/`UNKNOWN`; `verification`:
     `VERIFIED`/`SUPPORTED`/`INFERRED`/`UNVERIFIED`) — and that no single field's enum is a union
     or superset of another's values (guards against a future edit silently merging them into one
     confidence-style field, the explicit acceptance-criterion failure mode).
   - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

3. **`FACT`/`INFERENCE`/`DECISION` statement classification is present and closed**
   - Category: unit
   - Verifies: the statement-classification enum (§13) contains exactly
     `{FACT, INFERENCE, DECISION}` — no extra or missing values — wherever it is
     defined/referenced in the frozen schemas.
   - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

4. **`CONFLICTED` response shape matches §14**
   - Category: unit
   - Verifies: the response schema's conflict-representation branch (however it is expressed —
     `oneOf`/`allOf`-conditional per the `docs/parity_ledger/schema.json` precedent, or a
     `conflicts[]` array item schema) requires `subject`, `claims[]` (each with `value`,
     `source_id`, `authority`, `valid_from`, `valid_to`), `automatic_resolution`, and
     `recommended_action`, matching the proposal §14 conceptual shape exactly.
   - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

5. **Public request schema forbids internal routing fields**
   - Category: unit / architecture guard
   - Verifies: the `knowledge_context` request schema's top-level `properties` keys do not include
     any of a forbidden-field list (`provider_weights`, `cache_level`, `semantic_threshold`,
     `provider_forcing`/`force_provider`, `ranking_policy`, or equivalent) — and, ideally, that the
     schema sets `"additionalProperties": false` (or an equivalent explicit closed-property list)
     so a future edit cannot silently add one of these fields without the schema itself changing.
     This is the direct machine-checkable form of the acceptance criterion "the public request
     schema does not expose provider weights, cache-level selection, semantic thresholds, provider
     forcing, or ranking-policy switches."
   - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

6. **`knowledge_context` request schema covers the documented input fields**
   - Category: unit
   - Verifies: `query` is `required`; `mode`, `budget_tokens`, `changed_paths`, `include_history`,
     `evidence_detail` are present as optional properties with the correct JSON types (string,
     enum `answer`/`task_context`, integer, array of strings, boolean, string/enum respectively).
   - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

7. **`knowledge_status` response schema covers the §9.2 field list**
   - Category: unit
   - Verifies: required top-level properties exist for gateway/schema version, provider
     availability/generation, cache entry counts by kind/freshness, hit/miss/stale-rejection rates,
     per-stage latency summaries, provider fallback rates, recent invalidation reasons, branch/
     working-tree scope, and rebuildability — and that it does **not** expose provider weights,
     semantic thresholds, or provider-selection switches (mirrors test 5's forbidden-field pattern
     for the status tool).
   - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

8. **Provider adapter invocation contract is written down and checked against both adapters**
   - Category: unit / architecture guard
   - Verifies: the new `knowledge_gateway_mcp_contract.md` (or wherever the adapter invocation
     contract is written — per the placement decision in `investigation.md`) documents timeout,
     cancellation-where-supported, version reporting, and a fixture-test requirement, **and** that
     a companion test asserts the Context Search adapter's actual current values (from
     investigation: `timeout: false`, `cancellation: false`, no `adapter_version` field returned by
     `_run_health()`) are recorded honestly in its `ProviderCapabilities` descriptor rather than
     defaulted to `true`. This is a direct regression guard against fabricating capabilities the
     adapter cannot back.
   - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

9. **`ProviderCapabilities` descriptor is populated and tested for Context Search and Graphify**
   - Category: unit
   - Verifies: a descriptor (Python dict/dataclass or embedded schema fixture) exists for each of
     the two adapters with all eleven §8.1 fields present (`provider_id`, `adapter_version`,
     `stable_entity_ids`, `evidence_granularities[]`, `fine_grained_fingerprints`,
     `incremental_refresh`, `deterministic_relationships`, `historical_queries`,
     `negative_knowledge_support`, `cancellation`, `timeout`, `branch_awareness`,
     `generation_fingerprint`) and each enum-typed field's value is one of its declared closed set
     (e.g. `stable_entity_ids` ∈ `{NONE, PARTIAL, FULL}`).
   - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

10. **Router cannot claim a capability the descriptor does not advertise**
    - Category: architecture guard
    - Verifies: a test (or documented assertion helper the router must call) that given a
      `ProviderCapabilities` descriptor with e.g. `cancellation: false`, any attempt to treat that
      provider as cancellable is rejected/flagged. Since no router exists yet (Phase 0 is
      contract-only), this test operates on the descriptor/contract shape itself — e.g. asserting
      a helper function `capability_allows(descriptor, "cancellation")` returns `False` for a
      `false`-valued field — rather than on live routing code. This is the direct test form of the
      acceptance criterion citing §8.1's "stated consequence."
    - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

11. **Enum vocabularies do not alias existing registry/parity enums**
    - Category: architecture guard (anti-drift)
    - Verifies: none of the new gateway enums (`status`, `freshness`, `verification`,
      `classification`) share a value set identical to `tools/validate_frontmatter.py`'s
      `STATUS_VALUES`/`AUTHORITY_VALUES` or `docs/parity_ledger/schema.json`'s `status`/`priority`
      enums in a way that could be silently confused (e.g. assert the freshness enum's value set is
      disjoint from `{authoritative, active, historical, archive}`, and the new `status` enum's
      value set is disjoint from parity's five-value `status` enum). Directly enforces the
      Anti-Drift Hazards item in `investigation.md` about not aliasing existing vocabularies.
    - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

12. **No live tool/routing code was introduced**
    - Category: architecture guard (anti-drift / scope guard)
    - Verifies: no new `mcpServers` entry was added to `.mcp.json`, and no new module under
      `tools/` implements a callable `knowledge_context`/`knowledge_status` function (a simple
      grep-based or AST-based check against the diff/`tools/` directory listing). Guards directly
      against the ticket's Out of Scope line being silently exceeded.
    - Location: `tests/tools/test_knowledge_gateway_contract_schemas.py`

## Scoped Pytest Commands

```
# New contract/schema tests
pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v

# Regression surface: existing MCP/retrieval/context-packet/parity-schema tests this ticket must not break
pytest tests/tools/test_search_mcp.py tests/tools/test_hybrid_retrieval.py \
       tests/tools/test_parity_ledger_schema.py tests/tools/test_context_packet_assembler.py \
       tests/tools/test_validate_frontmatter.py -v
```

Never run `pytest tests/` for this ticket — scope stays within `tests/tools/`.

## Anti-Drift Test Guards

- **Forbidden-field guard (test 5/7 above)** is the single highest-value anti-drift test: it is
  the mechanical enforcement of the proposal's explicit "never expose provider weights,
  cache-level selection, semantic thresholds, provider forcing, or ranking-policy switches" rule,
  and it is cheap to defeat silently (someone adds one field to the request schema for
  "convenience" during a later ticket) without a test that fails on it.
- **Capability-honesty guard (test 8)** prevents the specific, concretely-observed failure mode
  from this investigation: it would be easy for a future editor to mark the Context Search
  adapter's `timeout`/`cancellation` as `true` by copying the proposal's aspirational text instead
  of reading `_run_search()`'s actual current behavior (no timeout wrapper, no cancellation hook
  anywhere in `tools/search_mcp.py`/`tools/hybrid_retrieval.py`).
- **Enum-disjointness guard (test 11)** prevents the new gateway vocabulary from silently drifting
  into or being confused with `tools/validate_frontmatter.py`'s frontmatter enums or
  `docs/parity_ledger/schema.json`'s `status`/`priority` enums — both already-governed vocabularies
  a careless copy-paste could accidentally reuse.
- **Scope guard (test 12)** catches the most likely drift for a "contract-only" ticket: an
  implementer starting to sketch a stub `knowledge_context` tool function "just to make the
  contract concrete," which the ticket's own Out of Scope line explicitly forbids.
- **Schema-version guard (test 1)** ensures every frozen schema is independently versionable from
  day one — a missing `schema_version` field discovered only after `KGMCP-EVIDENCE-CACHE-IDENTITY`
  or `KGMCP-REDACTION-RETENTION-POLICY` starts building against these schemas would be a much more
  expensive fix than catching it now.
