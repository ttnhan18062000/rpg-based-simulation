# High-Level Implementation Plan — Phase 7 of `src_v2`

This plan assumes Phase 6 has already produced:

- a frozen replacement ledger,
- a ratified support boundary,
- explicit preserved/divergent/unsupported/retired classifications,
- and a phase-allocation map for the remaining rewrite.

It also assumes the project has stopped pretending that “a lot of engine/runtime law exists” is the same thing as “the replacement substrate is done.”

Phase 7 is not the phase where the project should widen into major combat recovery, broad strategic cognition recovery, or full system compatibility closure.

It is the phase where `src_v2` must complete the deterministic substrate that all later preserved gameplay and compatibility claims depend on.

The purpose of Phase 7 is:

- close the remaining authoritative action/update substrate gaps,
- close authoritative apply-path and conflict-resolution gaps,
- close snapshot, immutability, deep-isolation, and serialization truth gaps,
- close deterministic world-generation and engine phase-order gaps,
- close replay-visible deterministic-state-shape gaps,
- and publish the substrate support/proof boundary that later phases must inherit.

This is the phase where the project earns the right to trust later semantic work.

---

# [Milestone 1] - Phase 6 Exit Closure and Phase 7 Readiness

## [Milestone Description]

Milestone 1 is the entry gate for Phase 7.

Its purpose is to stop the team from starting substrate closure while Phase 6 output is still unstable, informal, or not actually governing the work.

By this point, the project may already have:

- a master replacement ledger,
- future phase ownership mapping,
- and a declared Phase 7 substrate scope.

That is still not enough.

This milestone exists because Phase 7 should not proceed while:

- the Phase 6 ledger still has unresolved row ownership for substrate items,
- closure conditions for substrate rows remain vague,
- support claims still overstate substrate completion,
- or later semantic rows are still implicitly compensating for substrate drift.

This milestone does not close substrate behavior itself.

It closes the planning-to-implementation boundary honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 7.

This milestone must:

- freeze the exact set of replacement-ledger rows owned by Phase 7,
- freeze the closure conditions for those rows,
- confirm no Phase 8, 9, or 10 work is silently depending on unfinished Phase 7 behavior without being marked as blocked,
- restate the current substrate support boundary honestly,
- and publish one formal “Phase 7 begins from this substrate gap set” record.

This milestone must not:

- reopen Phase 6 classification work except where a genuine ledger defect exists,
- start broad semantic recovery under the excuse of “touching substrate,”
- or let open Phase 7 ambiguity survive into implementation.

## [Milestone important notes]

The trap here is pretending that Phase 6 being “complete enough” means the Phase 7 substrate backlog is automatically stable.

That is false.

If substrate-owned rows are still mixed with semantic or compatibility rows, this phase will immediately duplicate work and muddy ownership.

## [Milestone acceptance criteria]

At the end of this milestone:

- the exact Phase 7 substrate row set is frozen,
- substrate closure conditions are explicit,
- downstream dependency blockers are visible,
- the current substrate support boundary is restated honestly,
- and the branch has an explicit “Phase 7 ready” gate.

---

# [Milestone 2] - Authoritative Action and Typed Update Substrate Closure

## [Milestone Description]

Milestone 2 closes the remaining authoritative action/update model.

Its purpose is to ensure that gameplay intent and gameplay side effects live in the substrate as structured authoritative truth, not as scattered mutation behavior.

This milestone covers the semantic container model, not the full application pipeline.

It is about what an action is, what an update is, and what the engine is allowed to carry between thought and authority.

It does not yet close conflict resolution or authoritative application behavior itself.

## [Milestone technical implementation]

Complete the authoritative action/update substrate in a way that matches the preserved replacement surface and V2 contract model.

This milestone must:

- close any remaining gaps in typed action proposal structure,
- close any remaining gaps in typed update buckets or equivalent authoritative update domains,
- close reason/target coercion gaps where legacy inputs still need structured representation,
- ensure worker-side thought produces intent rather than world mutation,
- ensure update representations remain granular enough for partial rejection and replay-visible authority,
- and remove or fence off legacy-style hidden mutation paths that bypass the authoritative substrate.

