---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-SHADOW-BASELINE-COMPARISON
artifact_type: investigation
tags: [retro, agent-monitoring, observability]
---

# Investigation — TCK-20260729-SHADOW-BASELINE-COMPARISON

## Current Behavior

### `tools/agent-monitoring/generate_retro.py::compute_retrieval_metrics()` (lines 574-679)

Pure, read-only function. Filters `events` to `retrieval_events = [e for e in events if
"retrieval_event_schema_version" in e]` (line 587) — this is the sole discriminator for
"retrieval-shaped" vs. ordinary workflow events; it does **not** look at `run_id` at all. It then
computes, over that undifferentiated retrieval-event population:

- `cache_rates` (grouped by `cache_level`, hit/miss/stale-rejected counts+rates) — lines 589-606
- `candidate_to_selected_ratios` / `selected_to_cited_ratios` (per-event, `{run_id, seq, ratio}`
  rows) plus their aggregates — lines 608-653
- `authority_distribution` / `freshness_distribution` (Counters, updated from each event's
  `authority_counts`/`freshness_counts`) — lines 636-642
- `expansion_rate` — unconditional fraction of retrieval events carrying
  `expansion_reason`/`expansion_count` — lines 655-667

Returns one flat dict (line 669-679: `retrieval_event_count`, `cache_rates`,
`candidate_to_selected_ratios`, `selected_to_cited_ratios`, `candidate_to_selected_aggregate`,
`selected_to_cited_aggregate`, `authority_distribution`, `freshness_distribution`,
`expansion_rate`). **Nothing in this function partitions by real-vs-synthetic `run_id`** — every
matching event, regardless of provenance, is folded into one combined population. This is exactly
the gap this ticket's Scope requires filling: a new function that reuses this same measurement
domain but computed separately for the two cohorts.

### `compute_retro_metrics()` (line 322) and `generate()` (line 682)

