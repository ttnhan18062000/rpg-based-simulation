---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-FAILOPEN-TESTS
artifact_type: plan
tags: [ai, mcp, testing]
---

# Implementation Plan — TCK-20260815-KGMCP-P1-FAILOPEN-TESTS

## Summary

This ticket is mixed, not pure test-writing. Two §16 rows (gateway-unavailable, token-budget
failure) need only tests. The "one provider unavailable" row needs a real, minimal code fix in
this ticket's own subject modules (`tools/knowledge_gateway_packet_assembly.py`,
`tools/knowledge_gateway_mcp.py`) because a `failures` list is already computed internally and
then silently discarded before it reaches the response — closing that gap is surfacing
already-computed data, not inventing new architecture. Two more gaps found by re-reading the
source myself (not just trusting investigation.md's framing): a `FileNotFoundError` from a
missing `graphify` binary can propagate uncaught through **two distinct call sites**
(`knowledge_gateway_packet_assembly.py::call_providers_for_routing_decision()`'s own re-call of
`match_symbol_name()`, already flagged by Investigate, **and**
`knowledge_gateway_router.py::route()`'s *internal* calls via `_match_identifier()`'s
symbol-shape branch and `route_ambiguous()`'s `_run_graphify_provider()`, which happen before
packet assembly is ever invoked and are not covered by fixing the first site alone). Both are
fixed without touching the frozen `knowledge_gateway_router.py` at all — one fix extends an
existing `except` clause in packet assembly, the other adds a `try/except` around the `route()`
call site inside `knowledge_gateway_mcp.py`, which is this ticket's own subject module. The 2
Graphify/Context-Search-staleness rows get zero code — nothing in Phase 1 computes or compares a
staleness signal anywhere, and building that would be new-feature work ("building the gateway"),
categorically different from surfacing already-computed data; they are explicitly deferred and
documented, mirroring the ticket's own pre-authorized treatment of the 2 cache rows. The plan then
builds the 5-row failure-injection test harness and the end-to-end smoke test test_plan.md already
designed.

## Steps

### Step 1 — `PacketAssembly` gets a real `provider_failures` field; packet-assembly call site distinguishes crash from absence
**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:**
1. `call_providers_for_routing_decision()` (verified at `tools/knowledge_gateway_packet_assembly.py:159-194`, read in full) already builds `results["failures"]` for the `context_search` missing-index case (L174-175) and the `graphify` `subprocess.TimeoutExpired` case (L182-183), but a non-zero-returncode `graphify` call is silently `continue`d with no `failures` entry at all (L185-188), and `FileNotFoundError` (binary missing) is not caught at all — it propagates. Replace the `graphify` branch (L178-189) with:
   ```python
   elif provider_id == "graphify":
       _kgr = _load_router_module()
       try:
           raw = _kgr.match_symbol_name(query_text)
       except subprocess.TimeoutExpired:
           results["failures"].append("graphify: subprocess timeout")
           continue
       except FileNotFoundError:
           results["failures"].append("graphify: binary not found on PATH")
           continue
       if raw["returncode"] != 0:
           results["failures"].append(f"graphify: subprocess exited with code {raw['returncode']}")
           continue
       if not raw["stdout"].strip():
           # A successful call that legitimately found nothing is not a failure — absence,
           # not error (Step 6's negative-knowledge framing still governs this case only).
           continue
       results["graphify"] = raw
   ```
   This splits the old single `if raw["returncode"] != 0 or not raw["stdout"].strip():` condition into "crashed" (now a `failures` entry) vs. "ran fine, found nothing" (still silent absence, unchanged) — closing exactly the gap investigation.md's Risk 2 named ("a non-zero-returncode graphify failure is currently indistinguishable from a legitimate empty result").
2. `PacketAssembly` (verified at `tools/knowledge_gateway_packet_assembly.py:551-566`, read in full — 13 fields, only `negative_claim_support` has a default) gets one new field inserted after `budget_returned: int` and before `negative_claim_support` (keeps all non-default fields before the one defaulted field, per dataclass field-ordering rules):
   ```python
   provider_failures: list[str]
   ```
3. `assemble_packet()`'s return statement (verified at `tools/knowledge_gateway_packet_assembly.py:644-658`) already computes `failures = provider_results.get("failures", [])` at L627 purely to decide `status` — add `provider_failures=failures,` to the `PacketAssembly(...)` constructor call so the same list that already decides `status="PARTIAL"` is also carried on the object, instead of being thrown away after that one read.

**Other writers to `results["failures"]` / `PacketAssembly`:** `call_providers_for_routing_decision()` is the only writer to `results["failures"]` (confirmed by reading the whole function — no other code path appends to it). `assemble_packet()` is the only constructor call site for `PacketAssembly` (confirmed by `grep -n "PacketAssembly(" tools/knowledge_gateway_packet_assembly.py` — one hit, L644). No ordering/race concern: this is single-threaded, synchronous, in-process Python — no concurrent writers exist.

**Do NOT touch:** `tools/knowledge_gateway_router.py` (frozen — `match_symbol_name()` itself keeps raising `FileNotFoundError`/`TimeoutExpired` unmodified; only the caller's `except` clause changes). Do not touch the `context_search` branch (L171-177) — already correct, no gap found there. Do not touch `render_candidates()`, `assemble_within_budget()`, or any Step 5-8 logic — unrelated to this field.

**Verify:** `tests/tools/test_knowledge_gateway_packet_assembly.py`'s full existing suite must keep passing unmodified (new field with no default before it is additive only — no existing test constructs `PacketAssembly(...)` positionally without `provider_failures`, confirmed by `grep -n "PacketAssembly(" tests/tools/test_knowledge_gateway_packet_assembly.py` returning zero direct-construction hits; all existing tests build packets via `_assemble()`/`assemble_packet()`). New: `test_graphify_binary_missing_entirely_does_not_crash_the_tool_call`, `test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result` (Step 6 below).

---

### Step 2 — `knowledge_gateway_mcp.py`: wire `provider_failures` into the response; catch the router's own internal graphify-call exceptions
**Files:** `tools/knowledge_gateway_mcp.py`

**Change:**
1. Response wiring (verified at `tools/knowledge_gateway_mcp.py:185-194`, read in full): add `"provider_failures": packet.provider_failures,` to the `response: dict = {...}` literal alongside the other `packet.*`-sourced fields (`status`, `freshness`, `verification`, `provenance_providers`, `providers_consulted_this_call`, `answer`, `budget_requested`, `budget_returned`). Always include it (even as `[]`), matching how `conflicts`/`statements`/`context`/`evidence` are always emitted as arrays, never omitted — this is what makes it "a real field ... not a silent omission" per the ticket's own AC wording, rather than an optional field a caller has to guess might be present.
2. Router-call-site fix (verified at `tools/knowledge_gateway_mcp.py:178-183`, read in full — `routing_decision = _kgr.route(query)` has zero try/except today): `knowledge_gateway_router.py::route()` (frozen, verified at `tools/knowledge_gateway_router.py:392-433`, read in full) calls `match_symbol_name()` **internally** in two places that are *not* covered by Step 1's fix, because they execute before `assemble_packet()`/`call_providers_for_routing_decision()` is ever reached: `_match_identifier()`'s symbol-shape branch (`tools/knowledge_gateway_router.py:385-388`, unguarded) and `route_ambiguous()`'s `_run_graphify_provider()` call (`tools/knowledge_gateway_router.py:276-278`, unguarded — confirmed no try/except exists anywhere in `knowledge_gateway_router.py`, matching investigation.md's own finding: "this module has zero failure handling of its own"). Reorder and wrap the `_run_knowledge_context()` body:
   ```python
   _kgr = _load_router_module()
   _kgpa = _load_packet_assembly_module()
   effective_budget = budget_tokens if budget_tokens is not None else DEFAULT_BUDGET_TOKENS

   try:
       routing_decision = _kgr.route(query)
   except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
       reason = (
           "graphify: binary not found on PATH"
           if isinstance(exc, FileNotFoundError)
           else "graphify: subprocess timeout"
       )
       fallback_response: dict = {
           "status": "PARTIAL",
           "freshness": "UNKNOWN",
           "verification": "UNVERIFIED",
           "provenance_providers": [],
           "providers_consulted_this_call": [],
           "answer": "",
           "budget_requested": effective_budget,
           "budget_returned": 0,
           "statements": [],
           "context": [],
           "evidence": [],
           "conflicts": [],
           "provider_failures": [reason],
       }
       if mode is not None:
           fallback_response["mode"] = mode
       RESPONSE_VALIDATOR.validate(fallback_response)
       return fallback_response

   packet = _kgpa.assemble_packet(routing_decision, query, effective_budget)
   ```
   (`subprocess` is already imported at `tools/knowledge_gateway_mcp.py:32` for `_git_branch_scope()` — no new import.) Remove the old, now-duplicate `effective_budget = ...` line that previously sat between the router/assembler calls.

**Other writers to the response dict:** `_run_knowledge_context()` is the only function that constructs a `knowledge_context` response (confirmed: `knowledge_status`'s `_run_knowledge_status()` builds a structurally different dict against a different schema; the two never share construction code). The existing `ValidationError` early-return (L164-176) already builds its own separate `status="ERROR"` envelope and is untouched by this step — it does not go through the code this step modifies.

**Do NOT touch:** `assemble_packet()`'s own call — this step deliberately does **not** wrap `_kgpa.assemble_packet(routing_decision, query, effective_budget)` in a try/except. Step 1 already closes the one evidenced exception path inside it (`match_symbol_name()` via `call_providers_for_routing_decision()`); wrapping `assemble_packet()` here too would swallow any *other*, unevidenced exception (a real bug) and silently degrade it to `PARTIAL`, which is not justified by anything found in this ticket's investigation. Do not touch `_run_knowledge_status()`, `_build_server()`, or the `ValidationError` branch (L164-176) — all unrelated.

**Verify:** `tests/tools/test_knowledge_gateway_mcp.py`'s full existing suite must keep passing unmodified (`provider_failures` is additive to the response dict; the response schema's own `additionalProperties` is intentionally unrestricted at the top level — see Design Decision D1 below — so no existing schema-validation assertion breaks). New: `test_context_search_index_missing_yields_partial_status_via_real_mcp_call`, `test_provider_unavailable_is_a_real_response_field_not_silent_omission`, `test_graphify_binary_missing_entirely_does_not_crash_the_tool_call`, `test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result` (Step 6 below — several of these exercise both Step 1's and Step 2's code paths depending on which routing shape they force).

---

### Step 3 — Document the new field in the frozen response schema (no closure, additive only)
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`

**Change:** Verified at `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json:1-100` (read in full) that this schema's own top-level description explicitly states `additionalProperties` is intentionally *not* restricted at the top level, so `provider_failures` already validates today without any schema edit. Add it to `properties` anyway, purely for documentation/parity (Authoritative Mechanics Rule: code and docs must stay in semantic parity), directly after `providers_consulted_this_call`:
```json
"provider_failures": {
  "type": "array",
  "items": { "type": "string" },
  "description": "Machine-readable, per-provider failure reasons (e.g. 'graphify: subprocess timeout'). Always present as an array (possibly empty) — never a silent omission when a provider fails. See docs/plans/knowledge-gateway-mcp-proposal.md §16 'one provider unavailable' row."
}
```
Do not add it to `required` (mirrors how `conflicts`/`statements` are also not required — an `ERROR`-status response legitimately has none). Do not add `additionalProperties: false` anywhere in this file — the file's own header comment explicitly forbids that ("Do not 'fix' this by adding additionalProperties:false here").

**Other writers to this schema file:** none — it is a static contract file, not a runtime-written resource. Its only "writer" is a human/agent edit; its only "readers" are `REQUEST_VALIDATOR`/`RESPONSE_VALIDATOR` in `knowledge_gateway_mcp.py` (loaded once at import time, L60-73) and `tests/tools/test_knowledge_gateway_contract_schemas.py`.

**Do NOT touch:** `knowledge_context_request.schema.json` (closed schema, unrelated — this is a response-side field), `knowledge_status_response.schema.json` (unrelated tool), any other property definition in this file.

**Verify:** `tests/tools/test_knowledge_gateway_contract_schemas.py`'s full existing suite keeps passing unmodified (additive property, no `required`/`additionalProperties` change). `test_response_schema_keeps_status_freshness_verification_distinct` and `test_conflicts_array_item_shape_matches_proposal_section_14` are the two tests closest to this file's `properties` block — read them before editing to confirm neither asserts an exhaustive/closed property set (Investigate/this plan's own read of the schema file confirms no such closure exists to break).

---

### Step 4 — Explicitly defer the 2 staleness rows (and reconfirm the 2 cache rows) as documented gaps, zero code
**Files:** `staging_artifacts/TCK-20260815-KGMCP-P1-FAILOPEN-TESTS/plan.md` (this file, Design Decision D2 below is the authoritative record), and the new test file's module docstring (Step 5)

**Change:** No production code. This step is purely the decision record + its landing point in the new test file (written in Step 5, not here) stating: "Graphify stale" and "Context Search stale" (§16 rows 4-5) and "Cache missing or corrupt"/"Cached evidence mismatch" (§16 rows 1-2, already pre-authorized as Phase-2-only by the ticket's own Scope) are explicitly not tested in this suite, with a one-line reason each, citing `tools/knowledge_gateway_packet_assembly.py:636` (`freshness = "UNKNOWN"` — hardcoded literal, never computed or compared) as the evidence that no staleness signal exists to test against.

**Do NOT touch:** Do not add any staleness-comparison code to `knowledge_gateway_packet_assembly.py`'s `freshness` field, `provider_capabilities_graphify.json`/`provider_capabilities_context_search.json` (capability descriptors — reading `generation_fingerprint`/`adapter_version` for a real staleness check would require storing a baseline to compare against, which is new Phase-2 cache-identity work per `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §4). Do not add a test that monkeypatches a capability descriptor field and asserts "nothing observably different happens" — that is the exact vacuous-test anti-pattern the ticket's own AC #2 forbids.

