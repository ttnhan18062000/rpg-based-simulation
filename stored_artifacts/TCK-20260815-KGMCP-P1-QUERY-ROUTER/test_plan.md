---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-QUERY-ROUTER
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260815-KGMCP-P1-QUERY-ROUTER

## Regression Surface

Unit (KGMCP contract/schema layer — must stay green since the router consumes these frozen files):
- `tests/tools/test_knowledge_gateway_contract_schemas.py` — in particular:
  - `test_provider_capabilities_instance_has_all_fields_with_valid_enum_values` (both instances)
  - `test_capability_allows_rejects_unadvertised_cancellation_and_timeout` (both instances) — the
    router's real capability-consult logic must agree with this test's existing local
    `capability_allows()` semantics; a divergence between the two is itself a regression signal.
  - `test_no_live_gateway_tool_code_or_mcp_registration_introduced` — this is the **load-bearing
    anti-drift guard** for this ticket: it must still pass after adding the router (no `.mcp.json`
    `mcpServers` entry added, no `def knowledge_context(`/`def knowledge_status(` in any top-level
    `tools/*.py`).
  - `test_adapter_invocation_contract_documented_in_contract_md`

Unit (adjacent tooling the router reads from or shells out to — must not be broken by router work):
- `tests/tools/test_search_mcp.py` (15 tests — `TestMcpJson`, `TestRunSearch`,
  `TestRunSearchMissingIndex`, `TestRunHealth`, `TestPyprojectDeps`, `TestMakefileTargets`,
  `TestRunSearchFusionWiring`)
- `tests/tools/test_retrieval_baseline_metrics.py` (if present) / any `tests/tools/test_kgmcp_*`
  covering `kgmcp_baseline_corpus.py`/`kgmcp_baseline_runner.py`'s `ROUTING_SHAPES`/`_run_graphify`

Integration:
- None identified — this ticket has no kernel/pipeline/domain integration surface (agent-tooling
  only, no `src/` changes).

Architecture guard:
- `tests/tools/test_knowledge_gateway_contract_schemas.py::test_no_live_gateway_tool_code_or_mcp_registration_introduced`
  doubles as the architecture guard for "no MCP tool surface added" — see above, do not write a
  duplicate check; extend this one only if its glob (`tools/*.py`, non-recursive) needs to cover a
  new `tools/knowledge_gateway/` subpackage once Plan picks the module path.

## New Tests Required

All new tests live in a new file, path TBD by Plan (natural candidates:
`tests/tools/test_knowledge_gateway_router.py` or `tests/tools/knowledge_gateway/test_router.py`,
mirroring whichever module layout Plan selects for `tools/`).

**1. Stable-identifier recognition — one test class/group per category, grounded in real data:**

- `test_recognizes_real_ticket_id_from_tickets_done` — feed a real ID sampled live from
  `tickets/done/*.md` (e.g. any current `TCK-YYYYMMDD-*` filename stem) and assert it is classified
  as `ticket_id`, not free text. Category: unit. Verifies: ticket-ID matcher works on real IDs, not
  synthetic placeholders. Also assert a **negative** case: a legacy pre-convention filename stem
  (e.g. `adjust-01-action-speed-balance`) is *not* classified as `ticket_id` (expected — router only
  recognizes the current convention).
