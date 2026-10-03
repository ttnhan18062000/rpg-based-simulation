---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-FAILOPEN-TESTS
artifact_type: investigation
tags: [ai, mcp, testing]
---

# Investigation — TCK-20260815-KGMCP-P1-FAILOPEN-TESTS

## Current Behavior

### `tools/knowledge_gateway_mcp.py` (frozen, DONE by TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE)
- `_run_knowledge_context()` (L139-259): validates the request against
  `knowledge_context_request.schema.json`; on `ValidationError` it returns a hand-built
  `status="ERROR"` envelope (never raises to the caller) — this is the one place an error is
  already turned into a structured response. It then calls `_kgr.route(query)` and
  `_kgpa.assemble_packet(routing_decision, query, effective_budget)` **directly and unwrapped, with
  no try/except** (module docstring's own "Wrapper-function finding" confirms no
  `tools/retrieval_events.py` wrapper is used here). Any exception `route()`/`assemble_packet()`
  raise propagates straight out of `_run_knowledge_context()` and out of the registered
  `knowledge_context` FastMCP tool (L328-356) uncaught.
- `_run_knowledge_status()` (L278-315): calls `_sm._run_health()` (never raises — returns a status
  dict), reads `provider_capabilities_graphify.json` from disk, and calls
  `shutil.which("graphify")` (never raises). No provider-unavailable branch changes shape here;
  `available: false` is just a boolean field.
- `_build_server()`/`_run_mcp_server()` (L320-383): registers exactly `knowledge_context` and
  `knowledge_status` on a `FastMCP("knowledge-gateway")` instance; `_run_mcp_server()` only catches
  `ImportError` on `mcp` itself, not any tool-execution failure.
- **Finding: an unhandled exception from `route()`/`assemble_packet()` currently propagates, not
  turned into a fail-open response by this module.** Whether the FastMCP framework itself catches
  a raised exception from inside a `@server.tool()` function and converts it to a
  protocol-level error (rather than crashing the process) is a FastMCP-library behavior this
  ticket has not verified — see Risks.

### `tools/knowledge_gateway_router.py` (frozen, DONE by TCK-20260815-KGMCP-P1-QUERY-ROUTER)
- `match_symbol_name()` (L98-118) always shells out to the real `graphify` CLI via
  `subprocess.run(["graphify", "query", text], ..., timeout=120)`. It does **not** catch
  `subprocess.TimeoutExpired` (that raises straight out) and does **not** catch
  `FileNotFoundError` (raised if the `graphify` binary is not on `PATH` at all). It always returns
  a plain dict (`{"symbol", "returncode", "stdout"}`) on a completed process, regardless of
  `returncode` — a non-zero returncode is not itself an exception.
- `route_ambiguous()` (L281-304) and `route()` (L392-433) call
  `_run_context_search_provider()`/`_run_graphify_provider()`/`match_symbol_name()` with **no
  try/except anywhere in this module**. A `graphify` subprocess timeout or missing-binary error
  raised inside `match_symbol_name()` propagates straight out of `route()`/`route_ambiguous()`
  uncaught — this module does zero failure handling of its own; it delegates that entirely to
  callers (confirmed: `knowledge_gateway_packet_assembly.py` is the only caller that adds a
  try/except around `match_symbol_name()`, and only for `TimeoutExpired`).
- `_run_context_search_provider()` (L258-274) calls `_sm._run_search(query_text)` directly and
  returns its raw output unwrapped — `_run_search()` never raises (see below), so this is safe by
  the callee's own contract, not this module's own handling.

