---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-IMAGE-SBOM-SCAN-SIGN
phase: open
date: 2026-10-14
tags: [platform, security]
---

# TCK-20261014-IMAGE-SBOM-SCAN-SIGN

## Title
Published images get an SBOM (syft), a report-only Trivy scan, and a keyless cosign signature

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
DevOps step 1, the supply-chain part. Each published image should come with a list of its contents, a
vulnerability report, and a signature that proves it was built by this repo's workflow.

## Scope
These steps go in `publish-images.yml`, after the push, by **digest** (never by tag), and run only on non-PR events:
- **SBOM:** `anchore/sbom-action` (syft) in SPDX-JSON, uploaded as a workflow artifact and attached to the image with
  `cosign attest --type spdxjson`.
- **Scan:** `aquasecurity/trivy-action` with `exit-code: 0` (**report-only, ADR D3**), severity at least HIGH shown in
  the job summary, and full SARIF/JSON uploaded as an artifact. On PRs, scan the locally built image the same way,
  also report-only.
- **Sign:** `sigstore/cosign-installer`, then `cosign sign --yes <image>@<digest>` (keyless, GitHub OIDC). The job
  gets `id-token: write`. No keys or secrets are stored.
- A short "how to verify" block in the job summary, giving the exact `cosign verify` command with
  `--certificate-identity-regexp` and `--certificate-oidc-issuer https://token.actions.githubusercontent.com`.

## Out of Scope
A blocking Trivy gate or a vulnerability baseline file (a later step, once a baseline exists). Uploading SARIF to
code scanning (optional; leave it out unless it is free and simple for a public repo). Signing on PRs.

## Acceptance Criteria
- After merge, `cosign verify` succeeds for both images' digests, and `cosign verify-attestation --type spdxjson`
  returns the SBOM (**published**). Record both commands and their output in the Test Summary.
- The Trivy step never fails the job. Its HIGH/CRITICAL counts are shown in the job summary, and the PR records the
  numbers as the starting baseline.
- The `security` tag means this ticket gets the Security-Review phase: no secrets, minimum `permissions`, actions
  pinned by SHA.

## Related Tickets
Depends on `TCK-20261014-PUBLISH-IMAGES-TO-GHCR`. Epic `TCK-20261014-EPIC-DEVOPS-STEP1-CONTAINERS-DELIVERY`.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D3 report-only, D7 evidence labels)

## Related Stored Artifacts
None.

## Related Code Areas
`.github/workflows/publish-images.yml`

## Assumptions / Open Questions
Signature and attestation evidence exists only after the user merges. Before that, the PR shows the PR-run scan only.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
