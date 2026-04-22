Good. Phase 9 is where the rewrite either recovers the game’s mind, or keeps pretending local behavior is enough.

After Phase 8, the trap is obvious: once combat and local action look credible, people start saying “the core game is basically back.” That is false. What is still missing is the layer that gives the world continuity, consequence, memory, and progression meaning.

This Phase 9 plan is grounded in the roadmap and checklist surfaces from [resource_phases.md](sandbox:/mnt/data/resource_phases.md), [legacy_logic_checklist_part4.md](sandbox:/mnt/data/legacy_logic_checklist_part4.md), [legacy_logic_checklist_part5.md](sandbox:/mnt/data/legacy_logic_checklist_part5.md), and the V2 completion rules in [src_v2_principle.md](sandbox:/mnt/data/src_v2_principle.md).

---

# High-Level Implementation Plan — Phase 9 of `src_v2`

This plan assumes Phase 8 has already produced:

- a supported direct combat semantic slice,
- a supported bounded local tactical slice,
- a supported local environment/world-interaction slice,
- explicit divergences and unsupported remainder for those local semantics,
- and a formal Phase 8 exit package that later phases are required to trust.

It also assumes the project has stopped pretending that local gameplay closure is the same thing as long-horizon game meaning.

Phase 9 is not the phase where the project should widen into legacy system compatibility, cutover, or runtime retirement.

It is the phase where `src_v2` must recover the next large semantic surface of original `src`:

- strategic continuity,
- bounded cognition and explainability,
- blockers, leads, and knowledge continuity,
- social consequence and contracts,
- progression, classes, skills, attributes, and rewards.

The purpose of Phase 9 is:

- close the preserved long-horizon strategic and cognitive surface from legacy `src`,
- close the first-class social consequence and contract surface where preservation is required,
- close progression and RPG-math semantics that materially affect character growth and reward truth,
- prove the supported Phase 9 semantic slice against original `src` where preservation is required,
- and publish the supported strategic/social/progression boundary honestly for Phase 10 and later phases.

This is the phase where the project must recover meaning over time without collapsing back into a vague “AI phase.”

---

# [Milestone 1] - Phase 8 Exit Closure and Phase 9 Readiness

## [Milestone Description]

Milestone 1 is the entry gate for Phase 9.

Its purpose is to stop the team from starting long-horizon cognition and progression recovery while the Phase 8 local-gameplay baseline is still unstable, overstated, or not actually trusted.

By this point, the branch may already have:

- credible local combat behavior,
- a formal Phase 8 exit package,
- and broad pressure to “just bring back AI and progression.”

That is still not enough.

This milestone exists because Phase 9 should not proceed while:

- strategic/cognitive rows are still mixed with Phase 8 tactical rows,
- social/contract rows are still mixed with compatibility or cutover rows,
- progression rows are still mixed with local combat semantics already owned by Phase 8,
- closure conditions remain vague,
- or current support language implies broader mind/progression recovery than the branch actually has.

This milestone does not recover strategic or progression behavior itself.

It closes the local-gameplay-to-long-horizon handoff honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 9.

This milestone must:

- freeze the exact set of replacement-ledger rows owned by Phase 9,
- separate strategic/cognitive/social/progression rows from Phase 8 local tactical rows,
- separate Phase 9 rows from Phase 10 compatibility rows,
- restate the current support boundary honestly for strategic/social/progression scope,
- confirm downstream work is not assuming unsupported long-horizon semantics,
- and publish one formal “Phase 9 begins from this semantic gap set” record.

This milestone must not:

- reopen Phase 8 local semantic closure except where a genuine handoff defect exists,
- start compatibility work under the excuse of “consumer-facing AI behavior,”
- or allow long-horizon strategic meaning to get confused with local tactical behavior.

## [Milestone important notes]

The trap here is garbage-bucket thinking.

If “AI,” “social,” “strategy,” “memory,” and “progression” are allowed to blend into one fuzzy ownership zone, the phase becomes unfinishable.

## [Milestone acceptance criteria]

At the end of this milestone:

- the exact Phase 9 row set is frozen,
- strategic/cognitive/social/progression scope is separated from local tactical scope and compatibility scope,
- closure conditions for Phase 9 rows are explicit,
- the current support boundary is restated honestly,
- and the branch has an explicit “Phase 9 ready” gate.

---

# [Milestone 2] - Strategic Continuity, Bounded Cognition, and Explainability Closure

## [Milestone Description]

Milestone 2 closes the long-horizon strategic continuity layer and the bounded cognition layer that supports it.

