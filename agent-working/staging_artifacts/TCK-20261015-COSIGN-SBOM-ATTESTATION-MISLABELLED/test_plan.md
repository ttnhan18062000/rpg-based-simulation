---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261015-COSIGN-SBOM-ATTESTATION-MISLABELLED
date: 2026-10-15
tags: [platform, security]
---

# Test plan: TCK-20261015-COSIGN-SBOM-ATTESTATION-MISLABELLED

| # | Check | Where | Evidence label |
|---|---|---|---|
| 1 | Workflow YAML parses; actionlint is clean if available | local | running locally |
| 2 | PR run: build-only, so sign/attest/verify steps are skipped | PR CI | validated |
| 3 | Main run: SBOM, attest, sign and the new verify step all pass for backend and frontend | main CI (post-merge) | validated |
| 4 | Negative: the verify step fails when the attestation is missing or mislabelled, e.g. the verify command against the current mislabelled digests `154b5d5f…`/`fe94ffbb…` exits non-zero | local | running locally |
| 5 | Clean-machine `cosign verify` + `verify-attestation --type spdxjson` on the new digests with the pinned version; the predicate is SPDX 2.3 | local | running locally |
| 6 | The step-summary commands match #5 exactly | main CI summary | validated |

Post-merge checks 3, 5 and 6 are recorded in the ticket's Test Summary before close; the ticket stays INPROGRESS until then.

## Outcome so far (2026-10-16, platform-implementer)
- Check 1: done (actionlint clean, YAML parses). Check 4: done (cosign v3.1.3 `verify-attestation --type spdxjson` on backend `154b5d5f…` exits 1, "found: .../sign/v1"). Scratch repro: v3.1.3 labels the SBOM referrer `https://spdx.dev/Document` and the check passes (keyed, local stand-in registry).
- Checks 2, 3, 5, 6 are post-merge or PR-run observations, recorded in the ticket's Test Summary before close.
