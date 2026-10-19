---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-API-LOAD-TEST-MEASURED-RUN
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-API-LOAD-TEST-MEASURED-RUN

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Findings (full tables in the record)
- Baseline throughput fell from 409.6 req/s at 10 users to 116-135 req/s at 50 users and above while latency rose; the steps shared one ageing backend, so user count and age were confounded.
- Age soak (50 users, 12 repeats): 445.6 -> 139.9 req/s over ten repeats while engine ticks/s stayed 8.5 -> 7.5-7.9. The `GET /api/v1/entities` average response grew 69,427 B -> 744,977 B and then stayed constant. The route's `limit` defaults to 100 (`src/api/server.py` lines 241-248); the locustfile calls it without parameters.
- Fresh and aged py-spy profiles (PROVISIONAL): pydantic `dump_python` 10.4% -> 22.2%, gzip `_write_raw` 6.4% -> 11.7%, json `iterencode` 6.8% -> 11.6% of samples. py-spy nonblocking errors 1164/9044 and 518/9821.
- Aged curve at the cap (`/entities` 744,599 B by curl before and after): 144.9 / 146.1 / 151.9 / 146.1 req/s at 10 / 25 / 50 / 100 users; p95 200 / 410 / 680 / 1400 ms.
- Observability on (50 and 100 users): 421.5 and 424.0 req/s; Grafana peak 121% of one core. Open item 6b did not reproduce.
- Side findings: access-log volume, the idle-client prune loop at 7.8% of fresh samples.
