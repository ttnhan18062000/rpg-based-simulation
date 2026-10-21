---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261021-WORK-ITEM-PRIORITY-LOOKUP-KEY-MISMATCH
artifact_type: plan
tags: []
---

# Plan

1. `packet_work_id` in src/core/work.py; executor uses it at both packet sites and for priority_map.
2. `ConcurrencyLaw.commit_key`; kernel sorts by it.
3. Contract §3 wording; INFRA-420 text/evidence/test_path.
4. Tests. Hash check held.
