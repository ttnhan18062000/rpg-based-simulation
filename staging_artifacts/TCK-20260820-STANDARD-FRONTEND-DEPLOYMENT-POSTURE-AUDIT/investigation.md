---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT
artifact_type: investigation
tags: [architecture]
---

# Investigation — TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT

## Origin
Live session investigation into the repo root beyond `src/`/`tests/`, found 3 frontend-shaped
directories. Initial framing overstated the finding — corrected mid-investigation before writing
this ticket, not after.

## What was initially flagged, and what turned out to be a non-issue
`dashboard-frontend/` (agent-ops dashboard, actively developed) has no `docker-compose.yml`
service, while `frontend/` (the game UI, 2+ months stale) does — initially read as a concerning
asymmetry. **Corrected on closer check**: `dashboard-frontend/` has its own dedicated Makefile
lifecycle (`dashboard-install`, `dashboard-build`, `dashboard-dev`, `dashboard-serve` — ports
8420/8471), a deliberate, documented, separate-from-docker-compose internal dev/ops tool. This is
intentional design, not a gap. `website/` (Docusaurus docs site, 1.5 months stale) deploys via its
own GitHub Pages CI workflow, also intentional and separate.

## The one real open question this ticket is actually scoped to
`frontend/` — the real, docker-composed game UI (`frontend.Dockerfile` explicitly builds
`COPY frontend/ .`) — is **2+ months stale** (last commit 2026-06-12) with **no `node_modules`
installed locally**, unlike `dashboard-frontend/` which has both a recent commit and installed
deps. Two explanations are equally plausible and not yet distinguished:
1. `frontend/` is feature-complete/stable and genuinely doesn't need frequent changes — staleness
   here would be healthy, not a problem.
2. `frontend/` has been silently deprioritized while all recent frontend attention went to
   `dashboard-frontend/`, and may not build cleanly against current dependency versions anymore —
   staleness here would be real drift risk for the one frontend component that's actually in the
   deployed docker stack.

**Not resolved here**: whether `frontend/` currently builds successfully
(`npm install && npm run build`) wasn't run as part of this investigation — a real, decisive,
cheap test left to the implementer rather than assumed either way.

## Related
- `docker-compose.yml`, `frontend.Dockerfile` (confirms `frontend/` is the one actually deployed)
- `Makefile` (`dashboard-install`/`dashboard-build`/`dashboard-dev`/`dashboard-serve` — confirms
  `dashboard-frontend/`'s separate, intentional lifecycle)
