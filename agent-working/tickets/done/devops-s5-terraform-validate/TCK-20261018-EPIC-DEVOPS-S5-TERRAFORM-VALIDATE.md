---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-EPIC-DEVOPS-S5-TERRAFORM-VALIDATE
phase: done
date: 2026-10-18
tags: [platform, delivery, security]
---

# TCK-20261018-EPIC-DEVOPS-S5-TERRAFORM-VALIDATE

## Title
DevOps S5 (host ubuntu): Terraform for the amendment's 5b/5c AWS shape, written and validated in CI ($0, no account, no plan, no apply)

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Owner decision (2026-10-18, relayed by lead-planner): after S4, write Terraform per `devops_baseline_adr.md` D6 and the
amendment's step 5. CI checks only: $0, no cloud account, no credentials, no `plan`, no `apply`. Lead's review answers:
- **D-2:** CI runs `terraform fmt -check`, `terraform validate`, `tflint` (amendment 5a, ADR D6) and `trivy config`
  (ADR D6), with trivy config **report-only first**, like the image scan (D3). All tools pinned.
- **D-3:** write the 5b and 5c shape (S3 backend with `use_lockfile` and partial config; GitHub OIDC provider and role;
  budget alarm plus Budgets deny action; one Fargate service in the default VPC pulling the public GHCR image, no NAT,
  ALB or EKS). Evidence label **"written + validated"**. Apply/test/destroy (5c) stays a future owner decision.
- **D8:** register the new paths (`infra/**`, `.github/workflows/iac.yml`) to platform in the same PR; the owner confirms.

## Scope
Two children, in `SEQUENCE.md` order:
1. `TCK-20261018-TERRAFORM-AWS-SKELETON`: `infra/terraform/` (bootstrap and service roots), lock file, tflint config, README.
2. `TCK-20261018-IAC-WORKFLOW-AND-ROLES`: `.github/workflows/iac.yml` and the roles diff.

## Out of Scope
- `terraform plan`/`apply`/`destroy`, any AWS account or credentials (5c is a future owner decision).
- Kubernetes/Helm (step 4), Argo CD (step 6).
- Edits to `test.yml` (testing's) or `tests/**` (rpg's).

## Acceptance Criteria
- Both children DONE, one PR from `platform-implementer-local-terraform-validate`, after S4's PR merges.
- The PR's CI shows `iac.yml` running all four checks green (trivy config report-only, findings listed).
- Evidence label in every doc and the PR: "written + validated". Never "deployed".

## Related Tickets
S4: `TCK-20261018-EPIC-DEVOPS-S4-BASE-ALERTS-LOCAL` (lands first). Issue #618.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D6, D7, D8), `docs/architecture/devops_plan_amendment_proposal.md` (step 5)

## Related Stored Artifacts
None.

## Related Code Areas
`infra/terraform/**` (new), `.github/workflows/iac.yml` (new), `registries/session_roles.yaml`

## Assumptions / Open Questions
- Local runs use a pinned `hashicorp/terraform` image (and pinned tflint/trivy images) with a scratch plugin cache; the
  provider and plugin downloads are asked of lead-planner first, one at a time, and the cache is deleted afterwards.

## Implementation Notes
Epic tier: the children carry the implementation: `TCK-20261018-TERRAFORM-AWS-SKELETON` and `TCK-20261018-IAC-WORKFLOW-AND-ROLES` (both done, one branch `platform-implementer-local-terraform-validate`, PR #643).

## Test Summary
See the child tickets. Labels (ADR D7): **written + validated** (fmt, init -backend=false + validate, tflint and trivy config, locally in pinned images and on CI in run 39141316584). Nothing was planned or applied.

## Files Changed
`infra/terraform/**` (new), `.github/workflows/iac.yml` (new), `registries/session_roles.yaml` and the platform session cards, `docs/guidelines/repo_tooling_layout.md` (one line), `.gitignore`, the two child tickets and their stored artifacts.

## Completion Summary
Both children are done on `platform-implementer-local-terraform-validate`. The AWS shape (a GitHub OIDC deploy role scoped against escalation, a budget with a deny-all action, and one Fargate task in the default VPC) is written and proven only with `terraform fmt`, `init -backend=false` + `validate`, `tflint` and `trivy config`, locally and on CI (run 39141316584: every step of both terraform legs, tflint and trivy ran and succeeded; the CI trivy artifact lists the same 3 findings as the local run). Nothing was planned, applied or destroyed, and no AWS account, credential or bucket name exists in the repository. Apply, test and destroy (5c) is a future owner decision.

Owner decisions recorded here: the roles diff (`infra/**` and `iac.yml` to platform, D8), confirmed at the merge question; and `infra` as an allowed repo-root directory (2026-10-18, via lead), with the one-line allowlist edit assigned as a one-off.

Stated limits: `Resource "*"` remains on `ecs:*`, the ec2 describe and security-group actions and `logs:DescribeLogGroups` (plus the deny-all, correctly `*`), to be scoped before any apply; the security group's unrestricted egress (trivy AWS-0104 CRITICAL) is needed to pull the image from GHCR over the public IP with no NAT and is narrowed before any apply; trivy stays report-only; the Budgets deny-all stops further deploys but not a running Fargate task.
Knowledge index refreshed by lead-planner in the main checkout after merge.
