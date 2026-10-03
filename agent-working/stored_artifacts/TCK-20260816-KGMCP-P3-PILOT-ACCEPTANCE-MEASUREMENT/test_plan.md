---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT
artifact_type: test_plan
tags: [ai, mcp, testing]
---

# Test Plan — TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT

This ticket is measurement-only, but it still ships real, testable Python tooling (the new runner)
plus a real, one-time corpus-scale measurement run. "Tests" here means both: (A) unit/structural
tests proving the **runner itself** is correct (mirroring
`tests/tools/test_kgmcp_phase1_baseline_comparison.py`/`test_kgmcp_phase2_baseline_recomparison.py`'s
own precedent), and (B) the actual corpus-scale measurement run plan that produces this ticket's
real, honest findings. Neither substitutes for the other.

## Regression Surface

Existing tests that must keep passing, unmodified, throughout this ticket (no gateway/router/
packet_assembly/cache code changes are in scope, so none of these should need edits):

**Unit:**
- `tests/tools/test_knowledge_gateway_redaction.py` (includes `TestSizeCap`'s post-hotfix
  `MAX_PAYLOAD_BYTES == 65536` assertions).
- `tests/tools/test_knowledge_gateway_cache.py` (Level 1 + Level 2 orchestration unit tests,
  including `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`,
  `test_revalidate_context_packet_row_rejects_cross_branch_even_with_identical_dependencies`).
- `tests/tools/test_knowledge_gateway_packet_assembly.py` (dedup, `build_conflicts()`,
  `assemble_within_budget()`, `kgmcp_char_heuristic_v1`).
- `tests/tools/test_retrieval_cache.py` (Level 1 + Level 2 SQL layer).
- `tests/docs/test_redaction_retention_policy_doc.py` (includes the doc-vs-live-constant
  cross-check added by the hotfix).

