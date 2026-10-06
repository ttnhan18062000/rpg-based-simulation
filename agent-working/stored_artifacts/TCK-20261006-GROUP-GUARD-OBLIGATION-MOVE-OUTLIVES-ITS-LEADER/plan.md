---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER
artifact_type: plan
tags: [engine, combat]
---

# Plan

1. Measure guard move lifetimes on a legacy arm and an after arm (investigation section 2).
2. Extend `MovementCandidateSelector.tracked_move_complete` (gate 4's helper) to two guard kinds keyed on (`GUARD`, reason), extracting `_target_in_attack_reach` and renaming `_combat_positioning_kind` to `_tracked_move_kind`, so the per-function complexity stays under the project ceiling. No parallel termination path.
3. Decide the end condition (investigation section 3).
4. Tests: update gate 4's "guard unchanged" pins, add `TestGuardMoves` and dispatcher tests, with disabling controls.
5. Docs: tactical contract section 3, kernel note, divergence 2.71 (and the 2.70 wording), parity COMB-332 (and COMB-331).

Scope note: `GUARDING_ALLY` is included for the dead-ally end only, because it has the same shape and the same one-line condition; it was not in the ticket's text.
