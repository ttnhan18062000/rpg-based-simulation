# Implementation Sequence — provider-agnostic-implementation

Tickets must be implemented in this order. Written manually from the source plan's own
Delivery Sequence (`docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`,
Phase 0 through Phase 5) and the intra-batch "hard dependency" risks each concern's investigation
flagged — `implement-epic` reads this file to override alphabetical order.

Unlike the discovery-epic batch, `create-tickets`'s automatic dependency detection did not fire
here: each ticket's `related_tickets` cites already-DONE discovery-epic tickets (the evidence
inputs it consumes), not sibling tickets in this same batch, so the auto-generator found no
matching IDs to build a dependency graph from. The order below is deliberate, not automatic.

## Order

1. TCK-20260721-BASELINE-MONITORING-MANIFEST  (Phase 0 — no deps in this batch; must land before any writer change per the plan's Non-Negotiable Data-Safety Rules)
2. TCK-20260721-ORCHESTRATION-CONTRACT-CORE  (Phase 1a — no deps in this batch; only depends on the already-DONE ORCHESTRATION-CONTRACT-ADR)
3. TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER  (depends on: TCK-20260721-ORCHESTRATION-CONTRACT-CORE — needs `agent-orchestration/workflows/implement-ticket.yaml` to diff against)
4. TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE  (Phase 2 — no deps in this batch; independent of the contract work, but ordered after Phase 1 per the plan's own numbering. Contains its own hard entry gate: quarantine/replace the legacy `.agents/skills/` tree before any new AGENTS.md/skills content goes live.)
5. TCK-20260721-MONITORING-WRITER-UNIFICATION  (Phase 3 — no deps in this batch; implements the already-DONE MONITORING-WRITER-DECISION directly, independent of the contract/Codex work above)
6. TCK-20260721-CODEX-REPLAY-PARITY  (depends on: TCK-20260721-ORCHESTRATION-CONTRACT-CORE, TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE — needs the contract, a proven conformance baseline, and a trusted `.codex/` config with verified real hook payloads)
7. TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS  (depends on: TCK-20260721-ORCHESTRATION-CONTRACT-CORE, TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE, TCK-20260721-MONITORING-WRITER-UNIFICATION, TCK-20260721-CODEX-REPLAY-PARITY — last in the sequence, per the plan's own Phase 5 gating)

## Why This Order Matters

Running alphabetically would attempt CLAUDE-CONFORMANCE-ADAPTER, CODEX-GUIDANCE-FIXTURE-CAPTURE,
and CODEX-REPLAY-PARITY before their prerequisites exist — CLAUDE-CONFORMANCE-ADAPTER needs the
contract skeleton from ORCHESTRATION-CONTRACT-CORE, and CODEX-REPLAY-PARITY needs both the
contract and a trusted, fixture-verified Codex config. LIVE-CODEX-PILOT-GUARDRAILS is deliberately
last: its own ticket text is explicit that live pilot *execution* stays blocked even after this
ticket's own guardrail/rollback tooling is built, pending all 5 prior tickets plus a separate,
independently-owned precondition (the `.agents/skills/` quarantine gate, itself inside ticket #4's
scope, not this one's).

BASELINE-MONITORING-MANIFEST (#1), ORCHESTRATION-CONTRACT-CORE (#2), CODEX-GUIDANCE-FIXTURE-CAPTURE
(#4), and MONITORING-WRITER-UNIFICATION (#5) have no dependencies on each other within this batch
and may be implemented in parallel once their own (already-satisfied) discovery-epic prerequisites
are confirmed — but #2 is ordered ahead of #4/#5 to match the plan's own Phase 0→1→2→3 numbering,
since #3 and #6 both consume #2's output.

Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.

## Related, Not Duplicated

This batch was created from
`docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`, the
implementation blueprint authored by Codex and reviewed by Claude (no blocking issues) as a direct
follow-on to the now-closed discovery epic (`tickets/done/TCK-20260721-PROVIDER-AGNOSTIC-EPIC.md`
and its child batch, `tickets/done/provider-agnostic-discovery/`). This batch's own parent epic is
`TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC` (scope-only, tracks these 7 children).

Two open, cross-batch risks each ticket's own investigation flagged, not fully resolved by
Structure — carried forward for each ticket's own Scope/Plan phase to resolve, not assumed away:

- **TCK-20260721-MONITORING-WRITER-UNIFICATION** overlaps ambiguously with the still-open
  `TCK-20260713-MONITORING-SQLITE-INDEX` batch's "monitoring index" scope — that ticket's own
  Out of Scope section names the disambiguation explicitly, but the two batches were not
  cross-linked or re-sequenced against each other here.
- **TCK-20260721-CODEX-REPLAY-PARITY** needs a genuinely new process-level (not AST-scan)
  containment-verification technique for a real, opaque Codex process — flagged as an open
  technical question for that ticket's own Investigate/Plan phase, not designed anywhere yet.
