---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE

## Regression Surface

Existing tests that must keep passing (none of this ticket's files may cause a regression in these):

**Unit**
- `tests/tools/test_knowledge_gateway_router.py` — full suite (router is frozen; new code only
  imports it). Run to confirm zero import-order/monkeypatch collisions with the new module.
- `tests/tools/test_knowledge_gateway_packet_assembly.py` — full suite (packet assembler is frozen).
- `tests/tools/test_knowledge_gateway_contract_schemas.py` — full suite; in particular
  `test_no_live_gateway_tool_code_or_mcp_registration_introduced` (`:338-351`) currently asserts
  `.mcp.json`'s `mcpServers` keys are exactly `{"knowledge-search", "github"}` and that no
  `tools/*.py` file defines `def knowledge_context(` / `def knowledge_status(`. **This test will
  necessarily start failing once this ticket lands its real tool** — that is expected and correct
  (Phase 0's "no live gateway code yet" guarantee is meant to expire once Phase 1 lands it), but
  it must be updated in the same change, not left broken. Flag this explicitly in Implementation
  Notes when Plan/Implement touches it.
- `tests/tools/test_retrieval_events.py` (if it exists — confirm path at Plan time) — the 3 Wrapper
  functions' own unit tests must keep passing unmodified. Per Design Decision D1 (confirmed at
  Review, twice), this ticket does not call any of the 3 wrappers and does not add a new one —
  `tools/retrieval_events.py` remains completely untouched, verified by test 7's own zero-diff
  assertion. This file gains no new tests and loses none.

**Integration**
- `tests/tools/test_search_mcp.py` — full suite, **except** the 2 pre-existing failures already
  documented in investigation.md Risk #5 (`TestMcpJson::test_command_is_python3`,
  `TestMcpJson::test_args_point_to_search_mcp`), which are out-of-scope pre-existing regressions.
  Run this suite to prove `tools/search_mcp.py` itself is untouched and its own test results are
  bit-for-bit identical before/after (same 2 pre-existing failures, same pass count otherwise —
  no new failures and no accidental fixes bundled in).

