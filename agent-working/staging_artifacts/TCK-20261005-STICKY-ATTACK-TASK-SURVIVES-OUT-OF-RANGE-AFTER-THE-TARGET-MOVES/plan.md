---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
artifact_type: plan
tags: [engine, combat]
---

# Plan

1. Measure OUT_OF_RANGE rejections and repeat length on post-#344/#347 main (`probes/oor_probe.py`, `probes/measure.sh`). Done.
2. Decide the reset rule on the evidence (see `investigation.md`). Outcome: the repeat is bounded to one tick in every
   corpus world, so scale the change down to nothing, as ticket scope 2 permits.
3. No source, test, `docs/engine/` or parity-ledger change: engine behaviour is unchanged. The `actions.py:221-230`
   comment is left as is, because the code it describes is unchanged and the measurement does not contradict it on main.
4. Record the re-open trigger (re-run `measure.sh` once the flee gate opens the attack path) in the ticket.
