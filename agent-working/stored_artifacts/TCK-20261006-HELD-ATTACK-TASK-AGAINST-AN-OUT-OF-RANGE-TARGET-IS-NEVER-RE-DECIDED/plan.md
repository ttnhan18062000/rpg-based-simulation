---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED
artifact_type: plan
tags: [combat, cognition]
---

# Plan

Rulings (rpg-feature-planning, 2026-10-06): melee adjacency is orthogonal (MOV-07); OUT_OF_RANGE must lead to a re-decision or a closing step, never a re-swing, and the fix must guarantee closing; option A for the second root cause (hold granted on `pipeline_phases/movement.py`, guard reads `navigation.target_clear`); the int() versus float distance disagreement is its own P3 ticket; scheduler.py asks first, kernel.py frozen.

1. `actions.py`: end an `ATTACK` task on `OUT_OF_RANGE` through the existing clear (`_ENDS_HELD_ATTACK_REASONS`), reverse the stale comment and the old pinning test. Keep `INSUFFICIENT_READINESS`.
2. Verify the guarantee instead of assuming it: count tactical `ATTACK` decisions against legality, and every `OUT_OF_RANGE` call by held versus decision tick.
3. Build the constructed diagonal pair through the real Kernel (target pinned, attacker clearly stronger) and measure the first strike tick. If it does not strike, find out why before touching more code.
4. `movement.py`: skip an entity whose update carries `navigation.target_clear` with no new `target_set` (one helper, `_already_settled_this_tick`); no new notion of "arrived".
5. Tests: unit (route and classification), kernel-level bounded strike with a disabling control, one bracketing case.
6. Measure before and after: both worlds (seed 42, 2000 ticks) and the campaign episode (seeds 42 and 1337, 70 ticks), audit_mode, budget off, twice each. Disclose the re-baseline.
7. Docs, parity, divergence; file the P3 distance ticket; remove the misplaced AC from the salience ticket; gates.

Out of scope: the yield push (movement.py 8-neighbour), `scheduler.py`, `kernel.py`, legality and pursuit-completion semantics, `positioning.py`.
