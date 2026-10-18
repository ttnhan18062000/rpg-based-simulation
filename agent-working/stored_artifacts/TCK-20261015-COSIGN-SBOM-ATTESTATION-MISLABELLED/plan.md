---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261015-COSIGN-SBOM-ATTESTATION-MISLABELLED
date: 2026-10-15
tags: [platform, security]
---

# Plan: TCK-20261015-COSIGN-SBOM-ATTESTATION-MISLABELLED

1. Root cause (investigation.md "To find out"): reproduce locally against the published digests with the CI cosign version.
   If possible, attest a throwaway image in a scratch registry or namespace that the user approves. Do not re-attest the
   published images.
2. Pin `cosign-release:` on cosign-installer to the version the fix is proven on (comment: why pinned, and how to bump it).
3. Fix the attest invocation (flag or version) so the SBOM referrer is labelled `https://spdx.dev/Document`. If that is
   impossible upstream, use a verification command that passes and link the upstream issue in a comment.
4. Add a "Verify signature and SBOM attestation" step after signing (`if: env.PUSH == 'true'`) that runs both verify
   commands with `--certificate-identity` pinned to this workflow's ref, or the existing regexp, and the GitHub OIDC issuer.
5. Make "How to verify" print the same commands, plus the minimum cosign version.
6. PR run: confirm sign/attest/verify are skipped. After merge: the main run is green with the verify step, then a local
   verify on the new digests (test_plan.md).

Scope guard: only `.github/workflows/publish-images.yml`. No changes to the image contents or to other workflows.
