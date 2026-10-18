---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-IAC-WORKFLOW-AND-ROLES
artifact_type: plan
tags: [platform, delivery, security]
---

# Plan: TCK-20261018-IAC-WORKFLOW-AND-ROLES

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Steps
1. Read `publish-images.yml` for the pin style and trivy-action pin; read tests/static for workflow conventions.
2. Write `iac.yml` as scoped.
3. Roles diff, card regeneration, route and validate checks.
4. Local checks: YAML parse, `tests/static`, sessions tests, registry drift test.
5. The workflow's real proof is its run on the PR (push via lead-planner and the owner).

## Scope guards
No secrets, no plan/apply, no `test.yml`, no `tests/**`.
