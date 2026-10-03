---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-SHADOW-BASELINE-COMPARISON
artifact_type: plan
tags: [retro, agent-monitoring, observability]
---

# Implementation Plan — TCK-20260729-SHADOW-BASELINE-COMPARISON

## Summary

Add one new pure function, `compute_shadow_baseline_comparison(events)`, to
`tools/agent-monitoring/generate_retro.py` that partitions retrieval-shaped events into a
"shadow" cohort (real `TCK-...` run_ids) and a "baseline" cohort (synthetic
`RETRIEVAL-EVENT-...` run_ids) using `vocabulary.infer_workflow(run_id) is not None` as the sole
partition test, then calls the existing `compute_retrieval_metrics()` once per cohort — never
reimplementing its cache-rate/noise-ratio/freshness-authority/expansion-rate logic. Wire the
result into `generate()` as a new, additively-appended `## Shadow vs. Baseline Retrieval
Comparison` section, placed after the existing `## Retrieval Quality` section and before
`## Notes`, gated (mirroring the existing `## Retrieval Quality` gate at line ~901) on the shadow
cohort's `retrieval_event_count` being nonzero — omitted entirely, not rendered empty, when it is
zero. All work is fixture-tested in `tests/tools/test_generate_retro.py`; no other file changes.
Also append one new parity ledger entry, `INFRA-300`, to `docs/parity_ledger/infrastructure.yaml`,
following the unbroken INFRA-296 through INFRA-299 one-entry-per-ticket convention in this exact
series.

**Section naming decision:** `## Shadow vs. Baseline Retrieval Comparison`. This reuses "shadow"
and "baseline" — both already load-bearing terms in this ticket's own title and Scope text
("shadow-packet-covered phase outcomes... baseline metrics") — but avoids any of the six
approval-gate criteria phrasing or the words "approval," "gate," "promotion," or "scorecard" from
the idea doc's distinct, out-of-scope "Shadow evaluation and approval gate" concept. The heading
describes exactly what the section is (a side-by-side comparison of the same measurement domain
across two cohorts) and nothing more.

