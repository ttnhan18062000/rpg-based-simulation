---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON
artifact_type: test_plan
tags: [ai, mcp, testing]
---

# Test Plan — TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON

## Regression Surface

**Unit / structural (must keep passing unmodified):**
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py` — the full Phase 1 comparison suite; this
  ticket must never edit `kgmcp_phase1_gateway_runner.py`'s existing `run_corpus()`/`main()`
  behavior, the Phase 1 fixture, or the Phase 1 results doc — every test in this file must stay
  green untouched.
- `tests/tools/test_kgmcp_measurement_baseline.py` — the Phase 0 suite; this ticket does not touch
  `kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`, or the Phase 0 fixture.
- `tests/tools/test_knowledge_gateway_mcp.py` — the Phase 1 MCP tool-surface suite plus the 4 new
  Phase-2 cache-hit tests (11-14: identical-repeat-is-hit, corpus_generation-bump-forces-miss,
  branch-scope-partition, commit-alone-does-not-force-miss); this ticket reads
  `_run_knowledge_context()` and the real cache read-only and must not perturb these.
- `tests/tools/test_knowledge_gateway_cache.py` — orchestrator unit tests for
  `compute_lookup_identity`/`perform_cache_lookup`/`perform_cache_write`/`revalidate_cache_row`.
- `tests/tools/test_retrieval_cache.py` — Level 1 cache read/write/`hit_count`/`provider_result_
  cache_stats` tests; this ticket's own hit-count-delta check must reuse, not duplicate, its
  `test_record_provider_result_cache_hit_increments_hit_count_and_stamps_last_hit_at` pattern.
- `tests/tools/test_knowledge_gateway_redaction.py` — allowlist/redaction/secret-scan/size-cap/
  never-cache-category tests; this ticket's central finding (Risk #1) depends entirely on
  `check_size_cap()`'s real, unmodified behavior staying exactly as tested here.
- `tests/tools/test_knowledge_gateway_router.py`, `tests/tools/test_knowledge_gateway_packet_
  assembly.py`, `tests/tools/test_knowledge_gateway_failure_semantics.py`,
  `tests/tools/test_knowledge_gateway_contract_schemas.py` — same regression surface Phase 1's own
  test_plan.md named; unchanged relevance.

**Integration:**
- `tests/tools/test_search_mcp.py` — `_run_search()` is the underlying provider both cold and warm
  measurement paths ultimately depend on being callable; must remain unmodified.

## New Tests Required

Per AC1 ("each of the 7 corpus entries is run twice (cold + warm) ... warm call's cache-hit status
independently verified"):

- **`test_all_7_corpus_entries_run_cold_and_warm_in_recomparison_fixture`**
  Category: unit (structural, fixture-based).
  Verifies: the new fixture's entry `id` set equals `{e["id"] for e in kgmcp_baseline_corpus.
  CORPUS}` exactly (7 entries), and each entry has both a cold-call and a warm-call sub-object with
  real `time.perf_counter()`-derived wall times (`>= 0`, never fabricated/estimated).
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_warm_call_cache_hit_independently_verified_via_provider_round_trip_spy`**
  Category: unit/integration (real spy, no `unittest.mock`).
  Verifies: for each entry, a plain-Python counting spy assigned via direct attribute reassignment
  (mirroring `test_knowledge_gateway_mcp.py::_patch_small_cacheable_search`'s idiom, restored in a
  `finally` block, never `unittest.mock`/`MagicMock`) on `_kgpa.assemble_packet` records exactly 1
  call across the entry's cold+warm pair whenever the fixture's own `cache_status_warm == "HIT"` —
  and exactly 2 whenever `cache_status_warm == "MISS"`. This is the AC1-mandated "real check ...
  proving the provider round-trip was skipped," recorded per entry as a
  `provider_round_trip_call_count` fixture field.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_warm_call_cache_hit_corroborated_by_db_hit_count_delta`**
  Category: unit/integration (real, code-external signal).
  Verifies: for each entry where `cache_status_warm == "HIT"`, the fixture records a real
  `cache_hit_count_delta` field, derived from a direct SQL read of
  `retrieval_provider_result_cache_rows.hit_count` for the row keyed by
  `(query_hash, repo_branch_scope)` (both from `_kgc.compute_lookup_identity()`) before and after
  the warm call, and that delta equals exactly `1` — mirrors
  `test_retrieval_cache.py::test_record_provider_result_cache_hit_increments_hit_count_and_stamps_
  last_hit_at`'s own direct-SQL-read pattern, applied against the real corpus run rather than a
  synthetic row.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_cache_status_never_reports_hit_when_write_was_rejected_or_row_absent`**
  Category: unit (never-silent/anti-fabrication guard — directly guards against Risk #1's
  size-cap-blocked scenario being mislabeled).
  Verifies: for any entry whose fixture records a non-null `cache_write_rejection_reason` (e.g.
  `"oversized_payload"`), `cache_status_warm` is honestly `"MISS"`, and `provider_round_trip_call_
  count == 2` for that entry — never a fabricated `"HIT"` and never a `1`-count spy result that
  would contradict a rejected write.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

