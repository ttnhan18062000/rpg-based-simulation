---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-FAILOPEN-TESTS
artifact_type: test_plan
tags: [ai, mcp, testing]
---

# Test Plan — TCK-20260815-KGMCP-P1-FAILOPEN-TESTS

## Regression Surface

Unit / component (must keep passing unmodified — all 3 dependency modules are frozen per their
own tickets' scope guards):
- `tests/tools/test_knowledge_gateway_router.py` (31 tests — INFRA-335)
- `tests/tools/test_knowledge_gateway_packet_assembly.py` (INFRA-336)
- `tests/tools/test_knowledge_gateway_mcp.py` (12 tests — INFRA-337), including the existing
  partial-failure test `test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing`
  this ticket's new suite must not duplicate or contradict.
- `tests/tools/test_knowledge_gateway_contract_schemas.py` (contract-schema tests, TCK-20260814-KGMCP-CONTRACT-SCHEMAS)
- `tests/tools/test_search_mcp.py` (search_mcp.py's own suite — `_run_search`/`_run_health` must
  keep their current error-dict-not-exception contract, which this ticket's tests depend on).

Integration:
- None currently exist that drive the real stdio `FastMCP` transport for either
  `search_mcp.py` or `knowledge_gateway_mcp.py` — this ticket's own end-to-end smoke test will be
  the first process-level (subprocess) test in this area. Confirm it does not collide with or
  slow down the `make mcp-server-test` Makefile target's own subprocess invocation pattern.

Arena-combat: not applicable — this ticket touches no simulation/combat code.

## New Tests Required

New file: `tests/tools/test_knowledge_gateway_failure_semantics.py` (new file — mirrors the
existing `tests/tools/test_knowledge_gateway_*.py` flat-file, `importlib.util`-loading convention).

Per §16's 5 Phase-1-applicable rows (final set pending Plan's resolution of the two Risk items in
investigation.md — tests below are written against the row text as given; Plan may need to adjust
Rows 4/5 to a documented-gap form rather than a positive-behavior-proof form):

1. **Gateway process unavailable → agent calls provider tools directly**
   - Test name: `test_gateway_down_search_mcp_test_mode_still_works`
   - Category: integration (subprocess-based, no mocks)
   - Verifies: `python3 tools/search_mcp.py --test` (via `subprocess.run`, mirroring the
     `mcp-server-test` Makefile target) returns exit code 0 and valid JSON for a real query,
     **without `tools/knowledge_gateway_mcp.py` ever being imported, started, or referenced in
     this test's process** — the gateway module is not merely "not running," it is absent from the
     test's own import graph, the strongest available proof of independence.
   - Location: `tests/tools/test_knowledge_gateway_failure_semantics.py`

   - Test name: `test_gateway_down_graphify_cli_still_works`
   - Category: integration (subprocess-based, no mocks)
   - Verifies: `subprocess.run(["graphify", "query", "<real known symbol>"], ...)` succeeds
     (returncode 0, non-empty stdout) independently, again with zero import of any
     `knowledge_gateway_*` module in this test's process.
   - Location: same file

   - Test name: `test_neither_provider_tool_imports_knowledge_gateway_mcp`
   - Category: architecture guard (static, AST or substring)
   - Verifies: `tools/search_mcp.py` source and the real `graphify` executable's own repo-tracked
     source (if in this repo) never reference `knowledge_gateway_mcp`/`knowledge_gateway_router`/
     `knowledge_gateway_packet_assembly` — the structural guarantee underlying tests 1-2 above.
   - Location: same file

2. **One provider unavailable → partial result with explicit provider failure**
   - Test name: `test_context_search_index_missing_yields_partial_status_via_real_mcp_call`
   - Category: unit (monkeypatch at the same boundary `test_knowledge_gateway_mcp.py`'s existing
     test already uses — `pa_search_mod._run_search`)
   - Verifies: calling `_mod._run_knowledge_context(...)` with `_run_search` forced to return
     `{"error": "index not found"}` yields `response["status"] == "PARTIAL"` (already proven by the
     existing MCP-tool-surface test) **and** — this is the new assertion this ticket adds — checks
     whether a machine-readable indication of *which* provider failed is present anywhere in the
     response. If Plan concludes (per investigation.md Risk 2) that no such field exists and is not
     being added, this test must assert the documented current gap explicitly (e.g.
     `assert "failures" not in response` with a comment citing the ticket that will need to close
     it) rather than silently passing or silently asserting success — never leave this ambiguous.
   - Location: same file

   - Test name: `test_graphify_subprocess_timeout_yields_partial_status`
   - Category: unit (monkeypatch `subprocess.run` at `router_mod.subprocess.run`, reusing
     `test_knowledge_gateway_router.py::test_symbol_name_delegates_to_graphify_cli_not_a_new_symbol_table`'s
     established monkeypatch point) to raise `subprocess.TimeoutExpired`
   - Verifies: a real end-to-end `_mod._run_knowledge_context(...)` call (routed to graphify) still
     returns a schema-valid response with `status == "PARTIAL"`, never an unhandled
     `TimeoutExpired` reaching the test.
   - Location: same file

   - Test name: `test_graphify_binary_missing_entirely_does_not_crash_the_tool_call`
   - Category: unit (monkeypatch `subprocess.run` to raise `FileNotFoundError`, simulating a
     genuinely-absent `graphify` binary — not covered by any existing test)
   - Verifies: **this is the test most likely to fail against current code** (per investigation.md
     Risk 2 — `FileNotFoundError` is not caught anywhere in the pipeline). If it fails, this proves
     the gap is real, not hypothetical, and Plan's resolution must address it (either accept-and-
     document via `intentional_divergences.md`, or fix). Do not weaken this test to pass
     vacuously — if it must monkeypatch around the gap to pass, that defeats its purpose.
   - Location: same file

   - Test name: `test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result`
   - Category: unit
   - Verifies: the semantic gap identified in investigation.md Risk 2 — a graphify call that
     completes with a non-zero returncode (simulating a real crash) is currently indistinguishable
     from `returncode=0, stdout=""` (a legitimate "found nothing"). Assert the packet/response
     produced in each case, and record explicitly (via assertion, not just a comment) whether they
     are currently identical. If Plan does not fix this, this test documents the honest current
     behavior rather than asserting a distinction that doesn't exist.
   - Location: same file