**Integration:**
- `tests/tools/test_knowledge_gateway_mcp.py` (all Level 1 + Level 2 `_run_knowledge_context()`
  integration tests, `:658-950` for the Level 2 set specifically).
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py`,
  `tests/tools/test_kgmcp_phase2_baseline_recomparison.py` — including their own frozen-dependency
  guard tests (`test_no_frozen_kgmcp_dependency_edited`, `test_never_edits_phase1_results_doc`,
  `test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`). These must keep passing
  **because this ticket's own runner is a new file that never edits either predecessor runner or
  fixture** — a failure here would itself be evidence this ticket violated its own Out of Scope.

**Arena-combat:** not applicable — this ticket touches no combat/simulation code.

## New Tests Required

Per the ticket's 8 Acceptance Criteria (`tickets/inprogress/TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT.md`):

### AC1 — per-stage timings captured and reported separately for all 7 entries

- **`test_new_runner_never_edits_any_of_the_4_frozen_predecessor_files`**
  Category: architecture guard. Verifies (via a `git diff --stat HEAD` check, same technique as
  the Phase 2 guard) that `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py` remain
  byte-unchanged by this ticket's own diff. Location:
  `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py` (new file, mirroring the
  predecessor guard-test module naming).
- **`test_new_runner_imports_not_reimplements_phase1_and_phase2_pure_helpers`**
  Category: unit/architecture guard. Asserts the new runner's module object holds direct references
  to `kgmcp_phase1_gateway_runner._compute_threshold_4_3`/`_normalize_phase1_source_id`/`_path_only`
  (identity check, `is`, not just equal output) — proves reuse, not parallel reimplementation, per
  this repo's Gate Integrity discipline. Same file.
- **`test_per_entry_result_records_lookup_and_end_to_end_timings_as_distinct_fields`**
  Category: unit. Runs the new runner's single-entry function against one corpus entry (real call,
  not mocked) and asserts the returned dict carries separately-named, separately-valued timing
  fields for at least `lookup_and_validation_ms`, `fallback_and_assembly_ms` (or `None` on a
  genuine hit, since fallback/assembly never runs), and `end_to_end_ms` — never a single blended
  number standing in for all of them. Same file.
- **`test_end_to_end_ms_equals_sum_of_whichever_sub_stages_actually_ran`**
  Category: unit (honesty guard). Per `measurement_baseline_contract.md` §2.5's reconciliation
  rule: for a genuine cache-hit entry, `end_to_end_ms` should be commensurate with
  `lookup_and_validation_ms` alone (no fallback/assembly component); for a genuine miss entry, it
  should be commensurate with `lookup_and_validation_ms + fallback_and_assembly_ms`. A tolerance
  band (not exact equality — real wall-clock overhead exists between stages) should be asserted,
  documented in the test itself. Same file.

### AC2 — budget-respecting behavior measured with a constrained `budget_tokens`

- **`test_constrained_budget_request_shape_is_used_for_at_least_one_real_corpus_call`**
  Category: integration. Confirms the runner's budget-measurement pass genuinely passes a
  `budget_tokens` value below the gateway's `DEFAULT_BUDGET_TOKENS` (4000) into
  `_run_knowledge_context()` for real — not the DD1(b) exact-default-parity shape Phase 2 used for
  its own latency/token thresholds (this ticket has a different, budget-specific measurement goal,
  so reusing Phase 2's exact-parity choice verbatim would not exercise AC2 at all). Location: new
  test file.
- **`test_full_response_payload_tokens_reported_against_requested_budget_with_documented_tolerance`**
  Category: unit. Asserts the runner computes `kgmcp_char_heuristic_v1_token_count(json.dumps(response))`
  over the **full** response payload (not `response["budget_returned"]`, which per Investigation is
  a `statements[]`-only figure that is `<= budget_requested` by construction and would trivially
  "pass" without ever really measuring compliance) and compares it against the requested
  `budget_tokens` at the documented ±20% tolerance from `redaction_retention_policy.md` §8. Same
  file.

### AC3 — conflict visibility checked and reported (real measurement, not a documentation claim)

- **`test_conflicts_field_is_inspected_for_every_real_corpus_response`**
  Category: integration. Asserts the runner reads `response["conflicts"]` for every one of the 7
  real corpus calls and records its length/content honestly — including the disclosed real
  possibility (per Investigation Q3) that all 7 are empty. Same file.
- **`test_zero_observed_conflicts_is_reported_as_a_disclosed_corpus_limitation_not_a_pass`**
  Category: unit (honesty guard). If the real run's conflict count is 0 across all 7 entries, the
  runner's own report dict must carry an explicit `conflicts_observed_in_corpus: false` /
  limitation-note field distinct from a bare "criterion satisfied" flag — this test asserts that
  field exists and is populated correctly given a synthetic 0-conflict input, so a future silent
  regression (someone marking AC3 "PASS" on 0 real conflicts) is caught. Same file.

### AC4 — median latency and delivered-token counts vs. a justified baseline, honest FAIL if no improvement

- **`test_baseline_choice_is_recorded_with_explicit_derivation_string`**
  Category: unit. Asserts the runner's output dict names, per numeric threshold reported, exactly
  which baseline(s) it was computed against (Phase 1 cold / freshly-remeasured Level-1-warm / both)
  and includes a non-empty `derivation` string — mirrors Phase 1/2's own `derivation` field
  convention. Same file.
- **`test_median_not_mean_is_used_for_the_closing_criterion`**
  Category: unit. §21's closing bullet says "lower median end-to-end latency" explicitly (unlike
  §4.1/§4.2's own mean-based formulas) — asserts the runner uses `statistics.median`, not
  `statistics.mean`, for this specific comparison, so the two formulas are not silently conflated.
  Same file.
- **`test_fail_result_is_reported_honestly_when_synthetic_input_shows_no_improvement`**
  Category: unit (Gate Integrity guard). Feeds the aggregate-computation function a synthetic
  input where Level 2's numbers are *worse* than the baseline and asserts the function reports
  `pass: False` — proves the runner is structurally incapable of only ever reporting PASS. Same
  file.

### AC5 — recall recomputed and compared against Phase 1/Phase 2's own recorded counts

- **`test_recall_reuses_compute_threshold_4_3_against_both_phase1_and_phase2_recorded_counts`**
  Category: unit. Asserts the recall comparison is computed via the imported
  `_compute_threshold_4_3` (never reimplemented) and that the per-entry report includes both the
  Phase 1 and Phase 2 recorded `missing_sources` counts alongside this ticket's own real count —
  mirroring `kgmcp_phase2_gateway_runner.py`'s own `recall_missing_count_comparison_to_phase1`
  field precedent, extended to compare against both predecessors. Same file.
- **`test_recall_regression_relative_to_either_predecessor_is_flagged_not_glossed_over`**
  Category: unit (honesty guard). Synthetic input where this run's missing-source count for one
  entry is higher than Phase 1/Phase 2's recorded count — asserts the report marks that entry with
  an explicit regression flag. Same file.

### AC6 — stale-rejection / unrelated-change / branch-partition / uncommitted-change re-verified at real-corpus scale

- **`test_stale_rejection_verified_against_a_real_changed_cited_source_for_at_least_one_real_entry`**
  Category: integration. Picks a corpus entry with a known real cited `path` from its own real
  cold response, re-calls `_run_knowledge_context()` with that path in `changed_paths`, and asserts
  the packet is genuinely refreshed (not served from a stale Level 2 row) — a real call through the
  live gateway, not a synthetic row dict (distinguishing this from the sibling wiring ticket's own
  unit tests, per Investigation's Prior Work finding). Location: new test file.
- **`test_unrelated_changed_path_does_not_invalidate_a_real_cached_packet`**
  Category: integration. Same real-entry setup, but `changed_paths` contains a path known **not**
  to be among that entry's real cited evidence — asserts the second call is still a genuine hit.
- **`test_branch_partition_verified_with_a_real_but_synthetic_incompatible_branch_scope`**
  Category: integration (disclosed as targeted, not full-corpus-organic — per Investigation Q3, a
  second real incompatible branch cannot be produced by the 7-entry corpus alone). Calls
  `revalidate_context_packet_row()` directly (real function, real row, synthetic
  `current_repository_id`/`current_branch` args representing a different branch) and asserts
  `False`. This must be labeled in its own docstring as testing the real revalidation function
  directly rather than through a full `_run_knowledge_context()` round trip with an actual second
  git branch, and that distinction must also appear in the results doc.
- **`test_uncommitted_change_invalidation_verified_with_a_real_changed_paths_argument`**
  Category: integration. Same shape as the stale-rejection test above — `changed_paths` is exactly
  how "uncommitted changes" are represented in this gateway's contract (no separate git-diff-based
  mechanism exists), so this test and the stale-rejection test above jointly cover this criterion;
  the test plan should not double-count them as two independent real-world verifications beyond
  what the shared mechanism actually demonstrates.

### AC7 — honest completion summary if any criterion is missed

- No dedicated test — this is a documentation/process requirement on the ticket's own Completion
  Summary, verified by `done-checker` at Finalize, not by pytest.

### AC8 — schema-valid `docs/parity_ledger/infrastructure.yaml` entry

- **`test_new_infrastructure_parity_entry_is_schema_valid`**
  Category: unit. Standard parity-ledger schema-validation test, mirroring the pattern already used
  for `INFRA-344`/`INFRA-345` (validated via `docs/parity_ledger/schema.json` and
  `tools/parity_ledger_writer.py::write_entry()`'s own validation path) — run as part of Parity
  phase tooling, not hand-authored YAML.

## Scoped Pytest Commands

Regression + new-test verification, scoped to the Knowledge Gateway MCP domain (never
`pytest tests/`):

```
pytest tests/tools/test_knowledge_gateway_mcp.py \
       tests/tools/test_knowledge_gateway_cache.py \
       tests/tools/test_knowledge_gateway_redaction.py \
       tests/tools/test_knowledge_gateway_packet_assembly.py \
       tests/tools/test_retrieval_cache.py \
       tests/tools/test_kgmcp_phase1_baseline_comparison.py \
       tests/tools/test_kgmcp_phase2_baseline_recomparison.py \
       tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py \
       tests/docs/test_redaction_retention_policy_doc.py \
       -v
