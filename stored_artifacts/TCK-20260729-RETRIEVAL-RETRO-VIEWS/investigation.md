---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-RETRO-VIEWS
artifact_type: investigation
tags: [observability, agent-monitoring, retro]
---

# Investigation — TCK-20260729-RETRIEVAL-RETRO-VIEWS

## Current Behavior

### `tools/retrieval_events.py` (the shipped field shape this ticket must read, not extend)

- `RETRIEVAL_EVENT_FIELDS` (retrieval_events.py:52-73) — 17 retrieval-specific fields confirmed
  exactly as briefed: `retrieval_version`, `corpus_generation`, `cache_level`, `cache_status`,
  `latency_ms`, `candidate_count`, `selected_count`, `source_kind_counts`, `authority_counts`,
  `freshness_counts`, `exclusion_reason_counts`, `cited_source_hashes`, `adequacy_verdict`,
  `expansion_reason`, `expansion_count`, `scenario`, `risk_tier`, plus
  `retrieval_event_schema_version` itself (18 counting that field — the module docstring calls
  the frozenset "17" and separately versions the record with `retrieval_event_schema_version`).
- `compute_adequacy_verdict(selected_count, candidate_count)` (retrieval_events.py:80-88) —
  exact 3-branch logic: `"insufficient"` if `selected_count == 0`; `"noisy"` if
  `candidate_count >= NOISY_RATIO_THRESHOLD * selected_count` (`NOISY_RATIO_THRESHOLD = 5`,
  line 77); `"sufficient"` otherwise. This is a placeholder heuristic, not a real quality model
  (module docstring, line 75-77).
