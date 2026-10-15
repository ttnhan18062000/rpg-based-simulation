---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-10-12
tags: [architecture, observability, delivery]
---

# ADR: DevOps baseline at $0 (observability profile, image supply chain, tracing, alerting, Terraform validated)

## Status

**Accepted** by the owner on 2026-10-12, in the lead session: D1–D10 as written, alert channel **ntfy.sh** (topic name: the owner picks it at S4), run order S1 → S2 → S2b (D9) → S4 → S3 → S5, with D10 at any time. D8's `registries/session_roles.yaml` change is approved, with the literal diff shown in S1's PR. D3's later flip to blocking needs its own yes. A real AWS deploy ("2b") is not selected and stays out of scope.
**Amended 2026-10-13/14** by [`devops_plan_amendment_proposal.md`](devops_plan_amendment_proposal.md), accepted by the owner in full (decision 4 on 2026-10-13; decisions 1-3 on 2026-10-14): six steps replace S1-S5 (step 4 local Kubernetes and Helm; step 5 staged and $0-first, with one short apply/test/destroy; step 6 Argo CD deferred), and D8's paths move to the `platform` domain (#539). Where this ADR and the amendment differ, the amendment wins; D1-D7 and D9-D10 otherwise stand.
Slices start one at a time. Each slice becomes tickets in its owning domain: the lead scopes and routes, and domain implementers edit.

Origin: the owner's career plan (the personal-career session, 2026-10-11/12) asked which modern ops practices fit this repo at
**$0**. This ADR is the repo side of that plan: "P1 + 2a". A real cloud deploy ("2b") is **out of scope**. It gets its own ADR only if the
owner opens an AWS Free-plan account.

## Context (checked on `main`, 2026-10-12)

