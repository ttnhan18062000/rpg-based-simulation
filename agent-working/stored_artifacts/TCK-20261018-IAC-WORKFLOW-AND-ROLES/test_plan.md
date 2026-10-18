---
status: historical
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

## Results (2026-10-18)
- validated (local): the secrets/plan/apply grep finds nothing; YAML parses; tests/static, the session tests and the registry tests pass; sessions validate 0 findings; route returns platform for `infra/**` and `iac.yml`.
- running on CI: the PR's own `iac.yml` run 39141316584 (PR #643, head 0673009b1): `terraform (bootstrap)` and `terraform (service)` ran fmt, `init -backend=false` and validate, all success; `tflint` ran `--init` and `--recursive`, success; `trivy config` ran, summary and artifact upload success. The downloaded trivy artifact lists 3 findings (AWS-0017 LOW, AWS-0034 LOW, AWS-0104 CRITICAL, all `service/main.tf`), identical to the local run.
- The PR's first CI run failed `tests/codebase/test_repo_root_allowlist.py` because `infra` was not an allowed repo-root entry; fixed by the owner-decided allowlist edit (commit `0104c8ceb`); the test passes locally (4 passed).
