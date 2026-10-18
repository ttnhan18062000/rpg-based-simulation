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
