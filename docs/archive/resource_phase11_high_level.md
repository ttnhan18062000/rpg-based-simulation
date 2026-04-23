Below is the **high-level implementation plan for Phase 11** in the same milestone style as the earlier high-level phase plans.

This plan is grounded in the corrected roadmap and the replacement-governance model from [resource_phases.md](sandbox:/mnt/data/resource_phases.md), the completion/official-support standards from [src_v2_principle.md](sandbox:/mnt/data/src_v2_principle.md), and the compatibility-ledger framing already surfaced through [legacy_logic_checklist_part2.md](sandbox:/mnt/data/legacy_logic_checklist_part2.md).

---

# High-Level Implementation Plan — Phase 11 of `src_v2`

This plan assumes Phase 10 has already produced:

- a supported CLI/entry compatibility slice,
- a supported disabled-mode / infrastructure-isolation slice,
- a supported replay/logging/metrics/report compatibility slice,
- a supported API/protocol/headless compatibility slice,
- explicit divergences and unsupported remainder for those compatibility surfaces,
- and a formal Phase 10 exit package that later phases are required to trust.

It also assumes the project has stopped pretending that broad implementation coverage is the same thing as a ratified replacement claim.

Phase 11 is not the phase where the project should widen into new semantics, new compatibility work, or legacy retirement.

It is the phase where `src_v2` must turn all prior phase results into a **single authoritative replacement verdict**.

The purpose of Phase 11 is:

- verify that every preserved replacement claim across Phases 5 through 10 has evidence,
- verify that every intentional divergence is explicitly logged and justified,
- verify that every unsupported or retired legacy surface is explicitly accounted for,
- eliminate silent gaps between the master ledger and actual code/test/support claims,
- produce one final proof bundle and replacement-status package,
- and establish the truthful baseline that Phase 12 cutover is allowed to assume.

This is the phase where the rewrite stops being “a lot of completed work” and becomes “a ratified replacement statement.”

---

# [Milestone 1] - Phase 10 Exit Closure and Phase 11 Readiness

## [Milestone Description]

Milestone 1 is the entry gate for Phase 11.

Its purpose is to stop the team from starting final replacement ratification while the Phase 10 compatibility baseline is still unstable, overstated, or not actually reflected in the replacement ledger.

By this point, the branch may already have:

- broad semantic closure,
- broad compatibility closure,
- and intense pressure to say “we’ve basically replaced `src`.”

That is still not enough.

This milestone exists because Phase 11 should not proceed while:

- the replacement ledger still contains unclassified or weakly evidenced rows,
- support-boundary statements still overclaim preserved scope,
- divergence or unsupported-scope records are still incomplete,
- or Phase 12 cutover assumptions are already outrunning Phase 11 proof.

This milestone does not perform final proof itself.

It closes the implementation-to-ratification boundary honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 11.

This milestone must:

- freeze the exact set of rows subject to final replacement ratification,
- confirm all prior phase rows have current status, evidence links, and ownership,
- restate the current support boundary honestly across semantics and compatibility,
- confirm that Phase 12 cutover assumptions are still blocked on Phase 11 completion,
- and publish one formal “Phase 11 begins from this ratification baseline” record.

This milestone must not:

- reopen implementation scope from earlier phases except for genuine ledger defects,
- quietly reclassify unresolved work as “good enough,”
- or allow ratification to begin on a moving target.

## [Milestone important notes]

The trap here is obvious and deadly: calling the branch “effectively done” before the replacement ledger and proof surfaces actually agree.

If the ledger, support matrix, divergence log, and proof bundles do not align, Phase 11 is starting from fiction.

## [Milestone acceptance criteria]

At the end of this milestone:

- the ratification row set is frozen,
- prior-phase evidence/state is synchronized,
- the current support boundary is restated honestly,
- cutover remains blocked on Phase 11 completion,
- and the branch has an explicit “Phase 11 ready” gate.

---

# [Milestone 2] - Preserved-Surface Proof Closure and Coverage Reconciliation

## [Milestone Description]

Milestone 2 closes the proof story for all rows claimed as preserved.

Its purpose is to verify that every preserved behavior across semantic and compatibility surfaces actually has the required evidence.

This milestone covers:

- preserved gameplay-semantic rows,
- preserved substrate/runtime rows,
- preserved compatibility rows,
- coverage reconciliation between tests/docs/ledger,
- and elimination of preserved claims that are not actually proven.

It is about preserved-scope truth, not divergences or unsupported scope.

## [Milestone technical implementation]

Reconcile every preserved row against actual proof and support criteria.

This milestone must:

- confirm that each preserved row has appropriate characterization, differential, contract, or black-box proof,
- verify that proof scope matches the actual support claim,
- remove or downgrade preserved claims that are not sufficiently evidenced,
- and publish the reconciled preserved-surface baseline.

This milestone must not:

- rely on broad green suites as a substitute for row-level proof,
- keep preserved labels on rows that are only “likely correct,”
- or use vague confidence language instead of evidence.

## [Milestone important notes]

The trap here is proof inflation.

A branch with many tests will tempt you to believe preserved coverage is stronger than it is. Phase 11 has to be row-honest, not vibes-honest.

## [Milestone acceptance criteria]

At the end of this milestone:

- every preserved row has explicit supporting evidence,
- proof scope matches support scope,
- weak preserved claims are downgraded or corrected,
- and preserved replacement truth is no longer overstated.

