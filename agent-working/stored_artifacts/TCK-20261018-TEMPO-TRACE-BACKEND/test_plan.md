---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-TEMPO-TRACE-BACKEND
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-TEMPO-TRACE-BACKEND

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Test plan (what was run)

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1: both profiles' `config -q` pass; default profile has no Tempo; backend OTLP endpoint empty | static | config validation | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | exit 0 for both profiles | `docker compose config -q` and `docker compose --profile observability config -q` |
| AC2: Tempo up (probed as documented) and Grafana's Tempo datasource test succeeds | runtime, local | live service check | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | `/ready` returns `ready`; datasource health OK | `GET http://tempo:3200/ready` from the grafana container; `GET /api/datasources/uid/tempo/health` |
| AC3: one synthetic span found by trace id | runtime, local | end-to-end check | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | span `synthetic-span` returned for the trace id | OTLP/HTTP JSON POST to `tempo:4318/v1/traces` from the backend container; read back through Grafana's datasource proxy `/api/datasources/proxy/uid/tempo/api/traces/<id>` |
| AC5: Tempo's peak memory measured; profile fits the host | runtime, local | measurement | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | tempo 35 MiB of 512m; whole profile about 710 MiB | `docker stats --no-stream`, max of 3 samples |

## Results (from the ticket's Test Summary)
- config -q (both profiles) and YAML parse of `tempo.yaml` and `datasource.yml`: PASS.
- Runtime on 2026-10-18, local: Tempo started after the retention fix; `/ready` returned `ready`; datasource test returned "Data source is working".
- Synthetic trace `580bb4a0b429886696ebeda847e80411` was found on the first try through **Grafana's datasource proxy API**, not through the Explore UI.
- Memory: tempo 35 MiB; host available memory stayed >= 4.9 GB while up.
- Not run: the Explore UI view; trace-to-logs and trace-to-metrics links (they need rpg's R3 spans and a log field); `tests/static` and `tests/tools` (this ticket changed no Makefile or test).
