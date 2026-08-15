---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE

**Revision note:** This plan has been revised in response to an explicit Architecture Review
ruling (`NEEDS_CHANGES`, 2026-08-15) on its prior draft. The prior draft's Design Decision D1 added
a new function, `wrap_gateway_packet_assembly()`, to `tools/retrieval_events.py` specifically so
AC #4's literal wording would pass. The reviewer independently re-verified the underlying factual
claim (none of the 3 named wrappers has an undistorted real call site in this ticket's pipeline)
and confirmed it correct, but ruled that inventing a new 4th wrapper — rather than taking AC #4's
own explicitly-permitted "zero of the 3 apply" honest outcome — is scope creep (the ticket's own
Related Code Areas line names only the 3 pre-existing functions in `tools/retrieval_events.py`,
never "add a function to it") and a check-passing workaround forbidden by CLAUDE.md's Gate
Integrity hard rule. This revision removes the new-wrapper approach entirely and applies the
required cascading corrections throughout. Everything the reviewer explicitly confirmed correct —
the `.mcp.json` entry shape, the cache-specific-field omission reasoning, `tools/search_mcp.py`
remaining untouched, and the `pyproject.toml` dependency conclusion — is unchanged below.

## Summary

Add one new flat module, `tools/knowledge_gateway_mcp.py`, that mirrors `tools/search_mcp.py`'s
own FastMCP pattern exactly (sibling `importlib.util` loading, `_run_*` core-logic functions
shared between the MCP tool and any test/CLI mode, `@server.tool()` thin wrappers, `server.run()`
entry point) and wires two real tools — `knowledge_context` and `knowledge_status` — over the two
frozen Phase 1 dependencies: `tools/knowledge_gateway_router.py::route()` and
`tools/knowledge_gateway_packet_assembly.py::assemble_packet()`. Both tools validate their I/O
against the frozen `docs/engine/contracts/knowledge_gateway_mcp/*.schema.json` files using a real
`jsonschema.Draft7Validator` (+ `RefResolver` for the response schema's cross-file `$ref`s into
`shared_enums.schema.json`), matching AC #1's explicit requirement. A new sibling script
`tools/start_knowledge_gateway_mcp.sh` and one new `.mcp.json` entry register the server, following
`start_search_mcp.sh`'s real current shape (not the two known-stale assertions in
`tests/tools/test_search_mcp.py::TestMcpJson`).

The plan's one substantive architectural call — confirmed by re-reading `tools/retrieval_events.py`
in full and re-verifying every claim in `investigation.md`'s Risk #1 against the real source — is
that **none of the 3 named Wrapper functions (`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`,
`wrap_context_packet_assembly`) can be invoked from this ticket's real call site without either
duplicating frozen setup logic, requiring out-of-scope caching, or measuring the wrong subsystem**.
Per the Architecture Review ruling above, this plan does **not** add a new wrapper function to
`tools/retrieval_events.py` to close this gap. Instead it takes AC #4's own explicitly-permitted
alternative wording ("...or the subset architecturally applicable to a still-uncached Phase 1
gateway... not force-fit ones that don't") and reports that subset as the **empty set**: zero of
the 3 wrappers are invoked from this ticket's real call site. `knowledge_context`'s packet-assembly
call (`assemble_packet()`) and provider calls (`_run_search()`, `match_symbol_name()`) are made
directly and unwrapped — exactly as the frozen `knowledge_gateway_packet_assembly.py` orchestrator
already does them internally. `tools/retrieval_events.py` is not edited by this ticket at all. This
mirrors the precedent already set by `TCK-20260814-KGMCP-MEASUREMENT-BASELINE`'s own "implemented
but not invoked by any live call site" framing for these same 3 functions — that framing remains
accurate at this later Phase 1 point too, since this ticket does not change it.

Because no wrapper emits a timed event for packet assembly, `knowledge_status`'s
`latency_summary_ms.packet_assembly` and `latency_summary_ms.end_to_end` fields move from
"Phase-1-populable" (as the prior draft had them) to the **omitted** list, alongside the
already-correctly-omitted `provider_fallback`/`provider_fallback_rate` and the cache-domain fields
— there is no real call site emitting this data without the (now-rejected) new wrapper. With all 5
`latency_summary_ms` sub-fields Phase-1-unpopulable, the entire `latency_summary_ms` top-level key
is itself omitted from the response (see Step 3), rather than sent as an empty placeholder object.

`knowledge_status`'s cache-specific fields (6 named in the ticket, plus the 2 cache-domain
`latency_summary_ms` sub-fields, plus `provider_fallback_rate` — a 9th field this plan adds to the
omission list on its own evidence, see Design Decision D5) are omitted outright, never null/zero —
verified live that `additionalProperties: false` plus non-nullable `type` declarations make
omission the *only* schema-valid way to represent "not yet available."

## Steps

### Step 1 — Module skeleton: `tools/knowledge_gateway_mcp.py`

**Files:** `tools/knowledge_gateway_mcp.py` (new)

**Change:** Create the flat module following `tools/knowledge_gateway_router.py:1-41`'s and
`tools/search_mcp.py:1-50`'s own precedent exactly:
- `_REPO_ROOT`/`_TOOLS_DIR`/`_CONTRACTS_DIR` path constants (mirror
  `tools/knowledge_gateway_router.py:31-37`).
- Sibling-load helpers for `knowledge_gateway_router.py` and `knowledge_gateway_packet_assembly.py`
  via `importlib.util.spec_from_file_location()`, reusing the exact caching-by-`sys.modules`-key
  pattern already used at `tools/knowledge_gateway_packet_assembly.py:139-156`
  (`_load_search_mcp_module`/`_load_router_module`) — do not re-import via a bare `import
  knowledge_gateway_router`, since no `tools/` subpackage (`__init__.py`) exists anywhere in this
  repo today (confirmed by every sibling module's own docstring, e.g.
  `tools/knowledge_gateway_router.py:14-17`).
- Load the 3 frozen schema files once at module import time:
  `knowledge_context_request.schema.json`, `knowledge_context_response.schema.json` (+
  `jsonschema.RefResolver(base_uri=_CONTRACTS_DIR.resolve().as_uri() + "/", referrer=schema)` for
  its `shared_enums.schema.json` `$ref`s — verified live this resolves correctly, see Design
  Decision D3 below), `knowledge_status_response.schema.json` (no resolver needed — verified live
  it has no cross-file `$ref`).
- `GATEWAY_VERSION`: read `pyproject.toml`'s `[project].version` field
  (`pyproject.toml:8`, currently `"0.1.0"`) via `tomllib.load()` (stdlib, `requires-python = ">=3.11"`
  per `pyproject.toml:6`, verified) at module-import time — reuses the one real version string this
  repo already tracks rather than inventing a second, untracked "gateway version" concept.
- `REPORTED_SCHEMA_VERSION = 1`: hardcode, with a code comment citing
  `knowledge_context_response.schema.json`'s and `knowledge_status_response.schema.json`'s own
  top-level `"schema_version": 1` fields (both files, confirmed by direct read) as the source of
  truth this constant must be kept in sync with.

