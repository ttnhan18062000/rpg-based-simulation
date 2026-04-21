# [Milestone 6] - Execution Baseline Publication and Governance Lock

## [Milestone Description]

Milestone 6 is the exit gate for Phase 6.

Its purpose is to convert the ledger and phase-allocation map into the official execution baseline for the rest of the rewrite.

This milestone does not redo inventory.
It does not redo classification.
It does not widen scope.

It packages the Phase 6 output into the governance system that later phases must obey. That is necessary because the value of Phase 6 is not merely to think clearly once, but to stop later work from sliding back into informal scope management.

## [Milestone technical implementation]

Create one published execution baseline and one governance lock that prevent later phases from drifting back into undocumented assumptions.

This milestone must:

- publish the master replacement ledger as an official artifact,
- publish the phase-allocation map as an official artifact,
- derive the high-level remaining execution backlog from those artifacts,
- define change-control rules for new rows, status changes, and divergence decisions,
- and bind future phase plans and dashboards to the locked ledger baseline.

This milestone must not:

- reopen settled classifications without formal change control,
- invent off-ledger work as if it were official scope,
- or let future phase plans claim support beyond the ratified baseline.

## [Milestone important notes]

The trap here is regression into chaos.

Teams often do the hard thinking once, publish a document, and then immediately go back to operating from memory, status meetings, and vibes. If that happens here, Phase 6 was wasted. This milestone succeeds only if later phases are structurally constrained by the ledger rather than emotionally inspired by it.

## [Milestone acceptance criteria]

At the end of Milestone 6:

- the master replacement ledger is published,
- the phase-allocation map is published,
- the future-phase execution baseline is published,
- governance rules for new rows and status changes are published,
- and future phase planning is formally constrained by the Phase 6 output.

---

## Task

### [ ] (checkbox) - [Task 1] - Publish the master replacement ledger as an official project artifact

#### [Task Description]

Make the replacement ledger the project’s source of truth for remaining replacement scope.

#### [Task technical implementation]

Publish the ledger in a stable location and make it the reference artifact for:

- replacement status,
- divergence status,
- unsupported scope,
- retired scope,
- and open replacement rows.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

If the ledger is not treated as official, the project will keep making off-ledger decisions.

#### [Task check list]

- [ ] Ledger is published
- [ ] Ledger location is stable
- [ ] Ledger is referenceable
- [ ] Ledger is reviewable
- [ ] Ledger is treated as official scope truth

#### [Task acceptance criteria]

The master replacement ledger exists as an official project artifact.

---

### [ ] (checkbox) - [Task 2] - Publish the official phase-allocation map for Phases 7 through 10

#### [Task Description]

Make future-phase ownership explicit instead of implicit.

#### [Task technical implementation]

Publish the phase-allocation map and link it directly to:

- the replacement ledger,
- future phase planning docs,
- and the remaining-scope overview.

#### [Task possible affected files]

- `docs/engine/phase_allocation_map.md`
- `docs/engine/remaining_replacement_scope.md`

#### [Task important notes]

Future-phase ownership should never have to be guessed again after this point.

#### [Task check list]

- [ ] Map is published
- [ ] Map is linked to the ledger
- [ ] Phase ownership is visible
- [ ] Dependencies remain visible
- [ ] Later phase docs can consume the map directly

#### [Task acceptance criteria]

The official phase-allocation map is published and linked into planning artifacts.

---

### [ ] (checkbox) - [Task 3] - Derive the high-level remaining execution backlog from the locked ledger

#### [Task Description]

Convert the ledger into actionable remaining work without bypassing the governance structure.

#### [Task technical implementation]

Produce one high-level execution backlog grouped by:

- Phase 7 substrate rows,
- Phase 8 gameplay-semantic rows,
- Phase 9 strategic/social/progression rows,
- Phase 10 compatibility rows,
- and major proof/dependency clusters.

This should remain high-level and phase-oriented, not sprint-ticket noise.

#### [Task possible affected files]

- `docs/engine/remaining_execution_backlog.md`
- roadmap dashboards
- phase planning docs

#### [Task important notes]

The backlog must be derived from the ledger, not manually invented beside it.

#### [Task check list]

- [ ] Backlog is phase-grouped
- [ ] Ledger rows map into backlog items
- [ ] Dependency clusters are visible
- [ ] Off-ledger scope is avoided
- [ ] Backlog remains high-level

#### [Task acceptance criteria]

The project has one high-level remaining execution backlog derived from the locked ledger.

---

### [ ] (checkbox) - [Task 4] - Define change-control rules for new rows, status changes, and divergence decisions

#### [Task Description]

Prevent future phases from silently mutating scope truth.

#### [Task technical implementation]

Define the rules for:

- adding newly discovered legacy rows,
- correcting row evidence,
- changing row status,
- recording new intentional divergences,
- and updating closure conditions.

Require explicit rationale and artifact updates for each change.

#### [Task possible affected files]

- `docs/engine/replacement_ledger_governance.md`
- `docs/engine/change_control.md`

#### [Task important notes]

Without change control, Phase 6 outputs will rot immediately.

#### [Task check list]

- [ ] New-row rule exists
- [ ] Status-change rule exists
- [ ] Divergence-update rule exists
- [ ] Evidence-correction rule exists
- [ ] Governance rules are reviewable

#### [Task acceptance criteria]

There is a formal change-control model for all future modifications to the ledger baseline.

---

### [ ] (checkbox) - [Task 5] - Link future phase plans, dashboards, and reviews to the Phase 6 baseline

#### [Task Description]

Make Phase 6 structurally unavoidable in later planning and reviews.

#### [Task technical implementation]

Update future phase planning docs and dashboards so they reference:

- the master replacement ledger,
- the phase-allocation map,
- closure conditions,
- and governance rules.

Do not allow later phase plans to stand alone as independent narratives.

#### [Task possible affected files]

- `docs/engine/phase7_plan.md`
- `docs/engine/phase8_plan.md`
- `docs/engine/phase9_plan.md`
- `docs/engine/phase10_plan.md`
- roadmap dashboards

#### [Task important notes]

If later phase plans do not link back to Phase 6, they will drift immediately.

#### [Task check list]

- [ ] Future phase plans reference the ledger
- [ ] Future phase plans reference allocation map
- [ ] Dashboard views reflect locked scope
- [ ] Closure conditions remain visible
- [ ] Off-ledger planning is discouraged structurally

#### [Task acceptance criteria]

Future phase planning and review surfaces are tied directly to the Phase 6 baseline.

---

### [ ] (checkbox) - [Task 6] - Publish the formal “Phase 6 complete” exit package

#### [Task Description]

Close the phase with one package that proves the governance system now exists.

#### [Task technical implementation]

Publish one Phase 6 exit package containing:

- the master replacement ledger,
- the phase-allocation map,
- the remaining execution backlog,
- the governance/change-control rules,
- and the formal statement of what Phase 6 completed.

#### [Task possible affected files]

- `docs/engine/phase6_exit_package.md`
- milestone review docs
- roadmap summary docs

#### [Task important notes]

This is the line between “we discussed replacement clearly” and “the project is now governed by a replacement ledger.”

#### [Task check list]

- [ ] Exit package is published
- [ ] Core artifacts are linked
- [ ] Governance rules are linked
- [ ] Completion statement is explicit
- [ ] Later phases can consume the package directly

#### [Task acceptance criteria]

The project has a complete and reviewable Phase 6 exit package.
