---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-BASELINE-COMPARISON
artifact_type: plan
tags: [ai, mcp, testing]
---

# Implementation Plan — TCK-20260815-KGMCP-P1-BASELINE-COMPARISON

## Summary

This ticket closes the Phase 1 epic's acceptance loop by running the real
`_run_knowledge_context()` gateway against Phase 0's frozen 7-entry corpus, computing
`measurement_baseline_contract.md` §4's three predeclared thresholds against the real numbers, and
reporting PASS/FAIL honestly — including an expected, by-design FAIL on §4.3 recall for
`Q2_symbol_lookup` and `Q5_test_impact`. The approach mirrors `kgmcp_baseline_runner.py`'s own
shape (`run_corpus()`/`main()` split, external `time.perf_counter()` timing, one committed JSON
fixture) but targets the real gateway in-process (per `tests/tools/test_knowledge_gateway_mcp.py`'s
established direct-call pattern) instead of the two raw provider tools. New code: one runner script,
one comparison/threshold module, one fixture, one results doc, one structural test suite. No frozen
gateway/router/packet-assembly/corpus/runner code is touched — this ticket is measurement-only,
consuming Phase 1's frozen output as-is, including its expected shortfall.

## Design Decisions

These resolve the 4 open items flagged in `investigation.md`'s Risks section with an authoritative
call each, per this ticket's own Out-of-Scope ("no threshold redefined... no result
mischaracterized") and Gate Integrity framing.

### DD1 — Latency timing: external `time.perf_counter()`, not `retrieval_events.py` wrappers

The ticket's own Scope text ("via the now-wired `retrieval_events.py` Wrapper functions") is
factually wrong. Confirmed by direct read of `tools/knowledge_gateway_mcp.py:139-287`
(`_run_knowledge_context`'s full body) — the function imports only `_kgr` (router) and `_kgpa`
(packet assembly) via `_load_router_module()`/`_load_packet_assembly_module()`; there is no
`import retrieval_events` and no call to `wrap_retrieval_cache_check`,
`wrap_context_packet_assembly`, or `emit_retrieval_event` anywhere in that file. This corroborates
`investigation.md`'s citation of `test_wrapper_functions_genuinely_not_applicable_zero_invoked`
(`tests/tools/test_knowledge_gateway_mcp.py:190-214`), which spies on all 3 wrappers and asserts
zero calls during a real invocation.

**Decision:** the new runner records latency with `time.perf_counter()` wrapped directly around
each `_run_knowledge_context(query)` call — exactly the pattern `kgmcp_baseline_runner.py:68-71`'s
`_run_context_search()` already uses for the Phase 0 direct-tool baseline. The ticket's Scope
wording is corrected in this plan and in the results doc's own text (Step 5) to state plainly: no
wrapper wiring exists to use, external timing is the only available and honest approach, and
building a fake wrapper call site solely to match the ticket's inaccurate wording would itself be a
check-passing-over-substance move forbidden by this repo's Hard Rules. `tools/knowledge_gateway_mcp.py`
is not edited.

### DD2 — Evidence-ID normalization rule for §4.3 recall comparison

Read directly (not inferred): `tools/agent-monitoring/kgmcp_baseline_runner.py:78`
(`sources_recalled = [r["doc_id"] for r in results]`, where `doc_id` comes from
`tools/search_mcp.py`'s real `_run_search()` return, form confirmed by the committed fixture's own
values — e.g. `"simulation/quest_contract#authoritative-status-001"`, `"TCK-20260425-PH8-M3"`, and
one non-doc/non-ticket UUID-shaped value `"f037e9a1-43fa-4687-982f-38a78f927cb8"` on
`Q6_ticket_status`, verified by `python3 -c` dump of
`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` during Plan). Compare against
`tools/knowledge_gateway_packet_assembly.py:100-125`
(`_evidence_id_for_context_search_result`), which builds Phase 1's `context[].source_id` /
`evidence[].evidence_id` as:
- `doc:{source_path}#{anchor}` when `result["source_path"]` starts with `"docs/"` (anchor
  independently re-slugified from `heading`/`section`, with `-2`/`-3` duplicate suffixing) — L111-119
- `ticket:{TCK-id}` when `source_path` matches `tickets/(inprogress|done)/(TCK-...).md` — L121-123
- `file:{source_path}` otherwise (the fallback covering the UUID case) — L125

**Decision — normalization rule** (to be stated verbatim, with citations, in
`phase1_baseline_comparison.md`, Step 5):
1. Strip the `doc:` prefix from a Phase 1 evidence/source ID; if the remaining path starts with
   `docs/`, strip that `docs/` prefix and strip a `.md` immediately before the `#anchor` separator
   (or at end of string if no anchor). Result: `{path-without-docs-prefix-or-extension}#{anchor}`,
   directly comparable to Phase 0's `doc_id` shape (`simulation/quest_contract#anchor`).
2. Strip the `ticket:` prefix — the remainder (`TCK-...`) is directly comparable to Phase 0's bare
   ticket-ID strings.
3. Strip the `file:` prefix — the remainder (`source_path` verbatim) is directly comparable to
   Phase 0's non-doc/non-ticket `doc_id` values (covers the observed UUID case: Phase 0 recorded the
   bare UUID as `doc_id`, and Phase 1's `_evidence_id_for_context_search_result` falls through to
   `file:{source_path}` for any `source_path` that is neither `docs/`-prefixed nor a ticket path, so
   stripping `file:` recovers the same raw value when the same underlying source is recalled).
