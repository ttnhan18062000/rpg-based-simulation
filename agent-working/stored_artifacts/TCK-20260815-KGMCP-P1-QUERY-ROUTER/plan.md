---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-QUERY-ROUTER
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260815-KGMCP-P1-QUERY-ROUTER

## Summary

Build a single new flat module, `tools/knowledge_gateway_router.py`, that implements §8's
deterministic query router as a standalone, directly-testable component: six stable-identifier
matchers, a 7-row intent/provider routing table reusing the existing `ROUTING_SHAPES` vocabulary,
a real `capability_allows`-shaped function that loads and consults the two frozen
`provider_capabilities_*.json` descriptors, a sequential-bounded ambiguous-intent fallback, and a
plain typed `RoutingDecision` output record. No MCP server code, no packet assembly, no caching —
this ticket produces pure decision logic that later tickets (`MCP-TOOL-SURFACE`,
`PACKET-ASSEMBLY`) will import and call. Module layout, parity-ID matching strategy, source-path
semantics, and fallback concurrency mechanism are explicit Design Decisions below, each grounded
in re-verified evidence from this repo (schema/instance files, `ROUTING_SHAPES`, the `graphify`
CLI call shape, and the real parity-ID prefix set), not inherited unverified from Investigate.

## Module Layout Decision

`tools/knowledge_gateway_router.py` — single flat file, not a `tools/knowledge_gateway/` package.

Rationale: `tools/search_mcp.py` (verified directly at `tools/search_mcp.py:1-45`) is the only
existing module-layout precedent under `tools/` — flat file, `importlib.util.spec_from_file_location`
sibling-loading (`tools/search_mcp.py:27-42`), no `__init__.py`-based subpackage anywhere in
`tools/` today. A package with exactly one module today is premature structure per this repo's own
"do not create hidden or implicit durable behavior" bias toward minimalism. The two known future
importers — `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE` and `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY` —
can import `tools/knowledge_gateway_router.py` via the same `importlib.util` sibling-load pattern
`tools/search_mcp.py` already uses, or (since both are plain `tools/*.py` files with no `__init__.py`
involved) via a `sys.path`-relative `import knowledge_gateway_router` if invoked from `tools/`
itself — either path is trivial regardless of file vs. package. If Phase 2+ genuinely grows this
into multiple router-adjacent modules, a future ticket can promote it to a package then; this
ticket must not pre-build that structure now (YAGNI).

Test file: `tests/tools/test_knowledge_gateway_router.py` (flat, mirrors `tests/tools/test_search_mcp.py`'s
own flat-file precedent 1:1).

## Steps

### Step 1 — Capability descriptor loader

**Files:** `tools/knowledge_gateway_router.py` (new)

