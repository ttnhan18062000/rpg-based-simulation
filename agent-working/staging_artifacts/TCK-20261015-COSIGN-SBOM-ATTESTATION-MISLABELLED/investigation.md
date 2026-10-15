---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261015-COSIGN-SBOM-ATTESTATION-MISLABELLED
date: 2026-10-15
tags: [platform, security]
---

# Investigation: TCK-20261015-COSIGN-SBOM-ATTESTATION-MISLABELLED

## Known (lead-planner, 2026-10-15, cosign v3.1.3 on u24desktop)
- `cosign verify` passes on backend `154b5d5f…` and frontend `fe94ffbb…` (published by #561): identity is this repo's
  workflow, entries in Rekor, claims `https://sigstore.dev/cosign/sign/v1` and `https://spdx.dev/Document`.
- `cosign verify-attestation --type spdxjson` fails with "found: …/cosign/sign/v1".
- The registry's `sha256-<digest>` fallback index has two referrers, both annotated
  `dev.sigstore.bundle.predicateType: https://sigstore.dev/cosign/sign/v1`. The large one (backend 3.4 MB, frontend 1.4 MB)
  has a DSSE payload with predicateType `https://spdx.dev/Document` (SPDX 2.3, 129 packages on backend).
- cosign v2.x finds no signatures, because the v3 bundle format is stored as OCI referrers.

## Current workflow (`.github/workflows/publish-images.yml`, main)
- `sigstore/cosign-installer@6f9f177… # v4.1.2` with no `cosign-release:`, so the cosign version floats.
- `cosign attest --yes --type spdxjson --predicate sbom-<image>.spdx.json "$REF"`, then `cosign sign --yes "$REF"`.
- "How to verify" echoes `cosign verify …` and `cosign verify-attestation --type spdxjson …` with
  `--certificate-identity-regexp '^https://github.com/<repo>/'`.

## To find out (implementer)
- Which cosign version CI actually ran (the step log of the #561 publish run).
- Upstream: a cosign v3 issue or fix for the referrer annotation on `attest`; flags controlling the bundle format and
  the referrers fallback.
- Whether `verify-attestation` in v3 reads the annotation or the DSSE payload, and whether a newer v3 fixes either side.
