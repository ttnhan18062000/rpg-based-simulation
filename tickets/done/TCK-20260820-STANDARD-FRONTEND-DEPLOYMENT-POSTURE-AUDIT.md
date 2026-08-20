---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT
phase: done
date: 2026-08-20
tags: [architecture]
---

# TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT

## Title
Verify whether frontend/ (2+ months stale, the actual dockerized game UI) still builds cleanly

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P3

## Request Summary
Live session investigation into the repo root beyond `src/`/`tests/` found 3 frontend-shaped
directories. Two are confirmed healthy and intentional: `dashboard-frontend/` (agent-ops
dashboard) has its own dedicated, documented Makefile lifecycle
(`dashboard-install`/`dashboard-build`/`dashboard-dev`/`dashboard-serve`), separate from
docker-compose by design, not a gap; `website/` (Docusaurus docs site) deploys via its own GitHub
Pages CI workflow, also intentional. The one real open question: `frontend/` — the actual
docker-composed game UI (`frontend.Dockerfile` explicitly builds `COPY frontend/ .`) — is 2+
months stale (last commit 2026-06-12) with no `node_modules` installed locally, unlike
`dashboard-frontend/`. Whether that staleness reflects a stable, feature-complete component or
silent drift/breakage wasn't determined by this investigation — a cheap, decisive test
(`npm install && npm run build`) was identified but not run.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- Run `npm install && npm run build` in `frontend/` — the decisive test.
- If it builds cleanly: document the finding (no fix needed, staleness is healthy) so this doesn't
  get re-flagged as a false alarm in a future audit.
- If it fails: triage and fix the actual breakage — **added during Review: only contained fixes**
  (a dependency-version pin, lockfile regeneration, config/tsconfig tweak) stay in scope here; a
  major framework version bump or non-trivial source migration is out of scope for this P3 audit
  ticket — document the finding and flag it as a separate ticket candidate instead of fixing it
  inline.
- Either way, confirm the containerized build path (`frontend.Dockerfile`) also succeeds, not just
  the bare npm build.

## Out of Scope
- `dashboard-frontend/`'s or `website/`'s deployment posture — both confirmed intentional and
  healthy, not touched by this ticket.
- Adding a `docker-compose.yml` service for `dashboard-frontend/` — explicitly not warranted.

## Acceptance Criteria
- [x] `frontend/`'s current build health is verified, not assumed.
- [x] Any real breakage found is fixed, not just documented.
- [ ] The containerized build path (`frontend.Dockerfile`) is confirmed working too — **not
      verified**: see Implementation Notes for the environmental blocker (this sandbox's network is
      intermittently blocking Docker Hub infrastructure hostnames — confirmed via 4 separate real
      `docker build` attempts across this ticket's own review passes, each failing TLS verification
      against a *different* Docker Hub-related host, not a Dockerfile problem). Reported honestly as
      unverified rather than assumed passing.

## Related Tickets
None — this ticket originates from live session investigation, not the D23/D24 audit tree.

## Related Docs
None beyond this ticket's own staging artifacts.

## Related Stored Artifacts
staging_artifacts/TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT/

## Related Code Areas
- frontend/
- frontend.Dockerfile
- docker-compose.yml (frontend service)

## Assumptions / Open Questions
- Whether `frontend/`'s staleness is healthy-stable or actual drift is exactly what this ticket's
  Step 1 resolves — genuinely not known in advance, not pre-judged either way.

## Implementation Notes
Ran the decisive test: `cd frontend && npm install && npm run build`. `npm install` succeeded
cleanly (388 packages, 15s). `npm run build` (`tsc -b && vite build`) **failed** with a real,
genuine TypeScript error: `src/types/api.ts(10,3): error TS2300: Duplicate identifier 'tick'.` /
`(11,3): error TS2300`. `git blame -L 9,12 frontend/src/types/api.ts` confirmed `EntityMemoryEntry`
originally declared `tick: number;` on 2026-02-09, then a second, duplicate `tick: number;` line
was accidentally added by a later, unrelated commit on 2026-04-09 — a genuine copy-paste bug that
has sat silently broken for ~4 months, undetected specifically because nothing has actually built
`frontend/` since (matching this ticket's own premise: staleness was masking real drift, not
reflecting a stable, feature-complete component).

