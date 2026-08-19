---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT
artifact_type: plan
tags: [architecture]
---

# Plan — TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT

**Planning/investigation only — no implementation assumed in advance.** The right fix (if any)
depends entirely on what step 1 finds.

## Steps

1. **Decisive test, run first**: `cd frontend && npm install && npm run build`. This alone answers
   whether `frontend/`'s staleness is healthy-and-stable or actually broken.
2. **If it builds cleanly**: no code fix needed. Just document the finding (frontend/ is stable,
   staleness is not drift) somewhere durable — e.g. a one-line note in this ticket's Completion
   Summary — so a future audit doesn't re-raise the same false alarm.
3. **If it fails to build**: triage the failure (dependency version incompatibility, breaking API
   change in a dependency, etc.) and fix it — scope grows from "audit" to "repair," but only if
   step 1 actually finds a real problem.
4. **Either way**: confirm `frontend.Dockerfile`'s build (`docker build -f frontend.Dockerfile .`
   or equivalent, if a Docker environment is available to the implementer) also succeeds — the
   npm-level build succeeding doesn't guarantee the containerized build path does too.

## Explicitly out of scope
- Any change to `dashboard-frontend/`'s or `website/`'s deployment posture — both confirmed
  intentional and healthy in this investigation, not touched by this ticket.
- Adding a `docker-compose.yml` service for `dashboard-frontend/` — explicitly not warranted, it
  has its own correct, separate Makefile-based lifecycle.
