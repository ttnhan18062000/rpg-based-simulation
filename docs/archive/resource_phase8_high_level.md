Below is the **high-level implementation plan for Phase 8** in the same milestone style as the earlier high-level phase plans.

This plan is grounded in the corrected roadmap and the legacy replacement surfaces described in [resource_phases.md](sandbox:/mnt/data/resource_phases.md), [legacy_logic_checklist_part1.md](sandbox:/mnt/data/legacy_logic_checklist_part1.md), [legacy_logic_checklist_part4.md](sandbox:/mnt/data/legacy_logic_checklist_part4.md), [legacy_logic_checklist_part5.md](sandbox:/mnt/data/legacy_logic_checklist_part5.md), and the V2 completion rules in [src_v2_principle.md](sandbox:/mnt/data/src_v2_principle.md).

---

# High-Level Implementation Plan — Phase 8 of `src_v2`

This plan assumes Phase 7 has already produced:

- a closed deterministic substrate for supported authority paths,
- explicit action/update and apply-path contracts,
- explicit snapshot and serialization integrity guarantees,
- explicit world/init/order contracts,
- and a formal Phase 7 exit package that later phases are required to trust.

It also assumes the project has stopped pretending that substrate closure is the same thing as gameplay recovery.

Phase 8 is not the phase where the project should widen into broad strategic cognition recovery, social consequence recovery, progression/class math, or system-compatibility closure.

It is the phase where `src_v2` must recover the next large semantic surface of original `src`:

- combat legality,
- combat outcome semantics,
- tactical bounded decision-making,
- threat/engagement/disengagement behavior,
- and environment/world-interaction semantics that directly shape combat and local action behavior.

The purpose of Phase 8 is:

- close the preserved combat legality and combat-outcome surface from legacy `src`,
- close bounded tactical selection and engagement behavior where preservation is required,
- close terrain/building/local world-interaction semantics that affect combat or immediate local behavior,
- prove the supported Phase 8 semantic slice against original `src` where preservation is required,
- and publish the supported combat/tactical/world-interaction boundary honestly for Phase 9 and later phases.

This is the phase where the project must recover moment-to-moment gameplay semantics without smuggling broader long-horizon cognition or progression work into the same bucket.

---

# [Milestone 1] - Phase 7 Exit Closure and Phase 8 Readiness

## [Milestone Description]

Milestone 1 is the entry gate for Phase 8.

Its purpose is to stop the team from starting combat/tactical semantic recovery while Phase 7 substrate closure is still unstable, overstated, or not actually trusted.

By this point, the branch may already have:

- a stronger deterministic substrate,
- a formal Phase 7 exit package,
- and a broad sense that “the foundation is ready.”

That is still not enough.

This milestone exists because Phase 8 should not proceed while:

- combat/tactical rows are still mixed with substrate-only or strategy-only rows,
- the current support boundary still overstates what combat/world semantics are already preserved,
- Phase 8 closure conditions remain vague,
- or teams are already compensating for unfinished combat semantics with ad hoc tactical logic.

This milestone does not recover combat or tactical behavior itself.

It closes the substrate-to-semantics handoff honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 8.

This milestone must:

- freeze the exact set of replacement-ledger rows owned by Phase 8,
- separate combat/tactical/local-world rows from Phase 7 substrate rows and Phase 9 strategic/progression rows,
- restate the current support boundary honestly for combat/tactical/world-interaction scope,
- confirm downstream rows are not assuming unsupported combat semantics,
- and publish one formal “Phase 8 begins from this semantic gap set” record.

This milestone must not:

- reopen Phase 7 substrate closure except where a genuine handoff defect exists,
- start progression or strategy recovery under the excuse of “combat context,”
- or allow vague ownership between combat, tactics, and later strategic layers.

## [Milestone important notes]

The trap here is scope collapse.

If Phase 8 is allowed to absorb strategy, social, or progression concerns, the phase loses its purpose and every milestone becomes duplicated by later phases.

## [Milestone acceptance criteria]

At the end of this milestone:

- the exact Phase 8 row set is frozen,
- combat/tactical/local-world scope is separated from later-phase cognition and progression scope,
- closure conditions for Phase 8 rows are explicit,
- the current support boundary is restated honestly,
- and the branch has an explicit “Phase 8 ready” gate.

---

# [Milestone 2] - Combat Legality and Authoritative Combat Outcome Closure

## [Milestone Description]

