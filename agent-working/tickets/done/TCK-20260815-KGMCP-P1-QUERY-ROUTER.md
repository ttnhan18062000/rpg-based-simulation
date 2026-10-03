---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-QUERY-ROUTER
phase: done
date: 2026-08-15
tags: [ai, mcp]
---

# TCK-20260815-KGMCP-P1-QUERY-ROUTER

## Title
Deterministic query router: stable-identifier recognition, intent/provider routing table,
provider-capability-aware routing decisions

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §8 defines deterministic routing over Context Search
and Graphify: recognize stable identifiers (ticket IDs, parity IDs, source paths, symbol names,
registered document paths, subsystem IDs) before classifying free text, route via an intent/shape
table, and consult providers' frozen capability descriptors
(`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json`,
`provider_capabilities_graphify.json`) rather than assume identical guarantees across providers.
This ticket builds the router as a standalone, directly-testable module — no MCP tool surface, no
packet assembly, no caching. It is the first child of
`TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC`.

## Scope
- Implement stable-identifier recognition: regex/pattern matchers for ticket IDs
  (`TCK-YYYYMMDD-*`), parity IDs (`INFRA-\d+` and sibling subsystem prefixes — enumerate from
  `docs/parity_ledger/*.yaml`'s real `id` prefixes, not invented), source paths (existing-file
  check against the repo tree), symbol names (delegate detection to Graphify's own lookup, not a
  new symbol table), registered document paths (`docs/REGISTRY.yaml` membership), and known
  subsystem IDs (`registries/layer_registry.jsonl`).
- Implement the §8 intent/provider routing table exactly as specified (7 rows: definition/
  terminology, symbol/dependency, requirement-completeness [routes to Parity Ledger conceptually,
  but Parity Ledger adapter itself is Phase 4 — this ticket routes to Context Search as the Phase-1
  fallback and records the Parity-Ledger-shaped intent as unsupported-until-Phase-4, never silently
  drops it] , ticket/historical rationale, test-impact, ticket-status, broad-task-context).
