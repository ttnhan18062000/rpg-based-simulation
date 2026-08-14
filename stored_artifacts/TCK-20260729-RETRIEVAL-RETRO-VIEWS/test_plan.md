---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-RETRO-VIEWS
artifact_type: test_plan
tags: [observability, agent-monitoring, retro]
---

# Test Plan — TCK-20260729-RETRIEVAL-RETRO-VIEWS

## Regression Surface

Existing tests that must keep passing, unmodified, after this ticket's additive changes:

**Unit — `tools/agent-monitoring/generate_retro.py`:**
- `tests/tools/test_generate_retro.py` — the full file (996+ lines), in particular:
  - `TestComputeRetrievalMetrics` (lines 1048-1120) — the sibling ticket's own coverage of
    `compute_retrieval_metrics()`'s current (narrower) behavior; every existing assertion in this
    class must still pass byte-for-byte after this ticket extends the function or adds siblings.
  - `test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` — frozen
    Markdown output hash guard; the new retrieval section(s) must never appear for a fixture with
    no retrieval-shaped events (this fixture has none), so this test's frozen string must remain
    byte-identical.
  - `test_normalize_phase_agent_and_flag_outliers_untouched` — SHA256 source-hash pin on
    `_resolve_status`/`_is_legacy_event`/`_is_gate_fail`/`_normalize_phase`/`_normalize_agent`/
    `_canonicalize`/`_flag_outliers`; none of these functions may be touched by this ticket.
  - `test_generate_retro_builds_index_on_demand_when_missing`,
    `test_no_sys_exit_1_on_missing_index_in_generate_retro`,
    `test_generate_retro_produces_clear_error_message_if_build_on_demand_disabled_or_fails` — the
    graceful-degradation contract this ticket's new functions must not weaken if they end up in
    `generate_retro.py`.
  - `test_generate_retro_never_writes_to_agent_monitoring_index_db`,
    `test_main_loads_via_index_not_direct_jsonl_scan` — architecture guards this ticket's read-only
    additions must not violate.

**Unit/Integration — `tools/agent-monitoring/query.py`:**
- `tests/tools/test_query.py` — the full file, in particular `TestArchitectureGuards`
  (`test_query_py_has_no_direct_jsonl_reads`, `test_query_py_uses_order_by_id_in_index_queries`)
  and `TestMissingIndex` (the hard `sys.exit(1)` contract) — must hold if any new function/flag is
  added to `query.py`.

**Adjacent Phase 3 modules (must stay untouched — no code change expected, but a regression here
would indicate accidental scope creep into these files):**
- `tests/tools/test_hybrid_retrieval.py`
- `tests/tools/test_retrieval_cache.py`
- `tests/tools/test_context_packet_assembler.py`
- `tests/tools/test_retrieval_events.py`
- `tests/tools/test_retrieval_event_wrapper_single_source.py`
- `tests/tools/test_monitoring_writer_single_source.py`

## New Tests Required

Per AC, one entry per required new view/behavior. All new tests use in-file synthetic fixture
builders (following `test_generate_retro.py`'s existing `_retrieval_event(**overrides)` pattern —
see investigation.md Risk #2 on why a literal `tests/fixtures/agent_monitoring/*.jsonl` file cannot
be built for retrieval events), living in `tests/tools/test_generate_retro.py` (and/or
`tests/tools/test_query.py` if any function/flag lands in `query.py` — placement mirrors wherever
Plan puts the corresponding implementation).

1. **Cache hit/miss/stale-rejection rates by cache level — regression-proof of AC1's existing
   coverage, not new logic.**
   - Test name: `test_cache_rates_already_covers_hit_miss_stale_rejected_by_level` (or extend the
     existing `TestComputeRetrievalMetrics` class in place)
   - Category: unit
   - Verifies: a fixture events list spanning all 3 `cache_level` values
     (`retrieval_index_cache`/`retrieval_query_cache`/`retrieval_packet_cache`, imported from
     `retrieval_cache.py`'s constants, never re-literaled) × all 3 `cache_status` values (`HIT`/
     `MISS`/`STALE_REJECTED`, imported verbatim) returns correct per-level counts/rates. This is
     confirming the shipped `compute_retrieval_metrics()["cache_rates"]` already satisfies this AC
     signal (see investigation.md) — the new test's job is to pin that this stays true once the
     function is extended for the other 3 signals, not to add new cache-rate logic.
   - Location: `tests/tools/test_generate_retro.py`

