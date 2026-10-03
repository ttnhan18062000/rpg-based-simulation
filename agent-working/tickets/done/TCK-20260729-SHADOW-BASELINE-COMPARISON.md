---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260729-SHADOW-BASELINE-COMPARISON
phase: done
date: 2026-07-29
tags: [retro, agent-monitoring, observability]
---

# TCK-20260729-SHADOW-BASELINE-COMPARISON

## Title
Add shadow-vs-baseline retrieval comparison view to generate_retro.py

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Extend generate_retro.py with a query/report that compares shadow-packet-covered phase outcomes against existing baseline metrics, mirroring Phase 4's compute_retrieval_metrics() precedent. This produces comparison data only, never a promotion scorecard, and is fixture-tested.

## Scope
- Add a new function in generate_retro.py that partitions retrieval-shaped events by real (TCK-...) vs. synthetic (RETRIEVAL-EVENT-<slug>) run_id provenance
- Compute comparison rows for the shadow cohort using the same measurement domain as compute_retrieval_metrics() (cache rates, noise ratios, freshness-authority, expansion rate) — resolved as the correct baseline per this ticket's Resolved Decision, not tools/agent-monitoring/retrieval_baseline_metrics.py's separate duration/outcome/token-stat JSON report, because compute_retrieval_metrics() measures the same retrieval-quality domain for both cohorts and lives in the same file, following the established byte-identical-output-preserving extension pattern
- Follow generate()'s existing conditional-render pattern: the new comparison section is omitted entirely (not rendered empty) when zero shadow events are present
- Add fixture-only tests (synthetic runs.jsonl/events.jsonl) exercising both the zero-shadow-events (section omitted) and nonzero-shadow-events (comparison rows rendered) cases

## Out of Scope
- No scorecard or comparison against the six approval-gate criteria — verified by asserting none of those criteria phrases appear in generated report text
- No changes to retrieval_baseline_metrics.py's own standalone JSON report format
- No changes to existing non-shadow report output — must remain byte-identical (TCK-20260718-RETRO-STATS-REFACTOR precedent)
- No live dashboard/UI surfacing — report text output only
- No independent event-emission or call-site logic — this ticket only reads events already emitted by the merged shadow-packet call-site ticket

## Acceptance Criteria
- [x] A new function in generate_retro.py partitions retrieval-shaped events by real-vs-synthetic run_id provenance and computes comparison rows using compute_retrieval_metrics()'s measurement domain (cache rates, noise ratios, freshness-authority, expansion rate)
- [x] When zero shadow (real-run-id) events are present, the new report section is omitted entirely, per generate()'s existing conditional-render pattern
- [x] Existing non-shadow report output remains byte-identical to current output on the same fixture inputs
- [x] No phrase from any of the six approval-gate criteria appears in the new comparison section's generated text (asserted by test)
- [x] New tests are fixture-only (synthetic runs.jsonl/events.jsonl), with no live-data dependency

## Related Tickets
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260729-SHADOW-PACKET-CALL-SITE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/retrieval_baseline_metrics.py
- tools/retrieval_events.py
- tests/tools/test_generate_retro.py

## Assumptions / Open Questions
- Hard dependency: this ticket cannot land or be exercised against real data until the merged shadow-packet-call-site ticket (TCK-20260729-SHADOW-PACKET-CALL-SITE) lands and begins emitting real-run-id-provenance retrieval events; fixture tests here are built against the event shape that ticket defines

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260729-SHADOW-BASELINE-COMPARISON/plan.md`, with
one wording deviation (see below).

1. Added `compute_shadow_baseline_comparison(events: list[dict]) -> dict` to
   `tools/agent-monitoring/generate_retro.py`, immediately after `compute_retrieval_metrics()` and
   before `def generate(...)`. Partitions `events` into `shadow` (real `TCK-...` run_ids, via
   `infer_workflow(e.get("run_id") or "") is not None`) and `baseline` (synthetic
   `RETRIEVAL-EVENT-...` run_ids, the `is None` branch) cohorts, then calls the existing
   `compute_retrieval_metrics()` once per cohort's full (unfiltered) event list — `{"shadow": ...,
   "baseline": ...}`. No re-literal of `HIT`/`MISS`/`STALE_REJECTED`/cache-category constants.
2. Wired `shadow_comparison = compute_shadow_baseline_comparison(events)` into `generate()` right
   after `retrieval_metrics = compute_retrieval_metrics(events)`, and added a new
   `## Shadow vs. Baseline Retrieval Comparison` block after the existing `## Retrieval Quality`
   section and before `## Notes`, gated on `shadow_comparison["shadow"]["retrieval_event_count"]`
   truthiness — omitted entirely (no heading, no placeholder) when the shadow cohort has zero
   events, mirroring the existing gate style exactly. Renders a comparison table (event count,
   candidate→selected ratio, selected→cited ratio, expansion rate) plus per-cohort cache-rate and
   freshness/authority breakdowns.
