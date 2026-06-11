---
status: active
layer: observability
authority: P1
audience: developer
---

# Loki Label Ingestion Policy

## Purpose
To prevent high-cardinality label indexing explosion in Loki, which degrades query performance and crashes the storage coordinator in long simulation runs.

## Authorized Stream Labels
Only the following low-cardinality static attributes are authorized to be promoted to Loki stream labels:
- `level`: Log severity (INFO, WARNING, ERROR, etc.)
- `component`: Logging logger name/context
- `service`: Container/service name
- `environment`: Deployment tier (local, staging, production)
- `container`: Docker container identifier
- `job`: Promtail scrape task identification

## Prohibited Dynamic Labels
The following high-cardinality identifiers must **never** be relabeled or promoted to Loki stream labels:
- `tick` (unique per tick step)
- `entity_id` (unique per game actor)
- `worker_id` (unique per pool thread)
- `causal_id` (causal sequencing)
- `transaction_id` (financial/economic actions)
- `run_id` (individual run IDs)
- `target_id`
- `quest_id`

## JSON Logging Format and LogQL Querying
All dynamic identifiers must reside inside the structured JSON body payload.
The engine's `JsonFormatter` automatically serializes these fields under keys like `"tick"`, `"entity_id"`, and `"worker_id"`.

To query/filter logs based on these dynamic parameters in Grafana, extract the fields using LogQL's `| json` parser:

```logql
# Old high-cardinality label approach (PROHIBITED):
{service="backend", tick="145"}

# Safe JSON-parsed query approach (MANDATORY):
{service="backend"} | json | tick = 145
```
