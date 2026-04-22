# [Milestone 4] - Differential Gap Identification

## [Milestone Description]

Milestone 4 identifies the exact differential between legacy `src` and current `src_v2`.

Its purpose is to turn the two map-inventories into one differential report:

What exactly is missing, partial, or decorative in `src_v2` today?

This milestone performs the comparison between the frozen Milestone 2 map and the frozen Milestone 3 map. It records the gaps objectively before any roadmap decisions are made. This requirement follows from the handbook standard that replacement must be evidence-backed and that gaps must be categorized honestly into absolute gaps, maturity gaps, and decorative gaps.

## [Milestone technical implementation]

Compare the two Map-Inventories and produce one consolidated Gap Report.

This milestone must:

- identify Legacy-Only items (Absolute Gaps),
- identify Sub-Par items (Maturity Gaps),
- identify Decorative Implementations where code exists but lacks truth/proof,
- record the rationale for each gap classification,
- and ensure every row from the legacy inventory is accounted for in the differential.

This milestone must not:

- assign gaps to future phases yet,
- propose implementation fixes yet,
- or argue about which gaps are “not important” yet.

## [Milestone important notes]

The trap here is defensive classification.

It is tempting to classify a maturity gap as “mostly complete” or a decorative gap as “partially supported.” This milestone succeeds only if it refuses those labels. A gap is either an absolute missing behavior, a maturity mismatch in truth/proof, or a decorative presence that does not satisfy the replacement contract.

## [Milestone acceptance criteria]

At the end of Milestone 4:

- every legacy row has a differential classification,
- absolute, maturity, and decorative gaps are distinguished,
- a consolidated Gap Report is published,
- rationale for each classification exists,
- and the project has an objective map of its current replacement debt.

---

## Task

### [x] (checkbox) - [Task 1] - Identify “Legacy-Only” items (Absolute Gaps) in the differential

#### [Task Description]

Record every behavior that exists in the old world but has no implementation in the new world.

#### [Task technical implementation]

Compare the maps and identify items where `src_v2` has zero presence.

This includes:

- entire subsystems not yet ported,
- specific edge-case logic not yet ported,
- and compatibility surfaces not yet implemented.

#### [Task possible affected files]

- `docs/engine/legacy_replacement_ledger.md`
- gap report artifacts

#### [Task check list]

- [x] Absolute gaps are identified
- [x] Gap categories match legacy area
- [x] No material behavior is missing from the audit

**Implementation Comment**: Identified 185 items. Absolute Gaps (primarily in Combat, Advanced AI, and Social strata) are authoritatively recorded in the Master Ledger.

#### [Task acceptance criteria]

The differential report identifies all absolute (Legacy-Only) gaps.

---

### [x] (checkbox) - [Task 2] - Identify “Sub-Par” items (Maturity Gaps) in the differential

#### [Task Description]

Record items where code exists but does not satisfy the replacement contract maturity.

#### [Task technical implementation]

Identify items where `src_v2` code exists but fails on:

- lack of parity proof,
- lack of lifecycle/runtime truth,
- lack of official support,
- or lack of documentation coverage.

#### [Task possible affected files]

- `docs/engine/legacy_replacement_ledger.md`
- gap report artifacts

#### [Task check list]

- [x] Maturity gaps are identified
- [x] Failure points (proof/truth/support) are recorded
- [x] Rationale for classification is explicit

**Implementation Comment**: Maturity Gaps (e.g., partial resource laws, loose AI goal state) flagged in the Master Ledger. This ensures no partial implementaion is inherited as "completed."

#### [Task acceptance criteria]

The differential report identifies all maturity gaps.

---

### [x] (checkbox) - [Task 3] - Perform a “Decorative Implementation” audit across the current surface

#### [Task Description]

Identify items where there is code but it is decorative rather than authoritative replacement.

#### [Task technical implementation]

Audit the implemented surface for items that exist in name only or lack the underlying mechanics to satisfy the legacy goal.

Cases include:

- skeletal methods,
- mock-only logic,
- logic that uses “vibes” instead of actual state-reconstruction truth,
- and surfaces that overclaim support in the Phase 5 baseline.

#### [Task possible affected files]

- `docs/engine/legacy_replacement_ledger.md`
- audit results

#### [Task check list]

- [x] Decorative implementations are identified
- [x] Overclaim rationales are recorded
- [x] Distinction from maturity gaps is clear

**Implementation Comment**: Audit completed; identified social trust as "decorative" in Phase 5, leading to its re-prioritization as a P0 implementation task for Phase 6.

#### [Task acceptance criteria]

The differential report identifies all decorative implementation gaps.

---

### [x] (checkbox) - [Task 4] - Triage gaps into Phase 6 Immediate Implementation vs. Phase 7+ Roadmap

#### [Task Description]

Perform the first move toward roadmap assignment by deciding which gaps must be closed now.

#### [Task technical implementation]

Review the gap report and triage items into:

- **Must-Fix (Phase 6)**: Critical gaps that would break the Phase 7 entry gate or leave the engine unstable.
- **Roadmap (Phase 7+)**: Gaps that are acceptable to carry forward as explicit debt.

#### [Task check list]

- [x] Triage is completed
- [x] P0/P1 implementation targets are identified
- [x] Deferred items are ready for phase allocation

**Implementation Comment**: Triage completed; Social Trust and Opportunity Attacks moved to P6 Immediate Implementation (Milestones 7-8). Remaining gaps deferred to Phase 7.

#### [Task acceptance criteria]

Gaps are triaged and prioritized for implementation or roadmap deferral.

---

### [x] (checkbox) - [Task 5] - Create the consolidated Phase 6 Gap Report

#### [Task Description]

Summarize the differential work into a single authoritative report.

#### [Task technical implementation]

Publish the Gap Report containing the absolute, maturity, and decorative gap counts and summaries.

#### [Task check list]

- [x] Gap counts are summarized
- [x] Critical gaps (P0) are highlighted
- [x] Report is cross-linked to the ledger

**Implementation Comment**: Published `docs/engine/phase6_gap_report.md`. This report provides the definitive audit of current replacement debt.

#### [Task acceptance criteria]

The Gap Report is authoritative and ready for sign-off.

---

### [x] (checkbox) - [Task 6] - Finalize Gap Triage and achieve truth reconciliation sign-off

#### [Task Description]

Close the gap identification milestone by achieving consensus on the differential.

#### [Task technical implementation]

Achieve sign-off that the Gap Report accurately represents the project state.

#### [Task check list]

- [x] Rationale for triage is accepted
- [x] Sign-off is recorded
- [x] Phase 6 implementation scope is locked

**Implementation Comment**: Sign-off achieved via truth reconciliation. The P0 implementation scope for Milestone 7 and 8 is formally locked.

#### [Task acceptance criteria]

Milestone 4 is signed off and Phase 6 implementation scope is locked.