Per AC2 ("§4.1 is computed against the warm-path numbers and reported honestly, whatever the
result"):

- **`test_threshold_4_1_computed_against_warm_path_numbers_only`**
  Category: unit (structural, fixture-based).
  Verifies: every entry's `threshold_4_1_latency` sub-object uses `warm_call_wall_time_ms` (never
  `cold_call_wall_time_ms`) as its `pass`-determining value, and `threshold_ms` is re-derived live
  from the Phase 0 fixture average (935.32, or whatever the currently-committed fixture yields —
  never hand-typed independently of it), matching §4.1's literal warm-hit framing.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_threshold_4_1_reports_honestly_whatever_the_real_result_is`**
  Category: unit (negative-path/honesty guard).
  Verifies: `pass` is computed strictly as `(warm_call_wall_time_ms <= threshold_ms)` for every
  entry — no hardcoded `True`, no entry silently excluded from the aggregate regardless of whether
  it passes or fails (mirrors Phase 1's own
  `test_aggregate_thresholds_summarize_all_7_entries_not_just_a_subset`).
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

Per AC3 ("§4.2 is computed against both cold and warm numbers separately — no assumption that
caching alone satisfies it"):

- **`test_threshold_4_2_computed_separately_for_cold_and_warm`**
  Category: unit (structural, fixture-based).
  Verifies: every entry carries both `threshold_4_2_cold_tokens` and `threshold_4_2_warm_tokens`
  sub-objects, each independently computed via `kgmcp_char_heuristic_v1(json.dumps(response))`
  applied to that call's own real response (never one derived by copying or assuming from the
  other), each with its own `pass`/`derivation`.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_warm_tokens_never_smaller_than_cold_tokens_without_a_stated_explanation`**
  Category: unit (anti-drift, encodes Investigation Risk #3's code-level prediction as a
  falsifiable check rather than a silent assumption).
  Verifies: for every entry where `cache_status_warm == "HIT"`,
  `threshold_4_2_warm_tokens.gateway_tokens >= threshold_4_2_cold_tokens.gateway_tokens`. If a real
  run ever contradicts this, the test fails loudly (forcing investigation of *why* warm shrank —
  e.g. an unexpected `redact_content()` rewrite) rather than silently accepting a result that
  doesn't match the known code path (`hit_response` adds a `cache_key_version` field the cold
  response never had, and `redact_content()` cannot shrink already-relative repo paths).
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

Per AC4 ("§4.3 is recomputed with the now-fixed evidence-ID normalization; the Q2/Q5 architectural
miss ... is reported ... not silently dropped or re-explained away"):

- **`test_threshold_4_3_reuses_phase1s_own_normalization_functions_not_reimplemented`**
  Category: unit (structural, reuse/citation guard).
  Verifies: the new runner module imports (not copy-pastes) `_normalize_phase1_source_id`,
  `_path_only`, and `_compute_threshold_4_3` from `kgmcp_phase1_gateway_runner.py` — checked via
  `ast.parse()` on the new runner's source, asserting an `ImportFrom` node naming
  `kgmcp_phase1_gateway_runner` and those three names.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_q2_q5_recall_still_fails_for_the_documented_architectural_reason`**
  Category: unit (structural, fixture-based; mirrors Phase 1's own
  `test_predicted_q2_q5_recall_miss_is_reported_not_hidden`).
  Verifies: if `Q2_symbol_lookup` or `Q5_test_impact`'s real routing (confirmed via a real,
  unmocked `route()` call inside the same test) still selects `graphify` only, the corresponding
  fixture entry's `threshold_4_3_recall_warm.pass` (or the cold equivalent, whichever is entry's
  authoritative recall check per Plan's decision) is `False` with non-empty `missing_sources` — a
  test that fails loudly if a future change silently marks this a pass without a real, separately-
  justified routing change.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_non_q2_q5_recall_counts_reported_honestly_against_phase1s_own_recorded_counts`**
  Category: unit (structural, fixture-based, honesty guard — does not hardcode an expected
  improvement).
  Verifies: for `Q1`, `Q3`, `Q4`, `Q6`, `Q7`, the new fixture's `missing_sources` counts are present
  with non-empty `derivation`, and the test reports (via an assertion message, not a hard pass/fail
  gate on the count itself) how each compares to Phase 1's own recorded counts (4/8, 2/8, 1/8, 3/8,
  3/8) — proving the doc_id fix's effect is measured and stated, never assumed to be a full fix.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

Frozen-dependency / anti-drift guards (mirroring
`test_knowledge_gateway_mcp.py::test_search_mcp_py_provably_untouched` and Phase 1's own
`test_no_frozen_kgmcp_dependency_edited`):

- **`test_no_frozen_kgmcp_dependency_edited`**
  Category: architecture guard.
  Verifies: `git diff --stat HEAD` contains none of `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_mcp.py`,
  `tools/knowledge_gateway_cache.py`, `tools/knowledge_gateway_redaction.py`,
  `tools/retrieval_cache.py`, `tools/retrieval_events.py`, `tools/knowledge_search.py`,
  `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_baseline_runner.py`,
  `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
  `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`, or
  `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_never_edits_phase1_results_doc`**
  Category: architecture guard (explicit, named separately from the list-based check above since
  it is this ticket's single most emphasized Out-of-Scope item).
  Verifies: `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` does not
  appear in `git diff --stat HEAD`.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_new_runner_never_calls_emit_retrieval_event_or_wrap_functions`**
  Category: architecture guard (AST-based, mirrors Phase 0/Phase 1's own equivalent tests).
  Verifies: the new runner's AST contains no call to `emit_retrieval_event`,
  `wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, or `wrap_context_packet_assembly`.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`**
  Category: architecture guard (extends Phase 1's own `test_zero_mutation_of_real_agent_monitoring_
  corpus_from_comparison_runner` to also cover `knowledge-index/manifest.json`, per Investigation
  Risk #6 — a mid-run index rebuild would silently turn a would-be genuine hit into a
  `provider_generation`-mismatch MISS, confounding the comparison).
  Verifies: `git status --porcelain -- agent-monitoring/` is identical before/after running the new
  runner's `run_corpus()`-equivalent in-process, AND `knowledge-index/manifest.json`'s `built_at`
  value is identical before/after.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold`**
  Category: unit (structural, doc-text guard, mirrors Phase 1's own equivalent test).
  Verifies: `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` contains
  the literal new fixture path, `§4.1`/`§4.2`/`§4.3`, and a literal `PASS`/`FAIL` string per
  threshold per entry actually present in the real result — never a bare narrative summary with no
  per-threshold verdict, and never a fabricated `PASS` for a threshold that genuinely failed.
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

- **`test_missing_recomparison_field_fails_loudly`**
  Category: unit (negative-path proof of the never-silent convention, mirrors Phase 1's own
  `test_missing_comparison_field_fails_loudly`).
  Location: `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`.

## Scoped Pytest Commands

```
pytest tests/tools/test_kgmcp_phase2_baseline_recomparison.py \
       tests/tools/test_kgmcp_phase1_baseline_comparison.py \
       tests/tools/test_kgmcp_measurement_baseline.py \
       tests/tools/test_knowledge_gateway_mcp.py \
       tests/tools/test_knowledge_gateway_cache.py \
       tests/tools/test_retrieval_cache.py \
       tests/tools/test_knowledge_gateway_redaction.py \
       tests/tools/test_knowledge_gateway_router.py \
       tests/tools/test_knowledge_gateway_packet_assembly.py \
       tests/tools/test_knowledge_gateway_failure_semantics.py \
       tests/tools/test_knowledge_gateway_contract_schemas.py -v
```

Never: `pytest tests/`. If a broader sanity pass on the KGMCP domain is warranted:
`pytest tests/tools/ -k "kgmcp or knowledge_gateway or retrieval_cache" -v`.

## Anti-Drift Test Guards

- `test_no_frozen_kgmcp_dependency_edited` / `test_never_edits_phase1_results_doc` — the two
  guards most directly enforcing this ticket's own "measurement-only, never edit the historical
  record" discipline.
- `test_cache_status_never_reports_hit_when_write_was_rejected_or_row_absent` — the guard most
  directly protecting against Investigation Risk #1 being silently glossed over: if the real 8 KB
  cache-write size cap blocks writes for some/all of the 7 entries, this test forces that to be
  reported as `MISS` with a stated `cache_write_rejection_reason`, never quietly relabeled.
- `test_warm_tokens_never_smaller_than_cold_tokens_without_a_stated_explanation` — the guard
  protecting against silently assuming §4.2 is solved by caching (the epic's own explicit
  Out-of-Scope item).
- `test_q2_q5_recall_still_fails_for_the_documented_architectural_reason` — protects against
  silently widening routing (or otherwise loosening the recall comparison) to manufacture a pass
  for the two entries this ticket's own Scope predicts will still miss.
- `test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run` — protects the comparison's
  internal validity: a mid-run index rebuild silently converting an intended-genuine-hit entry into
  a `provider_generation`-mismatch MISS would corrupt the cold-vs-warm comparison without any
  visible symptom unless this guard exists.