3. **"flag code-graph/docs result unavailable" is a real response field, not a silent omission**
   - Test name: `test_provider_unavailable_is_a_real_response_field_not_silent_omission`
   - Category: unit
   - Verifies: directly targets ticket AC #4's own wording. Forces a provider failure (reuse the
     context-search-missing-index fixture) and asserts a specific, named field exists in the
     response identifying the unavailable provider — **this test's pass/fail outcome is itself
     the honest answer to investigation.md's central open question**: if no such field exists in
     current code, this test fails, proving code changes are required before this row can be
     honestly marked proven; it must not be rewritten to check for `status == "PARTIAL"` alone,
     which would silently weaken the AC to something already covered by test 2 above.
   - Location: same file

4. **Graphify stale → use Context Search/Parity where applicable; flag code-graph result unavailable**
   - Test name: `test_graphify_stale_signal_row_documented_gap_or_real_behavior` (name/shape
     depends on Plan's resolution of investigation.md Risk 1)
   - Category: unit, OR an explicit "deferred" documentation entry if Plan concludes there is no
     real Phase-1 staleness mechanism to test
   - Verifies: **do not write this test until Plan has resolved Risk 1.** If Plan scopes in real
     staleness-detection code, this test exercises that real code path (monkeypatching the
     `provider_capabilities_graphify.json` generation/adapter_version field per the ticket's own
     Scope text) and asserts the required fallback behavior. If Plan concludes no real mechanism
     exists and none will be added under this ticket, this row must be moved into this ticket's own
     "explicitly deferred" documentation (mirroring the cache rows' treatment) rather than backed by
     a vacuous test — per this ticket's own AC #2's anti-pattern rule, which applies here with equal
     force even though the ticket's Scope text originally categorized this row as Phase-1-applicable.
   - Location: same file (or ticket-body "Assumptions/Open Questions"/"Implementation Notes" if
     deferred, not a test file)

5. **Context Search stale → use direct docs/tickets/source where appropriate**
   - Same disposition and same blocking dependency on Plan's Risk 1 resolution as row 4 above.
   - Location: same file, or deferred documentation, mirroring row 4's treatment exactly (both
     rows share the identical "no real mechanism exists yet" finding — do not resolve them
     differently without a stated reason).

6. **Token-budget assembly failure → smaller evidence list, never fabricated content**
   - Test name: `test_budget_assembly_failure_via_real_mcp_call_returns_smaller_list_not_fabricated`
   - Category: unit/integration (calls `_mod._run_knowledge_context(query, budget_tokens=1)`
     end-to-end through the real MCP tool function, with only the minimum monkeypatch needed to
     guarantee at least one real provider hit — e.g. force routing to `context_search` and a
     single real, fixed-content search result)
   - Verifies: `response["statements"] == []`, `response["budget_returned"] == 0`, `response["status"]
     in {"PARTIAL"}`, and `response["evidence"]` remains non-empty with each entry carrying a real
     `evidence_hash` — i.e. the response-schema-level equivalent of the existing packet-assembly
     unit tests (`test_budget_assembly_failure_returns_smaller_real_list_not_fabricated_content`),
     proven at the MCP tool boundary this ticket is specifically chartered to test, not just at
     the packet-assembly unit level.
   - Location: same file

7. **Structural (not hardcoded-placeholder-string) no-fabrication guard — AC #4, cross-cutting**
   - Test name: `test_every_response_statement_traces_to_a_real_evidence_id_across_all_failure_modes`
   - Category: architecture guard (structural)
   - Verifies: parametrized over every failure-injection scenario above that still produces
     non-empty `statements`/`evidence` (rows 2/3/6) — every `response["statements"][i]["evidence_ids"]`
     entry resolves to a real `response["evidence"][j]["evidence_id"]`, reusing the same structural
     principle as `test_knowledge_gateway_packet_assembly.py`'s
     `_assert_answer_traces_to_statement_evidence()` helper (adapted for the response-dict shape
     rather than the `PacketAssembly` dataclass shape). This is the AC #4-mandated guard against a
     test that only checks for a specific hardcoded placeholder string.
   - Location: same file

8. **Phase-2-deferred rows — explicit non-test documentation, per AC #2**
   - No test named for "Cache missing or corrupt" or "Cached evidence mismatch." Instead: a
     dedicated section in this file's own suite module docstring (or a top-of-file comment block)
     stating both rows by name, citing that `tools/knowledge_gateway_packet_assembly.py` has no
     cache read/write path at all (verified in investigation.md — `assert "retrieval_cache" not in
     source` already exists as a guard test in `test_knowledge_gateway_packet_assembly.py`), and
     that no test in this file simulates either row. This satisfies AC #2's "zero vacuous tests"
     requirement by construction — there being no test is the honest answer, documented, not a
     test asserting something trivially true.

## Scoped Pytest Commands

```
pytest tests/tools/test_knowledge_gateway_failure_semantics.py -v
pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_knowledge_gateway_router.py tests/tools/test_knowledge_gateway_packet_assembly.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_search_mcp.py -v
```

Never `pytest tests/` — scope stays within `tests/tools/` for this ticket's whole regression
surface (Knowledge Gateway MCP + its direct provider dependencies only; no `src/` code is touched).

## Anti-Drift Test Guards

- A test asserting `"failures" not in response` (documenting the current gap, per test 2 above)
  must never be silently deleted/inverted to make a later, unrelated change look like it "fixed"
  this ticket's central finding — any change to that assertion's polarity must be a real code
  change to `knowledge_gateway_mcp.py`/`knowledge_gateway_packet_assembly.py`, ledgered, and
  cross-referenced from this test's own docstring.
- `test_neither_provider_tool_imports_knowledge_gateway_mcp` guards against a future edit to
  `search_mcp.py` accidentally adding a dependency on the gateway module, which would silently
  break the "gateway is never a correctness dependency" guarantee this whole ticket exists to
  prove.
- `test_graphify_binary_missing_entirely_does_not_crash_the_tool_call` and
  `test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result` must not be
  monkeypatched into passing by adding a try/except *inside the test* around the call — any fix
  belongs in production code (`knowledge_gateway_router.py`'s `match_symbol_name()` or
  `knowledge_gateway_packet_assembly.py`'s `call_providers_for_routing_decision()`), not in test
  scaffolding that hides the real exception from the assertion.
- Row 4/5 tests (Graphify/Context-Search stale) must not be retro-fitted to "pass" by asserting a
  behavior that was invented solely to satisfy the test — cross-check any new staleness code
  against `docs/plans/knowledge-gateway-mcp-proposal.md` §16's exact required-behavior text before
  writing the assertion, not after.
- Reuse, do not duplicate, `test_knowledge_gateway_mcp.py`'s existing
  `test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing` and
  `test_knowledge_gateway_packet_assembly.py`'s budget-failure tests — if this ticket's new suite
  re-implements the same scenario with a different assertion, prefer strengthening the existing
  test in place (if its own ticket's scope allows) over adding a near-duplicate in the new file.