This milestone must not:

- treat “we can carry some updates already” as sufficient closure,
- bundle apply-path logic into the representation-layer milestone,
- or preserve legacy shape leaks that violate the V2 authority model.

## [Milestone important notes]

The trap here is settling for an action/update model that is good enough for demos but not strict enough for authoritative replacement.

If action proposals and updates are still fuzzy, every later semantic port will keep re-embedding logic in the wrong layer.

## [Milestone acceptance criteria]

At the end of this milestone:

- authoritative action intent shape is explicit,
- authoritative update shape is explicit,
- reason/target structure is normalized where required,
- worker-side mutation shortcuts are no longer part of supported behavior,
- and the project has one authoritative action/update substrate that later phases can build on.

---

# [Milestone 3] - Authoritative Apply Path and Conflict Resolution Closure

## [Milestone Description]

Milestone 3 closes the authoritative application model.

Its purpose is to ensure that one authoritative outcome is produced per tick through one authoritative apply path, even when proposals conflict, partially fail, or touch multiple update domains.

This milestone consumes the action/update substrate from Milestone 2.

It is about how authoritative truth is applied, rejected, merged, or isolated.

It does not yet close snapshot immutability or world-generation determinism.

## [Milestone technical implementation]

Close the authoritative apply path so that later semantic work cannot quietly redefine world truth.

This milestone must:

- ensure authoritative world mutation occurs only after proposal generation,
- ensure conflicting proposals resolve through one authoritative path,
- ensure partial rejection does not corrupt unrelated update domains,
- ensure apply-order behavior is explicit and deterministic,
- ensure authoritative outcomes are the source for replay/observability rather than worker intent alone,
- and close any remaining gaps between represented updates and applied updates.

This milestone must not:

- defer partial-rejection correctness to later gameplay phases,
- let replay or observability become hidden sources of semantic truth,
- or preserve multiple quasi-authoritative application paths.

## [Milestone important notes]

The trap here is believing that “there is an apply path” means “authority is closed.”

Not true.

If unrelated update domains can still be corrupted by rejection behavior, or if multiple authoritative outcomes can leak through, then the substrate is still weak.

## [Milestone acceptance criteria]

At the end of this milestone:

- one authoritative apply path exists for the supported substrate,
- conflict resolution behavior is explicit,
- partial rejection is safe across update domains,
- authoritative outcomes define replay-visible truth,
- and one authoritative outcome per tick is enforced for the supported substrate.

---

# [Milestone 4] - Snapshot Integrity, Isolation, and Serialization Closure

## [Milestone Description]

Milestone 4 closes the snapshot and state-isolation substrate.

Its purpose is to ensure the engine’s read surfaces are not secretly mutable, not aliasing live state, and not producing serialization behavior that undermines determinism or authority.

This milestone is about state integrity, not world generation and not phase ordering.

It covers:

- snapshot immutability,
- deep-copy isolation where required,
- serialization stability,
- and authoritative state-shape discipline.

## [Milestone technical implementation]

Complete the snapshot and serialization substrate so that reads, exports, replay surfaces, and inspection surfaces cannot quietly redefine or contaminate authority.

This milestone must:

- enforce snapshot immutability for supported read surfaces,
- ensure deep isolation where snapshots are expected to be independent from live mutation,
- close serialization-shape drift that undermines deterministic comparison or replay,
- ensure authoritative state can be exported and compared without hidden mutation leaks,
- and define the supported deterministic state shape used by proof, replay, and later parity work.

This milestone must not:

- rely on “tests happened not to mutate it” as the integrity guarantee,
- leave ambiguous whether read surfaces are live views or frozen authority views,
- or treat serialization as a compatibility-only concern.

## [Milestone important notes]

The trap here is underestimating snapshot bugs because they look like test plumbing problems.

