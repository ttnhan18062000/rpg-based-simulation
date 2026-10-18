---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-TERRAFORM-AWS-SKELETON
artifact_type: investigation
tags: [platform, delivery, security]
---

# Investigation: TCK-20261018-TERRAFORM-AWS-SKELETON

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Findings at filing
- ADR D6: `infra/terraform/` minimal AWS shape, S3 backend with `use_lockfile` (Terraform >= 1.11, no DynamoDB), budget
  alarm; CI `iac.yml` runs fmt, validate, tflint, trivy config; no credentials, no plan, no apply.
- Amendment step 5: 5a ($0) fmt/validate/tflint; 5b (about $0) GitHub OIDC role, budget alarm, Budgets deny-all action;
  5c (cents, manual) apply/test/destroy of one small container service from public GHCR, no NAT/ALB/EKS. Lead D-3:
  write 5b+5c, validate only.
- `infra/**` routes to no domain on main (route.py: unowned); `TCK-20261018-IAC-WORKFLOW-AND-ROLES` registers it.
- Images on GHCR are tagged `sha-<short>` and semver, never `latest` (ADR D2).

## To confirm during the work
- Budgets action target for a standalone account (IAM policy attachment to the deploy role, not an SCP).
- Smallest valid Fargate CPU/memory pair for the backend image.

## Implementer findings (2026-10-18)
- Versions resolved from registries and the GitHub API without downloads: Terraform 1.16.5 (published 2026-10-02) in `hashicorp/terraform@sha256:c7926fea...`; aws provider constraint `~> 6.67.0` (6.67.0 from 2026-09-30); tflint v0.64.0 (2026-07-17); tflint-ruleset-aws 0.49.0 (2026-09-19); setup-terraform v4.0.1, setup-tflint v6.3.2.
- **Trivy version:** `aquasecurity/trivy-action@ed142fd0...` (v0.36.0, the pin publish-images already uses) has `version` input default `v0.70.0` (trivy v0.70.0, released 2026-04-17). Local runs and `iac.yml` both use 0.70.0 (iac.yml passes it explicitly), so local and CI findings match; it is older than two weeks. The image is `ghcr.io/aquasecurity/trivy:0.70.0@sha256:be1190afcb28352bfddc4ddeb71470835d16462af68d310f9f4bca710961a41e`, about 58.5 MB compressed.
- `terraform fmt -check -recursive` passed in the pinned image before any provider download (exit 0).
- Budgets action target: for a standalone account the action attaches an IAM policy (deny-all) to the deploy role, using a dedicated role that `budgets.amazonaws.com` assumes, limited to `iam:AttachRolePolicy/DetachRolePolicy` on that role with the `iam:PolicyARN` condition (no SCP).