Milestone 2 closes the core combat legality and direct combat outcome surface.

Its purpose is to ensure that the engine can resolve immediate combat interactions according to preserved rules rather than generic or drifted approximations.

This milestone covers:

- target legality,
- range and adjacency semantics where preserved,
- direct combat interaction validity,
- authoritative combat outcome emission,
- and supported immediate hit / damage / defeat / combat-result semantics.

It is about the local combat contract itself.

It does not yet close broader tactical behavior such as target switching, pursuit, disengagement, anti-stalemate, or environment-aware positioning logic.

## [Milestone technical implementation]

Recover the preserved combat legality and direct combat outcome model in native `src_v2` terms.

This milestone must:

- close the supported legality checks for combat initiation and execution,
- close supported range, adjacency, and target-validity rules,
- ensure combat outcomes are represented and applied through the authoritative substrate closed in Phase 7,
- recover supported defeat / kill / non-lethal outcome semantics where legacy preservation is required,
- and define what parts of direct combat semantics are preserved, intentionally divergent, or still unsupported.

This milestone must not:

- blur legality rules with high-level tactical decision logic,
- bypass authoritative update/apply models for combat outcomes,
- or quietly preserve accidental old behavior without explicit classification.

## [Milestone important notes]

The trap here is pretending that “entities can attack each other” means combat semantics are recovered.

It does not.

If legality, outcome emission, and direct resolution rules are still vague, later tactical work will sit on false assumptions.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported combat legality rules are explicit,
- supported direct combat outcomes are explicit,
- combat results flow through authoritative substrate paths,
- preserved versus divergent combat semantics are explicit,
- and the project has one credible direct-combat semantic slice.

---

# [Milestone 3] - Bounded Tactical Engagement and Local Decision Closure

## [Milestone Description]

Milestone 3 closes the bounded tactical behavior that sits on top of direct combat semantics.

Its purpose is to recover how actors behave in immediate conflict, without widening into long-horizon strategy.

This milestone covers:

- target selection and local tactical prioritization,
- engage versus disengage behavior,
- pursuit, stickiness, and retreat behavior where preserved,
- anti-stalemate handling,
- and bounded tactical evaluation rules.

It is about immediate combat-adjacent behavior under local pressure.

It does not yet close broader strategic continuity, social reasoning, or progression effects.

## [Milestone technical implementation]

Recover the supported bounded tactical layer in a way that is deterministic, local, and compatible with Phase 7 authority rules.

This milestone must:

- recover supported target-selection and local tactical prioritization behavior,
- recover supported engagement/disengagement/pursuit rules,
- recover supported retreat or local tactical fallback behavior where preservation is required,
- close anti-stalemate or local-combat deadlock handling where it is part of preserved gameplay semantics,
- and ensure the tactical evaluator remains bounded rather than becoming an uncontrolled strategic planner.

This milestone must not:

- absorb long-horizon project/blocker/lead logic from Phase 9,
- treat immediate tactical behavior as a generic AI layer with undefined boundaries,
- or let tactical behavior redefine direct combat legality from Milestone 2.

## [Milestone important notes]

The trap here is letting “AI” become a garbage bucket.

Phase 8 is about **local tactical behavior**, not the whole mind of the game.

If you let bounded tactical logic turn into strategic reasoning, the phase will rot and Phase 9 will duplicate it later.

## [Milestone acceptance criteria]

At the end of this milestone:

- bounded local tactical behavior is explicit,
- engage/disengage/pursuit/retreat behavior is explicit where supported,
- anti-stalemate behavior is explicit where supported,
- tactical logic remains bounded and local,
- and the project has a credible tactical behavior slice built on closed combat legality.

---

# [Milestone 4] - Environment, Terrain, Building, and Local World-Interaction Semantic Closure

## [Milestone Description]

Milestone 4 closes the local environment semantics that directly affect combat and immediate world behavior.

Its purpose is to recover the “fight and act in a place” part of the game rather than the long-horizon “plan across the world” part.

This milestone covers:

- terrain or spatial interaction rules that affect immediate legality or tactical choice,
- building/local structure interaction semantics relevant to immediate gameplay,
- chokepoint, bracketing, or position-sensitive local behavior where preserved,
- and immediate world-interaction semantics that materially shape local conflict or action resolution.

It is not a repetition of Phase 5’s broader resource loop, and it is not broader social/town/strategy work.

## [Milestone technical implementation]

