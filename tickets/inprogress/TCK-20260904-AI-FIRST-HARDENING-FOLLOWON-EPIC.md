---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC
phase: open
date: 2026-09-04
tags: [governance, ai, agent-monitoring]
---

# TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC

## Title
AI-First Hardening — Bucket B/C follow-on tracking epic (not yet scoped into child tickets)

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` (Rev.3, READY TO FREEZE, 2026-09-04) and its
detail plans under `docs/plans/agent_infrastructure/ai_first_hardening_epics/` name 21 inventory
items across 3 output buckets. All 12 Bucket-A (Committed) items have now been either ticketed
(`tickets/todos/ai-first-hardening-governance-guardrail-batch/`, 12 tickets) or accounted for
(1 already shipped before ticketing began, 1 skipped pending a governance re-ratification —
`TCK-20260904-BASH-SECRET-SCAN-HOOK`). What remains genuinely un-scoped is Bucket B (5 items —
Experiments) and Bucket C (4 items — blocked Future Options, plus explicitly-rejected directions).
Per the freeze verdict's own handoff boundary, Bucket B items become **Experiment Specifications**
(Hypothesis/Baseline/Method/Metrics/Exit/Kill Criteria), not straight implementation tickets, and
Bucket C items stay untouched until their named (not calendar) prerequisites clear. This epic
exists purely to track that this follow-on scope is real and known — it deliberately does not
break any of it down into concrete child tickets or Experiment Specifications yet. That
investigation/scoping work is future, out-of-session work.

## Scope
- Track, at epic level only, the 5 Bucket-B experiment items and the 4 Bucket-C future-option
  items (plus the 2 experiment-follow-on decisions, items 16 and 17) named in `roadmap.md`'s
  inventory table — see the list below.
- Serve as the `## Related Tickets` link target once any of the following becomes real work in a
  future session: an Experiment Specification for one of the 5 Bucket-B items, or a real ticket
  for a Bucket-C item once its named prerequisite clears.
- Nothing else. No investigation, no plan.md/investigation.md/test_plan.md staging artifacts, no
  child-ticket creation — held deliberately at `EPIC_SCOPED`, per direct instruction.

## Out of Scope
- Writing any Experiment Specification (Hypothesis/Baseline/Method/Metrics/Exit/Kill Criteria) for
  any Bucket-B item — that is real, separate future work, not part of scoping this epic.
- Creating any child ticket for a Bucket-C item — every one of them is genuinely blocked on a
  named prerequisite (see below), not ready regardless of this epic's existence.
- Re-litigating or re-evaluating the Bucket A/B/C split itself — that classification was already
  made in the frozen proposal and `roadmap.md`; this epic inherits it as given.
- Anything already covered by `tickets/todos/ai-first-hardening-governance-guardrail-batch/`'s 12
  tickets, or by `TCK-20260904-BASH-SECRET-SCAN-HOOK` (blocked, in `tickets/inprogress/`) — this
  epic tracks only the un-ticketed remainder.

## Acceptance Criteria
- [ ] This epic ticket exists at `## Status: EPIC_SCOPED`, correctly enumerating all 9 remaining
      Bucket B/C inventory items (5 Bucket-B, 4 Bucket-C) plus the 2 named experiment-follow-on
      decisions, with no child tickets or Experiment Specifications created as part of closing
      this acceptance criterion — the epic's job here is enumeration and linkage, not execution.
- [ ] A future session that picks up any one of these items links its resulting Experiment
      Specification or ticket back to this epic's `## Related Tickets` (or an equivalent
      cross-reference), so the roadmap's Bucket B/C scope stays traceable to one place.

