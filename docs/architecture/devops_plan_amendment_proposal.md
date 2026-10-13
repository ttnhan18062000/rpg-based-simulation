---
status: active
layer: architecture
authority: P2
audience: developer
date: 2026-10-13
tags: [architecture, observability, delivery, documentation]
---

# Proposal: DevOps plan, amendment 1 (study now, real project later)

**Status: Proposed, not accepted.** This proposes changes to `devops_baseline_adr.md` (accepted 2026-10-12). Nothing
here takes effect until the owner accepts it. The review is `lead-planner`'s (`docs/architecture/**`).
Written by `lead-planner-u24` on the owner's request, 2026-10-13.

## Why amend

- **The goal is set by the owner.** The owner is not aiming to become a DevOps engineer. The aim is to use and explain each
  piece from hands-on work in this project. Small, standard tools stay in, because this project may later become a real
  product.
- **Job-market input.** `career-prepare` read the 2026-10-12 scan (keyword shares across 936 DevOps/SRE/platform/infra
  postings, not requirements): Kubernetes 50 %, incident/on-call 44 %, AWS 43 %, Terraform 31 %, Grafana and Prometheus about
  14 %, OIDC/IAM 10 %, OpenTelemetry 3 %, cosign and load-test tools 0 %.
- **Nothing drives the ADR.** The plan was accepted on 2026-10-12. Since then only D10 (`system_overview.md`) has landed,
  and S1 is in progress. The lead seats cannot dispatch, and the new paths need an owner who can (see "Who does the work").
- **A VPS teaches little cloud.** A permanent VPS teaches Linux and Kubernetes, not cloud-provider skills (IAM, networking,
  managed services, Terraform against real APIs). A short-lived real AWS deploy, destroyed afterwards, teaches those at
  almost no cost.

## What stays from the ADR

- **D1-D10 still apply**, apart from the run-order and scope changes below. These are unchanged:
  - tracing at the API layer only, with the engine never instrumented (D4);
  - Trivy report-only until a baseline exists (D3);
  - explicit evidence levels (D7).
- **The engine stays one process with one writer.** Determinism and replay depend on it. Kubernetes runs it as a single
  replica; only the API and workers could scale.
- **No always-on paid deployment.**
- **No Postgres, Kafka, OpenSearch, chaos tooling or policy-as-code.** Postgres and Kafka have no fit. The rest either
  duplicate what we have or are too specialised.

## The plan: 6 steps, one PR each (step 6 optional)

| # | Step | Tools | What it shows / teaches | ADR link |
|---|---|---|---|---|
| 1 | **Containers and delivery** | Docker, Compose, GitHub Actions, GHCR, syft, Trivy, cosign, Dependabot | The observability profile is optional, with memory limits and health checks. Images are published with an SBOM, a scan and a keyless signature, and dependency and image pins are bumped by PR | S1 + S2, plus Dependabot (new) |
| 2 | **Observability** | Prometheus, Grafana, Loki, OpenTelemetry, Tempo | One API dashboard (metrics and logs) and one request trace; the engine imports no tracing code | S3, kept small |
| 3 | **Operate** | Locust, Grafana alerting, ntfy | A measured req/s and p95; one SLO alert; a runbook; one drill (stop Redis under load), recording detection time, recovery time and a short post-mortem | S2b + S4 (Locust instead of k6) |
| 4 | **Kubernetes locally** | kind, kubectl, Helm, kubeconform | Plain manifests first (Deployment, Service, probes, limits, rollout), then a Helm chart; the chart is checked in CI (kubeconform plus a `kind` smoke test) | **new** (the ADR deferred Kubernetes) |
| 5 | **Cloud once** | Terraform, AWS, GitHub OIDC | Terraform creates a small AWS setup (IAM through OIDC with no stored keys, one container service, a budget alarm). We apply it, test it, then `terraform destroy` it, and keep the dated evidence | S5 extended: **short-lived apply/destroy** (the ADR said validate only) |
| 6 | *(optional)* **GitOps** | Argo CD | Argo CD syncs the step-4 chart into the local cluster | **new** |

Evidence labels follow D7: "running locally", "published", "validated", and "measured" only where a number was recorded.
After step 5 the label is "deployed to AWS, then torn down". It is never just "deployed".

**Cost:** $0, except step 5, which is a few dollars per apply/destroy cycle and is covered by new-account credits and
capped by a budget alarm.

**When the project goes live:** steps 4-6 are already the deploy path. Pointing the chart and Terraform at real hosting
then needs its own ADR, covering hosting choice, budget and secrets.

## End state

- **Delivery:** one pipeline from commit to tested, scanned, signed image, then to Kubernetes.
- **Observability:** metrics, logs and traces, with one SLO alert tied to a runbook and a recorded drill.
- **Infrastructure:** written as code, applied once to real AWS and destroyed.
- **Ops table:** every row in `system_overview.md`'s ops table reaches a measured level.

## Who does the work

### Paths and their owners

| Paths | Owner today | Proposed owner |
|---|---|---|
| `compose.yaml`, `docker/**` | lead | platform |
| `infra/**`, `docs/runbooks/**`, `tools/loadtest/**`, `.github/workflows/publish-images.yml`, `.github/workflows/iac.yml` (all D8) | lead (D8) | platform |
| `deploy/k8s/**`, `charts/**`, `.github/workflows/k8s-validate.yml`, `.github/dependabot.yml` | none (new paths) | platform |
| `.github/workflows/rpg-gate-report.yml` | none | rpg (proposed) |
| OTel middleware in `src/api/` | rpg | rpg |

The lead seats can't dispatch, so the D8 paths have nobody to drive them. The new paths have no owner at all.

### Recommendation: register a `platform` domain, staffed on demand

- **Seats:** `platform-planner` and `platform-implementer`. It owns the "platform" rows above. It runs only while a step is
  open and pauses afterwards.
- **Setup:** one edit to `registries/session_roles.yaml`, a governing file, so the owner confirms the literal diff.
  `agent-working` implements the edit.
- **Why a domain:** one edit gives the paths an owner and a planner able to dispatch, which also suits the "real project
  later" goal.

### Alternative: no new domain

- The owner dispatches `codebase-implementer` step by step, which is the ADR's original route, and `lead-planner` reviews.
- **Costs less, but:** nothing drives the plan, and the new Kubernetes paths still need an owner registered somewhere.

### Other sessions involved in either case

| Session | Part |
|---|---|
| `rpg-planner` → `rpg-implementer` | Step 2's middleware in `src/api/` |
| `agent-working-planner` → `agent-working-implementer` | Registers the domain and path owners |
| `testing-planner` | Consulted if any job lands in `test.yml`; new CI work goes in its own workflow files |
| `lead-planner` | Reviews this amendment and each step's PR |

## Owner decisions

1. Accept the step order 1-6 in place of S1 → S2 → S2b → S4 → S3 → S5.
2. Add step 4 (local Kubernetes and Helm) and the optional step 6 (Argo CD).
3. Allow step 5's short-lived `terraform apply`/`destroy` on AWS under a budget alarm.
4. Choose who does the work: the `platform` domain (recommended) or `codebase-implementer`.
