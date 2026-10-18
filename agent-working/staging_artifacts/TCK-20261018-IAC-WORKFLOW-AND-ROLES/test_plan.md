---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-IAC-WORKFLOW-AND-ROLES
artifact_type: test_plan
tags: [platform, delivery, security]
---

# Test plan: TCK-20261018-IAC-WORKFLOW-AND-ROLES

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| workflow runs green on the PR | validated (CI) | the PR's own iac.yml run | GitHub Actions | all steps pass; trivy reports | `gh pr checks <PR>`; read the run's steps and job summary |
| no credentials, no plan/apply | static | grep | none: criterion from the ticket AC | no match | `grep -n -E "secrets\.|terraform (plan|apply|destroy)" .github/workflows/iac.yml` |
| workflow conventions | static | tests/static | the existing static tests | pass | `.venv/bin/python3 -m pytest tests/static -q --basetemp=<own>` |
| roles diff | static | route + validate | tools/sessions | platform for both paths; 0 findings | `python3 -m tools.sessions.route infra/terraform/README.md`; `... route .github/workflows/iac.yml`; `tools/sessions/validate.py` |

No `tests/**` changes (D-4).
