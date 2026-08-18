---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260817-DEAD-INFRA-REMOVAL-EPIC
phase: open
date: 2026-08-17
tags: [architecture, engine]
---

# TCK-20260817-DEAD-INFRA-REMOVAL-EPIC

## Title
Remove dead & declared-but-unused infrastructure: RabbitMQ/Kafka, src_legacy/, tests_legacy/

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P0

## Request Summary
Both `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`'s source audits confirmed two independent
pieces of dead infrastructure. RabbitMQ and Kafka are fully provisioned, health-checked, and
credentialed in `docker-compose.yml`/`pyproject.toml`, but zero application code imports either
(`pika`/`confluent_kafka` — repo-wide grep, zero matches); worse, the anomaly-detection worker's
container hard-depends on RabbitMQ's healthcheck despite never sending it a byte, so a RabbitMQ
failure can take down a real subsystem for no functional reason. Separately, `src_legacy/` and
`tests_legacy/` (601 files combined) contain nothing but stale `.pyc` bytecode with no surviving
`.py` source behind them. Both audits independently rank this the single highest-priority finding
in either report — the only one that can cause a real outage for a reason unrelated to the
affected subsystem's own function.

## Scope
Full findings and evidence are in `docs/plans/dead_infra_removal_epic.md`. Concrete scope:
- Un-couple `ai_worker`'s startup from RabbitMQ's healthcheck (`docker-compose.yml:70-71`).
- Decide and record RabbitMQ/Kafka's fate: commit to a real use case and scope it properly, or
  remove `pika`/`confluent-kafka` from `pyproject.toml`, the `rabbitmq`/`kafka`/`zookeeper`
  services from `docker-compose.yml`, and associated env vars.
- Delete `src_legacy/` + `tests_legacy/` after confirming no build/tooling step references them.

## Out of Scope
- Building a real RabbitMQ/Kafka use case, if that's the eventual decision instead of removal.
- Any other dead-code audit beyond the two specifically-confirmed trees.

## Acceptance Criteria
- [ ] `ai_worker`'s container start no longer depends on RabbitMQ's healthcheck.
- [ ] Either RabbitMQ/Kafka are fully removed (deps, services, env vars) or a real use case is
      scoped and tracked as separate follow-on work — not left indefinitely provisioned-but-unused.
- [ ] `src_legacy/`/`tests_legacy/` no longer exist in the repo.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/dead_infra_removal_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md
- docs/audits/D24_codebase_health_observatory.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- docker-compose.yml
- pyproject.toml
- src_legacy/
- tests_legacy/

## Assumptions / Open Questions
- Whether there's real future intent for RabbitMQ/Kafka is an open decision for the requester —
  neither audit found evidence of one.
- Confirm `src_legacy/`/`tests_legacy/` are safe to `git rm` (no build/tooling step references
  them) before deletion — not yet independently re-verified beyond the source audits' own checks.
- **Downgraded from epic to standard tier (2026-08-18):** originally created as one of 10
  sub-epics under `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`, but on review this doesn't meet
  the "large multi-ticket initiative" bar — it's 2-3 related, mostly mechanical changes that fit
  one standard ticket's own Investigate→Plan→Implement→Test→Parity→Verify pipeline. `staging_artifacts/TCK-20260817-DEAD-INFRA-REMOVAL-EPIC/` (investigation.md, plan.md, test_plan.md) is still required before implementation, per standard-tier Definition of Done, and has not been created yet.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
