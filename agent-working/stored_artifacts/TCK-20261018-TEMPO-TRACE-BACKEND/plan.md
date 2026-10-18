---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-TEMPO-TRACE-BACKEND
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-TEMPO-TRACE-BACKEND

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Plan (from the ticket Scope and the dispatch)
1. Add a `tempo` service to the `observability` profile: image pinned by version and digest, `mem_limit` (start 512m), a named volume `tempo_data`, OTLP gRPC 4317 and HTTP 4318 and query port 3200 as `expose` only (no host port).
2. Add `docker/tempo.yaml`: single binary, local storage, 24h block retention, no metrics-generator.
3. Add a Grafana datasource `tempo` (`uid: tempo`) with trace to logs (Loki) and trace to metrics (Prometheus).
4. Give the backend `OTEL_EXPORTER_OTLP_ENDPOINT` (empty by default) and `OTEL_SERVICE_NAME=rpg-backend` in compose; add `tempo` to the profiles comment at the top of `compose.yaml`.
5. Deferred by the ticket to rpg's R3 (#622): the Loki `derivedFields` entry, the sampling variable and the exporter port choice.

Commits: fd6d6fa42 (service, config, datasource), a201f87df (Tempo 3.0 retention key found at runtime).
