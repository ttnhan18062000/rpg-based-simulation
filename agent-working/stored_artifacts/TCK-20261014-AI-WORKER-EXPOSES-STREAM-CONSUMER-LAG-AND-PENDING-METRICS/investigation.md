---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS
artifact_type: investigation
tags: []
---

# investigation — TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS

- `RedisStreamConsumer` already reads `xpending_range`; XINFO GROUPS gives `pending` and `lag` per group in one call, so the collector does not touch the consumer.
- `lag` can be None (Redis cannot compute it); that sample is omitted, pending is still reported.
- Ports in compose: 8000 backend, 8080 frontend, 6379 redis, 9090 prometheus, 3000 grafana, 3100 loki; 9108 is free. The endpoint was agreed with rpg-planner before the build.
- A DLQ already exists in the consumer; out of scope (user: metrics only).
