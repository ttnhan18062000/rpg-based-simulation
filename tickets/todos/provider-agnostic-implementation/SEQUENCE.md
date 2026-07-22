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

1. TCK-20260721-BASELINE-MONITORING-MANIFEST  (Phase 0 — no deps in this batch; must land before any writer or reader migration can claim historical-data preservation, per the plan's Non-Negotiable Data-Safety Rules)
2. TCK-20260721-ORCHESTRATION-CONTRACT-CORE  (Phase 1a — no deps in this batch; only depends on the already-DONE ORCHESTRATION-CONTRACT-ADR)
3. TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER  (depends on: TCK-20260721-ORCHESTRATION-CONTRACT-CORE — needs `agent-orchestration/workflows/implement-ticket.yaml` to diff against)
4. TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE  (depends on: TCK-20260721-ORCHESTRATION-CONTRACT-CORE — the shared contract is the canonical semantic source; a manually curated Codex catalog produced before it exists would create a second semantic authority. Contains its own hard entry gate: quarantine/replace the legacy `.agents/skills/` tree before any new AGENTS.md/skills content goes live, with the replacement catalog generated from the validated contract, not merely "reviewed material.")
5. TCK-20260721-MONITORING-WRITER-UNIFICATION  (depends on: TCK-20260721-BASELINE-MONITORING-MANIFEST — its entry criterion consumes the baseline manifest; its exit criterion compares the post-migration corpus against that baseline, allowing only explicitly identified new append records)
6. TCK-20260721-CODEX-REPLAY-PARITY  (depends on: TCK-20260721-ORCHESTRATION-CONTRACT-CORE, TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE, TCK-20260721-MONITORING-WRITER-UNIFICATION — needs the contract, a proven conformance baseline, a trusted `.codex/` config with verified real hook payloads, and the writer/reader contract this ticket's shadow-mode comparison depends on. The plan sequences Phase 4 after Phase 3; safety over parallelism here.)
7. TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS  (depends on: TCK-20260721-ORCHESTRATION-CONTRACT-CORE, TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE, TCK-20260721-MONITORING-WRITER-UNIFICATION, TCK-20260721-CODEX-REPLAY-PARITY — last in the sequence, per the plan's own Phase 5 gating)

## Why This Order Matters

Running alphabetically would attempt CLAUDE-CONFORMANCE-ADAPTER, CODEX-GUIDANCE-FIXTURE-CAPTURE,
MONITORING-WRITER-UNIFICATION, and CODEX-REPLAY-PARITY before their prerequisites exist —
CLAUDE-CONFORMANCE-ADAPTER and CODEX-GUIDANCE-FIXTURE-CAPTURE both need the contract skeleton from
ORCHESTRATION-CONTRACT-CORE (the plan's approved architecture treats the shared contract as the
sole canonical semantic source; generating a Codex delivery catalog or diffing Claude's live
behavior before it exists would create a second semantic authority). MONITORING-WRITER-UNIFICATION
needs BASELINE-MONITORING-MANIFEST's read-only inventory as its own entry criterion, so its
data-preservation claim is actually falsifiable rather than asserted. CODEX-REPLAY-PARITY needs
the contract, a proven conformance baseline, a trusted Codex config, AND the writer/reader
contract from MONITORING-WRITER-UNIFICATION. LIVE-CODEX-PILOT-GUARDRAILS is deliberately last:
its own ticket text is explicit that live pilot *execution* stays blocked even after this ticket's
own guardrail/rollback tooling is built, pending all 5 prior tickets plus a separate,
independently-owned precondition (the `.agents/skills/` quarantine gate, itself inside ticket #4's
scope, not this one's).

Only BASELINE-MONITORING-MANIFEST (#1) and ORCHESTRATION-CONTRACT-CORE (#2) have no dependency on
any other ticket in this batch and may start immediately/in parallel. Every other ticket depends
on at least one of those two (or on a ticket that itself depends on them), per the corrections
below.

Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.

## Corrections Applied (Codex review, 2026-07-22)

This sequence was revised after Codex's review of the initial batch
(`docs/plans/agent_infrastructure/provider_agnostic_orchestration/tickets_review_response_codex.md`)
found 4 required corrections, all applied here and in the affected ticket files:

1. MONITORING-WRITER-UNIFICATION now depends on BASELINE-MONITORING-MANIFEST (was previously
   listed with no intra-batch dependency, which conflicted with Phase 0 and the plan's
   non-negotiable data rule).
2. CODEX-GUIDANCE-FIXTURE-CAPTURE now depends on ORCHESTRATION-CONTRACT-CORE (was previously
   independent; the plan's approved architecture requires the shared contract to exist before any
   provider-native delivery surface is generated from it).
3. CODEX-REPLAY-PARITY now depends on MONITORING-WRITER-UNIFICATION (was previously missing this
   dependency; the plan sequences Phase 4 after Phase 3, and safety is more important than
   parallelism here).
4. MONITORING-WRITER-UNIFICATION's own scope was narrowed to remove `query.py`/`validate.py`/
   `generate_retro.py` migration work — that ownership belongs to the separate, already-scoped
   `tickets/todos/agent-monitoring-derived-index/` batch (see "Related, Not Duplicated" below),
   which now depends on this ticket in turn.

## Related, Not Duplicated

This batch was created from
`docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`, the
implementation blueprint authored by Codex and reviewed by Claude (no blocking issues) as a direct
follow-on to the now-closed discovery epic (`tickets/done/TCK-20260721-PROVIDER-AGNOSTIC-EPIC.md`
and its child batch, `tickets/done/provider-agnostic-discovery/`). This batch's own parent epic is
`TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC` (scope-only, tracks these 7 children).

One cross-batch overlap flagged during Structure is now resolved, one open technical question
remains genuinely open by design:

- **TCK-20260721-MONITORING-WRITER-UNIFICATION ↔ `tickets/todos/agent-monitoring-derived-index/`
  batch — RESOLVED.** The two batches were initially ambiguous about who owns
  `query.py`/`validate.py`/`generate_retro.py`. Per Codex's review, ownership is now split
  cleanly: MONITORING-WRITER-UNIFICATION owns the append writer, additive record schema
  (`execution_id`/`provider`), legacy-normalization contract, and the dashboard-ingestion
  boundary only. The separate `agent-monitoring-derived-index` batch (`TCK-20260713-MONITORING-SQLITE-INDEX`
  plus its 3 already-scoped sub-tickets, `QUERY-INDEX-MIGRATE`/`VALIDATE-INDEX-MIGRATE`/
  `RETRO-INDEX-MIGRATE`) owns migrating those same three readers to provider/execution-aware
  normalized reads, and now depends on MONITORING-WRITER-UNIFICATION landing first (its own
  `SEQUENCE.md` and ticket files were updated in the same review-correction pass to record this
  cross-batch dependency explicitly — see that folder for details).
- **TCK-20260721-CODEX-REPLAY-PARITY** needs a genuinely new process-level (not AST-scan)
  containment-verification technique for a real, opaque Codex process — Codex's review confirmed
  leaving this to that ticket's own Investigate/Plan phase is appropriate, provided it selects one
  auditable method before any paid/live invocation rather than merely listing candidates.
