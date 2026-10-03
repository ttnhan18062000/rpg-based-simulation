---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-MEASUREMENT-BASELINE
artifact_type: test_plan
tags: [ai, agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260814-KGMCP-MEASUREMENT-BASELINE

## Regression Surface

Existing tests that must keep passing (none of this ticket's scoped work should change their
outcomes, since `SEARCH_TOOL_NAMES`/existing section functions are reused, not modified):

**Unit**
- `tests/tools/test_retrieval_baseline_metrics.py` (25 tests) — the one-off baseline snapshot
  tool this ticket's corpus work depends on but must not modify the internals of (reuse-not-
  reimplement AST guards, never-silent derivation tests, real-corpus plausibility test, zero-
  mutation guard, CLI top-level-key-set smoke test).
- `tests/tools/test_generate_retro.py` (119+ tests, includes the 17 added by the sibling
  `CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` ticket) — covers
  `compute_search_investigation_trend`, `compute_tool_safety_metrics` (incl.
  `read_count_correlation`), `compute_parity_index_readpath_call_count`, and the frozen
  `_FIXED_CORPUS_EXPECTED_REPORT` literal. Any new section this ticket adds to `generate()`
  output (if any) must not perturb this frozen literal for the zero-tools fixture case.

**Integration**
- `tests/tools/test_knowledge_gateway_contract_schemas.py` (19 tests) — the frozen Phase-0
  MCP request/response/capability schemas this ticket's new contract doc must not contradict.
- `tests/tools/test_evidence_cache_identity_contract.py` (19 tests) — the frozen lookup-vs-
  validity identity contract; this ticket's measurement-point contract must not redefine or
  duplicate cache-identity concepts already frozen there.

**Architecture guard (existing precedent to mirror)**
- Any AST-based "no live gateway code touched" guard, mirroring
  `KGMCP-EVIDENCE-CACHE-IDENTITY`'s `git diff --stat -- tools/retrieval_cache.py` empty-diff
  confirmation pattern — this ticket must show zero edits to any file that would constitute
  "wiring into a live gateway" (Out of Scope).

No `arena-combat` regression surface applies — this ticket touches agent-orchestration tooling
only, not simulation/combat code.

## New Tests Required

Per acceptance criteria:

1. **Sibling-status reuse guard**
   - Test name: `test_investigation_confirms_sibling_ticket_done_and_reuse_not_duplication`
   - Category: unit (doc/text assertion, not runtime code — may be a doc-lint-style test or a
     simple assertion the investigation.md exists and names the sibling ticket + reused function
     names)
   - Verifies: `investigation.md` explicitly states `TCK-20260810-CONTEXT-TOOLING-
     EFFECTIVENESS-TRACKING` is DONE and names the specific functions reused
     (`compute_search_investigation_trend`, `build_search_count_section`,
     `build_raw_investigation_count_section`).
   - Location: `staging_artifacts/TCK-20260814-KGMCP-MEASUREMENT-BASELINE/investigation.md`
     itself (this is a documentation AC, not code — Plan should decide whether a script-level
     test is warranted or whether `done-checker`'s manual review suffices).

2. **Representative-query corpus completeness**
   - Test name: `test_representative_query_corpus_covers_all_8_routing_shapes`
   - Category: unit
   - Verifies: every one of §8's 7 routing-shape rows (definition/terminology, symbol lookup,
     requirement-completeness, ticket/historical rationale, test-impact, ticket-status,
     broad-task-context) has at least one corpus entry tagged with that shape.
   - Location: wherever the corpus fixture lands (e.g.
     `tests/tools/fixtures/kgmcp_representative_query_corpus.json` +
     `tests/tools/test_kgmcp_measurement_baseline.py`).

   - Test name: `test_representative_query_corpus_covers_all_5_use_cases`
   - Category: unit
   - Verifies: all 5 §22 use cases (`AuthoritativeState` ownership, feature-completeness check,
     historical-removal rationale, test-impact-of-change, negative-knowledge/Kafka-style query)
     are present and tagged.

3. **Real, non-fabricated per-query baseline data**
   - Test name: `test_corpus_baseline_entries_have_real_measured_fields_never_estimated`
   - Category: unit
   - Verifies: every corpus entry's recorded baseline (wall time, tool-call count, sources
     recalled, serialized tokens) carries a `derivation`/`measurement_method` string disclosing
     how the number was obtained (mirroring the never-silent convention), and that no field is a
     placeholder/`None` masquerading as a real 0.
   - Location: same test file as above.

   - Test name: `test_corpus_baseline_wall_time_and_tool_call_count_are_plausible`
   - Category: integration (may re-run at least one real corpus query against
     `search_docs`/`graphify` live, similar to how `test_retrieval_baseline_metrics.py`'s
     `test_baseline_report_raw_investigation_count_plausible_on_real_corpus` checks against the
     real corpus rather than a mock) — Plan should scope which queries are safe/cheap enough to
     re-run in CI vs. recorded once and pinned.

