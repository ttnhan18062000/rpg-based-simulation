---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-SHADOW-BASELINE-COMPARISON
artifact_type: test_plan
tags: [retro, agent-monitoring, observability]
---

# Test Plan — TCK-20260729-SHADOW-BASELINE-COMPARISON

## Regression Surface

All unit-level — no integration/arena-combat surface exists for this ticket (it touches only
`tools/agent-monitoring/generate_retro.py`, an agent-orchestration reporting tool with no
`src/` dependency).

**Unit — `generate_retro.py` and its direct dependents:**
- `tests/tools/test_generate_retro.py` — the full existing suite (includes
  `TestComputeRetrievalMetrics`, the `compute_retro_metrics()` tests, the
  `test_normalize_phase_agent_and_flag_outliers_untouched` pre-migration source-hash guard, and
  every existing `generate()`-rendering test) must keep passing unmodified — this is the direct
  proof that the new addition does not perturb existing report output or existing function
  signatures.
- `tests/tools/test_retrieval_events.py` — `wrap_context_packet_assembly()`/`RETRIEVAL_EVENT_FIELDS`
  regression surface; this ticket does not touch `tools/retrieval_events.py` but reads its
  constants/shape, so a passing run here confirms no accidental drift in assumptions.
- `tests/tools/test_retrieval_event_parity_check.py` — `RETRIEVAL_EVENT_FIELDS` structural guard;
  unaffected by construction (no field added), included as a fast regression check.
- `tests/tools/test_retrieval_baseline_metrics.py` — confirms `retrieval_baseline_metrics.py`
  itself is untouched (Out of Scope: "No changes to retrieval_baseline_metrics.py's own standalone
  JSON report format").
- `tests/tools/test_shadow_packet_call_site.py` — the dependency ticket's own suite; confirms the
  upstream event-emission/seq-scheme this ticket's fixtures are modeled on is unchanged.

**Architecture guard:**
- `tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks()` — this ticket
  touches no `src/` file and introduces no durable-state mutation, so this should report zero
  findings; run as a fast sanity check before Parity/Verify.

## New Tests Required

All new tests live in `tests/tools/test_generate_retro.py`, extending the existing
`TestComputeRetrievalMetrics`-adjacent fixture idiom (`_retrieval_event(**overrides)` at line
~1033) rather than introducing a parallel fixture helper.

1. **`test_shadow_comparison_partitions_real_vs_synthetic_run_id`**
   Category: unit.
   Verifies: a mixed fixture list containing both a `run_id="TCK-FAKE-001"`,
   `agent="context-packet-wrapper"`, `phase="Retrieval"` row and a
   `run_id="RETRIEVAL-EVENT-context-packet"` (or `"RETRIEVAL-EVENT-test"`) row is split into exactly
   two cohorts by the new function, with the `TCK-` row landing in the "shadow"/real cohort and the
   `RETRIEVAL-EVENT-` row landing in the synthetic/baseline cohort. Directly asserts the partition
   uses `vocabulary.infer_workflow(run_id) is not None`, not a re-literaled prefix check (source-text
   assertion via `inspect.getsource`, mirroring
   `test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants`'s technique).
   Location: `tests/tools/test_generate_retro.py`.

2. **`test_shadow_comparison_computes_same_measurement_domain_as_compute_retrieval_metrics`**
   Category: unit.
   Verifies: the new function's per-cohort output shape matches
   `compute_retrieval_metrics()`'s own return-dict keys (`cache_rates`,
   `candidate_to_selected_aggregate`, `selected_to_cited_aggregate`, `authority_distribution`,
   `freshness_distribution`, `expansion_rate`) for both the shadow and baseline cohorts — proving
   reuse, not reimplementation. Construct a fixture with distinguishable cache/candidate/selected
   values per cohort and assert the numeric results match calling `compute_retrieval_metrics()`
   directly on each cohort's filtered event list.
   Location: `tests/tools/test_generate_retro.py`.

3. **`test_shadow_comparison_reuses_compute_retrieval_metrics_not_reimplemented`**
   Category: unit (source-text guard, mirrors
   `test_retrieval_baseline_metrics.py::test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`'s
   technique).
   Verifies: `inspect.getsource()` of the new function contains a call to
   `compute_retrieval_metrics(` and does not re-literal any of the cache-status/cache-level string
   constants that `test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants`
   already guards for `compute_retrieval_metrics()` itself (`"hit"`, `"miss"`,
   `"stale-rejected"`, `"retrieval_index_cache"`, `"retrieval_query_cache"`,
   `"retrieval_packet_cache"`).
   Location: `tests/tools/test_generate_retro.py`.

4. **`test_shadow_comparison_section_omitted_when_zero_shadow_events`**
   Category: unit (rendering).
   Verifies: given an `events` fixture containing only synthetic-cohort retrieval events (zero
   `TCK-`-prefixed / `infer_workflow(...) is not None` rows), `generate()`'s rendered Markdown
   output contains **no** new comparison-section heading at all — not an empty table, not a
   placeholder sentence. Assert the heading text (whatever literal heading Plan chooses, e.g.
   `## Shadow`) is absent from the output entirely. Also assert a fixture with **zero retrieval
   events of any kind** (neither cohort) likewise omits the section — covering both
   "no retrieval events at all" and "retrieval events exist but none are shadow" as distinct
   zero-shadow cases per the ticket's AC wording ("zero shadow (real-run-id) events").
   Location: `tests/tools/test_generate_retro.py`.

5. **`test_shadow_comparison_section_rendered_when_shadow_events_nonzero`**
   Category: unit (rendering).
   Verifies: given a fixture with at least one `TCK-`-prefixed, `agent="context-packet-wrapper"`,
   `phase="Retrieval"` event (mirroring `tests/tools/test_shadow_packet_call_site.py`'s `_event()`
   shape, including a negative `seq`), the new section heading and its comparison rows ARE
   present in `generate()`'s rendered output, and the section correctly reflects the shadow
   cohort's computed values (spot-check at least one numeric field, e.g. a cache-rate or
   expansion-rate figure, against a hand-computed expectation for the fixture).
   Location: `tests/tools/test_generate_retro.py`.

