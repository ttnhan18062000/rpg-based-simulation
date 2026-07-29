---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-RETRO-VIEWS
artifact_type: plan
tags: [observability, agent-monitoring, retro]
---

# Implementation Plan — TCK-20260729-RETRIEVAL-RETRO-VIEWS

## Summary

This ticket closes the gap between `compute_retrieval_metrics()` (shipped by
TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT as a minimal proof, never called by `generate()`) and a
real, rendered retro-report section covering all four dashboard signals from the idea doc: cache
hit/miss/stale-rejection rates by cache level (already covered, needs only rendering), an
aggregated candidate-to-selected / selected-to-cited noise-indicator view (the existing function
only returns a raw per-event list), a freshness/authority distribution that correctly buckets the
`UNRATED` sentinel, and a follow-up/expansion rate. All new logic lives in
`tools/agent-monitoring/generate_retro.py`, extending `compute_retrieval_metrics()` in place
(never `query.py` — its hard `sys.exit(1)`-on-missing-index contract is incompatible with a
graceful, always-available report section, and `compute_retrieval_metrics()` is already a pure
function with no SQLite dependency). `generate()` gains one new conditionally-rendered "##
Retrieval Quality" Markdown section, following the exact `if metrics[...]:` gating pattern already
used for Outliers/Tag Breakdown, appended after the existing Outliers section and before Notes so
it never disturbs any existing section's ordering. The section carries an explicit inline caveat
that retrieval-event volume is visible only under `--all` (never `--days`/`--week`), since
`RETRIEVAL-EVENT-<slug>` run_ids never match a `runs.jsonl` row by design. All five ambiguities
flagged by the investigation (expansion-rate formula, file placement, `--all`-only visibility,
fixture convention, parity-ledger entry) are resolved below — no unresolved question blocks
implementation.

## Resolved Decisions

