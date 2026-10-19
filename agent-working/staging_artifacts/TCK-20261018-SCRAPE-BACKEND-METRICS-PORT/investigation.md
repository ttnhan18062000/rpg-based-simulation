---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-SCRAPE-BACKEND-METRICS-PORT
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-SCRAPE-BACKEND-METRICS-PORT

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Findings at dispatch
- rpg R1 (#648, 0235c4dc3): `src/api/metrics_port.py` serves the manager's registry without auth on
  `BACKEND_METRICS_PORT` (default 9109) at `BACKEND_METRICS_HOST` (default 0.0.0.0); a bind failure is logged, never
  raised. It did not change `compose.yaml`.
- rpg R2 (#654, 590ee3e07): `http_request_duration_seconds{method, route, status_class}` on the same registry; route is
  the template or `unmatched`; websockets are not timed.
- S4 (#640) removed the old `backend:8000` job; `TargetDown` alerts on any job with `up == 0` for 2m.
