---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-TERRAFORM-AWS-SKELETON
artifact_type: plan
tags: [platform, delivery, security]
---

# Plan: TCK-20261018-TERRAFORM-AWS-SKELETON

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Steps
1. Investigation: current Terraform 1.x, aws provider major, tflint aws ruleset version, trivy image already pinned in
   `publish-images.yml` (reuse its version where possible). Record versions and sources.
2. Ask for the image pulls and provider downloads (via platform-planner to lead-planner), one at a time.
3. Write `bootstrap/` and `service/` roots, `.tflint.hcl`, README, `.gitignore` lines.
4. `terraform providers lock` for linux_amd64 and darwin_arm64; commit the lock files.
5. Run fmt, init -backend=false, validate, tflint, trivy config locally in the pinned images; record outputs.
6. Delete the scratch plugin cache.

## Scope guards
No credentials, no account ids, no plan/apply. No `tests/**`.
