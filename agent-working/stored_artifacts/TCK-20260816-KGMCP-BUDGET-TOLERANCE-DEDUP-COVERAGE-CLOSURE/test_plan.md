---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE

## Regression Surface

**Unit — `tests/tools/test_knowledge_gateway_packet_assembly.py`** (874 lines, ~50 tests as of this
investigation) must all keep passing, in particular the budget/dedup-adjacent ones whose assumptions
Gap 1's fix directly touches:
- `test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate`
- `test_budget_returned_never_exceeds_budget_requested`
- `test_deduplication_occurs_before_truncation_not_after`
- `test_priority_order_invariants_before_facts_before_tests_before_history`
- `test_budget_assembly_failure_returns_smaller_real_list_not_fabricated_content`
- `test_budget_assembly_failure_packet_has_no_new_content_beyond_real_provider_output`
- `test_budget_truncation_produces_visible_marker_when_content_is_dropped`
- `test_no_budget_truncation_marker_is_false_and_present_when_everything_fits`
- `test_budget_truncation_marker_set_in_sec16_total_failure_fallback_too`
- `test_evidence_dependencies_aggregated_from_packet_evidence_paths`
- `test_evidence_dependencies_excludes_paths_from_omitted_budget_truncated_statements`
- `test_evidence_dependencies_empty_in_section16_budget_assembly_failure_not_full_unfiltered_evidence`
- `test_dedup_collapses_only_on_exact_content_hash_match_across_providers`
- `test_dedup_does_not_merge_conflict_flagged_pair_even_with_identical_text`
- `test_conflict_index_pairs_correspondence_invariant_raises_on_desync`
- `test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids`

**Integration — `tests/tools/test_knowledge_gateway_mcp.py`** (1026 lines, 39 tests): all must keep
passing, in particular:
- `test_knowledge_context_response_schema_accepts_new_budget_marker_field`
- `test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker`
- any test asserting `response["budget_truncated"]`/`response["omitted_statement_count"]` shape.

**Schema** — `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`:
whatever test currently validates the response schema (see integration file above) must accept any
new field this ticket's fix adds (e.g. a context/evidence truncation marker), additively, not via a
`schema_version` bump, mirroring `budget_truncated`/`omitted_statement_count`'s own precedent
(INFRA-347).

**Arena-combat**: not applicable — this subsystem has no combat-domain coupling.

## New Tests Required

Mapped to the ticket's 5 Acceptance Criteria:

**AC1 — `assemble_within_budget()` genuinely accounts the full payload**
- `test_assemble_within_budget_accounts_context_and_evidence_bytes_not_just_statement_text` —
  unit — constructs statements whose `text` alone fits comfortably under budget but whose paired
  context/evidence content would not, and asserts the packet is genuinely truncated/flagged rather
  than silently returned oversized (mirrors the ticket's own AC1 wording almost verbatim). Lives in
  `tests/tools/test_knowledge_gateway_packet_assembly.py`.
- `test_full_response_payload_json_dumps_size_stays_within_budget_tolerance` — unit — asserts
  `len(kgmcp_char_heuristic_v1(json.dumps(response_subset)))`-style measurement (or whatever the
  real fixed accounting produces) for `context[]`+`evidence[]`+`conflicts[]` combined stays within
  the same measured-size discipline already used for statements, for a constructed case where
  context/evidence alone would exceed `budget_requested`. Lives in same file.
- `test_conflicts_are_measured_against_budget_even_though_real_corpus_never_populates_them` —
  unit, directly-constructed `Conflict` fixture (since real providers never populate `conflicts[]}`
  today, per module docstring) — verifies the extended accounting genuinely inspects
  `conflicts[]` cost, not just leaves it structurally exempt. Lives in same file.

**AC2 — real re-measurement of §21 #12 produces an honest new pass rate**
- Not a new pytest unit test — a one-time re-run of
  `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`'s existing `#12` methodology (reused, not
  reimplemented, per Scope) against the fixed code, with results committed to
  `tests/tools/fixtures/kgmcp_phase3_pilot_acceptance_measurement_results.json` (or a
  ticket-scoped sibling fixture if the runner needs a small, disclosed extension to call the fixed
  accounting path) and reported in `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`.
  If the runner itself needs code changes to reach the fixed accounting, add
  `test_kgmcp_phase3_runner_budget_compliance_check_measures_full_payload_post_fix` — unit,
  `tests/tools/test_kgmcp_phase3_gateway_runner.py` (create if it does not yet exist) — verifying
  `_compute_budget_compliance()` still computes against `json.dumps(response)` (unchanged measurement
  method) but now against a response whose `context[]`/`evidence[]` are genuinely budget-aware.