4. `symbol:` (graphify) evidence IDs are handled separately — see DD3; they are never compared
   against `doc_id`-shaped Phase 0 values under this rule.
5. Anchor re-slugging is a known, accepted source of imprecision: Phase 1's anchor is independently
   derived from `heading`/`section` via `_slugify()` and may not byte-for-byte match Phase 0's
   anchor for the same document if `search_mcp.py`'s heading/section text or duplicate-count state
   differs between runs. The comparison therefore matches on **normalized `path` only** (the part
   before `#`) when a same-path entry exists in both sets, and additionally reports anchor-level
   exact-match as an informational (non-blocking) sub-field — never a source of a false miss driven
   purely by cosmetic anchor drift. This is stated explicitly, not left implicit, in both the fixture
   `derivation` strings (Step 3) and the results doc (Step 5).

This is a documented, citable, per-format rule — not invented silently inside runner code with no
doc trail, satisfying `investigation.md` Risk #3's requirement.

### DD3 — Graphify half of §4.3's union: N/A, reported honestly, not faked

Read directly: `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`'s `graphify`
sub-object per entry has exactly `latency_ms`, `tool_call_count`, `raw_stdout_bytes`, `derivation`
(confirmed via `kgmcp_baseline_runner.py:151-156`, which builds exactly these 4 keys and no
`sources_recalled`-shaped field) — there is no committed raw stdout text, only a byte count, for any
of the 7 entries.

**Decision:** the graphify half of §4.3's union ("whatever authoritative sources the fixture's
`graphify` result for that entry would resolve to") is **not computable** from the committed Phase 0
fixture — there is no ground truth to diff against, and parsing `raw_stdout_bytes` (a count, not
text) cannot recover a source list. This ticket does **not** invent a fallback (e.g. stdout
containment) — the Phase 0 fixture literally does not preserve enough information for one, and
inventing a proxy would be new interpretive logic dressed up as measurement. The comparison
therefore evaluates §4.3 using the `context_search.sources_recalled` half of the union only, for
every entry, and the fixture, results doc, and results-doc narrative all state this explicitly and
by name: *"No Phase 0 graphify source baseline exists to compare against (the fixture recorded only
`raw_stdout_bytes`, never a source list) — the graphify half of §4.3's union is reported as N/A, not
silently treated as empty-and-passing."* This is a real, stated, honest scope narrowing of the
comparison method (permitted — this is not the same as narrowing the *threshold formula* itself,
which stays as declared in the contract), and is distinct from `investigation.md` Risk #2/#4's
warning against silently treating the graphify half as trivially satisfied.

### DD4 — Q2/Q5 recall miss: computed and reported as a real FAIL, not routed around

