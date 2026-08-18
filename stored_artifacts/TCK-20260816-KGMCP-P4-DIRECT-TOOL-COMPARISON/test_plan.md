---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON
artifact_type: test_plan
tags: [ai, mcp, testing]
---

# Test Plan — TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON

## Regression Surface

**Unit / structural (frozen predecessor guards — must stay green, unmodified):**
- `tests/tools/test_kgmcp_measurement_baseline.py`
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py`
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`

**Unit (gateway components this ticket's new runner calls but must not modify):**
- `tests/tools/test_knowledge_gateway_mcp.py`
- `tests/tools/test_knowledge_gateway_router.py`
- `tests/tools/test_knowledge_gateway_packet_assembly.py`
- `tests/tools/test_knowledge_gateway_cache.py`
- `tests/tools/test_knowledge_gateway_contract_schemas.py`
- `tests/tools/test_knowledge_gateway_failure_semantics.py`
- `tests/tools/test_knowledge_gateway_redaction.py`
- `tests/tools/test_parity_index.py`
- `tests/tools/test_parity_index_baseline.py`

**Integration (direct-tool call sites the new runner reuses):**
- `tests/tools/test_search_mcp.py` (if present — verify with `find tests -iname
  "*search_mcp*"` at Implementation time; `_run_search` is called directly by this ticket's runner)

**Docs structural:**
- `tests/docs/test_redaction_retention_policy_doc.py` (structural precedent, not a direct
  dependency, but must stay green as the pattern this ticket's own new doc test follows)

**Parity ledger schema:**
- Whatever test currently validates `docs/parity_ledger/infrastructure.yaml` against
  `docs/parity_ledger/schema.json` (locate via `find tests -iname "*parity_ledger*schema*"` at
  Implementation time) must still pass after the new `INFRA-354` entry is appended.

## New Tests Required

- **Test name:** `test_new_runner_never_edits_any_frozen_predecessor_file_or_fixture`
  **Category:** unit / architecture guard
  **Verifies:** the new Phase 4 direct-tool-comparison runner never writes to
  `kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`, `kgmcp_phase1_gateway_runner.py`,
  `kgmcp_phase2_gateway_runner.py`, `kgmcp_phase3_gateway_runner.py`, or any existing
  `tests/tools/fixtures/kgmcp_*_results.json` — via SHA-256 content-hash snapshot, mirroring
  `test_kgmcp_phase3_pilot_acceptance_measurement.py`'s own convention (chosen there specifically
  because `git diff --stat HEAD` false-positives on sibling-ticket concurrent changes).
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_new_runner_imports_not_reimplements_phase0_pure_helpers`
  **Category:** unit / architecture guard
  **Verifies:** `CORPUS`, `CORPUS_VERSION`, `kgmcp_char_heuristic_v1_token_count` are imported from
  `kgmcp_baseline_corpus`, never redefined locally in the new runner (AST-inspect the runner module,
  mirroring `test_kgmcp_phase3_pilot_acceptance_measurement.py`'s
  `test_new_runner_imports_not_reimplements_phase1_pure_helpers`).
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_never_calls_emit_retrieval_event_or_wrap_functions`
  **Category:** unit / architecture guard
  **Verifies:** the new runner never imports or calls `emit_retrieval_event`,
  `wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, or `wrap_context_packet_assembly` — zero
  side effects into `agent-monitoring/events.jsonl`, mirroring every predecessor runner's identical
  guard.
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`
  **Category:** unit / architecture guard
  **Verifies:** `git status --porcelain -- agent-monitoring/` is unchanged before/after a run of
  the new runner, mirroring `kgmcp_baseline_runner.py` and `kgmcp_phase1_gateway_runner.py`'s
  identical guard test.
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_all_7_corpus_entries_present_with_both_gateway_and_direct_results`
  **Category:** unit
  **Verifies:** the committed fixture has exactly 7 entries, each carrying both a `gateway`
  sub-record and a `direct` sub-record (context_search + graphify, plus parity_ledger for Q3) — the
  structural requirement behind Acceptance Criterion 1 ("each of the 7 corpus entries is run
  through both the real gateway and the real equivalent direct-tool call(s)").
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_q3_direct_result_includes_a_real_parity_index_entry_call`
  **Category:** unit
  **Verifies:** for `Q3_requirement_completeness` specifically, the `direct` sub-record includes a
  real `tools/parity_index.py::entry()` call result (not just context_search/graphify) — confirming
  the Scope's own named example ("`tools/parity_index.py::entry()` directly for a parity-shaped
  question") was actually exercised, not skipped.
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_raw_content_retained_on_both_sides_for_quality_comparison`
  **Category:** unit
  **Verifies:** unlike every predecessor fixture (which drops `raw_results`/`raw_stdout` before
  serialization — confirmed absent from the Phase 0/1/2/3 fixtures during Investigation), this
  ticket's own fixture retains enough raw content (full text or a structured evidence-item list,
  not just doc-id/byte-count) on both the gateway and direct sides to support the quality axis —
  the concrete new-instrumentation claim this ticket's Investigation makes.
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_graphify_half_of_recall_is_no_longer_na`
  **Category:** unit
  **Verifies:** this ticket's fixture reports a real (non-`"N/A"`) graphify-side source/recall
  comparison for at least one entry — closing Design Decision D3's gap, open and unchanged since
  Phase 1 (confirmed still `"N/A"` in the Phase 3 fixture's `recall_report.graphify_half_status`
  during Investigation).
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_quality_signal_is_labeled_judgment_not_scored_metric`
  **Category:** unit / architecture guard
  **Verifies:** the fixture's quality/completeness field for each entry carries an explicit
  disclosure (e.g. a `basis` or `derivation` string) stating it is a reviewer-judgment call, not an
  objectively computed score — per the Investigation's own Risk that the corpus has no gold answer
  and "quality" must not be dressed up as a formula-derived metric.
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_results_grouped_by_query_type_not_only_aggregate`
  **Category:** unit
  **Verifies:** the fixture/results doc reports results keyed or grouped by `routing_shape` (or an
  equivalent per-query-type dimension), in addition to any aggregate — the structural requirement
  behind Acceptance Criterion 2.
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_no_query_type_disadvantage_is_silently_excluded_or_redefined`
  **Category:** unit / architecture guard
  **Verifies:** every entry where the gateway does not show a genuine advantage (latency slower,
  tokens higher, or quality judged worse) is present in the results doc with its real numbers/
  judgment intact — no entry filtered out, no threshold redefined to flip a real fail to a pass.
  Cross-check against the real Phase 1 finding that all 7 entries are 1.05x-3.0x heavier in tokens
  and 4/7 are 1.35x-2.85x slower, unless this ticket's own fresh numbers differ — either way, the
  test asserts the doc's stated per-entry result matches the fixture's own computed result exactly.
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_q3_and_changed_path_context_entries_reflect_current_not_stale_routing`
  **Category:** unit
  **Verifies:** `Q3_requirement_completeness`'s gateway-side result in this ticket's fixture shows
  a real `parity_ledger`-sourced response (`providers_selected` includes `"parity_ledger"`), not
  the pre-`INFRA-351` dead-end behavior recorded in the Phase 1-3 fixtures — the concrete
  regression guard for the "stale fixture" risk identified in Investigation.
  **Where:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`

- **Test name:** `test_results_doc_states_no_gold_answer_limitation`
  **Category:** unit / architecture guard
  **Verifies:** `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md`
  explicitly states the corpus has no gold/expected-answer field and that its quality judgments are
  reviewer-judgment-based, not objectively scored — mirroring
  `tests/docs/test_redaction_retention_policy_doc.py`'s structural section/phrase-assertion pattern
  against a static markdown file.
  **Where:** `tests/docs/test_phase4_direct_tool_comparison_doc.py`

- **Test name:** `test_results_doc_cites_real_fixture_and_states_pass_fail_per_query_type`
  **Category:** unit / architecture guard
  **Verifies:** the results doc cites the committed fixture path and states each query type's
  result explicitly (not only a single aggregate verdict) — mirroring
  `test_kgmcp_phase3_pilot_acceptance_measurement.py::test_results_doc_cites_real_fixture_and_states_pass_fail_per_criterion`.
  **Where:** `tests/docs/test_phase4_direct_tool_comparison_doc.py`

- **Test name:** `test_infra354_entry_is_schema_valid_and_certifies_methodology_not_conclusion`
  **Category:** unit
  **Verifies:** the new `INFRA-354` entry in `docs/parity_ledger/infrastructure.yaml` validates
  against `docs/parity_ledger/schema.json`, has `status: verified` with both `v2_evidence` and
  `test_path` populated (schema requirement regardless of priority), and its `text` field states it
  certifies the measurement tool/reporting, not the comparison's conclusion — mirroring
  `INFRA-353`'s identical framing.
  **Where:** wherever the existing parity-ledger schema-validation test lives (located via
  `find tests -iname "*parity_ledger*schema*"` at Implementation time), or a new
  `tests/docs/test_infrastructure_ledger_infra354.py` if no such general test exists.

## Scoped Pytest Commands

```
pytest tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_kgmcp_phase1_baseline_comparison.py tests/tools/test_kgmcp_phase2_baseline_recomparison.py tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py tests/tools/test_kgmcp_phase4_direct_tool_comparison.py -v

pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_knowledge_gateway_router.py tests/tools/test_knowledge_gateway_packet_assembly.py tests/tools/test_knowledge_gateway_cache.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_knowledge_gateway_failure_semantics.py tests/tools/test_knowledge_gateway_redaction.py tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py -v

pytest tests/docs/test_redaction_retention_policy_doc.py tests/docs/test_phase4_direct_tool_comparison_doc.py -v
```

Never `pytest tests/` — scope stays within `tests/tools/` (Knowledge Gateway MCP domain) and
`tests/docs/` (docs-structure domain), per Testing Rule.

## Anti-Drift Test Guards

- `test_new_runner_never_edits_any_frozen_predecessor_file_or_fixture` and
  `test_never_calls_emit_retrieval_event_or_wrap_functions` together catch any accidental drift
  into modifying Phase 1-3 measurement state or leaking a side effect into
  `agent-monitoring/events.jsonl` — the exact two failure modes every predecessor runner's own test
  suite already guards against.
- `test_no_query_type_disadvantage_is_silently_excluded_or_redefined` is the direct guard against
  this ticket's own stated risk (Scope: "no redefinition, no exclusion to force a favorable
  result") — it fails loudly if a future edit tries to massage an unfavorable entry out of the
  reported set.
- `test_quality_signal_is_labeled_judgment_not_scored_metric` guards against the specific drift
  hazard of a later edit dressing up the necessarily-subjective quality judgment as an objective
  score the frozen corpus cannot actually support (no gold answer exists — see Investigation Risks).
- `test_q3_and_changed_path_context_entries_reflect_current_not_stale_routing` guards against
  silently reusing stale Phase 1-3 fixture numbers for entries whose live gateway behavior has
  since changed (`INFRA-351`/`INFRA-352`) — the specific staleness risk this ticket's Investigation
  flags as needing a fresh run, not a re-derivation.
- `test_infra354_entry_is_schema_valid_and_certifies_methodology_not_conclusion` guards against the
  same scope-creep this ticket's own Anti-Drift Hazards name: the parity entry certifying the
  *conclusion* (gateway wins/loses) rather than the measurement tool, which would misrepresent
  `INFRA-353`'s own established precedent for this exact ticket family.
