---
status: historical
layer: architecture
authority: P1
audience: agent
maturity: shipped
archived: 2026-08-20
tags: [architecture, engine]
---

# Epic Plan — Dead & Declared-but-Unused Infrastructure Removal

**Tracking ticket:** `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC`
**Source:** `docs/audits/D23_architecture_resilience.md` §B, §E, §I (R1); `docs/audits/D24_codebase_health_observatory.md` §B, §C, §I
**Priority:** P0 — the one finding in either audit that can take down a real subsystem for a reason unrelated to that subsystem's own function.

## Status
Resolved by `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC`. Both Problem items below now describe
pre-removal history, not current state: `pika`/`confluent-kafka` were dropped from
`pyproject.toml`, and the `rabbitmq`/`kafka`/`zookeeper` services (plus their env vars,
`depends_on` gates, and volumes) were dropped from `docker-compose.yml`. `src_legacy/`/
`tests_legacy/` were deleted, with the 3 git-tracked, load-bearing oracle `results.json` files
relocated to `tests/parity/oracles/` first (per the ticket's corrected scope — see its
Acceptance Criteria — which supersedes this plan's line 37 below, since a literal wholesale
delete would have broken `tests/integrity/test_parity_guards.py`). Left in place (not archived)
per this repo's convention that whole-epic archival is a separate human decision.

## Problem

Two independent, unrelated pieces of dead weight, both confirmed directly:

1. **RabbitMQ + Kafka are fully provisioned and health-checked, and used by zero application code.** `pyproject.toml:18-19` lists `pika>=1.3.2` and `confluent-kafka>=2.6.0` as core (non-dev) dependencies. `docker-compose.yml` provisions `rabbitmq` (with a healthcheck) and `kafka`+`zookeeper` as full services; `backend` and `ai_worker` both receive `RABBITMQ_URL`/`KAFKA_URL` env vars. A repo-wide grep for `import pika` or `confluent_kafka` returns zero results — the real event pipeline is Redis Streams only. Worse: `ai_worker` declares `depends_on: rabbitmq: condition: service_healthy` (`docker-compose.yml:70-71`) — the anomaly-detection worker's container refuses to start if RabbitMQ fails its healthcheck, despite never sending it a single byte.
2. **`src_legacy/` and `tests_legacy/` (601 files combined) contain nothing but stale compiled bytecode.** Every `.py` source file behind them has already been deleted, leaving only `.pyc` remnants of a pre-`AuthoritativeState` engine generation. Zero functional value; real risk of confusing an agent or a grep-based tool into thinking they're live code.

## Scope for the eventual `create-tickets` pass

- Un-couple `ai_worker`'s startup from RabbitMQ's healthcheck (`docker-compose.yml:70-71`) — pure risk-reduction, independent of the broader keep-or-remove decision, should land first/fastest.
- Decide the fate of RabbitMQ/Kafka: commit to a real use case and scope it properly, or remove `pika`/`confluent-kafka` from `pyproject.toml`, the `rabbitmq`/`kafka`/`zookeeper` services from `docker-compose.yml`, and all associated env vars.
- Delete `src_legacy/` + `tests_legacy/` — confirm first that these directories are safe to `git rm` (no build/tooling step still references them) before deleting.

## Out of scope

- Building a real RabbitMQ/Kafka use case, if that's the decision taken instead of removal — that would be new work tracked separately, not part of this cleanup epic.
- Any other dead-code audit beyond these two specifically-confirmed trees.

## Acceptance signal for this epic (not yet broken into child tickets)

- `ai_worker`'s container start no longer depends on RabbitMQ's healthcheck.
- Either RabbitMQ/Kafka are fully removed (deps, services, env vars) or a real use case is scoped and tracked as separate follow-on work — not left indefinitely provisioned-but-unused.
- `src_legacy/`/`tests_legacy/` no longer exist in the repo.

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic A)
- `docs/audits/D23_architecture_resilience.md` (R1, Stage 2)
- `docs/audits/D24_codebase_health_observatory.md` (§I, Phase 1 item 1)