### `tools/knowledge_gateway_packet_assembly.py` (frozen, DONE by TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY)
- `call_providers_for_routing_decision()` (L159-194) is the **one place** in the whole pipeline
  that catches a provider failure explicitly:
  - `context_search`: calls `_sm._run_search(query_text)`; if the result is a dict containing
    `"error"` (search_mcp's own no-index-found signal), appends
    `f"context_search: {raw['error']}"` to a local `results["failures"]` list.
  - `graphify`: calls `_kgr.match_symbol_name(query_text)` inside
    `try/except subprocess.TimeoutExpired` **only** — a timeout appends
    `"graphify: subprocess timeout"` to `results["failures"]`. A **non-zero returncode or empty
    stdout is treated as silent absence, not failure** — `continue`s with no `failures` entry at
    all (comment at L186-188: "An empty/failed call is never itself content ... this is not an
    error, just absence"). `FileNotFoundError` (graphify binary missing entirely) is **not caught
    here either** — it propagates.
  - `results["failures"]` is a **local dict key only** — it is read once, inside
    `assemble_packet()` (L627-628: `failures = provider_results.get("failures", []);
    if budget_assembly_failed or failures: status = "PARTIAL"`), purely to decide the `status`
    string. **`PacketAssembly` (the returned dataclass, L551-566) has no `failures` field at
    all** — the list of *which* provider failed and *why* is computed, used once to flip a status
    enum, and then discarded. Nothing downstream (`knowledge_gateway_mcp.py`'s response-building
    code, L185-259) ever sees or forwards it.
- `assemble_packet()`'s §16 budget-assembly-failure branch (L609-619) is real and already
  independently unit-tested (see Prior Work) — it correctly returns an empty statement/context
  list with real (never fabricated) evidence entries when even the highest-priority statement
  cannot fit the budget.
- `freshness` (L636) is a **hardcoded literal `"UNKNOWN"`** — there is no code path anywhere in
  this module, the router, or the MCP layer that computes, compares, or branches on any
  staleness/generation signal. See Mechanics/Engine Constraints and Risks below.

### `tools/search_mcp.py::_run_search()` (frozen; independently maintained)
- Never raises. On missing index (`_ensure_loaded()` returns `False`), returns
  `{"error": "index not found", "action": "run make knowledge-index"}` — a structured error
  dict, not an exception. Confirmed by `tests/tools/test_search_mcp.py::TestRunSearchMissingIndex`.
  This is exactly the shape `call_providers_for_routing_decision()`'s `context_search` branch
  checks for (`isinstance(raw, dict) and "error" in raw`), so "one provider unavailable" via a
  missing search index is **already** correctly turned into a `failures` entry → `status=PARTIAL`
  at the packet-assembly layer (though, per above, the specific failure text is then dropped
  before reaching the MCP response).
- `_run_search()` and `graphify query` are each independently invocable via `python3
  tools/search_mcp.py --test` (stdin/stdout JSON smoke-test mode, L177-206, wired to the
  `mcp-server-test` Makefile target) and the bare `graphify` CLI, **with zero import of or
  dependency on `tools/knowledge_gateway_mcp.py`** — confirmed by reading both files' imports.
  Neither module imports `knowledge_gateway_mcp`. This structurally proves the "gateway process
  unavailable → agent calls provider tools directly" row requires **no new code**, only a test
  that starts neither the gateway server nor mocks anything, and calls both provider entry points
  directly (subprocess for realism, matching the `--test` mode's own existing precedent).

## Mechanics / Engine Constraints
- `docs/plans/knowledge-gateway-mcp-proposal.md` §16 (the exact 7-row table, verbatim):

  | Failure | Required behavior |
  |---|---|
  | Gateway process unavailable | Agent calls provider tools directly |
  | Cache missing or corrupt | Recreate schema and perform cold provider query |
  | One provider unavailable | Return partial result with explicit provider failure |
  | Graphify stale | Use Context Search/Parity where applicable; flag code-graph result unavailable |
  | Context Search stale | Use direct docs/tickets/source where appropriate |
  | Cached evidence mismatch | Reject the cache hit and refresh |
  | Token-budget assembly failure | Return a smaller evidence list or provider references, never fabricated content |

  "Failures should be observable but fail-open for agent work."
- §16's own row order and prose group "Graphify stale" / "Context Search stale" alongside the
  purely cache-oriented rows ("Cache missing or corrupt", "Cached evidence mismatch"). The
  proposal's own Phase-plan section (§Phase list, "Phase 1: Read-Only Gateway") lists exactly 4
  Phase-1 bullets, all already DONE (router, MCP tool surface, uncached results with provenance,
  extractive packet assembly) — **no Phase 1 bullet anywhere mentions staleness detection,
  generation-fingerprint comparison, or any freshness computation.** The one place staleness logic
  is spec'd at all is `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`
  §4 ("Provider-generation fallback rule") — a **cache-identity contract**, i.e. explicitly Phase-2
  territory per the epic's own phasing (cache is Phase 2, confirmed by
  `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` and this ticket's own
  Request Summary treating "cache missing/corrupt" as Phase-2-only).
- `provider_capabilities_graphify.json`/`provider_capabilities_context_search.json` each carry a
  `generation_fingerprint: true` **boolean capability flag** ("this provider is capable of
  supporting generation fingerprinting") and an `adapter_version` string/`null` — neither is
  itself a "this result is stale" signal; staleness requires comparing a fingerprint **against a
  previously-observed baseline**, and nothing in Phase 1 code stores or compares any such
  baseline. `knowledge_status`'s `providers[].generation` field (populated only for `graphify`,
  since `context_search`'s `adapter_version` is genuinely `null`) is the only place a generation
  value is surfaced at all today, and it is purely descriptive — no gateway code branches on it.

## Docs Requiring Update
- `docs/plans/knowledge-gateway-mcp-proposal.md`: §16's "Graphify stale"/"Context Search stale"
  rows currently read as unconditionally Phase-1-testable; once Plan resolves the staleness gap
  (see Risks), this doc's Phase 1 bullet list should gain an explicit line noting which of the 7
  §16 rows Phase 1 code paths actually implement today (mirroring how "cache missing/corrupt" is
  already implicitly Phase-2 by the existing bullet list's silence on caching).
- `docs/guidelines/intentional_divergences.md`: if Plan decides the "one provider unavailable"
  gap (failure reason computed then silently dropped before reaching the MCP response; a
  non-zero-returncode graphify failure is currently indistinguishable from a legitimate empty
  result) is accepted as current, intentional Phase-1 behavior rather than fixed, it must be
  recorded here with a rationale class and a verification test path — this repo's Authoritative
  Mechanics Rule requires any intentional divergence from spec'd behavior to be logged, not left
  implicit.
- `docs/parity_ledger/infrastructure.yaml`: INFRA-337 (`tools/knowledge_gateway_mcp.py`,
  `test_path: tests/tools/test_knowledge_gateway_mcp.py`) and/or a new ledger entry for this
  ticket's own failure-semantics suite should be added/updated once the actual test suite lands,
  recording which of the 5 Phase-1-applicable §16 rows are genuinely proven and which (if any)
  required a follow-up code change to prove honestly.

## Parity Ledger Overlap
- `INFRA-335` (`tools/knowledge_gateway_router.py`) — `status: verified`, `priority: P1`,
  `test_path: tests/tools/test_knowledge_gateway_router.py` (exists, passes).
- `INFRA-336` (`tools/knowledge_gateway_packet_assembly.py`) — `status: verified`, `priority: P1`,
  `test_path: tests/tools/test_knowledge_gateway_packet_assembly.py` (exists, passes).
- `INFRA-337` (`tools/knowledge_gateway_mcp.py`) — `status: verified`, `priority: P1`,
  `test_path: tests/tools/test_knowledge_gateway_mcp.py` (exists, passes).
- No `P0` entries touch this ticket's scope — all 3 dependency entries are `P1`, so no ledger
  entry strictly *requires* a passing `test_path` under this repo's P0 rule, but per the
  Authoritative Mechanics Rule any status/behavior change discovered by this ticket's new tests
  (e.g. confirming the "explicit provider failure" field gap) should still update `v2_evidence` on
  the relevant entry once acted on.

## Prior Work
- `tests/tools/test_knowledge_gateway_mcp.py::test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing`
  (L231-242) already proves a **subset** of the "one provider unavailable" row: mocking
  `_run_search` to return `{"error": "index not found"}` and asserting `response["status"] ==
  "PARTIAL"` with a schema-valid response. It does **not** assert anything about *which* provider
  failed being visible in the response (no such field exists to assert on) — this ticket's
  dedicated test must go further, or the gap above must be resolved first.
- `tests/tools/test_knowledge_gateway_packet_assembly.py::test_budget_assembly_failure_returns_smaller_real_list_not_fabricated_content`
  and `..._packet_has_no_new_content_beyond_real_provider_output` (L346-373) already prove the
  §16 token-budget-assembly-failure row **at the packet-assembly unit level** — real evidence
  entries survive, `answer`/`context`/`statements` are emptied, `status == "PARTIAL"`. This
  ticket's own AC calls for proving this against "the real gateway" — an MCP-level test calling
  `_mod._run_knowledge_context(query, budget_tokens=1)` end-to-end (no mocks beyond what's needed
  to guarantee at least one real provider hit) would close that gap cheaply, reusing this existing
  logic rather than re-deriving it.
- `tests/tools/test_knowledge_gateway_packet_assembly.py`'s `_assert_answer_traces_to_statement_evidence()`
  helper (L125-134) is exactly the **structural** (not hardcoded-placeholder-string) fabrication
  guard this ticket's own AC #4 requires — every `answer`/statement text traces to a real
  `evidence_ids` entry that resolves in `packet.evidence`. Reuse this helper (or an MCP-response-level
  equivalent walking `response["statements"]`/`response["evidence"]`) rather than writing a new
  placeholder-string check.
- `tests/tools/test_search_mcp.py::TestRunSearchMissingIndex` and the `mcp-server-test` Makefile
  target establish the existing "prove a provider tool works standalone via its own `--test`
  mode/CLI, no MCP client needed" pattern — the precedent to reuse for the end-to-end
  gateway-down smoke test, rather than attempting to start/stop the real stdio `FastMCP` transport
  (no existing test in this repo drives `knowledge_gateway_mcp.py`'s or `search_mcp.py`'s actual
  `server.run()` stdio loop from within pytest — all existing tests call the underlying `_run_*`
  functions directly in-process).
- `tests/tools/test_knowledge_gateway_router.py::test_symbol_name_delegates_to_graphify_cli_not_a_new_symbol_table`
  (L84-102) is the existing pattern for monkeypatching `subprocess.run` under `_mod.subprocess.run`
  to force a specific graphify CLI outcome deterministically — reuse this monkeypatch point (not a
  new one) for the "one provider unavailable" tests that need to force a `FileNotFoundError` or a
  non-zero-returncode graphify response deterministically.

## Risks and Open Questions
1. **(Blocking for Plan) "Graphify stale" and "Context Search stale" have zero real
   implementation to test against in Phase 1.** `freshness` is hardcoded to `"UNKNOWN"` in
   `assemble_packet()` (packet_assembly.py:636) and nothing anywhere reads/compares a generation
   fingerprint or adapter version to decide staleness. The proposal's own Phase 1 bullet list
   contains no staleness-detection item, and the one doc that specs generation-fallback logic
   (`evidence_cache_identity_contract.md` §4) is cache-identity scoped — Phase 2 territory by this
   epic's own phasing. This ticket's Scope text describes these two rows as "Phase-1-applicable"
   and demands a deterministic test "proving the exact required behavior, not just 'does not
   crash'" — but there is no real behavior to prove; a test that monkeypatches a capability
   descriptor field to simulate a stale signal, calls the real gateway, and asserts nothing
   observably different happens (since no code branches on it) would either (a) trivially pass by
   asserting the absence of behavior that was never claimed to exist — the exact "vacuous test"
   anti-pattern this ticket's own AC #2 explicitly forbids for the cache rows — or (b) require
   Plan to scope in a small amount of real staleness-detection code, which arguably crosses into
   "building the gateway" (explicitly Out of Scope: "TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE's
   job"). **Plan must resolve this explicitly — do not assume it is testable as scoped, and do not
   assume it requires new code; both are live possibilities.**
2. **"One provider unavailable" is only partially implemented; the required "explicit provider
   failure" is silently dropped.** `call_providers_for_routing_decision()` computes a `failures`
   list (context_search error-dict, graphify subprocess timeout) but `PacketAssembly` has no field
   for it, so it never survives past `assemble_packet()`'s local `status` computation. The current
   real behavior is closer to "return partial result with an opaque `status=PARTIAL`" than
   "...with explicit provider failure." Separately, a non-zero-returncode graphify failure (e.g. a
   real crash, not a timeout) is currently classified identically to "the query legitimately found
   nothing" (packet_assembly.py:185-188) — no `failures` entry at all is recorded for that case.
   And a fully-missing `graphify` binary (`FileNotFoundError` from `subprocess.run`) is not caught
   anywhere in the pipeline and would propagate as an unhandled exception rather than degrading
   gracefully. Plan must decide whether proving this row honestly requires: (a) accepting current
   behavior and writing a test that documents the real, weaker semantics (opaque `PARTIAL`, not
   "explicit" failure) with a corresponding `intentional_divergences.md` entry, or (b) scoping in a
   minimal fix (surface `failures`/an `unavailable_providers` field on the response; catch
   `FileNotFoundError` alongside `TimeoutExpired`) as part of this ticket despite the "don't build
   the gateway" Out-of-Scope line, since the required behavior is explicitly enumerated in this
   ticket's own Scope/Acceptance-Criteria text ("'flag code-graph/docs result unavailable' (a real
   field in the response, not a silent omission)").
3. **Whether FastMCP itself converts an uncaught tool-function exception into a graceful
   protocol-level error, or crashes the server process, is unverified.** This matters for the
   "token-budget assembly failure" and "one provider unavailable via FileNotFoundError" scenarios
   if either is left as an uncaught-exception path — the real fail-open guarantee depends on
   `mcp.server.fastmcp.FastMCP`'s own exception-handling behavior, which this investigation did not
   test end-to-end through the real stdio transport (no existing test in this repo drives the real
   transport at all — see Prior Work). Flag as an open question rather than assume either
   direction.
4. **No existing pattern in this repo drives the actual stdio `FastMCP` process from pytest.**
   Every existing gateway/search-mcp test calls the underlying `_run_*` functions in-process. The
   ticket's own end-to-end smoke test AC ("kill/disable the gateway process entirely and confirm an
   agent-like caller can still complete a real workflow unassisted") does not actually require
   starting `knowledge_gateway_mcp.py`'s server at all — it requires *not* starting it and proving
   `search_mcp.py --test` / `graphify query` work with zero import of
   `knowledge_gateway_mcp` (already structurally true — see Current Behavior). This should keep the
   smoke test simple (subprocess calls to the two provider entry points only) rather than inventing
   new stdio-transport test infrastructure. If Plan instead wants to prove "the registered
   `knowledge-gateway` MCP entry itself is down," that would need new transport-level test
   infrastructure this repo does not have a precedent for — worth calling out explicitly rather
   than silently deciding either way.

## Anti-Drift Hazards
- Do not "fix" the staleness gap by inventing a new ad hoc freshness heuristic inside the test
  suite itself (e.g. a test-local function that decides staleness from `adapter_version` strings)
  — any staleness logic belongs in production code (`knowledge_gateway_packet_assembly.py` or the
  router), not smuggled into a test as a stand-in for real behavior. If Plan scopes in real
  code, it must land in the actual module, be covered by that module's own test file, and be
  ledgered — not private test-file logic that only the failopen suite exercises.
- Do not write a "no cache exists, so trivially there is no stale-cache-hit case" test for either
  of the 2 explicitly-deferred cache rows — this repo's own precedent (this ticket's own Scope
  text) explicitly names that exact anti-pattern as forbidden.
- Do not conflate "one provider returned zero results" (a legitimate, non-failure outcome —
  `NegativeClaimSupport`'s own domain, per `docs/plans/knowledge-gateway-mcp-proposal.md` §13.1)
  with "one provider is unavailable/crashed." The current code already conflates these for the
  graphify non-zero-returncode case (see Risk 2) — a failure-semantics test suite must not paper
  over that distinction by testing only the cases current code already handles correctly (missing
  search index, subprocess timeout) while ignoring the case it handles wrong (a real graphify
  crash/non-zero exit).
- Do not let the "gateway process unavailable" smoke test accidentally exercise
  `knowledge_gateway_mcp.py`, `knowledge_gateway_router.py`, or
  `knowledge_gateway_packet_assembly.py` at all (even via import) — the entire point is proving
  the fallback tools work with the gateway module never touched. A test that imports
  `knowledge_gateway_mcp` "just to check something" and then asserts the provider tools also work
  independently is a weaker proof than one that never imports it in that test's process/subprocess
  at all.
- `tools/search_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, and `tools/retrieval_events.py` are frozen per
  their own tickets' explicit scope guards (enforced by existing tests, e.g.
  `test_search_mcp_py_provably_untouched`, `test_module_does_not_edit_knowledge_gateway_router`).
  If Plan decides code changes are needed for Risk 2/3, they belong in
  `tools/knowledge_gateway_mcp.py` and/or `tools/knowledge_gateway_packet_assembly.py` only if that
  module's own ticket (INFRA-336, DONE) is understood to be reopened for this — otherwise a new,
  explicitly-scoped follow-up ticket may be the cleaner path. Flag this choice to Plan rather than
  silently editing a frozen module.
