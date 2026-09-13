---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [assets, adoption, provenance, rehearsal, planning]
---

# AM-M4 — Candidate Adoption Rehearsal

## Outcome

Plan `ASSET-2`: rehearse one disposable candidate through source, artifact, provenance, catalog and audit
records without creating an adopted source, deployable release, active manifest, or production asset.

## Repository evidence and assumptions

No production semantic asset registry, source-artifact layout, binary policy, provenance schema or adoption
authority was found at drafting time. M1 must replace these unknowns with accepted contracts. The rehearsal
may use a tiny synthetic or manually supplied non-production image; CAP-A is not a prerequisite.

## Prerequisites and dependencies

- M1 `PASS` including `AM-C01`, and M2 `PASS` including `AM-C02`.
- Approved rehearsal fixture, evidence charter, isolated storage root and cleanup owner.
- Separate execution authorization through the normal ticket workflow.
- A provenance/license disposition that permits the bounded rehearsal.
- No dependency on CAP-A, CAP-B, real art quality, renderer selection or production activation.

## Deliverables and acceptance criteria

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `AM4-W01` | Disposable candidate record | Candidate identity is immutable, non-authoritative and cannot be mistaken for adopted/active state |
| `AM4-W02` | Source/artifact rehearsal | Source and derived artifact hashes, transformations and schema versions remain separate and traceable |
| `AM4-W03` | Allowlisted build rehearsal | Only declared inputs/outputs are touched; network, secrets, publication and activation are denied |
| `AM4-W04` | Provenance/license record | Author/tool/input/config/revision/license/reviewer fields are present or explicitly reject the candidate |
| `AM4-W05` | Catalog-delta preview | Semantic changes are bounded, deterministic, human-readable and never committed to production state |
| `AM4-W06` | Independent validation | Hash, format, decoded bounds, semantic contract, license and reproducibility checks produce retained results |
| `AM4-W07` | Audit reconstruction | An independent reviewer can reconstruct who proposed/reviewed what without relying on mutable filenames |
| `AM4-W08` | Cleanup proof | Candidate records and bytes are removable without affecting source truth, fixtures or runtime behavior |
| `AM4-W09` | Candidate handoff intake | A versioned asset-owned `CandidateHandoffPackage` from either an approved manual or CAP-A producer is copied into bounded quarantine, independently validated, and cannot assert adoption, publication or activation |
| `AM4-W10` | Post-review revocation case | Revoking/quarantining the candidate after review but before build eligibility prevents build, catalog commit, publication and activation despite late work |

## Applicable gates

M4 targets `AM-C03`, `AM-C04`, and `AM-C08`. It relies on C01/C02 but does not reopen them unless a
contract defect is discovered. It passes no activation gate and contributes no CAP-A/CAP-B evidence.

## Retained evidence

Approved fixture identity; source/artifact/config hashes; bounded build logs; SBOM/tool versions where
applicable; catalog-delta preview; provenance/license record; reviewer decision; validation and negative
results; package-schema and intake result; producer class; post-review revocation trace; cleanup inventory.
Records label the result `REHEARSAL_ONLY`.

## Security and recovery

Use an isolated allowlisted working root with no network, secrets, plugin installation, repository-wide
write, publication or activation authority. Reject traversal, symlink escape, executable formats,
decompression/resource abuse, ambiguous metadata and mutable-only identities. Recovery removes the
disposable rehearsal objects and restores the empty rehearsal root; retained evidence remains immutable.

## Explicit non-goals

- Creating or approving production art, an adopted source tree, a release or an active catalog.
- Running Aseprite/MCP or judging artistic quality.
- Choosing repository binary/LFS policy beyond recording M1's decision.
- Live Map/HUD display, renderer migration or deployment.

## Authorization required to start

Not currently authorized. Requires M1/M2 passage, an implementation ticket, named rehearsal owner and
reviewer, fixture/license approval, scoped filesystem authority, and approved cleanup/evidence locations.

## Result classification

| Result | M4 condition |
|---|---|
| `PASS` | C03/C04/C08 pass and the disposable record is traceable, bounded, independently validated and cleanly removed |
| `FAIL` | The predeclared C08 evidence level fails, producer classes receive unequal intake policy, revoked input reaches build, build behavior is unbounded, provenance is incomplete, identities conflate states, or cleanup affects other roots |
| `BLOCKED` | Contracts, fixture rights, reviewers, isolation or execution authority are absent |
| `INCONCLUSIVE` | Output variance or provenance cannot be attributed or evaluated under the predeclared C08 evidence level |

## Rollback, abandonment, and stop conditions

Delete only the explicitly inventoried disposable rehearsal state, retain the evidence bundle, and leave
the production/runtime trees unchanged. Stop on undeclared files, network/secret access, executable input,
license uncertainty, implicit adoption, repository-wide mutation, or attempts to use rehearsal passage as
activation authority.

## Decisions remaining unfrozen

Actual asset families/content, art direction, adoption candidates, physical source/artifact layout,
storage/LFS, build tools, artifact formats, packing, deployment, renderer and migration scope.

## Candidate sources allowed for a future rehearsal

A deliberately synthetic fixture, an approved output of the manual art experiment plan, or an approved
CAP-A result may be used. These sources are alternatives; none is privileged or automatically adopted.
Both manual and CAP-A sources must conform to the asset-owned `CandidateHandoffPackage`; unavailable fields
are explicit, and the asset boundary independently copies, quarantines and validates every source.