**Change:** Add `load_capability_descriptor(path: Path) -> dict` that reads and `json.loads()`s a
`provider_capabilities_*.json` file, and `_CONTEXT_SEARCH_CAPS_PATH` / `_GRAPHIFY_CAPS_PATH`
constants pointing at
`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json` and
`provider_capabilities_graphify.json` respectively (both files verified to exist and to contain
exactly the 12 required fields — `provider_id`, `adapter_version`, `stable_entity_ids`,
`evidence_granularities`, `fine_grained_fingerprints`, `incremental_refresh`,
`deterministic_relationships`, `historical_queries`, `negative_knowledge_support`, `cancellation`,
`timeout`, `branch_awareness` — read directly from the files during this Plan phase: schema at
`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities.schema.json`, both instances
confirmed to validate against it with `context_search` = `{stable_entity_ids: PARTIAL,
deterministic_relationships: NONE, negative_knowledge_support: NONE, cancellation: false, timeout:
false, branch_awareness: NONE}` and `graphify` = `{stable_entity_ids: PARTIAL,
deterministic_relationships: PARTIAL, negative_knowledge_support: NONE, cancellation: false,
timeout: false, branch_awareness: NONE}`). Load at call time from disk (not module-level constant
dicts), so a monkeypatched/temp-copy fixture file is actually read — this is required for the
acceptance-criterion test `test_capability_change_flips_routing_decision`, which proves a fixture
edit changes router output. Do not validate against the JSON Schema at runtime with a schema
validator library (no `jsonschema` dependency currently used anywhere in `tools/` per
`tools/search_mcp.py`'s own import list — do not introduce a new dependency for this); this
ticket's own test `test_router_loads_real_capability_descriptors_from_disk` performs the
membership/enum checks directly in the test rather than the router importing a schema-validation
library.

**Do NOT touch:** `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities*.json` files
themselves (frozen contract files from a prior ticket) — read-only inputs.

**Verify:** `test_router_loads_real_capability_descriptors_from_disk`.

### Step 2 — Six stable-identifier matchers

**Files:** `tools/knowledge_gateway_router.py`

**Change:** Add one pure function per category, each returning a matched-identifier record (or
`None`):

1. `match_ticket_id(text: str) -> str | None` — regex `^TCK-\d{8}-[A-Z0-9-]+$` (matches this
   ticket's own ID shape, confirmed against `tickets/inprogress/TCK-20260815-KGMCP-P1-QUERY-ROUTER.md`'s
   filename and frontmatter `ticket_id` field). Legacy pre-convention names
   (`tickets/done/adjust-01-action-speed-balance.md`-shaped) correctly fail this pattern — expected,
   per ticket scope's "current convention only."
2. `match_parity_id(text: str) -> str | None` — shape-only regex `^[A-Z]+(-[A-Z]+)*-\d+$`. See
   Design Decision D1 below for why shape-only (not full-membership) was chosen, re-verified
   directly this session: `grep`-extracted prefixes across all `docs/parity_ledger/*.yaml` id fields
   confirm real prefixes `COMB, FAC, FACTION-DIR, FACTION-TENSION, INFRA, INFRA-PACK, INFRA-TYPE,
   PROG, SIMQ-CALIBRATED, SOC, SOC-ABAND-TYPE, SOC-CHRON, SOC-CROSS-EP, SOC-FAC, STRAT, SUB,
   SUBSTRATE-NEW, TOWN, WORLD, WORLD-CULT, WORLD-DEMO` — all conform to the shape regex; a
   hardcoded enum would need updating on every new shard prefix.
3. `match_source_path(text: str) -> str | None` — `pathlib.Path` existence check plus a traversal
   guard using `Path(repo_root / text).resolve().is_relative_to(repo_root.resolve())` (Python
   3.9+ `is_relative_to`; confirm repo's minimum Python version supports it — `tools/search_mcp.py`
   uses `from __future__ import annotations`, a 3.7+-compatible file, but does not itself prove a
   3.9 floor; if the implementer's `python3 --version` in this repo's venv is `< 3.9`, fall back to
   `os.path.commonpath` for the same check). No shell, no subprocess for this matcher — pure
   `pathlib`.
4. `match_symbol_name(text: str) -> dict` — does NOT do local detection; always delegates to
   `subprocess.run(["graphify", "query", text], cwd=str(_REPO_ROOT), capture_output=True, text=True,
   timeout=120)`, the exact list-args call shape verified directly at
   `tools/agent-monitoring/kgmcp_baseline_runner.py:92-114`'s `_run_graphify`. `timeout=120` is
   documented in a docstring as the *caller's* process-level safeguard, not a provider guarantee
   (both descriptors declare `"timeout": false`, confirmed in Step 1's cited JSON contents). No new
   symbol table is built.
5. `match_registered_doc_path(text: str) -> str | None` — loads `docs/REGISTRY.yaml` (confirmed
   structure at `docs/REGISTRY.yaml:1-20`: top-level list of mappings, each with `type: doc` and a
   `path:` field, e.g. `path: docs/core/README.md`) via `yaml.safe_load`, and checks `text` against
   the set of `path` values for entries where `type == "doc"`.
6. `match_subsystem_id(text: str) -> str | None` — loads `registries/layer_registry.jsonl`
   (confirmed structure at `registries/layer_registry.jsonl:1-5`: one JSON object per line, keys
   `added_date`, `layer`, `note` — no separate `id` key, `layer` itself is the identifier) and
   checks `text` against the set of `layer` values.

**Do NOT touch:** `docs/REGISTRY.yaml`, `registries/layer_registry.jsonl`, `docs/parity_ledger/*.yaml`
— read-only inputs, never write to any of these from the router.

**Verify:** `test_recognizes_real_ticket_id_from_tickets_done`,
`test_recognizes_real_parity_id_across_multiple_shard_prefixes`,
`test_recognizes_real_source_path_and_rejects_traversal`,
`test_symbol_name_delegates_to_graphify_cli_not_a_new_symbol_table`,
`test_recognizes_real_registered_document_path_from_registry`,
`test_recognizes_real_subsystem_layer_id_from_layer_registry`.

### Step 3 — 7-row routing table

**Files:** `tools/knowledge_gateway_router.py`

**Change:** Add `ROUTING_TABLE: dict[str, RoutingTableRow]` keyed by the exact 7 string IDs
imported from `tools/agent-monitoring/kgmcp_baseline_corpus.py::ROTING_SHAPES` — import that
frozenset directly (via the same `importlib.util` sibling-load pattern used by `tools/search_mcp.py`,
since `tools/agent-monitoring/` has no `__init__.py` either) rather than re-typing the 7 strings, so
a future rename of `ROUTING_SHAPES` cannot silently desync from the router. Each row maps to:

| shape ID (from `ROUTING_SHAPES`) | primary | optional |
|---|---|---|
| `definition_terminology_architecture` | context_search | registry, graphify |
| `symbol_lookup_callers_references` | graphify | context_search |
| `requirement_completeness_verification` | context_search (Phase-1 fallback) + `not_yet_routed: "parity_ledger"` marker | — |
| `ticket_historical_rationale` | context_search (ticket index) | working_log, registry |
| `test_impact_of_change` | graphify (code/test index) | — |
| `ticket_work_status` | ticket index (context_search over `tickets/`) | working_log |
| `broad_task_context` | multiple providers (context_search + graphify) | — |

Add `test_router_shape_ids_match_baseline_corpus_routing_shapes` (per test_plan.md) asserting
`set(ROUTING_TABLE.keys()) == ROUTING_SHAPES`.

The `requirement_completeness_verification` row's output record must carry an explicit typed field
(e.g. `not_yet_routed: str | None`, set to `"parity_ledger"` for this row only) — not a free-text
note buried in a rationale string, consistent with this repo's "do not store durable meaning in
`reason` strings" architecture rule. Since this router's output is a transient decision record (not
durable world/entity state), a typed dataclass field is sufficient; it does not need registry
storage.

**Do NOT touch:** `tools/agent-monitoring/kgmcp_baseline_corpus.py` — read-only import source; do not
edit `ROUTING_SHAPES` or `CORPUS` from this ticket.

**Verify:** the 7 per-row tests (`test_routes_definition_terminology_architecture_to_context_search`
through `test_routes_broad_task_context_to_multiple_providers`) and
`test_router_shape_ids_match_baseline_corpus_routing_shapes`.

### Step 4 — Capability-aware routing-consequence logic

**Files:** `tools/knowledge_gateway_router.py`

**Change:** Add the real `capability_allows(descriptor: dict, capability_name: str) -> bool`
function — same signature and semantics as the test-local stand-in at
`tests/tools/test_knowledge_gateway_contract_schemas.py:287-293` (`return bool(descriptor[capability_name])`).
This is the one function this repo's own `capability_allows()` docstring (line 288: "Test-only
contract helper — not tools/ code, since no router exists yet to own it") explicitly anticipates
being replaced by real router code. **Other writer/reader of this same logic:**
`tests/tools/test_knowledge_gateway_contract_schemas.py::test_capability_allows_rejects_unadvertised_cancellation_and_timeout`
(lines 296-300) currently calls its own local copy, not this new one — this step does NOT modify
that test file (out of scope for this ticket's diff; the investigation flagged retiring the local
copy as an open decision, resolved here as: leave the existing test's local copy in place
unmodified for this ticket, since importing across `tests/tools/` -> `tools/` in that older test
file is a separate, non-blocking cleanup and touching that test file risks widening this ticket's
diff into contract-schema-ticket territory it doesn't own). Add a new, additional
`test_router_never_claims_unadvertised_capability` in the new router test file that imports the
*real* function and asserts it agrees with the existing test's semantics on both real fixtures —
this is the explicit cross-check requested by the ticket, without editing the existing test.

Beyond the boolean `capability_allows`, add `apply_capability_constraints(row: RoutingTableRow,
requested_guarantee: str | None) -> CapabilityConstraint` implementing §8.1's routing-consequence
examples: for the `symbol_lookup_callers_references` row, since Graphify's own
`deterministic_relationships` is `"PARTIAL"` (confirmed in Step 1) and Context Search's is `"NONE"`,
a request that specifically needs a `FULL` deterministic-relationship guarantee gets a
`CapabilityConstraint(satisfied=False, reason="neither provider advertises FULL
deterministic_relationships")` rather than a silent successful-looking route. This is the function
`test_capability_change_flips_routing_decision` monkeypatches
`provider_capabilities_context_search.json`'s `deterministic_relationships` from `"NONE"` to
`"FULL"` against, to prove the constraint flips to `satisfied=True` when the descriptor changes —
this is the literal fixture-to-decision proof the ticket's acceptance criteria require.

**Do NOT touch:** `tests/tools/test_knowledge_gateway_contract_schemas.py` — this ticket adds a new
router test file, it does not modify the existing contract-schema test file at all.

**Verify:** `test_router_never_claims_unadvertised_capability`,
`test_capability_change_flips_routing_decision`,
`test_negative_knowledge_support_none_does_not_assert_absence`.

### Step 5 — Sequential-bounded ambiguous-intent fallback

**Files:** `tools/knowledge_gateway_router.py`

**Change:** Add `route_ambiguous(query_text: str) -> RoutingDecision` that calls exactly the two
known providers — Context Search (via the same in-process call `tools/search_mcp.py` uses
internally, or a thin wrapper reusing `_run_context_search`'s shape from
`tools/agent-monitoring/kgmcp_baseline_runner.py`) and Graphify (via the `subprocess.run` shape from
Step 2's `match_symbol_name`) — **sequentially, one after another**, not via
`concurrent.futures.ThreadPoolExecutor` or any other concurrency primitive. See Design Decision D3
below for why "parallel" in the ticket's prose is satisfied by sequential-but-bounded for Phase 1.
The returned `RoutingDecision.providers_consulted` field lists both provider IDs actually called
(`["context_search", "graphify"]`), proving the set is bounded (exactly 2, not unbounded fan-out)
and reported, per the acceptance criterion. **Other callers of these two providers this step must
not collide with:** `tools/agent-monitoring/kgmcp_baseline_runner.py::run_corpus` (lines 117-145)
also calls both providers sequentially per corpus entry, but that is a separate one-time
measurement script, not a shared resource this router writes to or reads from — no ordering,
race, or double-counting risk since the two code paths share no file, counter, or log target (the
router returns an in-memory `RoutingDecision`; the baseline runner writes its own separate results
file). No other `tools/` code currently calls either provider concurrently.

**Do NOT touch:** `tools/agent-monitoring/kgmcp_baseline_runner.py` — read as a call-shape
precedent only, never imported or modified.

**Verify:** `test_ambiguous_intent_queries_bounded_provider_set_in_parallel` (the test's name says
"parallel" per the existing test_plan.md wording, but per Design Decision D3 the test itself should
assert boundedness — exactly `{"context_search", "graphify"}` — and reporting, not actual
thread-level concurrency; if the test file as drafted asserts real parallelism via timing, the
implementer must flag this to the orchestrator rather than fabricate concurrency to pass it — see
Anti-Drift Notes), `test_ambiguous_intent_does_not_silently_pick_one_provider`.

### Step 6 — Plain typed `RoutingDecision` output record

**Files:** `tools/knowledge_gateway_router.py`

**Change:** Add a `@dataclass RoutingDecision` (or `NamedTuple`) with fields: `providers_selected:
list[str]`, `matched_identifier: IdentifierMatch | None`, `routing_shape: str | None`,
`rationale: str`, `capability_constraints: list[CapabilityConstraint]`, `not_yet_routed: str |
None`, `providers_consulted: list[str]`. Explicitly no `jsonrpc`, `id`, or `method` fields — this is
not a JSON-RPC/MCP envelope. Add the top-level `route(query_text: str) -> RoutingDecision`
dispatcher that: (1) tries each of the 6 identifier matchers from Step 2 in a fixed order (ticket_id
→ parity_id → source_path → registered_doc_path → subsystem_id → symbol_name, since symbol_name is
the most expensive/subprocess-bound check and should run last), (2) on no identifier match,
classifies into one of the 7 routing-shape rows from Step 3 using simple keyword/heuristic matching
(NOT model-based — deterministic-only per ticket Out of Scope), (3) on no confident shape match,
falls through to Step 5's `route_ambiguous`. Applies Step 4's capability constraints to whichever
row/provider was selected before returning.

**Do NOT touch:** No MCP registration, no `def knowledge_context(`/`def knowledge_status(` names
anywhere in this file or any other top-level `tools/*.py` file (verified guard:
`tests/tools/test_knowledge_gateway_contract_schemas.py:338-349`,
`test_no_live_gateway_tool_code_or_mcp_registration_introduced`, which globs `tools/*.py`
non-recursively — since this ticket puts the router at `tools/knowledge_gateway_router.py`
directly under `tools/`, it IS scanned by this glob, so the forbidden-name constraint applies
literally, not just in spirit). No `.mcp.json` edits.

**Verify:** `test_router_output_is_plain_typed_record_not_mcp_envelope`,
`test_router_module_introduces_zero_mcp_zero_packet_zero_cache_code`,
`test_no_live_gateway_tool_code_or_mcp_registration_introduced` (existing, must stay green).

## Scope Guards

- No MCP server code: no `.mcp.json` edits, no `def knowledge_context(`, no `def knowledge_status(`
  anywhere in `tools/*.py`.
- No packet/statement/evidence assembly: do not import, reference, or extend
  `tools/context_packet_assembler.py`.
- No caching: do not import, reference, or extend `tools/retrieval_cache.py`; no
  routing-decision memoization of any kind (module-level cache dict, `functools.lru_cache` on
  `route()`, disk cache) — this ticket's router recomputes every call.
- No real Parity Ledger adapter: the `requirement_completeness_verification` row routes to Context
  Search with an explicit `not_yet_routed="parity_ledger"` marker; never silently drop the marker
  and never build a real ledger query path (that is Phase 4).
- No model-based intent classification: shape classification in Step 6 is deterministic
  keyword/heuristic logic only, no LLM call, no embedding similarity model.
- Do not modify `tests/tools/test_knowledge_gateway_contract_schemas.py` (existing test file) — add
  a new, separate `tests/tools/test_knowledge_gateway_router.py` instead.
- Do not modify `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities*.json` or
  `.schema.json` — frozen contract inputs, read-only.
- Do not modify `docs/REGISTRY.yaml`, `registries/layer_registry.jsonl`, `docs/parity_ledger/*.yaml`
  — read-only identifier-recognition sources.
- Do not modify `tools/agent-monitoring/kgmcp_baseline_corpus.py` or `kgmcp_baseline_runner.py` —
  import `ROUTING_SHAPES` read-only; do not alter the baseline corpus/runner.
- No `shell=True`, no string-interpolated subprocess calls anywhere in the symbol-name path — list-
  form `subprocess.run(["graphify", "query", query_text], ...)` only.

## Dependency Map

Steps 1-5 are independent of each other and can be implemented/tested in any order (each is a
self-contained function or function group with its own test). Step 6 depends on Steps 1-5 being
present, since `route()` composes the identifier matchers (Step 2), routing table (Step 3),
capability logic (Step 4), and ambiguous fallback (Step 5) into one dispatcher, and
`RoutingDecision` (Step 6) is the return type Steps 3-5 already construct instances of — so
implement Steps 1-5 first, Step 6 last as the integration step.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| All 6 stable-identifier categories recognized with real, tested pattern/lookup logic | Step 2 | `test_recognizes_real_ticket_id_from_tickets_done`, `test_recognizes_real_parity_id_across_multiple_shard_prefixes`, `test_recognizes_real_source_path_and_rejects_traversal`, `test_symbol_name_delegates_to_graphify_cli_not_a_new_symbol_table`, `test_recognizes_real_registered_document_path_from_registry`, `test_recognizes_real_subsystem_layer_id_from_layer_registry` |
| §8 routing table's 7 intent shapes each have a real router decision path, incl. Phase-1 fallback + not-yet-routed marker for Parity-Ledger row | Step 3 | 7 per-row tests + `test_router_shape_ids_match_baseline_corpus_routing_shapes` + `test_routes_requirement_completeness_to_context_search_with_not_yet_routed_marker` |
| Router decisions demonstrably consult real frozen `provider_capabilities_*.json` files (loaded from disk, not hardcoded); fixture change flips a routing decision | Step 1, Step 4 | `test_router_loads_real_capability_descriptors_from_disk`, `test_capability_change_flips_routing_decision` |
| Ambiguous-intent fallback queries a bounded (not unbounded) provider set and reports which were used | Step 5 | `test_ambiguous_intent_queries_bounded_provider_set_in_parallel`, `test_ambiguous_intent_does_not_silently_pick_one_provider` |
| Zero MCP server code, zero packet-assembly code, zero cache code in this ticket's diff | Step 6 (guard), all steps (scope) | `test_no_live_gateway_tool_code_or_mcp_registration_introduced`, `test_router_module_introduces_zero_mcp_zero_packet_zero_cache_code`, `test_router_output_is_plain_typed_record_not_mcp_envelope` |

## Design Decisions

**D1 — Parity-ID matching: shape-only regex, not full-membership.** Re-verified directly this
session (not merely trusting Investigate's claim): extracting the id prefix from every entry across
all `docs/parity_ledger/*.yaml` shards yields 20+ distinct prefixes (`COMB`, `FAC`, `FACTION-DIR`,
`FACTION-TENSION`, `INFRA`, `INFRA-PACK`, `INFRA-TYPE`, `PROG`, `SIMQ-CALIBRATED`, `SOC`,
`SOC-ABAND-TYPE`, `SOC-CHRON`, `SOC-CROSS-EP`, `SOC-FAC`, `STRAT`, `SUB`, `SUBSTRATE-NEW`, `TOWN`,
`WORLD`, `WORLD-CULT`, `WORLD-DEMO`), all conforming to `^[A-Z]+(-[A-Z]+)*-\d+$`. Full-membership
matching would require loading and indexing all 2017 IDs from 9 YAML files at router call time (or
caching that index — which is explicitly out of scope: "no caching"), making membership-checking
either slow-per-call or scope-creeping into Phase 2+ cache territory. Shape-only is the correct
Phase-1 choice: it accepts false positives on unrelated hyphenated-uppercase strings (e.g.
`ZZZZ-9999`), which the router should classify as `parity_id`-shaped but let the downstream
Context Search/Parity Ledger consumer report "not found" rather than the router pre-verifying
existence. `test_recognizes_real_parity_id_across_multiple_shard_prefixes`'s nonexistent-ID case
(`ZZZZ-9999`) must assert it IS classified as `parity_id`-shaped (matches the regex) but the router
attaches no existence guarantee — this is the concrete behavior the test must encode.

**D2 — Source-path check: working-tree existence only, no branch-awareness.** Both provider
capability descriptors declare `branch_awareness: "NONE"` (confirmed directly in Step 1's JSON
reads), and this ticket's Out of Scope has no branch/working-tree cache identity concept. A plain
`Path.exists()` (with the traversal guard from Step 2 item 3) against the current working tree is
the correct and only sensible Phase-1 semantics — checking against `git HEAD` or any other ref
would require shelling out to `git` for every path check, a new dependency this ticket does not
need and the ticket scope does not request.

**D3 — Ambiguous-intent fallback: sequential, not literally parallel.** No concurrency precedent
exists anywhere in `tools/` — the only existing multi-provider caller,
`kgmcp_baseline_runner.py::run_corpus` (verified at lines 117-145), calls Context Search then
Graphify sequentially in a plain `for` loop, no `ThreadPoolExecutor` or `asyncio` anywhere in that
file or `tools/search_mcp.py`. Introducing thread-level concurrency for this ticket would add a new
concurrency-safety surface (shared-state races, exception handling across threads, timeout
interaction with `subprocess.run`) that the ticket's own scope (a standalone, directly-testable
router with no MCP/caching complexity) does not ask for and Phase 1 does not need for correctness.
The ticket's acceptance criterion is "query a small bounded provider set... and reports which
providers were used" — a sequential call to exactly `{context_search, graphify}` that reports both
in `providers_consulted` satisfies "bounded" and "reports which were used" in full; true parallelism
is a latency optimization for a later phase, not a Phase 1 correctness requirement. If a stricter
reading of the ticket's "in parallel" wording is later judged non-negotiable at Review, that is a
scope clarification for the orchestrator to resolve before Verify — this plan's chosen
interpretation is the more conservative, lower-risk one, consistent with the repo's "do not create
hidden or implicit durable behavior" and general minimal-surface bias.

## Docs and Parity Follow-Up (not this plan's work)

- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` §2 (around line 61-63) currently states
  `capability_allows()` is "test-only... no router exists yet to own it." Once this ticket's Step 4
  lands the real `tools/knowledge_gateway_router.py::capability_allows`, that sentence becomes
  stale and must be updated to point at the real implementation's file:line. Flagged for the
  Document-Update phase — not edited by this plan or its implementer.
- A new `INFRA-*` entry in `docs/parity_ledger/infrastructure.yaml` will likely be needed once this
  ticket's real code lands, following the `INFRA-334` precedent (`infrastructure.yaml:8598-8613`,
  `status: verified`, `v2_evidence` citing file:line, `test_path` citing the scoped pytest command).
  Flagged for this ticket's own Parity phase to write — not written by this plan.

## Anti-Drift Notes

- The existing anti-drift guard test `test_no_live_gateway_tool_code_or_mcp_registration_introduced`
  globs `tools/*.py` **non-recursively**. Because Step 1's Module Layout Decision places the router
  directly at `tools/knowledge_gateway_router.py` (not in a subpackage), this test scans it
  automatically — good, no test update needed. Do not later move the router into a
  `tools/knowledge_gateway/` subpackage without separately confirming this guard (or a new
  recursive one) still covers it; that would silently weaken the anti-drift guard.
- Both provider descriptors have `cancellation: false` and `timeout: false` — every subprocess call
  to `graphify` and every call path to Context Search must treat `timeout=120` (or any timeout
  value used) as a caller-side safeguard only, never surfaced in `RoutingDecision.rationale` as if
  the provider itself guaranteed cancellation/timeout behavior.
- Both descriptors have `negative_knowledge_support: "NONE"` — an empty result from either provider
  must never be treated by the router as a verified-absence signal; `apply_capability_constraints`
  (Step 4) must not synthesize a "confirmed not present" conclusion from an empty result set.
- `stable_entity_ids` is `"PARTIAL"` for both providers, never `"FULL"` — do not write router logic
  that assumes IDs are stable across a `graphify update`/reindex; this matters if a future step
  is tempted to cache a symbol-to-provider mapping keyed by an ID (which caching is out of scope for
  this ticket anyway).
- Do not retire or edit the existing test-local `capability_allows()` in
  `tests/tools/test_knowledge_gateway_contract_schemas.py:287-293` — Step 4 explicitly leaves it in
  place and adds a new cross-check test instead, to keep this ticket's diff from touching a file it
  does not own.
- If, during implementation, the drafted `test_ambiguous_intent_queries_bounded_provider_set_in_parallel`
  test asserts actual thread-level concurrency (e.g. via timing assertions) rather than boundedness/
  reporting, the implementer must not silently rewrite router internals to fake concurrency just to
  pass that assertion — surface the mismatch against Design Decision D3 to the orchestrator instead
  of routing around it.

## Deviations (recorded during Implement)

- **Test rename (Review-mandated, not a plan deviation):**
  `test_ambiguous_intent_queries_bounded_provider_set_in_parallel` was implemented as
  `test_ambiguous_intent_queries_bounded_provider_set` (dropped `_in_parallel`), per an explicit
  Architecture Review ruling relayed to the implementer: the test's real assertions (bounded
  `{context_search, graphify}` set, `providers_consulted` reporting) never required actual
  concurrency, and the ticket's formal Acceptance Criteria never says "in parallel." No
  concurrency was faked; `route_ambiguous` remains the sequential-bounded implementation this
  plan's Design Decision D3 specifies.
- **`route()` dispatcher's `symbol_name` gating (implementation detail the plan left implicit):**
  Step 6 specifies the fixed identifier-matcher order ends with `symbol_name` "since it is the
  most expensive/subprocess-bound check," but does not specify what triggers the dispatcher to
  attempt it. Implemented as: the dispatcher only calls `match_symbol_name` (and therefore only
  shells out to `graphify`) when the *entire* query text is single-identifier-shaped (no
  whitespace, `^[A-Za-z_][A-Za-z0-9_]*$`) — a full natural-language sentence is never a bare
  "symbol name" on its own and instead reaches Step 6's shape classification. `match_symbol_name`
  itself is unaffected and still "always delegates" once called, per its own contract in Step 2 —
  this gating lives only in the dispatcher that decides whether to call it.