**Architecture guard**
- Any existing "module introduces zero MCP server code" / "does not modify X" guard tests in the
  router/packet-assembly test files (`test_router_module_introduces_zero_mcp_zero_packet_zero_cache_code`,
  `test_module_introduces_zero_mcp_server_code`, `test_module_does_not_edit_knowledge_gateway_router`)
  — these must stay true of the frozen files themselves; this ticket's new module is exempt from
  them (it's expected to add MCP server code) but must not cause those frozen files to fail their
  own self-checks.

## New Tests Required

New test file: `tests/tools/test_knowledge_gateway_mcp.py` (module path TBD by Plan — mirrors
`tools/knowledge_gateway_mcp.py` or whatever filename Plan settles on).

1. **`test_knowledge_context_tool_real_invocation_validates_against_response_schema`**
   Category: integration.
   Verifies: calling the registered `knowledge_context` tool function directly (not just importing
   the module — call the underlying Python callable the `@server.tool()` decorator wraps, same
   pattern as `tests/tools/test_search_mcp.py`'s direct `_mod._run_search(...)` calls) with a real
   query against a real or realistically-faked index, then validates the returned dict against
   `knowledge_context_response.schema.json` using `jsonschema.Draft7Validator` +
   `jsonschema.RefResolver` (base_uri = the contracts dir), asserting zero validation errors. This
   is AC #1's first half.
   Location: `tests/tools/test_knowledge_gateway_mcp.py`.

2. **`test_knowledge_status_tool_real_invocation_validates_against_response_schema`**
   Category: integration.
   Verifies: calling the registered `knowledge_status` tool function directly, validating the
   returned dict against `knowledge_status_response.schema.json` with the same real
   `jsonschema.Draft7Validator` pattern (note: this schema has no cross-file `$ref`s, so no resolver
   base_uri is strictly needed, but reuse the same helper as test #1 for consistency). AC #1's
   second half.
   Location: `tests/tools/test_knowledge_gateway_mcp.py`.

3. **`test_knowledge_context_rejects_forbidden_request_field`**
   Category: unit.
   Verifies: a request dict containing an extra/forbidden field (e.g.
   `{"query": "x", "provider_weights": {...}}` or any field from
   `test_knowledge_gateway_contract_schemas.py`'s `_FORBIDDEN_REQUEST_FIELDS` set) is rejected before
   reaching the router — either by validating the incoming request against
   `knowledge_context_request.schema.json` (`additionalProperties: false`) with the same real
   validator and raising/returning an error, or by FastMCP's own typed-parameter mechanism rejecting
   an unexpected kwarg (verify which mechanism the real implementation uses and assert against that
   real behavior, not an assumed one). AC #2.
   Location: `tests/tools/test_knowledge_gateway_mcp.py`.

4. **`test_knowledge_status_omits_all_cache_specific_fields_enumerated`**
   Category: unit — the field-omission test AC #3 requires.
   Verifies: enumerate §9.2's **full** field list. Since none of `retrieval_events.py`'s 3 Wrapper
   functions genuinely apply to this ticket's real Phase 1 call path (Design Decision D1 —
   `wrap_hybrid_retrieval` needs internal state only `search_mcp.py::_run_search()` builds
   internally; `wrap_retrieval_cache_check` needs a real cache, Phase 2 out of scope;
   `wrap_context_packet_assembly` wraps a structurally different, unrelated module), there is no
   real call site emitting `latency_summary_ms` data at all — the entire `latency_summary_ms` key
   is omitted, not just its 2 cache-domain sub-fields. The omitted-field list is:
   `cache_entry_counts`, `cache_hit_rate`, `cache_miss_rate`, `cache_stale_rejection_rate`,
   `recent_invalidation_reasons`, `cache_rebuildable`, and the top-level `latency_summary_ms` key
   itself (all 5 sub-fields — `lookup`, `evidence_validation`, `provider_fallback`,
   `packet_assembly`, `end_to_end` — go with it). For each: assert it is **absent** from the
   response dict — never present with value `0`, `0.0`, `None`, `{}`, or an empty list/string
   standing in for "unavailable." Also assert the schema-valid fields that ARE Phase-1-populable
   (`gateway_version`, `reported_schema_version`, `providers`, `branch_scope`) ARE present with real
   (non-fabricated) values — a pure absence-check alone wouldn't catch a broken implementation that
   omits everything. Location: `tests/tools/test_knowledge_gateway_mcp.py`.

5. **`test_mcp_json_gains_exactly_one_new_server_entry`**
   Category: integration.
   Verifies: `.mcp.json`'s `mcpServers` key set is exactly `{"knowledge-search", "github",
   "<new-server-name>"}` (one net-new key vs. the pre-ticket baseline), and the new entry's shape
   (`command`/`args`/`env`/`description` keys, following the *real* current `knowledge-search`
   entry's `bash` + wrapper-script pattern, not the stale `test_search_mcp.py` expectation — see
   investigation.md's current-behavior section). AC #4 (`.mcp.json` half).
   Location: `tests/tools/test_knowledge_gateway_mcp.py` (or a dedicated
   `TestMcpJsonNewEntry` class alongside test 6).

6. **`test_search_mcp_py_provably_untouched`**
   Category: integration / architecture guard — git-diff-based, per AC #4's exact wording.
   Verifies: `subprocess.run(["git", "diff", "--stat", "HEAD", "--", "tools/search_mcp.py"])`
   produces empty stdout. (Run relative to repo root; skip/xfail gracefully if not inside a git
   worktree, matching whatever convention existing git-diff-based tests in this repo already use —
   check `tests/` for precedent at Plan time.) Also assert the `graphify` CLI invocation path is
   untouched: no new `tools/graphify*.py` file and no edit to `graphify-out/` config paths in this
   ticket's diff — confirm the concrete assertion shape against how `graphify` is actually invoked
   (likely just: no `tools/knowledge_gateway_mcp.py` shells out to a *modified* graphify wrapper;
   it should reuse `knowledge_gateway_router.py::match_symbol_name()` unchanged).
   Location: `tests/tools/test_knowledge_gateway_mcp.py`.

7. **`test_wrapper_functions_genuinely_not_applicable_zero_invoked`**
   Category: integration.
   Verifies the honest-negative outcome AC #4's own parenthetical permits ("or the subset
   architecturally applicable... not force-fit ones that don't"): per Design Decision D1, zero of
   the 3 `retrieval_events.py` Wrapper functions (`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`,
   `wrap_context_packet_assembly`) genuinely apply to this ticket's real Phase 1 call path, and no
   new function is added to `retrieval_events.py` to force a fit (that approach was explicitly
   rejected at Review as scope creep / a check-passing workaround). Concretely: monkeypatch/spy on
   all 3 wrapper functions (e.g. `monkeypatch.setattr(retrieval_events_module, "wrap_hybrid_retrieval",
   spy1)` etc.) and assert `spy.call_count == 0` for each after invoking `knowledge_context` and
   `knowledge_status` — proving the honest-zero claim structurally, not just by absence of an
   import. Separately assert `git diff --stat HEAD -- tools/retrieval_events.py` is empty — proving
   the file itself was never touched, not just that its functions weren't called at runtime. Two
   independent proofs: "genuinely zero invocations" and "the module itself is byte-unchanged." AC #4
   (wrapper half).
   Location: `tests/tools/test_knowledge_gateway_mcp.py`.

8. **`test_only_knowledge_context_and_knowledge_status_registered`**
   Category: architecture guard.
   Verifies: enumerate the FastMCP server's registered tool names (via the server object's own
   introspection — check what `mcp.server.fastmcp.FastMCP` exposes, e.g. `server._tool_manager.
   _tools.keys()` or an equivalent public/semi-public accessor; confirm the exact real attribute
   at Plan/Implement time rather than guessing) and assert the set is exactly
   `{"knowledge_context", "knowledge_status"}` — no `knowledge_learn`/`knowledge_promote`/
   `knowledge_verify`/invalidation tool. AC #5.
   Location: `tests/tools/test_knowledge_gateway_mcp.py`.

9. **`test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing`**
   Category: unit (happy-path-adjacent, not the full §16 matrix — that's
   `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`'s job per this ticket's own Out of Scope).
   Verifies: if `call_providers_for_routing_decision()` records a failure (e.g. context_search
   returns `{"error": ...}`), the resulting `PacketAssembly.status == "PARTIAL"` (per
   `assemble_packet()`'s own real logic, `:627-633`) is surfaced in the tool's response `status`
   field unchanged — the new server layer does not catch and re-shape this into a generic "OK" or
   swallow it silently.
   Location: `tests/tools/test_knowledge_gateway_mcp.py`.

10. **`test_provider_context_search_adapter_version_null_not_fabricated`**
    Category: unit — regression guard for investigation.md's `adapter_version: null` finding.
    Verifies: `knowledge_status`'s `providers[]` entry for `provider_id == "context_search"` has
    `generation` either absent or explicitly `None`/`null`-equivalent — never a fabricated version
    string — reflecting the frozen descriptor's real `adapter_version: null`.
    Location: `tests/tools/test_knowledge_gateway_mcp.py`.

## Scoped Pytest Commands

```bash
# This ticket's own new test file
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -v

# Regression surface: the 3 frozen KGMCP dependencies + the schema/contract suite this ticket
# necessarily perturbs (test_no_live_gateway_tool_code_or_mcp_registration_introduced must be
# updated, not merely re-run)
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_router.py \
  tests/tools/test_knowledge_gateway_packet_assembly.py \
  tests/tools/test_knowledge_gateway_contract_schemas.py \
  tests/tools/test_knowledge_gateway_mcp.py -v

# tools/search_mcp.py's own suite — prove no accidental behavior change; expect the SAME 2
# pre-existing TestMcpJson failures before and after, nothing new
.venv/bin/python3 -m pytest tests/tools/test_search_mcp.py -v

# Wrapper module's own suite, if it exists as a dedicated file (confirm exact path at Plan time)
.venv/bin/python3 -m pytest tests/tools/test_retrieval_events.py -v
```

Never `pytest tests/` — scope stays inside `tests/tools/` for this ticket (agent-orchestration
tooling, no `src/` domain to cross-cut).

## Anti-Drift Test Guards

- **Frozen-file-untouched guard** (test 6 above) — the single highest-value anti-drift test in this
  plan; directly enforces AC #4's `.mcp.json`/`search_mcp.py` half and should also assert (via the
  same `git diff --stat` mechanism) that `tools/knowledge_gateway_router.py` and
  `tools/knowledge_gateway_packet_assembly.py` are untouched, even though the AC only names
  `search_mcp.py` literally — both are DONE dependencies this ticket must only import.
- **No-force-fit guard**: test 7's two-independent-proofs shape (spy `call_count == 0` on all 3
  wrappers AND an empty `git diff` on `tools/retrieval_events.py`) exists specifically so a future
  edit that "just calls a wrapper once on arbitrary dummy args to make AC #4's literal wording look
  satisfied," or that adds a new unauthorized wrapper function to close the same gap, fails this
  test — a spy-only check without the zero-diff check would not catch a new-function addition, and
  a diff-only check without the spy check would not catch a dummy-arg force-call of an existing
  wrapper.
- **Exactly-2-tools guard** (test 8) directly blocks §9.3 scope creep — any future edit that
  accidentally registers `knowledge_learn`/`knowledge_promote`/`knowledge_verify` (e.g. copy-pasted
  from a Phase 2+ branch) fails immediately.
- **Cache-field-omission guard** (test 4) is the direct enforcement of AC #3 and must assert the
  entire `latency_summary_ms` top-level key is absent, not just its cache-domain sub-fields — since
  no real call site (per the honest-zero wrapper finding) emits any latency data at all in Phase 1.
  A test that only checked the 6 ticket-named cache fields would pass a Phase 1 implementation that
  silently fabricates `latency_summary_ms` values instead of omitting the whole key.
- **Request-schema-closure guard** (test 3) directly enforces §9.1's "never expose provider
  weights/cache-level/semantic-threshold/provider-forcing/ranking-policy" rule at the live tool
  boundary, not just at the frozen-schema-file level `test_knowledge_gateway_contract_schemas.py`
  already covers.
- **`adapter_version: null`-is-real guard** (test 10) exists specifically to stop a future edit from
  "fixing" what looks like a missing value by fabricating a `context_search` version string —
  `null` is the correct, evidenced value here.