2. **Candidate-to-selected / selected-to-cited as an aggregated noise-indicator view (the real gap
   in AC2).**
   - Test name: `test_candidate_to_selected_and_selected_to_cited_aggregate_ratio`
   - Category: unit
   - Verifies: given a fixture events list with several `candidate_count`/`selected_count`/
     `cited_source_hashes` combinations (including one event with `candidate_count=0` and one with
     `selected_count=0`), the new aggregated view (whatever shape Plan chooses — e.g. overall
     sum-of-selected/sum-of-candidates and sum-of-cited/sum-of-selected, or grouped) computes the
     correct ratio and does not raise `ZeroDivisionError` for the zero-denominator case. Must
     explicitly assert both directions: an entirely-zero-candidate fixture (no non-zero
     `candidate_count` events at all) and a zero-count within a larger, otherwise-populated fixture.
   - Location: `tests/tools/test_generate_retro.py`

3. **Freshness/authority distribution including the UNRATED sentinel.**
   - Test name: `test_freshness_authority_distribution_includes_unrated_sentinel_bucket`
   - Category: unit
   - Verifies: a fixture events list with `authority_counts`/`freshness_counts` objects that
     include the literal `"unrated"` key (imported from `hybrid_retrieval.UNRATED`, never
     re-literaled) alongside real authority/freshness values returns a correct combined
     distribution where `"unrated"` appears as its own bucket with the correct count — never
     dropped, never crashing.
   - Test name: `test_freshness_authority_distribution_empty_when_no_counts_present`
   - Category: unit
   - Verifies: events lacking `authority_counts`/`freshness_counts` entirely (current real-world
     state for e.g. cache-only events) do not crash and produce an empty/zero distribution, not a
     `KeyError`.
   - Location: `tests/tools/test_generate_retro.py`

4. **Follow-up/expansion rate from `adequacy_verdict` and `expansion_reason`/`expansion_count`.**
   - Test name: `test_expansion_rate_computed_from_adequacy_verdict_and_expansion_fields`
   - Category: unit
   - Verifies: a fixture events list mixing events with all 3 `adequacy_verdict` values
     (`"sufficient"`/`"insufficient"`/`"noisy"`) and a subset carrying `expansion_reason`/
     `expansion_count` returns the rate Plan's chosen formula defines (see investigation.md Risk
     #1) — asserted against a hand-computed expected value in the test, with the formula's
     rationale documented in the test's own docstring/comment so a future reader isn't left
     guessing why that specific ratio is "correct."
   - Test name: `test_expansion_rate_zero_when_no_events_carry_expansion_fields`
   - Category: unit
   - Verifies: the realistic current-state case — a fixture with `adequacy_verdict` set but zero
     events carrying `expansion_reason`/`expansion_count` (matches the fact that no shipped
     `wrap_*()` function emits these fields today) returns a 0-rate, not a crash or a fabricated
     nonzero value.
   - Location: `tests/tools/test_generate_retro.py`

5. **Every new view is fixture/unit-tested, never validated only against live data (AC5).**
   - Test name: `test_new_retrieval_views_are_pure_functions_no_live_file_dependency`
   - Category: architecture guard
   - Verifies (mirrors the existing
     `test_function_is_read_only_no_write_call_or_file_open_in_write_mode` pattern): each new
     view function's source contains no reference to `EVENTS_FILE`/`RUNS_FILE`/`load_jsonl`/
     `DEFAULT_DB_PATH` — operates purely on its `events`/`runs` argument, same discipline as
     `compute_retrieval_metrics()`.
   - Location: `tests/tools/test_generate_retro.py`

