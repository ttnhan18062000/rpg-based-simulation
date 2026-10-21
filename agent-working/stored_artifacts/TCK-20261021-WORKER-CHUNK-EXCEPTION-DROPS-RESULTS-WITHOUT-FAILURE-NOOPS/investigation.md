---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261021-WORKER-CHUNK-EXCEPTION-DROPS-RESULTS-WITHOUT-FAILURE-NOOPS
artifact_type: investigation
tags: []
---

# Investigation

execute_batch collected future.result() bare; a raising chunk logged and dropped its results. No timeout config exists anywhere (src/config/docs/engine). Gate runs inject LocalSequentialExecutor. Ruling (c) by rpg-planner: no timeout.

docs_to_update: docs/engine/contracts/bounded_concurrency_contract.md §4; docs/parity_ledger/infrastructure.yaml (INFRA-437).
