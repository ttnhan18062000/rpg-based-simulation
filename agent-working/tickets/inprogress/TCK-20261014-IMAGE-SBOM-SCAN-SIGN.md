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
INPROGRESS

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
Steps added to `publish-images.yml` after the build: Trivy (report-only, `exit-code: "0"`, HIGH/CRITICAL counts in the job summary, JSON artifact; also on PRs against the locally built image), then on non-PR events SBOM (`anchore/sbom-action`, SPDX JSON), `cosign attest --type spdxjson` and keyless `cosign sign` by digest, and a how-to-verify block. Job has `id-token: write`; no secrets; all actions SHA-pinned.
## Test Summary
- **validated:** actionlint passes.
- **published:** to be confirmed after merge: `cosign verify` / `cosign verify-attestation --type spdxjson` for both digests, plus the first Trivy HIGH/CRITICAL counts as the baseline (to be recorded here from the run).
- Security-Review: no secrets, minimum permissions, SHA pins; Trivy never fails the job.
- Security-Review note: PR runs also get `packages: write` and `id-token: write` (job-level) although they never push or sign; acceptable for same-repo PRs, and fork PRs receive a read-only token anyway. Trivy steps are `continue-on-error`, so a DB/scan error cannot skip SBOM/attest/sign; `cancel-in-progress` applies to PR runs only, so a main run cannot be cancelled between push and sign.
## Files Changed
## Completion Summary