- `compose.yaml` runs nine services: backend, redis, ai_worker, frontend, prometheus, grafana, loki, promtail and watchdog.
  - It has **no `profiles:` and no memory limits**, so the observability stack starts with every `docker compose up`.
  - This VM has 9.7 GiB and was RAM-starved with the agent fleet running (see #520).
  - `watchdog` **depends on** `prometheus` and `loki`.
- The backend already serves `/health` and a Prometheus `/metrics` (`src/api/server.py`). `prometheus-client` is a runtime dependency.
  Grafana, Loki and Promtail are configured under `docker/`. There is no tracing.
- CI (`test.yml`) builds `docker/backend.Dockerfile` in a non-required job but **never publishes** the image: no registry, no login.
- The repository is **public**: standard GitHub-hosted runner minutes and public GHCR packages cost $0. The real cost is CI queue time
  (more than 1,200 workflow runs from 10-01 to 10-12), so new jobs must be path-gated.
- `docs/architecture/observability_hot_path_safety_contract.md` forbids heavy or blocking work in the simulation hot path. The HTTP layer is not
  the hot path (§5).
- Nothing deploys anywhere, and there is no cloud account or infrastructure-as-code.

## Decisions

| # | decision | why |
|---|---|---|
| D1 | **Observability becomes an opt-in compose profile.** `prometheus`, `grafana`, `loki`, `promtail` (and `tempo`, D4) get `profiles: [observability]` and a `mem_limit` each. `watchdog` joins the same profile, because it depends on two of them. Default `docker compose up` = backend, redis, ai_worker, frontend. `make` targets gain `--profile observability` where they need it. | Laptop safety. The default stack shrinks, and the full stack stays one flag away. Keeping `watchdog` in the default set would make it fail to start without its dependencies. |
| D2 | **Images publish to GHCR (public) from a new workflow**, `.github/workflows/publish-images.yml`. It runs on release tags, on `workflow_dispatch`, and on pushes to `main` that change `docker/**`, `uv.lock`, `pyproject.toml` or `frontend/package-lock.json`. It is not on every PR. It produces: an SBOM (syft, SPDX JSON, attached as an attestation), a Trivy image scan (report-only at first, SARIF uploaded), and a **keyless cosign signature** via GitHub OIDC (no stored keys). Tags: `sha-<short>`, plus the semver on release tags. No `latest`. | The CI half of CI/CD already exists. This adds the CD half plus supply-chain evidence at $0. Path gating keeps the CI queue clear. |
| D3 | **Trivy is report-only** until one measured baseline exists, then CRITICAL fails the publish job. That flip needs its own owner yes. | The same ratchet pattern as code-health gates: never start a new gate blocking on unknown debt. |
| D4 | **OpenTelemetry tracing at the API layer only.** It covers FastAPI/ASGI middleware, outbound HTTP and redis client spans. **Nothing under `src/engine/`, the kernel or the tick loop is instrumented** (hot-path contract §3/§4). It exports OTLP to a local **Grafana Tempo**, which runs in the `observability` profile with a `mem_limit`. Spans use head sampling (default 10 %, env-configurable) and are **off when the endpoint is unset**, so tests and CI see no exporter. | Closes the one real observability gap (traces) without touching determinism or tick cost. |
| D5 | **Alerting and one drill, $0.** SLOs: `/health` availability ≥ 99 % over 1 h, and API p95 latency below a threshold measured first. Rules are Grafana alert rules, provisioned as files under `docker/grafana/`. The contact point is **ntfy.sh** (no account, free), with Telegram as the alternative. A runbook in `docs/runbooks/` covers each alert. **One failure drill:** stop redis under load, observe the alert, follow the runbook, record the timeline. | On-call practice with evidence (a drill record), not just config. |
| D6 | **Terraform is written and validated, not applied.** `infra/terraform/` holds a minimal AWS shape: one small host or Lightsail instance, a security group, an S3 state backend with `use_lockfile` (Terraform ≥ 1.11; no DynamoDB) and a budget alarm. CI job `iac.yml` runs `terraform fmt -check`, `terraform validate`, `tflint` and `trivy config` on PRs that change `infra/**`. **No credentials in CI, no `plan`, no `apply`.** | It reaches the "written + validated" evidence level honestly. `plan` needs real credentials and belongs to 2b. |
| D7 | **Evidence levels are explicit.** Each slice records what it reached: *written + validated* (D6), *running locally* (D1, D4, D5), *published* (D2), and never "deployed" until 2b. | The owner's rule: claim only what is measured. |
| D9 | **One load test with an honestly measured throughput figure**, run **before S4**, because it sets D5's latency SLO threshold. k6 or Locust against the API (read endpoints and `/health`) at fixed concurrency steps, recording requests/s and p50/p95/p99 with the machine spec (CPU, RAM, host or VM) and the commit. The script lives under `tools/loadtest/` or `perf/` (owner per D8). The results are a dated record, not a gate. **It never runs in CI** (CI runners are shared and noisy) and it never drives the simulation tick: API only. | Gives a real number for interviews and the real SLO threshold. A figure without the machine spec and method would not count (D7). |
| D10 | **A one-page architecture write-up with a diagram** (`docs/architecture/system_overview.md`): services and how they talk (API, workers, redis streams, observability), where determinism lives (the 7-phase kernel), what is deliberately not distributed, and the evidence level of each ops capability (D7). The diagram is Mermaid in the markdown, so it renders on GitHub with no binary to maintain. | A reusable interview artifact; half a day. |
| D8 | **Ownership of new paths** (to be registered in `registries/session_roles.yaml` by agent-working, a governing-file edit the owner confirms): `infra/**`, `.github/workflows/publish-images.yml`, `.github/workflows/iac.yml`, `docs/runbooks/**` and `tools/loadtest/**` → **lead-planner**. D4's middleware lives in `src/api/` → **rpg-planner**. | Every touched path must have an owner before work starts. |

### Rejected or deferred

- **Kafka:** Redis Streams already exist, and adding a broker for its own sake is not justified.
- **Postgres:** run data is analytical and append-only, and DuckDB fits.
- **Pulumi:** postings name Terraform.
- **Fargate + ALB:** an always-on cost.
- **A second cloud.**
- **An always-on deploy of any kind.**
- **Docker builds of a shared search server:** see #520.
- **Kubernetes** (kind/k3s manifests) is a later, optional "P3" with no ADR here.

## Slices (each one PR, in order)

Run order chosen by the owner: S1 → S2 → S2b (D9) → S4 → S3 → S5; D10 any time.

1. **S1: showable in a day.** D1 (compose profile + mem limits + watchdog move + `make` targets) and D2 without signing (GHCR publish + SBOM + Trivy report). Evidence: a published public image with an SBOM, and `docker compose up` RSS before and after.
2. **S2:** D2's cosign keyless signing plus a `cosign verify` step documented in the README.
3. **S3:** D4 (OTel middleware in `src/api/`, Tempo in the profile, sampling, off by default) with a test that the engine imports no OTel module.
3b. **S2b: D9 load test** (before S4; it sets D5's latency threshold) and **D10** (the write-up, any time).
4. **S4:** D5 (SLO rules, the ntfy contact point, runbooks, the recorded drill).
5. **S5:** D6 (Terraform skeleton + `iac.yml`).

## Who does what

**Only the owner can:**
- accept this ADR, decision by decision;
- confirm the `session_roles.yaml` diff for D8 (a governing file);
- allow GHCR package visibility: the first publish creates the package, and the owner makes it public in GitHub settings once;
- choose the ntfy topic name, or create a Telegram bot, for D5;
- run the `--admin` merges;
- approve the later flip of D3 from report-only to blocking.

**Owning seats can do the rest:**
- the lead scopes and routes tickets and reviews the `compose.yaml`, `docker/**` and `Makefile` diffs;
- codebase-implementer can implement S1, S2, S4 and S5 under the lead's review (the precedent is #518 and #524);
- rpg implements S3 (its `src/api/` half);
- agent-working registers D8.

## Consequences

- Default `docker compose up` loses the observability stack. Anyone who wants dashboards adds `--profile observability`.
- One more workflow runs on release tags and on dependency or Docker changes, not on every PR.
- The repo gains a public image and supply-chain attestations. Signing ties images to this repository's workflow identity.
- No new runtime cost and no change to determinism: nothing in the engine changes.