- Implement provider-capability-aware routing: load and validate both frozen
  `provider_capabilities_*.json` instances against
  `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json`; a routing
  decision must consult `stable_entity_ids`, `deterministic_relationships`, and
  `negative_knowledge_support` before selecting a provider for a request shape that needs those
  guarantees (§8.1's routing-consequence examples).
- Implement the ambiguous-intent fallback: query a small bounded provider set in parallel, merge,
  and report which providers were used (`providers_consulted_this_call`-shaped output at the router
  level, not yet the full MCP response envelope — that's a downstream ticket's job).
- Router output is a plain typed record (provider(s) selected, matched identifier if any, routing
  rationale, capability constraints applied) — not a JSON-RPC/MCP response; this ticket has no MCP
  server code.

## Out of Scope
- MCP tool exposure (`knowledge_context`/`knowledge_status`) — separate ticket
  (`TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`).
- Packet/statement/evidence assembly — separate ticket (`TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY`).
- A real Parity Ledger adapter — Phase 4. Requirement-completeness-shaped queries route to Context
  Search in Phase 1 with an explicit "Parity Ledger not yet routed" marker, never a silent
  misroute.
- Model-based intent classification — deterministic-only per proposal §9.1.
- Caching of routing decisions.

## Acceptance Criteria
- [x] All 6 stable-identifier categories are recognized with real, tested pattern/lookup logic
      grounded in this repo's actual ID formats (not placeholder regexes).
- [x] The §8 routing table's 7 intent shapes each have a real router decision path, including the
      explicit Phase-1 fallback + not-yet-routed marker for the Parity-Ledger-shaped row.
- [x] Router decisions demonstrably consult the real frozen `provider_capabilities_*.json` files
      (loaded from disk, not hardcoded) — a test must prove a capability change in the fixture
      changes a routing decision.
- [x] Ambiguous-intent fallback queries a bounded (not unbounded) provider set and reports which
      were used.
- [x] Zero MCP server code, zero packet-assembly code, zero cache code in this ticket's diff.

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC (parent)
- TCK-20260814-KGMCP-CONTRACT-SCHEMAS (DONE; source of the frozen `provider_capabilities*` files
  this ticket consumes)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §8, §8.1

## Related Stored Artifacts
None yet.

## Related Code Areas
- `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json`,
  `provider_capabilities_context_search.json`, `provider_capabilities_graphify.json`
- `docs/REGISTRY.yaml`, `registries/layer_registry.jsonl`, `docs/parity_ledger/*.yaml` (identifier
  recognition sources)
- New: a router module under `tools/` (exact path decided by this ticket's Plan phase)

## Assumptions / Open Questions
- Whether the router lives at `tools/knowledge_gateway/router.py` (package layout, anticipating
  Phase 2+ growth) or a single `tools/knowledge_gateway_router.py` — Plan phase decides based on
  `tools/search_mcp.py`'s precedent (single-file) vs. this epic's larger eventual surface.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260815-KGMCP-P1-QUERY-ROUTER/plan.md`'s 6 ordered steps,
in a single new flat module `tools/knowledge_gateway_router.py` (Module Layout Decision followed
exactly — no subpackage).

- **Step 1** — `load_capability_descriptor(path)` reads+`json.loads()`s a
  `provider_capabilities_*.json` file fresh from disk on every call (no module-level cache), so a
  fixture-file edit is observable to the very next call. `_CONTEXT_SEARCH_CAPS_PATH` /
  `_GRAPHIFY_CAPS_PATH` point at the two frozen instance files.
- **Step 2** — Six matchers implemented: `match_ticket_id` (`^TCK-\d{8}-[A-Z0-9-]+$`),
  `match_parity_id` (shape-only `^[A-Z]+(-[A-Z]+)*-\d+$` per Design Decision D1, no hardcoded
  prefix enum), `match_source_path` (pure `pathlib`, `Path.resolve().is_relative_to(repo_root)`
  traversal guard, no shell), `match_symbol_name` (always delegates to
  `subprocess.run(["graphify", "query", text], cwd=repo_root, capture_output=True, text=True,
  timeout=120)`, mirroring `tools/agent-monitoring/kgmcp_baseline_runner.py:92-114` exactly),
  `match_registered_doc_path` (`docs/REGISTRY.yaml`'s `path` field on `type: doc` entries),
  `match_subsystem_id` (`registries/layer_registry.jsonl`'s `layer` field).
- **Step 3** — `ROUTING_TABLE` (7 rows) keyed by `ROUTING_SHAPES` imported (not re-typed) from
  `tools/agent-monitoring/kgmcp_baseline_corpus.py` via the same `importlib.util` sibling-load
  pattern `tools/search_mcp.py` uses; a module-load-time `assert` guards the two vocabularies
  from silently desyncing. The `requirement_completeness_verification` row carries an explicit
  typed `not_yet_routed: str | None = "parity_ledger"` field (never a free-text note).
- **Step 4** — Real `capability_allows(descriptor, capability_name)` (same signature/semantics as
  the existing test-local stub at
  `tests/tools/test_knowledge_gateway_contract_schemas.py:287-293`, which was left untouched — a
  new cross-check test proves agreement instead of replacing it). `apply_capability_constraints(row,
  requested_guarantee)` reasons over `deterministic_relationships` rank (`NONE < PARTIAL < FULL`)
  across a row's primary providers and returns a `CapabilityConstraint(satisfied, reason)` —
  never silently claims a guarantee no primary provider advertises.
- **Step 5** — `route_ambiguous(query_text)` queries exactly `{context_search, graphify}`
  sequentially (a plain `for` loop, no `ThreadPoolExecutor`/`asyncio`) per Design Decision D3, and
  reports both in `RoutingDecision.providers_consulted`.
- **Step 6** — `RoutingDecision` is a plain frozen `@dataclass` (`providers_selected`,
  `matched_identifier`, `routing_shape`, `rationale`, `capability_constraints`, `not_yet_routed`,
  `providers_consulted`) — no `jsonrpc`/`id`/`method` envelope fields. `route(query_text,
  requested_guarantee=None)` dispatches: (1) six identifier matchers in the fixed order
  ticket_id → parity_id → source_path → registered_doc_path → subsystem_id → symbol_name; (2) on
  no identifier match, deterministic keyword-heuristic classification into one of the 7 routing
  shapes (verified against all 7 real, versioned queries in
  `kgmcp_baseline_corpus.CORPUS` — every one classifies to its documented `routing_shape`); (3) on
  no shape match, falls through to `route_ambiguous`.

**Review-mandated rename applied**: `test_ambiguous_intent_queries_bounded_provider_set_in_parallel`
was implemented under the corrected name `test_ambiguous_intent_queries_bounded_provider_set` (no
`_in_parallel` suffix), per the explicit Architecture Review ruling relayed with this ticket — the
test's real assertions (bounded `{context_search, graphify}` set, `providers_consulted` reporting)
never required actual concurrency, and the ticket's own formal Acceptance Criteria bullet never
says "in parallel" either. No threading/concurrency was faked; `route_ambiguous` is the
sequential-bounded implementation Design Decision D3 specifies.

**Implementation-level decision beyond the plan's explicit text (not a scope deviation, a
necessary dispatcher-wiring choice the plan left implicit):** in the `route()` dispatcher's fixed
identifier-matcher order, `match_symbol_name` (subprocess-bound, delegates to the real `graphify`
CLI) is only attempted when the *entire* query text is single-identifier-shaped (no whitespace,
`^[A-Za-z_][A-Za-z0-9_]*$`) — a full natural-language sentence is never a bare "symbol name" on
its own; it belongs to Step 6's shape classification instead. This gating lives in the dispatcher
only; `match_symbol_name` itself still "always delegates" once called, per its own contract and
per the test that exercises it directly with a mocked `subprocess.run`.

Scope guards verified in the diff: no `.mcp.json` edit, no `knowledge_context`/`knowledge_status`
definitions anywhere in `tools/*.py`, no import/reference of `tools/context_packet_assembler.py`
or `tools/retrieval_cache.py`, no caching (no module-level cache dict, no `lru_cache`, no disk
cache — `load_capability_descriptor` re-reads from disk every call), no model-based
classification (pure keyword/heuristic string matching only).

Per this ticket's explicit instruction, the `docs/engine/contracts/knowledge_gateway_mcp_contract.md`
§2 update and the new `INFRA-*` parity ledger entry were deliberately NOT written here — both are
flagged in plan.md's "Docs and Parity Follow-Up" section for this ticket's own later
Document-Update and Parity phases.

## Test Summary
New file `tests/tools/test_knowledge_gateway_router.py` — 31 tests, all passing, covering:
identifier recognition (6 categories, real data from `tickets/done/`, `docs/parity_ledger/*.yaml`,
`tools/search_mcp.py`, `docs/REGISTRY.yaml`, `registries/layer_registry.jsonl`); the 7 routing-table
rows (driven by the real, versioned `kgmcp_baseline_corpus.CORPUS` query text, each asserted
against its documented `routing_shape`); the `requirement_completeness_verification` row's
`not_yet_routed="parity_ledger"` marker; capability-descriptor loading and the
fixture-change-flips-routing-decision proof; a cross-check against the existing test-local
`capability_allows()` stub (left unmodified); the sequential-bounded ambiguous-intent fallback
(mocked at the router's own provider-call seam, not real subprocess/model calls); and the
zero-MCP/zero-packet/zero-cache scope guards, including the existing anti-drift guard
`test_no_live_gateway_tool_code_or_mcp_registration_introduced` duplicated in the new file (kept
green).

Ran and confirmed passing:
```
pytest tests/tools/test_knowledge_gateway_router.py -v            # 31 passed
pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v  # 12 passed (unchanged, regression-clean)
pytest tests/tools/ -k "kgmcp or knowledge_gateway or router" -v  # 73 passed
```
`tests/tools/test_search_mcp.py` was run as part of the regression surface: 33/35 passed; the 2
pre-existing failures (`TestMcpJson::test_command_is_python3`,
`TestMcpJson::test_args_point_to_search_mcp`) are unrelated to this ticket — `.mcp.json` has no
diff in this session (confirmed via `git diff HEAD -- .mcp.json`, empty) and last changed in commit
`6e25d4f2`, well before this ticket; `.mcp.json`'s `knowledge-search` entry now launches via a
`bash` wrapper script (`tools/start_search_mcp.sh`) rather than `python3` directly, a drift that
predates and is orthogonal to this ticket's diff.

## Files Changed
- `tools/knowledge_gateway_router.py` (new)
- `tests/tools/test_knowledge_gateway_router.py` (new)
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (§2 stale "no router exists yet" claim
  corrected, Document-Update phase)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (§20 Phase 1's "Implement deterministic routing"
  bullet annotated Done, Document-Update phase)
- `docs/parity_ledger/infrastructure.yaml` (new `INFRA-335` entry, via `write_entry()`, Parity phase)

## Completion Summary
Built the standalone, directly-testable Knowledge Gateway MCP query router
(`tools/knowledge_gateway_router.py`) per `docs/plans/knowledge-gateway-mcp-proposal.md` §8: six
real stable-identifier matchers, the 7-row intent/provider routing table sharing
`kgmcp_baseline_corpus.ROUTING_SHAPES`'s vocabulary, capability-descriptor-aware routing
constraints that consult the two frozen `provider_capabilities_*.json` files fresh from disk on
every call, a sequential-bounded `{context_search, graphify}` ambiguous-intent fallback (Design
Decision D3), and a plain typed `RoutingDecision` output record with no MCP/JSON-RPC envelope
fields. All 6 non-negotiable scope guards (no `.mcp.json` edits, no
`knowledge_context`/`knowledge_status` tool definitions, no packet-assembler/retrieval-cache
imports, zero caching, zero model-based classification) were verified in the diff. 31 new tests
pass, plus the full pre-existing KGMCP/router-adjacent regression surface (73 tests) stays green.
The `test_ambiguous_intent_queries_bounded_provider_set_in_parallel` -> `test_ambiguous_intent_queries_bounded_provider_set`
rename mandated by Architecture Review was applied. Doc-update (§2 of the contract doc) and the
new `INFRA-*` parity ledger entry are intentionally deferred to this ticket's own
Document-Update/Parity phases, per plan.md.
