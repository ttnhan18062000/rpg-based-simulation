---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-IAC-WORKFLOW-AND-ROLES
artifact_type: investigation
tags: [platform, delivery, security]
---

# Investigation: TCK-20261018-IAC-WORKFLOW-AND-ROLES

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Findings at filing
- `publish-images.yml` pins actions by SHA with a version comment (for example `aquasecurity/trivy-action@ed142fd... #
  v0.36.0`) and uploads Trivy SARIF.
- `.github/workflows/iac.yml` and `infra/**` route to no domain on main (route.py: unowned).
- Runner label: `ubuntu-latest`, per `docs/plans/codebase_health/ubuntu_26_runner_precheck.md` (no pre-emptive pin).