- `expansion_reason`/`expansion_count` are documented as "present only if a follow-up expansion
  occurred" (schema.md:270) but **none of the 3 shipped `wrap_*()` functions
  (`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, `wrap_context_packet_assembly`,
  lines 146-308) ever emit either field.** No caller in this repo populates them today — any
  fixture exercising the expansion-rate view is necessarily synthetic, there is no real-code path
  to observe.

### `tools/agent-monitoring/generate_retro.py::compute_retrieval_metrics()` (generate_retro.py:561-617) — the exact gap

This is the function the sibling ticket TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT already shipped
to satisfy its own AC7 ("prove the new schema is queryable end-to-end"), **explicitly scoped in
its own docstring as "a minimal proof, not the full dashboard/retro views (those belong to the
sibling ticket TCK-20260729-RETRIEVAL-RETRO-VIEWS)."** Reading its actual body:

1. Filters `events` to those carrying `"retrieval_event_schema_version"` (line 573) — ordinary
   workflow events pass through unaffected.
2. **`cache_rates`** (lines 575-592): groups by `cache_level`, tallies `cache_status` via
   `Counter`, returns `{counts, total, rates}` per level, `rates` = `count / total` per status.
   **This already fully covers the AC1 signal** ("hit/miss/stale-rejection rates by cache
   level") — confirmed by the sibling ticket's own test
   `test_cache_hit_miss_stale_rejected_rates_grouped_by_cache_level`
   (test_generate_retro.py:1065-1082). Nothing to add here except surfacing it in the rendered
   report (see Gap 4 below).
3. **`candidate_to_selected_ratios`** / **`selected_to_cited_ratios`** (lines 594-610): a flat
   **per-event** list of `{run_id, seq, ratio}` dicts, zero-division-guarded at the single-event
   level (`ratio = None` when the denominator is 0 — confirmed by
   `test_candidate_to_selected_ratio_guards_zero_candidate_count`,
   `test_selected_to_cited_ratio_guards_zero_selected_count`). **This is genuinely narrower than
   the ticket's AC2 signal.** The AC text says "a zero-candidate **group** does not raise
   ZeroDivisionError" (group, singular concept implying an aggregation dimension, e.g. by
   `cache_level` or overall), but the shipped function has no grouping/aggregation at all — it is
   a raw per-event list, the kind of shape a dashboard would need to further reduce (sum/average)
   before it's a "ratio as noise indicator" view. **Genuinely missing: an aggregated
   candidate-to-selected / selected-to-cited view** (e.g. overall sum-of-selected /
   sum-of-candidates, or grouped by some caller-supplied dimension), not just the per-event list.
4. **Completely absent — freshness/authority distribution.** No code anywhere in
   `compute_retrieval_metrics()` reads `authority_counts` or `freshness_counts`. This is 100% new
   work.
5. **Completely absent — follow-up/expansion rate.** No code anywhere reads `adequacy_verdict`,
   `expansion_reason`, or `expansion_count`. This is 100% new work. The exact formula is
   ambiguous from the ticket text alone — see Risks/Open Questions.
6. **Not called by `generate()` at all.** `generate()` (line 620) calls only
   `compute_retro_metrics()` (line 626); `compute_retrieval_metrics()` has zero call sites in
   `generate_retro.py` outside its own tests. **There is no "## Retrieval ..." Markdown section in
   the retro report today** — the function exists and is unit-tested in isolation, but nothing
   renders it. Confirmed by grepping `generate()`'s body (lines 620-840): no reference to
   `compute_retrieval_metrics` or any retrieval-shaped key.
7. **A load-bearing wiring gap in `main()` that blocks this data from ever reaching the report
   under realistic invocation.** `main()`'s `--days`/`--week` branches (lines 858-871) filter
   `events` to `run_id in {r["run_id"] for r in runs}` — i.e., only events whose `run_id` matches
   a row in `runs.jsonl`. Retrieval events use the `RETRIEVAL-EVENT-<slug>` `run_id` prefix
   (retrieval_events.py:142,196,260), which **never** has a matching `runs.jsonl` row (by design —
   schema.md:288-291: "these `run_id`s have no matching `runs.jsonl` row ... naturally excluded
   from every existing run-scoped retro/dashboard view"). Only the `--all` branch (line 852-857)
   passes `all_events` through unfiltered. **Consequence: even after this ticket adds rendering,
   the new retrieval-quality section will only ever populate under `generate_retro.py --all`, never
   under `--days N` or `--week`.** This is intentional per the schema-emit ticket's own framing
   (retrieval events are deliberately outside the run-scoped join), but it is a real, undocumented-
   until-now constraint this ticket's Plan must decide whether to state explicitly in the rendered
   report (e.g. a note under the new section) or leave implicit.

### `tools/agent-monitoring/query.py` (query.py:1-166)

Zero retrieval-awareness of any kind — no `cache_level`/`cache_status`/`adequacy_verdict` filter
flag exists in `build_parser()` (lines 136-146) or `filter_events()` (lines 119-133). `open_index()`
(lines 29-36) hard `sys.exit(1)`s when `agent-monitoring-index/monitoring.db` is missing — directly
opposite of `generate_retro.py::_load_runs_and_events()`'s graceful on-demand-build-then-fallback
(generate_retro.py:53-87). Since real retrieval-event volume is (and will remain, per this ticket's
own Out of Scope) near-zero, and since `compute_retrieval_metrics()`'s existing home operates on a
plain `events: list[dict]` (no SQLite dependency at all — it's a pure function, confirmed by
`test_function_is_read_only_no_write_call_or_file_open_in_write_mode`), the path of least resistance
and highest consistency with the shipped precedent is to keep new aggregation functions in
`generate_retro.py` alongside `compute_retrieval_metrics()`. `query.py` remains a plausible home only
for new ad-hoc *filter flags* (e.g. `--cache-level`, `--adequacy-verdict`) mirroring its existing
per-field filter pattern (`filter_events()`), which is a materially different kind of feature
("browse individual matching events") than a "dashboard view" ("aggregate/summarize across events").
The ticket's own Scope allows either-or-both; Plan must pick explicitly per the ticket's own
Assumptions/Open Questions bullet.

### `tools/retrieval_cache.py` (retrieval_cache.py:56-62)

`HIT = "hit"`, `MISS = "miss"`, `STALE_REJECTED = "stale-rejected"` — confirmed importable
constants. `INDEX_CACHE_CATEGORY = "retrieval_index_cache"`, `QUERY_CACHE_CATEGORY =
"retrieval_query_cache"`, `PACKET_CACHE_CATEGORY = "retrieval_packet_cache"` (lines 56-58) — these
are the literal `cache_level` values that appear in real/fixture events (confirmed by
`wrap_retrieval_cache_check()`'s dispatch dict, retrieval_events.py:224-228). Any new view must
reuse these constants by import, never re-literal the strings — same anti-drift rule the schema-emit
ticket already enforced for `cache_status`.

### `tools/hybrid_retrieval.py` (hybrid_retrieval.py:41-45)

`UNRATED: str = "unrated"`, with an explicit assertion `UNRATED not in AUTHORITY_VALUES and
UNRATED not in STATUS_VALUES` (line 45) — proves `"unrated"` is a genuine third bucket, not a
member of the real authority/freshness enums. `wrap_hybrid_retrieval()` builds `authority_counts`/
`freshness_counts` via plain `Counter(r.authority for r in results)` (retrieval_events.py:170-171)
— `"unrated"` values flow into the `Counter` exactly like any other string. **No special-casing is
required to "handle" the sentinel correctly** (a plain `Counter`/groupby naturally buckets it) — the
risk is the opposite: a naive filter that only recognizes "known" authority/freshness values would
silently *drop* the `unrated` bucket. The new freshness/authority distribution view must count
`unrated` as a first-class bucket, never filter it out or crash on it.

### `tests/tools/test_generate_retro.py::TestComputeRetrievalMetrics` (lines 1048-1120)

Already covers, with passing tests today: non-retrieval-event skip-not-crash, mixed-fixture
counting, cache rate grouping by level, per-event candidate/selected and selected/cited ratio
computation plus their zero-guards, and a read-only/no-write architecture guard. **All of this is
prior work this ticket extends, not duplicates.** Uses an inline `_retrieval_event(**overrides)`
synthetic builder (lines 1033-1045), not a `tests/fixtures/agent_monitoring/*.jsonl` file — see Risks
below, this is a direct conflict with the ticket's own Scope wording.

### `tests/fixtures/agent_monitoring/PROVENANCE.md`

States, as a hard rule: every `.jsonl` file in that directory is "a byte-for-byte copy of exactly
one real line from `agent-monitoring/{runs,events,tools}.jsonl}`" — "Do not hand-edit any file in
this directory." **No real retrieval-event line exists in the live `agent-monitoring/events.jsonl`
to extract from** (confirmed: real retrieval-event volume is zero, per both this ticket's own
Assumptions and the schema-emit ticket's parity-ledger `support_boundary` note: "real
retrieval-event volume in the live `agent-monitoring/events.jsonl` stays at zero after this ticket
ships, by design"). See Risks/Open Questions — literal adherence to this convention is impossible
for retrieval-event fixtures.

## Mechanics / Engine Constraints

Not applicable. This ticket touches only `tools/agent-monitoring/generate_retro.py`/`query.py` and
reads (never modifies) `tools/retrieval_events.py`/`tools/retrieval_cache.py`/
`tools/hybrid_retrieval.py`. None of these are part of the simulation kernel, `docs/mechanics/`, or
`docs/engine/` — confirmed by the identical `support_boundary` language on every INFRA-28x/29x
entry in this batch ("Agent-orchestration/retrieval tooling only — no simulation behavior,
Mechanics Bible chapter, or engine contract governs this module's semantics").

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml`, all entries in this family `status: verified`,
`priority: P2` (no P0 in scope, so no pre-existing hard test-pass gate beyond the repo's general
regression discipline):

- **INFRA-297** (infrastructure.yaml:6174-6232) — `TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT`'s own
  entry. Its `v2_evidence` explicitly cites `generate_retro.py:561-612`
  (`compute_retrieval_metrics()`) and describes it as covering "cache hit/miss/stale-rejection
  rates grouped by `cache_level`, candidate-to-selected and selected-to-cited ratios, both
  zero-division guarded, non-retrieval events skipped not crashed on." **This entry's `v2_evidence`
  will become an incomplete description once this ticket extends or adds sibling functions to that
  same file** — it does not need correction (it accurately describes what shipped under that
  ticket), but a reader following it forward would miss the new freshness/authority + expansion-rate
  work. Recommend leaving INFRA-297 untouched (it correctly scopes itself to the schema-emit
  ticket's own AC7) and adding a **new** entry (next free ID, `INFRA-298`) for this ticket's
  work specifically — mirrors the established 1:1 ticket-to-ledger-entry pattern already used for
  INFRA-293 through INFRA-297 in this same batch.
- **INFRA-294/295/296** (`hybrid_retrieval.py`/`retrieval_cache.py`/`context_packet_assembler.py`)
  — reference-only for the field vocabulary (`HIT`/`MISS`/`STALE_REJECTED`, `UNRATED`,
  `INDEX_CACHE_CATEGORY` etc.) this ticket's new views must reuse verbatim; not themselves touched.
- No entry in `infrastructure.yaml` (or any other parity ledger file) currently describes a
  Markdown-rendered retro report section for retrieval quality — this ticket's new `INFRA-298`
  entry would be the first to do so.

## Prior Work

- **`stored_artifacts/TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT/`** (investigation.md, plan.md) —
  the direct predecessor. Its plan.md Step 9 explicitly scoped `compute_retrieval_metrics()` as
  "a minimal proof, not the full dashboard/retro views," Resolved Decision noting Step 9 is
  "independent of Steps 4-8," and its own Scope Guards state "full dashboard/retro views belong to
  the sibling ticket covering C3" — i.e., this ticket. Confirms the hard dependency stated in this
  ticket's own Assumptions is satisfied (schema-emit is DONE, `compute_retrieval_metrics()` exists
  and its field names match `RETRIEVAL_EVENT_FIELDS` exactly).
- **`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/
  ticket_plan_structure_phase4.md`** (lines 100-110) — the batch-scoping doc naming this ticket's
  exact deliverable: "new query functions extending `generate_retro.py`/`query.py` for the
  dashboard views the idea doc lists (cache hit/miss/stale rates, candidate-to-selected ratios,
  freshness/authority distribution)" plus "follow-up/expansion rate" from the fuller enumeration at
  lines 104-107. Confirms this ticket's AC signals are traceable to the source idea doc, not
  invented ad hoc.
- **TCK-20260718-RETRO-STATS-REFACTOR** — established the `compute_*_metrics()` (pure, dict-
  returning) + `generate()` (sole Markdown-rendering consumer) split this ticket must follow for
  any new retrieval view, per its own byte-identical-output-proof precedent
  (`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus`).
- **TCK-20260719-RETRO-OUTLIER-FLAGS** / **TCK-20260708-RETRO-TAG-BREAKDOWN** — both establish the
  exact "new dict key in `compute_retro_metrics()`'s return + new conditionally-rendered Markdown
  section in `generate()`, gated on `if metrics[...]:` being truthy" pattern this ticket's new
  sections should mirror (e.g. Outliers section at generate_retro.py:799-832, Tag Breakdown sections
  at 680-703).
- **TCK-20260728-RETRIEVAL-BASELINE-METRICS** — an earlier, unrelated read-only aggregation tool
  (`tools/agent-monitoring/retrieval_baseline_metrics.py`) over the *pre-existing* `runs.jsonl`/
  `events.jsonl`/`tools.jsonl` fields (duration, tool_call_count, etc.) — predates the retrieval-
  event schema entirely and does not read any `RETRIEVAL_EVENT_FIELDS` field. Related by name only;
  no code reuse opportunity beyond the shared "strictly read-only, mirrors manifest.py precedent"
  convention.
- **`tests/tools/test_query.py`** — establishes `query.py`'s test conventions (module loaded via
  `importlib.util.spec_from_file_location`, fixture DBs built through `build_index.py`'s real
  `_create_schema`/`_ingest_events`, architecture guards for "no direct JSONL reads" and "ORDER BY
  id"). If Plan decides any new retrieval filter flag belongs in `query.py`, these are the patterns
  to extend, not reinvent.

## Risks and Open Questions

1. **BLOCKING for Plan (not for this investigation): exact formula for "follow-up/expansion
   rate."** The ticket text ("follow-up/expansion rate as an initial-packet adequacy indicator")
   admits at least two readings: (a) unconditional — fraction of retrieval events carrying an
   `expansion_reason`/`expansion_count` at all; (b) conditional — of events whose
   `adequacy_verdict` is `"insufficient"` or `"noisy"`, what fraction actually got a follow-up
   expansion. Reading (b) is more literally "an adequacy indicator" (it measures whether a
   detected-inadequate packet was actually followed up), but neither shipped `wrap_*()` function
   ever emits `expansion_reason`/`expansion_count` today (confirmed above), so there is no real
   code path to validate either reading against, and the AC test must be entirely fixture-driven.
   Recommend Plan pick explicitly and document the formula inline (both are reasonable; do not
   silently guess one without a comment explaining the choice).
2. **Fixture convention conflict (non-blocking, but must be resolved explicitly, not silently).**
   `tests/fixtures/agent_monitoring/PROVENANCE.md` requires every fixture file be a byte-for-byte
   extraction from a real, live corpus line — but zero real retrieval-event lines exist to extract
   (by design, per both tickets' own framing). The shipped sibling ticket's own tests
   (`TestComputeRetrievalMetrics`) already deviated from this by using an inline synthetic
   `_retrieval_event(**overrides)` builder rather than a `.jsonl` fixture file, and that is the only
   available real precedent. This ticket's own Scope text ("following the
   `tests/fixtures/agent_monitoring/*.jsonl` convention") should be read as "in-repo, fixture-style,
   never validated only against live data" (the AC's own restated language) rather than literally
   requiring a new `.jsonl` file under that directory — recommend following the sibling ticket's
   established synthetic-builder pattern, not inventing a fabricated "real" `.jsonl` line. Flag this
   explicitly in plan.md so it isn't read as scope non-compliance.
3. **The `--days`/`--week` exclusion gap (documented above, "Current Behavior" item 7) means any
   new retrieval section in `generate()` is dead weight for the two most common invocation modes.**
   Plan must decide: (a) leave as-is and document the `--all`-only constraint inline in the
   rendered section (lowest risk, no behavior change to existing filtering), or (b) special-case
   retrieval events to bypass the run_id-membership filter in `--days`/`--week` too (higher risk —
   touches `main()`'s existing, well-tested filtering logic, and blurs the "run-scoped" framing the
   schema-emit ticket deliberately built to keep retrieval events out of real tickets' event
   streams). Recommend (a) — it's additive-only and consistent with the schema-emit ticket's
   explicit design intent that these events "do not corrupt or interleave into any existing
   run-scoped retro/dashboard view."
4. **The ticket's Out of Scope bullet ("any windowed aggregation must take an explicit cutoff
   argument, never an assumed default") only binds if a new function adds its own time-windowing.**
   Neither `compute_retrieval_metrics()` today nor any of the AC's 4 new views inherently need a
   cutoff (they operate over whatever `events` list they're handed, same as
   `compute_retro_metrics()`) — this constrains a hypothetical future addition, not something
   currently missing. No action needed unless Plan chooses to add a `--days`-equivalent for
   retrieval views specifically.
5. **Naming/placement is an open decision, not a gap.** The ticket's own Assumptions section
   already flags this ("query.py hard-fails ... generate_retro.py degrades gracefully ... planning
   must be explicit"). Investigation's recommendation (see "Current Behavior" `query.py` section
   above): keep aggregation/view functions in `generate_retro.py` beside
   `compute_retrieval_metrics()`; only add to `query.py` if Plan wants ad-hoc per-event filter flags
   (a materially different feature).

## Anti-Drift Hazards

- **Do not re-derive `cache_status`/`cache_level` string literals.** Always import
  `retrieval_cache.HIT`/`MISS`/`STALE_REJECTED` and
  `INDEX_CACHE_CATEGORY`/`QUERY_CACHE_CATEGORY`/`PACKET_CACHE_CATEGORY` — the schema-emit ticket
  already established this as a tested anti-drift guard (its Step 6 test
  `test_retrieval_cache_wrapper_emits_correct_cache_status_per_level`); a new view re-literaling
  `"hit"`/`"miss"` would silently diverge if those constants' values ever changed.
- **Do not modify `compute_retro_metrics()` or `generate()`'s existing rendered sections/ordering.**
  This ticket is purely additive — new dict keys in a retrieval-scoped computation, new
  conditionally-rendered Markdown section(s) appended in a new location, never touching the
  existing Run Summary/Gate Failure/Tag Breakdown/Tier Distribution/Outliers sections' logic or
  table shapes. `test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus`
  and `test_normalize_phase_agent_and_flag_outliers_untouched` (both in test_generate_retro.py) are
  hash/byte-identity guards that will catch accidental drift here.
- **Do not silently drop the `unrated` sentinel from freshness/authority distributions.** A naive
  "only count known values" filter would incorrectly exclude `hybrid_retrieval.UNRATED` results —
  the correct behavior is a plain `Counter`/groupby that treats `"unrated"` as an ordinary bucket
  value, per the "Current Behavior" section above.
- **Do not fabricate `expansion_reason`/`expansion_count` test data implying a real call site
  populates it.** No shipped wrapper emits either field today — any fixture exercising the
  expansion-rate view must be clearly synthetic/hypothetical, and the new function must handle the
  all-events-missing-these-fields case (0% rate, not a crash) since that is the actual current
  real-world state.
- **Do not add a new frontend/UI file.** Ticket's own AC6 forbids it explicitly; all new surface
  area is Python functions in `generate_retro.py`/`query.py` plus Markdown text in the existing
  retro report.
- **Do not touch `tests/tools/test_monitoring_writer_single_source.py`'s `_CALL_SITES` list or any
  writer/lock mechanism** — this ticket is entirely read-only aggregation/rendering, it has no
  legitimate reason to touch any write path at all (confirmed no write-path files are in Related
  Code Areas).
- **Do not assume `agent-monitoring-index/monitoring.db` has retrieval-event awareness.** Per the
  schema-emit ticket's own anti-drift note, the index stores `raw_json` verbatim — any new view
  reading through the index (if placed in `query.py`) must go through `json.loads(raw_json)`
  Python-side, never assume a dedicated SQL column for a retrieval field exists.