## Related Tickets
- Bucket A (already handled, not part of this epic's remaining scope):
  `tickets/todos/ai-first-hardening-governance-guardrail-batch/` (12 tickets),
  `TCK-20260904-BASH-SECRET-SCAN-HOOK` (blocked, `tickets/inprogress/`).
- `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` — the ratified decision `TCK-20260904-BASH-SECRET-SCAN-HOOK`
  and the knowledge-gateway removal item are both blocked on; not itself part of this epic's Bucket
  B/C scope, referenced for traceability.

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md (the master inventory this
  epic's item list is drawn from — items 13–21 plus follow-on items 16–17)
- docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md (M2, M3 —
  Bucket-B members: ticket-claim detection logging, phase-level resume design)
- docs/plans/agent_infrastructure/ai_first_hardening_epics/review_independence_epic.md (M2 —
  Bucket-B: shadow comparison & cutover decision)
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md
  (post-M5 follow-on — Bucket-B: Bash secret-exposure hook blocking-escalation decision)
- docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md
  (item 13 — the highest-leverage Bucket-B item; every Bucket-C item is gated on its exit criteria)
- docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md (items 18–21
  plus the explicitly-rejected directions)
- docs/brainstorm/agent-working-design/ai_first_engineering_next_evolution_proposal.html (Rev.3
  frozen proposal — the freeze verdict's Bucket-B handoff-format requirement)

## Related Stored Artifacts
None — epic held at scope-only, no staging artifacts created per direct instruction.

## Related Code Areas
None yet — no code investigation performed for this epic's remaining scope.

## Assumptions / Open Questions
- **Bucket B inventory (5 items, each needs its own Experiment Specification before any ticket)**:
  1. Item 13 — Filtered replay eval pilot + dataset hygiene + metric design
     (`agent_evaluation_foundation_experiment.md`). Highest-leverage: every Bucket-C item downstream
     gates on its exit criteria. Its actual replay run is recommended (not required) to follow
     `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` landing, per `roadmap.md`'s execution-timing note
     — planning may proceed in parallel regardless.
  2. Item 14 — Ticket-claim detection logging (`workflow_reliability_epic.md` M2). Log-only,
     no lock; decision gate at 30 days of real data to decide build-vs-convention-only.
  3. Item 15 — Phase-level workflow resume: design/validation-rule resolution
     (`workflow_reliability_epic.md` M3). Design-resolution work, not implementation.
  4. Item 16 — Model-diverse reviewer shadow comparison & cutover decision
     (`review_independence_epic.md` M2). Gated on `TCK-20260904-SHADOW-REVIEWER-LOGGING` (this
     batch's M1 ticket) running long enough to produce comparison data.
  5. Item 17 — Bash secret-exposure hook blocking-escalation decision (governance epic's post-M5
     follow-on). Gated on `TCK-20260904-BASH-SECRET-SCAN-HOOK` (currently blocked) running through
     its own M5 exit window — doubly gated: first on the knowledge-gateway re-ratification, then
     on a real false-positive-rate measurement.
- **Bucket C inventory (4 items, each blocked on a named — not calendar — prerequisite)**:
  1. Item 18 — Model-based routing for mechanical agents. Hard prerequisite: item 13's eval pilot
     produces a trusted baseline.
  2. Item 19 — Task-success-rate metric closing the improvement loop. Hard prerequisite: item 13
     establishes a repeatable scoring approach.
  3. Item 20 — Full agent-behavior eval platform. Evidence prerequisite: item 13 proves the signal
     is useful and repeatable.
  4. Item 21 — Live Codex provider pilot. Hard prerequisite: item 12 (provider-portability
     conformance test — `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST`, already ticketed in
     this batch) passing. Item 13 is an *additional* prerequisite only if the intended pilot
     includes a comparative quality evaluation between providers.
  - Plus 5 explicitly-rejected directions (`bucket_c_future_options.md`'s "Explicitly not
    recommended" section) — re-evaluated independently in the freeze pass, not inherited from the
    earlier maturity audit; no action expected on these unless someone re-opens the question with
    new evidence.
- Whether a future session should scope Bucket B items one at a time as Experiment Specifications,
  or batch several together, is left open — not decided here, per direct instruction to hold this
  epic at scope-only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
