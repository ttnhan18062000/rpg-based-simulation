---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON
artifact_type: test_plan
tags: [ai, mcp, performance, testing]
---

# Test Plan: TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON

## New Tests — `tests/tools/test_kgmcp_phase4_warm_direct_tool_comparison.py` (10 tests)

- `test_fixture_has_all_seven_corpus_entries` / `test_fixture_uses_same_corpus_as_cold_fixture` —
  never a modified/different corpus.
- `test_all_entries_are_structurally_verified_warm` — `warm_verified is True` and
  `assemble_packet_call_count_on_measured_call == 0` for all 7, plus a dual-signal cross-check
  (`response["cache"]` also independently reports a hit).
- `test_cache_was_genuinely_cleared_before_the_run` — the pre-run hygiene step happened.
- `test_no_disadvantage_silently_excluded_or_redefined` — the honest, real result (gateway never
  faster/lighter) is pinned, mirroring the cold comparison's own anti-cherry-picking guard.
- `test_warm_cost_gap_is_narrower_than_cold_but_did_not_flip_the_verdict` — the one genuinely new
  finding: at least one entry's warm ratio must be measurably better than its cold counterpart
  (caching must demonstrably help something, not be a no-op).
- `test_real_reviewer_verdicts_include_at_least_one_non_gateway_favoring_result` +
  `gateway_equal_or_better not in verdicts` — pins the real 6/1/0 distribution.
- `test_by_routing_shape_summary_covers_all_shapes_and_marks_warm_verified`.
- `test_runner_never_writes_into_the_cold_fixture` — structural guard the new runner writes its
  own fixture, never merges into the historical one.
- `test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner` — mirrors every
  sibling runner's own guard.

## Regression Coverage

- Full `tests/tools/` suite (`CI=true pytest tests/tools/ -m "not slow and not extra_slow"`) run
  after implementation, not just the new test file.

## Explicitly Not Re-Tested Here

- §4.1/§4.2 absolute-threshold warm measurement — already real, already committed by the
  recalibration hotfix; cross-referenced, not repeated.
- The context_search_half recall-proxy false-positive analysis — already disclosed in the cold
  comparison's own results doc; this ticket confirms the same pattern recurs (not warm-specific)
  but does not re-derive the analysis from scratch.
