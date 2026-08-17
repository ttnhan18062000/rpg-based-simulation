---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC
phase: open
date: 2026-08-17
tags: [architecture, engine, observability, testing, documentation]
---

# TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC

## Title
Codebase health & architectural resilience: investigate and prioritize two independent audits before scoping remediation epics

## Status
INPROGRESS

## Tier
epic

## Type
repair

## Priority
P1

## Request Summary
Two independent audits were run against this repo in the same session (2026-08-17):
`docs/audits/D23_architecture_resilience.md` (failure modes, resource governance, distributed-
system operability — 8 risk items, R1-R8) and `docs/audits/D24_codebase_health_observatory.md`
(codebase-scale health, dependency graph, test architecture, AI-agent navigability). Both are
thorough, evidence-cited (file:line citations, cross-verified across independent passes), and
already stage their own findings by priority (P0-P3 / Stage 1-5 / Phase 1-4). This epic tracks
the investigation and prioritization of those findings — grouped into 11 candidate epics in
`docs/plans/architecture_resilience_remediation_roadmap.md` — **before** any one of them is
broken into concrete, investigated child tickets via the `create-tickets` pipeline. No code or
doc fix from either audit has been applied yet.

## Scope
- Investigation-only epic: track and prioritize the 11 candidate sub-epics (A-K) in
  `docs/plans/architecture_resilience_remediation_roadmap.md`; do not implement any fix or run
  `create-tickets` on any of them from this ticket directly.
- Preserve both source audits durably in `docs/audits/` (D23, D24) since they were authored in
  `tmp/`, which is gitignored — the two Write operations creating those files are the only
  "implementation" this ticket itself performs.
- Identify and document overlap with already-in-flight work: the phase-count/documentation-drift
  findings both audits independently re-discovered are the same issue
  `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION` and `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` (under
  `TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC`) already cover — this epic amends that finding
  into the roadmap rather than re-ticketing it.
- Once a specific sub-epic (A-K) is chosen for action, run the `create-tickets` pipeline against
  a dedicated proposal document for that sub-epic only, producing its own investigated child
  tickets in `tickets/todos/<sub-epic-name>/` — that work is out of scope for this ticket and
  will be tracked as this epic's own child ticket once created.

## Out of Scope
- Implementing any fix from either audit (RabbitMQ/Kafka removal, `/health` fix, Redis DLQ,
  doc corrections, boundary-test hardening, etc.) — all deferred to whichever sub-epic is chosen.
- Re-running or second-guessing the audits' own findings — both are treated as trustworthy source
  material (evidence-cited, cross-verified across independent passes per their own Evidence Notes).
- Creating detailed child tickets for all 11 sub-epics up front — the explicit instruction for
  this epic is to scope and prioritize first, then focus into one sub-epic at a time.

## Acceptance Criteria
- [ ] Both source audits are durably preserved under `docs/audits/` as `D23`/`D24`, since their
      origin in `tmp/` is gitignored and would otherwise be lost.
- [ ] `docs/plans/architecture_resilience_remediation_roadmap.md` groups every risk item from
      both audits into a named, evidence-cited epic (A-K), each tagged with the source audit's
      own priority tier.
- [ ] The overlap between this roadmap's Epic C and the already-existing
      `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` ticket is explicitly documented, with the two new
      pieces of evidence (the `CLAUDE.md` "32-phase" claim, `docs/guides/simulation.md`'s
      nonexistent-file citation) identified as scope to fold into that existing ticket rather
      than duplicate.
- [ ] This epic remains open (not closed) until a decision is made on which sub-epic(s) to
      formalize into real tickets — closing this ticket is not itself the deliverable; the
      roadmap and preserved audits are.

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC (Epic C in the roadmap extends this epic's
  `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` child ticket)
- TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT (target of Epic C's amendment)
- TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION (same underlying contradiction, independently found)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (the concrete case study behind Epic E — the epic
  both audits found being incorrectly flagged stale by the file-mtime-only staleness hook)

## Related Docs
- docs/audits/D23_architecture_resilience.md
- docs/audits/D24_codebase_health_observatory.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/architecture/simulation_watchdog.md
- docs/architecture/observability_hot_path_safety_contract.md
- docs/guides/simulation.md
- docs/engine/kernel.md

## Related Stored Artifacts
None yet — staging artifacts for this ticket are in
`staging_artifacts/TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC/`.

## Related Code Areas
- src/api/server.py (R2 — `/health` stub)
- src/observability/watchdog.py (R2 — real watchdog implementation)
- src/observability/stream/consumer.py (R3 — Redis Stream consumer failure handling)
- src/observability/alerts/sinks.py (R7 — `WebhookAlertSink`)
- src/engine/phases.py (R4 — authoritative `TickPhase` enum)
- docker-compose.yml, pyproject.toml (R1 — RabbitMQ/Kafka dead infrastructure)
- tests/architecture/test_phase18_import_boundaries.py, test_phase19_observability_boundaries.py
  (D24 §E, §K — weak substring-based boundary tests)
- src_legacy/, tests_legacy/ (D24 §I — 601 dead bytecode files)

## Assumptions / Open Questions
- Which sub-epic(s) to formalize first is an open decision for the requester — the roadmap
  recommends A (dead infra) and B (engine liveness) as the only two both audits independently
  rank P0, with no dependency between them.
- Two items are flagged by the audits themselves as needing a closer look before any remediation
  ticket is written: (1) whether `pipeline.py`/`tactical.py` are genuinely covered indirectly via
  integration/kernel suites, or represent a real test-coverage gap; (2) whether
  `src/observability/mining/`'s three similarly-named orchestration classes are legitimately
  distinct or partially duplicative.
- Whether hardware-class (A/B/C) performance budgets are runtime-enforced or configuration-only
  was explicitly not fully traced in D23 and would need a follow-up pass if it matters for a
  future decision.

## Implementation Notes
(pending — scope-only epic; see `staging_artifacts/TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC/plan.md`)

## Test Summary
(pending — no direct tests; each future sub-epic ticket will carry its own)

## Files Changed
- docs/audits/D23_architecture_resilience.md (new)
- docs/audits/D24_codebase_health_observatory.md (new)
- docs/plans/architecture_resilience_remediation_roadmap.md (new)

## Completion Summary
(pending)
