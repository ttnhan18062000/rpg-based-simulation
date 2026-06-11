---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 5] - Final Replacement Verdict, Proof Bundle, and Release-Truth Ratification

## [Milestone Description]

Milestone 5 turns the reconciled governance system into the official replacement verdict.

Its purpose is to produce the final proof bundle and replacement-status package that says, precisely, what `src` has replaced and what it has not.

This milestone covers:

- final replacement summary,
- final proof bundle consolidation,
- final support-boundary statement,
- final preserved/divergent/unsupported/retired summaries,
- and release-truth ratification.

It is the publication milestone for replacement truth.

## [Milestone technical implementation]

Publish the final Phase 11 replacement package as the authoritative source of truth.

This milestone must:

- consolidate the final proof bundle,
- publish the final support/replacement boundary,
- publish the replacement verdict tied to the ledger,
- ensure release/readiness docs say exactly what the proof says,
- and explicitly define what Phase 12 cutover is now allowed to assume.

This milestone must not:

- market the branch beyond the evidence,
- blur supported replacement with aspirational future work,
- or leave Phase 12 to infer the final replacement verdict.

## [Milestone important notes]

The trap here is sales language.

The more complete the project feels, the more pressure there will be to exaggerate. This milestone must be clinically honest.

## [Milestone acceptance criteria]

At the end of Milestone 5:

- the final proof bundle is published,
- the final replacement boundary is published,
- release-truth surfaces match the evidence,
- and the project has one formal replacement verdict ready for cutover planning.

---

## Task

### [ ] (checkbox) - [Task 1] - Consolidate the final cross-phase proof bundle

#### [Task Description]

Turn all prior phase proof into one discoverable final proof package.

#### [Task technical implementation]

Collect and index:

- preserved-surface proof references,
- divergence and unsupported-scope references,
- compatibility proof references,
- governance reconciliation outputs,
- and final evidence links needed for the replacement verdict.

#### [Task possible affected files]

- `docs/engine/phase11_proof_bundle.md`
- `docs/engine/release_proof/final/*`
- prior phase proof bundle docs

#### [Task important notes]

If the final proof bundle is scattered, the replacement verdict is weak no matter how good the code is.

#### [Task check list]

- [ ] Prior phase proof bundles are linked
- [ ] Final indexes are complete
- [ ] Divergence/unsupported links are included
- [ ] Governance reconciliation links are included
- [ ] Bundle is reviewable

#### [Task acceptance criteria]

The project has one discoverable final proof bundle.

---

### [ ] (checkbox) - [Task 2] - Publish the final replacement boundary and status summary

#### [Task Description]

State exactly what `src` has replaced and what it has not.

#### [Task technical implementation]

Publish one final boundary package covering:

- preserved supported scope,
- divergent-but-supported scope,
- unsupported scope,
- retired scope,
- and any explicitly deferred remainder still visible at Phase 11 close.

#### [Task possible affected files]

- `docs/engine/final_replacement_boundary.md`
- `docs/engine/replacement_status_overview.md`
- `docs/engine/support_matrix.md`

#### [Task important notes]

This is where vague phrases must die.

#### [Task check list]

- [ ] Preserved scope is explicit
- [ ] Divergent scope is explicit
- [ ] Unsupported scope is explicit
- [ ] Retired scope is explicit
- [ ] Deferred remainder is explicit if any remains

#### [Task acceptance criteria]

The project has one explicit final replacement boundary.

---

### [ ] (checkbox) - [Task 3] - Publish the formal replacement verdict tied to the ledger and proof bundle

#### [Task Description]

Turn the ratified boundary into the official project verdict.

#### [Task technical implementation]

Publish one replacement verdict artifact that directly references:

- the master replacement ledger,
- the final proof bundle,
- the support boundary,
- and the non-preserved baselines.

#### [Task possible affected files]

- `docs/engine/final_replacement_verdict.md`
- `docs/engine/phase11_proof_bundle.md`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

If the verdict is not tied to the ledger, it is just branding.

#### [Task check list]

- [ ] Verdict cites the ledger
- [ ] Verdict cites the proof bundle
- [ ] Verdict cites support boundaries
- [ ] Verdict cites non-preserved baselines
- [ ] Verdict is reviewable

#### [Task acceptance criteria]

The project has one formal replacement verdict tied to its evidence surfaces.

---

### [ ] (checkbox) - [Task 4] - Ratify release/readiness language against the final replacement verdict

#### [Task Description]

Make all release-facing truth surfaces say exactly what the verdict says.

#### [Task technical implementation]

Review and align all release/readiness statements so they match the final replacement verdict without overclaiming or omitting known non-preserved scope.

#### [Task possible affected files]

- `README.md`
- `docs/engine/release_readiness.md`
- `docs/engine/replacement_status_overview.md`
- `docs/engine/final_replacement_verdict.md`

#### [Task important notes]

If release docs still overclaim here, the whole phase failed.

#### [Task check list]

- [ ] Release wording matches verdict
- [ ] Support wording matches verdict
- [ ] Non-preserved scope remains visible
- [ ] Overclaims are removed
- [ ] Public-facing docs agree with internal docs

#### [Task acceptance criteria]

Release/readiness language is fully ratified against the final replacement verdict.
