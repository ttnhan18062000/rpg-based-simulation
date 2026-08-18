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
- Investigation/scoping epic: track and prioritize the candidate sub-epics in
  `docs/plans/architecture_resilience_remediation_roadmap.md`; do not implement any fix directly
  from this ticket.
- Preserve both source audits durably in `docs/audits/` (D23, D24) since they were authored in
  `tmp/`, which is gitignored — the two Write operations creating those files are the only
  "implementation" this ticket itself performs.
- Identify and document overlap with already-in-flight work: the phase-count/documentation-drift
  findings both audits independently re-discovered are the same issue
  `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION` and `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` (under
  `TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC`) already cover — amended into that existing
  ticket's scope directly (2026-08-17) rather than duplicated as a new epic. This is why the
  roadmap's Epic C has no corresponding epic-tier ticket of its own, unlike Epics A/B/D-K below.
- **(Added 2026-08-17)** Created one epic-tier ticket per remaining candidate epic (10 of the
  original 11 — all except C, per the point above), each in its own `tickets/todos/<name>/`
  folder with its own `docs/plans/<name>_epic.md` document and staging artifacts, listed under
  Related Tickets below. Each of those 10 is itself still scope-only — none has had
  `create-tickets` run against it yet; that remains deferred until a specific one is chosen for
  action, per the original instruction.

## Sub-epic tickets created (2026-08-17)
| Epic | Ticket | Priority | Tier (as of 2026-08-18) |
|---|---|---|---|
| A — Dead Infra Removal | `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` | P0 | standard |
| B — Engine Liveness & Health | `TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC` | P0 | standard |
| C — Doc Drift Reconciliation | *(no epic — amended into `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` directly)* | — | — |
| D — Redis Stream Resilience | `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC` | P1 | standard |
| E — Epic-Staleness Status-Aware | `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` | P1 | hotfix |
| F — HTTP Admission Control | `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC` | P2 | standard |
| G — Architecture Boundary Hardening | `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` | P2 | standard |
| H — Error-Handling Hygiene | `TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC` | P2 | standard |
| I — Determinism Verification Gap | `TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC` | P3 | standard |
| J — Codebase Navigability Hygiene | `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC` | P3 | epic |
| K — Codebase Health Observatory Tooling | `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC` | P3 | epic |

**(2026-08-18)** Audited all 10 sub-epics against this project's actual epic-tier bar ("large
multi-ticket initiative") and found 8 of 10 had been mechanically split from the roadmap
document's sections without individually re-testing tier fit. Downgraded A, B, D, F, G, H, I to
standard tier and E to hotfix tier (each rewritten to a concrete, directly-actionable scope/
acceptance-criteria — no `create-tickets` pass needed for these 8). J and K remain epic tier —
both are genuinely multi-ticket-shaped per their source docs. No sub-epic ticket was removed.

Once a specific sub-epic is chosen for action: the 8 standard/hotfix ones go straight to
implementation against their own ticket; J and K still need a `create-tickets` pass against a
dedicated proposal document, producing investigated child tickets in their own
`tickets/todos/<name>/` folder.

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
- [x] Ten sub-epic tickets (all candidate epics except C, which was amended into existing work
      instead) are created in their own `tickets/todos/<name>/` folders, each with its own
      `docs/plans/<name>_epic.md` and staging artifacts.
- [ ] This epic remains open (not closed) until a decision is made on which sub-epic(s) to
      actually formalize into investigated child tickets via `create-tickets` — closing this
      ticket is not itself the deliverable; the roadmap, preserved audits, and the 10 scoped
      sub-epics are.

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC (Epic C in the roadmap extends this epic's
  `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` child ticket)
- TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT (target of Epic C's amendment)
- TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION (same underlying contradiction, independently found)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (the concrete case study behind Epic E — the epic
  both audits found being incorrectly flagged stale by the file-mtime-only staleness hook)
- TCK-20260817-DEAD-INFRA-REMOVAL-EPIC
- TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC
- TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC
- TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC
- TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC
- TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC
- TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC
- TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC
- TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC

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
- docs/plans/{dead_infra_removal,engine_liveness_health,redis_stream_resilience,
  epic_staleness_status_aware,http_admission_control,architecture_boundary_hardening,
  error_handling_hygiene,determinism_verification_gap,codebase_navigability_hygiene,
  codebase_health_observatory_tooling}_epic.md (new — 10 files)
- tickets/todos/{dead-infra-removal,engine-liveness-health,redis-stream-resilience,
  epic-staleness-status-aware,http-admission-control,architecture-boundary-hardening,
  error-handling-hygiene,determinism-verification-gap,codebase-navigability-hygiene,
  codebase-health-observatory-tooling}/TCK-*-EPIC.md (new — 10 epic tickets, each with
  staging_artifacts/)
- tickets/todos/kernel-concurrency-design-review/TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT.md
  (amended — two new evidence pieces folded into existing scope, not duplicated)

## Completion Summary
(pending)