`generate()` (line 682-982) calls `compute_retro_metrics(runs, events, tickets_root)` (line 688,
the run/tier/tag/spend-proxy domain) and, separately, `compute_retrieval_metrics(events)` (line
689, the retrieval-quality domain) — both pure computations, no shared state. `generate()` then
renders both to one Markdown `lines` list. The **existing conditional-render pattern** this ticket
must mirror is at lines 897-972 (`## Retrieval Quality`): `if
retrieval_metrics["retrieval_event_count"]:` (line 901) gates the entire section — when zero
retrieval-shaped events exist, no heading, no "no data" placeholder, nothing at all is appended
for that section (contrast with the Cache Rates / Freshness / Authority sub-tables *inside* that
gated section, which do render an explicit `_No … this period._` placeholder line at lines 925,
955, 966 — that finer-grained pattern is for populated-but-empty-subgroup cases, not the
zero-events gate this ticket's AC actually asks for). The three other sections using the same
top-level gate style are Reason Codes (line 734), Tag Breakdown — Subsystem/Topic (line 746), and
Tag Breakdown — Process/Skill-signal (line 757).

### `tools/retrieval_events.py` — event shape and provenance signal

`RETRIEVAL_EVENT_FIELDS` (lines 52-73, 17 members, frozen) plus `emit_retrieval_event()`'s 7 base
fields (`run_id, seq, ts, phase, agent, summary, status`) define the full event shape.
`wrap_context_packet_assembly()` (lines 264-308) is the one wrapper this ticket's dependency
(`TCK-20260729-SHADOW-PACKET-CALL-SITE`, now DONE) wired into `implement-ticket.js`'s Investigate
phase: it hardcodes `phase="Retrieval"` (line 295) and `agent=AGENT_PACKET` =
`"context-packet-wrapper"` (line 261, 296), and now receives the real ticket's `tid` as `run_id`
(confirmed live in `.claude/workflows/implement-ticket.js`'s Investigate phase and in
`tests/tools/test_shadow_packet_call_site.py`'s fixtures) instead of falling back to its default
`RUN_ID_PACKET = "RETRIEVAL-EVENT-context-packet"` (line 260). `seq` for these shadow rows is
`<= 0` (a monotonic negative counter, `seq = -(1 + prior_shadow_count_for_this_run_id)`,
confirmed in `tests/tools/test_shadow_packet_call_site.py:263-267`'s `_compute_shadow_seq()`
helper and the behavioral test at line 288) — disjoint from every real per-phase `seq` (`>= 1`),
but this is a `seq`-disjointness property, not itself the run_id-provenance partition key this
ticket needs.

### `tools/agent-monitoring/vocabulary.py::infer_workflow()` (line 73) — the actual partition mechanism

`infer_workflow(run_id)` (lines 73-94) checks four disjoint, confirmed-by-grep prefixes in order:
`"SIMQ-AUDIT-"` → `"simq-audit"`, `"EPIC-"`/`"FOLDER-"` → `"implement-epic"`,
`"CREATE-TICKETS-"` → `"create-tickets"`, `"TCK-"` → `"implement-ticket"`; **returns `None` if no
prefix matches** (line 94), and the module's docstring on that return value is explicit: "callers
must treat `None` as 'skip the check silently.'" This is directly reusable as the real-vs-synthetic
partition test: `wrap_hybrid_retrieval()`'s `RUN_ID_HYBRID = "RETRIEVAL-EVENT-hybrid-retrieval"`
(line 142), `wrap_retrieval_cache_check()`'s `RUN_ID_CACHE = "RETRIEVAL-EVENT-retrieval-cache"`
(line 196), and `wrap_context_packet_assembly()`'s default `RUN_ID_PACKET =
"RETRIEVAL-EVENT-context-packet"` (line 260) all start with the literal `"RETRIEVAL-EVENT-"`
prefix — none of which matches any of `infer_workflow()`'s four recognized prefixes, so
`infer_workflow()` returns `None` for every synthetic standalone-invocation run_id, and returns
`"implement-ticket"` (non-`None`) for exactly the real `TCK-...`-prefixed shadow rows this
ticket's dependency ticket now emits. **This exact non-`None`-vs-`None` check is already the
established idiom in this file**: `_normalize_phase()` (line 183-194) and `_normalize_agent()`
(line 197+) both branch on `if workflow is None: return <unchanged>` immediately after calling
`infer_workflow()`.

### `tools/agent-monitoring/retrieval_baseline_metrics.py` — confirmed wrong extension point

Read in full (201 lines). It is a **structurally distinct domain and distinct output shape**:
`build_baseline_report()` (line 170) composes `context_tokens` (marked `"unavailable"`),
`search_count` (per-run follow-up-search tool-call counts from `tools.jsonl`, filtered to
`SEARCH_TOOL_NAMES = {mcp__knowledge-search__search_docs, ToolSearch, WebSearch}`), `duration`
(flagged `"pause-contaminated"`), `gate_outcome` (status breakdown / gate-fail / terminal-success
counts from `runs.jsonl`), `review_rework` (multi-record-per-run_id NEEDS_CHANGES/BLOCKED→DONE
transition proxy), and `legacy_schema_notes`. None of these six sections touch cache
hit/miss/stale-rejected rates, candidate/selected/cited ratios, or
authority/freshness/expansion-rate — the retrieval-quality domain `compute_retrieval_metrics()`
owns. It prints one JSON report to stdout (`main()`, line 183) and is explicitly a "one-off
baseline snapshot... not part of [the] recurring weekly RETRO-* cadence" (module docstring, lines
2-12) — a different consumption model entirely from `generate()`'s Markdown-report rendering.
This confirms the ticket's Scope reasoning is sound: `compute_retrieval_metrics()` in
`generate_retro.py` is the correct, same-domain/same-file extension point, not
`retrieval_baseline_metrics.py`.

### Gap check — no file listed in Related Code Areas is missing

`tools/agent-monitoring/generate_retro.py`, `tools/agent-monitoring/retrieval_baseline_metrics.py`,
`tools/retrieval_events.py`, and `tests/tools/test_generate_retro.py` all exist and were read in
full or in the relevant sections. No gap.

## Mechanics / Engine Constraints

None. This ticket touches only `tools/agent-monitoring/generate_retro.py` (a Markdown-report
generator over agent-orchestration telemetry) and its test file. No `docs/mechanics/` chapter or
`docs/engine/` contract governs simulation state, formulas, or the 32-phase mutation pipeline —
same posture as this ticket's direct predecessors
(`TCK-20260729-RETRIEVAL-RETRO-VIEWS`, `TCK-20260729-SHADOW-PACKET-CALL-SITE`). No `src/` file is
in scope.

## Parity Ledger Overlap

**None — confirmed explicitly, as the ticket description anticipated.** Grepping
`docs/parity_ledger/*.yaml` for `shadow.baseline|shadow_packet|compute_retrieval_metrics|retrieval_events`
surfaces only the three directly-preceding entries already read in full:

- **INFRA-296** (`TCK-20260729-CONTEXT-PACKET-ASSEMBLY`) — status `verified`, `test_path:
  tests/tools/test_context_packet_assembler.py`. `support_boundary` states: "Agent-orchestration/
  retrieval tooling only — no simulation behavior, Mechanics Bible chapter, or engine contract
  governs this module's semantics" and its own updated note documents the now-live wiring from
  `TCK-20260729-SHADOW-PACKET-CALL-SITE`.
- **INFRA-297** (`TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT`) — status `verified`, `test_path:
  tests/tools/test_retrieval_events.py`. Same `support_boundary` posture, also updated to note the
  live wiring.
- **INFRA-299** (`TCK-20260729-SHADOW-PACKET-CALL-SITE`) — status `verified`, `test_path:
  tests/tools/test_shadow_packet_call_site.py`. `support_boundary`: "Agent-orchestration/retrieval
  tooling only... No `src/` file touched... Off by default... fully fail-open... advisory-only."

An INFRA-298 entry (`TCK-20260729-RETRIEVAL-RETRO-VIEWS`, which built
`compute_retrieval_metrics()` itself and wired it into `generate()`) exists at the same
`support_boundary` posture: "not wired into any real-time workflow orchestrator file or existing
pipeline/gate — real retrieval-event volume in the live `agent-monitoring/events.jsonl` stays at
zero after this ticket ships, by design." That statement is now stale for the
`context-packet-wrapper` sub-population specifically (per INFRA-299's shipped wiring), but
INFRA-298 itself was not asked to be updated by this ticket's investigation — flagged below as an
open question for Plan/Parity, since this ticket's own new function inherits the same
"agent-orchestration tooling, no `src/` touch" category and will need its own new INFRA-30x-style
entry, not a correction to INFRA-298.

No P0 parity entry is implicated (INFRA-296/297/298/299 are all P1). No `test_path` obligation
beyond this ticket's own new tests is triggered. **A new parity ledger entry should be added**
(not strictly required by any P0 rule, but consistent with the unbroken INFRA-28x/29x
retrieval-tooling series convention every predecessor in this chain has followed) — left as an
open question for the Plan phase / parity-updater, not decided here.

## Prior Work

- **`TCK-20260729-RETRIEVAL-RETRO-VIEWS`** (done, INFRA-298) — built `compute_retrieval_metrics()`
  and its `generate()` conditional-render section. This ticket's new function must reuse
  `compute_retrieval_metrics()` itself (call it twice, once per cohort's filtered event list) —
  not reimplement any of its cache/ratio/distribution/expansion-rate logic, per the ticket's own
  Scope wording ("using compute_retrieval_metrics()'s measurement domain").
- **`TCK-20260718-RETRO-STATS-REFACTOR`** (done) — the cited "byte-identical-output-preserving
  extension pattern" precedent. Its Acceptance Criteria #3 required proving the refactor left
  `generate()`'s CLI output byte-identical via a `git stash`/before-after diff on the real corpus;
  Implementation Notes confirm this was executed and passed. This ticket's own AC ("Existing
  non-shadow report output remains byte-identical... on the same fixture inputs") is the same
  proof obligation, scoped to fixture inputs instead of the live corpus (appropriate here since
  this ticket is purely additive — a new conditionally-rendered section — rather than a structural
  extraction).
- **`TCK-20260728-RETRIEVAL-BASELINE-METRICS`** (done) — confirmed (see Current Behavior above) to
  be a genuinely separate duration/outcome/token-stat JSON-report domain; its own test file
  (`tests/tools/test_retrieval_baseline_metrics.py`) establishes a reuse-not-reimplement guard
  pattern (`test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`,
  `test_baseline_report_tool_causes_zero_diff_on_real_corpus`) that is a useful structural template
  for this ticket's own "reuses `compute_retrieval_metrics()`, does not reimplement it" test, even
  though the module itself is not touched.
- **`tests/tools/test_generate_retro.py::TestComputeRetrievalMetrics`** (class at line ~1048) and
  its `_retrieval_event(**overrides)` fixture helper (line ~1033, defaults: `run_id:
  "RETRIEVAL-EVENT-test"`, `phase: "Retrieval"`, `agent: "retrieval-cache-wrapper"`,
  `retrieval_event_schema_version: 1`) — the exact fixture-construction idiom this ticket's new
  tests should reuse/extend (override `run_id` to a `"TCK-..."` value and `agent` to
  `"context-packet-wrapper"` to build a "shadow cohort" fixture row alongside the existing
  synthetic-cohort rows).
- **`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/
  idea_context_efficient_agent_retrieval_observability.md`** — "Evaluation and Decision
  Follow-Up" → "Shadow evaluation and approval gate" section (lines 245-266) is the source of the
  **six approval-gate criteria** this ticket's Out of Scope explicitly forbids surfacing in the
  new report section's text: (1) authoritative-source recall at least the agreed baseline; (2) no
  material increase in missed contracts/test-gate-failures/review rework; (3) a meaningful,
  pre-declared reduction in median injected context tokens or follow-up retrieval burden; (4)
  cache correctness (stale packets rejected, source-hash checks pass); (5) provider parity
  (comparable request/packet/outcome events for every enabled provider); (6) privacy boundary (no
  raw prompts/source text/sensitive payloads in monitoring). These are promotion-gate criteria for
  a *future* decision, not something this reporting-only ticket evaluates or renders judgments
  against — confirmed directly from the source doc, not inferred.
- **`tests/tools/test_shadow_packet_call_site.py`** (already implemented, 12 test functions) —
  confirms the exact live event shape this ticket's shadow cohort will see in production:
  `run_id` = a real `"TCK-..."` ticket id, `agent == "context-packet-wrapper"`, `phase ==
  "Retrieval"`, `seq <= 0` (its `_event()`/`_compute_shadow_seq()` helpers at lines ~260-267
  construct exactly this shape for its own seq-collision regression test).

## Risks and Open Questions

1. **Partition boundary: prefix-based, not `infer_workflow()`-based, is the safer choice for this
   ticket specifically (recommendation, not yet an implementation decision).**
   `vocabulary.infer_workflow()` classifies `"TCK-..."` as `"implement-ticket"` and every
   `"RETRIEVAL-EVENT-..."` synthetic run_id as `None` — a clean binary split today. But
   `infer_workflow()`'s docstring return-value contract is "which workflow produced this run_id,"
   not "is this a real vs. synthetic run_id" — a future 5th workflow's real run_ids would also
   return non-`None`, and would correctly still count as "real" for this ticket's purposes, so
   `workflow is not None` remains a **correct** superset test today, not merely a coincidence.
   However, using `infer_workflow()` directly also means this new function silently inherits any
   future change to that function's prefix list — acceptable, since that list only grows more
   workflows (never removes the `TCK-` case), but worth flagging so the implementer does not
   instead invent a second, parallel `run_id.startswith("TCK-")` check that could drift from
   `infer_workflow()`'s own list. **Recommendation: call `infer_workflow(run_id) is not None` as
   the partition predicate**, reusing the existing single-source-of-truth function rather than
   re-literaling `"TCK-"`/`"RETRIEVAL-EVENT-"` prefixes a second time in this new function.
2. **Does the new function need its own parity ledger entry, or does it stay under INFRA-298's
   umbrella?** INFRA-298 already covers `compute_retrieval_metrics()`/the `## Retrieval Quality`
   section as "not wired into any real-time workflow orchestrator" — a claim INFRA-299 already
   partially superseded for the underlying event-emission side. This ticket's new function is a
   *pure consumer* of already-verified event data (no new emission, no new wiring), which argues
   for treating it as a natural extension of INFRA-298 the same way INFRA-296/297 were corrected
   in-place rather than superseded by a new entry — but the established convention in this chain
   (INFRA-296 through INFRA-299, one entry per ticket) argues for a new INFRA-30x entry instead.
   Left open for Plan/parity-updater; not a scope-blocking question, since either resolution is a
   pure documentation choice with no code-path implication.
3. **Zero live shadow data exists at investigation time.** `SHADOW_CONTEXT_PACKET_ENABLED`
   defaults to off (confirmed: `stored_artifacts/TCK-20260729-SHADOW-PACKET-CALL-SITE/plan.md`'s
   shell guard `if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]`), so the real
   `agent-monitoring/events.jsonl` corpus almost certainly contains zero `"TCK-..."`-run_id,
   `agent == "context-packet-wrapper"` rows today. This ticket's AC "fixture-only tests... no
   live-data dependency" already anticipates this and is the correct scoping — the new function
   must be provably correct against synthetic fixtures, not validated against the live corpus
   (which cannot yet exercise the nonzero-shadow-events branch).
4. **Naming collision risk between this ticket's "shadow cohort" and the existing "shadow
   evaluation" terminology in the idea doc.** The idea doc's "Shadow evaluation and approval
   gate" section is a distinct, larger, not-yet-built concept (comparing packets/outcomes against
   a *baseline period*, with the six-criteria promotion gate). This ticket's own Out of Scope
   correctly disclaims building that: "No scorecard or comparison against the six approval-gate
   criteria." The new function's naming (whatever the Plan phase chooses) should avoid implying it
   *is* that approval-gate mechanism — it is a narrower, purely descriptive real-vs-synthetic
   comparison of the same measurement domain, nothing more.

None of these open questions block understanding scope — #1 and #2 are concrete Plan-phase
choices; #3 and #4 are confirmations, not blockers.

## Anti-Drift Hazards

- **Do not** compute recall, "material increase in missed contracts/test-gate-failures/review
  rework," a "meaningful, pre-declared reduction in tokens," cache correctness against a
  stale-rejection standard, provider parity, or a privacy-boundary check — none of these six
  approval-gate criteria (see Prior Work) may be computed or their phrasing echoed anywhere in the
  new function's output text; this is a directly testable Acceptance Criterion via a phrase-absence
  grep over the generated report.
- **Do not** modify `retrieval_baseline_metrics.py` — confirmed (Current Behavior above) to be the
  wrong extension point; the ticket's Out of Scope forbids touching its JSON report format.
- **Do not** reimplement any of `compute_retrieval_metrics()`'s cache-rate/ratio/distribution/
  expansion-rate logic inline in the new function — call `compute_retrieval_metrics()` itself
  (twice, once per filtered cohort's event list), matching the ticket's own Scope wording.
- **Do not** change `compute_retrieval_metrics()`'s existing signature, return shape, or any of its
  literals (`RETRIEVAL_EVENT_FIELDS`, `HIT`/`MISS`/`STALE_REJECTED`, `UNRATED`,
  `INDEX_CACHE_CATEGORY`/`QUERY_CACHE_CATEGORY`/`PACKET_CACHE_CATEGORY`) — several existing tests
  (`test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants`,
  `test_function_is_read_only_no_write_call_or_file_open_in_write_mode`) assert against its exact
  current source; any edit to that function itself risks breaking them for no reason, since this
  ticket only needs to *call* it, not modify it.
- **Do not** alter the existing `## Retrieval Quality` section's gating condition
  (`if retrieval_metrics["retrieval_event_count"]:`, line 901) or its rendered content — the new
  shadow-comparison section must be a wholly separate, additively-appended block with its own
  independent zero-events gate, per the ticket's own explicit AC ("Existing non-shadow report
  output remains byte-identical").
- **Do not** introduce a second, parallel `run_id.startswith(...)` literal for the
  real/synthetic partition — reuse `vocabulary.infer_workflow()` (already imported into
  `generate_retro.py` at line 35) as the single source of truth, per Risk #1 above.
- **Do not** let the new section render when the shadow (real-run-id) cohort is empty, even if the
  synthetic cohort is nonzero — the ticket's AC specifically conditions on "zero shadow
  (real-run-id) events," not "zero retrieval events of any kind." Conflating the two would make the
  new section appear even when there is nothing shadow-specific to report, drifting from the
  literal AC wording.
- **Do not** write fixture tests that depend on the real `agent-monitoring/events.jsonl` corpus —
  the AC is explicit ("fixture-only... no live-data dependency"); this differs from
  `test_retrieval_baseline_metrics.py`'s own zero-mutation test, which *does* read the real corpus
  read-only — that pattern is not the one to copy here.
