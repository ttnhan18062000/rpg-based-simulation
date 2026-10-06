---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan

No behaviour changed, so no new tests and no disabling control. Verification is the measurement: `probes/measure.sh` (4 worlds x 2 runs,
2000 ticks, seed 42, `audit_mode`, budget disabled; matched pairs, so values) and `probes/ff_origin.py` (the caller trace; one run per world,
whose friendly-fire counts equal the counting runs: 372 and 211). Instrument check: the probe's friendly-fire count equals the real verdict
count in every world. A test pinning the dead raw-equality fallback was NOT added (planner ruled no hardening in this batch).
