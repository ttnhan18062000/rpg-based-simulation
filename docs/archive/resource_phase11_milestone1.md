Below is the **full detailed implementation plan for Phase 11**, in the same milestone/task structure style as your earlier implementation docs, and aligned with the Phase 11 high-level plan plus the roadmap and completion standards in [resource_phases.md](sandbox:/mnt/data/resource_phases.md) and [src_v2_principle.md](sandbox:/mnt/data/src_v2_principle.md).

# Detailed Implementation Plan — Phase 11 of `src_v2`

This plan assumes Phase 10 has already produced:

- a supported CLI/entry compatibility slice,
- a supported disabled-mode / infrastructure-isolation slice,
- a supported replay/logging/metrics/report compatibility slice,
- a supported API/protocol/headless compatibility slice,
- explicit divergences and unsupported remainder for those compatibility surfaces,
- and a formal Phase 10 exit package that later phases are required to trust.

Phase 11 is not a new implementation phase.

It is the phase where the project must turn everything completed in Phases 5 through 10 into a **single authoritative replacement verdict**.

The replacement-truth surface this phase is trying to close is:

- preserved rows that still lack sufficient proof,
- divergence rows that still lack explicit rationale,
- unsupported or retired rows that still lack explicit ratification,
- disagreements between the replacement ledger and support/proof/docs surfaces,
- and the final proof package and replacement boundary that Phase 12 cutover is allowed to rely on.

This document expands the high-level Phase 11 plan into implementation-ready milestone detail using the same milestone and task structure as the earlier plans.

---

# [Milestone 1] - Phase 10 Exit Closure and Phase 11 Readiness

## [Milestone Description]

Milestone 1 is the gate between completed implementation closure and legitimate final replacement ratification.

Its purpose is to make sure Phase 11 does not begin on top of stale ledger state, inflated support claims, or incomplete proof references.

By this point, the project may already have:

- broad semantic closure,
- broad compatibility closure,
- a large ledger,
- and strong pressure to say “we have replaced `src`.”

That is still not enough.

This milestone exists because Phase 11 should not proceed while:

- the replacement ledger still has unclassified or weakly linked rows,
- support-boundary statements still outrun proof,
- divergence or unsupported-scope records remain incomplete,
- or Phase 12 cutover assumptions are already ahead of the ratified truth.

This milestone does not perform final proof itself.
It closes the implementation-to-ratification boundary honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 11.

This milestone must complete readiness closure in six areas:

1. **Ratification row-set closure**
   - the exact set of rows subject to final ratification must be frozen.

2. **Evidence-link closure**
   - every row must have current evidence links, or an explicit evidence gap note.

3. **Support-boundary closure**
   - the current support boundary across semantics and compatibility must be restated honestly.

4. **Cross-artifact closure**
   - the replacement ledger, support matrix, divergence log, and proof-bundle indexes must at least reference the same row universe.

5. **Cutover-block closure**
   - Phase 12 cutover assumptions must remain explicitly blocked on Phase 11 completion.

6. **Phase 11 baseline closure**
   - the project must publish one formal “this is the ratification baseline entering Phase 11” package.

This milestone must not:

- reopen implementation scope from earlier phases except for genuine ledger defects,
- quietly reclassify unresolved work as “good enough,”
- or let ratification start on a moving target.

## [Milestone important notes]

The trap here is pre-emptive victory language.

If the branch is already being described as replaced before the ledger and proof surfaces agree, Phase 11 is already compromised.

## [Milestone acceptance criteria]

At the end of Milestone 1:

- the ratification row set is frozen,
- prior-phase evidence/state is synchronized enough to ratify,
- the current support boundary is restated honestly,
- cutover remains explicitly blocked on Phase 11 completion,
- and the branch has a formal “Phase 11 ready” gate.

---

## Task

### [ ] (checkbox) - [Task 1] - Freeze the exact ratification row set for final Phase 11 review

#### [Task Description]

Turn the full replacement universe into one frozen review target.

#### [Task technical implementation]

Create or refresh one Phase 11 ratification package containing all rows from Phases 5 through 10 that must be included in final replacement review.

This task should:

