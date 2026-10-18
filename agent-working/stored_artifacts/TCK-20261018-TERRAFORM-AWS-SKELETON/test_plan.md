---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-TERRAFORM-AWS-SKELETON
artifact_type: test_plan
tags: [platform, delivery, security]
---

# Test plan: TCK-20261018-TERRAFORM-AWS-SKELETON

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| formatted | static | terraform fmt | Terraform's formatter | no diff | `terraform fmt -check -recursive infra/terraform` (pinned image) |
| valid | static | init -backend=false + validate per root | Terraform's validator | "Success!" for bootstrap and service | `terraform -chdir=infra/terraform/<root> init -backend=false && terraform -chdir=... validate` |
| lint | static | tflint with pinned aws ruleset | tflint rules | no errors | `tflint --init && tflint --recursive` |
| config scan | static | trivy config (report-only) | trivy's misconfiguration checks | runs; findings listed | `trivy config infra/terraform` (pinned image) |
| no secrets/ids | static | grep | none | no match | `git grep -n -E "[0-9]{12}|AKIA|@" infra/` (reviewed by hand) |

No `tests/**` changes (D-4).

## Results (2026-10-18)
- validated (terraform 1.16.5 in the pinned image, no credentials): `fmt -check -recursive` clean; `init -backend=false` + `validate` pass for `bootstrap` and `service`; lock files for linux_amd64 and darwin_arm64 committed.
- validated: `tflint --recursive` with the aws ruleset 0.49.0 reports no finding.
- validated: `trivy config` 0.70.0 reports 3 findings in `service/main.tf` (AWS-0104 CRITICAL, AWS-0017 LOW, AWS-0034 LOW), each accepted with its reason in the ticket's Test Summary; none in `bootstrap/`; no inline ignores.
- `git grep` finds no account id, access key, bucket name or real email in `infra/`.
