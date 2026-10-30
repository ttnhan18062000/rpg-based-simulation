---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED
phase: open
date: 2026-10-28
tags: []
---

# plan

Approval wanted from rpg-planner before code. Implements the rulings (decisions 1-5).

1. Lookup (`intelligence.py:1610`): replace "first same-kind record" with a pure helper in src/core/strategic.py (`same_kind_live_record(projects, kind, current_project_id)`): current project if it is of the kind; else newest live record by `created_tick` (ties: larger id), ACTIVE before SUSPENDED. Dead records never take part. Dict order plays no part.
2. Target match helper (`project_target_matches(project, candidate)`): target_entity_id equality when either side has one, else target_id equality; both None is a match. Read from the project's active objective (falls back to the first objective).
3. Branches at :1612:
   a. live record, target matches, current -> continue (no new project, no switch).
   b. live record, target matches, SUSPENDED/non-current -> resume the newest.
   c. live record, target differs -> SUPERSEDE: one StrategicUpdate that sets the newest live record to ABANDONED with the new typed end reason and adds the candidate project; cap-neutral, gate not consulted; `evaluate_project_switch` still decides whether it becomes current.
   d. no live record -> new project through the cap gate (`:1773` uses "no live same-kind record" in place of `not existing`).
4. Typed end reason: smallest field is `ProjectState.ended_by: Optional[ProjectEnd] = None`, enum `ProjectEnd` with one member `SUPERSEDED_BY_TARGET`; omitted from the canonical dict when None so unrelated hashes do not move. Needs rpg-planner's yes (a new durable field with a lifecycle: set once with the terminal status, read by observability).
5. Observability: supersede and resume counts per kind as typed counters next to the capacity refusal counts, for the Measured section.
6. Records: new divergence (Bug Fix) stating rules 1-5 plus 2.77/2.137 amendments; Bible 04 l.229 sentence rewritten (diff to rpg-designer); parity ledger entry for the capacity gate; mechanism registry `strategic_intelligence_core` entry reviewed.
7. Measured step: tools/rpg_measure paired, 3 worlds x s42-46 x 5000t, base = d914bace7 (or current main), per-kind refusal and supersede counts, extinction line.
