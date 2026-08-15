---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE
phase: done
date: 2026-08-15
tags: [ai, mcp]
---

# TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE

## Title
Expose knowledge_context and knowledge_status as real MCP tools over the router and packet
assembler

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Wire `TCK-20260815-KGMCP-P1-QUERY-ROUTER`'s routing and `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY`'s
packet output into a real, callable FastMCP server exposing `knowledge_context` (§9.1) and
`knowledge_status` (§9.2), conforming to Phase 0's frozen
`knowledge_context_request.schema.json`/`knowledge_context_response.schema.json`/
`knowledge_status_response.schema.json`. Mirrors `tools/search_mcp.py`'s existing FastMCP pattern
(`TCK-20260612-LOCAL-CTX-MCP`) rather than inventing a new server framework.

## Scope
- Implement `knowledge_context` as a FastMCP tool: accept the frozen request schema's fields
  (`query` required; `mode`, `budget_tokens`, `changed_paths`, `include_history`,
  `evidence_detail` optional), reject any field the schema's `additionalProperties: false` already
  disallows, call the router then the packet assembler, and return a response validating against
  `knowledge_context_response.schema.json`.
- Implement `knowledge_status` as a FastMCP tool, Phase-1-scoped field subset only (no cache
  exists yet): gateway/schema version, provider availability and generation (read from the real
  `provider_capabilities_*.json` files' `adapter_version`/live health-check), the 5
  measurement-point latency summaries (§18, wired through `tools/retrieval_events.py`'s 3 Wrapper
  functions — this is the real call site that finally invokes them), provider fallback rates,
  branch and working-tree scope. Omit every cache-specific field §9.2 lists (cache entry counts,
  hit/miss/stale-rejection rates, recent invalidation reasons, cache-rebuild-safety) — those require
  Phase 2's cache to exist; document the omission explicitly in the response or a companion field,
  never silently return a fabricated zero.
- Register the new server in `.mcp.json` following the existing `knowledge-search` entry's exact
  shape (command/args/env/description), so it is ambiently available with no ticket/workflow
  metadata required (§2.1).
- Ensure `knowledge_learn`, `knowledge_promote`, `knowledge_verify`, and any invalidation tool are
  NOT exposed (§9.3 — explicitly deferred).
- Preserve `tools/search_mcp.py` and the `graphify` CLI exactly as they are — this ticket adds a
  new server, it does not modify, wrap, or deprecate the existing ones (§16's "preserve direct
  provider tools" requirement, verified by a git-diff-based regression test against both files).

## Out of Scope
- Fail-open failure-path behavior beyond what naturally falls out of correct implementation —
  the dedicated fail-open/failure-semantics test matrix is `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`'s
  job; this ticket implements the happy path and passes through router/assembler failures without
  swallowing them, but does not itself build the full §16 failure-matrix test suite.
- Any caching.
- Any CLAUDE.md/.claude/agents/*.md/.claude/skills/*.md edit — registering the server in
  `.mcp.json` makes the tool available, never mandatory; this ticket must not touch any instruction
  file.
- Model-generated synthesis or model-based intent classification.

## Acceptance Criteria
- [x] `knowledge_context` and `knowledge_status` are real, invocable FastMCP tools; a test invokes
      each directly (not just imports the module) and validates the response against the frozen
      JSON Schemas using a real JSON Schema validator, not hand-written assertions.
- [x] `knowledge_context`'s request validation rejects any field not in the frozen schema (a test
      sends an extra/forbidden field and asserts rejection).
- [x] `knowledge_status`'s Phase 1 response never includes a cache-specific field with a fabricated
      value — a test enumerates §9.2's full field list and asserts every cache-specific one is
      either absent or an explicit "not yet available (Phase 2)" marker, never a bare `0`/`null`
      that could be misread as "empty but real."
- [x] `.mcp.json` gains exactly one new server entry; `tools/search_mcp.py` and the `graphify` CLI
      invocation path are provably untouched (`git diff --stat HEAD -- tools/search_mcp.py` empty).
- [x] `wrap_hybrid_retrieval`/`wrap_retrieval_cache_check`/`wrap_context_packet_assembly` (or the
      subset architecturally applicable to a still-uncached Phase 1 gateway — Investigate must
      determine which of the 3 genuinely apply pre-Phase-2 and not force-fit ones that don't) are
      invoked from this real call site, with a test proving the invocation actually happens (not
      just that the import succeeds). **Satisfied via the honest empty-subset outcome this AC's own
      wording explicitly permits** — zero of the 3 named wrappers genuinely apply (see
      Implementation Notes); `test_wrapper_functions_genuinely_not_applicable_zero_invoked` proves
      the zero-invocation claim structurally (spy `call_count == 0` on all 3) plus a zero-diff guard
      on `tools/retrieval_events.py` itself.
- [x] `knowledge_learn`/`knowledge_promote`/`knowledge_verify`/any invalidation tool: zero such tool
      is registered — a test enumerates the FastMCP server's registered tool names and asserts the
      set is exactly `{knowledge_context, knowledge_status}`.

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC (parent)
- TCK-20260815-KGMCP-P1-QUERY-ROUTER (dependency)
- TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY (dependency)
- TCK-20260814-KGMCP-CONTRACT-SCHEMAS (DONE; source of the frozen schemas this ticket's I/O must
  validate against)
- TCK-20260612-LOCAL-CTX-MCP (DONE; `tools/search_mcp.py`'s FastMCP pattern this ticket mirrors and
  must not modify)
- TCK-20260814-KGMCP-MEASUREMENT-BASELINE (DONE; names the 3 Wrapper functions as "implemented but
  not invoked" — this ticket is where that gap is closed)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §9.1, §9.2, §9.3, §16 ("preserve direct provider
  tools and fail-open behavior" bullet)
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json`,
  `knowledge_context_response.schema.json`, `knowledge_status_response.schema.json`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/search_mcp.py` (pattern to mirror; must remain untouched)
- `.mcp.json`
- `tools/retrieval_events.py` (3 Wrapper functions to wire in)
- New: `tools/knowledge_gateway_mcp.py` (or the package path chosen by the router ticket's Plan
  phase)

## Assumptions / Open Questions
- `knowledge_status`'s Phase-1-appropriate schema handling: reuse
  `knowledge_status_response.schema.json` as-is with cache fields nullable/omitted, or freeze a
  Phase-1 response variant — flagged by the parent epic for this ticket's own Investigate phase to
  resolve against the real, existing frozen schema (check whether it already models optionality
  correctly) before Plan.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE/plan.md`
(post-Architecture-Review revision), no deviations.

- **New module `tools/knowledge_gateway_mcp.py`.** Single flat file mirroring
  `tools/search_mcp.py`'s FastMCP pattern: `importlib.util` sibling-loading of
  `knowledge_gateway_router.py`/`knowledge_gateway_packet_assembly.py`/`search_mcp.py` under
  distinct `sys.modules` keys, module-level `jsonschema.Draft7Validator` instances for the request
  schema, the response schema (with a `jsonschema.RefResolver` for its `shared_enums.schema.json`
  `$ref`s), and the status-response schema. `GATEWAY_VERSION` is read from `pyproject.toml`'s
  `[project].version` via `tomllib`; `REPORTED_SCHEMA_VERSION = 1` is a hardcoded constant kept in
  sync with both frozen schemas' own `"schema_version": 1`.
- **`_run_knowledge_context()`.** Builds a request dict from only the non-`None` supplied kwargs,
  validates it against the frozen request schema (secondary, value-level enforcement — e.g. an
  invalid `mode` value returns a schema-conformant `status: "ERROR"` response). Primary
  forbidden-field enforcement is the registered tool's fixed keyword-only Python signature: an
  unexpected kwarg raises `TypeError` before the function body runs (verified live, both at the
  direct-call layer and via FastMCP's own protocol-level schema). Calls `_kgr.route(query)` then
  `_kgpa.assemble_packet(routing_decision, query, budget_tokens or DEFAULT_BUDGET_TOKENS)` directly
  and unwrapped — no `tools/retrieval_events.py` wrapper is invoked (see wrapper finding below).
  Maps `PacketAssembly`'s dataclass fields onto the response schema field-by-field; a shared
  `_omit_none()` helper strips any `None`-valued key from `statements[]`/`context[]`/`evidence[]`
  entries before serialization — verified live via `jsonschema.Draft7Validator` that
  `context[].path`/`context[].authority`/`evidence[].path` (typed plain `string`, no `null`
  variant) fail validation if passed as JSON `null`, and validate cleanly only when omitted. Every
  returned response is validated against the frozen response schema before being returned (raises
  if a future edit ever breaks conformance — fail-loud by construction, not fail-open).
- **`_run_knowledge_status()`.** Populates only the 4 Phase-1-populable top-level fields:
  `gateway_version`, `reported_schema_version`, `providers[]` (2 entries — `context_search`'s
  `available` from a real `_run_health()` call, `generation` omitted since its frozen
  `adapter_version` is genuinely `null`; `graphify`'s `available` from a real
  `shutil.which("graphify")` check, `generation` read live from the frozen
  `provider_capabilities_graphify.json`), and `branch_scope` (real `git branch --show-current` /
  `git status --porcelain` subprocess calls, list-form args, no `shell=True`). All 6 named
  cache-specific fields, the entire `latency_summary_ms` top-level key (all 5 sub-fields), and
  `provider_fallback_rate` are omitted outright — never a fabricated `0`/`null`/`{}`. Verified live
  this is schema-valid: the status response schema's `required` list is only
  `["gateway_version", "reported_schema_version"]`.
- **Wrapper-function finding (AC #4b), honestly reported per Architecture Review ruling.** Zero of
  `tools/retrieval_events.py`'s 3 Wrapper functions (`wrap_hybrid_retrieval`,
  `wrap_retrieval_cache_check`, `wrap_context_packet_assembly`) genuinely apply to this ticket's
  real call site — re-verified function-by-function against the real source (see plan.md Step 4 /
  investigation.md Risk #1 for the full evidence): `wrap_hybrid_retrieval` needs internal state
  only `search_mcp.py::_run_search()` builds for itself; `wrap_retrieval_cache_check` needs a real
  cache (Phase 2, out of scope); `wrap_context_packet_assembly` wraps a structurally different,
  unrelated packet assembler (`tools/context_packet_assembler.py`). No 4th wrapper was added — that
  approach was explicitly rejected at Architecture Review as scope creep / a check-passing
  workaround. `tools/retrieval_events.py` is not imported or called anywhere in this module —
  confirmed zero-diff (`git diff --stat HEAD -- tools/retrieval_events.py` empty) and zero
  invocation (test 7, spy `call_count == 0` on all 3 functions).
- **`tools/start_knowledge_gateway_mcp.sh`.** Byte-for-byte structural mirror of
  `tools/start_search_mcp.sh` (same venv-priority-list pattern), only the final `exec` target
  changed. Made executable (`chmod +x`), matching the sibling script's permission bits.
- **`.mcp.json`.** Added exactly one new `knowledge-gateway` entry under `mcpServers`, merged in
  (not overwritten) alongside the existing `knowledge-search`/`github` entries, following
  `knowledge-search`'s real shape exactly (`command: "bash"`, `args: ["tools/start_knowledge_gateway_mcp.sh"]`,
  `env: {}`, `description: "..."`).
- **`_build_server()` / `_run_mcp_server()` split.** `_run_mcp_server()`'s FastMCP-registration
  logic was factored into a separate `_build_server()` that returns the configured server without
  calling `.run()` — necessary so tests can introspect `server._tool_manager._tools.keys()` (AC #5)
  without blocking on the stdio transport. This is a minimal structural addition within Step 7's
  own scope (registering the tools on a FastMCP instance); no new tool, no behavior change to the
  real entry point (`__main__` still calls `_run_mcp_server()` -> `_build_server().run()`).
- **Stale Phase-0 guard tests — 3 files affected, not just the 1 plan.md named.** Plan.md's Step 7
  named only `tests/tools/test_knowledge_gateway_contract_schemas.py`'s
  `test_no_live_gateway_tool_code_or_mcp_registration_introduced` as needing an update (renamed to
  `test_phase_1_gateway_tool_code_and_mcp_registration_now_exist`, assertions inverted per Step 7's
  exact instruction). Running the full regression suite surfaced that the identical
  `.mcp.json`-key-set assertion (`{"knowledge-search", "github"}`) was independently duplicated in
  two more DONE-ticket test files not named by plan.md: `tests/tools/test_knowledge_gateway_router.py::test_no_live_gateway_tool_code_or_mcp_registration_introduced`
  and `tests/tools/test_knowledge_gateway_packet_assembly.py::test_module_introduces_zero_mcp_server_code`.
  Both were updated with the same minimal, surgical fix already established as correct precedent by
  plan.md Step 7 (the literal `.mcp.json` key set is now `{"knowledge-search", "github", "knowledge-gateway"}`) —
  their other assertions (that `knowledge_gateway_router.py`/`knowledge_gateway_packet_assembly.py`
  themselves still define zero live tool code) are still true and were left unchanged. The router
  test's `tools/*.py` glob loop was also given a one-line skip for `knowledge_gateway_mcp.py`
  itself, since that file now legitimately defines `knowledge_context`/`knowledge_status`. This is
  not scope creep — it is the same "test must be updated in the same change, not left broken"
  discipline plan.md's own Step 7 established, applied to a duplicate the plan's authors did not
  enumerate. No other assertion in either file was touched. This deviation is also recorded in
  `staging_artifacts/TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE/plan.md`'s Deviations section.
- **Document-Update and Parity phases, deferred by design at Implement time, are now both
  complete.** Per plan.md's own "Docs to Update (Document-Update Phase — not part of Implement)"
  and "Parity Ledger (flag only — not written by this Plan phase)" sections, these were
  intentionally NOT written by this Implement pass. They were subsequently completed in this
  ticket's own later phases: Document-Update added the `measurement_baseline_contract.md` §2.1/§2.4
  reconfirmation footnotes (the real sections citing the 2 relevant wrappers turned out to be §2.1
  and §2.4, not §2.3 — corrected against the real file text) and the
  `knowledge-gateway-mcp-proposal.md` §20 Phase 1 checklist annotations; Parity added the new
  `INFRA-337` ledger entry, re-verified 12/12 `test_path` pass.

## Test Summary

New file `tests/tools/test_knowledge_gateway_mcp.py` — 12 tests, all passing (test_plan.md's 10
tests plus test_plan.md-cited-but-not-numbered `test_knowledge_context_omits_null_path_and_authority_never_returns_null_for_typed_string_fields`,
plus one additional value-level-validation variant covering the ERROR-response path explicitly):

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -v
12 passed
```

Regression suite (this ticket's 3 frozen KGMCP dependencies + the schema/contract suite this
ticket necessarily perturbs + this ticket's own new file):

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_router.py \
  tests/tools/test_knowledge_gateway_packet_assembly.py \
  tests/tools/test_knowledge_gateway_contract_schemas.py \
  tests/tools/test_knowledge_gateway_mcp.py -q
89 passed
```

`tools/search_mcp.py`'s own suite — same 2 pre-existing `TestMcpJson` failures before and after
(`test_command_is_python3`, `test_args_point_to_search_mcp` — documented stale, out of this
ticket's scope, investigation.md Risk #5), nothing new, no accidental fixes:

```
.venv/bin/python3 -m pytest tests/tools/test_search_mcp.py -q
2 failed, 14 passed
```

`tools/retrieval_events.py`'s own suite — unmodified, still fully passing:

```
.venv/bin/python3 -m pytest tests/tools/test_retrieval_events.py -q
36 passed
```

`tests/tools/test_kgmcp_measurement_baseline.py` (Phase 0 measurement-baseline suite, also
git-diff-sensitive to `tools/retrieval_events.py`/`tools/search_mcp.py`) — run as an extra
cross-check, unaffected:

```
.venv/bin/python3 -m pytest tests/tools/test_kgmcp_measurement_baseline.py -q
23 passed
```

Frozen-file zero-diff verified directly: `git diff --stat HEAD -- tools/search_mcp.py` and
`git diff --stat HEAD -- tools/retrieval_events.py` both produce empty output.

## Files Changed

- `tools/knowledge_gateway_mcp.py` (new) — the FastMCP server: `knowledge_context`/`knowledge_status`
  tools, schema validators, sibling-module loaders.
- `tools/start_knowledge_gateway_mcp.sh` (new) — launcher script, mirrors `start_search_mcp.sh`.
- `.mcp.json` (modified) — one new `knowledge-gateway` entry added under `mcpServers`.
- `tests/tools/test_knowledge_gateway_mcp.py` (new) — 12 tests for the new module.
- `tests/tools/test_knowledge_gateway_contract_schemas.py` (modified) — Phase-0 guard test renamed
  to `test_phase_1_gateway_tool_code_and_mcp_registration_now_exist`, assertions inverted per
  plan.md Step 7's explicit instruction.
- `tests/tools/test_knowledge_gateway_router.py` (modified) — updated the duplicate stale
  `.mcp.json`-key-set assertion inside `test_no_live_gateway_tool_code_or_mcp_registration_introduced`
  (not named by plan.md; discovered running the regression suite; same fix pattern as the
  contract-schemas test).
- `tests/tools/test_knowledge_gateway_packet_assembly.py` (modified) — same fix, inside
  `test_module_introduces_zero_mcp_server_code`.
- `docs/plans/knowledge-gateway-mcp-proposal.md` (§20 Phase 1 bullets annotated Done: "Expose
  knowledge_context and knowledge_status", "Register the gateway as an ambient general repository
  utility...", "Return uncached normalized results with provenance", Document-Update phase)
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` (§2.1/§2.4
  "Reconfirmed 2026-08-15" footnotes added — the pre-existing "implemented but not invoked" framing
  for `wrap_retrieval_cache_check()`/`wrap_context_packet_assembly()` was re-examined and confirmed
  still accurate, Document-Update phase)
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` ("Phase 1 update" footnote correcting a
  stale "no code exists yet" claim and "a future router" wording, Document-Update phase)
- `docs/ai/claude_md_prescan_mandate_relaxation_draft.md` ("Update" footnote noting the gateway now
  exists, while clarifying this does not satisfy the draft's separate Activation Precondition,
  Document-Update phase)
- `docs/parity_ledger/infrastructure.yaml` (new `INFRA-337` entry, via `write_entry()`, Parity
  phase)

Not touched (verified via `git diff --stat HEAD`, empty for each): `tools/search_mcp.py`,
`tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
`tools/retrieval_events.py`.

## Completion Summary

Implement phase is complete and all of this ticket's own acceptance criteria are satisfied,
including AC #4b via the honest "zero of the 3 named wrappers genuinely apply" outcome AC #4's own
wording explicitly permits (re-verified against real source, twice reviewed — no 4th wrapper was
added). `knowledge_context` and `knowledge_status` are real, invocable FastMCP tools registered on
a `FastMCP("knowledge-gateway")` instance (exactly these two — no `knowledge_learn`/
`knowledge_promote`/`knowledge_verify`/invalidation tool), wired over the frozen router and packet
assembler, validating both request and response against the frozen JSON Schemas with a real
`jsonschema.Draft7Validator`. `.mcp.json` gained exactly one new entry; `tools/search_mcp.py`,
`tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, and
`tools/retrieval_events.py` are all provably untouched (zero diff). All 12 new tests pass, and the
full regression surface (89 tests across the 4 KGMCP suites, plus `search_mcp.py`'s and
`retrieval_events.py`'s own suites) passes with no new failures. Document-Update added the
`measurement_baseline_contract.md` §2.1/§2.4 reconfirmation footnotes and the
`knowledge-gateway-mcp-proposal.md` §20 checklist annotations; Parity added the `INFRA-337` ledger
entry, re-verified 12/12 `test_path` pass, shape-matches the `INFRA-336` precedent. Both phases are
now complete.