**Verify:** No test to verify (deliberately). The verification *is* the deferral documentation existing and being unambiguous — checked at Document-Update/Verify phase by confirming the new test file's docstring names both rows and cites the same `freshness="UNKNOWN"` evidence this step cites.

---

### Step 5 — New test file: gateway-down smoke test + deferral documentation block
**Files:** `tests/tools/test_knowledge_gateway_failure_semantics.py` (new file)

**Change:** Create the file following the existing flat-file, `importlib.util`-loading convention shared by `tests/tools/test_knowledge_gateway_router.py`/`test_knowledge_gateway_packet_assembly.py`/`test_knowledge_gateway_mcp.py` (verified by reading all three files' import blocks — none use `pytest.ini`/`conftest.py` magic, all load target modules via `importlib.util.spec_from_file_location` directly in the test file). Module docstring must contain the Step 4 deferral block (4 rows named: Graphify stale, Context Search stale, Cache missing/corrupt, Cached evidence mismatch — each with a one-line reason and file:line citation). Then, independent of Steps 1-3 (this step has no dependency on them — see Dependency Map):
- `test_gateway_down_search_mcp_test_mode_still_works` — `subprocess.run([python, "tools/search_mcp.py", "--test"], input=json.dumps({"query": "damage formula", "top_k": 3}), text=True, capture_output=True, cwd=repo_root)`, mirroring the `mcp-server-test` Makefile target's own invocation (`Makefile:380-382`, verified) exactly, including its stdin JSON shape. Assert `returncode == 0` and `stdout` parses as non-empty JSON. This test's own process never imports `knowledge_gateway_mcp`/`knowledge_gateway_router`/`knowledge_gateway_packet_assembly` — it only shells out.
- `test_gateway_down_graphify_cli_still_works` — `subprocess.run(["graphify", "query", "assemble_packet"], capture_output=True, text=True, cwd=repo_root, timeout=120)`. `"assemble_packet"` was verified live during Plan (`graphify query "assemble_packet"` → `returncode=0`, 18+ non-empty result lines) — a real, stable symbol name from this ticket's own subject module, safe to hardcode. Assert `returncode == 0` and non-empty `stdout`.
- `test_neither_provider_tool_imports_knowledge_gateway_mcp` — static/AST or substring check that `tools/search_mcp.py`'s source text never contains `"knowledge_gateway"` (covers `knowledge_gateway_mcp`/`_router`/`_packet_assembly` in one substring check, since none of the three names appears in `search_mcp.py` for any other legitimate reason — confirmed live via `grep -c knowledge_gateway tools/search_mcp.py` returning 0 during Plan).

**Other writers to this file:** none — brand-new file, no other ticket/module writes to it.

**Do NOT touch:** any existing file in `tests/tools/`. Do not start/import the real `FastMCP` stdio transport (no precedent anywhere in this repo — investigation.md Risk 4 confirmed this; keep the smoke test at the subprocess/CLI level exactly as designed).

**Verify:** the three tests above, run standalone: `pytest tests/tools/test_knowledge_gateway_failure_semantics.py -k gateway_down or imports_knowledge_gateway_mcp -v`.

---

### Step 6 — New test file: 5-row failure-injection harness (rows 2/3/6/7)
**Files:** `tests/tools/test_knowledge_gateway_failure_semantics.py` (same file, appended)

**Change:** Add, reusing the exact monkeypatch boundaries already established by sibling test files (cited per test, not invented fresh):
- `test_context_search_index_missing_yields_partial_status_via_real_mcp_call` — same monkeypatch boundary as `tests/tools/test_knowledge_gateway_mcp.py:231-242`'s existing `test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing` (`pa_search_mod._run_search` forced to return `{"error": "index not found"}`), plus the **new** assertion this ticket adds: `assert "context_search: index not found" in response["provider_failures"]`.
- `test_provider_unavailable_is_a_real_response_field_not_silent_omission` — same fixture; asserts `"provider_failures" in response` and `isinstance(response["provider_failures"], list)` and it is non-empty for this scenario. This test's pass/fail is the direct proof that Step 1/Step 2 closed the gap — it must not be weakened to `status == "PARTIAL"` alone (that would just duplicate the test above).
- `test_graphify_subprocess_timeout_yields_partial_status` — monkeypatch `subprocess.run` at `router_mod.subprocess.run` (same point as `tests/tools/test_knowledge_gateway_router.py:84-102`'s `test_symbol_name_delegates_to_graphify_cli_not_a_new_symbol_table`) to raise `subprocess.TimeoutExpired`. Force routing to select `graphify` as primary (e.g. query text matching `symbol_lookup_callers_references` shape via a bare-identifier-shaped string, or via `test_knowledge_gateway_router.py`'s own shape-keyword fixtures) so the exception is hit inside `_match_identifier()` (Step 2's new catch) — assert `response["status"] == "PARTIAL"` and `"graphify: subprocess timeout" in response["provider_failures"]`.
- `test_graphify_binary_missing_entirely_does_not_crash_the_tool_call` — same monkeypatch point, raising `FileNotFoundError` instead. Must exercise **both** call sites found in Plan: one test variant routes through `_match_identifier()`/`route_ambiguous()` (Step 2's catch) and one routes through `call_providers_for_routing_decision()` (Step 1's catch) — use two distinct query shapes to hit each path (a bare single-identifier query for the router-internal path per `tools/knowledge_gateway_router.py:385-388`; a `symbol_lookup_callers_references`-shape-classified multi-word query, e.g. `"where is X defined"`, for the packet-assembly re-call path, since shape-classification routing does not itself call `match_symbol_name()` inside `route()`). Assert `response["status"] == "PARTIAL"` and a `"graphify: binary not found on PATH"` entry in `response["provider_failures"]` for both.
- `test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result` — monkeypatch `subprocess.run` to return a completed process with `returncode=1, stdout=""` in one sub-case and `returncode=0, stdout=""` in another; assert the first produces a `"graphify: subprocess exited with code 1"` entry in `response["provider_failures"]` and the second produces none — the explicit, no-longer-vacuous proof that Step 1 distinguishes crash from legitimate absence.
- `test_budget_assembly_failure_via_real_mcp_call_returns_smaller_list_not_fabricated` — call `_mod._run_knowledge_context(query, budget_tokens=1)` with `context_search` forced to return one real, fixed-content result (reuse `_load_packet_assembly_module()._load_search_mcp_module()` monkeypatch pattern from `test_knowledge_gateway_mcp.py`'s existing tests). Assert `response["statements"] == []`, `response["budget_returned"] == 0`, `response["status"] == "PARTIAL"`, `response["evidence"]` non-empty with real `evidence_hash` values.
- `test_every_response_statement_traces_to_a_real_evidence_id_across_all_failure_modes` — parametrized over the non-empty-`statements` scenarios above (the budget-failure case has `statements == []` so is excluded by construction, not skipped); for each, assert every `response["statements"][i]["evidence_ids"]` entry resolves to a `response["evidence"][j]["evidence_id"]`. Port `tests/tools/test_knowledge_gateway_packet_assembly.py:125-134`'s `_assert_answer_traces_to_statement_evidence()` helper to the response-dict shape rather than writing new logic.

**Other writers:** none new. This step only adds tests — the underlying modules were already listed with their real writers in Steps 1-2.

**Do NOT touch:** Steps 1-3's production files any further here — this step is test-only. Do not delete or invert `tests/tools/test_knowledge_gateway_mcp.py`'s existing `test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing` — strengthen understanding by adding new assertions in the *new* file, not by editing that existing, already-passing test.

**Verify:** `pytest tests/tools/test_knowledge_gateway_failure_semantics.py -v` (full file), plus the full regression surface command from test_plan.md:
```
pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_knowledge_gateway_router.py tests/tools/test_knowledge_gateway_packet_assembly.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_search_mcp.py -v
```

---

## Scope Guards

- No new caching of any kind (no `retrieval_cache`, no cache-hit/miss logic, no cache-key computation) — Phase 2 territory, out of scope per the ticket's own Out of Scope section.
- No edits to `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md` — explicitly out of scope per the ticket.
- `tools/search_mcp.py` remains untouched — confirmed by Step 5's own architecture-guard test (`test_neither_provider_tool_imports_knowledge_gateway_mcp`) and the existing frozen-module guard `test_search_mcp_py_provably_untouched` in `tests/tools/test_knowledge_gateway_mcp.py:170`.
- `tools/knowledge_gateway_router.py` remains untouched — **this was checked explicitly per the ticket-launch instruction's point 3.** Both `FileNotFoundError` propagation paths this plan found (`_match_identifier()`'s symbol branch, `route_ambiguous()`'s graphify branch) are fixed by wrapping the *caller* (`knowledge_gateway_mcp.py`'s `route()` call site, Step 2) rather than editing `route()`/`match_symbol_name()` themselves — no router-layer fix is needed or performed. The existing frozen-module guard `test_module_does_not_edit_knowledge_gateway_router` in `tests/tools/test_knowledge_gateway_packet_assembly.py:514` continues to hold.
- No staleness-detection code anywhere (`freshness` field, capability-descriptor generation/adapter-version comparison, any baseline-storage mechanism) — Design Decision D2 below.
- No new provider integrations (`registry`, `working_log`, `parity_ledger`) — `call_providers_for_routing_decision()`'s existing silent-skip comment (L190-192) for these stays untouched.
- Do not modify `docs/plans/knowledge-gateway-mcp-proposal.md`'s §16 table text itself (the requirement text) — only the Phase-1-applicability annotation Document-Update adds around it, per investigation.md's own Docs Requiring Update note.

## Dependency Map

- Step 1 (packet_assembly.py) — independent, no dependency.
- Step 2 (knowledge_gateway_mcp.py) — independent of Step 1's code (different file, different call sites) but both must land before Step 6's tests can pass; can be implemented in either order relative to Step 1, or in parallel.
- Step 3 (schema doc) — independent; can land before, after, or alongside Steps 1-2 (schema already accepts the field without this edit — this step is documentation, not a gate).
- Step 4 (deferral decision record) — independent; feeds Step 5's docstring content.
- Step 5 (smoke test + deferral doc) — independent of Steps 1-3 (exercises `search_mcp.py`/`graphify` directly, never the modules Steps 1-2 touch).
- Step 6 (failure-injection harness) — **depends on Steps 1, 2, and 3 having landed** (asserts on `response["provider_failures"]`, which does not exist until Steps 1-2 are complete). Must be implemented last.

Suggested implementation order: 1 → 2 → 3 → 4 → 5 → 6 (5 could move earlier/parallel with 1-3 since it has no dependency, but keeping it sequential keeps the implementer's diff easier to review step-by-step).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| All 5 Phase-1-applicable §16 rows have a dedicated, deterministic test proving the exact required behavior, not just "does not crash" | Steps 1, 2, 5, 6 | `test_gateway_down_search_mcp_test_mode_still_works`, `test_gateway_down_graphify_cli_still_works`, `test_context_search_index_missing_yields_partial_status_via_real_mcp_call`, `test_graphify_subprocess_timeout_yields_partial_status`, `test_graphify_binary_missing_entirely_does_not_crash_the_tool_call`, `test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result`, `test_budget_assembly_failure_via_real_mcp_call_returns_smaller_list_not_fabricated` |
| The 2 Phase-2-only cache rows are explicitly documented as deferred, zero vacuous tests | Step 5 (deferral doc block, cache portion) | No test — verified by the docstring's presence and wording at Document-Update/Verify |
| The end-to-end smoke test passes against a genuinely disabled/unreachable gateway process, not a mock | Step 5 | `test_gateway_down_search_mcp_test_mode_still_works`, `test_gateway_down_graphify_cli_still_works`, `test_neither_provider_tool_imports_knowledge_gateway_mcp` |
| No test asserts fabricated content is absent via a hardcoded placeholder string only — must be structural | Step 6 | `test_every_response_statement_traces_to_a_real_evidence_id_across_all_failure_modes` |
| ("flag code-graph/docs result unavailable" — a real field, not a silent omission; this is Scope text repeated inside the AC's own bullets) | Steps 1, 2, 3 | `test_provider_unavailable_is_a_real_response_field_not_silent_omission` |
| (2 staleness rows must not get a vacuous test standing in for real behavior — Scope text, cross-checked against AC's anti-vacuous-test wording) | Step 4, Step 5 (deferral doc block, staleness portion) | No test — verified by the docstring's presence and wording |

## Design Decisions

**D1 — "One provider unavailable" gets a real minimal fix, not an accepted-and-documented divergence.** Investigation's Risk 2 posed this as an open choice between (a) accept-and-document via `intentional_divergences.md` or (b) fix. Resolved as **(b), fix** — per the ticket-launch instruction's explicit precedent note: this ticket's own subject is `tools/knowledge_gateway_mcp.py` and its immediate dependency `tools/knowledge_gateway_packet_assembly.py`, and the sibling MCP-TOOL-SURFACE ticket's Out of Scope text named *this* ticket as the one responsible for the real failure-semantics work. The fix is minimal: `results["failures"]` was already computed at three sites (`call_providers_for_routing_decision()`, verified `tools/knowledge_gateway_packet_assembly.py:159-194`); the only change is (i) also catching the two previously-unguarded exception classes at their call sites and (ii) carrying the already-computed list one hop further, onto `PacketAssembly` and then the response dict, instead of discarding it after a single boolean read at `assemble_packet():627-628`. No new architecture, no new field concept invented beyond what §16 already names ("explicit provider failure"). Because this is a genuine fix (not an accepted divergence), **no `docs/guidelines/intentional_divergences.md` entry is needed** for this row — closing a spec'd-but-unimplemented gap is not a divergence from the Mechanics Bible/engine contracts, it is compliance with them.

**D2 — The 2 staleness rows are deferred, not built.** Investigation's Risk 1 asked Plan to make a real call between (a) documented deferral or (b) minimal real staleness-signal logic. Resolved as **(a), deferral** — for a reason distinct from D1's "fix it" call: staleness detection requires comparing a live generation/adapter-version signal against a *stored baseline*, and nothing in Phase 1 stores, reads, or has ever computed such a baseline anywhere in the codebase (`freshness = "UNKNOWN"` is a hardcoded literal at `tools/knowledge_gateway_packet_assembly.py:636`, confirmed by reading the whole file — no other line reads or writes any freshness-adjacent state). This is categorically different from D1: D1 surfaces data that already exists and is already computed; staleness detection would require inventing new state and new comparison logic that has never existed, which is exactly "building the gateway" — the sibling MCP-TOOL-SURFACE ticket's job, not this one's, and explicitly named as Phase-2 cache-identity territory by `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §4. Building it now would also violate the proposal's own Phase-1 bullet list, which names zero staleness feature. Per the ticket's own AC #2 anti-pattern rule (which the ticket's Scope text also applies with equal force to any row lacking real behavior, not just the 2 rows it originally labeled Phase-2), a test that monkeypatches a capability-descriptor field and asserts nothing branches on it would be exactly the forbidden vacuous test. Deferral, documented plainly (Step 4/5), is the honest answer.

**D3 — `FileNotFoundError` handling needed fixes at two call sites, not one, and neither touches the frozen router.** Investigation's Risk 2/AC required deciding where to add `FileNotFoundError` handling. Re-reading `tools/knowledge_gateway_router.py` in full (not just trusting investigation.md's summary) surfaced a second propagation path investigation.md had already named but not fully traced to a fix location: `route()` itself calls `match_symbol_name()` internally via `_match_identifier()`'s symbol-shape branch (`tools/knowledge_gateway_router.py:385-388`) and via `route_ambiguous()`'s `_run_graphify_provider()` (`tools/knowledge_gateway_router.py:276-278`) — both unguarded, both executing *before* `assemble_packet()`/`call_providers_for_routing_decision()` is ever reached, so a fix scoped only to the packet-assembly call site (Step 1) would leave this path fully unfixed for any query that is either a bare single-identifier string or ambiguous-intent free text. Resolved: fix both, neither inside the frozen router. Step 1 extends packet assembly's own existing `except subprocess.TimeoutExpired` clause (already a precedent for catching-at-the-caller, not the callee). Step 2 adds a new `try/except` around the `_kgr.route(query)` call site inside `knowledge_gateway_mcp.py` — this ticket's own subject module, per the same precedent note that authorizes D1. `tools/knowledge_gateway_router.py`'s source is never edited; `match_symbol_name()` keeps raising both exception types unmodified, exactly as its own docstring's "always delegates once called" contract requires.

**D4 — Response schema field placement.** `knowledge_context_response.schema.json`'s own header comment (verified, read in full) states `additionalProperties` is intentionally open at the top level specifically because the ERROR/PARTIAL response shape is underspecified by the source proposal — this is precisely the situation `provider_failures` falls into. No `error`-shaped field fits (the existing `error` property is `{code, message}`, singular, required only when `status == "ERROR"`, and this ticket's field must appear on `PARTIAL` responses, a different status). A new top-level array field (`provider_failures: string[]`), always present, is the minimal fit — no schema restructuring, no reuse of an ill-fitting existing field forced into service.

## Docs Requiring Update (Document-Update phase)

- `docs/plans/knowledge-gateway-mcp-proposal.md` §16: annotate which of the 7 rows Phase 1 code now genuinely implements after this ticket (gateway-unavailable: yes: no-code, always-true; one-provider-unavailable: yes, real field as of this ticket; token-budget-failure: yes, pre-existing; graphify-stale/context-search-stale: no, deferred; the 2 cache rows: no, deferred) — per investigation.md's own "Docs Requiring Update" note.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 (if it is the "Phase status" section — confirm exact section number against the live doc; investigation.md did not pin this precisely) — mark this ticket's 3 landed code changes.
- `docs/parity_ledger/infrastructure.yaml` — see Parity flag below (Parity phase, not Document-Update).
- `docs/guidelines/intentional_divergences.md` — **not needed**, per Design Decision D1 (this is a fix, not an accepted divergence).

## Parity Ledger Flag (for this ticket's own Parity phase — do not write the entry now)

This ticket lands real code changes in both `tools/knowledge_gateway_packet_assembly.py` (INFRA-336's own module) and `tools/knowledge_gateway_mcp.py` (INFRA-337's own module). Recommendation: **add a new entry (next available INFRA-XXX id)** rather than amending INFRA-336/INFRA-337 in place. Rationale: this repo's own INFRA-335/336/337 sequence already establishes one-ledger-entry-per-ticket as the working precedent for this exact epic, even across tickets that touch adjacent/dependent modules; INFRA-336 and INFRA-337's existing `text` fields describe those tickets' own original, now-superseded-in-part scope ("only ever imported/called, never modified" language, etc.) — amending them in place would blur which ticket a reader should credit for the `provider_failures` behavior. Per the Authoritative Mechanics Rule's "If no entry exists, add one," a new entry documenting this ticket's specific behavior change (provider-failure surfacing spanning two modules, plus the new failure-semantics test suite) is more traceable than retrofitting two "verified, DONE" entries with new evidence. Final id/text is the Parity phase's job, not Plan's.

## Anti-Drift Notes

- Do not let Step 6's tests get "fixed" by weakening `test_provider_unavailable_is_a_real_response_field_not_silent_omission` to `status == "PARTIAL"` alone — that duplicates an already-existing assertion and defeats the test's whole purpose (per test_plan.md's own anti-drift guard).
- Do not monkeypatch inside `test_graphify_binary_missing_entirely_does_not_crash_the_tool_call` or `test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result` in a way that hides the real exception from the assertion (e.g. wrapping the call itself in a test-local try/except) — any handling belongs in Steps 1/2's production code, already landed before these tests are written (Dependency Map).
- Do not add a staleness test of any shape for the 2 deferred rows, per D2 — if a future ticket needs this, it is a new ticket, not a retrofit of this suite.
- Do not touch `tools/knowledge_gateway_router.py` under any circumstance in this ticket — both `FileNotFoundError`/`TimeoutExpired` gaps are fixed entirely at caller sites (D3). If Step 6's tests reveal a *third* propagation path not covered by Steps 1-2, stop and re-plan rather than patching the router to "just be safe."
- `results["failures"]`/`response["provider_failures"]` naming: keep it exactly `provider_failures` end-to-end (dataclass field, response key, schema property) — do not let it drift to `failures`/`unavailable_providers`/other near-synonyms partway through the stack; the whole point is one traceable name from computation to response.

## Deviations (recorded during Implement)

1. **AC #4's structural fabrication guard needed a real non-empty-statements scenario that Step
   6's literal test list does not actually provide.** Tracing every scenario Step 6 names
   (context-search-missing-index, both graphify-binary-missing variants, graphify-nonzero-
   returncode, budget-assembly-failure) through the real code shows every one of them yields
   `statements == []` — a single-provider failure with zero surviving providers has no content
   left to trace evidence for. Parametrizing `test_every_response_statement_traces_to_a_real_
   evidence_id_across_all_failure_modes` only over these scenarios would make its own assertion
   loop body never execute against non-empty `statements` in most cases — the exact vacuous-test
   shape the ticket's own AC #2/#4 forbid. Fix: added
   `_mixed_context_search_fails_graphify_succeeds_response()` (context_search fails via the
   missing-index fixture, graphify simultaneously succeeds via monkeypatch) as a new, honest
   scenario — it is a truer proof of §16's "partial result with **explicit provider failure**"
   row than a zero-survivor case, since a fully-empty "partial" result never actually
   demonstrates partial-ness. Landed as both its own dedicated test
   (`test_mixed_provider_failure_still_returns_real_content_from_surviving_provider`) and as one
   of the two structural-guard parametrize cases.
2. **The plan's implicit "real end-to-end query, no mocks" second structural-guard scenario is
   genuinely flaky under the plan's own mandated regression command, for a reason outside this
   ticket's scope.** `tests/tools/test_search_mcp.py:19` does
   `sys.modules.setdefault("knowledge_search", _KS_STUB)` at module import time, with no teardown
   — that file's own comment block acknowledges the general risk ("do NOT stub
   sentence_transformers/sqlite_vec at module level to avoid poisoning other test files") but
   the `knowledge_search` stub itself was missed by that same guard. Because `sys.modules` is
   process-global, once `test_search_mcp.py` is collected in the same pytest session (as it
   always is, per test_plan.md's own mandated regression command, which lists it before this
   ticket's new file), any later test that drives the real `_run_search()` end-to-end silently
   gets an empty-result index for the rest of that session — reproduced deterministically via
   direct `importlib` collection-order replay, confirmed unrelated to Steps 1-3's code changes
   (same failure reproduces on unmodified `tools/search_mcp.py`/`knowledge_gateway_router.py`).
   Fix: replaced the live-index scenario with a second deterministic monkeypatched scenario,
   `_graphify_succeeds_alone_response()` (mirrors this whole suite's established, non-flaky
   convention — every other test here already drives content through a monkeypatch boundary,
   never the live index). `tests/tools/test_search_mcp.py` itself was left untouched — fixing its
   own test-isolation bug is out of this ticket's scope; it is a pre-existing repo-wide test
   pollution risk affecting any future test file collected after it, not something this ticket's
   own Scope/AC text asked it to fix, and no other test in this ticket's suite is affected by it
   (all use monkeypatched fixtures already).