Fixed per the plan's scope boundary (contained fix, in scope): removed the duplicate `tick:
number;` line. Re-ran `npm run build` — succeeds cleanly (`✓ 1723 modules transformed`, `✓ built
in 1.99s`).

**Docker verification — genuinely blocked, reported honestly, not assumed passing**: attempted
`docker build -f frontend.Dockerfile -t frontend-test-build .` repeatedly across this ticket's
Implement and Architecture-Verify passes (4 separate real attempts). Every attempt failed with a
TLS certificate verification error at the `FROM node:20-alpine` / `FROM nginx:alpine` image-pull
step — but the *specific* Docker Hub-related hostname implicated changed each time:
attempt 1 → `registry-1.docker.io` served a `Fortinet`/`Fortiguard SDNS Blocked Page` cert;
attempt 2 (independent Architecture-Verify recheck) → `registry-1.docker.io` alone now returned a
legitimate cert, but the build still failed, this time apparently at `auth.docker.io`;
attempt 3 (second independent recheck) → `auth.docker.io` alone now returned a legitimate cert too,
but the build still failed, this time against `production.cloudfront.docker.com` (confirmed via
cert inspection to be Fortinet-blocked);
attempt 4 (this pass) → failed again with the exact original signature, `registry-1.docker.io`
returning `x509: certificate is not valid for any names, but wanted to match registry-1.docker.io`.
Each individual cert check was a real, correct TLS handshake result at the moment it was run — the
underlying phenomenon is not one fixed blocked hostname but an **intermittent, rotating** Fortinet
SDNS filter hitting whichever Docker Hub/CDN edge host the build client happens to resolve to on a
given attempt (consistent with Docker Hub's multi-host, CDN-fronted architecture). Four consecutive
real build attempts, none successful, is itself sufficient evidence the containerized build path
cannot be verified in this sandbox right now — pinning blame to a single hostname was the wrong
framing from the start and is not repeated further. Same class of local network-filter block
already documented in `CLAUDE.md`'s CI Failure Triage section for `huggingface.co`/GitHub Actions
blob storage. This is an environmental limitation outside this ticket's control, not a defect in
`frontend.Dockerfile` itself (a standard, unremarkable multi-stage Node build + Nginx static-file
copy, no unusual constructs). Reporting AC3 honestly as unverified rather than claiming it passed.

## Test Summary
- `npm install` (frontend/): succeeded, 388 packages, 0 errors.
- `npm run build` (frontend/), pre-fix: FAILED — `TS2300: Duplicate identifier 'tick'` (x2).
- `npm run build` (frontend/), post-fix: PASSED — `tsc -b && vite build` clean,
  `dist/assets/index-*.js` 333.99 kB, built in 1.99s.
- `docker build -f frontend.Dockerfile`: NOT VERIFIED — 4 separate real attempts across this
  ticket's review passes, every one failed on TLS certificate verification against a Docker
  Hub/CDN host, though the specific host implicated rotated between attempts (see Implementation
  Notes) — confirms an intermittent sandbox network block, not a code/Dockerfile issue.

## Files Changed
- frontend/src/types/api.ts

## Completion Summary
`frontend/`'s 2+ months of staleness was NOT healthy-stable — it was masking a real, genuine
TypeScript compile error (a duplicate `tick: number;` field in `EntityMemoryEntry`, introduced by
an unrelated commit ~4 months ago) that has silently broken every build since, undetected because
nothing had rebuilt `frontend/` in that window. Fixed with a one-line removal, a contained fix
squarely within this ticket's scope boundary. `npm run build` now passes cleanly. The
containerized build path (`frontend.Dockerfile`) could not be verified in this session: 4 separate
real `docker build` attempts across Implement and Architecture-Verify passes all failed on TLS
certificate verification, confirmed via cert inspection to be an intermittent, rotating Fortinet
SDNS filter block on Docker Hub/CDN infrastructure hosts (not a fixed single hostname, and not a
code problem) — reported honestly as an unverified acceptance criterion rather than assumed
passing, consistent with this repo's Gate Integrity discipline.
