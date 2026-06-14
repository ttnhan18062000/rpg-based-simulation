# Implementation Sequence: resource-safety epic

Tickets in this batch have load-bearing dependencies. Implement child tickets in this order.

## Prerequisites (cert-memory-fix batch — must be done first)
1. TCK-20260614-CERT-SAFE-SERIAL
2. TCK-20260614-CERT-RECORDER-REFACTOR
3. TCK-20260614-CERT-EVIDENCE-LEVELS

---

## Phase 1 — Foundation (independent, can run in parallel)
These establish the base abstractions that later phases extend.

- **TCK-20260614-ARTIFACT-BUDGET-REG** — ArtifactBudgetRegistry (artifact write governance)
- **TCK-20260614-RESOURCE-BUDGET-GATE** — SubsystemBudget + pressure_report() per subsystem
- **TCK-20260614-CONTENT-HOTPATH-GUARD** — ContentWarmupService + ContentHotPathViolation

## Phase 2 — Subsystem features (each depends on Phase 1 budget gates)
These wire pressure reporting and behavioral changes per subsystem.

- **TCK-20260614-HASH-SCHEDULER** — depends on RESOURCE-BUDGET-GATE (hash rate budget)
- **TCK-20260614-REPLAY-BACKPRESSURE** — depends on RESOURCE-BUDGET-GATE (max_pending_flushes)
- **TCK-20260614-OBS-BACKPRESSURE** — depends on RESOURCE-BUDGET-GATE (queue fill thresholds)

## Phase 3 — Integration (depends on Phase 2)
- **TCK-20260614-LIFECYCLE-SUPERVISOR** — depends on REPLAY-BACKPRESSURE + OBS-BACKPRESSURE
  (reads pending_replay_flushes and survival_event_counts from those subsystems)
- **TCK-20260614-RESOURCE-DASHBOARD** — depends on all Phase 1 and Phase 2 tickets
  (reads pressure_report() from every wired subsystem)

---

## Rationale
`SubsystemBudget` and `pressure_report()` are the shared contract. Every Phase 2 ticket
produces a `pressure_report()`; the Dashboard in Phase 3 aggregates them all.
The Lifecycle Supervisor needs accurate `pending_replay_flushes` from Phase 2.
