---
status: historical
layer: ai
authority: P2
audience: developer
maturity: shipped
date: 2026-07-30
archived: 2026-08-20
tags: [ai, workflows, process-improvement]
---

# Ticket Plan Structure — Context-Efficient Agent Retrieval, Phase 6 Prep

Guide for `/create-tickets`'s Comprehend/Structure phases when parsing
`idea_context_efficient_agent_retrieval_observability.md` for the single remaining
prerequisite to Phase 6.

This supersedes `ticket_plan_structure_phase5.md` for this batch — Phase 5 is now `DONE`
(`TCK-20260729-SHADOW-PACKET-CALL-SITE`, `TCK-20260729-SHADOW-BASELINE-COMPARISON`), giving
this batch a real, tested shadow-packet call site and comparison-report view to ground
Open Decision 5's answer in.

## Scope this batch to Open Decision 5 only — this is NOT Phase 6 itself

Phase 6 is **"Selective workflow adoption — enable the packet phase only for scenarios that
pass the approval gate; retain direct targeted reads as the safety fallback."** Phase 6
cannot be scoped yet: its own gate (the "Shadow evaluation and approval gate" section, six
criteria) requires "numeric thresholds, sample size, and attribution method" to already be
decided, and the source doc is explicit that these **"must be selected before shadow
evaluation, not retrofitted after results are known"** — i.e. they must be decided
independent of observed shadow-packet results, precisely to prevent picking criteria that
happen to match whatever data comes in later. That decision is Open Decision 5, still
unresolved. This batch resolves Open Decision 5 only. It does NOT scope Phase 6, does NOT
run a real shadow evaluation, and does NOT judge any actual scenario against the six
criteria — there is no accumulated shadow-packet production data yet (the Phase 5 call site
is opt-in, off by default; `SHADOW_CONTEXT_PACKET_ENABLED` has not been enabled in
production as of this batch).

**This batch should produce one standard-tier ticket whose deliverable is a written,
reviewable decision document** (following this epic's own Phase 2 precedent — see
`docs/ai/default_packet_scenarios_decision.md` and `docs/ai/code_test_index_boundaries_decision.md`
for the exact shape/rigor bar to match), **not working code and not a promotion verdict**.
Acceptance criteria must be things like "resolves Open Decision 5 with an explicit, cited
sample-size/threshold/attribution-method answer for each of the six approval-gate criteria,"
not "implements a promotion check" or "evaluates scenario X against the gate."

**Cover these source-doc items, each traceable to a concrete deliverable:**

1. **Per-criterion numeric threshold or qualitative bar** for each of the six approval-gate
   criteria quoted below — a concrete, falsifiable definition of "passes," not a restatement
   of the criterion itself.
2. **Sample size** — how many shadow-packet events (or over what elapsed period) constitute
   enough evidence to evaluate a scenario against the six criteria, grounded in whatever real
   volume characteristics `tools/agent-monitoring/retrieval_baseline_metrics.py` and
   `TCK-20260729-SHADOW-BASELINE-COMPARISON`'s comparison view already show about this
   epic's typical event throughput — not an arbitrary round number.
3. **Attribution method** — how a specific outcome (a missed contract, a test/gate failure,
   a token-count change) gets causally attributed to "missing/present context" versus
   unrelated factors, since several of the six criteria require this causal link and none of
   the Phase 0-5 tooling currently computes it.
4. **Explicit acknowledgment of the current evidence gap** — state plainly that zero real
   shadow-packet production events exist as of this decision (the mechanism is opt-in/
   off-by-default), and that this decision is deliberately made in that absence, per the
   source doc's own "must be selected before shadow evaluation, not retrofitted after
   results are known" instruction — this is a feature of the process, not a gap to apologize
   for or work around.

**Do NOT ticket in this batch** (still Phase 6's own job, once this decision lands):
- Any actual promotion of a scenario to default/mandatory workflow behavior.
- Any change to `implement-ticket.js`'s gate PASS/FAIL/BLOCKED logic, or any packet content
  surfaced to an agent's real prompt/context.
- A live run judging any real scenario against the six criteria using this decision's
  thresholds — that requires accumulated evidence this batch does not generate.
- Open Decision 6 (MCP tool vs. provider-adapter-library exposure) — remains a separate,
  explicitly deferred decision, unrelated to promotion thresholds.
- Enabling `SHADOW_CONTEXT_PACKET_ENABLED` in any production/default configuration.

**Approval-gate criteria (quoted verbatim from the idea doc — this batch's job is to attach
concrete thresholds/sample-size/attribution method to each, not restate them):**
> - authoritative-source recall is at least the agreed baseline;
> - no material increase in missed contracts, test/gate failures, or review rework
>   attributable to missing context;
> - a meaningful, pre-declared reduction in median injected context tokens or follow-up
>   retrieval burden;
> - cache correctness: stale packets are rejected and source-hash checks pass;
> - provider parity: comparable request/packet/outcome events are emitted for every enabled
>   provider; and
> - privacy boundary: monitoring contains no raw prompts, raw retrieved source text, or
>   sensitive tool payloads.

If investigation reveals Open Decision 5 cannot be meaningfully resolved without first
generating at least some real (not fixture-only) shadow-packet evidence — i.e. that a
purely a priori numeric answer is not defensible for one or more of the six criteria — say
so plainly as a risk/open-question in the ticket rather than inventing a number to satisfy
this batch's own acceptance criteria.