**Parity ledger decision:** Add a new entry, `id: INFRA-300`, rather than folding this into
INFRA-298. Rationale: this ticket's function is a new, independently-testable unit with its own
new tests and its own new rendered section — the same shape of change INFRA-296 through INFRA-299
each received their own entry for, even though all five entries share one `support_boundary`
posture ("agent-orchestration/retrieval tooling only, no `src/` file, no simulation/Mechanics
Bible/engine-contract surface"). Correcting INFRA-298's text in place would be appropriate only if
this ticket modified `compute_retrieval_metrics()` or the `## Retrieval Quality` section itself —
it does neither (Anti-Drift Notes, below). One entry per ticket is the established, low-cost
convention in this specific chain; skipping it would be the outlier, not the norm.

## Steps

### Step 1 — Add `compute_shadow_baseline_comparison()`

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** Add a new pure function immediately after `compute_retrieval_metrics()` (after line
~679, before `def generate(...)`):

```python
def compute_shadow_baseline_comparison(events: list[dict]) -> dict:
    """Partitions events by real (TCK-...) vs. synthetic (RETRIEVAL-EVENT-...) run_id
    provenance, using vocabulary.infer_workflow(run_id) is not None as the sole partition test —
    the same non-None-vs-None idiom _normalize_phase()/_normalize_agent() already use. Does NOT
    pre-filter to retrieval-shaped events itself: compute_retrieval_metrics() already applies its
    own "retrieval_event_schema_version" in e discriminator internally, so passing the full
    per-cohort event list (including ordinary workflow events) is correct and avoids a second,
    redundant filter.
    """
    shadow_events = [e for e in events if infer_workflow(e.get("run_id") or "") is not None]
    baseline_events = [e for e in events if infer_workflow(e.get("run_id") or "") is None]
    return {
        "shadow": compute_retrieval_metrics(shadow_events),
        "baseline": compute_retrieval_metrics(baseline_events),
    }
```

`infer_workflow` is already imported at module top (line 35: `from vocabulary import
WORKFLOW_AGENTS, WORKFLOW_PHASES, infer_workflow`) — no new import needed. Do not call
`generate()` or touch it in this step; this step is the pure-computation function only.

**Do NOT touch:** `compute_retrieval_metrics()` itself (no signature, return-shape, or literal
change — call it, don't edit it); `vocabulary.py`; `retrieval_events.py`.

**Verify:**
- `test_shadow_comparison_partitions_real_vs_synthetic_run_id` (mixed fixture splits correctly;
  asserts via `inspect.getsource()` that the partition uses `infer_workflow(...) is not None`, not
  a re-literaled `"TCK-"`/`"RETRIEVAL-EVENT-"` prefix check)
- `test_shadow_comparison_computes_same_measurement_domain_as_compute_retrieval_metrics` (per-cohort
  output keys/values match calling `compute_retrieval_metrics()` directly on each cohort's filtered
  list)
- `test_shadow_comparison_reuses_compute_retrieval_metrics_not_reimplemented` (source-text guard:
  `inspect.getsource()` of the new function contains a call to `compute_retrieval_metrics(` and
  none of the cache/authority string literals `test_compute_retrieval_metrics_does_not_
  reliteral_cache_or_authority_constants` already guards for the original function)

### Step 2 — Wire the new section into `generate()`

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** In `generate()` (currently lines 682-982):
1. After the existing line `retrieval_metrics = compute_retrieval_metrics(events)` (line ~689),
   add: `shadow_comparison = compute_shadow_baseline_comparison(events)`.
2. After the existing `## Retrieval Quality` block closes (immediately after its last
   `lines.append("")` following the Expansion Rate sub-section, currently ending at line ~966,
   and strictly before the `# Notes (human-written)` comment / `lines.append("## Notes")` at line
   ~968), insert a new conditionally-gated block:

```python
    # Shadow vs. Baseline Retrieval Comparison (TCK-20260729-SHADOW-BASELINE-COMPARISON):
    # additive, separately-gated section — never rendered empty, omitted entirely when the
    # shadow (real-run-id) cohort has zero retrieval events, independent of whether the
    # synthetic/baseline cohort is nonzero.
    if shadow_comparison["shadow"]["retrieval_event_count"]:
        lines.append("## Shadow vs. Baseline Retrieval Comparison")
        lines.append("")
        lines.append(
            "_Compares shadow-packet-covered (real TCK-... run_id) retrieval events against the "
            "synthetic/manual-invocation baseline, using the same cache-rate/noise-ratio/"
            "freshness-authority/expansion-rate measurement domain as `## Retrieval Quality` "
            "above. Comparison data only — not a promotion or approval-gate scorecard._"
        )
        lines.append("")

        shadow_m = shadow_comparison["shadow"]
        baseline_m = shadow_comparison["baseline"]

        lines.append("| Metric | Shadow | Baseline |")
        lines.append("|---|---|---|")
        lines.append(
            f"| Retrieval event count | {shadow_m['retrieval_event_count']} | "
            f"{baseline_m['retrieval_event_count']} |"
        )

        def _fmt_ratio(agg):
            return "n/a" if agg["ratio"] is None else f"{agg['ratio']:.2f}"

        lines.append(
            f"| Candidate → Selected ratio | "
            f"{_fmt_ratio(shadow_m['candidate_to_selected_aggregate'])} | "
            f"{_fmt_ratio(baseline_m['candidate_to_selected_aggregate'])} |"
        )
        lines.append(
            f"| Selected → Cited ratio | "
            f"{_fmt_ratio(shadow_m['selected_to_cited_aggregate'])} | "
            f"{_fmt_ratio(baseline_m['selected_to_cited_aggregate'])} |"
        )
        lines.append(
            f"| Expansion rate | {shadow_m['expansion_rate'] * 100:.1f}% | "
            f"{baseline_m['expansion_rate'] * 100:.1f}% |"
        )
        lines.append("")

        lines.append("**Cache Rates by Level — Shadow**")
        lines.append("")
        if shadow_m["cache_rates"]:
            lines.append(f"| Cache Level | {HIT} | {MISS} | {STALE_REJECTED} | Total |")
            lines.append("|---|---|---|---|---|")
            for cache_level in sorted(shadow_m["cache_rates"]):
                row = shadow_m["cache_rates"][cache_level]
                counts = row["counts"]
                lines.append(
                    f"| {cache_level} | {counts.get(HIT, 0)} | {counts.get(MISS, 0)} | "
                    f"{counts.get(STALE_REJECTED, 0)} | {row['total']} |"
                )
        else:
            lines.append("_No cache-level data this period._")
        lines.append("")

        lines.append("**Cache Rates by Level — Baseline**")
        lines.append("")
        if baseline_m["cache_rates"]:
            lines.append(f"| Cache Level | {HIT} | {MISS} | {STALE_REJECTED} | Total |")
            lines.append("|---|---|---|---|---|")
            for cache_level in sorted(baseline_m["cache_rates"]):
                row = baseline_m["cache_rates"][cache_level]
                counts = row["counts"]
                lines.append(
                    f"| {cache_level} | {counts.get(HIT, 0)} | {counts.get(MISS, 0)} | "
                    f"{counts.get(STALE_REJECTED, 0)} | {row['total']} |"
                )
        else:
            lines.append("_No cache-level data this period._")
        lines.append("")

        lines.append("**Freshness / Authority — Shadow**")
        lines.append("")
        lines.append(f"Authority: {dict(shadow_m['authority_distribution']) or '_none_'}")
        lines.append(f"Freshness: {dict(shadow_m['freshness_distribution']) or '_none_'}")
        lines.append("")
        lines.append("**Freshness / Authority — Baseline**")
        lines.append("")
        lines.append(f"Authority: {dict(baseline_m['authority_distribution']) or '_none_'}")
        lines.append(f"Freshness: {dict(baseline_m['freshness_distribution']) or '_none_'}")
        lines.append("")
```

(Exact string formatting for the freshness/authority lines is at the implementer's discretion —
a compact inline rendering is acceptable since the ticket does not require a full sub-table per
distribution; the comparison-table rows for count/ratios/expansion-rate above are the load-bearing
content. Implementer may render freshness/authority as tables mirroring `## Retrieval Quality`'s
own sub-table style instead, if preferred, as long as no six-criteria phrase is introduced — see
Step 3.)