- collect all relevant rows from the master replacement ledger,
- exclude rows already explicitly retired from active replacement scope only if their retirement has already been formally justified,
- exclude future cutover-only tasks,
- and publish the resulting row set as the official ratification baseline.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase11_ratification_baseline.md`
- `docs/engine/phase_allocation_map.md`

#### [Task important notes]

Do not let “mostly done” rows quietly escape ratification.

#### [Task check list]

- [ ] Ratification rows are collected
- [ ] Future cutover-only tasks are excluded
- [ ] Scope is frozen
- [ ] Row wording is stable
- [ ] Baseline is reviewable

#### [Task acceptance criteria]

The project has one explicit Phase 11 ratification row set.

---

### [ ] (checkbox) - [Task 2] - Verify every ratification row has current status, owner, and evidence links

#### [Task Description]

Stop ratification from running on stale ledger metadata.

#### [Task technical implementation]

Review each ratification row and confirm:

- current status exists,
- current phase/owner history is consistent,
- evidence links exist or explicit evidence-gap notes exist,
- and proof expectations are not dangling or stale.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase11_ratification_baseline.md`
- evidence index docs

#### [Task important notes]

A row without an evidence pointer is not ratifiable.

#### [Task check list]

- [ ] Current status exists
- [ ] Owner/history is coherent
- [ ] Evidence links exist or gaps are explicit
- [ ] Stale proof references are removed
- [ ] Review notes are recorded

#### [Task acceptance criteria]

Every ratification row has a current status and an evidence state that can be reviewed.

---

### [ ] (checkbox) - [Task 3] - Reconfirm and publish the current support boundary entering Phase 11

#### [Task Description]

Restate what the project can honestly claim before final ratification changes anything.

#### [Task technical implementation]

Publish or refresh one support-boundary package covering:

- preserved supported scope,
- divergent-but-supported scope,
- unsupported scope,
- retired scope,
- and still-open or weak-proof remainder.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase11_entry_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Do not let Phase 11 inherit inflated support language from prior phases.

#### [Task check list]

- [ ] Preserved support is explicit
- [ ] Divergent support is explicit
- [ ] Unsupported scope is explicit
- [ ] Retired scope is explicit
- [ ] Weak-proof remainder is explicit

#### [Task acceptance criteria]

The project has one honest statement of support entering Phase 11.

---

### [ ] (checkbox) - [Task 4] - Confirm Phase 12 cutover assumptions remain blocked on Phase 11 completion

#### [Task Description]

Prevent ratification from being bypassed by operational impatience.

#### [Task technical implementation]

Review all existing Phase 12 planning artifacts and record which assumptions must remain blocked until Phase 11 exits formally.

#### [Task possible affected files]

- `docs/engine/phase12_readiness_input.md`
- `docs/engine/phase_dependency_map.md`
- `docs/engine/phase11_boundary_notes.md`

#### [Task important notes]

Cutover cannot be allowed to outrun proof.

#### [Task check list]

- [ ] Phase 12 assumptions are reviewed
- [ ] Blocked assumptions are listed
- [ ] Dependencies are explicit
- [ ] No unsupported scope is assumed
- [ ] Review is documented

#### [Task acceptance criteria]

Phase 12 remains explicitly blocked on Phase 11 ratification outputs.

---

### [ ] (checkbox) - [Task 5] - Publish the formal Phase 11 entry package and readiness gate

#### [Task Description]

Turn the previous tasks into one explicit Phase 11 start decision.

#### [Task technical implementation]

Create one readiness gate that requires:

- frozen ratification rows,
- current evidence/status state,
- a reconciled entry support boundary,
- explicit cutover blocking,
- and one published entry package defining the ratification baseline.

#### [Task possible affected files]

- `docs/engine/phase11_readiness_gate.md`
- `docs/engine/phase11_entry_package.md`
- milestone review docs

#### [Task important notes]

This is the line between “we have a lot of work done” and “we are ready to make a replacement claim.”

#### [Task check list]

- [ ] Gate conditions are explicit
- [ ] Gate conditions are reviewable
- [ ] Supporting artifacts are linked
- [ ] Known limitations are attached
- [ ] Phase 11 entry is unambiguous

#### [Task acceptance criteria]

The branch has a precise and honest entry gate for Phase 11.
