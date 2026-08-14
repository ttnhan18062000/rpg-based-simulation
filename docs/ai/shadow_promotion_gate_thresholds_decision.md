---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, agent-monitoring]
---

# Shadow-Evaluation Promotion Gate Thresholds Decision — TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS

Resolves **Open Decision 5** from
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
(tracked by epic `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`):

> What sample size and thresholds are sufficient to promote a scenario from advisory to default
> behavior?

This document **decides and evidences**. It implements nothing — no promotion, no gate
PASS/FAIL/BLOCKED logic, and no live shadow evaluation is created or run as part of landing it.
Every numeric anchor below is either (a) a real, freshly-computed field from
`tools/agent-monitoring/retrieval_baseline_metrics.py`'s output (re-run on 2026-07-30 against the
live `agent-monitoring/*.jsonl` corpus: 721 `runs.jsonl` records, 3831 `events.jsonl` records, 122
distinct run_ids with at least one qualifying search, `search_count.total = 1738`), (b) a real
figure already recorded in a prior Phase-2 decision doc this one builds on, or (c) an explicit,
labeled policy choice made in the deliberate absence of real shadow data — never an unattributed
round number presented as if it were measured.

---

## 1. What the idea doc's approval gate proposed

The idea doc's "Shadow evaluation and approval gate" section states, verbatim:

> Promotion from advisory to default workflow behavior requires a recorded review
> showing all of the following for the selected scenarios:
>
> - authoritative-source recall is at least the agreed baseline;
> - no material increase in missed contracts, test/gate failures, or review
>   rework attributable to missing context;
> - a meaningful, pre-declared reduction in median injected context tokens or
>   follow-up retrieval burden;
> - cache correctness: stale packets are rejected and source-hash checks pass;
> - provider parity: comparable request/packet/outcome events are emitted for
>   every enabled provider; and
> - privacy boundary: monitoring contains no raw prompts, raw retrieved source
>   text, or sensitive tool payloads.
>
> The numeric thresholds, sample size, and attribution method are deliberately
> open decisions for discovery. They must be selected before shadow evaluation,
> not retrofitted after results are known.

This decision resolves exactly the three things that closing paragraph names as open: numeric
thresholds (§2), sample size (§3), and attribution method (§4) — plus the explicit pre-declaration
required of a gate selected before any real evaluation exists (§5).

**"Selected scenarios" is not "all scenarios."** Only 3 of the idea doc's 5 named scenarios are
even eligible to enter this gate at all: `docs/ai/default_packet_scenarios_decision.md` (Open
Decision 1) found **Small bugfix**, **Ticket implementation**, and **Architecture-planning**
justify a default packet today; **Code review** and **Incident-monitoring investigation** remain
deferred pending phase-scoped aggregation tooling that does not exist. This document's thresholds
therefore apply only to the 3 already-justified scenarios — extending this gate to the 2 deferred
scenarios is out of scope here and blocked on Open Decision 1's own stated prerequisite, not this
ticket's.

---

## 2. Per-Criterion Threshold Table