Recover the supported local environment/world-interaction semantics in a way that is native to `src_v2` authority and determinism rules.

This milestone must:

- close terrain/building/local-position semantics that affect combat or immediate action behavior,
- recover preserved local environment constraints that shape legality or tactical action,
- define the supported interaction boundary between local world structure and direct gameplay behavior,
- and keep this layer local rather than expanding into broad economy/town/strategy systems.

This milestone must not:

- duplicate Phase 5’s bounded resource-town-progression loop,
- duplicate Phase 9’s strategic or social meaning,
- or invent unsupported environment semantics that were never classified in the replacement ledger.

## [Milestone important notes]

The trap here is turning “world interaction” into an infinite bucket.

It is not.

Phase 8 only owns **local interaction semantics that materially shape direct action and combat behavior**.

## [Milestone acceptance criteria]

At the end of this milestone:

- local environment semantics affecting combat/action are explicit,
- building/terrain/local-position effects are explicit where supported,
- world-interaction scope remains local and bounded,
- preserved versus divergent local semantics are explicit,
- and the project has one credible immediate world-interaction semantic slice.

---

# [Milestone 5] - Differential Proof and Support Ratification for Combat / Tactical / Local World Semantics

## [Milestone Description]

Milestone 5 turns the recovered Phase 8 semantic slices into auditable replacement truth.

Its purpose is to ensure that combat/tactical/local-world support is proven rather than merely implemented.

This milestone covers:

- characterization of preserved legacy behavior,
- differential old-vs-new proof where preservation is required,
- explicit divergence logging where preservation is not required,
- support-boundary ratification,
- and honest naming of unsupported remainder.

It does not widen semantic support.
It proves and classifies the recovered slice.

## [Milestone technical implementation]

Create one proof and ratification pass across the supported Phase 8 slice.

This milestone must:

- add or consolidate characterization tests against original `src` where needed,
- add differential tests for preserved combat/tactical/local-world behavior,
- log intentional divergences explicitly,
- ratify the supported boundary for preserved and divergent behavior,
- and keep unsupported remainder visible instead of quietly shrinking it by omission.

This milestone must not:

- confuse demo behavior with preserved behavior,
- defer divergence logging until later phases,
- or overclaim support simply because the local engine now “feels playable.”

## [Milestone important notes]

The trap here is emotional validation.

Combat and tactics are visible, so once they look good in a run, teams start lying to themselves.

Visible behavior is not replacement proof.

## [Milestone acceptance criteria]

At the end of this milestone:

- preserved combat/tactical/local-world cases have proof where required,
- intentional divergences are logged,
- unsupported remainder remains explicit,
- the support boundary is ratified from evidence,
- and Phase 8 semantics are no longer informal.

---

# [Milestone 6] - Phase 8 Exit Package and Phase 9 Handoff Baseline

## [Milestone Description]

Milestone 6 is the exit gate for Phase 8.

Its purpose is to package the recovered combat/tactical/local-world slice into one explicit support/proof boundary that Phase 9 must inherit rather than reinterpret.

This milestone does not begin broad strategic cognition recovery.
It does not begin social consequence recovery.
It does not begin progression/class/reward closure.

It closes the phase honestly and hands off a stable baseline.

## [Milestone technical implementation]

Create one Phase 8 exit package that turns the supported semantic slice into a reviewable and enforceable baseline.

This milestone must:

- publish the supported combat/tactical/local-world semantic boundary,
- publish known intentional divergences and known unsupported remainder,
- update the replacement ledger for completed Phase 8 rows,
- publish the proof bundle and support statements that justify the Phase 8 claims,
- and define exactly what Phase 9 is allowed to assume from the local gameplay layer.

This milestone must not:

- describe local tactical closure as broad AI closure,
- describe combat/world semantics as broad progression closure,
- or leave Phase 9 to infer what was actually settled.

## [Milestone important notes]

The trap here is inflation.

Once a game can fight and act more credibly, people start talking like “the core game is back.”

That is how later phases inherit fiction.

Phase 8 closes **moment-to-moment combat/tactical/local-world semantics**, not the whole remaining RPG-core surface.

## [Milestone acceptance criteria]

At the end of this milestone:

- the supported combat/tactical/local-world boundary is explicit,
- Phase 8 proof and ledger updates are complete,
- known divergences and unsupported remainder are explicit,
- Phase 9 assumptions are constrained by the exit package,
- and the branch has a formal “Phase 8 complete” handoff baseline.
