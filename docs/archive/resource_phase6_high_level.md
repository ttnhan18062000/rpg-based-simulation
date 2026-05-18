# High-Level Implementation Plan — Phase 6 of `src`

This plan assumes Phase 5 has materially improved `src` by recovering a bounded resource/town/progression slice and by strengthening runtime truth around supported behavior.

It also assumes Phase 5 did **not** complete full replacement of original `src`.

Phase 6 is therefore not a feature-expansion phase.

It is the phase where `src` must stop operating on implied scope and start operating on an authoritative replacement ledger.

The purpose of Phase 6 is:

- close remaining Phase 5 truth gaps that would poison replacement planning,
- construct one authoritative inventory of the remaining old-`src` replacement surface,
- construct one authoritative inventory of the current `src` replacement surface,
- classify every legacy item as preserved, intentionally divergent, unsupported, or retired,
- assign every remaining item to a proof path and a future phase,
- and publish a locked execution baseline for Phases 7 through 10.

This is not the phase where the project should widen into major new gameplay recovery, broad compatibility implementation, or consumer cutover.

It is the phase where the team stops guessing.

---

# [Milestone 1] - Phase 5 Exit Closure and Phase 6 Entry Gate

## [Milestone Description]

Milestone 1 is the entry gate for Phase 6.

Its purpose is to stop the team from creating a replacement ledger on top of unresolved Phase 5 ambiguity.

Phase 5 may already have delivered a stronger bounded progression slice, but that does not automatically make the branch fit for replacement-scope ratification.

This milestone exists to close the remaining truth debt that would corrupt the ledger from day one:

- unresolved support-boundary ambiguity,
- unresolved proof artifact drift,
- unresolved documentation or release-truth drift,
- unresolved known-divergence ambiguity,
- and unresolved Phase 5 “done enough” language.

This milestone does not construct the ledger itself.

It closes the prior phase honestly so that Phase 6 does not inherit a lie.

## [Milestone technical implementation]

Create one explicit Phase 6 entry gate that confirms the current `src` branch is stable enough to serve as the baseline for replacement-scope ratification.

This milestone must:

- finalize the declared support boundary of the completed Phase 5 slice,
- freeze known preserved behavior and known declared divergences from Phase 5,
- ensure release/documentation truth matches actual support,
- ensure current proof artifacts are discoverable and not scattered across ad hoc notes,
- and publish one formal “Phase 6 begins from this baseline” record.

This milestone must not:

- begin legacy-surface inventory work,
- reopen completed Phase 5 implementation work unless truth is broken,
- or silently carry undocumented ambiguity into the ledger phase.

## [Milestone important notes]

The trap here is bureaucratic dishonesty.

If Phase 5 is described too broadly at entry, then every later classification decision gets poisoned by fake assumptions about what `src` already supports.

This milestone is successful only if the Phase 6 baseline is narrower, clearer, and more explicit than whatever informal narrative currently exists.

## [Milestone acceptance criteria]

At the end of this milestone:

- the supported Phase 5 slice is explicitly restated,
- known Phase 5 divergences are recorded,
- current proof artifacts are linked to that slice,
- documentation and release-truth surfaces no longer overclaim support,
- and a formal Phase 6 entry gate exists.

## Task

- [ ] (checkbox) - [Task 1] - Freeze the exact supported Phase 5 slice as the official Phase 6 baseline
- [ ] (checkbox) - [Task 2] - Consolidate known Phase 5 preserved behaviors, divergences, and unsupported remainder into one record
- [ ] (checkbox) - [Task 3] - Reconcile documentation, support statements, and release-truth surfaces with the actual Phase 5 baseline
- [ ] (checkbox) - [Task 4] - Consolidate Phase 5 proof artifacts into a discoverable entry package
- [ ] (checkbox) - [Task 5] - Publish the formal “Phase 6 ready” gate

---

# [Milestone 2] - Canonical Legacy Surface Inventory