- `test_recognizes_real_parity_id_across_multiple_shard_prefixes` — parametrize over at least 4 real
  IDs pulled live from different `docs/parity_ledger/*.yaml` shards with different prefixes (e.g.
  one `INFRA-*`, one `COMB-*`, one compound like `SOC-CHRON-*` or `WORLD-CULT-*`, one `FACTION-
  TENSION-*`) — proves the matcher isn't hardcoded to a single enumerated prefix list. Category:
  unit. Also assert a plausible-but-nonexistent ID shaped like `ZZZZ-9999` is handled per whichever
  shape-vs-membership design Plan picks (flagged as an open question in investigation.md — this test
  must encode Plan's actual decision, not assume one).
- `test_recognizes_real_source_path_and_rejects_traversal` — assert a real existing repo file (e.g.
  `tools/search_mcp.py`) is classified as `source_path`; assert a nonexistent path is not; assert a
  traversal attempt (e.g. `../../etc/passwd` or an absolute path escaping repo root) is safely
  rejected, not resolved outside the repo tree. Category: unit + security-adjacent. Verifies: no
  path-traversal escape, no shell/subprocess used for this check.
- `test_symbol_name_delegates_to_graphify_cli_not_a_new_symbol_table` — assert the router's
  symbol-name path invokes `subprocess.run(["graphify", "query", <symbol>], ...)` in the same
  list-form-args, `cwd=repo_root` shape as `tools/agent-monitoring/kgmcp_baseline_runner.py::
  _run_graphify`. Use a subprocess mock/monkeypatch to assert the exact call signature (args list,
  no `shell=True`) rather than actually shelling out in the unit test. Category: unit. Verifies: no
  reinvented symbol table, matches existing precedent's call shape exactly.
- `test_recognizes_real_registered_document_path_from_registry` — load `docs/REGISTRY.yaml` live,
  pick a real `type: doc` entry's `path` field, assert the router classifies it as a registered
  document path; assert an unregistered `docs/`-shaped path is not. Category: unit. Verifies:
  membership check reads `path` from real `REGISTRY.yaml` structure, not an invented field name.
- `test_recognizes_real_subsystem_layer_id_from_layer_registry` — load
  `registries/layer_registry.jsonl` live, assert every one of the ~19 real registered `layer` values
  (e.g. `ai`, `combat`, `economy`, `misc`) is recognized as a subsystem ID; assert an unregistered
  string (e.g. `not_a_real_layer`) is not. Category: unit. Verifies: reads the real JSONL shape
  (`{"added_date", "layer", "note"}` per line, no separate `"id"` key — `layer` itself is the ID).

**2. §8 routing table — one test per row (7 total), each asserting the *primary* provider selected
and, where applicable, the presence of optional supporting providers in the router's rationale:**

- `test_routes_definition_terminology_architecture_to_context_search` — primary: context_search;
  optional: registry, graphify.
- `test_routes_symbol_dependency_path_to_graphify` — primary: graphify; optional: context_search.
- `test_routes_requirement_completeness_to_context_search_with_not_yet_routed_marker` — primary:
  context_search (Phase-1 fallback); **must** assert an explicit "Parity Ledger not yet routed"
  (or equivalent typed) marker is present in the router output — this is the one row where a plain
  successful-looking route without the marker is a **failure**, not a pass (per ticket scope's
  explicit "never silently drops it" requirement).
- `test_routes_ticket_historical_rationale_to_context_search_ticket_index` — primary: context_search
  / ticket index; optional: working log, registry.
- `test_routes_test_impact_of_change_to_graphify_code_test_index` — primary: graphify/code-test
  index; optional: architecture-test mapping.
- `test_routes_ticket_work_status_to_ticket_index` — primary: ticket index; optional: working log.
- `test_routes_broad_task_context_to_multiple_providers` — primary: "multiple providers"; assert
  more than one provider appears in the router's output for this shape.
- Reuse the existing tested vocabulary from `tools/agent-monitoring/kgmcp_baseline_corpus.py:23-33`
  (`ROUTING_SHAPES` — 7 canonical string IDs) as the parametrization IDs for these 7 tests rather
  than inventing new shape names, so the epic's baseline corpus and the router speak the same
  vocabulary; a mismatch between the router's internal shape IDs and `ROUTING_SHAPES` should itself
  be caught by a `test_router_shape_ids_match_baseline_corpus_routing_shapes` assertion.

**3. Capability-aware routing — the acceptance-criterion test that a capability fixture change
alters a routing decision:**

- `test_router_loads_real_capability_descriptors_from_disk` — assert the router reads
  `provider_capabilities_context_search.json`/`provider_capabilities_graphify.json` from their real
  `docs/engine/contracts/knowledge_gateway_mcp/` paths at call/init time, not hardcoded Python
  dicts (e.g. monkeypatch the file's `deterministic_relationships` value and assert the loaded
  in-memory descriptor changes accordingly).
- `test_capability_change_flips_routing_decision` (the hard acceptance-criterion test): construct a
  temporary/monkeypatched copy of `provider_capabilities_context_search.json` with
  `deterministic_relationships` changed from `"NONE"` to `"FULL"`, point the router at it, and prove
  a request shape that needs a deterministic-relationship guarantee (the symbol/dependency-path
  routing row, or a synthetic "needs FULL deterministic_relationships" request) now considers
  Context Search viable where it previously would not have been under the real `"NONE"` value —
  i.e., the routing *decision* (which provider(s) are selected, or whether a capability-constraint
  note is attached) demonstrably differs between the real fixture and the mutated one. This is the
  literal proof required by the ticket's acceptance criteria — not merely that the descriptor loads,
  but that a value change measurably changes router output.
- `test_router_never_claims_unadvertised_capability` — for both real (unmutated) descriptors, assert
  the router does not attempt/claim `cancellation` or `timeout` behavior from either provider (both
  are `false` in the real fixtures) — mirrors and should stay consistent with
  `test_capability_allows_rejects_unadvertised_cancellation_and_timeout`.
- `test_negative_knowledge_support_none_does_not_assert_absence` — both real descriptors have
  `negative_knowledge_support: "NONE"`; assert the router does not treat an empty result from either
  provider as a verified-absence signal (per §8.1's own routing-consequence example).

**4. Ambiguous-intent fallback:**

- `test_ambiguous_intent_queries_bounded_provider_set_in_parallel` — assert the fallback path calls
  more than one provider but the set is bounded (currently exactly the two known providers,
  context_search + graphify — not unbounded fan-out), and that the router reports which providers
  were used (a `providers_consulted`-shaped field on the router's output record). Category: unit.
- `test_ambiguous_intent_does_not_silently_pick_one_provider` — assert an ambiguous query does not
  get silently routed to a single default provider without the bounded-fallback marker.

**5. Scope-boundary guards:**

- `test_router_output_is_plain_typed_record_not_mcp_envelope` — assert the router's return type has
  no JSON-RPC/MCP envelope fields (no `jsonrpc`, no `id`/`method` wire fields) — it is provider(s)
  selected, matched identifier (if any), routing rationale, capability constraints applied, per the
  ticket's own "Router output is a plain typed record" scope line.
- `test_router_module_introduces_zero_mcp_zero_packet_zero_cache_code` — grep-style assertion (mirrors
  `test_no_live_gateway_tool_code_or_mcp_registration_introduced`'s style) that the new router
  module(s) do not import/reference `tools/context_packet_assembler.py` or
  `tools/retrieval_cache.py`, and do not define `def knowledge_context(`/`def knowledge_status(`.

## Scoped Pytest Commands

```
pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v
pytest tests/tools/test_knowledge_gateway_router.py -v   # path per Plan's module-layout decision
pytest tests/tools/test_search_mcp.py -v
pytest tests/tools/ -k "kgmcp or knowledge_gateway or router" -v
```

Never `pytest tests/`. Scope is `tests/tools/` — this ticket touches no `src/` code, so no
domain/simulation test directories are in scope.

## Anti-Drift Test Guards

- `test_no_live_gateway_tool_code_or_mcp_registration_introduced` (existing, regression surface
  above) is the primary guard against this ticket accidentally growing MCP server surface — keep it
  green, do not weaken or delete it to make room for router code.
- `test_capability_allows_rejects_unadvertised_cancellation_and_timeout` (existing) must keep
  passing verbatim; if the router's real `capability_allows`-equivalent function disagrees with this
  test's local copy on either fixture, that is a real bug, not a test to update.
- `test_router_never_claims_unadvertised_capability` (new, above) guards against the router silently
  starting to assume `cancellation`/`timeout`/`negative_knowledge_support` guarantees neither
  provider currently advertises — the single most likely silent-scope-creep failure mode named
  explicitly in the ticket's acceptance criteria.
- `test_routes_requirement_completeness_to_context_search_with_not_yet_routed_marker` guards against
  the Parity-Ledger-shaped row quietly degrading into an indistinguishable Context Search route —
  the ticket explicitly calls out "never silently drops it" as a hard requirement, not a nice-to-have.
- `test_ambiguous_intent_queries_bounded_provider_set_in_parallel`'s "bounded" assertion guards
  against an unbounded-fan-out regression if a third provider (e.g. a future Parity Ledger adapter)
  is added later without updating the bound.
