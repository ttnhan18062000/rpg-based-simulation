---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT
artifact_type: test_plan
tags: [architecture]
---

# Test Plan — TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT

This ticket is itself a verification exercise; the "test" is the audit's own decisive check.

1. `npm install && npm run build` inside `frontend/` — pass/fail is the primary finding.
2. If a fix was needed (step 1 failed), re-run the same command post-fix to confirm resolution.
3. If a Docker environment is available: `docker build -f frontend.Dockerfile .` (or the
   equivalent `docker compose build frontend` via `docker-compose.yml`) succeeds.

## Acceptance-criteria mapping
| Acceptance criterion | Verified by |
|---|---|
| `frontend/`'s current build health is known, not assumed | Test 1 |
| Any real breakage found is fixed, not just documented | Test 2 |
| The containerized build path (what's actually deployed) also works | Test 3 |