**Do NOT touch:** the existing `## Retrieval Quality` block's gating condition (`if
retrieval_metrics["retrieval_event_count"]:`, line ~901) or any of its rendered lines; the
placement must be strictly additive (new lines only), never interleaved with or reordering the
existing block.

**Verify:**
- `test_shadow_comparison_section_omitted_when_zero_shadow_events` (fixture with only synthetic
  retrieval events → no `## Shadow vs. Baseline Retrieval Comparison` heading anywhere in output;
  same for a fixture with zero retrieval events of any kind)
- `test_shadow_comparison_section_rendered_when_shadow_events_nonzero` (fixture with at least one
  `TCK-...`-run_id, `agent="context-packet-wrapper"`, `phase="Retrieval"` event → heading present,
  at least one numeric field spot-checked against hand-computed expectation)
- `test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture` (fixture with zero
  shadow/synthetic retrieval events at all → full `generate()` output identical to
  pre-this-ticket's exact rendered text; also re-run the full existing `test_generate_retro.py`
  suite unmodified as the broader regression proof)

### Step 3 — Phrase-absence guard for the six approval-gate criteria

**Files:** `tests/tools/test_generate_retro.py` (test-only; no production code change beyond
Step 2's own careful wording, already written above without any of these phrases)

**Change:** Add `test_shadow_comparison_never_emits_any_approval_gate_criteria_phrase`: render
`generate()` against the nonzero-shadow-events fixture from Step 2's second test, and assert none
of the following substrings appear anywhere in the full rendered report text: `"authoritative-
source recall"`, `"missed contracts"`, `"review rework"`, `"context tokens"` (as a reduction
claim), `"cache correctness"`, `"provider parity"`, `"privacy boundary"`, `"approval gate"`,
`"promotion"`. This is a pure test addition — if it fails, the fix is to reword Step 2's rendered
text, not to add new computation.

**Do NOT touch:** any of the six approval-gate criteria's actual measurement logic — do not add
recall computation, a "material increase" threshold, a token-reduction claim, a stale-rejection
correctness check, a provider-parity comparison, or a privacy-boundary scan. None of these exist
in `compute_retrieval_metrics()`'s domain and none should be added anywhere in this ticket.

**Verify:** `test_shadow_comparison_never_emits_any_approval_gate_criteria_phrase` passes.

### Step 4 — Fixture-only guard for the new tests

**Files:** `tests/tools/test_generate_retro.py` (test-only)

**Change:** Add `test_shadow_comparison_new_tests_are_fixture_only_no_live_data_read`: via
`inspect.getsource()`/`ast`-walk of the new test functions added in Steps 1-3, assert no reference
to `EVENTS_FILE`, `RUNS_FILE`, `DEFAULT_DB_PATH`, or `_load_runs_and_events` appears — mirroring
`test_retrieval_baseline_metrics.py::test_baseline_report_reuses_load_data_pattern_not_a_fourth_
loader`'s reuse-guard technique, applied here as a live-data-absence guard.

**Do NOT touch:** the existing tests that legitimately do read live data via `tmp_path`-based
fixtures for unrelated `generate_retro.py` behavior (e.g. `test_generate_retro_builds_index_on_
demand_when_missing`) — this guard applies only to the new tests added by this ticket.

**Verify:** `test_shadow_comparison_new_tests_are_fixture_only_no_live_data_read` passes.

### Step 5 — Parity ledger entry INFRA-300

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry after INFRA-299 (currently the last entry, ends at line ~6335),
following the exact YAML field set every INFRA-29x entry uses (`id`, `text`, `status`, `priority`,
`legacy_evidence`, `v2_evidence`, `proof_type`, `test_path`, `divergence_note`,
`support_boundary`):

```yaml
- id: INFRA-300
  text: >
    generate_retro.py gains compute_shadow_baseline_comparison(events), a new pure function that
    partitions retrieval-shaped events into a shadow cohort (real TCK-... run_ids) and a baseline
    cohort (synthetic RETRIEVAL-EVENT-... run_ids) using vocabulary.infer_workflow(run_id) is not
    None -- the same non-None-vs-None idiom _normalize_phase()/_normalize_agent() already use --
    then calls the existing compute_retrieval_metrics() (INFRA-298) once per cohort, never
    reimplementing its cache-rate/noise-ratio/freshness-authority/expansion-rate logic. generate()
    renders the result as a new, additively-appended "## Shadow vs. Baseline Retrieval Comparison"
    section, placed after the existing "## Retrieval Quality" section and before "## Notes",
    gated on the shadow cohort's retrieval_event_count being nonzero -- omitted entirely, not
    rendered empty, when it is zero, mirroring the existing section's own gate. Comparison data
    only: renders no phrase from the six approval-gate criteria in docs/plans/
    agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_
    observability.md's "Shadow evaluation and approval gate" section -- that remains a distinct,
    larger, not-yet-built concept this ticket does not implement.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: >
    tools/agent-monitoring/generate_retro.py::compute_shadow_baseline_comparison() -- new function,
    partitions by infer_workflow(run_id) is not None, returns {"shadow": ..., "baseline": ...}
    each shaped identically to compute_retrieval_metrics()'s own return dict.
    tools/agent-monitoring/generate_retro.py::generate() -- new conditionally-rendered
    "## Shadow vs. Baseline Retrieval Comparison" section, gated on
    shadow_comparison["shadow"]["retrieval_event_count"], omitted entirely when zero.
  proof_type: regression
  test_path: tests/tools/test_generate_retro.py
  divergence_note: null
  support_boundary: >
    Agent-orchestration/retrieval tooling only -- no simulation behavior, Mechanics Bible chapter,
    or engine contract governs this module's semantics (same category as INFRA-281 through
    INFRA-299). No `src/` file touched, no on-disk schema/corpus change, no new event-emission or
    call-site logic -- this is a pure read-only consumer of already-emitted events. Real shadow-
    cohort volume in the live agent-monitoring/events.jsonl corpus stays at zero while
    SHADOW_CONTEXT_PACKET_ENABLED remains unset (the current default per INFRA-299) -- the new
    section only populates against fixture/test data or a future manual invocation until that flag
    is enabled.
```

**Do NOT touch:** INFRA-296, INFRA-297, INFRA-298, or INFRA-299's existing text/fields — this is a
new, additive entry, not a correction to any of them (see Summary's Parity ledger decision).

**Verify:** `python3 tools/validate_frontmatter.py` (or the project's standard parity-ledger schema
check, if a dedicated one exists) accepts the new entry; no existing parity ledger test breaks.

## Scope Guards

- **No six-approval-gate-criteria scorecard.** Never compute or render recall,
  missed-contracts/test-gate-failure/review-rework deltas, a token-reduction claim, cache
  stale-rejection "correctness," provider parity, or a privacy-boundary check. Verified by Step 3's
  `test_shadow_comparison_never_emits_any_approval_gate_criteria_phrase`.
- **No changes to `retrieval_baseline_metrics.py`.** File is not touched by any step in this plan.
  Verified by re-running `tests/tools/test_retrieval_baseline_metrics.py` unmodified and confirming
  zero diff to that file.
- **Existing non-shadow report output stays byte-identical.** Verified by Step 2's
  `test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture` (fixture with zero
  shadow/synthetic events → identical full output) plus the full existing
  `tests/tools/test_generate_retro.py` suite passing unmodified — any diff in an existing test's
  expected string is a signal the additive boundary leaked.
- **No live dashboard/UI.** No new frontend/UI file is created; Markdown text output only, same
  mechanism `test_no_new_frontend_ui_file_introduced_by_this_ticket` already guards for the
  sibling `## Retrieval Quality` feature.
- **No new event-emission or call-site logic.** `tools/retrieval_events.py` and any
  `.claude/workflows/*.js` orchestrator file are not touched by any step — this ticket only reads
  events already emitted by the (already-merged) `TCK-20260729-SHADOW-PACKET-CALL-SITE`.
- **`compute_retrieval_metrics()` itself is not modified** — no signature, return-shape, or
  literal change. Only called (twice, once per cohort). Verified by the full existing
  `TestComputeRetrievalMetrics` class continuing to pass unmodified, plus Step 1's own
  reuse-not-reimplement source-text guard.
- **The existing `## Retrieval Quality` section's gate and content are untouched** — the new
  section is a separate, independently-gated block appended after it.
- **No parallel `run_id.startswith(...)` literal** — `vocabulary.infer_workflow()` is the single
  partition mechanism. Verified by Step 1's source-text assertion.

## Dependency Map

- Step 2 depends on Step 1 (`compute_shadow_baseline_comparison()` must exist before `generate()`
  can call it).
- Step 3 depends on Step 2 (asserts against Step 2's rendered output text).
- Step 4 depends on Steps 1-3 existing (it source-scans the test functions they add), but is
  otherwise independent of their outcome — it can run any time after they are written.
- Step 5 (parity ledger) is independent of Steps 1-4's test outcomes but should land last, once the
  implementation is final, since its `text`/`v2_evidence` describe the shipped behavior.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A new function partitions retrieval-shaped events by real-vs-synthetic run_id provenance and computes comparison rows using compute_retrieval_metrics()'s measurement domain | Step 1 | `test_shadow_comparison_partitions_real_vs_synthetic_run_id`, `test_shadow_comparison_computes_same_measurement_domain_as_compute_retrieval_metrics`, `test_shadow_comparison_reuses_compute_retrieval_metrics_not_reimplemented` |
| When zero shadow (real-run-id) events are present, the new report section is omitted entirely | Step 2 | `test_shadow_comparison_section_omitted_when_zero_shadow_events` |
| Existing non-shadow report output remains byte-identical to current output on the same fixture inputs | Step 2 | `test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture` (plus full existing suite passing unmodified) |
| No phrase from any of the six approval-gate criteria appears in the new comparison section's generated text | Step 3 | `test_shadow_comparison_never_emits_any_approval_gate_criteria_phrase` |
| New tests are fixture-only, with no live-data dependency | Step 4 (guards Steps 1-3's tests) | `test_shadow_comparison_new_tests_are_fixture_only_no_live_data_read` |

## Anti-Drift Notes

- Reuse `vocabulary.infer_workflow(run_id) is not None` as the sole partition predicate — do not
  invent a second `run_id.startswith("TCK-")`/`startswith("RETRIEVAL-EVENT-")` literal check. This
  is investigation Risk #1's explicit recommendation and Anti-Drift Hazard; a parallel literal
  would silently desynchronize from any future change to `infer_workflow()`'s prefix list.
- `compute_shadow_baseline_comparison()` must call `compute_retrieval_metrics()` twice (once per
  cohort's filtered event list) — never re-literal `HIT`/`MISS`/`STALE_REJECTED`,
  `INDEX_CACHE_CATEGORY`/`QUERY_CACHE_CATEGORY`/`PACKET_CACHE_CATEGORY`, or `UNRATED` inside the
  new function. These are `compute_retrieval_metrics()`'s constants; the new function only touches
  the dict it returns.
- The new section's gate must be on the **shadow cohort's** `retrieval_event_count`, not on
  "any retrieval events of either cohort." A fixture with a large synthetic/baseline population but
  zero shadow events must still omit the new section entirely — conflating the two would drift
  from the ticket's literal AC wording ("zero shadow (real-run-id) events").
- Do not pre-filter `events` to `"retrieval_event_schema_version" in e` before partitioning by
  run_id — `compute_retrieval_metrics()` already applies that filter internally for each cohort's
  list. Adding a redundant pre-filter is not wrong, but it duplicates logic already owned
  elsewhere; Step 1's function as specified passes the unfiltered per-cohort event list straight
  through.
- Zero live shadow data exists at implementation time (`SHADOW_CONTEXT_PACKET_ENABLED` defaults
  off, per INFRA-299) — this is expected and does not block correctness; all new tests are
  fixture-only by design (Step 4 makes this a hard test-time guard, not just a convention).
- The section heading and inline caveat text (Step 2) must not use the words "approval," "gate"
  (as in approval-gate), "promotion," or "scorecard," and must not echo any of the six criteria's
  phrasing verbatim or in close paraphrase (Step 3 makes this a hard test-time guard).

## Deviations

- **Step 2's caveat text, as literally sampled in this plan, was self-contradictory and had to be
  reworded during implementation.** The sample code block's caveat line —
  `"Comparison data only — not a promotion or approval-gate scorecard._"` — contains the literal
  words `"promotion"` and `"approval-gate"`. This directly conflicts with this same document's own
  Anti-Drift Note two paragraphs above ("must not use the words 'approval,' 'gate' ... 'promotion,'
  or 'scorecard'") and with Step 3's own phrase-absence test list (which bans the literal substring
  `"promotion"`). Since Step 3 explicitly states "if it fails, the fix is to reword Step 2's
  rendered text, not to add new computation," the implementer shortened the caveat line to
  `"Comparison data only._"`, dropping the self-contradictory clause. No gating condition,
  computation, section placement, or any other wording changed. All of Step 3's phrase-absence
  assertions (including the `"promotion"` and `"approval gate"` checks) pass against the shipped
  text.
