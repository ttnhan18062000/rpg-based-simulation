---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261005-ACTION-HANDLERS-MAY-RETURN-BARE-NO-OPS-THAT-HOLD-THE-TASK
artifact_type: test_plan
tags: [engine, investigation]
---

# Test plan

No behaviour changes, so no new tests. The evidence is the measurement in `probes/` (investigation section 3).

## Proof Plan

- Level: real-kernel corpus measurement.
- Proof kind: measurement (a non-defect claim), with a positive control: the probe reports the typed `ACTION_WITHHELD_BY_POSTURE` failures the parent ticket fixed, so a bare return would be visible in the same classification.
- Oracle source: the Sticky-Task Law in `docs/engine/kernel.md` and divergence 2.69.
- Expected effect: zero bare dispatches in a run of 2 or more on any action kind.
- Selected commands: `probes/measure.sh before` (4 worlds x 2 runs, one simulation at a time).
