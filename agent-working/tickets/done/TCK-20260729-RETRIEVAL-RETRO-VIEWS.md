---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-RETRO-VIEWS
phase: done
date: 2026-07-29
tags: [observability, agent-monitoring, retro]
---

# TCK-20260729-RETRIEVAL-RETRO-VIEWS

## Title
Extend generate_retro.py/query.py with dashboard/retro views for retrieval quality

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The author wants new query functions (in generate_retro.py/query.py, or a clearly-scoped new module they import) that produce the decision-support dashboard views described in the idea doc: cache hit/miss/stale-rejection rates by cache level, candidate-to-selected and selected-to-cited ratios as noise indicators, freshness/authority distribution, and follow-up/expansion rate as an initial-packet adequacy indicator. Each view must be unit-tested against a fixture events file rather than only eyeballed against live data. This extends the existing dashboard/retro query layer rather than replacing it or building a new frontend/UI surface from scratch.

## Scope
- New query/aggregation functions in generate_retro.py and/or query.py (placement decided per each file's existing precedent — generate_retro.py's graceful build-on-demand/fallback-to-raw-JSONL-scan style vs. query.py's hard SQLite-index requirement)
- Cache hit/miss/stale-rejection rates broken down by cache level
- Candidate-to-selected and selected-to-cited ratios as noise indicators
- Freshness/authority distribution, including correct handling of an UNRATED sentinel
- Follow-up/expansion rate as an initial-packet-adequacy indicator
- New retro report sections rendered via the existing conditional-render pattern
- Fixture-based unit tests for every new view, following the tests/fixtures/agent_monitoring/*.jsonl convention

## Out of Scope
- No execution_id or provider fields added to runs.jsonl/events.jsonl, and no cross-provider comparison views (forbidden this phase; flag as a Phase 4b follow-on if needed)
- No new dashboard frontend/UI surface — extends generate_retro.py/query.py/existing dashboard query layer only
- No wiring into .claude/workflows/*.js — views are built and tested against fixture/test-invocation data only, since no Phase 3 module is wired into real agent runs yet
- No live Codex pilot execution
- Must not assume a bounded/prunable retention window — retrieval events are retain-forever/append-only; any windowed aggregation must take an explicit cutoff argument (e.g. --days), never an assumed default

## Acceptance Criteria
- [x] A fixture events list with cache_status values at multiple cache levels returns correct hit/miss/stale-rejection rates by cache level
- [x] A fixture events list with candidate_count/selected_count/cited-source-hash-count fields returns correct candidate-to-selected and selected-to-cited ratios; a zero-candidate group does not raise ZeroDivisionError
- [x] A fixture events list with authority_counts/freshness_counts fields (including an UNRATED sentinel) returns a correct distribution without crashing on the sentinel
- [x] A fixture events list with adequacy_verdict and expansion_reason/expansion_count fields returns a correct follow-up/expansion rate
- [x] Each new function is unit-tested against an in-repo fixture, never validated only against live data
- [x] No new frontend/UI file is added; new functions live in generate_retro.py and/or query.py, and the retro report renders new sections following the existing conditional-render pattern

## Related Tickets
- TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT
- TCK-20260729-HYBRID-RETRIEVAL-FUSION
- TCK-20260729-RETRIEVAL-CACHE-LEVELS
- TCK-20260729-CONTEXT-PACKET-ASSEMBLY
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION
- TCK-20260718-RETRO-STATS-REFACTOR
- TCK-20260706-MONITORING-REASON-CODE
- TCK-20260708-RETRO-TAG-BREAKDOWN
- TCK-20260719-RETRO-OUTLIER-FLAGS

## Related Docs
- docs/agent-monitoring/schema.md
- docs/observability/retrieval_retention_redaction_policy.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase4.md
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/query.py
- tools/agent-monitoring/writer.py
- tools/hybrid_retrieval.py
- tools/retrieval_cache.py
- tests/tools/test_generate_retro.py
- tests/tools/test_query.py
- tests/fixtures/agent_monitoring/*.jsonl

## Assumptions / Open Questions
- HARD DEPENDENCY: this ticket depends on TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT landing first — this ticket's views assume a retrieval-event field shape that must be defined and actually emitted by that ticket; field names used here must be taken from that ticket's actual shipped output, not guessed in advance of it
- query.py hard-fails (sys.exit(1)) on a missing SQLite index while generate_retro.py degrades gracefully to a raw JSONL scan — planning must be explicit about which file each new function lives in and why, following the existing precedent rather than inventing a third pattern
- Real retrieval-event volume will be near-zero at ship time since no workflow wiring exists yet; fixture-based testing is the only pre-adoption validation path

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260729-RETRIEVAL-RETRO-VIEWS/plan.md`'s revised 8 steps,
in the suggested order (4 → 1 → 2 → 3 → 5 → 6 → 7 → 8). No implementation-level deviations from the
plan; the plan's own "Deviations" section (Revision 1, Step 8 field-shape fix) was pre-existing and
did not need further amendment.

- **Step 4 (imports):** Added `from hybrid_retrieval import UNRATED` and `from retrieval_cache
  import HIT, MISS, STALE_REJECTED, INDEX_CACHE_CATEGORY, QUERY_CACHE_CATEGORY,
  PACKET_CACHE_CATEGORY` to `generate_retro.py`'s existing `sys.path`-wired import block, both
  `# noqa: E402` matching the file's existing convention.
- **Step 1 (`candidate_to_selected_aggregate`/`selected_to_cited_aggregate`):** Added running-sum
  accumulators inside the existing per-event ratio loop (no second iteration over
  `retrieval_events`); both aggregates zero-division-guarded (`ratio: None` when the denominator
  is 0). Existing per-event `candidate_to_selected_ratios`/`selected_to_cited_ratios` logic
  untouched.
- **Step 2 (`authority_distribution`/`freshness_distribution`):** Plain `Counter.update()` per
  event inside the same loop — no allowlist filter, so `UNRATED`/`"unrated"` buckets naturally
  in the merged distribution.
- **Step 3 (`expansion_rate`):** Unconditional formula per Resolved Decision 1 — `0.0` when
  `retrieval_events` is empty. Code comment above the computation cites why the
  adequacy_verdict-conditional alternative was rejected (no shipped wrapper emits
  `expansion_reason`/`expansion_count` today).
- **Step 5 (architecture guards):** Extended
  `test_function_is_read_only_no_write_call_or_file_open_in_write_mode` with explicit
  `EVENTS_FILE`/`RUNS_FILE`/`load_jsonl`/`DEFAULT_DB_PATH`-absence assertions. Added
  `test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants` asserting no
  bare `"hit"`/`"miss"`/`"stale-rejected"`/cache-category-name literals in
  `compute_retrieval_metrics()`'s source, and that the Step 4 constants + `UNRATED` are imported
  at module level.
- **Step 6 (rendered section):** `generate()` now calls
  `retrieval_metrics = compute_retrieval_metrics(events)` alongside the existing
  `compute_retro_metrics()` call. New `## Retrieval Quality` section inserted after the existing
  Outliers block and before Notes, gated on `if retrieval_metrics["retrieval_event_count"]:`.
  Renders the `--all`-only caveat verbatim, a Cache Rates by Level table (headers sourced from the
  imported `HIT`/`MISS`/`STALE_REJECTED` constants rather than re-literaled strings), a Noise
  Indicators table (ratio `None` rendered as `"n/a"`), Freshness/Authority Distribution tables
  (unrated bucket included, empty case renders a `_No ... data this period._` line rather than a
  crash), and an Expansion Rate line. `fmt_pct(n, total)` expects two ints, not a pre-computed
  float ratio, so it was not reused for `expansion_rate` — a local `f"{rate * 100:.1f}%"` one-liner
  is used instead, per the plan's own documented fallback. No existing section's ordering/content
  was touched (verified by the frozen-output-hash test and the SHA256 source-hash pin test, both
  still green).
- **Step 7 (no-frontend guard):** Added `test_no_new_frontend_ui_file_introduced_by_this_ticket`
  asserting no frontend-path-shaped literal/import appears in
  `compute_retrieval_metrics`/`generate`'s source.
- **Step 8 (parity ledger):** Appended `INFRA-298` to `docs/parity_ledger/infrastructure.yaml`,
  copying INFRA-297's field shape verbatim (`id`, `text`, `status`, `priority`, `legacy_evidence`,
  `v2_evidence`, `proof_type`, `test_path`, `divergence_note`, `support_boundary`) per the plan's
  revised Step 8 text. Verified the file still parses as valid YAML with matching field sets
  across all entries, and `tools/parity_ledger_scan.py` exits 0.
- Ran `graphify update .` after the `tools/`/`tests/` changes (no topology changes detected).

## Test Summary

`pytest tests/tools/test_generate_retro.py -q` — 75 passed (62 pre-existing + 13 new tests added:
`test_cache_rates_already_covers_hit_miss_stale_rejected_by_level`,
`test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants`,
`test_candidate_to_selected_and_selected_to_cited_aggregate_ratio`,
`test_candidate_to_selected_aggregate_ratio_is_none_when_all_candidate_counts_zero`,
`test_freshness_authority_distribution_includes_unrated_sentinel_bucket`,
`test_freshness_authority_distribution_empty_when_no_counts_present`,
`test_expansion_rate_computed_from_adequacy_verdict_and_expansion_fields`,
`test_expansion_rate_zero_when_no_events_carry_expansion_fields`,
`test_expansion_rate_zero_when_no_retrieval_events_at_all`,
`test_retrieval_quality_section_omitted_when_no_retrieval_events`,
`test_retrieval_quality_section_rendered_with_fixture_retrieval_events`,
`test_retrieval_quality_section_placement_does_not_disturb_existing_sections`,
`test_no_new_frontend_ui_file_introduced_by_this_ticket`, plus the extended read-only guard test
(existing test, new assertions added). All prior tests in this file, including
`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` (frozen
Markdown output hash — confirms the new section is correctly gated off for the no-retrieval-events
fixture) and `test_normalize_phase_agent_and_flag_outliers_untouched` (SHA256 source-hash pin on
disjoint functions), remain green and byte-identical.

Adjacent regression suite:
`pytest tests/tools/test_query.py tests/tools/test_retrieval_events.py
tests/tools/test_hybrid_retrieval.py tests/tools/test_retrieval_cache.py
tests/tools/test_context_packet_assembler.py tests/tools/test_retrieval_event_wrapper_single_source.py
tests/tools/test_monitoring_writer_single_source.py -q` — 107 passed, zero touched.

## Files Changed

- `tools/agent-monitoring/generate_retro.py` — extended `compute_retrieval_metrics()` with 5 new
  return keys (`candidate_to_selected_aggregate`, `selected_to_cited_aggregate`,
  `authority_distribution`, `freshness_distribution`, `expansion_rate`); added `hybrid_retrieval`/
  `retrieval_cache` constant imports; wired `compute_retrieval_metrics(events)` into `generate()`
  and added the new conditionally-rendered `## Retrieval Quality` Markdown section.
- `tests/tools/test_generate_retro.py` — 13 new tests plus 2 extended existing tests (see Test
  Summary above).
- `docs/parity_ledger/infrastructure.yaml` — appended `INFRA-298`.
- `tickets/inprogress/TCK-20260729-RETRIEVAL-RETRO-VIEWS.md` — this file (AC checkboxes,
  Implementation Notes, Test Summary, Files Changed, Completion Summary).

## Completion Summary

All 8 plan steps implemented in the suggested order with no deviations beyond the plan's own
pre-recorded Revision 1 (Step 8 field-shape fix, already resolved before implementation began).
`compute_retrieval_metrics()` now surfaces all four retrieval-quality dashboard signals from the
idea doc (cache rates by level, noise-indicator ratios, freshness/authority distribution including
the UNRATED sentinel, and an unconditional expansion rate), and `generate()` renders them as a new
`## Retrieval Quality` section, visible only under `--all` per the schema-emit ticket's own
run_id-isolation design (documented inline in the rendered caveat). All 6 acceptance criteria are
met and test-covered; no existing section's ordering/content changed (frozen-output-hash and
SHA256 source-hash guards both remain green); no new frontend/UI surface was introduced; the
parity ledger's INFRA-298 entry documents the shipped behavior. Ready to move to
`tickets/done/`.
