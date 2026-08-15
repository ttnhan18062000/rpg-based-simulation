---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-BASELINE-COMPARISON
artifact_type: test_plan
tags: [ai, mcp, testing]
---

# Test Plan — TCK-20260815-KGMCP-P1-BASELINE-COMPARISON

## Regression Surface

**Unit / structural (must keep passing unmodified):**
- `tests/tools/test_kgmcp_measurement_baseline.py` — the full Phase 0 suite; this ticket must not
  touch `kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`, or the Phase 0 fixture, and every
  test in this file (corpus coverage, `char_heuristic_v1` formula match, zero-mutation-of-
  `agent-monitoring/` guard, frozen-file guards) must stay green.
- `tests/tools/test_knowledge_gateway_mcp.py` — the Phase 1 MCP tool-surface suite (12 tests);
  this ticket calls `_run_knowledge_context()` read-only and must not perturb its own passing
  state or the frozen response-schema validation it exercises.
- `tests/tools/test_knowledge_gateway_router.py` — 31 tests over `route()`; this ticket depends on
  (reads, does not modify) the router's real per-query provider selection, so these must stay
  green as the ground truth for which providers each corpus entry actually calls.
- `tests/tools/test_knowledge_gateway_packet_assembly.py` — 27 tests over `assemble_packet()`/
  `kgmcp_char_heuristic_v1`; this ticket reuses `kgmcp_char_heuristic_v1` directly, so a change
  here would silently change this ticket's own token measurements.
- `tests/tools/test_knowledge_gateway_failure_semantics.py` — 13 tests; establishes
  `provider_failures`'s real, always-present-field behavior this ticket's runner must report
  honestly per entry.
- `tests/tools/test_knowledge_gateway_contract_schemas.py` — schema-shape guards for the frozen
  `docs/engine/contracts/knowledge_gateway_mcp/*.schema.json` files this ticket's runner validates
  responses against indirectly (via `_run_knowledge_context()`'s own internal validation).

**Integration (must keep passing, broader domain sanity):**
- `tests/tools/test_search_mcp.py` — `_run_search()` is the underlying provider Phase 1's
  `context_search` calls; must remain independently callable/unmodified per the fail-open
  precedent this ticket does not touch.

## New Tests Required

Per AC #1 ("all 7 corpus entries run through the real gateway, not a subset, not a mock"):
- **`test_all_7_corpus_entries_present_in_comparison_fixture`**
  Category: unit (structural, fixture-based).
  Verifies: `kgmcp_phase1_baseline_comparison_results.json`'s entry `id` set equals
  `{e["id"] for e in kgmcp_baseline_corpus.CORPUS}` exactly (7 entries, no subset, no extras,
  no cherry-picking).
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

- **`test_comparison_runner_calls_real_run_knowledge_context_not_a_mock`**
  Category: unit (AST-based structural guard, mirrors
  `test_kgmcp_measurement_baseline.py::test_runner_module_never_calls_emit_retrieval_event_or_wrap_functions`).
  Verifies: the new runner module's AST contains a real call to `_run_knowledge_context` (or
  imports `knowledge_gateway_mcp` and calls it), and contains no `unittest.mock`/`MagicMock`/
  monkeypatch usage in the corpus-running code path.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

Per AC #2 ("each of §4's predeclared thresholds computed and reported PASS/FAIL, per entry and in
aggregate, with actual numbers shown"):
- **`test_each_entry_reports_latency_threshold_pass_fail_with_numbers`**
  Category: unit (structural, fixture-based).
  Verifies: every entry in the new fixture has a `threshold_4_1_latency` sub-object with
  `pass: bool`, `gateway_wall_time_ms: float`, `threshold_ms: 935.32` (or the value recomputed
  from the currently-committed Phase 0 fixture average — never hardcoded independently of it),
  and a non-empty `derivation` string — never a bare boolean with no supporting numbers.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

- **`test_each_entry_reports_token_threshold_pass_fail_with_numbers`**
  Category: unit (structural, fixture-based).
  Verifies: every entry has a `threshold_4_2_tokens` sub-object with `pass: bool`,
  `gateway_tokens: int` (measured via `knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1`
  over the real response payload), `threshold_tokens: 1263.57`, `derivation`.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

- **`test_each_entry_reports_recall_threshold_pass_fail_with_numbers`**
  Category: unit (structural, fixture-based).
  Verifies: every entry has a `threshold_4_3_recall` sub-object with `pass: bool`,
  `baseline_sources: list[str]`, `gateway_sources: list[str]`, `missing_sources: list[str]`
  (baseline sources not covered by gateway sources under the documented normalization rule), and
  `derivation` stating the exact normalization applied (per Investigation Risk #3). Missing
  entries must never be silently coerced into a pass.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

- **`test_aggregate_thresholds_summarize_all_7_entries_not_just_a_subset`**
  Category: unit (structural, fixture-based).
  Verifies: a top-level `aggregate` object reports per-threshold pass counts out of 7 and an
  overall `all_thresholds_pass: bool`, and that `all_thresholds_pass` is `False` whenever any
  individual entry's any threshold is `False` (no aggregate that papers over a per-entry miss).
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

Per AC #3 ("if any threshold is missed, the ticket's Completion Summary states this plainly — no
threshold redefined, no result mischaracterized"):
- **`test_no_threshold_formula_redefined_from_measurement_baseline_contract`**
  Category: unit (structural, cross-doc guard).
  Verifies: the new fixture's threshold constants (`935.32`, `1263.57`) match values re-derivable
  from `measurement_baseline_contract.md`'s own stated corpus-wide averages (`1870.648`,
  `2527.143`) via the exact §4.1/§4.2 formulas — catches an accidental or convenient threshold
  drift.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

