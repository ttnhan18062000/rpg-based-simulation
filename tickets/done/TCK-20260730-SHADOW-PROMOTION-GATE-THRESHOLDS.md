---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS
phase: done
date: 2026-07-30
tags: [agent-monitoring, observability]
---

# TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS

## Title
Resolve Open Decision 5: sample size, thresholds, and attribution method for the shadow-evaluation promotion gate

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Produce a written, reviewable decision document — matching the shape and rigor of the epic's prior Phase 2 decision docs (docs/ai/default_packet_scenarios_decision.md, docs/ai/code_test_index_boundaries_decision.md) — that resolves Open Decision 5 from the context-efficient-retrieval idea doc: "What sample size and thresholds are sufficient to promote a scenario from advisory to default behavior?" The doc must attach a concrete, falsifiable numeric threshold or qualitative bar to each of the six approval-gate criteria; define a sample size grounded in real throughput characteristics drawn from retrieval_baseline_metrics.py / compute_shadow_baseline_comparison(); define an attribution method for causally linking outcomes to missing/present context; and explicitly acknowledge that zero real shadow-packet production events exist as of this decision, framing that absence as a process feature per the idea doc's own instruction. This is a decision-document deliverable only — no promotion, no gate logic change, no live evaluation, and no enabling of SHADOW_CONTEXT_PACKET_ENABLED in production.

