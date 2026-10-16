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
INPROGRESS

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
- **Root cause (evidence, not a full upstream trace):** CI's cosign-installer v4.1.2 defaults to cosign **v3.0.6** (the `Install cosign` step log of main run 38719666196 prints `cosign-release: v3.0.6`). The v3.0.6 `attest` published the SBOM referrer annotated `dev.sigstore.bundle.predicateType: https://sigstore.dev/cosign/sign/v1` (both referrers of the published backend digest `154b5d5f…` carry that label). A local `attest` + `sign` with **v3.1.3** on a scratch image labels the SBOM referrer `https://spdx.dev/Document` and the sign referrer `sign/v1`, and `verify-attestation --type spdxjson` passes. Release notes show v3.1.2 touching predicate-type validation for the new bundle format and v3.0.6 changing the referrer-writing path, but I did not trace the exact upstream commit, so the cause is "fixed between v3.0.6 and v3.1.3", not a named bug.
- `publish-images.yml`: `cosign-release: v3.1.3` on cosign-installer (comment says why and how to bump); new step "Verify signature and SBOM attestation" after signing runs `cosign verify` and `cosign verify-attestation --type spdxjson` with the workflow identity regexp and the GitHub OIDC issuer under `set -euo pipefail`, so a missing or mislabelled attestation turns the job red; "How to verify" prints the same two commands plus "needs cosign v3.1.3 or later". The published images were not touched or re-attested.
- Correction: my earlier session note that `verify-attestation` passed (exit 0) for the #561 digests was wrong; it fails, as lead-planner reported.

## Test Summary
- **running locally (reproduction, read-only, cosign v3.1.3):** `cosign verify` on backend `154b5d5f…` exits 0; `cosign verify-attestation --type spdxjson` on the same digest exits 1: `none of the attestations matched the predicate type: spdxjson, found: https://sigstore.dev/cosign/sign/v1`. This is test_plan check 4 (the verify step fails on the current mislabelled digests).
- **running locally (scratch image, local stand-in registry on localhost:5055, keyed, `--use-signing-config=false --tlog-upload=false`, cosign v3.1.3):** referrer 1 (attest) `https://spdx.dev/Document`, referrer 2 (sign) `https://sigstore.dev/cosign/sign/v1`; `cosign verify-attestation --key cosign.pub --type spdxjson --insecure-ignore-tlog=true` exits 0. Limits: keyed, no Rekor, one tiny image; the keyless/GitHub-OIDC path is proved only by the main run below. The cosign v3.0.6 comparison on the scratch image could not be run (the binary download failed and Docker Hub pulls fail here on a TLS error).
- **validated (static):** `actionlint` on the workflow is clean; the YAML parses. No test in `tests/` references publish-images.
- **Not yet observed (post-merge, ticket stays INPROGRESS):** the main publish run is green with the verify step; `verify` and `verify-attestation --type spdxjson` pass from a clean machine on the new digests; the step summary shows the same commands. If the main run's verify step fails, the pin does not fix it under keyless: record that and reopen the investigation.
- PR runs (push: false) skip the sign, attest and verify steps (all gated on `env.PUSH == 'true'`); confirm on this PR's run.

## Files Changed
- `.github/workflows/publish-images.yml`

## Completion Summary