```

The real, one-time corpus-scale measurement run itself (analogous to the hotfix's own manual
`run_corpus()` invocation) is **not** part of this pytest command — it is run once, by hand, during
Implementation, exactly mirroring both predecessor runners' own "never wired into pytest's fast
loop" convention (`kgmcp_phase1_gateway_runner.py`/`kgmcp_phase2_gateway_runner.py` module
docstrings). Its real output is what produces the new results doc and the new committed fixture
this ticket must write.

## Anti-Drift Test Guards

- **Frozen-file guard** (`test_new_runner_never_edits_any_of_the_4_frozen_predecessor_files`, plus
  a parallel check against `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
  `kgmcp_phase2_gateway_runner.py`, `kgmcp_baseline_corpus.py`, and both predecessor fixture JSONs)
  — catches any accidental edit to inputs this ticket must only ever read.
- **Budget-tolerance honesty guard** (`test_full_response_payload_tokens_reported_against_requested_budget_with_documented_tolerance`)
  — specifically catches the trap Investigation surfaced: measuring `budget_returned` instead of
  the real full-payload token count would make AC2 "pass" by construction, regardless of real
  gateway behavior. This guard exists precisely to prevent that silent substitution.
  - **Median-vs-mean guard** (`test_median_not_mean_is_used_for_the_closing_criterion`) — catches
  silent conflation of §21's closing-criterion formula with §4.1/§4.2's differently-shaped
  mean-based formulas.
- **FAIL-capable guard** (`test_fail_result_is_reported_honestly_when_synthetic_input_shows_no_improvement`)
  — catches a runner refactor that accidentally makes the pass/fail computation structurally
  incapable of ever reporting FAIL (the same class of guard both predecessor tickets' own honest-
  reporting discipline depends on).
- **Recall-regression guard** (`test_recall_regression_relative_to_either_predecessor_is_flagged_not_glossed_over`)
  — catches silent recall regressions being reported as neutral/unremarked rather than flagged, per
  AC5's explicit "any regression is reported plainly" requirement.
- **Corpus-limitation disclosure guard** (`test_zero_observed_conflicts_is_reported_as_a_disclosed_corpus_limitation_not_a_pass`)
  — catches the specific failure mode named in this ticket's own Out of Scope: silently treating an
  unexercised criterion as satisfied rather than disclosing the real corpus limitation.