---

# [Milestone 3] - Divergence, Unsupported, and Retired-Scope Ratification

## [Milestone Description]

Milestone 3 closes the truth story for everything that is **not** preserved.

Its purpose is to ensure that intentional divergences, unsupported legacy behaviors, and retired scope are all explicit, justified, and discoverable.

This milestone covers:

- intentional divergence records,
- unsupported-scope records,
- retired-scope records,
- rationale completeness,
- and support-matrix alignment for all non-preserved rows.

It is about explicit non-equivalence, not preserved parity.

## [Milestone technical implementation]

Reconcile every non-preserved row against formal policy and explicit documentation.

This milestone must:

- verify every intentionally divergent row has explicit rationale and evidence,
- verify every unsupported row is named and constrained,
- verify every retired row has a real retirement rationale,
- align all non-preserved rows with the support matrix and replacement ledger,
- and eliminate silent or ambiguous non-preserved scope.

This milestone must not:

- leave “known differences” buried in test comments or code,
- confuse unsupported with retired,
- or treat undocumented differences as harmless.

## [Milestone important notes]

The trap here is embarrassment.

Teams hate writing down what they did not preserve. That discomfort is exactly why this milestone exists.

## [Milestone acceptance criteria]

At the end of this milestone:

- every non-preserved row has explicit status and rationale,
- divergence/unsupported/retired boundaries are clean,
- support claims do not silently imply broader parity,
- and non-preserved scope is fully ratified.

---

# [Milestone 4] - Master-Ledger Reconciliation and Silent-Gap Elimination

## [Milestone Description]

Milestone 4 closes the governance gap between all project truth surfaces.

Its purpose is to eliminate disagreement between:

- the replacement ledger,
- the support matrix,
- divergence logs,
- unsupported/retired registers,
- proof bundles,
- and current docs/release truth.

This milestone is where the project stops having multiple partially correct truths.

## [Milestone technical implementation]

Run one full reconciliation pass across all authoritative governance artifacts.

This milestone must:

- cross-check every ledger row against its linked evidence,
- verify support matrix entries match ledger status,
- verify divergence and unsupported registers match ledger status,
- verify proof bundles and docs do not imply unsupported claims,
- and eliminate orphaned, duplicated, or silently contradictory rows.

This milestone must not:

- tolerate “close enough” alignment,
- leave row references broken or stale,
- or allow any public-facing support surface to outrun the ledger.

## [Milestone important notes]

The trap here is thinking a mostly aligned governance system is good enough.

It is not.

If there are multiple competing truths, Phase 12 cutover becomes politics instead of engineering.

## [Milestone acceptance criteria]

At the end of this milestone:

- the ledger, support matrix, divergence log, and proof surfaces agree,
- contradictory rows are eliminated,
- orphaned scope is eliminated,
- and the project has one coherent governance truth.

---

# [Milestone 5] - Final Replacement Verdict, Proof Bundle, and Release-Truth Ratification

## [Milestone Description]

Milestone 5 turns the reconciled governance system into the official replacement verdict.

Its purpose is to produce the final proof bundle and replacement-status package that says, precisely, what `src_v2` has replaced and what it has not.

This milestone covers:

- final replacement summary,
- final proof bundle consolidation,
- final support-boundary statement,
- final preserved/divergent/unsupported/retired counts or summaries,
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

At the end of this milestone:

- the final proof bundle is published,
- the final replacement boundary is published,
- release-truth surfaces match the evidence,
- and the project has one formal replacement verdict ready for cutover planning.

---

# [Milestone 6] - Phase 12 Cutover Baseline and Phase 11 Exit Package

## [Milestone Description]

Milestone 6 is the exit gate for Phase 11.

Its purpose is to convert final replacement truth into a constrained handoff baseline for Phase 12.

This milestone does not begin cutover execution itself.
It does not retire old `src`.
It does not reopen implementation.

It closes the ratification phase and defines what cutover is now allowed to rely on.

## [Milestone technical implementation]

Create one Phase 11 exit package that binds Phase 12 to the ratified truth.

This milestone must:

- publish the Phase 11 exit package,
- define exactly which supported surfaces Phase 12 may cut over,
- define which unsupported/divergent/retired surfaces must not be assumed during cutover,
- and link all cutover assumptions back to the final ledger and proof bundle.

This milestone must not:

- quietly let cutover assume more than was ratified,
- let unsupported scope disappear into silence,
- or treat “mostly replaced” as a cutover license.

## [Milestone important notes]

The trap here is impatience.

After all this work, people will want cutover immediately. That is exactly why the exit package must be explicit and limiting, not merely celebratory.

## [Milestone acceptance criteria]

At the end of this milestone:

- the Phase 11 exit package is published,
- Phase 12 assumptions are explicit and bounded,
- unsupported/divergent scope remains visible,
- and the branch has a formal “Phase 11 complete” handoff baseline.

---

## Why these milestones do not duplicate each other

Milestone 2 is about **preserved-surface proof closure**.

Milestone 3 is about **non-preserved-surface ratification**.

Milestone 4 is about **cross-artifact governance reconciliation**.

Milestone 5 is about **the final replacement verdict and proof package**.

Milestone 6 is about **the bounded cutover handoff**, not proof itself.

If you merge these, you will create a fake “final verification” phase that sounds tidy and guarantees silent gaps.
