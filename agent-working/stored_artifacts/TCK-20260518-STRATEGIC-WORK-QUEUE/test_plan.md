---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260518-STRATEGIC-WORK-QUEUE
artifact_type: test_plan
tags: [strategic, work, queue]
---

# Test Plan: StrategicWorkQueue

Implement the following unit tests in `tests/unit/optimization/test_strategic_work_queue.py`:
- `test_strategic_queue_prioritizes_failed_action_entity`
- `test_strategic_queue_prioritizes_unresolved_blocker`
- `test_strategic_queue_prioritizes_biological_emergency`
- `test_strategic_queue_includes_dirty_strategic_entities`
- `test_strategic_queue_respects_budget`
- `test_strategic_queue_background_sweep_prevents_starvation`
- `test_strategic_queue_force_full_scan_includes_all_strategic_entities`
