---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261005-ACTION-HANDLERS-MAY-RETURN-BARE-NO-OPS-THAT-HOLD-THE-TASK
artifact_type: plan
tags: [engine, investigation]
---

# Plan

1. Enumerate every handler return without a `failure_reason` (investigation section 2).
2. Establish which action kinds can be a held task (investigation section 1).
3. Measure held-task exposure per action kind with a corrected run definition (probes/handler_exposure.py).
4. Fix only a reachable instance. None is reachable, so no source change; close as a measured non-defect.