6. **`test_shadow_comparison_never_emits_any_approval_gate_criteria_phrase`**
   Category: unit (negative/phrase-absence guard) — this is the ticket's explicit Out of Scope
   AC, made concrete.
   Verifies: render `generate()`'s output against the nonzero-shadow-events fixture from test 5,
   and assert none of the following substrings (or their obvious paraphrases as agreed at Plan
   time) appear anywhere in the full rendered report text: `"authoritative-source recall"`,
   `"missed contracts"`, `"review rework"`, `"context tokens"` (as a reduction claim; note
   `compute_retrieval_metrics()`'s own domain has no token-count field so this should be trivially
   true, but assert it explicitly as a regression guard), `"stale packets are rejected"` /
   `"cache correctness"`, `"provider parity"`, `"privacy boundary"`. Also assert the literal phrase
   `"approval gate"` / `"promotion"` does not appear.
   Location: `tests/tools/test_generate_retro.py`.

7. **`test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture`**
   Category: unit (regression proof) — directly implements the ticket's AC "Existing non-shadow
   report output remains byte-identical to current output on the same fixture inputs," following
   `TCK-20260718-RETRO-STATS-REFACTOR`'s precedent (there: `git stash`/live-corpus diff; here:
   fixture-based, since this is an additive change, not an extraction).
   Verifies: run `generate()` against a fixture with **zero shadow/synthetic retrieval events at
   all** (a plain runs/events fixture with only ordinary workflow events) both against the current
   `main`-equivalent behavior description (every existing section's exact text, captured as a
   golden string/fixture-of-expected-lines from the current test suite's existing
   `generate()`-output assertions) and after this ticket's change, and diff them — must be
   identical. In practice: reuse an existing `test_generate_retro.py` fixture/assertion that
   already renders full `generate()` output and assert no new lines are inserted when the shadow
   cohort is empty (this collapses into test 4's coverage but is called out separately here since
   it is the ticket's own explicit, named AC, not merely a side-effect of test 4).
   Location: `tests/tools/test_generate_retro.py`.

8. **`test_shadow_comparison_new_tests_are_fixture_only_no_live_data_read`**
   Category: unit (source-text guard) — implements the ticket's AC "New tests are fixture-only...
   with no live-data dependency."
   Verifies: `inspect.getsource()` (or `ast`-walk) of the new test functions/module section
   contains no reference to `EVENTS_FILE`, `RUNS_FILE`, `DEFAULT_DB_PATH`, or
   `_load_runs_and_events` — mirroring `test_retrieval_baseline_metrics.py`'s own
   `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`-style reuse guard, applied
   here as a live-data-absence guard instead.
   Location: `tests/tools/test_generate_retro.py`.

## Scoped Pytest Commands

```
pytest tests/tools/test_generate_retro.py -v
pytest tests/tools/test_retrieval_events.py tests/tools/test_retrieval_event_parity_check.py -v
pytest tests/tools/test_retrieval_baseline_metrics.py -v
pytest tests/tools/test_shadow_packet_call_site.py -v
```

Never `pytest tests/` — scoped to the agent-monitoring/retrieval-reporting domain touched by this
ticket, per CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- **Test 3** and **test 8** are the primary anti-drift guards against silent scope-creep: test 3
  prevents the implementer from copy-pasting `compute_retrieval_metrics()`'s cache/ratio/
  distribution logic into the new function (which would create two divergent copies of the same
  measurement domain — exactly what this ticket's Scope explicitly says not to do); test 8
  prevents the new tests from quietly depending on the real `agent-monitoring/*.jsonl` corpus,
  which would make them non-deterministic/order-dependent on whatever real shadow data has
  accumulated by the time CI runs.
- **Test 6** is the guard against the single highest-risk drift for this ticket: silently turning
  a "comparison data only" reporting feature into something that reads like a go/no-go promotion
  scorecard, which the ticket's Out of Scope explicitly forbids ("No scorecard or comparison
  against the six approval-gate criteria").
- **Test 1** guards against reintroducing a second, parallel `run_id.startswith("TCK-")` /
  `run_id.startswith("RETRIEVAL-EVENT-")` literal instead of reusing
  `vocabulary.infer_workflow()` — a drift that would silently desynchronize from any future change
  to `infer_workflow()`'s recognized-workflow prefix list (e.g., a 5th workflow added later).
- **Test 4** guards against the most likely rendering mistake: rendering an empty/placeholder
  section instead of omitting it entirely when there is no shadow data — the exact distinction
  `generate()`'s own `## Retrieval Quality` section (line 901) already draws correctly, and which
  this ticket's own AC restates as a hard requirement.
- **Regression run of `tests/tools/test_generate_retro.py`'s full existing suite** (not just the
  new tests) is itself the guard against this ticket accidentally perturbing the unrelated
  `## Retrieval Quality`, `## Tag Breakdown`, `## Outliers`, or `## Run Summary` sections' existing
  conditional-render behavior or exact text — any diff in an existing test's expected output is a
  signal this ticket's diff leaked outside its intended additive boundary.
- **Regression run of `tests/tools/test_retrieval_baseline_metrics.py`** guards against the
  temptation (explicitly named in the ticket's Out of Scope) to instead extend
  `retrieval_baseline_metrics.py`'s JSON report format — if that file's tests ever need to change
  because of this ticket's diff, that is itself a signal the work has drifted into the wrong
  module.