1. **Expansion-rate formula — UNCONDITIONAL.** `expansion_rate = (# retrieval events carrying
   `expansion_reason` or `expansion_count`) / (# retrieval events total)`, NOT conditioned on
   `adequacy_verdict`. Investigation confirmed (Current Behavior §1, Risk #1) that none of the 3
   shipped `wrap_*()` functions ever emit `expansion_reason`/`expansion_count` today — there is no
   real code path to validate a conditional-on-verdict formula against, which would make that
   reading unfalsifiable against genuinely producible data right now. The unconditional formula is
   chosen because it is the only one testable against fixture data that reflects actual current
   system behavior (0% rate on any realistic fixture, per test_plan.md item 4's second test). A
   future ticket can add a conditional breakdown (rate among `"insufficient"`/`"noisy"`-verdict
   events specifically) once a real expansion-emitting wrapper exists.
2. **Location — `generate_retro.py`, extending `compute_retrieval_metrics()` in place.** Matches
   investigation's own recommendation (Current Behavior, `query.py` section), the existing
   pure-function precedent (`compute_retrieval_metrics()` already operates on a plain
   `events: list[dict]`, confirmed read-only by
   `test_function_is_read_only_no_write_call_or_file_open_in_write_mode`), and avoids `query.py`'s
   incompatible hard `sys.exit(1)`-on-missing-index contract (`open_index()`, query.py:29-36) for
   what must be a graceful, always-available report section. `query.py` is not touched by this
   plan at all — no new filter flag is in scope (ticket's Scope allows either-or-both; this plan
   picks `generate_retro.py`-only since "dashboard view" is a materially different feature from
   "browse individual matching events").
3. **`--all`-only visibility — YES, explicit inline caveat.** The rendered "## Retrieval Quality"
   section carries a one-line note: "Retrieval-event volume reflects test/manual invocations only;
   visible under `--all`, not `--days`/`--week`, since these run_ids are deliberately unlinked from
   any `runs.jsonl` row." This does not silently ship a section that mysteriously never appears
   under the two most common CLI flags. No change to `main()`'s existing `--days`/`--week`
   run_id-membership filtering (investigation Risk #3, option (a) — additive-only, consistent with
   the schema-emit ticket's explicit design intent that retrieval events "do not corrupt or
   interleave into any existing run-scoped retro/dashboard view").
4. **Fixture convention — inline synthetic builder, following sibling precedent.** New tests reuse
   the existing `_retrieval_event(**overrides)` helper (test_generate_retro.py:1033-1045),
   extending it with new overrides (`authority_counts`, `freshness_counts`, `adequacy_verdict`,
   `expansion_reason`, `expansion_count`) rather than attempting a literal
   `tests/fixtures/agent_monitoring/*.jsonl` PROVENANCE.md-compliant extraction. Investigation
   confirmed zero real retrieval-event corpus lines exist to extract from (PROVENANCE.md section),
   and the sibling schema-emit ticket's own shipped tests already established this exact deviation
   as the working convention. This is a documented Resolved Decision, not a silent scope deviation
   from the ticket's Scope wording ("following the `tests/fixtures/agent_monitoring/*.jsonl`
   convention" is read as "in-repo, fixture-style, never validated only against live data," per the
   AC5 text itself).
5. **Parity ledger — new INFRA-298 entry.** Unlike a test-only sibling ticket that might claim a
   no-new-entry exemption, this ticket adds new real behavior (dashboard views wired into
   `generate()`'s actual rendered report output, not just test-only proof), following the
   established 1:1 ticket-to-INFRA-entry pattern already used for INFRA-293 through INFRA-297 in
   this same batch. `id: INFRA-298` (confirmed next free ID — INFRA-297 is the last entry in
   `docs/parity_ledger/infrastructure.yaml`), `test_path: tests/tools/test_generate_retro.py`,
   `priority: P2` (matches the family's existing priority, no P0 in scope),
   `status: verified` once Step 6's tests pass.

## Steps

### Step 1 — Aggregate candidate-to-selected / selected-to-cited into a noise-indicator view

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** Inside `compute_retrieval_metrics()` (generate_retro.py:561-617), add an aggregated
view alongside the existing per-event `candidate_to_selected_ratios` / `selected_to_cited_ratios`
lists (do not remove or alter those two existing keys — they are covered by passing tests today).
Add two new keys to the returned dict:
- `"candidate_to_selected_aggregate"`: `{"total_candidates": int, "total_selected": int, "ratio":
  float | None}` — `ratio = total_selected / total_candidates if total_candidates else None`,
  summed across all `retrieval_events` that carry both `candidate_count` and `selected_count`.
- `"selected_to_cited_aggregate"`: `{"total_selected": int, "total_cited": int, "ratio": float |
  None}` — `ratio = total_cited / total_selected if total_selected else None`, summed across all
  `retrieval_events` that carry both `selected_count` and `cited_source_hashes` (`total_cited` =
  sum of `len(cited_source_hashes)`).

Compute both aggregates in the same loop that already builds the per-event lists (lines 596-610)
to avoid iterating `retrieval_events` twice — accumulate running sums, then compute the two ratios
once after the loop, zero-guarded.

**Do NOT touch:** the existing per-event `candidate_to_selected_ratios` / `selected_to_cited_ratios`
list-building logic or their existing dict keys/shape — these are separately tested and referenced
by AC2's per-event coverage; this step is purely additive.

**Verify:** `test_candidate_to_selected_and_selected_to_cited_aggregate_ratio`
(tests/tools/test_generate_retro.py) — asserts correct aggregate ratios across a fixture with
mixed candidate/selected/cited combinations, including one all-zero-candidate fixture (ratio is
`None`, no `ZeroDivisionError`) and one zero-count-within-a-larger-fixture case.

### Step 2 — Freshness/authority distribution, including the UNRATED sentinel

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** Add `from hybrid_retrieval import UNRATED  # noqa: E402` near the existing
`sys.path.insert(0, str(_TOOLS_DIR))` import block (generate_retro.py:24-32) — `_TOOLS_DIR` is
`tools/`, and `hybrid_retrieval.py` lives directly under `tools/`, so this import resolves via the
existing sys.path wiring without any new path manipulation. `UNRATED` is imported for
documentation/anti-drift purposes (the aggregation itself is a plain `Counter`, which naturally
buckets any string value including `"unrated"` — no special-casing needed per investigation's
"Current Behavior" `hybrid_retrieval.py` section) — but the anti-drift test guard (Step 5 below)
requires the import exist and any comparison/example code reference the constant, not a re-literaled
`"unrated"` string.

Inside `compute_retrieval_metrics()`, add a new aggregation loop over `retrieval_events` that reads
`e.get("authority_counts")` and `e.get("freshness_counts")` — both are pre-aggregated `dict[str,
int]` fields already produced upstream by `wrap_hybrid_retrieval()` (per investigation:
`Counter(r.authority for r in results)`), so this function sums them across events rather than
recomputing from raw results. Add two new keys to the returned dict:
- `"authority_distribution"`: `dict[str, int]` — summed `authority_counts` across all
  `retrieval_events` that carry the field. Events without `authority_counts` are skipped, not
  crashed on (`KeyError`).
- `"freshness_distribution"`: `dict[str, int]` — same treatment for `freshness_counts`.

Both distributions must include an `"unrated"` bucket if it is present in any event's
`authority_counts`/`freshness_counts` — a plain `Counter.update(dict)` / manual dict-sum achieves
this naturally since it treats every key uniformly; do not add an allowlist/known-values filter.

**Do NOT touch:** `hybrid_retrieval.py` itself (read-only reference for the `UNRATED` constant —
this ticket's Related Code Areas lists it as read-only) or the `wrap_hybrid_retrieval()` function
that produces `authority_counts`/`freshness_counts` in the first place.

**Verify:**
`test_freshness_authority_distribution_includes_unrated_sentinel_bucket` and
`test_freshness_authority_distribution_empty_when_no_counts_present`
(tests/tools/test_generate_retro.py).

### Step 3 — Follow-up/expansion rate

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** Inside `compute_retrieval_metrics()`, add a new key to the returned dict:
- `"expansion_rate"`: `float` — computed as `(count of retrieval_events where
  e.get("expansion_reason") is not None or e.get("expansion_count") is not None) /
  len(retrieval_events)` if `retrieval_events` is non-empty, else `0.0` (or `None` — pick `0.0` for
  consistency with an empty-but-valid report, since `retrieval_event_count` is already `0` in that
  case and a `None` rate reads as "unknown" rather than "no events," document the choice with a
  one-line comment above the computation). This is the UNCONDITIONAL formula from Resolved Decision
  1 above — add a code comment directly above this block citing that the conditional-on-
  `adequacy_verdict` alternative was considered and rejected because no shipped wrapper emits
  `expansion_reason`/`expansion_count` today, making it untestable against real behavior.

Do not read `adequacy_verdict` for this computation — it is not part of the formula. (It remains
available on the raw event dicts for a future ticket to build a conditional breakdown, but this
step does not surface a separate `adequacy_verdict`-keyed view; that would be new, unscoped work.)

**Do NOT touch:** `retrieval_events.py::compute_adequacy_verdict()` — read-only reference, not
modified. Do not fabricate test fixtures implying a real call site populates
`expansion_reason`/`expansion_count` — per investigation's Anti-Drift Hazards, any such fixture
must be clearly synthetic and the function must correctly return a `0.0`/near-zero rate for the
realistic all-fields-missing case.

**Verify:**
`test_expansion_rate_computed_from_adequacy_verdict_and_expansion_fields` and
`test_expansion_rate_zero_when_no_events_carry_expansion_fields`
(tests/tools/test_generate_retro.py).

### Step 4 — Cache-rate literal-reuse anti-drift fix (housekeeping, in the same function)

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** The existing cache-rate logic (lines 575-592) already correctly groups by
`cache_level`/`cache_status` — no logic change required (AC1 is already satisfied per investigation
"Current Behavior" item 2). However, since Steps 1-3 add new imports at the top of the file, add
`from retrieval_cache import HIT, MISS, STALE_REJECTED, INDEX_CACHE_CATEGORY, QUERY_CACHE_CATEGORY,
PACKET_CACHE_CATEGORY  # noqa: E402` alongside the Step 2 `hybrid_retrieval` import (same sys.path
block), even though `compute_retrieval_metrics()`'s cache-rate code itself does not need to
re-literal any of these (it reads `cache_level`/`cache_status` generically off the event dict, no
hardcoded status strings exist in the function body today). The import exists so that (a) the new
Step 6 test fixtures and (b) the Step 5 anti-drift test can both reference the real constants
rather than any test/production code re-literaling `"hit"`/`"retrieval_index_cache"` etc.

**Do NOT touch:** the existing `cache_status_counts_by_level` / `cache_rates` computation logic
(lines 575-592) — this step is import-only, zero behavior change. `retrieval_cache.py` itself is
not modified (read-only reference).

**Verify:** covered transitively by `test_cache_rates_already_covers_hit_miss_stale_rejected_by_level`
(regression-proof, test_plan.md item 1) and the Step 5 literal-reuse guard.

### Step 5 — Read-only / pure-function architecture guard extension

**Files:** `tests/tools/test_generate_retro.py`

**Change:** Extend the existing read-only guard pattern
(`test_function_is_read_only_no_write_call_or_file_open_in_write_mode`,
test_generate_retro.py:1112-1119) to re-run against the now-extended `compute_retrieval_metrics()`
source (same function, no new sibling function is introduced — Steps 1-3 all extend the one
existing function in place per this plan's Resolved Decision 2). No new test class is needed since
there is no new function to guard separately; the existing test's `inspect.getsource(
compute_retrieval_metrics)` call automatically covers the Step 1-4 additions. Add one new
assertion to the same test: `assert "EVENTS_FILE" not in source` and `assert "RUNS_FILE" not in
source` and `assert "load_jsonl" not in source` and `assert "DEFAULT_DB_PATH" not in source` — these
were previously true implicitly (the function never used them) but were not explicitly asserted;
making them explicit now that new logic has been added guards against a future edit accidentally
introducing a live-file dependency.

Additionally add a new literal-reuse anti-drift test,
`test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants`, asserting via
`inspect.getsource(compute_retrieval_metrics)` (and the module-level import statements) that the
bare string literals `"hit"`, `"miss"`, `"stale-rejected"`, `"retrieval_index_cache"`,
`"retrieval_query_cache"`, `"retrieval_packet_cache"` do not appear as Python string literals in
the function body (they may appear inside docstrings/comments), while confirming `HIT`, `MISS`,
`STALE_REJECTED`, `INDEX_CACHE_CATEGORY`, `QUERY_CACHE_CATEGORY`, `PACKET_CACHE_CATEGORY`, and
`UNRATED` are imported at module level.

**Do NOT touch:** `test_normalize_phase_agent_and_flag_outliers_untouched`'s SHA256 source-hash pin
— that test targets a disjoint set of functions (`_resolve_status`/`_is_legacy_event`/
`_is_gate_fail`/`_normalize_phase`/`_normalize_agent`/`_canonicalize`/`_flag_outliers`), none of
which this ticket modifies.

**Verify:** the extended
`test_function_is_read_only_no_write_call_or_file_open_in_write_mode` plus the new
`test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants` test, both green.

### Step 6 — Render the "## Retrieval Quality" section in `generate()`

**Files:** `tools/agent-monitoring/generate_retro.py`

**Change:** In `generate()` (generate_retro.py:620-840), add a call to
`retrieval_metrics = compute_retrieval_metrics(events)` near the top of the function (alongside the
existing `metrics = compute_retro_metrics(runs, events, tickets_root)` call, generate_retro.py:626)
so it operates on the same `events` list already passed into `generate()` — no new argument to
`generate()`'s signature. Insert a new conditionally-rendered section **after** the existing
Outliers section (after line 832, before the "## Notes" block starting at line 834), gated on
`if retrieval_metrics["retrieval_event_count"]:` — mirrors the exact `if metrics[...]:` truthy-gate
pattern already used for Reason Codes/Tag Breakdown/Outliers (lines 671, 683, 694, 803). When zero
retrieval events are present (the realistic majority case today), the section is omitted entirely,
not rendered empty — matching AC6's own test (`test_retrieval_quality_section_omitted_when_no_
retrieval_events`).

Section content, in order:
1. `## Retrieval Quality` heading.
2. The `--all`-only caveat line (Resolved Decision 3, verbatim or near-verbatim): "_Retrieval-event
   volume reflects test/manual invocations only; visible under `--all`, not `--days`/`--week`,
   since these run_ids are deliberately unlinked from any `runs.jsonl` row._"
3. A "Cache Rates by Level" subsection/table rendering `retrieval_metrics["cache_rates"]` (one row
   per `cache_level` × `cache_status`, or one table per level — follow the existing Agent/Phase
   Status Distribution table shape at lines 720-728 for consistency: `| Cache Level | hit | miss |
   stale-rejected | Total |`).
4. A "Noise Indicators" subsection rendering `candidate_to_selected_aggregate` and
   `selected_to_cited_aggregate` (Step 1) as a small key-value table — render `ratio: None` as
   `"n/a"`, never as the literal string `"None"` or a crash.
5. A "Freshness / Authority Distribution" subsection rendering `authority_distribution` and
   `freshness_distribution` (Step 2) as two small tables, each bucket (including `unrated`) as its
   own row.
6. An "Expansion Rate" line rendering `expansion_rate` (Step 3) as a formatted percentage via the
   existing `fmt_pct`-style helper already used elsewhere in `generate()` (or a one-line `f"{rate *
   100:.1f}%"` if `fmt_pct` doesn't fit the numerator/denominator shape here — check `fmt_pct`'s
   signature first and reuse it if compatible, since it is already imported/used throughout this
   function for the exact same percentage-formatting need).

**Do NOT touch:** any existing section's rendering logic, line ordering, or Markdown structure
(Run Summary, Gate Failure Breakdown, Reason Codes, Tag Breakdown ×2, Tier Distribution, Agent/Phase
Status Distribution, Spend Proxy ×2, Summary Quality, Slow Runs, Outliers, Notes) — this step only
inserts new lines between the existing Outliers block (ends line 832) and the existing Notes block
(starts line 834). Do not reorder or rename any existing `## ` heading.

**Verify:**
`test_retrieval_quality_section_omitted_when_no_retrieval_events`,
`test_retrieval_quality_section_rendered_with_fixture_retrieval_events`,
`test_retrieval_quality_section_placement_does_not_disturb_existing_sections`
(all in tests/tools/test_generate_retro.py) — plus re-running
`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` to confirm the
frozen no-retrieval-events fixture's Markdown output hash is unchanged (proves the new section is
correctly gated off).

### Step 7 — "No new frontend/UI file" structural guard

**Files:** `tests/tools/test_generate_retro.py`

**Change:** Add `test_no_new_frontend_ui_file_introduced_by_this_ticket` — a lightweight structural
check (mirrors the schema-emit ticket's own AC6 grep-based guard style) confirming no new file
under a frontend/dashboard-UI directory (e.g. `dashboard-frontend/src/`,
`experiments/agent_ops_dashboard/`) is referenced or imported by any code touched in this ticket.
Simplest implementation: assert `compute_retrieval_metrics`'s and `generate()`'s source contain no
`import` statement referencing those directory names, and/or assert (via `git diff --name-only` at
test time is too fragile/non-hermetic — instead) a static string-absence check against the two
functions' `inspect.getsource()` output for any frontend-path-shaped string literal.

**Do NOT touch:** any actual frontend directory — this is a guard against introducing one, not a
change to existing frontend code (none is touched by this ticket, confirmed by Related Code Areas).

**Verify:** `test_no_new_frontend_ui_file_introduced_by_this_ticket` passes; combined with AC6's
first half (Step 6 verifies the section renders via the existing conditional-render pattern).

### Step 8 — Parity ledger: add INFRA-298

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry after INFRA-297 (currently the last entry, ends at line ~6232),
following the exact YAML shape and field set of INFRA-293 through INFRA-297 — architecture review
(NEEDS_CHANGES round) found the first draft of this entry omitted `legacy_evidence`, `proof_type`,
and `support_boundary`, all present on every sibling entry; the corrected entry includes them:
```yaml
- id: INFRA-298
  text: >
    generate_retro.py's compute_retrieval_metrics() (previously computed but never rendered by
    generate(), per TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT's own AC7 minimal-proof scoping) is
    extended in place with an aggregated candidate-to-selected/selected-to-cited noise-indicator
    view, a freshness/authority distribution (including the UNRATED sentinel bucket, imported from
    hybrid_retrieval.py, never re-literaled), and an unconditional follow-up/expansion rate --
    unconditional rather than adequacy_verdict-conditional because no shipped wrap_*() function
    emits expansion_reason/expansion_count today, making a conditional formula untestable against
    real behavior. generate() now calls compute_retrieval_metrics(events) and renders all four
    retrieval-quality signals (cache rates by level, noise indicators, freshness/authority
    distribution, expansion rate) as a new conditionally-gated "## Retrieval Quality" Markdown
    section -- the first real rendered dashboard output this event family produces, inserted after
    the existing Outliers section and before Notes, disturbing no existing section's ordering.
    Visible only under --all (never --days/--week), with an explicit inline caveat, since
    RETRIEVAL-EVENT-<slug> run_ids are deliberately unlinked from any runs.jsonl row by the
    schema-emit ticket's own design (docs/agent-monitoring/schema.md's provenance section)`; this
    plan does not special-case that filter, preserving that documented isolation intent.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: >
    tools/agent-monitoring/generate_retro.py::compute_retrieval_metrics() -- extended with
    candidate_to_selected_aggregate/selected_to_cited_aggregate (zero-division guarded),
    authority_distribution/freshness_distribution (UNRATED-inclusive), expansion_rate
    (unconditional formula). tools/agent-monitoring/generate_retro.py::generate() -- new
    conditionally-rendered "## Retrieval Quality" section, gated on
    retrieval_metrics["retrieval_event_count"], omitted entirely (not rendered empty) when zero
    retrieval events are present.
  proof_type: regression
  test_path: tests/tools/test_generate_retro.py
  divergence_note: null
  support_boundary: >
    Agent-orchestration/retrieval tooling only -- no simulation behavior, Mechanics Bible chapter,
    or engine contract governs this module's semantics (same category as INFRA-281 through
    INFRA-297). No `src/` file touched, no on-disk schema/corpus change to any existing store, and
    not wired into any real-time workflow orchestrator file or existing pipeline/gate -- real
    retrieval-event volume in the live `agent-monitoring/events.jsonl` stays at zero after this
    ticket ships, by design; the new report section only ever populates against fixture/test data
    or a future manual invocation, never against a real tracked workflow run.
```
Field names, order, and presence of `legacy_evidence`/`proof_type`/`support_boundary` must match
`docs/parity_ledger/schema.json` and the immediately preceding INFRA-297 entry's structure exactly
— copy its shape verbatim (already done above) and do not omit any of its fields.

**Do NOT touch:** INFRA-297's own entry (it correctly and accurately scopes itself to the
schema-emit ticket's AC7 minimal proof — leave it untouched per investigation's explicit
recommendation) or any other existing entry in `infrastructure.yaml`.

**Verify:** no automated test — this is a documentation/traceability step verified by the
Definition of Done's "parity ledger updated" requirement and `validate_frontmatter.py`-style YAML
schema validation if such a check exists in the repo's pre-commit/CI (confirm via
`python3 tools/parity_ledger_lint.py` or equivalent if present; otherwise visual diff against
schema.json is sufficient).

## Scope Guards

Verbatim from the ticket's Out of Scope section — none of the following are touched by any step
above:

- No `execution_id` or `provider` fields added to `runs.jsonl`/`events.jsonl`, and no cross-provider
  comparison views (forbidden this phase; would be a Phase 4b follow-on if needed).
- No new dashboard frontend/UI surface — extends `generate_retro.py`/`query.py`/existing dashboard
  query layer only.
- No wiring into `.claude/workflows/*.js` — views are built and tested against fixture/test-
  invocation data only, since no Phase 3 module is wired into real agent runs yet.
- No live Codex pilot execution.
- Must not assume a bounded/prunable retention window — retrieval events are retain-forever/
  append-only; any windowed aggregation must take an explicit cutoff argument (e.g. `--days`), never
  an assumed default. (No step in this plan adds any new time-windowing to the retrieval views
  themselves — they operate over whatever `events` list `generate()` is already handed, same as
  `compute_retro_metrics()`.)

Additional guards derived from investigation's Anti-Drift Hazards:

- Do not re-derive `cache_status`/`cache_level` string literals — always import from
  `retrieval_cache.py`'s constants (Step 4).
- Do not modify `compute_retro_metrics()` or any of `generate()`'s existing rendered
  sections/ordering (Step 6's "Do NOT touch").
- Do not silently drop the `unrated` sentinel from freshness/authority distributions (Step 2).
- Do not fabricate `expansion_reason`/`expansion_count` test data implying a real call site
  populates it (Step 3, Resolved Decision 1).
- Do not add a new frontend/UI file (Step 7).
- Do not touch `tests/tools/test_monitoring_writer_single_source.py`'s `_CALL_SITES` list or any
  writer/lock mechanism — this ticket is entirely read-only aggregation/rendering.
- Do not assume `agent-monitoring-index/monitoring.db` has retrieval-event awareness — moot since no
  step touches `query.py` or the index at all (Resolved Decision 2).
- `query.py` is not modified by any step in this plan.
- `tools/retrieval_events.py`, `tools/retrieval_cache.py`, `tools/hybrid_retrieval.py` are read-only
  references throughout — imported for constants, never modified.

## Dependency Map

- Steps 1, 2, 3 are independent of each other (each adds a distinct new key to
  `compute_retrieval_metrics()`'s return dict; no shared state between them beyond the same
  `retrieval_events` filter already computed at the top of the function).
- Step 4 (imports) should land before or alongside Steps 1-3, since Steps 2 and 5 both depend on
  the `hybrid_retrieval`/`retrieval_cache` imports being present.
- Step 5 depends on Steps 1-4 being complete (it guards the fully-extended function's source).
- Step 6 depends on Steps 1-4 being complete (it renders all four signals; cannot render
  `candidate_to_selected_aggregate` before Step 1 adds it, etc.).
- Step 7 is independent — can land any time after Step 6 exists (nothing to guard against before
  the section exists, but logically follows Step 6).
- Step 8 (parity ledger) should land last, after Steps 1-7 are verified green, since its
  `v2_evidence` and `text` describe the final shipped state.

Suggested implementation order: 4 → 1 → 2 → 3 → 5 → 6 → 7 → 8.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: cache_status values at multiple cache levels return correct hit/miss/stale-rejection rates by cache level | Already shipped (generate_retro.py:575-592); Step 4 adds constant imports for anti-drift only | `test_cache_rates_already_covers_hit_miss_stale_rejected_by_level` |
| AC2: candidate_count/selected_count/cited-source-hash-count fields return correct candidate-to-selected and selected-to-cited ratios; zero-candidate group does not raise ZeroDivisionError | Step 1 | `test_candidate_to_selected_and_selected_to_cited_aggregate_ratio` |
| AC3: authority_counts/freshness_counts fields (including UNRATED sentinel) return a correct distribution without crashing on the sentinel | Step 2 | `test_freshness_authority_distribution_includes_unrated_sentinel_bucket`, `test_freshness_authority_distribution_empty_when_no_counts_present` |
| AC4: adequacy_verdict and expansion_reason/expansion_count fields return a correct follow-up/expansion rate | Step 3 | `test_expansion_rate_computed_from_adequacy_verdict_and_expansion_fields`, `test_expansion_rate_zero_when_no_events_carry_expansion_fields` |
| AC5: each new function is unit-tested against an in-repo fixture, never validated only against live data | Steps 1-3, 5 | `test_function_is_read_only_no_write_call_or_file_open_in_write_mode` (extended), plus all Step 1-3/6 tests using `_retrieval_event(**overrides)` fixtures |
| AC6: no new frontend/UI file added; new functions live in generate_retro.py and/or query.py; retro report renders new sections following the existing conditional-render pattern | Steps 6, 7 | `test_retrieval_quality_section_omitted_when_no_retrieval_events`, `test_retrieval_quality_section_rendered_with_fixture_retrieval_events`, `test_retrieval_quality_section_placement_does_not_disturb_existing_sections`, `test_no_new_frontend_ui_file_introduced_by_this_ticket` |

## Anti-Drift Notes

- **Never re-literal `"hit"`/`"miss"`/`"stale-rejected"`/`retrieval_index_cache`/etc.** Import from
  `retrieval_cache.py` (Step 4); Step 5's new test enforces this at the source-inspection level.
- **`UNRATED` is a genuine third bucket, not a member of the real authority/freshness enums**
  (`hybrid_retrieval.py:45`'s own assertion). A plain `Counter`/dict-sum naturally buckets it — the
  risk is a future refactor adding an "only known values" allowlist that would silently drop it.
  Step 2's test guards this explicitly.
- **No shipped wrapper emits `expansion_reason`/`expansion_count` today.** Any fixture exercising
  the expansion-rate view (Step 3) must be clearly synthetic; the function must return `0.0` (not
  crash, not a fabricated nonzero) when all events lack these fields — this is the actual real-world
  state as of this ticket.
- **`main()`'s `--days`/`--week` run_id-membership filter is not modified.** The new Retrieval
  Quality section will only ever populate under `generate_retro.py --all` — this is a deliberate,
  by-design consequence of the schema-emit ticket's run_id isolation, not a bug. Step 6's rendered
  caveat line makes this explicit to a human reading the report rather than leaving it silently
  undiscoverable.
- **`compute_retrieval_metrics()` remains a single extended function, not split into siblings.**
  All four new signals (Steps 1-3, plus the already-shipped cache rates) live in the same function's
  return dict — this keeps the read-only architecture guard (Step 5) targeting one function's
  source, consistent with the sibling ticket's own precedent, and avoids introducing a second
  pure-function entry point that `generate()` would need to call and thread through separately.
- **`fmt_pct` reuse in Step 6:** check its existing signature/behavior before reusing for
  `expansion_rate` — if it expects `(count, total)` rather than a pre-computed float ratio, either
  pass `expansion_rate`-supporting numerator/denominator through instead of the final ratio, or use
  a local one-line percentage format — do not modify `fmt_pct` itself to accommodate this new call
  site.

## Deviations

**Revision 1 (architecture-review NEEDS_CHANGES round):** an architecture-reviewer pass on the
original Step 8 draft returned NEEDS_CHANGES, finding the draft `INFRA-298` entry omitted
`legacy_evidence`, `proof_type`, and `support_boundary` — all three present on every sibling entry
(INFRA-293 through INFRA-297) — contradicting the plan's own instruction to "copy [the preceding
entry's] shape verbatim." Fixed by rewriting Step 8's draft entry to match INFRA-297's real shape
field-for-field (reading `docs/parity_ledger/infrastructure.yaml`'s actual INFRA-297 entry
directly, not re-deriving the shape from memory). All other steps (1-7), the Resolved Decisions
(1-5), Scope Guards, Dependency Map, Acceptance Criteria Map, and Anti-Drift Notes are unchanged
from the original plan — this was a narrowly-scoped fix to Step 8 only.