## Scope
- Author a new docs/ai/*_decision.md doc (following the default_packet_scenarios_decision.md / code_test_index_boundaries_decision.md shape) resolving Open Decision 5
- Attach an explicit, falsifiable numeric threshold or qualitative bar to each of the six approval-gate criteria quoted verbatim from the idea doc
- Define a sample size (event count or elapsed period) grounded in a real field/value from retrieval_baseline_metrics.py's output or compute_shadow_baseline_comparison()'s cohort structure — not an unattributed round number
- Define an attribution method for causally linking an outcome to "missing/present context", stating plainly that no existing Phase 0-5 tool computes this today
- Include a labeled section explicitly stating zero real shadow-packet production events exist as of this decision (SHADOW_CONTEXT_PACKET_ENABLED off by default), and that thresholds are chosen deliberately in that absence
- For any criterion where a defensible a priori number is not possible without real shadow data, state that plainly as a risk/open question rather than inventing a number
- Update TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md's Assumptions/Open Questions to mark Open Decision 5 RESOLVED with a pointer to the new doc, mirroring the Open Decisions 1-4 convention exactly

## Out of Scope
- No promotion of any scenario from advisory to default behavior
- No change to gate PASS/FAIL/BLOCKED logic
- No live scenario evaluation
- No enabling SHADOW_CONTEXT_PACKET_ENABLED in production or any environment
- Open Decision 6 stays out of scope and is not touched
- No src/ or workflow code created or modified — Files Changed lists only the new doc plus the epic ticket edit

## Acceptance Criteria
- [x] New docs/ai/*_decision.md attaches an explicit, falsifiable numeric threshold or qualitative bar to each of the six approval-gate criteria quoted verbatim in the idea doc
- [x] Doc defines sample size (event count or elapsed period) citing a real field/value from retrieval_baseline_metrics.py's output or compute_shadow_baseline_comparison()'s cohort structure — not an unattributed round number
- [x] Doc defines an attribution method for causally linking an outcome to "missing/present context," explicitly stating no existing Phase 0-5 tool computes this today
- [x] Doc explicitly states, in a labeled section, that zero real shadow-packet production events exist as of this decision (SHADOW_CONTEXT_PACKET_ENABLED off by default) and thresholds are chosen deliberately in that absence
- [x] For any criterion where a defensible a priori number isn't possible without real shadow data, the doc states that plainly as a risk/open question rather than inventing a number
- [x] TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md's Assumptions/Open Questions is updated to mark Open Decision 5 RESOLVED with a pointer to the new doc, mirroring the Open Decisions 1-4 convention exactly
- [x] No src/ or workflow code is created/modified — Files Changed lists only the new doc + epic ticket edit

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-DEFAULT-PACKET-CRITERIA
- TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260729-SHADOW-PACKET-CALL-SITE
- TCK-20260729-SHADOW-BASELINE-COMPARISON

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/ai/default_packet_scenarios_decision.md
- docs/ai/code_test_index_boundaries_decision.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase6prep.md
- docs/ai/default_packet_scenarios_decision.md
- docs/ai/code_test_index_boundaries_decision.md
- tools/agent-monitoring/retrieval_baseline_metrics.py
- tools/agent-monitoring/generate_retro.py
- tools/retrieval_events.py
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md
- tickets/done/TCK-20260729-SHADOW-BASELINE-COMPARISON.md
- tickets/done/TCK-20260729-SHADOW-PACKET-CALL-SITE.md
- docs/agent-monitoring/schema.md

## Assumptions / Open Questions
- Tier tension resolved: proposal text said "standard-tier" but both immediate precedent tickets of identical shape (TCK-20260728-DEFAULT-PACKET-CRITERIA, TCK-20260728-CODE-TEST-INDEX-BOUNDARIES) landed as hotfix tier — confirmed via direct read of both files' ## Tier section — so this ticket uses hotfix tier to match established convention, not the structure-doc's stale wording
- context_tokens telemetry is confirmed platform-unavailable (not recorded in agent-monitoring/*.jsonl per docs/agent-monitoring/schema.md), so any criterion citing token reduction must use a proxy metric or explicitly flag the gap rather than cite a real token figure
- No existing tool computes causal attribution between an outcome and missing/present context today — the decision doc must propose a new method rather than reference an existing one
- Real shadow-packet production volume is confirmed zero as of this decision; sample-size/threshold answers for recall and provider-parity criteria may not be fully defensible a priori and must be stated as an open risk rather than resolved by invention

## Implementation Notes
Authored `docs/ai/shadow_promotion_gate_thresholds_decision.md`, matching
`docs/ai/default_packet_scenarios_decision.md`'s shape (frontmatter, "decides and evidences"
framing, numbered sections, closing Resolution section).

Grounding evidence was gathered fresh rather than reused blindly from prior decision docs:
- Re-ran `python3 tools/agent-monitoring/retrieval_baseline_metrics.py` on 2026-07-30 against the
  live corpus (721 `runs.jsonl` records, 3831 `events.jsonl` records, 122 distinct search-active
  run_ids, `search_count.total = 1738`, corpus-wide median `search_count.per_run = 3`,
  `gate_outcome.gate_fail_count = 74`, `review_rework.count = 4`).
- Confirmed via direct Python (`_load_runs_and_events()` + `compute_shadow_baseline_comparison()`)
  that both the "shadow" and "baseline" cohorts report `retrieval_event_count: 0` — zero real
  `retrieval_event_schema_version`-carrying records exist in `agent-monitoring/events.jsonl` today,
  confirming §5's zero-real-shadow-events claim independently of the `SHADOW_CONTEXT_PACKET_ENABLED`
  off-by-default confirmation already on record in `TCK-20260729-SHADOW-PACKET-CALL-SITE`/
  `TCK-20260729-SHADOW-BASELINE-COMPARISON`.
- Read `tools/eval_search.py`, `tickets/done/TCK-20260728-EVAL-FIXTURE-REPAIR.md` (existing 0.80
  Recall@5 gate, currently measuring 0.67), `tools/retrieval_event_parity_check.py` (structural-only
  provider-parity check, confirms only `claude-code` has ever produced a real event), `tests/tools/
  test_retrieval_cache.py` (25 existing cache-correctness tests), and `docs/observability/
  retrieval_retention_redaction_policy.md` (existing MAY/PROHIBITED list, reused directly as the
  privacy-boundary criterion's bar) to ground each of the six criteria in something real rather than
  inventing a number for all six equally.
- Confirmed `reason_code` (`docs/agent-monitoring/schema.md`) is populated only for `Scope`/
  `ticket-scoper` and `Verify`/`done-checker` events — `null` for every `Review`/`Architecture-Verify`
  event, i.e. exactly where the review-rework criterion's `NEEDS_CHANGES`/`BLOCKED` statuses are
  recorded — confirming no existing tool can causally attribute a gate-fail's cause today, which
  grounds the attribution-method gap (§4) and forces the proposed method to require a human-reviewed
  audit rather than an automated classifier.

Per Scope item 3, sample size was NOT set to a single invented round number. Instead each of the 3
shadow-eligible scenarios (per Open Decision 1) got its own floor, directly citing the real figure
Decision 1 already used for that scenario: Small bugfix → 56 (of 122 search-active run_ids at ≤2
searches, 45.9%, matching Decision 1's 53/118); Ticket implementation → 122 (the full population
size Decision 1's median-3 claim was computed over); Architecture-planning → 6 (the exact count of
outlier tickets Decision 1 named, still the same 6 in the fresh top-outlier list). An elapsed-period
floor (one agent-monitoring-retro cadence cycle) was added as a second, independently-grounded axis,
reusing the repo's own already-adopted weekly/5-ticket cadence rule rather than inventing a new one.

Per Scope item 6, two of the six criteria (authoritative-source recall; provider parity) were
explicitly flagged as NOT fully defensible a priori, with the concrete reason stated (no join from
`eval_search.py`'s index-level recall to a real shadow packet's cited sources; only one of two known
provider adapters has ever gone live) rather than forcing a false-precision number onto either.

Also caught and documented a structural gap not explicitly asked for in scope but directly relevant:
`compute_shadow_baseline_comparison()`'s existing "shadow" vs "baseline" cohort split partitions on
`infer_workflow(run_id) is not None` (real vs synthetic run_id provenance, built for Phase 4's
schema-emission tests) — this is NOT, as currently written, a shadow-packet-enabled-vs-not
comparison. Documented this as §3.3 so a future ticket does not assume this function already
provides the promotion-gate's needed partition.

No deviation from the ticket's Scope/Acceptance Criteria. No `src/` or `.claude/workflows/*.js`
file was touched. `SHADOW_CONTEXT_PACKET_ENABLED` was not enabled anywhere. Open Decision 6's text
was not touched.

## Test Summary
Documentation-only ticket — no `src/` or test code was added or modified, so no pytest run applies.
Verification performed instead:
- `python3 tools/validate_frontmatter.py docs/ai/shadow_promotion_gate_thresholds_decision.md` → OK
- `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` → OK
- `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS.md` → OK
- `python3 tools/ticket_field_values.py tickets/inprogress/TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS.md` → no violations
- All numeric claims in the new doc were verified against a fresh, real tool run
  (`retrieval_baseline_metrics.py`) or a direct read of the cited source file, not assumed from
  memory of the prior Phase 2 decision docs.

## Files Changed
- `docs/ai/shadow_promotion_gate_thresholds_decision.md` (new)
- `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` (modified — Open Decision 5 marked RESOLVED)
- `tickets/inprogress/TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS.md` (this ticket, modified — Status/AC/Implementation Notes/Test Summary/Files Changed/Completion Summary)

## Completion Summary
Resolved Open Decision 5 with a new decision doc,
`docs/ai/shadow_promotion_gate_thresholds_decision.md`, matching the shape and rigor of
`docs/ai/default_packet_scenarios_decision.md`/`docs/ai/code_test_index_boundaries_decision.md`.
Each of the six approval-gate criteria from the idea doc's "Shadow evaluation and approval gate"
section got an explicit, falsifiable bar (two — cache correctness, privacy boundary — are
zero-tolerance invariants already checkable today; two — recall, provider parity — are honestly
flagged as not fully defensible a priori and listed as open risk rather than forced into a number).
Sample size was defined as a per-scenario shadow-enabled run-count floor (56/122/6, each citing the
exact real figure `docs/ai/default_packet_scenarios_decision.md` used for that scenario) plus an
elapsed-period floor reusing the repo's existing agent-monitoring-retro cadence rule. An attribution
method was proposed (join by `run_id` between shadow-packet candidate/cited hashes and terminal gate
outcomes), explicitly stated as something no existing Phase 0-5 tool computes today, and explicitly
requiring a human-reviewed audit rather than an automated classifier until a structured
gate-failure-cause field exists. A labeled section confirms zero real shadow-packet production
events exist as of this decision, framing that absence as the precondition the idea doc itself
requires for selecting thresholds before evaluation, not retrofitting after. `tickets/inprogress/
TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Open Decision 5 entry was updated to RESOLVED,
mirroring Decisions 1-4's exact convention; Open Decision 6 was not touched. No `src/` or
`.claude/workflows/*.js` file was created or modified, and `SHADOW_CONTEXT_PACKET_ENABLED` was not
enabled anywhere.
