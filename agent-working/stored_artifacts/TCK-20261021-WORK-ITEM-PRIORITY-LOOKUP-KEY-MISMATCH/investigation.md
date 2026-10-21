---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261021-WORK-ITEM-PRIORITY-LOOKUP-KEY-MISMATCH
artifact_type: investigation
tags: []
---

# Investigation

Verified by reading origin/main 735a1c635. scheduler.py builds WorkItem.work_id `{tick}:{kind_lower}:{id}`; executor.py builds packet/result work_id `{tick}:{id}:{KIND}` and `priority_map` keyed by the former, looked up with the latter: never hits. Packet.local_priority = item.priority already. Sort direction: INFRA-420, deterministic_execution.md:138, scheduler_contract.md:38 and kernel.py agree (higher local_priority first); bounded_concurrency_contract §3 alone says lower. Ruled by rpg-planner: code is right.

docs_to_update: docs/engine/contracts/bounded_concurrency_contract.md (§3 local_priority line), docs/parity_ledger/infrastructure.yaml INFRA-420.
