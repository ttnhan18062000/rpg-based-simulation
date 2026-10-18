---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-TERRAFORM-AWS-SKELETON
phase: inprogress
date: 2026-10-18
tags: [platform, delivery, security]
---

# TCK-20261018-TERRAFORM-AWS-SKELETON

## Title
Terraform: infra/terraform bootstrap (OIDC role, budget alarm and deny action) and service (one Fargate task in the default VPC) roots, written and validated, never applied

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Amendment step 5 (5b, 5c shape) as decided by lead (D-3, 2026-10-18): write the AWS shape now, prove it only with
`fmt`, `validate`, `tflint` and `trivy config`. Nothing is planned or applied; no account exists.

## Scope
- Layout (two root modules, each self-contained):
  - `infra/terraform/bootstrap/`: GitHub OIDC provider (`token.actions.githubusercontent.com`) and one IAM role whose
    trust policy is limited to this repository and its `main` branch (variables, no defaults that name an account);
    a monthly cost budget with a notification (email from a variable, no default) and a Budgets action that attaches a
    deny policy to the deploy role when the budget is exceeded.
  - `infra/terraform/service/`: default VPC and subnets by data source; one security group (ingress on the API port from
    a CIDR variable with no default; egress all); one ECS cluster; one Fargate task definition (smallest CPU/memory;
    image from a variable such as `ghcr.io/<owner>/<repo>-backend:sha-<short>`, no `latest`); one ECS service, desired
    count 1, public IP, no load balancer; one CloudWatch log group with a short retention (1 day).
  - Each root: `versions.tf` (`required_version >= 1.11`, aws provider pinned with `~>` to a current major),
    `backend.tf` with `backend "s3" {}` (partial config) and `backend.hcl.example` showing `use_lockfile = true`
    (no bucket names), `variables.tf` with descriptions and validations where useful, `outputs.tf`.
- `.terraform.lock.hcl` per root, committed, with `linux_amd64` and `darwin_arm64` hashes
  (`terraform providers lock -platform=...`).
- `infra/terraform/.tflint.hcl`: the aws ruleset plugin pinned by version.
- `infra/terraform/README.md`: what each root would create, the evidence label "written + validated", one line that
  apply/test/destroy (5c) is a future owner decision, how to run the checks locally, and the cost notes from the
  amendment (5b about $0; 5c cents per cycle, not run).
- `.gitignore`: `.terraform/`, `*.tfstate*`, `*.tfvars` (keep `*.tfvars.example` if any), crash logs.

## Out of Scope
- `plan`, `apply`, `destroy`, any AWS credentials or account id.
- NAT gateway, ALB, EKS, Route 53, ACM.
- The workflow (`TCK-20261018-IAC-WORKFLOW-AND-ROLES`).

## Acceptance Criteria
- `terraform fmt -check -recursive` clean; `terraform init -backend=false` + `terraform validate` pass for both roots
  (**validated**, run locally in the pinned image).
- `tflint --recursive` passes with the pinned aws ruleset, or every finding is fixed or justified inline.
- `trivy config infra/terraform` runs; findings are listed in the Test Summary (report-only; none silenced without a
  reason).
- `git grep` finds no account id, access key, bucket name or real email in `infra/`.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-S5-TERRAFORM-VALIDATE`. Next: `TCK-20261018-IAC-WORKFLOW-AND-ROLES`.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D6), `docs/architecture/devops_plan_amendment_proposal.md` (step 5)

## Related Stored Artifacts
None.

## Related Code Areas
`infra/terraform/**` (new), `.gitignore`

## Assumptions / Open Questions
- Terraform version: the current 1.x release at implementation time, pinned in the image tag and in the workflow.
- The repo-scoped OIDC trust uses `repo:ttnhan18062000/rpg-based-simulation:ref:refs/heads/main` (a variable with that
  default is fine: it names a public repo, not an account).

## Implementation Notes
- Written (no downloads): `infra/terraform/bootstrap/` (GitHub OIDC provider, role trusted only for `repo:<repo>:ref:refs/heads/<branch>`, broad-on-purpose deploy permissions, monthly budget with 80 and 100 percent email notifications, deny-all policy, a Budgets-assumed role limited to attaching that one policy to the deploy role, and the `aws_budgets_budget_action`), `infra/terraform/service/` (default VPC and subnets by data source, security group with ingress/egress rules as separate resources, ECS cluster, task execution role, Fargate task 256/512, service desired 1 with a public IP, log group with 1 day retention), per-root `versions.tf` (`>= 1.11`, aws `~> 6.67.0`, which resolves to 6.67.0, a release over two weeks old on 2026-10-18), `backend.tf` (`backend "s3" {}`), `backend.hcl.example` (`use_lockfile = true`, placeholders only), `variables.tf` with validations, `outputs.tf`; `infra/terraform/.tflint.hcl` (aws ruleset 0.49.0); `infra/terraform/README.md`; `.gitignore` entries.
- Pins: Terraform 1.16.5 (2026-10-02; 1.16.6 is from 10-14); tflint v0.64.0; tflint-ruleset-aws 0.49.0; trivy v0.70.0, which is trivy-action v0.36.0's own default `version` input (action.yaml at the SHA publish-images uses), so local and CI findings match.
- D-3 (lead): the 5b plus 5c shape is written; the README says apply/test/destroy (5c) is a future owner decision. Note 5: trivy config will flag the public IP and the CIDR-variable ingress; those are listed in the Test Summary as accepted for the evidence-only skeleton.

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
