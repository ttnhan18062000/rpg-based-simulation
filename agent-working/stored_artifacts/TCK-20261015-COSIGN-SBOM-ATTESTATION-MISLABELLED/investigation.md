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

## Findings (2026-10-16, platform-implementer)
- CI ran cosign **v3.0.6**: the installer's default (`cosign-release: v3.0.6` in the main run 38719666196 step log). Local `cosign v3.1.3` on the same published digest fails `verify-attestation` with `found: .../sign/v1`.
- Both referrers of the published backend digest carry `predicateType: .../cosign/sign/v1`. A scratch attest + sign with v3.1.3 gives `https://spdx.dev/Document` for the attest referrer and `sign/v1` for the sign referrer, and `verify-attestation --type spdxjson` passes. Exact upstream commit not traced (v3.0.6 and v3.1.2 release notes mention referrer-writing and predicate-type fixes). v3.1.3 is the latest cosign release (2026-08-06).
- Not reproducible here: v3.0.6 on the scratch image (binary download failed; Docker Hub pulls fail with a TLS error).
- Evidence limits of the scratch repro: it was keyed (`--key`, `--use-signing-config=false --tlog-upload=false`), had no Rekor entry, used one tiny image and a stand-in Python OCI registry on localhost, not ghcr.io, and compared only v3.1.3 (v3.0.6 could not be run on the scratch image). It showed v3.1.3 labels the attest referrer correctly; it did not prove the keyless path or name the upstream fix.
- Outcome (2026-10-16): the first main run with `cosign-release: v3.1.3` passed the new verify step on both images (keyless), and both new digests verified from a local clean machine with `predicateType https://spdx.dev/Document`. The published images from before the pin remain mislabelled.