Its purpose is to recover the part of the game where actors behave like they have limited minds with persistent priorities, bounded attention, and explainable continuity across ticks.

This milestone covers:

- project continuity and switching,
- interruption resistance,
- bounded active-slice logic,
- bounded concern intake and lead retention,
- cognition-capacity derivation,
- overload/explainability surfaces,
- and strategic continuity rules that persist across ticks.

It is about bounded mind and continuity, not local tactical combat behavior.

It does not yet close social consequence, contracts, or progression math itself.

## [Milestone technical implementation]

Recover the supported strategic continuity and cognition layer in native `src_v2` terms.

This milestone must:

- recover supported strategic continuity behavior across ticks,
- recover bounded cognition-capacity rules and deterministic profile derivation,
- recover interruption, abandonment, and switch/retention semantics where preservation is required,
- recover explainability metadata where the legacy surface requires it,
- and keep the cognition layer bounded rather than turning it into an ungoverned planner.

This milestone must not:

- absorb local tactical logic already owned by Phase 8,
- absorb social consequence or progression logic owned by later Phase 9 milestones,
- or hide missing strategic semantics behind vague “AI improvement” language.

## [Milestone important notes]

The trap here is pretending that because agents now move and fight better, they therefore “have strategy.”

They do not.

Phase 9 starts where local behavior ends and persistent bounded intention begins.

## [Milestone acceptance criteria]

At the end of this milestone:

- strategic continuity rules are explicit,
- bounded cognition-capacity rules are explicit,
- continuity across ticks is explicit where supported,
- explainability surfaces are explicit where supported,
- and the project has one credible long-horizon strategic/cognitive slice.

---

# [Milestone 3] - Blockers, Leads, Knowledge Continuity, and Resource Intelligence Closure

## [Milestone Description]

Milestone 3 closes the knowledge-and-resource intelligence layer that turns strategic lack into directed future behavior.

Its purpose is to recover how actors recognize missing needs, preserve blockers, use leads, resolve knowledge gaps, and update strategic state over time without cheating.

This milestone covers:

- blocker generation and persistence,
- blocker resolution,
- lead creation, testing, retention, and suppression,
- knowledge continuity across ticks,
- source trust and certainty handling where preserved,
- and resource-intelligence behavior that sits above local action and below broader social meaning.

It is not a repetition of Phase 5’s bounded resource loop. It is the long-horizon intelligence layer built on top of it.

## [Milestone technical implementation]

Recover the supported blocker/lead/knowledge-intelligence layer in a way that is deterministic, bounded, and faithful to the preserved replacement surface.

This milestone must:

- recover supported blocker generation and persistence semantics,
- recover supported blocker-resolution logic tied to acquisitions and state change,
- recover supported lead retention, testing, suppression, and continuity behavior,
- recover supported uncertainty/anti-cheating rules where preservation is required,
- and keep the knowledge layer bounded rather than turning it into a perfect-information planner.

This milestone must not:

- duplicate Phase 5’s direct resource-resolution logic,
- duplicate Phase 8’s local-world semantics,
- or absorb broader social contract meaning that belongs to the next milestone.

## [Milestone important notes]

The trap here is silent cheating.

The fastest way to make this phase look successful is to let agents infer too much from perfect internal state. That is exactly what this phase must prevent.

## [Milestone acceptance criteria]

At the end of this milestone:

- blocker and lead semantics are explicit,
- persistence and resolution behavior are explicit where supported,
- uncertainty and anti-cheating behavior are explicit where supported,
- resource intelligence remains bounded and long-horizon,
- and the project has one credible blocker/lead/knowledge slice.

---

# [Milestone 4] - Social Consequence, Contracts, Trust, and Recruitment Closure

## [Milestone Description]

Milestone 4 closes the social meaning layer.

Its purpose is to recover how social memory, betrayal, trust, debt, contracts, and recruitment consequences shape future behavior rather than remaining isolated narrative artifacts.

This milestone covers:

- betrayal and social trauma consequences,
- trust/debt/reputation effects where preserved,
- recruitment and contract semantics,
- candidate filtering and alliance-related decision surfaces,
- and social state transitions that materially affect long-horizon behavior.

It does not yet close progression math, class identity, or reward formulas.

## [Milestone technical implementation]

Recover the supported social consequence and contract layer in native `src_v2` terms.

This milestone must:

- recover supported betrayal-memory and social consequence semantics,
- recover supported recruitment-offer evaluation consequences,
- recover supported trust/debt/relationship effects where preservation is required,
- recover contract-related long-horizon semantics that materially affect strategic choice,
- and define the supported social boundary explicitly rather than leaving it implied.

This milestone must not:

