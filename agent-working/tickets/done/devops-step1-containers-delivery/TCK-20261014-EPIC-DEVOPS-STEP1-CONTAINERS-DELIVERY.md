---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-EPIC-DEVOPS-STEP1-CONTAINERS-DELIVERY
phase: done
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-EPIC-DEVOPS-STEP1-CONTAINERS-DELIVERY

## Title
DevOps step 1: containers and delivery (compose profile and limits, GHCR publish, SBOM, Trivy report-only, cosign, Dependabot)

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Step 1 of the DevOps plan (`docs/architecture/devops_plan_amendment_proposal.md`, PR #537). On 2026-10-14 the owner
accepted owner decision 1 (step order 1-6) and chose to **rebuild** T1 (compose profile) and T2 (publish-images.yml)
here instead of pushing the parked `devops-s1` work (codebase, local `7e604d3fa`, ubuntu host). The plan's T3 is
redone as a platform `owns` line (child 5).

## Scope
One PR, five child tickets, in the order given in `SEQUENCE.md`:

1. `TCK-20261014-COMPOSE-OBSERVABILITY-PROFILE-AND-LIMITS`: an optional observability profile, memory limits, and working health checks.
2. `TCK-20261014-PUBLISH-IMAGES-TO-GHCR`: build the backend and frontend images and push them to GHCR.
3. `TCK-20261014-IMAGE-SBOM-SCAN-SIGN`: syft SBOM, Trivy report-only scan, cosign keyless signature.
4. `TCK-20261014-DEPENDABOT-AND-BASE-IMAGE-PINS`: `.github/dependabot.yml`; base images pinned by digest; `npm ci`.
5. `TCK-20261014-PLATFORM-OWNS-STEP1-PATHS`: register the two new paths to the platform domain.

## Out of Scope
- Anything under `src/**` (rpg-planner). That includes the ai_worker metrics port, which waits on
  `TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS`.
- `.github/workflows/test.yml` (testing-planner).
- Steps 2-6 (Grafana API dashboard, OTel/Tempo, Locust, k8s/Helm, Terraform, Argo CD).
- Postgres, Kafka, OpenSearch, chaos tooling, policy-as-code (ADR exclusions).
- Making Trivy blocking (it stays report-only until a baseline exists, per ADR D3).

## Acceptance Criteria
- All five child tickets are DONE and land in a single PR.
- The PR's evidence uses only the D7 labels: "running locally" (compose), "published" (GHCR images, SBOM, Trivy report,
  signature), "validated" (config checks). Nothing is described as "deployed".
- Cost stays $0. The repo is public, so GHCR storage and Actions minutes are free.

## Related Tickets
- `TCK-20261013-PLATFORM-DOMAIN-SEATS` (#539): created the platform domain.
- Issue #541: accepted inputs for later steps.
- `TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK`, `TCK-20261008-OPS-FILES-INTO-DOCKER-DIR`: current Dockerfile shape.

## Related Docs
- `docs/architecture/devops_plan_amendment_proposal.md` (PR #537), `docs/architecture/devops_baseline_adr.md` (D3, D7, D8)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`, `docker/**`, `.github/workflows/publish-images.yml` (new), `.github/dependabot.yml` (new), `registries/session_roles.yaml`

## Assumptions / Open Questions
- **Layer and tag registration:** the `platform` layer and tag are not registered yet, and platform-planner cannot
  write `registries/**`. platform-implementer registers them first (see `SEQUENCE.md` step 0).
- **Disk:** the repo filesystem has about 4.6 GB free. Full image builds run in Actions; local work stays with
  `docker compose config` plus starting the default profile.

## Implementation Notes
Epic tier: the children carry the implementation.

## Test Summary
See the child tickets.

## Files Changed
See the child tickets.

## Completion Summary
All five children plus the follow-up `TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS` are done. Step 1 shipped in #561 (7fa1fc7bc); images are published and verified (cosign verify and verify-attestation on both digests), Trivy baseline recorded in `TCK-20261014-IMAGE-SBOM-SCAN-SIGN`.
(open)
