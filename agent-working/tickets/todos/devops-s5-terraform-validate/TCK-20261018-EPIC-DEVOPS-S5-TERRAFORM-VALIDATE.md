---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-EPIC-DEVOPS-S5-TERRAFORM-VALIDATE
phase: open
date: 2026-10-18
tags: [platform, delivery, security]
---

# TCK-20261018-EPIC-DEVOPS-S5-TERRAFORM-VALIDATE

## Title
DevOps S5 (host ubuntu): Terraform for the amendment's 5b/5c AWS shape, written and validated in CI ($0, no account, no plan, no apply)

## Status
EPIC_SCOPED

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
Epic tier: the children carry the implementation.

## Test Summary
See the child tickets.

## Files Changed
See the child tickets.

## Completion Summary
(open)