- absorb broad economic or compatibility scope,
- reduce social meaning to generic mood modifiers,
- or hide missing social semantics behind narrative wording.

## [Milestone important notes]

The trap here is fake richness.

A few relationship flags or memory records are not social consequence closure. What matters is whether those records actually alter future strategic and contract behavior in preserved ways.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported social consequence semantics are explicit,
- supported contract/recruitment semantics are explicit,
- trust/debt/reputation effects are explicit where supported,
- preserved versus divergent social semantics are explicit,
- and the project has one credible social/contract slice.

---

# [Milestone 5] - Progression, Classes, Skills, Attributes, and Rewards Closure

## [Milestone Description]

Milestone 5 closes the RPG progression layer.

Its purpose is to recover the math and progression semantics that make outcomes accumulate into character growth and class identity over time.

This milestone covers:

- level-up and advancement behavior,
- veterancy and training semantics,
- talents and breakthroughs,
- class and gear identity where preserved,
- skill scaling,
- attribute synergy,
- kill/reward emission semantics,
- and other progression math that materially affects long-horizon gameplay truth.

It is not local combat, and it is not compatibility plumbing.

## [Milestone technical implementation]

Recover the supported progression layer in a way that is deterministic, bounded, and explicit about preserved versus divergent behavior.

This milestone must:

- recover supported leveling, veterancy, and training behavior,
- recover supported talent/breakthrough and class/gear semantics,
- recover supported skill-scaling and attribute-synergy behavior,
- recover supported reward-emission semantics tied to authoritative apply behavior,
- and define what parts of progression math are preserved, intentionally divergent, or still unsupported.

This milestone must not:

- duplicate Phase 8’s local combat semantics,
- hide broken formulas behind broad “balance changes” language,
- or defer reward/emission truth to a future unspecified phase.

## [Milestone important notes]

The trap here is hand-wavy balance talk.

This phase is not about making the system feel balanced. It is about closing the preserved progression math and growth semantics that the old game actually depended on.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported progression semantics are explicit,
- supported class/skill/attribute semantics are explicit,
- supported reward-emission semantics are explicit,
- preserved versus divergent progression math is explicit,
- and the project has one credible progression slice.

---

# [Milestone 6] - Differential Proof, Support Ratification, and Phase 9 Exit Package

## [Milestone Description]

Milestone 6 turns the recovered Phase 9 semantic slices into auditable replacement truth and closes the phase honestly.

Its purpose is to ensure strategic/social/progression support is proven rather than merely implemented.

This milestone covers:

- characterization of preserved legacy behavior,
- differential old-vs-new proof where preservation is required,
- explicit divergence logging where preservation is not required,
- support-boundary ratification,
- replacement-ledger updates,
- and the handoff baseline for Phase 10.

It does not widen semantic support.
It proves, classifies, and packages the recovered slice.

## [Milestone technical implementation]

Create one proof and ratification pass across the supported Phase 9 slice.

This milestone must:

- add or consolidate characterization tests against original `src` where needed,
- add differential tests for preserved strategic/social/progression behavior,
- log intentional divergences explicitly,
- ratify the supported boundary for preserved and divergent behavior,
- update the replacement ledger for completed Phase 9 rows,
- publish known unsupported remainder,
- and publish one formal “Phase 9 complete” package that later phases must inherit.

This milestone must not:

- confuse richer-looking behavior with preserved behavior,
- defer divergence logging until compatibility/cutover phases,
- or overclaim support because the branch now feels more like a full RPG again.

## [Milestone important notes]

The trap here is the worst one so far.

Once long-horizon strategy, social consequence, and progression start working together, the branch will feel dramatically more complete. That is exactly when teams start lying to themselves about how much is actually proven.

## [Milestone acceptance criteria]

At the end of this milestone:

- preserved Phase 9 behavior has proof where required,
- intentional divergences are logged,
- unsupported remainder remains explicit,
- the support boundary is ratified from evidence,
- replacement-ledger updates are complete,
- and the branch has a formal “Phase 9 complete” handoff baseline.

---

## Why these milestones do not duplicate each other

Milestone 2 is about **bounded strategic continuity and cognition**.

Milestone 3 is about **blockers, leads, knowledge continuity, and resource intelligence**.

Milestone 4 is about **social consequence, contracts, trust, and recruitment**.

Milestone 5 is about **progression math, class identity, skills, attributes, and rewards**.

Milestone 6 is about **proof, ratification, and handoff**, not more semantic widening.

If you merge these, you will get exactly the kind of fake “AI/progression/social overhaul” phase that sounds ambitious and guarantees duplicated work.