They are not test plumbing problems.
They are authority problems.

If snapshots are mutable or alias live objects, later semantic parity claims become untrustworthy.

## [Milestone acceptance criteria]

At the end of this milestone:

- snapshot immutability is enforced for the supported substrate,
- deep-copy or equivalent isolation guarantees are explicit,
- deterministic serialization shape is explicit,
- authoritative state export is trustworthy for proof and replay,
- and snapshot/state integrity is no longer a hidden risk surface.

---

# [Milestone 5] - Deterministic World Generation and Engine Phase-Order Closure

## [Milestone Description]

Milestone 5 closes the execution substrate that defines how the world is formed and how the engine advances it in deterministic order.

Its purpose is to stop later phases from inheriting drift caused by world-init nondeterminism, ordering ambiguity, or unstable subsystem sequencing.

This milestone covers:

- deterministic world generation,
- deterministic entity initialization relevant to supported substrate scope,
- engine phase order,
- subsystem tick order,
- and tick-integrity guarantees.

It does not cover combat or broader semantic recovery itself.

## [Milestone technical implementation]

Close the deterministic runtime baseline so that later semantic work sits on a stable execution substrate.

This milestone must:

- ensure supported world-generation behavior is deterministic under equivalent inputs,
- ensure supported entity initialization is deterministic where preservation or V2 contract requires it,
- ensure engine tick phases execute in explicit and deterministic order,
- ensure subsystem sequencing is not defined by incidental implementation details,
- ensure tick-integrity rules are explicit for supported paths,
- and define which parts of initialization/order are supported replacement surface versus intentionally divergent or out of current scope.

This milestone must not:

- silently preserve accidental old ordering quirks without classification,
- let concurrency or infrastructure timing redefine baseline semantics,
- or leave subsystem ordering as an implementation accident.

## [Milestone important notes]

The trap here is treating world generation and engine order as low-level mechanics that can be cleaned up later.

That is backwards.

If the baseline world or tick order drifts, later parity mismatches will be misdiagnosed as gameplay problems.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported world-generation behavior is deterministic,
- supported entity initialization behavior is deterministic,
- engine phase order is explicit,
- subsystem tick order is explicit,
- and later semantic phases inherit a stable deterministic baseline.

---

# [Milestone 6] - Replay-Visible Deterministic State Closure and Phase 7 Exit Package

## [Milestone Description]

Milestone 6 is the exit gate for Phase 7.

Its purpose is to prove and publish the deterministic substrate that later phases are now required to trust.

This milestone does not widen semantic support.
It does not start combat or strategic recovery.
It does not start compatibility closure.

It packages the completed substrate into one explicit support/proof boundary and closes the phase honestly.

## [Milestone technical implementation]

Create one Phase 7 exit package that turns the completed substrate into a reviewable and enforceable baseline.

This milestone must:

- verify that replay-visible authoritative state shape matches the supported deterministic substrate,
- verify that authoritative outcomes, snapshots, and serialized state are coherent enough for later proof work,
- publish the supported deterministic substrate boundary,
- publish known intentional divergences, unsupported remainder, and remaining blocked rows,
- and publish one formal “Phase 7 complete” package that later phases must inherit.

This milestone must not:

- overclaim semantic replacement beyond the substrate,
- describe partial substrate closure as full-engine closure,
- or leave later phases to infer what Phase 7 actually settled.

## [Milestone important notes]

The trap here is familiar: you will want to describe this phase as bigger than it is because substrate work is expensive and invisible.

Do not do that.

If you overclaim here, Phase 8 and Phase 9 will inherit fake certainty and waste months.

## [Milestone acceptance criteria]

At the end of this milestone:

- replay-visible deterministic substrate truth is explicitly defined,
- Phase 7 support boundaries are explicit,
- known divergences and unsupported remainder are explicit,
- remaining blocked semantic rows are visible,
- and the branch has a formal “Phase 7 complete” exit package.