- **`test_predicted_q2_q5_recall_miss_is_reported_not_hidden`** (anti-drift-flavored acceptance
  test, given Investigation Risk #2's specific prediction)
  Category: unit (structural, fixture-based).
  Verifies: if `Q2_symbol_lookup` or `Q5_test_impact`'s real routing selected `graphify` only
  (confirmed against the real `route()` call inside the same test, not assumed), the corresponding
  fixture entry's `threshold_4_3_recall.pass` is `False` and `missing_sources` is non-empty — a
  test that would fail loudly if a future change silently marks this a pass without a real
  behavior change (e.g. router now also calling `context_search`, which would be a legitimate,
  separately-noted change) or without properly deriving `missing_sources`.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

Per AC #4 ("fixture and test suite structurally enforce the never-silent convention"):
- **`test_all_comparison_entries_carry_nonempty_derivation_strings`**
  Category: unit (structural, mirrors
  `test_kgmcp_measurement_baseline.py::test_all_new_sections_carry_a_derivation_string`).
  Verifies: every threshold sub-object on every entry has a truthy `derivation` field — a future
  gateway change that drops a comparison field must fail this test loudly, not degrade to a
  silently-passing default.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

- **`test_missing_comparison_field_fails_loudly`**
  Category: unit (negative-path proof of the never-silent claim).
  Verifies: constructing a comparison-fixture-shaped dict with a threshold sub-object deliberately
  omitted, then running the same field-presence assertions used elsewhere in this suite against it,
  raises `AssertionError` — proves the guard itself is load-bearing, not vacuous.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

Frozen-dependency / anti-drift guards (mirroring
`test_knowledge_gateway_mcp.py::test_search_mcp_py_provably_untouched` and
`test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_introduced`):
- **`test_no_frozen_kgmcp_dependency_edited`**
  Category: architecture guard.
  Verifies: `git diff --stat HEAD` contains none of `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_mcp.py`,
  `tools/retrieval_events.py`, `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_baseline_runner.py`, or the Phase 0 fixture path.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

- **`test_new_runner_never_calls_emit_retrieval_event_or_wrap_functions`**
  Category: architecture guard (AST-based, mirrors the Phase 0 runner's own equivalent test).
  Verifies: the new runner's AST contains no call to `emit_retrieval_event`,
  `wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, or `wrap_context_packet_assembly` — this
  ticket must not write into `agent-monitoring/events.jsonl` either, same constraint as Phase 0's
  runner.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

- **`test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`**
  Category: architecture guard (mirrors Phase 0's own `test_zero_mutation_of_real_agent_monitoring_corpus`).
  Verifies: `git status --porcelain -- agent-monitoring/` is identical before and after running
  the new runner's `run_corpus()`-equivalent function in-process.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

- **`test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold`**
  Category: unit (structural, doc-text guard, mirrors
  `test_predeclared_thresholds_cite_recorded_baseline_numbers`).
  Verifies: `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` contains
  the literal new fixture path, and the literal strings `PASS`/`FAIL` (or equivalent) appear at
  least once per threshold per the doc's own presentation — never a bare narrative summary with
  no per-threshold verdict.
  Location: `tests/tools/test_kgmcp_phase1_baseline_comparison.py`.

## Scoped Pytest Commands

```
# This ticket's own new/changed test file plus every KGMCP sibling suite it depends on or
# regression-guards, scoped to tools/ knowledge-gateway domain only:
pytest tests/tools/test_kgmcp_phase1_baseline_comparison.py \
       tests/tools/test_kgmcp_measurement_baseline.py \
       tests/tools/test_knowledge_gateway_mcp.py \
       tests/tools/test_knowledge_gateway_router.py \
       tests/tools/test_knowledge_gateway_packet_assembly.py \
       tests/tools/test_knowledge_gateway_failure_semantics.py \
       tests/tools/test_knowledge_gateway_contract_schemas.py -v
```

Never: `pytest tests/`. If a broader agent-monitoring sanity pass is warranted (e.g. to confirm
`agent-monitoring/` truly wasn't mutated across a full local run), scope it explicitly:
`pytest tests/tools/ -k "kgmcp or knowledge_gateway"`.

## Anti-Drift Test Guards

- `test_no_frozen_kgmcp_dependency_edited` (above) — catches any accidental edit to the 4 frozen
  gateway modules or the Phase 0 corpus/runner/fixture, which would invalidate the comparison's
  premise (measuring a moving target against a moving baseline).
- `test_predicted_q2_q5_recall_miss_is_reported_not_hidden` (above) — the most important anti-drift
  guard in this suite: it exists specifically so that a future edit cannot quietly make §4.3
  "pass" for Q2/Q5 by loosening the recall comparison, without that being a loud, visible,
  independently-justified change to the router or the comparison method itself.
- `test_no_threshold_formula_redefined_from_measurement_baseline_contract` (above) — catches the
  literal "quietly resolve a miss by adjusting the threshold" anti-pattern the ticket's own Out of
  Scope section names explicitly.
- Reuse of `test_kgmcp_measurement_baseline.py`'s `_run_with_timeout`-style bounded live smoke
  check pattern for exactly one corpus entry (not all 7) if any new test needs a genuinely live,
  non-fixture-based re-invocation — avoids re-running all 7 real gateway calls (each incurring a
  real `graphify query` subprocess and/or `_run_search()` call) on every `pytest` invocation, while
  still proving the runner is "still really callable."
