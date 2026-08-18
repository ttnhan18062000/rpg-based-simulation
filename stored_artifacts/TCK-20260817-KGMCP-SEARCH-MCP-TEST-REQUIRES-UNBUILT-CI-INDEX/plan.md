---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX
tags: [ai, mcp, testing]
---

# Plan — TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX

## Files and guards

1. `tests/tools/test_knowledge_search.py`: add `_numpy_available()` and `_bm25_deps_available()`
   helpers (mirroring the existing `_deps_available()` pattern). Class-level
   `@pytest.mark.skipif` on `TestBm25BuildLoad` (3 failing methods + 2 already-passing ones,
   thematically all bm25-related). Inline skip in
   `TestHybridFusionWiring::test_lexical_only_match_surfaced_through_cmd_query` (numpy only).
2. `tests/tools/test_hybrid_retrieval.py`: inline numpy import-guard in
   `TestModeRoutingGuard::test_vector_and_keyword_modes_do_not_call_fusion_helper`.
3. `tests/tools/test_kgmcp_measurement_baseline.py`: index-existence skip in
   `test_corpus_baseline_wall_time_and_tool_call_count_are_plausible`; index + `graphify`
   skip in `test_zero_mutation_of_real_agent_monitoring_corpus`.
4. `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`: index + `graphify` skip in
   both `test_branch_partition_live_direct_call_against_a_real_current_row` (plus a further
   `row is None` skip — this test also depends on a specific gitignored local-history L2 cache
   row from an earlier session's own run, not reproducible on any fresh checkout even with
   index+graphify present) and `test_stale_rejection_and_unrelated_change_live_real_corpus_round_trip`
   (index + graphify only — this one bootstraps its own fresh identity, no historical-row
   dependency). The latter's real CI failure and this session's local full-file timeout were both
   confirmed to be resource-contention artifacts from running alongside the file's other
   already-`@pytest.mark.slow`/`@pytest.mark.extra_slow`-marked tests without the real CI `-m
   "not slow"` filter applied — under the actual filter it passes cleanly in ~10s for the whole
   file.
5. `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`: index + `graphify` skip in
   `test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner` (already marked
   `@pytest.mark.extra_slow`, but the "API / tools / logging" CI job's filter is `-m "not slow"`
   only — it does not also exclude `extra_slow`, unlike the one job in the workflow that uses `-m
   "not slow and not extra_slow"` — so this test IS collected and run there; separately flagged
   as a follow-up, not fixed here to keep this ticket's diff to test-level guards only).
6. `tests/tools/test_knowledge_gateway_failure_semantics.py`: index skip in
   `test_gateway_down_search_mcp_test_mode_still_works` (the ticket's original scope); `graphify`
   skip in `test_gateway_down_graphify_cli_still_works`.

## Out of scope
- `.github/workflows/test.yml`'s `-m "not slow"` vs `-m "not slow and not extra_slow"`
  inconsistency across fast-lane jobs — real, but a distinct, wider finding affecting 7 jobs, not
  specific to knowledge-tooling tests. Filed as a separate follow-up ticket rather than fixed here.
- `requirements.txt`'s deliberate exclusion of the ML stack — confirmed correct, not touched.
- `tools/knowledge_search.py`'s own unconditional `numpy` import inside `cmd_query()`'s bm25
  branch (arguably a source-code correctness gap, not just a test-skip issue) — noted but not
  fixed; the test guards are sufficient to stop the CI failures, and changing production import
  behavior is a separate, judgment-call decision outside a test-fix ticket's scope.
