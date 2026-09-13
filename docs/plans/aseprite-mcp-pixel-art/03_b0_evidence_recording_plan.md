---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [architecture, evidence, security, provenance, pixel-art]
---

# Milestone 03 — B0 Evidence-Only Recording

## Outcome

Demonstrate that complete drawing-session evidence can be retained, reconstructed, sanitized, quarantined,
revoked, and deleted under policy without placing any prior-case content into an agent drawing context.
B0 builds no adaptive behavior and makes no improvement claim.

## Prerequisites

- M0 evidence ownership, storage boundary, schemas, size limits, retention policy, and threat model approved.
- Storage/access-control technology selected; unresolved deletion guarantees remain `BLOCKED`.
- Synthetic inert cases available; real human reviews are forbidden until privacy/retention controls pass.

## Deliverables

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `B0-W01` | Evidence archive schema | Brief, parentage, revisions, artifacts, operations, previews, reviews, errors, scores, outcomes, roles, timestamps, and component provenance are versioned |
| `B0-W02` | Append/tamper contract | Existing evidence is not silently rewritten; hash/chain or equivalent tamper evidence detects mutation |
| `B0-W03` | Safe-projection schema | Only bounded typed allowlisted facts and explicit success/failure outcome can leave the archive boundary |
| `B0-W04` | Projection builder | Raw text, code-like data, tool calls, paths, URLs, controls, filenames, errors, manifests, and imported metadata cannot enter projection output |
| `B0-W05` | Quarantine/retention lifecycle | Quarantine, tombstone, redacted successor, index/retrieval revocation, retention expiry, and required deletion have auditable behavior |
| `B0-W06` | Reconstruction report | A complete permitted case can be reconstructed from immutable evidence and exact schema/component identities |
| `B0-W07` | Adversarial evidence suite | Direct, indirect, obfuscated, impersonated, metadata/image-borne, oversized, contradictory, and authority-changing inputs are denied or quarantined |
| `B0-W08` | B0 disposition | Foundation portions of `CAP-B01`, `B06`, and `B09` classified without claiming the full gates pass |

## Non-goals

- Retrieving cases or guidance into agent context.
- Creating candidate guidance, a playbook, embeddings, a ranker, or an external scorer.
- Evaluating drawing quality or cross-session improvement.
- Reusing the Knowledge Gateway cache as the evidence archive without a separate suitability decision.

## Authorization boundary

B0 receives evidence through a typed recorder only. It exposes no prompt/context endpoint and no Aseprite,
MCP, repository, network, simulation-state, or production-asset authority. Archive administrators may apply
retention/quarantine actions; agents cannot activate guidance because no active playbook exists.

## Covered capability gates

B0 supplies prerequisite evidence for `CAP-B01`, `CAP-B06`, and `CAP-B09`; none fully passes until the
end-to-end adaptive path exists. `CAP-B02`–`B05`, `B07`, and `B08` are not attempted.

## Required evidence

- Schema versions, fixture corpus hashes, exact archive/projection implementation, access policy, and storage platform.
- Complete/partial/tampered/quarantined/deletion-required cases and expected outcomes.
- Proof that raw fields never appear in projection bytes, logs, errors, caches, or indexes.
- Reconstruction, tamper, expiry, revocation, deletion, and “removed case disclosed in evaluation” reports.
- Model/provider fields recorded as `UNAVAILABLE` rather than fabricated when APIs do not expose them.

## Security checks

- Test the full ingestion → archive → projection boundary, including Unicode controls, nesting, compression,
  image metadata, filenames, scorer-shaped input, and authority impersonation.
- Unknown fields and unsupported schema versions fail closed.
- Projection output has strict type, enum, item-count, byte, and reference-namespace limits.
- Access roles cannot cross archive administration, projection, and future activation boundaries.
- Removed/quarantined content is absent from every searchable/indexed/cache path while audit reason stays non-sensitive.

## Objective exit criteria

B0 `PASS` requires complete reconstruction, detected tampering, zero raw-to-projection leakage, safe empty
projection, proven quarantine/revocation/retention/deletion behavior, and retained negative evidence.
Platform-limited deletion proof is `INCONCLUSIVE`; retrievable revoked content or silent evidence rewriting
is `FAIL`.

## Dependencies

B0 depends only on M0 evidence/archive/privacy contract alignment, not the tool-feasibility disposition or
M1 execution. Synthetic fixtures can prove mechanics. A real case may be recorded only from a separately
authorized supervised agent session after B0 passes privacy/security controls and a separate retention
authorization exists. Manual-art records remain outside CAP-B unless its owner later approves a
producer-class, corpus-separation, scope-matching and baseline-leakage amendment.

## Rollback path

Disable recording, revoke projection/index access, quarantine affected records, execute approved deletion,
retain a non-sensitive audit tombstone, and return drawing workflow to stateless supervised operation.

## Stop conditions

Stop if raw review/error/operation data can enter agent-visible output, tampering is undetectable, deletion
cannot meet policy, secrets or personal data cannot be controlled, or the store becomes project truth or
simulation state.

## Ticket-ready slices after authorization

Schema registry; archive writer/tamper evidence; safe projection; quarantine/retention/deletion; adversarial
fixtures; reconstruction audit. Keep every slice context-output-free.
