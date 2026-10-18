---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, delivery, security]
---

# infra/terraform

Evidence label: **written + validated**. This is a minimal AWS shape (ADR D6, amendment step 5b plus 5c) that is written and proven only with `terraform fmt`, `init -backend=false` + `validate`, `tflint` and `trivy config`. Nothing is planned, applied or destroyed; no AWS account, credential or bucket name is in this repository. Apply, test and destroy (5c) is a future owner decision.

## What each root would create

| Root | Creates |
|---|---|
| `bootstrap/` | the GitHub OIDC identity provider; one IAM role that only this repository's `main` branch can assume (variables, no account in any default); a monthly cost budget with an email notification at 80 and 100 percent; a Budgets action that attaches a deny-all policy to the deploy role when the budget is exceeded |
| `service/` | in the default VPC: one security group (the API port from one CIDR variable, all egress); one ECS cluster; one Fargate task definition (256 CPU, 512 MiB) running a GHCR backend image given by a variable (an explicit tag, never `latest`); one ECS service with desired count 1 and a public IP, no load balancer; one CloudWatch log group with one day of retention |

Not created: NAT gateway, load balancer, EKS, Route 53, ACM.

## Files in each root

`versions.tf` (`required_version >= 1.11`, aws provider `~> 6.67.0`), `backend.tf` (an empty `backend "s3" {}`), `backend.hcl.example` (shape only, with `use_lockfile = true` and no real names), `variables.tf`, `main.tf`, `outputs.tf`, and a committed `.terraform.lock.hcl` with `linux_amd64` and `darwin_arm64` hashes.

## Run the checks locally

From the repository root, with Terraform 1.16.5 (pinned the same way as `.github/workflows/iac.yml`):

```
terraform -chdir=infra/terraform/bootstrap fmt -check -recursive
terraform -chdir=infra/terraform/bootstrap init -backend=false && terraform -chdir=infra/terraform/bootstrap validate
terraform -chdir=infra/terraform/service init -backend=false && terraform -chdir=infra/terraform/service validate
(cd infra/terraform && tflint --init && tflint --recursive)
trivy config infra/terraform
```

`init` downloads the aws provider (about 180 MB); set `TF_PLUGIN_CACHE_DIR` to a scratch directory to share it between the roots.

## Cost notes (amendment step 5)

5b (this evidence): about $0, since nothing is created. 5c (not run): a few cents per apply, test and destroy cycle of one Fargate task, with no NAT gateway or load balancer.

**Limit of the cost cap:** the Budgets action attaches a deny-all policy to the deploy role. That stops further deploys but does not stop an already-running Fargate task; stopping or destroying it then needs an admin.

## Deploy role scope

The bootstrap deploy role is scoped so it cannot escalate: it manages only roles named `<name_prefix>-task-*`, attaches only `AmazonECSTaskExecutionRolePolicy` to them, passes them only to `ecs-tasks.amazonaws.com`, and touches only log groups under `/<name_prefix>/`. `ecs:*` and the `ec2` actions are still on `"*"` for this evidence-only skeleton and must be scoped before any apply. Use the same `name_prefix` in both roots.
