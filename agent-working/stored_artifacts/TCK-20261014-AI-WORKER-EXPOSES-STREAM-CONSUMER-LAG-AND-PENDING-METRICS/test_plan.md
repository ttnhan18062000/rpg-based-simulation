---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS
artifact_type: test_plan
tags: []
---

# test_plan — TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS

- Fake Redis: lag and pending per stream and group; read at scrape time; unknown lag; Redis down gives up=0 and no gauges; a client that cannot be built; port default, env override and bad values; /metrics served over HTTP on the env port; the module imports no `src.engine`.