**AC3 — truncation of context/evidence/conflicts is visibly marked, never silent**
- `test_context_truncation_produces_visible_marker_distinct_from_statement_truncation` — unit —
  whatever new field(s) Plan defines (e.g. `context_truncated`/`omitted_context_count`, naming
  finalized by Plan mirroring `budget_truncated`/`omitted_statement_count`'s own precedent) must be
  `True`/nonzero when context/evidence content alone is dropped to fit budget, and the existing
  `budget_truncated`/`omitted_statement_count` fields must remain independently meaningful (not
  collapsed into one shared boolean that loses "which subset was truncated" information). Lives in
  `tests/tools/test_knowledge_gateway_packet_assembly.py`.
- `test_new_truncation_marker_present_and_false_when_everything_fits` — unit — the "never absent,
  never silently omitted" counterpart to the existing `test_no_budget_truncation_marker_is_false_and_present_when_everything_fits`.
- `test_new_truncation_markers_threaded_into_run_knowledge_context_response` — integration,
  `tests/tools/test_knowledge_gateway_mcp.py` — verifies the new field(s) reach the live
  `_run_knowledge_context()` response dict, mirroring
  `test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker`'s own pattern.
- `test_knowledge_context_response_schema_accepts_new_context_truncation_marker_field` —
  integration — additive schema field, no `schema_version` bump, mirroring INFRA-347's own
  `budget_truncated`/`omitted_statement_count` precedent.

**AC4 — multi-provider dedup real-corpus-proof gap genuinely closed or honestly re-confirmed open**
- Not a new unit test by itself — this investigation already ran the live gateway against all 7
  corpus entries and found 0 real cross-provider duplicates (see investigation.md). If Plan/human
  review decides to close this via a principled corpus note, add
  `test_corpus_extension_entry_produces_genuine_cross_provider_dedup_hit` — unit,
  `tests/tools/test_knowledge_gateway_packet_assembly.py` or a new
  `tests/tools/test_kgmcp_baseline_corpus_dedup_coverage.py` — running the real gateway against the
  new entry and asserting `deduplicate_statements()` genuinely collapses two same-content
  statements from different providers into one, with both `evidence_ids` merged. If instead honestly
  re-confirmed as still open (no corpus change), add
  `test_live_corpus_has_zero_cross_provider_content_duplicates_documented_limitation` — unit —
  codifying this investigation's own 0/7 live finding as a regression-locking test, so a future
  change that silently starts producing (or silently loses the ability to detect) real duplicates is
  caught, mirroring `#13`'s own `DISCLOSED LIMITATION` precedent in the Phase 3 measurement doc.
- `test_parity_ledger_evidence_hash_uses_canonical_fragment_hash_not_content_hash` — unit — locks in
  the real, newly-found structural fact (this investigation) that parity-sourced statements key
  dedup identity on `record["canonical_fragment_hash"]`, not `_content_hash(text)` — a regression
  guard for the divergence, not a fix (fixing it is out of this ticket's scope per Anti-Drift
  Hazards, unless Plan explicitly brings it in scope).

**AC5 — parity ledger entry added/corrected**
- Not a pytest test — verified via `python3 tools/parity_ledger_validate.py` (or equivalent schema
  validator already used in this repo for `docs/parity_ledger/*.yaml`) confirming the new/updated
  `INFRA-347` entry (or a new `INFRA-35x` entry, per Plan's decision) is schema-valid.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py tests/tools/test_knowledge_gateway_mcp.py -q
```

If a new dedicated corpus-dedup-coverage test file is created:

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_kgmcp_baseline_corpus_dedup_coverage.py -q
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- `test_deduplication_occurs_before_truncation_not_after` (existing) must keep passing unmodified —
  Gap 1's fix must not silently reorder dedup relative to truncation as a side effect of widening
  truncation's measurement scope.
- `test_module_does_not_edit_knowledge_gateway_router` / `test_module_not_referenced_by_any_claude_workflows_file`
  / `test_module_introduces_zero_mcp_server_code` (existing architecture-guard tests) must keep
  passing — confirms this ticket's fix stays inside `tools/knowledge_gateway_packet_assembly.py`
  (and its declared caller `tools/knowledge_gateway_mcp.py`), never touches the frozen router.
- A new guard, `test_assemble_within_budget_never_uses_length_times_constant_estimate` — unit —
  asserts the fixed accounting calls `kgmcp_char_heuristic_v1()` (or the equivalent real primitive)
  on real text for context/evidence/conflicts, not a multiplier applied to the statements-only cost
  — directly enforces the Anti-Drift Hazard against the `len(candidates) * constant` anti-pattern
  named in `assemble_within_budget()`'s own docstring.
- A new guard, `test_budget_returned_semantics_documented_change_is_explicit_not_silent` — unit —
  if `budget_returned`'s meaning changes (e.g. now includes context/evidence cost), assert this is
  reflected in a field the caller can observe as changed-shape, not a silent widening of what the
  same field name means; if `budget_returned` is deliberately left statements-only and a new field
  carries the extended total instead, assert both fields coexist and are independently correct.
- `test_conflicts_never_populated_from_bare_topical_similarity` (existing) must keep passing —
  confirms any new conflicts-truncation logic added for AC1/AC3 does not accidentally introduce a
  semantic/topical-similarity path into `build_conflicts()` itself.
- `test_no_semantic_or_embedding_dependency_introduced` (existing) must keep passing — confirms no
  new dependency is introduced anywhere in this module as a side effect of either gap's fix.
