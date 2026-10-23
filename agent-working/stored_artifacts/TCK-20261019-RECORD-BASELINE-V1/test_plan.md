---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261019-RECORD-BASELINE-V1
artifact_type: test_plan
tags: []
---

# Test plan — TCK-20261019-RECORD-BASELINE-V1

- Paired base: --self-check full spread 0 over all 30 base runs; audit_mode and signals_zeroed true in every run.
- behavioral_5k: green on 864f7b281 after rebaseline; two further repeats produce the same metrics (host-independent).
- Gate rows: acceptance by rpg-planner from the main run; this ticket does not re-measure them.
