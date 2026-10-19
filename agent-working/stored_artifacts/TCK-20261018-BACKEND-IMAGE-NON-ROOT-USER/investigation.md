---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Findings (recorded in the ticket)
- A grep of `src/` found `mkdir` calls in `src/lab/*`, `src/worldassembly/resolve_io.py` and `src/observability/behavior/worker.py`. At runtime none of them fired in `serve` or in the anomaly worker; the run showed no PermissionError.
- `--no-create-home` leaves `HOME=/home/app`, which does not exist; nothing used it, so no `ENV HOME` change was made.
- The watchdog is in the `observability` profile, so the default-profile run did not start it. In the later observability start of the measured-run window, the first watchdog showed uid 0 because the `platform-watchdog` image was stale (built before this change, and `docker compose build` had run without the observability profile). After `docker compose --profile observability build watchdog` it showed uid 1000.
- The root-owned `data/runs/run_1792263138_5169_1_3e0de9d3` pre-dates this change; it is the owner's to remove.
