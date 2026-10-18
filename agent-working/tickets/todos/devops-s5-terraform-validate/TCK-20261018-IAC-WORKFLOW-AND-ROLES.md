---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-IAC-WORKFLOW-AND-ROLES
phase: open
date: 2026-10-18
tags: [platform, delivery, security]
---

# TCK-20261018-IAC-WORKFLOW-AND-ROLES

## Title
CI: .github/workflows/iac.yml (fmt, validate, tflint, trivy config report-only; no credentials) and the D8 roles diff for infra/** and iac.yml

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
ADR D6/D8 and lead's D-2: a path-gated workflow proves the Terraform on every PR that touches it, at $0 and with no
credentials. The new paths get an owner in the same PR.

## Scope
- `.github/workflows/iac.yml`:
  - on `pull_request` and `push` to `main` with `paths: ["infra/**", ".github/workflows/iac.yml"]`, plus
    `workflow_dispatch`;
  - `permissions: contents: read` at the top (add `security-events: write` only on the job that uploads SARIF, if
    SARIF is uploaded like `publish-images.yml`);
  - `runs-on: ubuntu-latest` (precheck decision: no pre-emptive pin);
  - actions pinned by SHA with a version comment, like `publish-images.yml` (`hashicorp/setup-terraform`, the tflint
    setup action, `aquasecurity/trivy-action` at the same pin as publish-images unless newer is needed);
  - Terraform and tflint versions pinned;
  - steps: `terraform fmt -check -recursive`; per root (matrix `bootstrap`, `service`): `init -backend=false`,
    `validate`; `tflint --init` + `tflint --recursive`; `trivy config` with `exit-code: 0` (report-only), results in
    the job summary (and SARIF if uploaded);
  - no `secrets.*`, no `env` with credentials, no `plan`, `apply` or `destroy` anywhere.
- `registries/session_roles.yaml`: add `infra/**` and `.github/workflows/iac.yml` to platform's `owns`; regenerate the
  cards with `tools/sessions/generate_agents.py`; `python3 -m tools.sessions.route` returns platform for both.
- The PR body asks the owner to confirm the roles diff (D8), states "written + validated", and lists trivy config's
  findings as the baseline (the flip to blocking needs its own owner yes, as D3).

## Out of Scope
- Blocking on trivy findings. Any cloud credentials or OIDC use in CI. `test.yml`.

## Acceptance Criteria
- The PR's own CI runs `iac.yml` (path match) and all steps pass; trivy config reports without failing.
- `grep -n -E "secrets\.|terraform (plan|apply|destroy)" .github/workflows/iac.yml` finds nothing.
- `tests/static` passes (it covers workflow conventions); `tools/sessions/validate.py` reports 0 findings.
- The roles diff moves exactly the two new globs.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-S5-TERRAFORM-VALIDATE`. Needs `TCK-20261018-TERRAFORM-AWS-SKELETON`. Runner decision: `TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24`.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D3, D6, D8), `docs/plans/codebase_health/ubuntu_26_runner_precheck.md`

## Related Stored Artifacts
None.

## Related Code Areas
`.github/workflows/iac.yml` (new), `registries/session_roles.yaml`, generated session cards

## Assumptions / Open Questions
- If `tests/static` has a workflow rule this file breaks (for example an allowlist of workflow files), stop and report
  to platform-planner: the fix may be in rpg's or testing's files.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