3. Added 8 new tests to `tests/tools/test_generate_retro.py`: partition correctness (source-text
   guard confirming `infer_workflow(...) is not None` is used, not a re-literaled prefix check),
   same-measurement-domain equivalence, reuse-not-reimplementation source guard, section-omitted
   (both zero-shadow-with-baseline and zero-retrieval-events-at-all cases), section-rendered,
   byte-identical-on-existing-fixture (reusing the existing `_FIXED_CORPUS_RUNS`/
   `_FIXED_CORPUS_EVENTS`/`_FIXED_CORPUS_EXPECTED_REPORT` fixture — its run_ids are real `TCK-...`
   ids but carry zero retrieval-shaped events, so both cohorts have `retrieval_event_count == 0`
   and the new section stays fully absent while `generate()`'s frozen-string assertion still
   passes untouched), the six-approval-gate-criteria phrase-absence guard, and a fixture-only
   guard (source-scans the 7 preceding new test functions for `EVENTS_FILE`/`RUNS_FILE`/
   `DEFAULT_DB_PATH`/`_load_runs_and_events` references).
5. Added parity ledger entry `INFRA-300` to `docs/parity_ledger/infrastructure.yaml`, following
   the exact INFRA-296–299 field set (`status: verified`, `priority: P2`, `test_path:
   tests/tools/test_generate_retro.py`, `support_boundary` noting agent-orchestration/retrieval
   tooling only, no `src/` file touched).

**Deviation from plan.md's literal Step 2 code sample:** the plan's own suggested caveat text —
`"Comparison data only — not a promotion or approval-gate scorecard._"` — contains the literal
words `"promotion"` and (hyphenated) `"approval-gate"`, which directly conflicts with plan.md's own
Anti-Drift Note ("must not use the words 'approval,' 'gate' ... 'promotion,' or 'scorecard'") and
with Step 3's own phrase-absence test list (which bans the literal substring `"promotion"`). Per
Step 3's own text ("if it fails, the fix is to reword Step 2's rendered text, not to add new
computation"), the caveat line was shortened to `"Comparison data only._"`, dropping the
self-contradictory clause entirely. No other wording, gating, or computation logic differs from
the plan. Recorded in staging_artifacts plan.md's Deviations section.

## Test Summary
`python3 -m pytest tests/tools/test_generate_retro.py -q` — 83 passed (75 pre-existing + 8 new),
zero regressions. `python3 -m pytest tests/tools/test_retrieval_baseline_metrics.py -q` — 13
passed, confirming `retrieval_baseline_metrics.py` is untouched (zero diff). YAML schema for the
new `INFRA-300` entry validated directly against `docs/parity_ledger/schema.json` via `jsonschema`
(the one pre-existing schema violation at a different, unrelated entry index is not introduced by
this change). `python3 -m pytest tests/tools/test_parity_ledger_scan.py -q` — 3 passed.

## Files Changed
- tools/agent-monitoring/generate_retro.py
- tests/tools/test_generate_retro.py
- docs/parity_ledger/infrastructure.yaml

## Completion Summary
Added `compute_shadow_baseline_comparison()` to `generate_retro.py`, a pure function that
partitions retrieval-shaped events into a real (`TCK-...` run_id) shadow cohort and a synthetic
(`RETRIEVAL-EVENT-...` run_id) baseline cohort via the existing `infer_workflow(...) is not None`
idiom, then reuses `compute_retrieval_metrics()` unmodified once per cohort. Wired the result into
`generate()` as a new, additively-gated `## Shadow vs. Baseline Retrieval Comparison` report
section (omitted entirely when the shadow cohort is empty), added 8 fixture-only tests covering
partition correctness, reuse-not-reimplementation, both omission cases, rendering, byte-identical
existing-output preservation, the six-approval-gate-criteria phrase-absence guard, and a
live-data-absence guard on the new tests themselves, and appended parity ledger entry `INFRA-300`.
All acceptance criteria verified and checked off; no scope-guarded file
(`retrieval_baseline_metrics.py`, event-emission/call-site logic, dashboard/UI) was touched.