6. **New retro report section(s) render via the existing conditional-render pattern (AC6).**
   - Test name: `test_retrieval_quality_section_omitted_when_no_retrieval_events`
   - Category: integration (exercises `generate()` end-to-end, matching
     `test_outliers_section_omitted_when_none_flagged`'s precedent)
   - Verifies: `generate()` called with a fixture events list containing zero
     `retrieval_event_schema_version`-bearing records produces a report with no new retrieval
     section heading at all (not an empty/placeholder section).
   - Test name: `test_retrieval_quality_section_rendered_with_fixture_retrieval_events`
   - Category: integration
   - Verifies: `generate()` called with a fixture events list containing retrieval-shaped events
     produces a report containing the new section heading(s) and correct rendered values for at
     least one of the 4 AC signals (spot-check, not full duplication of the unit tests above).
   - Test name: `test_retrieval_quality_section_placement_does_not_disturb_existing_sections`
   - Category: integration (mirrors
     `test_retro_spend_breakdown_placement_does_not_disturb_tag_breakdown_sections`'s precedent)
   - Verifies: existing section ordering (Run Summary → ... → Notes) is unchanged; the new
     section(s) insert without reordering or duplicating any existing heading.
   - Location: `tests/tools/test_generate_retro.py`

7. **No new frontend/UI file added (AC6 structural half).**
   - Test name: `test_no_new_frontend_ui_file_introduced_by_this_ticket`
   - Category: architecture guard
   - Verifies: a structural check (e.g. asserting no new file under `dashboard-frontend/src/` or
     `experiments/agent_ops_dashboard/` is referenced/imported by the new code) — lightweight,
     mirrors the schema-emit ticket's AC6 grep-based guard style rather than trying to enumerate
     the whole frontend tree.
   - Location: `tests/tools/test_generate_retro.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_generate_retro.py tests/tools/test_query.py -v
```

If any new function/flag also touches `query.py`, additionally scope to that file's dependency,
`build_index.py`, since `test_query.py` imports it directly:

```
pytest tests/tools/test_generate_retro.py tests/tools/test_query.py tests/tools/test_build_index.py -v
```

Adjacent-module regression check (confirm zero accidental touch to Phase 3 modules or the
schema-emit ticket's own files):

```
pytest tests/tools/test_retrieval_events.py tests/tools/test_hybrid_retrieval.py tests/tools/test_retrieval_cache.py tests/tools/test_context_packet_assembler.py tests/tools/test_retrieval_event_wrapper_single_source.py tests/tools/test_monitoring_writer_single_source.py -v
```

Never: `pytest tests/` (repo-wide) — per CLAUDE.md's Testing Rule, scope to the domain under
modification only.

## Anti-Drift Test Guards

- **Cache-status/cache-level literal-reuse guard** (mirrors the schema-emit ticket's own Step 6
  test): assert any new view's source imports `retrieval_cache.HIT`/`MISS`/`STALE_REJECTED` and
  `*_CACHE_CATEGORY` constants rather than containing the literal strings `"hit"`/`"miss"`/
  `"stale-rejected"`/`"retrieval_index_cache"` etc. as bare string literals outside a docstring/
  comment.
- **UNRATED-sentinel-not-silently-dropped guard**: explicit test (item 3 above) asserting `unrated`
  survives into the distribution output, catching a future refactor that adds an
  "only known values" allowlist filter.
- **Frozen-output hash guards stay green**: rerun
  `test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` and
  `test_normalize_phase_agent_and_flag_outliers_untouched` after implementation — any diff here
  means this ticket accidentally touched `compute_retro_metrics()`/`generate()`'s pre-existing
  logic rather than adding new, separate logic.
- **No expansion-field fabrication guard**: the "zero rate when no events carry expansion fields"
  test (item 4, second test) doubles as an anti-drift guard against a future change silently
  assuming `expansion_reason`/`expansion_count` are always present just because `adequacy_verdict`
  is.
- **`--all`-only visibility note guard (optional, recommended)**: if Plan documents the
  `--days`/`--week` exclusion (investigation.md Risk #3) inline in the rendered section text, add a
  test asserting that note's presence when the section renders — prevents the caveat from being
  silently dropped in a future edit.
- **No `query.py` hard-exit regression**: if any new flag/function is added to `query.py`, rerun
  `TestMissingIndex` unmodified — a new retrieval-aware code path must not accidentally introduce a
  second, softer failure mode that bypasses `open_index()`'s existing `sys.exit(1)` contract.
- **Read-only guard extended, not replaced**: item 5 above must cover every *new* function
  individually (not just re-assert the existing `compute_retrieval_metrics` guard), since a new
  sibling function is a distinct piece of source `inspect.getsource()` would need to target
  separately.