Confirmed directly: `tools/knowledge_gateway_router.py:151-183`'s `ROUTING_TABLE` —
`symbol_lookup_callers_references` → `primary_providers=("graphify",)` (L157-159) and
`test_impact_of_change` → `primary_providers=("graphify",)` (L172-174); no other row selects
`graphify` alone besides these two, and `broad_task_context` (Q7) is the only row selecting both
(L181-183). Cross-checked against `_classify_routing_shape`/`_SHAPE_KEYWORDS` (L326-358) and the two
corpus query strings themselves (`kgmcp_baseline_corpus.py:53-56` "Where is
compute_search_investigation_trend defined..." and L72-75 "What tests must run if
tools/agent-monitoring/generate_retro.py changes?") — both trivially match `"where is"`/`"defined"`
and `"what tests"`/`"must run if"` respectively, before any other shape's keywords, per
`_SHAPE_CLASSIFICATION_ORDER` (L339-347, `symbol_lookup...` and `test_impact...` both precede
`broad_task_context`).

**Decision:** for these 2 entries, `response["context"]` (and therefore
`sources_recalled`-under-DD2-normalization) will contain zero `context_search`-derived items, so
`threshold_4_3_recall.pass` computes to `False` and `missing_sources` will be non-empty (equal to
Phase 0's full `context_search.sources_recalled` list for that entry, since none of it can be
covered). This is computed by the same formula as every other entry — no special-cased exclusion,
no widened routing, no substituting `provenance_providers` membership for actual source identity.
The results doc's narrative (Step 5) states this is a routing-design consequence
(`TCK-20260815-KGMCP-P1-QUERY-ROUTER`, Done, frozen), not an implementation defect, and is expected
per §8's routing table — consistent with `investigation.md` Risk #2's framing.

## Steps

### Step 1 — New runner script: `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`

**Files:** `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` (new)

**Change:** Mirror `kgmcp_baseline_runner.py:117-179`'s `run_corpus()`/`main()` split exactly.
- Load `tools/knowledge_gateway_mcp.py` in-process via
  `importlib.util.spec_from_file_location(...)` + `spec.loader.exec_module(mod)`, exactly the
  pattern already established and exercised in `tests/tools/test_knowledge_gateway_mcp.py` (per
  `investigation.md`'s Current Behavior section, "answers Assumptions/Open Question #1" —
  confirmed no MCP server/session/transport is needed, `_run_knowledge_context` is a plain
  importable module-level function per `tools/knowledge_gateway_mcp.py:139` itself).
- Import `CORPUS`, `CORPUS_VERSION` from `kgmcp_baseline_corpus.py` (unmodified, read-only import —
  same module Phase 0's runner already imports from, `kgmcp_baseline_runner.py:49-53`).
- For each of the 7 `CORPUS` entries, in order, call:
  ```
  start = time.perf_counter()
  response = mod._run_knowledge_context(entry["query_text"])
  latency_ms = (time.perf_counter() - start) * 1000
  ```
  (DD1 — no `retrieval_events.py` import, no wrapper call anywhere in this file.)
- Also call `mod._load_router_module().route(entry["query_text"])` once per entry (read-only,
  side-effect-free per `route()`'s own signature at `knowledge_gateway_router.py:392`) to record
  the real `providers_selected` list for that entry — this is the ground truth
  `test_predicted_q2_q5_recall_miss_is_reported_not_hidden` checks against per the test plan, not an
  assumption baked into the runner.
- Record per entry: `latency_ms` (wall time), `providers_selected` (from `route()`), the full raw
  `response` dict (needed by Step 2/3 for evidence extraction and token measurement), and a
  `derivation` string citing `_run_knowledge_context()` and `time.perf_counter()` by name (never a
  bare number with no derivation, per AC #4 and the never-silent convention).
- `run_corpus()` returns the report dict kept separate from `main()`, exactly mirroring
  `kgmcp_baseline_runner.py:117/171`'s split, so tests can exercise the live path without
  re-writing the pinned fixture (mirrors
  `test_zero_mutation_of_real_agent_monitoring_corpus`-style testability).
- `main()` is NOT auto-run by pytest — same one-time-by-hand convention as
  `kgmcp_baseline_runner.py`'s own module docstring (`kgmcp_baseline_runner.py:1-6`).

**Other writers to this resource:** none — this is a brand-new script; nothing else writes to it.
The corpus module (`kgmcp_baseline_corpus.py`) it imports from is read-only shared state also
imported by `kgmcp_baseline_runner.py` and the Phase 0 test suite; this step only reads `CORPUS`/
`CORPUS_VERSION`, never mutates the module.

**Do NOT touch:** `kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`, `tools/search_mcp.py`,
`tools/retrieval_events.py`, `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py` — all read-only imports/calls, zero edits.

**Verify:** `test_all_7_corpus_entries_present_in_comparison_fixture`,
`test_comparison_runner_calls_real_run_knowledge_context_not_a_mock`,
`test_new_runner_never_calls_emit_retrieval_event_or_wrap_functions`,
`test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`.

### Step 2 — Evidence-normalization and recall-comparison module

**Files:** `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` (same file, or a clearly
separated section within it — implementer's choice, but keep pure functions unit-testable)

**Change:** Implement DD2's normalization rule as a pure function, e.g.
`_normalize_phase1_source_id(evidence_id: str) -> str`, operating on strings from
`response["context"][*]["source_id"]` (per `tools/knowledge_gateway_mcp.py:245`,
`response["context"]` built from `packet.context` with `source_id` key) or
`response["evidence"][*]["evidence_id"]` (`tools/knowledge_gateway_mcp.py:256`). Cite
`_evidence_id_for_context_search_result`/`_evidence_id_for_graphify_result`
(`tools/knowledge_gateway_packet_assembly.py:100-134`) by name and line in the function's
docstring, matching the 3-branch rule from DD2 (`doc:`/`ticket:`/`file:` prefixes; `symbol:`
excluded from doc/ticket comparison per DD3).
Implement `_compute_threshold_4_3(baseline_sources: list[str], gateway_sources: list[str]) ->
dict` returning `{"pass": bool, "baseline_sources": [...], "gateway_sources": [...],
"missing_sources": [...], "derivation": "..."}` where `missing_sources` = baseline sources (after
normalization) not present in the normalized gateway set — per-query, never aggregate-only, per
`measurement_baseline_contract.md:220-222`'s explicit "per query, not only in aggregate" rule
(confirmed by direct read).

**Other writers to this resource:** none — pure function, no shared mutable state. The formula it
implements (§4.3) is authored once here; it must not diverge from the contract's stated formula
(`measurement_baseline_contract.md:214-222`, read and confirmed above) — Step 6's structural test
(`test_no_threshold_formula_redefined_from_measurement_baseline_contract`-equivalent for §4.3, if
scoped there) guards against silent drift.

**Do NOT touch:** the Phase 0 fixture (read-only input), any frozen gateway module.

**Verify:** `test_each_entry_reports_recall_threshold_pass_fail_with_numbers`,
`test_predicted_q2_q5_recall_miss_is_reported_not_hidden`.

### Step 3 — Per-entry and aggregate §4.1/§4.2/§4.3 threshold computation

**Files:** `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`

**Change:** Compute, per entry:
- `threshold_4_1_latency`: `{"pass": gateway_wall_time_ms <= 935.32, "gateway_wall_time_ms": ...,
  "threshold_ms": 935.32, "derivation": "..."}`. `935.32` is re-derived at runtime from the
  Phase 0 fixture's own 7 `combined.wall_time_ms` values (`0.5 * mean(...)`), never hand-typed —
  confirmed by direct computation during Plan that `mean(combined.wall_time_ms) == 1870.6478...`
  over the currently-committed fixture, matching `measurement_baseline_contract.md:195`'s stated
  935.32 figure exactly (computed via `python3` against the real fixture file during Plan).
- `threshold_4_2_tokens`: `gateway_tokens` measured via
  `knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1` (imported from the loaded module,
  `tools/knowledge_gateway_packet_assembly.py:81-87` — confirmed identical formula to
  `kgmcp_baseline_corpus.py:93-103`'s copy, per `investigation.md`'s Current Behavior citation)
  applied to `json.dumps(response)` (the full real response payload, mirroring Phase 0's
  `combined.serialized_tokens_estimate` measuring the full returned payload, not a sub-field).
  `threshold_tokens = 1263.57`, re-derived the same way (`0.5 * mean(combined.serialized_tokens_estimate)`,
  confirmed `== 2527.1428571...` over the real fixture during Plan, matching
  `measurement_baseline_contract.md:211`'s stated figure).
- `threshold_4_3_recall`: from Step 2's `_compute_threshold_4_3`, called with
  `baseline_sources = fixture_entry["context_search"]["sources_recalled"]` (Phase 0 fixture, read
  only) and `gateway_sources = [normalized source_id for each response["context"] item]`.
- A top-level `aggregate` object: `{"threshold_4_1": {"pass_count": int, "of": 7}, "threshold_4_2":
  {...}, "threshold_4_3": {...}, "all_thresholds_pass": bool}` where `all_thresholds_pass` is
  `False` if *any* per-entry threshold is `False` (per test plan's
  `test_aggregate_thresholds_summarize_all_7_entries_not_just_a_subset`).

**Other writers to this resource:** none new. This step reads two existing frozen inputs
concurrently: (a) the Phase 0 fixture (`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`,
written once by `kgmcp_baseline_runner.py::main()`, never touched again per Anti-Drift Hazard) and
(b) the live gateway response (freshly computed each run by Step 1, non-deterministic on latency
only — `derivation` strings must state that `latency_ms`/`wall_time_ms` numbers are point-in-time,
not reproducible bit-for-bit across runs, mirroring `measurement_baseline_contract.md:180-184`'s own
caveat about the Phase 0 figures). No ordering/race concern: both reads happen sequentially within
one single-process script run, no concurrent writers.

**Do NOT touch:** the threshold constants' *source of truth* — always compute `935.32`/`1263.57`
from the fixture, never hardcode a bare literal disconnected from the formula.

**Verify:** `test_each_entry_reports_latency_threshold_pass_fail_with_numbers`,
`test_each_entry_reports_token_threshold_pass_fail_with_numbers`,
`test_aggregate_thresholds_summarize_all_7_entries_not_just_a_subset`,
`test_no_threshold_formula_redefined_from_measurement_baseline_contract`.

### Step 4 — Committed fixture: `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`

**Files:** `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` (new)

**Change:** Run `kgmcp_phase1_gateway_runner.py::main()` once, by hand, during Implementation
(never wired into pytest's fast loop, mirroring `kgmcp_baseline_runner.py`'s own one-time-script
convention stated in its module docstring, L1-6). Write
`{"corpus_version": 1, "compared_against_phase0_corpus_version": 1, "recorded_at_utc": "...",
"entries": [ {id, query_text, providers_selected, gateway_wall_time_ms, gateway_tokens,
threshold_4_1_latency, threshold_4_2_tokens, threshold_4_3_recall}, ... 7 entries ...],
"aggregate": {...}}` via `json.dumps(..., indent=2, sort_keys=True)`, matching
`kgmcp_baseline_runner.py:174`'s exact serialization convention. Every entry and every threshold
sub-object carries a non-empty `derivation` string (never a bare boolean/number).

**Other writers to this resource:** none — this fixture path is new and unique to this ticket; the
Phase 0 fixture (`kgmcp_measurement_baseline_corpus_results.json`) is a *different* path, has its
own separate writer (`kgmcp_baseline_runner.py::main()`), and is never regenerated or hand-edited by
this ticket (Anti-Drift Hazard, `investigation.md` line 296-299) — this step only *reads* it via
Step 3.

**Do NOT touch:** `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`.

**Verify:** all fixture-based structural tests in the test plan; `git status --porcelain` before/
after confirms only the new fixture path is touched, not the Phase 0 one.

### Step 5 — Results doc: `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` (new)

**Change:** Author a results doc presenting, per threshold (§4.1/§4.2/§4.3), the aggregate and
per-entry PASS/FAIL with actual numbers (never a bare verdict), citing the new fixture path
literally. Must include, verbatim or near-verbatim:
- DD1's scope-text correction (the ticket's own Scope said "via the now-wired `retrieval_events.py`
  Wrapper functions"; this doc states plainly that this was inaccurate and external
  `time.perf_counter()` timing was used instead, citing
  `tests/tools/test_knowledge_gateway_mcp.py`'s wrapper-non-invocation test).
- DD2's normalization rule, stated as a citable rule (not buried in code comments only).
- DD3's explicit N/A statement for the graphify half of §4.3's union, with the literal sentence
  "No Phase 0 graphify source baseline exists to compare against."
- DD4's narrative: Q2/Q5 recall is an **expected FAIL**, citing the real routing table
  (`ROUTING_TABLE["symbol_lookup_callers_references"]`/`["test_impact_of_change"]`, both
  `primary_providers=("graphify",)`) and stating this is routing-design behavior from
  `TCK-20260815-KGMCP-P1-QUERY-ROUTER`, not a defect.
- The literal strings `PASS`/`FAIL` at least once per threshold, per the doc's own presentation
  (test plan's `test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold`).
- An overall honest verdict sentence (e.g. "§4.1: PASS. §4.2: <verdict>. §4.3: FAIL for
  Q2/Q5 (expected, by design); <verdict> for the remaining 5 entries.") — never a blanket "Phase 1
  succeeded" characterization if any per-entry threshold misses.

**Other writers to this resource:** none — new file, unique path.

**Do NOT touch:** `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`'s
§4 prose (the Phase 0 threshold figures are pinned to the Phase 0 fixture and do not change — this
ticket only *cites* §4, never edits it, per `investigation.md`'s Docs Requiring Update section).

**Verify:** `test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold`.

### Step 6 — Structural test suite: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`

**Files:** `tests/tools/test_kgmcp_phase1_baseline_comparison.py` (new)

**Change:** Implement every test named in `test_plan.md`'s "New Tests Required" section verbatim
(11 tests total): the 2 AC#1 tests, 4 AC#2 tests, 2 AC#3 tests, 2 AC#4 tests, and the 4
frozen-dependency/anti-drift guard tests (`test_no_frozen_kgmcp_dependency_edited`,
`test_new_runner_never_calls_emit_retrieval_event_or_wrap_functions`,
`test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`,
`test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold`) — mirror
`test_kgmcp_measurement_baseline.py`'s AST-based structural-guard pattern
(`ast.parse` + `ast.walk` over the runner module's source, never a runtime mock-detection hack) for
the two AST-based tests, and its `git diff --stat HEAD`-based frozen-file check pattern for
`test_no_frozen_kgmcp_dependency_edited`, extending the banned-edit list to cover this ticket's own
7 frozen paths (per `investigation.md` Anti-Drift Hazards: the 4 frozen gateway modules,
`kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`, and the Phase 0 fixture path).

**Other writers to this resource:** none — new test file. It reads (never writes) the Phase 0
fixture, the new Phase 1 fixture, and both runner/gateway module sources.

**Do NOT touch:** `tests/tools/test_kgmcp_measurement_baseline.py`,
`tests/tools/test_knowledge_gateway_mcp.py`, or any other existing test file in the Regression
Surface — this step only adds a new file.

**Verify:** the full scoped pytest command from `test_plan.md`'s "Scoped Pytest Commands" section:
```
pytest tests/tools/test_kgmcp_phase1_baseline_comparison.py \
       tests/tools/test_kgmcp_measurement_baseline.py \
       tests/tools/test_knowledge_gateway_mcp.py \
       tests/tools/test_knowledge_gateway_router.py \
       tests/tools/test_knowledge_gateway_packet_assembly.py \
       tests/tools/test_knowledge_gateway_failure_semantics.py \
       tests/tools/test_knowledge_gateway_contract_schemas.py -v
```

### Step 7 — §20 Phase 1 checklist: new appended prose (not a bullet retrofit)

**Files:** `docs/plans/knowledge-gateway-mcp-proposal.md`

**Change:** Confirmed by direct read (`docs/plans/knowledge-gateway-mcp-proposal.md:1142-1191`):
all 6 existing Phase 1 bullets already carry **Done** annotations from the 4 prior child tickets,
and the section ends at line 1191 immediately before `### Phase 2: Real Provider-Result Cache` at
line 1193. This ticket's own contribution is not a natural fit for any existing bullet (none of the
6 describes a comparison/acceptance-check activity). Append a new short paragraph immediately after
line 1191 (before the `### Phase 2` heading) stating: this ticket ran the real gateway against the
Phase 0 corpus and reports the comparison outcome (cite `phase1_baseline_comparison.md` and the new
fixture by path), including the honest §4.3 Q2/Q5 miss — explicitly not declaring Phase 1
"successful" in blanket terms if any threshold misses, per this ticket's own AC #3. This is
Document-Update-phase work, not Plan/Implement work — flagged here so Document-Update has an
unambiguous target location and does not have to re-derive it.

**Other writers to this resource:** this doc has been edited by each of the 4 prior Phase 1 child
tickets in sequence, each appending its own **Done** annotation to its own bullet — this step
follows that exact same "append, never rewrite a sibling's line" precedent, touching only new prose
after the existing 6 bullets.

**Do NOT touch:** any of the 6 existing bullets' text (lines 1144-1191), the Phase 3/§21 pilot-bar
section, or any other section of this proposal doc.

**Verify:** doc-only change; verified by Document-Update phase review, not a pytest test.

## Scope Guards

- Never edit `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
  `tools/knowledge_gateway_mcp.py`, or `tools/retrieval_events.py` — all are DONE/frozen; this
  ticket measures their real, current behavior, including its real shortfalls, and does not alter
  it to make a threshold pass.
- Never widen `ROUTING_TABLE` or otherwise cause Q2/Q5 to call `context_search` — the
  single-primary-provider routing table is frozen, ledgered behavior from
  `TCK-20260815-KGMCP-P1-QUERY-ROUTER` (INFRA-335).
- Never modify `kgmcp_baseline_corpus.py`'s `CORPUS` (no cherry-picking, reordering, or adding
  entries) — reuse verbatim, all 7, in order.
- Never regenerate or hand-edit
  `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` — read-only input; this
  ticket writes only the new, separate `kgmcp_phase1_baseline_comparison_results.json`.
- Never redefine or loosen §4.1/§4.2/§4.3's threshold formulas from
  `measurement_baseline_contract.md` — always recompute `935.32`/`1263.57` from the Phase 0
  fixture's own averages, never hand-type independently, and never substitute a looser recall
  definition (e.g. provider-membership instead of actual source identity) to avoid a per-entry FAIL.
- Never characterize a per-entry threshold miss as an aggregate pass, and never omit the Q2/Q5
  miss from the Completion Summary or results doc.
- Never edit `CLAUDE.md`, any `.claude/agents/*.md`, or any `.claude/skills/*.md` file.
- Never touch `tests/tools/test_kgmcp_measurement_baseline.py`,
  `tests/tools/test_knowledge_gateway_mcp.py`, `tests/tools/test_knowledge_gateway_router.py`,
  `tests/tools/test_knowledge_gateway_packet_assembly.py`, or
  `tests/tools/test_knowledge_gateway_failure_semantics.py` — regression surface, read/run-only.
- Do not write a new `docs/parity_ledger/infrastructure.yaml` INFRA-339 entry during Plan or
  Implement — that is this ticket's own later Parity phase's job (flagged, not actioned, here).
- Do not decide or record any Phase 2/3 promotion recommendation — that is an explicitly
  out-of-scope human-reviewer decision per the ticket's own Out of Scope section.

## Dependency Map

- Step 1 (runner) has no dependency on other steps; it is the foundation.
- Step 2 (normalization) is a pure function usable independently of Step 1 but is invoked by Step 1
  during `run_corpus()` — implement Step 2's logic before or alongside Step 1, but Step 1's
  `run_corpus()` cannot be considered complete until Step 2's function is available to call.
- Step 3 (threshold computation) depends on Step 1's raw response data and Step 2's normalized
  recall comparison; implement after both.
- Step 4 (fixture) depends on Steps 1-3 being complete and correct — it is produced by running the
  finished runner once.
- Step 5 (results doc) depends on Step 4's real fixture numbers (cites them directly) — write after
  the fixture exists.
- Step 6 (test suite) depends on Steps 1-5 all existing (it tests the fixture, the runner's AST, and
  the results doc's text) — implement last among the code/doc steps, though individual test
  functions can be scaffolded earlier against expected shapes.
- Step 7 (§20 prose) depends on Step 5 (cites `phase1_baseline_comparison.md` by name) — do last, or
  at minimum after Step 5's filename is final.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| All 7 corpus entries run through the real gateway (not a subset, not a mock) | Step 1 | `test_all_7_corpus_entries_present_in_comparison_fixture`, `test_comparison_runner_calls_real_run_knowledge_context_not_a_mock` |
| Each §4 threshold computed and reported PASS/FAIL per entry and aggregate, with actual numbers | Steps 2, 3 | `test_each_entry_reports_latency_threshold_pass_fail_with_numbers`, `test_each_entry_reports_token_threshold_pass_fail_with_numbers`, `test_each_entry_reports_recall_threshold_pass_fail_with_numbers`, `test_aggregate_thresholds_summarize_all_7_entries_not_just_a_subset` |
| If a threshold is missed, Completion Summary states this plainly — no threshold redefined, no result mischaracterized | Steps 3, 5, 7 (Completion Summary itself is written at ticket close, informed by these) | `test_no_threshold_formula_redefined_from_measurement_baseline_contract`, `test_predicted_q2_q5_recall_miss_is_reported_not_hidden`, `test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold` |
| New fixture and test suite structurally enforce the never-silent convention | Steps 4, 6 | `test_all_comparison_entries_carry_nonempty_derivation_strings`, `test_missing_comparison_field_fails_loudly` |

## Anti-Drift Notes

- The single most consequential fact from investigation: only `Q7_negative_knowledge` routes to
  both providers under the real router (`ROUTING_TABLE["broad_task_context"]`,
  `knowledge_gateway_router.py:181-183`); the other 6 entries route to exactly one provider each.
  This structurally caps how many entries can pass a naive both-provider-union recall check — DD2/
  DD3/DD4 exist specifically to make this honest rather than hidden.
- Format mismatch is real and non-trivial: Phase 0's `sources_recalled` is a flat mixed-shape list
  (doc-anchor strings, bare ticket IDs, at least one bare UUID observed on `Q6_ticket_status`);
  Phase 1's `source_id`/`evidence_id` values are uniformly prefixed (`doc:`/`ticket:`/`file:`/
  `symbol:`). A literal set-equality or substring check without DD2's normalization will produce
  false regressions across nearly every entry, not just Q2/Q5 — this is a correctness risk for the
  *entire* §4.3 computation, not only the two expected-fail entries.
- `provider_failures` (from the sibling `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`/INFRA-338 ticket) is
  a real, always-emitted response field (`tools/knowledge_gateway_mcp.py:221`,
  `response["provider_failures"] = packet.provider_failures`). If a live run of Step 1 ever produces
  a non-empty `provider_failures` for any entry (e.g. a transient `graphify` subprocess hiccup), that
  must be recorded and reported honestly for that entry — never silently re-run until it succeeds
  (survivorship bias), and never excluded from that entry's threshold computation.
- The `935.32`/`1263.57` threshold constants must always be *computed*, never hardcoded as bare
  literals disconnected from the Phase 0 fixture — confirmed during Plan by direct computation
  against the real committed fixture (`mean(combined.wall_time_ms) = 1870.6478597596288`,
  `mean(combined.serialized_tokens_estimate) = 2527.1428571428573`, both matching
  `measurement_baseline_contract.md`'s stated figures exactly), so implementers should re-derive
  rather than trust this plan's numbers blindly if the fixture is ever re-recorded under a new
  `corpus_version` (it should not be, within this ticket's scope, but the formula must stay
  live-computed regardless).
- This ticket is the last child of the Phase 1 epic — its Completion Summary is the epic's own
  closing acceptance record. It must not overstate Phase 1 as unconditionally successful if §4.3
  misses on Q2/Q5, per the ticket's own AC #3 and Out of Scope section.
