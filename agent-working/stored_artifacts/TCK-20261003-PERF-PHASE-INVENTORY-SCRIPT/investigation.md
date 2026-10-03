---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT
date: 2026-10-03
tags: [performance, architecture, engine]
---

# Investigation: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT

- `refine()` has 44 `run_phase()` calls, all literal names, none conditional or in a loop, 12 flagged.
- `run_phase(name, update, lambda u: X.apply(...), flag)` is the only call shape; the dispatch target
  is the first call in the lambda body that is not a method of the lambda's own argument.
  Four calls dispatch to a bare local name (`_SU_fa`, `_SU_ip`, `_SU_dt`, `_SU_fs`).
- Direct operations: 9 assignments to `update` (`replace` / `update.replace`), plus 5 direct
  class-method calls made by `refine()` outside `run_phase()` (including `FactionDecisionPhase.execute`
  and two `FactionSentimentService` calls), which the `update` assignments alone would not show.
- `phase_domain_permissions.py` keys are the 7 kernel `TickPhase` members, a different unit from
  `refine()` phases; `PhaseDependencyGraph.PHASES` has 31 names, 14 of which are missing for pipeline phases.
- The documented sources differ in kind: the pipeline doc and D19 list names, the generator note and
  the epic state only a count.