4. **Measurement-point contract**
   - Test name: `test_measurement_baseline_contract_defines_all_5_latency_points`
   - Category: unit (text/JSON-schema assertion against the new contract doc, mirroring
     `test_knowledge_gateway_contract_schemas.py`'s raw `read_text()`/`json.loads()` pattern —
     no `jsonschema` dependency, per that file's own precedent)
   - Verifies: lookup, evidence-validation, provider-fallback, packet-assembly, and end-to-end
     latency are each defined as a distinct field/section with a stated unit and attachment
     point, with `end_to_end` explicitly documented as inclusive of the other four (or with a
     documented reconciliation rule) — no ambiguity about overlap.

5. **Threshold predeclaration is baseline-derived, not invented**
   - Test name: `test_predeclared_thresholds_cite_recorded_baseline_numbers`
   - Category: unit
   - Verifies: every predeclared threshold in the contract doc references (by literal number or
     named field) a real value present in the recorded corpus baseline data — a structural check
     that the threshold section is not free-floating prose disconnected from the measured data.

6. **Repeated-demand design uses only safe deterministic identity**
   - Test name: `test_repeated_demand_design_never_stores_raw_prompt_text`
   - Category: unit / architecture guard
   - Verifies (structurally, against the contract doc and, if a script exists, via AST scan of
     any function key-naming): the repeated-demand design's identity fields are limited to
     `intent`, `entity_id`, `normalized_filters`, and `query_hash` — no field named/described as
     storing raw prompt text. Mirrors `KGMCP-EVIDENCE-CACHE-IDENTITY`'s
     `test_no_migration_library_dependency_introduced`-style "scan the artifact, not just trust
     the prose" approach.

7. **Test-plan mirrors existing never-silent, derivation-string convention**
   - Test name: `test_all_new_sections_carry_a_derivation_string`
   - Category: unit
   - Verifies: every new function/section this ticket adds returns a `derivation` (or documented
     equivalent) key, matching `build_search_count_section`/`build_raw_investigation_count_section`'s
     established shape — a parametrized sweep over all new section-producing functions, mirroring
     `test_baseline_report_search_count_is_marked_or_derived_never_silent`.

8. **No live gateway wiring (Out of Scope guard)**
   - Test name: `test_no_live_gateway_code_or_search_mcp_edits_introduced`
   - Category: architecture guard
   - Verifies: `git diff --stat` (or an AST import-scan) confirms zero edits to `tools/
     search_mcp.py`, `tools/hybrid_retrieval.py`, or any file under a hypothetical
     `tools/knowledge_gateway/` — mirrors `KGMCP-EVIDENCE-CACHE-IDENTITY`'s zero-diff-on-
     `retrieval_cache.py` guard.
   - Location: `tests/tools/test_kgmcp_measurement_baseline.py`.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_retrieval_baseline_metrics.py tests/tools/test_generate_retro.py -v
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_evidence_cache_identity_contract.py -v
.venv/bin/python3 -m pytest tests/tools/test_kgmcp_measurement_baseline.py -v   # new file, once created
```

Never `pytest tests/` — scoped to the agent-monitoring/knowledge-gateway-contract domain only.

## Anti-Drift Test Guards

- **`test_search_tool_names_membership_unchanged`**: pins `SEARCH_TOOL_NAMES ==
  {"mcp__knowledge-search__search_docs", "ToolSearch", "WebSearch"}` exactly — catches any
  accidental edit to the frozenset this ticket's Out of Scope forbids touching.
- **`test_no_duplicate_read_to_search_ratio_computation`**: an AST scan of any new module this
  ticket adds, asserting it imports `build_search_count_section`/
  `build_raw_investigation_count_section`/`compute_search_investigation_trend` from
  `generate_retro.py` rather than defining a second `total = 0; for record in tools: ...` loop
  over `tools.jsonl` rows — directly enforces the "must not build a second, parallel measurement
  path" ticket-level constraint.
- **`test_read_count_correlation_and_repeated_demand_stay_separate_sections`**: asserts the new
  repeated-demand output structure does not reuse or alias `read_count_correlation`'s field names
  (`compliant_group`/`non_compliant_group`) — guards against the two distinct metrics this
  ticket's Anti-Drift Hazards flagged getting silently merged.
- **`test_context_tokens_still_reports_unavailable_for_live_telemetry`**: re-asserts
  `build_context_tokens_section()`'s existing `status == "unavailable"` behavior is untouched —
  guards against this ticket quietly claiming live token telemetry now exists when it does not.
- **`test_zero_mutation_of_real_agent_monitoring_corpus`**: `git status --porcelain --
  agent-monitoring/` before/after running any new corpus-recording code, mirroring
  `test_baseline_report_tool_causes_zero_diff_on_real_corpus` — any real-tool-invocation corpus
  run must not write into `agent-monitoring/runs.jsonl`/`events.jsonl`/`tools.jsonl` as a side
  effect of being *measured* (as opposed to the tool calls' own normal hook-recorded rows, which
  are expected and out of this guard's concern).