## [Milestone Description]

Milestone 2 constructs the authoritative inventory of the old `src` replacement surface.

Its purpose is to answer one question cleanly:

What exactly exists in legacy `src` that could still require replacement, ratified divergence, explicit non-support, or retirement?

This milestone looks only at the legacy side.

It does not judge whether `src` already covers those behaviors.
It does not classify parity status.
It does not assign implementation phases.

It only normalizes the old world into an auditable inventory.

## [Milestone technical implementation]

Create one canonical legacy inventory using both checklist families and the uploaded original source/test snapshots as the organizing evidence.

This milestone must:

- enumerate the RPG-core semantic replacement surface,
- enumerate the add-on system-compatibility replacement surface,
- normalize item granularity so the ledger compares like with like,
- attach original evidence paths for each inventory item,
- and define the canonical row identity for later comparison.

This milestone must not:

- classify items as preserved/divergent/unsupported/retired,
- decide whether `src` already satisfies the item,
- or assign future proof or implementation ownership.

## [Milestone important notes]

The trap here is bad granularity.

If the inventory mixes large subsystems, tiny tests, vague concepts, and release surfaces in inconsistent units, the rest of Phase 6 becomes impossible to govern.

This milestone is successful only if every legacy row is precise enough to compare and coarse enough to remain manageable.

## [Milestone acceptance criteria]

At the end of this milestone:

- the full legacy replacement surface is enumerated,
- RPG-core and add-on compatibility surfaces are both included,
- every row has a canonical identifier and original evidence path,
- item granularity is consistent enough for later comparison,
- and no later milestone needs to “discover” missing legacy scope informally.

## Task

- [ ] (checkbox) - [Task 1] - Build the canonical row schema for the legacy replacement ledger
- [ ] (checkbox) - [Task 2] - Enumerate the RPG-core semantic replacement surface from the existing checklist family
- [ ] (checkbox) - [Task 3] - Enumerate the add-on system-compatibility replacement surface from the separate compatibility checklist
- [ ] (checkbox) - [Task 4] - Normalize row granularity so behaviors, contracts, and consumer surfaces are comparable
- [ ] (checkbox) - [Task 5] - Attach original `src` source/test evidence to every legacy row
- [ ] (checkbox) - [Task 6] - Freeze the canonical legacy inventory as the comparison baseline for later milestones

---

# [Milestone 3] - Canonical `src` Surface Inventory

## [Milestone Description]

Milestone 3 constructs the authoritative inventory of the current `src` replacement surface.

Its purpose is to answer the mirror question:

What does `src` actually implement, prove, expose, and claim today?

This milestone looks only at the current `src` side.

It does not reopen legacy inventory work.
It does not classify final replacement status yet.
It does not assign target future phases yet.

It creates the evidence-backed current-state map that the replacement ledger needs.

## [Milestone technical implementation]

Create one canonical `src` inventory that maps current source, tests, support claims, proof artifacts, and declared boundaries into the same comparison unit used by the legacy inventory.

This milestone must:

- enumerate implemented `src` slices relevant to replacement,
- attach current source and test evidence for each row,
- record current support status where already declared,
- record current proof paths where already present,
- and flag rows where `src` evidence is ambiguous, partial, or decorative.

This milestone must not:

- declare final parity status,
- decide whether ambiguity is acceptable,
- or map remaining work into future implementation phases.

## [Milestone important notes]

The trap here is optimistic interpretation.

This milestone is not allowed to treat “there is code somewhere” as equivalent to “there is a supported slice.”

It must separate:

- implemented,
- test-covered,
- proof-backed,
- support-declared,
- and consumer-usable.

Those are not the same thing.

## [Milestone acceptance criteria]

At the end of this milestone:

- the current `src` replacement-relevant surface is enumerated,
- every comparable row has current evidence attached,
- ambiguous or partial `src` coverage is explicitly flagged,
- support and proof claims are distinguished from raw implementation presence,
- and the project has a current-state map suitable for classification.