| # | Criterion (verbatim) | Falsifiable bar | A priori defensible? |
|---|---|---|---|
| 1 | authoritative-source recall is at least the agreed baseline | The "agreed baseline" is `tools/eval_search.py`'s existing Recall@5 gate: **threshold 0.80**, currently measuring **0.67** on the 61-query fixture set (`tools/eval/queries.json`, repaired by `TCK-20260728-EVAL-FIXTURE-REPAIR`). No shadow-eligible scenario's packet-level recall may fall below whatever `eval_search.py` measures for its scenario-relevant query categories at promotion-review time. | **No — flagged in §6.** `eval_search.py` measures index-level recall against fixture queries; nothing joins a real shadow packet's `cited_source_hashes`/`selected_count` (from `compute_retrieval_metrics()`) to `queries.json`'s `expected_doc_ids` at emission time. |
| 2 | no material increase in missed contracts, test/gate failures, or review rework attributable to missing context | Baseline (fresh 2026-07-30 run): `gate_outcome.gate_fail_count = 74` of 721 runs (10.26%); `review_rework.count = 4` of 721 (0.55%), per `retrieval_baseline_metrics.py`'s `build_gate_outcome_section`/`build_review_rework_section`. Bar: for the shadow-enabled cohort of a given scenario, the same two rates computed over that cohort must not exceed the baseline rate by more than **+1 percentage point** each (≤11.26% gate-fail, ≤1.55% rework). | Numeric bar is possible; the **+1pp margin itself is a deliberate policy choice**, not a statistically derived figure (no variance/effect-size field exists to derive one) — stated plainly, not disguised as measured. |
| 3 | a meaningful, pre-declared reduction in median injected context tokens or follow-up retrieval burden | `context_tokens` is confirmed platform-unavailable (`build_context_tokens_section()`'s own `"status": "unavailable"`, matching `docs/agent-monitoring/schema.md`'s "What is not recorded" section). Proxy: `search_count.per_run`, corpus-wide median currently **3** (n=122). Bar: shadow-cohort median `search_count.per_run` for a scenario must be **at least 1 whole search lower** than the baseline-cohort's contemporaneous median for that same scenario — a full integer unit, not a fractional/noise-level delta, since `search_count.per_run` is integer-valued by construction. | Numeric bar possible today as a proxy; genuinely cannot cite a token figure (see intro). |
| 4 | cache correctness: stale packets are rejected and source-hash checks pass | Zero tolerance. Any single cache `HIT` served for content whose `source_hash` does not match (i.e., any `STALE_REJECTED`-eligible case not rejected), or any regression in the existing 25 tests in `tests/tools/test_retrieval_cache.py`, fails this criterion outright. Not a percentage — a correctness invariant. | Yes — fully defensible today; this is a deterministic code-correctness property already tested, not a statistical one requiring live shadow volume. |
| 5 | provider parity: comparable request/packet/outcome events are emitted for every enabled provider | `tools/retrieval_event_parity_check.py`'s existing structural check (zero provider-specific/execution-identity field names in `RETRIEVAL_EVENT_FIELDS`) must continue passing — that much is enforceable today. | **No — flagged in §6.** Of the two known provider adapters (`codex`, `claude`/`claude-code`, per `retrieval_event_parity_check.py`'s `_KNOWN_PROVIDER_TOKENS`), only `claude-code` has ever produced a real workflow event; Codex has no live pilot (`TCK-20260729-SHADOW-PACKET-CALL-SITE`'s Out-of-Scope: "No live Codex pilot"). "Comparable events emitted for every enabled provider" cannot be measured against live data when only one provider is live. |
| 6 | privacy boundary: monitoring contains no raw prompts, raw retrieved source text, or sensitive tool payloads | Zero tolerance, grounded in `docs/observability/retrieval_retention_redaction_policy.md`'s already-enumerated MAY/PROHIBITED field list (Open Decision 4). Any single occurrence of a PROHIBITED field or content shape in `agent-monitoring/*.jsonl` fails the gate. | Yes — fully defensible today; the enumerated list already exists and is checkable by direct field-shape inspection, independent of shadow-packet volume. |

---

## 3. Sample Size

Grounded in `retrieval_baseline_metrics.py`'s real `search_count.per_run` distribution and
`compute_shadow_baseline_comparison()`'s cohort-partition structure — not an invented round number.

### 3.1 Per-scenario floor, each citing the same real evidence Decision 1 used for that scenario

| Scenario | Shadow-enabled run-count floor | Grounding |
|---|---|---|
| Small bugfix | **≥ 56** | Matches today's real ≤2-search-count cluster: 56 of 122 search-active run_ids (45.9%), the same cluster `docs/ai/default_packet_scenarios_decision.md` cited (53 of 118, 45%, as of 2026-07-29) to justify this scenario's baseline in the first place. Requiring a shadow-enabled sample of the same order as the sample that already characterizes the scenario's baseline is the minimum needed to compare like with like. |
| Ticket implementation | **≥ 122** | Matches the full search-active population size (n=122) `retrieval_baseline_metrics.py` needed to compute this scenario's baseline median (`search_count.per_run` = 3) in the first place — this is the modal scenario (`DONE: 622` of 721, ~86%), so its promotion review is held to the same population size that already grounds the number it must beat. |
| Architecture-planning | **≥ 6** | Matches the count of named outlier tickets (`TCK-20260614-WORLDMOD-PARAMS`, `TCK-20260623-FIX-WORLDASSEMBLY`, `TCK-20260630-SIMQ-WIRE-KERNEL`, `TCK-20260619-E41A-GROUP-LIFECYCLE`, `TCK-20260626-FIX-DESIGN-PATTERNS`, `TCK-20260628-E-LONGRUN-REGRESSION`) that constituted this scenario's entire evidentiary basis in Decision 1 — confirmed still the same 6 in the fresh 2026-07-30 top-outlier list.

### 3.2 Elapsed-period floor

No promotion review may be convened before **at least one full agent-monitoring-retro cadence
cycle** has elapsed for the scenario under review — the repo's own existing cadence rule (weekly,
or after 5+ completed tickets, whichever comes first, per the `agent-monitoring-retro` skill and
`CLAUDE.md`'s cadence rule), applied to the shadow-eligible scenario's own completed-ticket count
rather than the whole corpus's. This reuses an existing, already-adopted repo convention for
"how much evidence is enough before revisiting a decision" rather than inventing a new one.

The **binding floor is whichever of §3.1's run-count and §3.2's elapsed-period is reached later**
for the scenario in question — a scenario that reaches its run-count floor in three days still
waits out one retro cycle; a slow-moving scenario that takes two months to reach its run-count
floor is not reviewed early just because a retro cycle passed.

### 3.3 A structural caveat on `compute_shadow_baseline_comparison()`

`generate_retro.py`'s `compute_shadow_baseline_comparison()` partitions `events.jsonl` into a
`"shadow"` cohort (`infer_workflow(run_id) is not None` — i.e. events whose `run_id` matches a
known **real** workflow prefix: `TCK-`, `EPIC-`/`FOLDER-`, `CREATE-TICKETS-`, `SIMQ-AUDIT-`) versus
a `"baseline"` cohort (`run_id` matches none of those — which today catches Phase 4's synthetic
`RETRIEVAL-EVENT-*` test fixtures, not a real "shadow-packet-enabled" population). Despite its
name, this function's existing partition is **real-vs-synthetic run_id provenance**, built for
Phase 4's schema-emission tests — it is **not**, as currently written, a shadow-packet-enabled-vs-
not comparison. Any future tool computing the sample-size floors in §3.1 for real data must
partition on a different key: presence of a shadow-packet event for that `run_id` (per
`TCK-20260729-SHADOW-PACKET-CALL-SITE`'s monotonic-negative-`seq` scheme, `seq <= 0`) — not
`infer_workflow(run_id) is not None`. This gap is stated here rather than silently assumed away;
building that join is part of the genuine tooling gap in §4.

---

## 4. Attribution Method

**No existing Phase 0-5 tool computes causal attribution between an outcome and missing/present
context today.** This is a genuine gap, not an oversight to be papered over:

- `reason_code` (per `docs/agent-monitoring/schema.md`) is populated **only** for
  `Scope`/`ticket-scoper` and `Verify`/`done-checker` `failed` events — it is `null` for every
  `Review`/`Architecture-Verify` event, which is exactly where `NEEDS_CHANGES`/`BLOCKED` (the
  statuses `retrieval_baseline_metrics.py`'s `REWORK_TRIGGER_STATUSES` already targets for review
  rework) are recorded. There is no structured, closed taxonomy distinguishing "gate failed because
  of missing context" from any other gate-failure cause at the exact phase this criterion cares
  about.
- No function anywhere in `retrieval_baseline_metrics.py`, `generate_retro.py`, or
  `retrieval_events.py` joins a shadow-packet event's `included_candidates`/`cited_source_hashes`
  to a later gate-fail/rework/test-failure event for the same `run_id`.

### Proposed method (to be built — not a description of anything that exists)

1. **Join key: `run_id`.** For each `run_id` with at least one real shadow-packet event
   (`retrieval_event_schema_version` present, `seq <= 0` per the negative-seq convention), collect
   the event's `included_candidates` and `cited_source_hashes`.
2. **Outcome side.** For the same `run_id`, take its terminal outcome via `_resolve_status` —
   whether it is a gate fail (`_is_gate_fail`), review rework (`REWORK_TRIGGER_STATUSES`), or a
   `TESTS_FAILED` record.
3. **Candidate attribution test.** If the outcome's recorded review/failure reason names a specific
   doc, contract, or test file, check whether that file's content-hash appears in step 1's
   `cited_source_hashes`/`included_candidates`. Absence is *consistent with* "missing context
   contributed to this outcome" — presence rules it out for that specific artifact.
4. **This cannot be automated yet, and must not be presented as if it were.** Step 3's "recorded
   review/failure reason" is today a free-text `reason` string on `Review`/`Architecture-Verify`
   events (no structured field), and per this repo's own Durable State Rule, durable meaning must
   never live in a `reason` string. Until a structured, closed-vocabulary field for
   review/gate-failure cause exists, step 3 requires a **human-reviewed audit**: an analyst reads
   each shadow-cohort gate-fail/rework case in the sample window and manually tags it
   "missing-context-attributable" or "other," rather than an automated classifier inferring it from
   free text. This is stated as a real, current limitation of the proposed method, not a permanent
   design choice — a follow-up ticket adding a structured gate-failure-cause field to
   `Review`/`Architecture-Verify` events would be a prerequisite to automating step 3.

---

## 5. Zero Real Shadow-Packet Production Events Exist As Of This Decision

Confirmed directly: `agent-monitoring/events.jsonl` (4064 lines as of 2026-07-30) contains **zero**
records carrying the `retrieval_event_schema_version` key that `compute_retrieval_metrics()` uses
to identify a retrieval event. Independently confirmed via `compute_shadow_baseline_comparison()`:
both its `"shadow"` and `"baseline"` cohorts report `retrieval_event_count: 0` against the live
corpus. `SHADOW_CONTEXT_PACKET_ENABLED` remains off by default in `.claude/workflows/
implement-ticket.js` (strict `"$SHADOW_CONTEXT_PACKET_ENABLED" = "1"` shell-side gate,
`TCK-20260729-SHADOW-PACKET-CALL-SITE`) and has not been enabled in any environment
(`TCK-20260729-SHADOW-BASELINE-COMPARISON`'s own investigation confirms the same).

This is stated as a **feature of this decision's process, not an apology.** The idea doc's own
closing instruction for this exact gate is: "the numeric thresholds, sample size, and attribution
method ... must be selected before shadow evaluation, not retrofitted after results are known."
Every threshold in §2, every sample-size floor in §3, and the attribution method in §4 was
necessarily written with zero real shadow-packet evidence in hand — that absence is the entire
point of resolving this decision now, before `SHADOW_CONTEXT_PACKET_ENABLED` is ever turned on
anywhere. Recalibrating any of these numbers *after* real shadow data starts flowing, in response
to what that data shows, would be exactly the retrofitting the idea doc prohibits; recalibrating
in response to a newly-discovered tooling gap (e.g., §3.3's partition-key correction, or a
structured gate-failure-cause field landing) is not the same thing and remains legitimate.

---

## 6. Risks / Open Questions — Criteria Not Defensible A Priori

Two of the six criteria (§2, rows 1 and 5) do **not** have a fully defensible a priori numeric
answer, and are stated here as open risk rather than forced into a false-precision number:

- **Authoritative-source recall (criterion 1).** `eval_search.py`'s existing 0.80 Recall@5 gate
  (currently measuring 0.67) is the closest real, already-adopted "recall" concept in this repo,
  but it measures index-level recall against `queries.json`'s fixture queries — it has no join to
  a real shadow packet's actual `cited_source_hashes` at emission time. Until that join exists, this
  criterion's bar is an analogy to a related real number, not a direct measurement of the thing the
  idea doc's criterion actually names. A future ticket building `join_shadow_outcomes_by_run_id()`-
  shaped tooling (§4) would need to extend it to also compute packet-level recall directly, at
  which point this bar should be re-derived from real shadow data rather than left as an analogy.
- **Provider parity (criterion 5).** Only one of the two known provider adapters (`claude-code`)
  has ever produced a real event; `codex` has no live pilot anywhere in this repo today. "Comparable
  request/packet/outcome events... for every enabled provider" is fundamentally a claim about
  *multiple* live providers' data, which does not exist yet — no amount of careful reasoning from
  today's single-provider corpus substitutes for that. This criterion cannot be promotion-ready
  until a second provider adapter goes live and produces comparable real events; it is listed here
  as a blocking prerequisite, not a number to hit.

Both gaps are consistent with `docs/ai/default_packet_scenarios_decision.md`'s own precedent of
deferring rather than inventing a proxy where the underlying data genuinely does not exist yet
(that document deferred the Code Review and Incident-monitoring-investigation scenarios for the
same reason: real inability to isolate the needed signal, not oversight).

---

## 7. Resolution

**Open Decision 5 is resolved.** For the 3 shadow-eligible scenarios (Small bugfix, Ticket
implementation, Architecture-planning), promotion from advisory to default behavior requires:

- All six approval-gate criteria's bars in §2 to hold, with criteria 1 (recall) and 5 (provider
  parity) explicitly carrying the a priori-defensibility caveat in §6 — a promotion review must
  treat those two as open risks to be re-examined against real data, not as pre-cleared checkboxes.
- The per-scenario sample-size floor in §3.1 (56 / 122 / 6 shadow-enabled runs respectively) AND
  the elapsed-period floor in §3.2 (one full agent-monitoring-retro cadence cycle), whichever is
  reached later.
- Any causal-attribution claim under criterion 2 to follow the human-reviewed audit method in §4,
  explicitly not an automated classifier, until a structured gate-failure-cause field is built.
- Confirmation, at review time, that §5's zero-events baseline has actually changed — i.e., real
  shadow-packet events exist for the scenario under review, not merely that `SHADOW_CONTEXT_PACKET_
  ENABLED` was toggled once.

`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Assumptions/Open Questions
section is updated to mark Open Decision 5 **RESOLVED**, mirroring the convention set by Open
Decisions 1-4, and pointing here.

Any future ticket that builds the real shadow-evaluation review (Phase 5/6 of the idea doc's
Sequenced Future Epic) should: (a) start from §2's per-criterion bars and §3's sample-size floors;
(b) build the §3.3 partition-key correction and the §4 join tooling before attempting to automate
any part of the review; and (c) treat §6's two flagged criteria as blocking prerequisites requiring
real multi-provider and packet-level-recall data, not as gaps to be silently waived.
