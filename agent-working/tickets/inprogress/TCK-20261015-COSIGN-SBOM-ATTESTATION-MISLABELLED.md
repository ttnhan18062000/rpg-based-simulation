---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261015-COSIGN-SBOM-ATTESTATION-MISLABELLED
phase: inprogress
date: 2026-10-15
tags: [platform, security]
---

# TCK-20261015-COSIGN-SBOM-ATTESTATION-MISLABELLED

## Title
publish-images: the SBOM attestation fails `cosign verify-attestation --type spdxjson`; pin cosign and gate the job on verification

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
lead-planner checked the #561 images on 2026-10-15 with cosign v3.1.3. `cosign verify` passes on both published digests
(backend `154b5d5f…`, frontend `fe94ffbb…`): the identity is this repo's workflow and the entries are in Rekor, with two
claims each (`sigstore.dev/cosign/sign/v1` and `spdx.dev/Document`). But `cosign verify-attestation --type spdxjson`
fails on both with "found: …/cosign/sign/v1". Both referrers in the `sha256-<digest>` fallback index carry
`dev.sigstore.bundle.predicateType: https://sigstore.dev/cosign/sign/v1`, including the SBOM bundle, whose DSSE payload
is `https://spdx.dev/Document` (SPDX 2.3). The job summary's "How to verify" prints exactly this failing command.
cosign v2.x finds no signatures at all, because v3 stores bundles as OCI referrers. The cosign version is unpinned in
`sigstore/cosign-installer`.

## Scope
`.github/workflows/publish-images.yml`:
1. Pin the cosign binary (`cosign-release:` on cosign-installer) to the version the fix is proven on.
2. Find out why `cosign attest --type spdxjson` produces a bundle annotated `predicateType: …/cosign/sign/v1`: a known
   cosign v3 issue, a missing flag (`--new-bundle-format`, registry referrers mode, …), or the order of `attest` and `sign`.
   Fix it so `verify-attestation --type spdxjson` passes. If upstream cannot fix it, document a verification command that
   does pass and link the upstream issue.
3. After signing, add a step that runs `cosign verify` and `cosign verify-attestation --type spdxjson` on the pushed
   digest with the workflow identity, so a missing or mislabelled signature or attestation turns the job red.
4. Make "How to verify" print commands that pass, and state the minimum cosign version.

## Out of Scope
Re-signing or deleting already-published images; the next main run publishes fresh digests. Trivy gating. Any `src/**` change.
SLSA provenance (`attest-build-provenance`); that is a separate decision.

## Acceptance Criteria
- A `publish-images` run on main (or a `workflow_dispatch` on main) is green, including the new verify step (validated, CI).
- `cosign verify-attestation --type spdxjson` passes on the new digests from a clean machine with the pinned cosign
  version, and the predicate is SPDX (running locally; record the command and the output summary).
- The step summary's commands are exactly the ones validated above.
- PR runs (push: false) still skip sign/attest/verify.

## Related Tickets
TCK-20261014-IMAGE-SBOM-SCAN-SIGN (#561, introduced the step); TCK-20261014-ACTIONS-MAJORS-COMBINED.

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1: image delivery)

## Related Stored Artifacts
`agent-working/staging_artifacts/TCK-20261015-COSIGN-SBOM-ATTESTATION-MISLABELLED/`

## Related Code Areas
`.github/workflows/publish-images.yml`

## Assumptions / Open Questions
- The mislabel comes from the attest step in CI, not from lead-planner's local cosign. Both digests show it.
- Proving the fix needs a publishing run on main, which pushes new images. The user approves that merge and run.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