## Task

- [ ] (checkbox) - [Task 1] - Build the canonical `src` row schema aligned to the legacy inventory structure
- [ ] (checkbox) - [Task 2] - Enumerate current `src` source surfaces relevant to replacement
- [ ] (checkbox) - [Task 3] - Attach current `src` test and proof evidence to each row where present
- [ ] (checkbox) - [Task 4] - Separate implemented, tested, proof-backed, and officially supported status in the inventory
- [ ] (checkbox) - [Task 5] - Flag rows where `src` evidence is partial, ambiguous, or not yet support-worthy
- [ ] (checkbox) - [Task 6] - Freeze the canonical current-state inventory for use in replacement classification

---

# [Milestone 4] - Replacement Classification and Support Ratification

## [Milestone Description]

Milestone 4 is where the actual replacement ledger begins to mean something.

Its purpose is to compare the canonical legacy inventory against the canonical `src` inventory and classify every row.

This milestone decides status.
It does not yet design the future proof program in detail.
It does not yet build the execution backlog for later phases.

Its job is to replace vague progress language with auditable truth.

## [Milestone technical implementation]

Create one authoritative classification pass across all ledger rows.

Every row must be classified as one of:

- preserved,
- intentionally divergent,
- unsupported,
- retired.

This milestone must:

- compare original evidence and current `src` evidence row by row,
- determine whether preservation is already achieved,
- determine whether an observed mismatch is intentional and acceptable,
- determine whether a legacy item is explicitly unsupported,
- determine whether a legacy item is truly retired and no longer part of the product truth,
- and ratify the current support boundary implied by those decisions.

This milestone must not:

- assign detailed proof implementation work to future phases yet,
- reopen inventory normalization arguments except for genuine blocking defects,
- or hide undecided items under vague temporary labels.

## [Milestone important notes]

The trap here is cowardice.

If the team invents soft statuses like “partially close,” “basically replaced,” or “probably okay,” this milestone fails.

A replacement ledger that cannot make hard classification calls is not a ledger.
It is a mood board.

## [Milestone acceptance criteria]

At the end of this milestone:

- every inventory row has one formal replacement status,
- current support boundaries are ratified from those statuses,
- intentional divergences are distinguished from accidental mismatches,
- unsupported and retired behavior are explicitly named,
- and no material legacy row remains unclassified.

## Task

- [ ] (checkbox) - [Task 1] - Compare canonical legacy and `src` rows one by one using the frozen inventories
- [ ] (checkbox) - [Task 2] - Classify each row as preserved, intentionally divergent, unsupported, or retired
- [ ] (checkbox) - [Task 3] - Record concise divergence rationale for every intentionally divergent row
- [ ] (checkbox) - [Task 4] - Record explicit non-support rationale for every unsupported row
- [ ] (checkbox) - [Task 5] - Record retirement rationale for every retired row so dead scope cannot quietly return
- [ ] (checkbox) - [Task 6] - Ratify the current official support boundary implied by the completed classifications
- [ ] (checkbox) - [Task 7] - Publish the first complete authoritative replacement ledger

---

# [Milestone 5] - Proof Path Mapping and Future Phase Allocation

## [Milestone Description]

Milestone 5 converts the classified ledger into an execution architecture for the remaining rewrite.

Its purpose is to answer two questions for every row that is not already fully closed:

- What proof path is required?
- Which future phase owns closure?

This milestone consumes the classifications from Milestone 4.
It does not re-decide the classifications.
It does not yet build sprint-level implementation tasks.

It turns replacement truth into future-phase structure.

## [Milestone technical implementation]

Create one allocation model that maps every open ledger row to:

- a proof path,
- a target phase,
- a phase dependency,
- and a closure condition.

This milestone must:

- assign proof path types such as characterization, differential, contract, regression, lifecycle, certification, compatibility, or cutover validation,
- assign target closure phases across Phases 7 through 10 where implementation or closure belongs,
- identify rows that must be closed before later rows can honestly proceed,
- identify rows whose proof depends on earlier substrate closure,
- and define what counts as closure for each row so later phases do not improvise their own finish lines.

This milestone must not:

- reopen support-ratification decisions from Milestone 4,
- create sprint-level engineering tasks yet,
- or quietly move unresolved classification ambiguity into “future proof work.”

## [Milestone important notes]

The trap here is phase pollution.

If combat rows leak into substrate ownership, if compatibility rows get buried under gameplay work, or if proof paths are left generic, later phases will duplicate work and miss real blockers.

This milestone is successful only if future work becomes cleaner, not messier.

## [Milestone acceptance criteria]

At the end of this milestone:

- every non-closed row has an assigned proof path,
- every non-closed row has an assigned future phase owner,
- cross-phase dependencies are explicit,
- closure conditions are explicit,
- and Phases 7 through 10 can be planned without re-litigating Phase 6 decisions.

## Task

- [ ] (checkbox) - [Task 1] - Define the allowed proof-path taxonomy for remaining replacement rows
- [ ] (checkbox) - [Task 2] - Assign a proof path to every non-closed ledger row
- [ ] (checkbox) - [Task 3] - Assign every non-closed ledger row to a target closure phase across Phases 7 through 10
- [ ] (checkbox) - [Task 4] - Record phase dependencies and prerequisite relationships between rows
- [ ] (checkbox) - [Task 5] - Define explicit closure conditions per row so later phases inherit fixed finish lines
- [ ] (checkbox) - [Task 6] - Publish the authoritative phase-allocation map derived from the ledger

---

# [Milestone 6] - Execution Baseline Publication and Governance Lock

## [Milestone Description]

Milestone 6 is the exit gate for Phase 6.

Its purpose is to convert the ledger and phase-allocation map into the official execution baseline for the remainder of the rewrite.

This milestone does not redo inventory.
It does not redo classification.
It does not widen scope.

It packages the Phase 6 output into the control system that the later phases must obey.

## [Milestone technical implementation]

Create one published execution baseline and one governance lock that prevents later phases from drifting back into informal scope management.

This milestone must:

- publish the master ledger and phase-allocation map as official project artifacts,
- derive the high-level execution backlog for Phases 7 through 10 from those artifacts,
- define the rules for introducing new legacy rows, merging rows, or changing row status,
- define the rules for declaring new divergences or new unsupported items,
- and link later phase planning to the locked ledger rather than to informal narratives.

This milestone must not:

- reopen settled classification arguments without formal change control,
- invent untracked work outside the ledger,
- or allow future phase plans to claim support beyond the ratified baseline.

## [Milestone important notes]

The trap here is regression into chaos.

Teams often do the hard thinking once, publish a document, and then immediately go back to acting from memory and vibes.

If that happens here, Phase 6 was wasted.

## [Milestone acceptance criteria]

At the end of this milestone:

- the master replacement ledger is published,
- the phase-allocation map is published,
- the future-phase execution baseline is published,
- governance rules for status and scope changes are published,
- and future phase planning is formally constrained by the Phase 6 output.

## Task

- [ ] (checkbox) - [Task 1] - Publish the master replacement ledger as an official project artifact
- [ ] (checkbox) - [Task 2] - Publish the official phase-allocation map for Phases 7 through 10
- [ ] (checkbox) - [Task 3] - Derive the high-level remaining execution backlog from the locked ledger
- [ ] (checkbox) - [Task 4] - Define change-control rules for new rows, status changes, and divergence decisions
- [ ] (checkbox) - [Task 5] - Link later phase plans and dashboards to the Phase 6 ledger baseline
- [ ] (checkbox) - [Task 6] - Publish the formal “Phase 6 complete” exit package