**Do NOT touch:** `tools/search_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, `tools/retrieval_events.py` — sibling-load and call
only (the latter is not touched or even imported by this module at all, see Step 4).

**Verify:** Module imports cleanly with no import-order collision against the router/packet-assembly
test suites' own sibling-loading (`tests/tools/test_knowledge_gateway_router.py`,
`tests/tools/test_knowledge_gateway_packet_assembly.py` still pass unmodified — Regression Surface).

---

### Step 2 — `knowledge_context` tool: request validation, provider call, response mapping

**Files:** `tools/knowledge_gateway_mcp.py`

**Change:** Implement `_run_knowledge_context(query, mode=None, budget_tokens=None,
changed_paths=None, include_history=None, evidence_detail=None) -> dict`, the core logic function
(mirrors `search_mcp.py::_run_search()`'s "shared by the MCP tool and any test mode" convention,
`tools/search_mcp.py:82-84`):

1. **Request validation (AC #2).** Build a request dict from only the non-`None` supplied
   arguments (never inject a fabricated default for an omitted optional field) and validate it with
   `jsonschema.Draft7Validator(REQUEST_SCHEMA).validate(request_dict)`. Two independent enforcement
   layers exist, and the plan is explicit about which does what (do not conflate them):
   - **Primary, protocol-level enforcement of "extra/forbidden field" rejection**: the
     `@server.tool()`-registered `knowledge_context` function has a **fixed, keyword-only-by-name**
     Python signature matching exactly the request schema's 6 properties
     (`knowledge_context_request.schema.json`'s `properties` list, confirmed: `query`, `mode`,
     `budget_tokens`, `changed_paths`, `include_history`, `evidence_detail`) — no `**kwargs`
     catch-all. A real MCP client's forbidden extra field is rejected by FastMCP's own
     protocol-layer input-schema validation before this function body ever runs; a direct Python
     call (the test-suite's own calling convention, per test_plan.md's `test_search_mcp.py`-mirror
     pattern) with an unexpected keyword raises `TypeError` at the call site, before entering the
     function — this is "FastMCP's own typed-parameter mechanism," the second option test_plan.md's
     test 3 explicitly names.
   - **Secondary, value-level enforcement**: the internal `jsonschema.Draft7Validator` call above
     additionally rejects invalid *values* for a present field (e.g. `mode="not_a_real_mode"`,
     which the fixed-signature/TypeError mechanism cannot catch, since Python does not enforce type
     hints at runtime). On a `jsonschema.ValidationError`, return a schema-conformant `status:
     "ERROR"` response (see step 4 below) rather than letting the exception propagate — this is a
     validation-layer behavior, not a router/assembler-failure pass-through, so it does not
     conflict with this ticket's Out-of-Scope fail-open boundary.
2. **Routing.** Call `_kgr.route(query)` (the frozen router's real signature,
   `tools/knowledge_gateway_router.py:392`, confirmed — `requested_guarantee` stays `None`; nothing
   in the request schema's 6 fields maps to it, and inventing a mapping would be new
   provider-forcing surface §9.1 explicitly forbids).
3. **Packet assembly — direct call, no wrapper (Architecture Review ruling, see Step 4's Design
   Decision D1).** Call `_kgpa.assemble_packet(routing_decision, query, budget_tokens or
   DEFAULT_BUDGET_TOKENS)` directly — the real, frozen signature confirmed at
   `tools/knowledge_gateway_packet_assembly.py:578`. No `tools/retrieval_events.py` wrapper is
   invoked here, and none is added to that module by this ticket: Step 4 re-verifies,
   function-by-function, that none of the 3 pre-existing wrappers (`wrap_hybrid_retrieval`,
   `wrap_retrieval_cache_check`, `wrap_context_packet_assembly`) has an undistorted real call site
   in this pipeline, and this plan reports that finding honestly — AC #4's own explicit "or the
   subset architecturally applicable... not force-fit ones that don't" permission, with that subset
   being the empty set — rather than inventing a new 4th wrapper to force AC #4's literal wording to
   pass. `DEFAULT_BUDGET_TOKENS`: module-level constant (e.g. `4000`) used only when the caller
   omits `budget_tokens` — the request schema does not mark it required, so a sensible default must
   exist somewhere; document this constant's value and rationale (one sentence) in the module.
4. **Response mapping — field-by-field, from `PacketAssembly`'s real dataclass shape
   (`tools/knowledge_gateway_packet_assembly.py:551-566`, confirmed) to
   `knowledge_context_response.schema.json`'s real properties (confirmed by direct read):**
   - `status`, `freshness`, `verification`, `provenance_providers`, `providers_consulted_this_call`,
     `answer`, `budget_requested`, `budget_returned`: direct 1:1 field copy. Verified live (via
     `jsonschema.Draft7Validator`) that `PacketAssembly`'s real string values — `status` ∈
     `{OK, PARTIAL, CONFLICTED}`, `freshness = "UNKNOWN"`, `verification` ∈ `{SUPPORTED,
     UNVERIFIED}` — are all valid members of `shared_enums.schema.json`'s corresponding enums
     (`status`: `[OK, PARTIAL, CONFLICTED, UNVERIFIED, ERROR]`; `freshness`: `[FRESH,
     NEEDS_REVALIDATION, STALE, UNKNOWN]`; `verification`: `[VERIFIED, SUPPORTED, INFERRED,
     UNVERIFIED]`).
   - `mode`: pass through only if the caller supplied it in the request — never fabricate a default
     `mode` value in the response when the request omitted it (the response schema does not require
     `mode`).
   - `statements[]`: map each `Statement(statement_id, text, classification, evidence_ids,
     priority_tier, verification)` (`tools/knowledge_gateway_packet_assembly.py:199-206`) to
     `{statement_id, text, classification, evidence_ids, verification}` — **drop `priority_tier`**,
     it is not a response-schema property (confirmed: the schema's `statements[].items.properties`
     lists only `statement_id`/`text`/`classification`/`verification`/`evidence_ids`) and is
     internal ranking bookkeeping only.
   - `context[]`/`evidence[]`: map each `ContextEntry`/`EvidenceEntry` field-for-field
     (`kind`/`summary`/`source_id`/`path`/`evidence_hash`/`authority` and
     `evidence_id`/`source_id`/`path`/`evidence_hash` respectively — both dataclasses confirmed at
     `tools/knowledge_gateway_packet_assembly.py:209-224`). **Critical, verified-live finding: when
     `path` or `authority` is `None` on the dataclass (always true for graphify-sourced entries —
     `tools/knowledge_gateway_packet_assembly.py:299`/`:305-310` construct both with `path=None`,
     and `authority` is always `None` for every real Phase 1 provider today, confirmed by reading
     `render_candidates()` in full), the response dict must OMIT that key entirely, never set it to
     `null`.** Verified with a real `jsonschema.Draft7Validator` run against the actual response
     schema: `context[].path`/`context[].authority`/`evidence[].path` are all declared `{"type":
     "string"}` with no `null` variant — passing `null` raises `"None is not of type 'string'"`;
     omitting the key validates cleanly (both cases reproduced live, zero errors on omission, 2
     errors on `null`). This is the same class of bug as the `knowledge_status.providers[].
     generation` finding in Step 3 — write one shared helper, e.g. `_omit_none(d: dict) -> dict`
     that strips `None`-valued keys, and apply it to every `context`/`evidence`/`statement` entry
     dict before returning.
   - `conflicts[]`: map each `Conflict(subject, claims, automatic_resolution, recommended_action)`
     and each `ConflictClaim(value, source_id, authority, valid_from, valid_to)`
     (`tools/knowledge_gateway_packet_assembly.py:438-452`) field-for-field — `valid_to` is
     explicitly typed `["string", "null"]` in the response schema (confirmed by direct read), so
     unlike the fields above, a real `None` `valid_to` value passes through as JSON `null`
     unmodified, no omission needed here. In real Phase 1 data `conflicts` is always `[]` (per
     `build_conflicts()`'s own docstring, `tools/knowledge_gateway_packet_assembly.py:496-503`,
     confirmed: neither real provider's return shape exposes a supersession/incompatibility signal
     key) — this mapping exists for completeness/future-correctness, not because it is exercised by
     real Phase 1 data today.
   - `cache`, `cache_key_version`: never populate — Phase 2 concepts, no cache exists (ticket
     Out of Scope).
   - `error`: populate only on the `status == "ERROR"` path from item 1's value-validation failure.

**Do NOT touch:** the router's `requested_guarantee` parameter usage (leave `None`); do not add a
provider-forcing/weighting field anywhere in the request-building code, even internally — §9.1.
`tools/retrieval_events.py` — do not import it, do not call any of its 3 wrapper functions, and do
not add a new function to it (see Step 4).

**Verify:** test_plan.md tests 1 (`test_knowledge_context_tool_real_invocation_validates_against_
response_schema`), 3 (`test_knowledge_context_rejects_forbidden_request_field`), 9
(`test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing`), plus one
new test this plan adds (see Step 8's addendum) asserting `path`/`authority` omission for
graphify-sourced entries.

---

### Step 3 — `knowledge_status` tool: Phase-1 field subset, real provider/branch checks

**Files:** `tools/knowledge_gateway_mcp.py`

**Change:** Implement `_run_knowledge_status() -> dict`. Field-by-field, against
`knowledge_status_response.schema.json`'s real property list (confirmed by direct read:
`gateway_version`, `reported_schema_version`, `providers[]`, `cache_entry_counts[]`,
`cache_hit_rate`, `cache_miss_rate`, `cache_stale_rejection_rate`, `latency_summary_ms{lookup,
evidence_validation, provider_fallback, packet_assembly, end_to_end}`, `provider_fallback_rate`,
`recent_invalidation_reasons[]`, `branch_scope{branch, working_tree_dirty}`, `cache_rebuildable`):

- `gateway_version`, `reported_schema_version`: from Step 1's module-level constants.
- `providers[]`: two entries.
  - `context_search`: `provider_id="context_search"`, `available` = real live check — call
    `_sm._run_health()` (`tools/search_mcp.py:147-165`, confirmed real function, sibling-loaded the
    same way `knowledge_gateway_packet_assembly.py:139-146` already does) and set `available =
    (health["status"] == "ok")`. `generation`: **omit the key entirely** — do not set it to `null`.
    Verified live with `jsonschema.Draft7Validator`: `providers[].generation` is declared `{"type":
    "string"}` (no `null` variant) in the real schema; passing `"generation": None` raises `"None is
    not of type 'string'"`, omitting the key validates cleanly (reproduced live). The frozen
    descriptor's real `adapter_version: null`
    (`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json`,
    confirmed) is genuinely absent information, and the *only* schema-valid way to represent that is
    omission, not a fabricated string and not a type-violating `null`. This corrects
    test_plan.md test 10's literal wording ("absent or explicitly `None`/`null`-equivalent") — write
    the test to assert the key is **absent**, since a `None`-valued key would itself be a schema
    violation the response must never contain.
  - `graphify`: `provider_id="graphify"`, `available` = `shutil.which("graphify") is not None` (a
    real, verifiable CLI-presence check — the router has no dedicated graphify health-check
    function to reuse, confirmed by reading `tools/knowledge_gateway_router.py` in full; this is a
    new, narrow, honest check, not a fabricated `True`). `generation =
    "graphify-cli-0.8.39"` — read live from
    `docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_graphify.json`'s real
    `adapter_version` field (confirmed non-null, unlike context_search's).
- `cache_entry_counts`, `cache_hit_rate`, `cache_miss_rate`, `cache_stale_rejection_rate`,
  `recent_invalidation_reasons`, `cache_rebuildable`: **omit all 6** — the ticket's own
  explicitly-named cache-specific fields, no cache exists.
- `latency_summary_ms` — **omit the entire top-level key.** All 5 sub-fields (`lookup`,
  `evidence_validation`, `provider_fallback`, `packet_assembly`, `end_to_end`) are
  Phase-1-unpopulable, for the reasons below; with nothing left to populate, sending an empty `{}`
  object would itself be a fabricated placeholder this plan's own never-fabricate/never-placeholder
  discipline forbids (same reasoning as the 6 cache-specific top-level fields above). Verified
  against the real schema (`docs/engine/contracts/knowledge_gateway_mcp/
  knowledge_status_response.schema.json:8`, confirmed): the top-level `required` list is only
  `["gateway_version", "reported_schema_version"]`, so omitting `latency_summary_ms` entirely is
  schema-valid.
  - `lookup`, `evidence_validation`: cache-domain concepts per `measurement_baseline_contract.md`
    §2.1/§2.2 (confirmed by direct read: §2.1's own "Live-precedent status" names
    `wrap_retrieval_cache_check()` as the closest instrumentation-shape precedent, a cache-check
    wrapper; §2.2 states "no existing wrapper... this measurement point is a pure definition
    today"), matching investigation.md Risk #3 exactly.
  - `provider_fallback`: `measurement_baseline_contract.md` §2.3 (confirmed by direct read,
    `:88-100`) states explicitly "no existing wrapper; this concept has no timed call site anywhere
    in this repository today. Pure definition — no live number exists, and none is fabricated."
    This ticket's direct, unwrapped `assemble_packet()` call (Step 2, item 3) does not create a
    provider-fallback call site either — no cache exists to fall back from.
  - `packet_assembly`, `end_to_end`: **corrected per Architecture Review ruling — omitted, not
    populated.** The prior draft of this plan populated these two fields from real historical
    `agent-monitoring/events.jsonl` rows emitted by a new wrapper function; that wrapper has been
    removed from this plan entirely (see Step 4's Design Decision D1). With no wrapper timing
    `assemble_packet()`, there is no real, durable, cross-process data source to compute a mean
    latency from — an in-process transient timer around the direct call would fabricate a
    fixture-shaped number that `measurement_baseline_contract.md` §2.6 explicitly forbids
    presenting as if it were the real gateway's number. Per §2.5's reconciliation rule (`:126-131`,
    confirmed: "end-to-end latency is defined as the sum of whichever of §2.1–§2.4 actually execute
    for a given request — never a 6th, independently-measured number"), since none of §2.1–§2.4
    execute for any real Phase 1 call (no cache, no wrapper), `end_to_end` has nothing to sum and
    must also be omitted, not independently timed. **This corrects test_plan.md test 4's stated
    expectation that `latency_summary_ms.packet_assembly`/`end_to_end` are "Phase-1-populable" —
    they are not.** Flag this test_plan.md deviation explicitly in Implementation Notes at Implement
    time, alongside the pre-existing `provider_fallback` deviation.
- `provider_fallback_rate`: **omit** — this plan extends investigation.md Risk #3's reasoning (which
  only named the 2 `latency_summary_ms` sub-fields) to this field too: a "fallback rate" is only a
  meaningful concept relative to a cache-hit alternative to fall back from (per §2.3's own framing,
  "falling back to live `PROVIDER_GENERATION` evidence... when no finer-grained cached evidence
  fingerprint is available or valid") — with zero cache in Phase 1, there is no fallback/non-fallback
  distinction to compute a rate over, so any value here would be fabricated (either a meaningless
  "100%" or an equally meaningless "undefined 0%"). Flag this as a plan-level addition beyond the
  ticket's own explicit 6-field list, justified by the same substance-over-name principle
  investigation.md Risk #3 already established.
- `branch_scope`: real `subprocess.run(["git", "branch", "--show-current"], cwd=_REPO_ROOT,
  capture_output=True, text=True)` for `branch`, and `subprocess.run(["git", "status",
  "--porcelain"], ...)` with non-empty stdout for `working_tree_dirty` — list-form args, no
  `shell=True`, matching `tools/knowledge_gateway_router.py:107-113`'s own subprocess convention
  exactly.

**Do NOT touch:** do not add a `cache`-namespaced companion field anywhere in the response (schema's
`additionalProperties: false` forbids any field not in its property list, confirmed by direct read —
there is no schema-valid way to add a sibling "omission marker" field; document the omission in code
comments/docstring only, per investigation.md Risk #2's own resolution).

**Verify:** test_plan.md tests 2, 4 (corrected per above), 10 (corrected per above).

---

### Step 4 — Wrapper-function resolution: confirm and report that zero of the 3 named wrappers apply; `tools/retrieval_events.py` stays untouched

**Files:** none — this is a documentation/decision step; no source file is edited.

**Change:** This is the plan's Design Decision D1 (full reasoning below), **revised per explicit
Architecture Review ruling (`NEEDS_CHANGES`, 2026-08-15)** on the prior draft of this plan. The
prior draft proposed adding a new function, `wrap_gateway_packet_assembly()`, to
`tools/retrieval_events.py` specifically so AC #4's literal wording ("...are invoked") would have
something to point at. The reviewer independently re-verified the underlying factual claim — none
of the 3 named wrappers has an undistorted real call site in this ticket's pipeline — and confirmed
it correct, but ruled that inventing a 4th wrapper to make the AC's literal wording pass, rather
than taking the AC's own explicitly-permitted "zero of the 3 apply" honest outcome, is scope creep
(the ticket's own Related Code Areas line says "tools/retrieval_events.py (3 Wrapper functions to
wire in)", naming only the 3 existing functions, never "add a function to it") and a check-passing
workaround forbidden by CLAUDE.md's Gate Integrity hard rule.

This plan now does the following instead: **report, with the same function-by-function evidence
already derived, that zero of the 3 named wrappers apply — and add no code to
`tools/retrieval_events.py` at all.** `knowledge_context`'s real call path (Step 2) calls
`assemble_packet()` and the two provider functions (`_run_search()`, `match_symbol_name()`)
directly and unwrapped, exactly as the frozen `knowledge_gateway_packet_assembly.py::
call_providers_for_routing_decision()` orchestrator already does internally. No event is emitted to
`agent-monitoring/events.jsonl` for this call path by this ticket.

**Design Decision D1 — full reasoning for why none of the 3 named wrappers are used, re-verified
against the real source (not merely trusting investigation.md):**
- `wrap_hybrid_retrieval()` (`tools/retrieval_events.py:154-212`, confirmed by full read): hardcodes
  `from hybrid_retrieval import candidate_k, hybrid_fuse_and_filter` (`:173`) and requires
  caller-supplied `conn`/`query_vec_bytes`/`query_tokens`/`bm25_obj`/`bm25_doc_ids`/`top_k` via
  `**hybrid_kwargs`, passed straight to `hybrid_fuse_and_filter(**hybrid_kwargs)` (`:176`). The only
  real caller in this repository that builds this exact state is
  `search_mcp.py::_run_search()` (`tools/search_mcp.py:100-113`, confirmed: opens its own SQLite
  connection, loads `sqlite_vec`, embeds the query, tokenizes it — all internal, never returned to
  any caller). `knowledge_gateway_packet_assembly.py::call_providers_for_routing_decision()` calls
  `_sm._run_search(query_text)` as a single opaque call (`tools/knowledge_gateway_packet_assembly.py:
  172-173`, confirmed) — it has zero access to any of `wrap_hybrid_retrieval`'s required kwargs.
  Additionally confirmed: none of `measurement_baseline_contract.md`'s 5 latency measurement points
  (§2.1–§2.5, full section read) cites `wrap_hybrid_retrieval()` at all — it corresponds to no
  Phase 1 gateway measurement concept, not merely "hard to wire."
- `wrap_retrieval_cache_check()` (`:223-288`, confirmed by full read): dispatches to
  `check_index_cache`/`check_query_cache`/`check_packet_cache` from `tools/retrieval_cache.py`. This
  is the real precedent `measurement_baseline_contract.md` §2.1 (Lookup latency) itself names
  (`:59-63`, confirmed) — but no cache exists in Phase 1 (explicit Out of Scope: "Any caching"), so
  there is nothing for this wrapper to check.
- `wrap_context_packet_assembly()` (`:299-358`, confirmed by full read): imports `assemble_context_
  packet` from `tools/context_packet_assembler.py` (`:322`, confirmed) — a distinct module (built
  for `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`) whose real signature (`packet_id, corpus_generation,
  retrieval_version, budget_requested, included_candidates: list[Candidate], excluded=()`) is
  structurally incompatible with this epic's own `assemble_packet(routing_decision, query_text,
  budget_requested)` (`tools/knowledge_gateway_packet_assembly.py:578`, confirmed). Calling the real
  `wrap_context_packet_assembly()` on real `context_packet_assembler.py` data would produce a
  latency number for a subsystem this ticket's actual `knowledge_context` response never touches —
  the textbook force-fit the ticket's own AC #4 explicitly warns against.

**This resolution's relationship to AC #4's literal wording:** AC #4 names the 3 pre-existing
functions ("`wrap_hybrid_retrieval`/`wrap_retrieval_cache_check`/`wrap_context_packet_assembly` (or
the subset architecturally applicable...) are invoked"). This plan reports that subset as the
**empty set**, with the same re-verified, function-by-function evidence above — this is the AC's
own explicitly-permitted honest outcome, not a workaround, and is exactly what an Architecture
Review pass confirmed should be reported instead of a new-wrapper workaround. This mirrors the
precedent already set by `TCK-20260814-KGMCP-MEASUREMENT-BASELINE`'s own "implemented but not
invoked by any live call site" framing for these same 3 functions (`measurement_baseline_contract.
md` §2.4, `:112-113`, confirmed) — that framing remains accurate at this later Phase 1 point too,
since this ticket does not change it. Flag this explicitly for Review/Verify-phase confirmation —
a zero-invocation finding is still a substantive claim that must be checked, not rubber-stamped.

**Do NOT touch:** `tools/retrieval_events.py` — not edited at all by this ticket. Its 3 existing
wrapper functions, `RETRIEVAL_EVENT_FIELDS`, `retrieval_event_schema_version`,
`emit_retrieval_event()`, `compute_adequacy_verdict()`, `NOISY_RATIO_THRESHOLD` are all untouched —
zero diff, verified by Step 6/8's git-diff guard test, which includes `tools/retrieval_events.py` in
its banned-paths list (see Step 6).

**Anti-Drift Note for a future editor:** do not resurrect a "4th wrapper," or otherwise add any code
to `tools/retrieval_events.py`, to make AC #4's literal wording appear to pass — the Architecture
Review ruling above is explicit and binding on this point. If a genuine live call site for
packet-assembly latency measurement is ever needed, wire it as its own scoped follow-up ticket (see
Anti-Drift Notes at the bottom of this plan), not as a reactive patch to this ticket's AC #4.

**Verify:** test_plan.md test 7, corrected per the Architecture Review ruling to prove the **honest
negative finding** rather than a positive invocation —
`test_wrapper_functions_genuinely_not_applicable_zero_invoked`: `monkeypatch.setattr` spies on all 3
of `retrieval_events.wrap_hybrid_retrieval`/`wrap_retrieval_cache_check`/
`wrap_context_packet_assembly`, invokes a real `knowledge_context` call, and asserts
`spy.call_count == 0` for each of the 3; also assert `git diff --stat HEAD --
tools/retrieval_events.py` is empty (folds into Step 6/8's frozen-file guard test). Plus
`tests/tools/test_retrieval_events.py`'s existing suite, unmodified, still passing (Regression
Surface).

---

### Step 5 — `tools/start_knowledge_gateway_mcp.sh`

**Files:** `tools/start_knowledge_gateway_mcp.sh` (new)

**Change:** Byte-for-byte structural mirror of `tools/start_search_mcp.sh` (confirmed by full read):
same venv-priority-list pattern (`$REPO_ROOT/.venv/bin/python3`, `/home/vboxuser/Work/venv/bin/
python3`, `command -v python3`), only the final `exec` target changed to
`"$SCRIPT_DIR/knowledge_gateway_mcp.py" "$@"`. `chmod +x` the new file (verify `start_search_mcp.sh`
is itself executable and match its permission bits).

**Do NOT touch:** `tools/start_search_mcp.sh` itself.

**Verify:** test_plan.md test 5 (`.mcp.json` shape assertion covers the script path indirectly);
manually confirm `bash tools/start_knowledge_gateway_mcp.sh --test < /dev/null` at least reaches
Python (script-level smoke check, not a formal pytest case).

---

### Step 6 — `.mcp.json` new entry

**Files:** `.mcp.json`

**Change:** Add exactly one new key under `mcpServers`, following the real current
`knowledge-search` entry's shape exactly (confirmed by direct read of `.mcp.json`: `command:
"bash"`, `args: ["tools/start_search_mcp.sh"]`, `env: {}`, `description: "..."`):

```json
"knowledge-gateway": {
  "command": "bash",
  "args": ["tools/start_knowledge_gateway_mcp.sh"],
  "env": {},
  "description": "Knowledge Gateway MCP — routed, provenance-tracked context packets over Context Search and Graphify (Phase 1: read-only, uncached)"
}
```

Merge into the existing file (2 existing keys: `knowledge-search`, `github` — confirmed by direct
read), never overwrite — matches `stored_artifacts/TCK-20260612-LOCAL-CTX-MCP/investigation.md`'s
documented merge-not-overwrite convention.

**Do NOT touch:** the existing `knowledge-search` or `github` entries — zero-diff on those two keys.

**Verify:** test_plan.md test 5 (`test_mcp_json_gains_exactly_one_new_server_entry`) and test 6
(`test_search_mcp_py_provably_untouched`, extended per Anti-Drift Test Guards to also assert
`tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, **and
`tools/retrieval_events.py`** are untouched via the same `git diff --stat HEAD` mechanism, confirmed
real precedent at `tests/tools/test_kgmcp_measurement_baseline.py:343-357` — note that, per the
Architecture Review ruling reversing the prior draft's exclusion, **this ticket's own frozen-file
guard MUST include `tools/retrieval_events.py`** in its banned-paths list: this ticket does not edit
that file at all, so it rejoins the fully-frozen set alongside the router and packet-assembly
modules).

---

### Step 7 — Register both tools on a `FastMCP` server, update the stale Phase-0 guard test

**Files:** `tools/knowledge_gateway_mcp.py`, `tests/tools/test_knowledge_gateway_contract_schemas.py`

**Change:**
- In `tools/knowledge_gateway_mcp.py`'s `_run_mcp_server()` (mirrors `search_mcp.py:210-256`
  exactly): `server = FastMCP("knowledge-gateway")`; register `knowledge_context` and
  `knowledge_status` via `@server.tool()` on thin wrappers around `_run_knowledge_context()`/
  `_run_knowledge_status()` (same "thin wrapper calls the shared `_run_*` function" pattern as
  `search_mcp.py:224-253`); **register nothing else** — no `knowledge_learn`, no
  `knowledge_promote`, no `knowledge_verify`, no invalidation tool (§9.3, AC #5).
- Update `tests/tools/test_knowledge_gateway_contract_schemas.py::
  test_no_live_gateway_tool_code_or_mcp_registration_introduced` (`:338-351`, confirmed exact
  current assertions by direct read: `.mcp.json`'s `mcpServers` keys `== {"knowledge-search",
  "github"}`, and no `tools/*.py` file contains `def knowledge_context(` / `def knowledge_status(`).
  This test **must** start failing once Step 6/Step 2/Step 3 land, and per test_plan.md's Regression
  Surface note this is expected and must be fixed in the same change: update the `mcpServers`
  key-set assertion to `{"knowledge-search", "github", "knowledge-gateway"}`, and replace the
  "no live tool code exists" assertion with the inverse — assert `tools/knowledge_gateway_mcp.py`
  now *does* define both, confirming Phase 0's contract-only guarantee has correctly expired at
  Phase 1. Rename the test to reflect its new meaning (e.g.
  `test_phase_1_gateway_tool_code_and_mcp_registration_now_exist`) rather than leaving a stale name
  describing behavior the test no longer checks.

**Do NOT touch:** any other test in `test_knowledge_gateway_contract_schemas.py` — only this one
test function changes.

**Verify:** `tests/tools/test_knowledge_gateway_contract_schemas.py`'s full suite passes after the
edit (Regression Surface); test_plan.md test 8
(`test_only_knowledge_context_and_knowledge_status_registered`), using
`server._tool_manager._tools.keys()` — verified live this is the real, correct introspection path
for the installed `mcp` package (confirmed: `FastMCP._tool_manager` is a `ToolManager` whose
`_tools` dict maps tool name → `Tool` object; `Tool.fn` is the original undecorated callable,
confirmed live — use `server._tool_manager._tools["knowledge_context"].fn` for the "call the
underlying callable directly" test-calling convention test_plan.md specifies).

---

### Step 8 — New test file `tests/tools/test_knowledge_gateway_mcp.py`

**Files:** `tests/tools/test_knowledge_gateway_mcp.py` (new)

**Change:** Implement all 10 tests from test_plan.md, with the corrections established in Steps
2–4 above (do not implement test_plan.md's literal wording where this plan has found and cited a
factual correction):
1. `test_knowledge_context_tool_real_invocation_validates_against_response_schema` — as specified.
2. `test_knowledge_status_tool_real_invocation_validates_against_response_schema` — as specified.
3. `test_knowledge_context_rejects_forbidden_request_field` — assert `TypeError` on direct-call with
   an unexpected kwarg (Step 2's primary mechanism), per the real behavior verified in Step 2, not
   an assumed jsonschema-based rejection path.
4. `test_knowledge_status_omits_all_cache_specific_fields_enumerated` — **extend the field list**
   beyond test_plan.md's 8 fields to include `provider_fallback_rate` (Step 3's D5 addition), and
   **correct** the assertions per the Architecture Review ruling: assert `latency_summary_ms` is
   **absent** as a top-level key entirely (not present, not `{}}` — Step 3's corrected disposition),
   and assert the corrected Phase-1-populable field list reads exactly
   `{gateway_version, reported_schema_version, providers, branch_scope}` — this removes
   `latency_summary_ms.packet_assembly`/`latency_summary_ms.end_to_end` from the populated-fields
   list (this revision's correction, cited against `measurement_baseline_contract.md` §2.4's
   still-accurate "implemented but not invoked" language and §2.5's reconciliation rule) in addition
   to `latency_summary_ms.provider_fallback` (already corrected in the prior draft, cited against
   §2.3).
5. `test_mcp_json_gains_exactly_one_new_server_entry` — as specified, asserting the real
   `bash`+wrapper-script shape.
6. `test_search_mcp_py_provably_untouched` — extended per Step 6 to also cover the router, the
   packet-assembly module, **and `tools/retrieval_events.py`** (all four are fully frozen for this
   ticket).
7. `test_wrapper_functions_genuinely_not_applicable_zero_invoked` (renamed from test_plan.md's
   placeholder `test_wrapper_function_real_invocation_proven`, per the Architecture Review ruling
   reversing the prior draft's new-wrapper approach) — spies on all 3 of
   `retrieval_events.wrap_hybrid_retrieval`/`wrap_retrieval_cache_check`/
   `wrap_context_packet_assembly`, invokes a real `knowledge_context` call, and asserts
   `spy.call_count == 0` for each of the 3 — the honest-negative proof AC #4's own "subset
   architecturally applicable" hedge explicitly permits. Also asserts `git diff --stat HEAD --
   tools/retrieval_events.py` is empty.
8. `test_only_knowledge_context_and_knowledge_status_registered` — as specified, using
   `server._tool_manager._tools.keys()`.
9. `test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing` — as
   specified.
10. `test_provider_context_search_adapter_version_null_not_fabricated` — **correct** the assertion
    from "absent or explicitly `None`" to "absent" only (Step 3's finding: a `None`-valued
    `generation` key would itself fail schema validation).

**One new test this plan adds, not in test_plan.md's original 10** (covers the `path`/`authority`
omission finding from Step 2):
11. `test_knowledge_context_omits_null_path_and_authority_never_returns_null_for_typed_string_fields`
    — build a real response from a graphify-only routing decision (or a monkeypatched provider
    call returning a graphify-shaped result) and assert `path`/`authority` keys are absent from the
    resulting `context[]`/`evidence[]` entries, never present with value `null`. Justification: this
    is the direct, symmetric counterpart to test 10's `knowledge_status` finding, applied to
    `knowledge_context`'s response — both are instances of the same underlying rule ("a schema field
    typed as plain `string` with no `null` variant can only be satisfied by omission, never by
    `null`") discovered by this plan's own live `jsonschema` verification, not by test_plan.md
    (written before this plan's Step 2 fact-check).

**Do NOT touch:** any pre-existing test file other than the one update in Step 7.

**Verify:** `.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -v` — all pass.
Then the full regression command from test_plan.md's Scoped Pytest Commands section.

## Scope Guards

- **Never edit `tools/search_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, or `tools/retrieval_events.py`.** All four are
  frozen for this ticket: the first three are DONE/frozen dependencies, imported and called only;
  `tools/retrieval_events.py` is frozen by this revision (Architecture Review ruling — the prior
  draft's plan to add a new function to it has been removed entirely, see Step 4). Verified empty
  diff on all four is a hard test assertion (Step 6/Step 8 test 6).
- **Never add a new function to `tools/retrieval_events.py`, and never invoke any of its 3 existing
  wrapper functions from this ticket's real call site.** Architecture Review ruling: adding a 4th
  wrapper specifically to satisfy AC #4's literal wording is scope creep and a check-passing
  workaround. This ticket reports, honestly, that zero of the 3 pre-existing wrappers
  (`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, `wrap_context_packet_assembly`) apply to
  its real call site — per AC #4's own explicit permission — rather than inventing a new one.
- **Never register `knowledge_learn`, `knowledge_promote`, `knowledge_verify`, or any invalidation
  tool.** Exactly 2 tools registered, enforced by Step 8 test 8.
- **Never build any caching** — no `retrieval_cache.db` schema/migration, no in-process memoization
  of packet results, no import of `tools/retrieval_cache.py` anywhere in the new module.
- **Never touch `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md`.** The `.mcp.json`
  registration is the only activation mechanism.
- **Never build the full §16 fail-open/failure-semantics test matrix** — `TCK-20260815-KGMCP-P1-
  FAILOPEN-TESTS`'s job; this ticket only needs Step 2's item 4 (unswallowed status pass-through).
- **Never silently return `0`/`null`/an empty placeholder (including an empty `{}` object) for a
  cache-specific or otherwise not-yet-real `knowledge_status` field** — omission only, per Step 3's
  full field-by-field disposition table, including the now-fully-omitted `latency_summary_ms`
  object.
- **Never edit `pyproject.toml`** — Design Decision D2 (below) establishes `jsonschema`/
  `referencing` are already transitively available via the declared `mcp>=1.0.0` dependency in the
  `search-mcp` extra; no new dependency declaration is needed or should be added.
- **Never edit `tests/tools/test_search_mcp.py`** — its 2 pre-existing `TestMcpJson` failures
  (`test_command_is_python3`, `test_args_point_to_search_mcp`) are out-of-scope, not this ticket's
  fault or job.
- **`docs/parity_ledger/infrastructure.yaml`, `measurement_baseline_contract.md`, and
  `knowledge-gateway-mcp-proposal.md` are not edited during Implement** — deferred to the
  Document-Update/Parity phases per this plan's own notes below; Implement should not touch
  `docs/` except where a Step above explicitly names a test file under `tests/`.

## Dependency Map

- Step 1 (skeleton) must land before Steps 2, 3, 7 (all reference its constants/loaders).
- Step 4 (wrapper-function resolution) is a documentation/decision step only — it edits no source
  file and has no code dependency on any other step. Its function-by-function evidence should be
  finalized before Step 2 is implemented, since Step 2 item 3's direct-call design and Step 8 test
  7's honest-negative test both rest on it, but there is no hard ordering requirement.
- Steps 5 and 6 are independent of 1–4 and of each other's internals, but Step 6's `.mcp.json` entry
  should reference Step 5's script path, so land Step 5 first for a working end-to-end smoke check
  (not a hard technical dependency — the JSON entry is valid either order).
- Step 7's test-file update depends on Steps 2, 3, 6 all being complete (it asserts the post-ticket
  end state).
- Step 8 depends on all of Steps 1–7 being complete; it is the final verification step.

All other step pairs are independent and can be implemented in any relative order within the
constraints above.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — real, invocable `knowledge_context`/`knowledge_status` tools; response validated against frozen schemas via real `jsonschema` validator | Steps 1, 2, 3, 7 | test_plan.md tests 1, 2 |
| AC #2 — `knowledge_context` request validation rejects forbidden fields | Step 2 (item 1) | test_plan.md test 3 |
| AC #3 — `knowledge_status` Phase 1 response never fabricates a cache-specific field value | Step 3 | test_plan.md test 4 (corrected field list, see Step 8) |
| AC #4a — `.mcp.json` gains exactly one new entry; `search_mcp.py` provably untouched | Steps 5, 6 | test_plan.md tests 5, 6 (extended to router/packet-assembly/retrieval_events, see Step 6) |
| AC #4b — Wrapper function(s) invoked from the real call site, with proof of real invocation | Step 4 (honest finding: zero of the 3 named wrappers apply — the AC's own explicitly-permitted "subset architecturally applicable" outcome, confirmed correct by Architecture Review; no new wrapper is added) | test_plan.md test 7 (corrected — proves zero invocation, see Step 8) |
| AC #5 — exactly `{knowledge_context, knowledge_status}` registered, no learn/promote/verify/invalidation tool | Step 7 | test_plan.md test 8 |

**Explicit flag for Verify/Finalize phase:** AC #4b is satisfied via the empty-subset outcome AC #4's
own wording explicitly permits, re-verified against the real source by both this plan and an
independent Architecture Review pass. This is not a silent gap — Step 4's function-by-function
evidence and test 7's honest-negative proof must both be confirmed at Verify, not merely
rubber-stamped. Do not treat a future "let's just add the wrapper" suggestion as a simplification —
it was explicitly reviewed and rejected.

## Anti-Drift Notes

- **Do not force-fit `wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, or
  `wrap_context_packet_assembly` onto this ticket's pipeline, and do not add a new 4th wrapper
  function to `tools/retrieval_events.py` either.** Design Decision D1 re-verified, from the real
  source, that none of the 3 has an undistorted real call site here — and an explicit Architecture
  Review ruling (2026-08-15) rejected this plan's earlier draft, which had proposed a new
  `wrap_gateway_packet_assembly()` function specifically to make AC #4's literal wording pass. That
  was ruled scope creep and a check-passing workaround. If a future editor is tempted to "re-add" a
  wrapper to "simplify" AC #4, re-read Step 4's full citations and this ruling first — this is a
  deliberate, twice-reviewed rejection, not an oversight.
- **Never populate `knowledge_status.providers[].generation` with `null`** — the schema types it as
  plain `string`; omit the key for `context_search` (whose `adapter_version` is genuinely `null`).
  `null` is not the same as "absent" for this field and will fail schema validation.
- **Never populate `knowledge_context`'s `context[].path`/`context[].authority`/`evidence[].path`
  with `null`** when the underlying dataclass field is `None` (always true for graphify-sourced
  entries today) — same class of bug as the previous bullet, verified live with the real schema and
  a real `jsonschema.Draft7Validator` run (see Step 2, item 4).
- **`latency_summary_ms` is omitted in its entirety in Phase 1 — all 5 sub-fields, including
  `packet_assembly`/`end_to_end`, corrected per the Architecture Review ruling.** The prior draft
  populated `packet_assembly`/`end_to_end` from a new wrapper's emitted events; with that wrapper
  removed, no real data source exists for either field, and `measurement_baseline_contract.md`
  §2.5's "never a 6th, independently-measured number" rule forbids computing `end_to_end` any other
  way. Do not resurrect an in-process timer around the direct `assemble_packet()` call to "fill in"
  these fields.
- **`latency_summary_ms.provider_fallback` and `provider_fallback_rate` must stay omitted in Phase
  1** — no cache exists, so no fallback concept has meaning yet; this contradicts test_plan.md's
  literal test 4 wording (which listed `provider_fallback` as Phase-1-populable) — that wording is
  corrected by this plan, cited against `measurement_baseline_contract.md` §2.3's own explicit "no
  live number exists, and none is fabricated" statement.
- **`context_search`'s `adapter_version: null` is the genuine, correct real value** — never "fixed"
  by fabricating a version string for it.
- **`tools/retrieval_events.py` is fully frozen for this ticket — zero diff, no exceptions.** Unlike
  the prior draft (which carved out an exception for a new wrapper function), this revised plan adds
  nothing to this file. It is included in the same frozen-file git-diff guard test as
  `tools/search_mcp.py`, `tools/knowledge_gateway_router.py`, and
  `tools/knowledge_gateway_packet_assembly.py` (Step 6/8's test 6).
- **Forward-looking observation (not built by this ticket).** A genuine future path exists for
  wiring real, durable packet-assembly latency measurement: a follow-up ticket could add a
  narrowly-scoped wrapper (or extend `knowledge_gateway_packet_assembly.py` itself, if that module
  is ever unfrozen) that times `assemble_packet()` and emits a real event, at which point
  `knowledge_status.latency_summary_ms.packet_assembly`/`end_to_end` could be populated from genuine
  historical data. This is noted here for the epic owner's consideration as a possible scope
  amendment or child ticket — it must not be built by this ticket.

## Design Decisions

**D1 — Wrapper-function resolution (revised per Architecture Review ruling, 2026-08-15).** Covered
in full under Step 4 above. The original draft of this plan proposed adding a new 4th wrapper
function, `wrap_gateway_packet_assembly()`, to `tools/retrieval_events.py`. An Architecture Review
pass confirmed the underlying factual claim (none of the 3 named wrappers applies to this ticket's
real call site) but ruled the new-wrapper approach itself out of scope and a check-passing
workaround. This plan now reports, honestly, that zero of the 3 named wrappers apply — the AC
#4-permitted empty-subset outcome — and adds no code to `tools/retrieval_events.py`.

**D2 — `pyproject.toml` dependency declaration for `jsonschema`/`referencing`.** Verified live: `pip
show jsonschema` in `.venv` reports `Required-by: mcp` (confirmed), and `pip show referencing`
reports `Required-by: jsonschema, jsonschema-specifications` (confirmed) — both are already
transitively pulled in by the `mcp>=1.0.0` dependency already declared in `pyproject.toml`'s
`[project.optional-dependencies].search-mcp` group (`pyproject.toml`, confirmed by direct read). This
means `jsonschema`/`referencing` are **not genuinely missing** from the dependency graph — anyone who
installs `pip install -e '.[search-mcp]'` (already the documented install path for the FastMCP
server pattern this ticket mirrors, per `tools/search_mcp.py`'s own module docstring) already gets
both. **No `pyproject.toml` edit is needed or should be made.** Add a one-line code comment in
`tools/knowledge_gateway_mcp.py` at the `import jsonschema` statement noting this transitive-
availability fact, so a future reader does not wrongly conclude the import is undeclared/fragile.

**D3 — `jsonschema.RefResolver` vs. `referencing`-library-based resolution.** Use the deprecated
`RefResolver` API (`jsonschema.RefResolver(base_uri=..., referrer=...)`) — verified live it correctly
resolves `knowledge_context_response.schema.json`'s relative `$ref`s into `shared_enums.schema.json`.
This matches `tests/tools/test_knowledge_gateway_contract_schemas.py`'s own established real-validator
pattern (per investigation.md) and is the simplest correct option; the newer `referencing`-library
API is more future-proof but adds meaningfully more code for zero behavioral difference at this
ticket's scope. If `jsonschema` drops `RefResolver` in a future major version, that is a
forward-looking maintenance concern for a later ticket, not this one.

**D4 — Never-null-for-typed-string-fields.** Both `knowledge_status.providers[].generation` and
`knowledge_context`'s `context[]`/`evidence[]` `path`/`authority` fields are typed plain `string`
(no `null` variant) in their respective frozen schemas. Every dataclass field this plan maps from
that can genuinely be `None` in real Phase 1 data must be **omitted from the response dict**, never
passed through as JSON `null`. This is verified live (not inferred) for both cases via direct
`jsonschema.Draft7Validator` runs reproduced in Steps 2 and 3 above. A single shared `_omit_none()`
helper should be used for all such mappings, to avoid re-deriving this rule ad hoc at each call site.

**D5 — `knowledge_status` field-population source of truth (revised per Architecture Review
ruling).** `latency_summary_ms.packet_assembly`/`end_to_end` are **omitted**, not populated — the
prior draft of this plan sourced them from real historical rows in `agent-monitoring/events.jsonl`
emitted by a new wrapper (D1's rejected approach); with that wrapper removed, no real data source
exists for either field in Phase 1, so both are omitted per the same never-fabricate discipline as
the cache fields. This resolves investigation.md Risk #4's option (b) as **not currently available**
(it depended on Risk #1 being resolved in favor of a new/existing wrapper, which the Architecture
Review ruling forecloses for this ticket) rather than as chosen. `provider_fallback_rate` remains
omitted outright (no cache-relative concept exists in Phase 1) — unchanged from the prior draft.

## Docs to Update (Document-Update Phase — not part of Implement)

- **`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §2.3
  (Provider-fallback latency)**: **no substantive edit needed** — its current text ("no existing
  wrapper; this concept has no timed call site anywhere in this repository today... no live number
  exists, and none is fabricated") remains accurate even after this ticket lands, since this
  ticket's direct, unwrapped `assemble_packet()` call (Step 2, item 3; Step 4's Design Decision D1)
  does not create a provider-fallback call site (no cache exists to fall back from). Add one short
  reconfirming sentence/footnote noting that Phase 1's `knowledge_context`/`knowledge_status` tool
  surface (this ticket, `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`) was evaluated and does not change
  this section's status, so a future reader does not have to re-derive this from scratch.
- **§2.4 (Packet-assembly latency)**: **no substantive edit needed — reconfirmed accurate at this
  Phase 1 point, per Architecture Review ruling.** Its current "Live-precedent status" paragraph
  (`:112-113`, confirmed: `wrap_context_packet_assembly()` is "implemented but not invoked by any
  live call site... direct precedent for this measurement point's instrumentation shape") remains
  true after this ticket lands — this ticket does not add a new wrapper and does not wire a real
  call site for packet-assembly latency measurement (the prior draft's plan to do so was rejected by
  Architecture Review; see Design Decision D1 and Step 4). Add one short reconfirming
  sentence/footnote, mirroring the §2.3 footnote above, noting that Phase 1's
  `knowledge_context`/`knowledge_status` tool surface (this ticket) was evaluated and does not
  change this section's status either, so a future reader does not have to re-derive this from
  scratch.
- **`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 1 checklist** (confirmed exact real
  bullet list by direct read, `:1132-1154`): annotate these bullets with `**Done**
  (TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE)` following the exact annotation style the two already-
  `**Done**`-marked bullets use:
  - `"Expose knowledge_context and knowledge_status."` (`:1141`) — this ticket's primary deliverable.
  - `"Register the gateway as an ambient general repository utility, with no ticket or workflow
    metadata required."` (`:1142-1143`) — **note the real bullet text says "ambient general
    repository utility," not "ambient, phase-agnostic repository utility"** — use the real wording
    when annotating, not a paraphrase.
  - `"Return uncached normalized results with provenance."` (`:1144`) — also satisfied, since the
    live tool now actually *returns* `PacketAssembly.provenance_providers` uncached, over the MCP
    protocol, for the first time.
  - **Do not** mark `"Preserve direct provider tools and fail-open behavior."` (`:1154`) as fully
    `**Done**` by this ticket alone — this ticket satisfies only the "preserve direct provider
    tools" half (verified untouched via Step 6/8's git-diff test); the fail-open half is
    `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`'s job. If annotating, note the partial/shared status
    explicitly rather than implying full completion.

## Deviations

- **Step 7's stale-guard-test fix had 2 more real instances than this plan named.** Step 7
  identified exactly one stale Phase-0 guard test needing an update:
  `tests/tools/test_knowledge_gateway_contract_schemas.py::test_no_live_gateway_tool_code_or_mcp_registration_introduced`.
  At Implement time, running the full regression suite (`tests/tools/test_knowledge_gateway_router.py`
  + `tests/tools/test_knowledge_gateway_packet_assembly.py` + the contract-schemas suite + this
  ticket's new file) surfaced that the identical `.mcp.json`-mcpServers-key-set assertion
  (`{"knowledge-search", "github"}`) was independently duplicated, verbatim, inside two more
  DONE-ticket test files this plan did not enumerate:
  `tests/tools/test_knowledge_gateway_router.py::test_no_live_gateway_tool_code_or_mcp_registration_introduced`
  and `tests/tools/test_knowledge_gateway_packet_assembly.py::test_module_introduces_zero_mcp_server_code`.
  Both were fixed with the same minimal, surgical pattern this plan's own Step 7 already
  established as correct (update the literal key-set to include `knowledge-gateway`; leave every
  other assertion in those tests — which still correctly assert that the router/packet-assembly
  modules themselves define zero live tool code — untouched). The router test's `tools/*.py` glob
  loop also needed a one-line skip for the new `knowledge_gateway_mcp.py` file itself, since that
  file now legitimately defines `knowledge_context`/`knowledge_status`. This is the same
  "must be updated in the same change, not left broken" discipline Step 7 already applied to the
  one instance it found — applied here to two instances it did not enumerate, not a new decision
  or a scope change. No other assertion in either file was touched, and no other regression-surface
  test required any change.

## Parity Ledger (flag only — not written by this Plan phase)

A new `INFRA-337` entry (next after `INFRA-336`, confirmed by reading `docs/parity_ledger/
infrastructure.yaml`'s tail) will be needed once this ticket's real code lands, following the
INFRA-334/335/336 precedent exactly: `status: verified`, `priority: P1` (matches the ticket's own
P1 priority), `v2_evidence` naming `tools/knowledge_gateway_mcp.py`'s `knowledge_context`/
`knowledge_status` tools and the new `.mcp.json` entry; `test_path:
tests/tools/test_knowledge_gateway_mcp.py`; `support_boundary` should explicitly state that, like
INFRA-334/335/336, this ticket only reads/imports existing `tools/*.py` modules (the router, the
packet assembler, `search_mcp.py`, and — per this revision's corrected Design Decision D1 —
`tools/retrieval_events.py` too, which it does not import from or call at all) and adds one new live
`.mcp.json` server entry; it does **not** add a new function to any existing `tools/*.py` module
(reversing the prior draft's framing, which incorrectly anticipated an edit to
`tools/retrieval_events.py`). Not written now — this is the Parity phase's job, after Step 8's tests
are green.
