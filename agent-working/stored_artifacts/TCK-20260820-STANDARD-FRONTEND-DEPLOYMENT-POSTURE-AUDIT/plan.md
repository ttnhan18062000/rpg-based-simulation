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

   **Scope boundary — added during Review**: this P3 audit ticket authorizes fixing *contained*
   breakage inline only — a dependency-version pin, a lockfile regeneration, a config/tsconfig
   tweak, or an equivalently narrow, mechanical fix. If the real failure turns out to require a
   major framework version bump (e.g. React/Vite major version), non-trivial source-code migration,
   or any change touching more than a handful of files, **stop**: document the finding precisely
   (what's broken, what a real fix would require) in this ticket's Completion Summary, do not
   attempt the fix here, and flag it back as a candidate for a separate, properly-scoped ticket
   instead. This ticket's own job is to determine health and fix small breakage, not to absorb an
   open-ended migration.
4. **Either way**: confirm `frontend.Dockerfile`'s build (`docker build -f frontend.Dockerfile .`
   or equivalent, if a Docker environment is available to the implementer) also succeeds — the
   npm-level build succeeding doesn't guarantee the containerized build path does too.

## Explicitly out of scope
- Any change to `dashboard-frontend/`'s or `website/`'s deployment posture — both confirmed
  intentional and healthy in this investigation, not touched by this ticket.
- Adding a `docker-compose.yml` service for `dashboard-frontend/` — explicitly not warranted, it
  has its own correct, separate Makefile-based lifecycle.
