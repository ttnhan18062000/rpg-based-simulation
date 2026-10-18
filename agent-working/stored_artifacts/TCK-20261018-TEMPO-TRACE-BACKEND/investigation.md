---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-TEMPO-TRACE-BACKEND
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-TEMPO-TRACE-BACKEND

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Findings (all recorded in the ticket's Implementation Notes and Test Summary)
- Version: Tempo 3.0.3 (2026-08-13) was the latest stable at least two weeks old on 2026-10-18; 3.0.4 was dated 2026-10-16. Digest `sha256:0296560a...` from a registry query.
- `docker/tempo.yaml` was first written from Tempo "next" docs. Tempo 3.0.3 rejected the `compactor:` block (`field compactor not found in type app.Config`, restart loop). Retention is `backend_worker.compaction.block_retention`, found with `-help`.
- The image has no probe tool and no healthcheck was added; readiness is `GET http://tempo:3200/ready` from the grafana container.
- The WAL started on a fresh named volume with no `user:` or init service; no permission error in the log.
- Harmless warnings: "metrics-generator is not configured", "unowned file entry ignored during wal replay file=blocks", a BackendScheduler "no jobs found".
