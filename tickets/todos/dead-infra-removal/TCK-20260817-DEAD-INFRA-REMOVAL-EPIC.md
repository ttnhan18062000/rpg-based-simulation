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
EPIC_SCOPED

## Tier
epic

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
- Scope-only epic: full findings, evidence, and proposed remediation steps are in
  `docs/plans/dead_infra_removal_epic.md`. Detailed, investigated child tickets are not created
  yet — this ticket tracks prioritization only, per explicit instruction.
- When work begins: run `create-tickets` against a proposal document scoped to this epic's items
  (un-couple `ai_worker` startup from RabbitMQ; decide keep-vs-remove for RabbitMQ/Kafka; delete
  `src_legacy/`/`tests_legacy/`), producing investigated child tickets in
  `tickets/todos/dead-infra-removal/`.

## Out of Scope
- Building a real RabbitMQ/Kafka use case, if that's the eventual decision instead of removal.
- Any other dead-code audit beyond the two specifically-confirmed trees.

## Acceptance Criteria
- [ ] `docs/plans/dead_infra_removal_epic.md` is reviewed and its scope confirmed accurate.
- [ ] A decision is made (and tracked) on whether to build or remove RabbitMQ/Kafka.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

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

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
