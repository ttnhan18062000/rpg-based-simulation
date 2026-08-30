# Core RPG New-Idea Portfolio

Date: 2026-08-27  
Status: brainstorming proposal for review  
Scope: additional core-RPG ideas discovered while reviewing the live simulation and Ideas 1-66  
Constraint: these are candidates, not approved idea numbers, plans, tickets, or implementation specifications

## Purpose

This document asks which additional ideas could make the simulation feel like a living RPG without making it unbounded, computationally noisy, or too expensive to deliver.

It deliberately distinguishes five different situations:

- a genuinely new feature;
- a feature that existed in the legacy engine but is absent from the current authoritative model;
- a live or typed substrate that lacks a producer or consumer;
- a useful composition of existing roadmap ideas;
- an attractive idea that should be folded, deferred, or rejected as a standalone system.

The proposal is grounded in the [Core RPG Feature Review](2026-08-27-core-rpg-feature-review.md), the [Brainstorm-to-Plan Crosswalk](2026-08-27-brainstorm-plan-crosswalk-review.md), the [RPG Feature Atlas](../rpg_feature_atlas.html), and the [RPG Schema Registry](../rpg_expected_schemas.html).

## Design position

The project does not need sixteen new engines. It needs a small number of live loops assembled from mechanisms that already exist or were previously attempted.

The strongest additions are:

1. a durable Household connecting family, home, resources, and succession;
2. commitments that actually alter future choices;
3. witnessed deeds that propagate through memory, testimony, and local reputation;
4. failure that changes later behavior.

The remaining candidates are mostly extensions of those four and Ideas 1-66. They are still documented because knowing what to fold or defer is part of keeping the simulation manageable.

## Assessment vocabulary

### Existing status

- **Live:** used by the normal simulation.
- **Partial:** some current state or behavior exists, but the loop is incomplete.
- **Dormant:** typed code exists but has no normal producer, consumer, or enabled phase.
- **Legacy:** implemented in `src_legacy` or historical work, absent from the current authoritative model.
- **Planned overlap:** substantially covered by Ideas 1-66.
- **New:** no adequate existing feature shape was found.

### Frequency

- **Rare:** birth, death, household formation, succession, or similarly exceptional events.
- **Low:** occasional voluntary social action or long-lived project transition.
- **Medium:** normal goal/project outcomes or recurring social encounters.
- **High:** potentially many times per tick unless explicitly bounded.

### Impact range

`entity < pair < household/group < place < faction < world/campaign`

Frequency and range are separate. A death consequence is rare but can affect a Household and campaign memory; witnessing candidates may be common but should normally materialize only local effects after filtering. Chronicle is an observer surface, not a separate impact range.

### Priority

- **P1:** high-value proposal to review early.
- **P2:** valuable after named dependencies are real.
- **P3:** later option, experiment, or deliberate deferral.

Priority expresses design value, not immediate implementation readiness.

## Portfolio summary

| Candidate | Primary status | Existing anchor or overlap | Raw -> materialized frequency | Normal -> maximum range | Priority | Proposed disposition |
|---|---|---|---:|---|---:|---|
| A. Household continuity | Legacy | Current home/storage/heir anchors are partial | Rare -> rare/low | Household -> campaign | P1 | Standalone foundation |
| B. Promises, favors, debts, and oaths | Dormant | Live Contracts, quests, parties, and social debt | Low/medium -> low/medium | Pair -> group | P1 | Integrate existing substrate |
| C. Witnessed deeds and testimony | Partial | Fragmented perception, rumor, reputation, and memory | High -> low/medium | Pair/Place -> faction/campaign | P1 | Standalone connective loop |
| D. Meaningful failure and adaptation | Partial | Typed turning points and learning | Medium -> medium | Entity -> pair | P1 | Focused integration slice |
| E. Values earned through choices | Dormant | Existing motivation/value profile | Rare/low -> rare/low | Entity -> entity | P2 | Fold into cognition activation |
| F. Personal life projects | Partial | Live generic project hierarchy lacks life-purpose generation | Low -> low | Entity -> Household/Place | P2 | Extend project generation |
| G. Mentorship and technique traditions | Planned overlap | Ideas 6/22/26 | Low -> low | Pair -> campaign | P2 | Compose existing ideas |
| H. Guardianship and adoption | New | Planned parentage, dependents, and Household | Rare -> rare | Household -> campaign | P2 | Fold into M3/Household |
| I. Caregiving and rescue | Partial | Flag-gated cooperation and live recovery | Low/medium -> low | Pair -> group | P2 | Extend cooperation/recovery |
| J. Apprenticeship and role succession | Planned overlap | Mentorship, careers, and Idea 64 | Rare/low -> rare/low | Pair -> Place | P2 | Fold into career/Empty Chair work |
| K. Mourning and death consequences | New | Death, bonds, grief, Chronicle, and Household anchors | Rare -> rare | Household/Place -> campaign | P2 | Bounded death extension |
| L. Conflicting identities and loyalties | New | Planned Household, Clan, affiliation, home, commitments | Low -> low | Entity -> faction/Household | P3 | Defer until identity systems exist |
| M. Reconciliation and restorative action | New | Live trust/grudge/debt plus proposal patterns | Low -> low | Pair -> Household/group | P3 | Later proposal type |
| N. Property, permission, and theft | Partial | Theft legality plus Idea 30; ownership missing | Medium/high -> deferred | Entity -> world | P3 | Defer; too cross-cutting now |
| O. Downtime and reflection | Partial | Rest/recovery live; reflection absent | Medium -> low/medium | Entity -> entity | P3 | Fold into existing cadences |
| P. Local customs and cultural rites | Dormant | Cultural derivation and bias substrate | Low/periodic -> deferred | Place -> faction | P3 | Defer; avoid content explosion |

## Candidate proposals

### A. Household continuity

**Status and overlap:** **Legacy.** This is a revival, not a wholly new concept. `src_legacy` contains a `HouseholdRecord` with members, home, storage, reputation, gold, heirlooms, and history links. The current model retains per-entity home storage, `home_region_id`, place attachment, and `heir_entity_id`, but no current Household registry.

**Core idea:** A Household is the durable social/economic unit between an individual and a Clan or faction. It connects marriage, children, guardians, residence, shared storage, inheritance, and remembered family history.

**Manageable first version:** Membership, one home anchor, one shared-storage reference, and simple lifecycle events: founded, joined, left, and ended. Shared storage means container membership and access only; it does not add per-item title, loans, theft, inheritance law, or ownership history. Do not add taxes, land law, dynasties, or complex household schedules.

**Frequency and impact:** Rare formation/dissolution and low-frequency membership changes. Reads may affect family and home decisions. Range is Household and local Place, with succession reaching campaign continuity.

**Balance/data surface:** Formation eligibility, maximum active membership considered by AI, and storage access rules. Keep single thresholds as code defaults; introduce data only if multiple Household archetypes are later approved.

**Review scenarios:** Two adults form a Household; a child/dependent joins; one member dies; the survivor retains shared storage; the last member dies; two Households do not accidentally merge because members share a Place.

**Priority/disposition:** P1 standalone foundation, but not implementation-ready until the family model and home anchor representation are accepted.

### B. Promises, favors, debts, and oaths

**Status and overlap:** **Dormant.** `CommitmentEntry`, `CommitmentModel`, pressure, abandonment, and reputation helpers exist. Contracts, quests, parties, social debt, and strategic projects are live in separate paths, but they do not form one normal commitment loop.

**Core idea:** Accepted commitments should compete with immediate self-interest. A character may promise protection, repayment, delivery, secrecy, return, or assistance, then fulfill, renegotiate, abandon for survival, or betray the commitment.

**Manageable first version:** Materialize commitments only from already-accepted Contracts, quests, and party duties. Cap active commitments using existing cognition bandwidth. Start with protection, repayment, and delivery; defer free-form oaths.

**Frequency and impact:** Low creation frequency; medium scoring pressure while active. Normally affects one entity pair or group. It should never scan all social relationships.

**Balance/data surface:** Strength, deadline pressure, survival override, fulfillment reward, and selfish-abandonment penalty. Commitment kinds may become a small catalog; universal pressure limits remain code defaults.

**Review scenarios:** Fulfillment despite a tempting alternative; valid abandonment at critical health; selfish abandonment with trust loss; expiry without betrayal; conflicting commitments resolved deterministically.

**Priority/disposition:** P1 integration of existing substrate, not a new universal social state machine.

### C. Witnessed deeds and testimony propagation

**Status and overlap:** **Partial.** Perception and salience models, rumor/belief handling, public reputation, reputation-label helpers, local-reputation Idea 60, Chronicle, and campaign social memory exist in fragmented states of activation.

**Core idea:** A deed changes public knowledge only when someone perceives it or later receives testimony. The bounded loop is `salient event -> nearby perceivers -> private evidence -> testimony/rumor -> local reputation or Chronicle`.

**Manageable first version:** Allowlist a few high-value deeds such as rescue, betrayal, murder, major victory, and commitment fulfillment. Use existing perceived-entity/spatial information, deterministic witness ordering, a small witness cap, and local propagation. No all-event witness ledger and no global broadcast.

**Frequency and impact:** Raw candidate events may be high-frequency, but materialized witness evidence should be low/medium after filtering. Only salient events create evidence, and only local eligible perceivers are evaluated. Normal range is pair/Place; repeated testimony may reach faction or campaign memory.

**Balance/data surface:** Deed salience, witness cap, testimony fidelity, trust weighting, and local decay. A deed-rule catalog is appropriate because multiple deed kinds need distinct effects.

**Review scenarios:** Deed with no witness; one reliable witness; conflicting testimony; witness dies before spreading the account; distant faction remains unaware; repeated reports do not multiply reputation without a cap.

**Priority/disposition:** P1 connective loop, gated on the perception/relationship representation decision and coordinated with Ideas 25, 54, 57, 60, and 62.

### D. Meaningful failure and adaptation

**Status and overlap:** **Partial.** Turning points and learning biases exist, and project outcome logic can describe victory, abandonment, and loss, but the terminal project-outcome path is not normally wired as one complete learning loop.

**Core idea:** Failure should create a changed future choice rather than only consume resources. Defeat, abandonment, betrayal, and failed searches can temporarily increase caution, preparation, avoidance, or determination.

**Manageable first version:** Wire terminal project outcomes into bounded turning points and existing goal-score modifiers. Reuse current categories before adding trauma taxonomies. Biases must decay or saturate so one failure does not permanently disable a play style.

**Frequency and impact:** Medium, event-driven per project outcome. Usually entity-only; betrayal or combat defeat can affect a pair.

**Balance/data surface:** Salience, maximum accumulated bias, recovery/decay, and repeated-failure saturation. These are initially single code defaults.

**Review scenarios:** One defeat creates caution; repeated defeat increases preparation without permanent paralysis; later success reduces avoidance; unrelated failures do not affect combat preferences.

**Priority/disposition:** P1 focused integration slice with high RPG value and little new state.

### E. Values earned through choices

**Status and overlap:** **Dormant.** `ValuePreferenceProfile` already carries survival, reward, knowledge, loyalty, pride, curiosity, and caution, and a motivation service can score tagged routes. The richer cognition hierarchy still has an explicit keep/finish-or-cut decision under Idea 8.

**Core idea:** Repeated costly choices gradually shape values. Values describe what a character will sacrifice for, rather than what they frequently do or are skilled at.

**Manageable first version:** Adjust only existing value axes after a small allowlist of high-salience choices. Use small bounded changes and require repeated evidence; do not generate arbitrary personality labels.

**Frequency and impact:** Rare/low updates at turning points; frequent reads only if the existing motivation scorer becomes live. Entity-local impact.

**Balance/data surface:** Per-event value deltas, evidence threshold, cap, and optional slow regression toward baseline. A rule catalog is justified only after the cognition substrate is retained.

**Review scenarios:** Costly rescue strengthens loyalty; repeated selfish abandonment strengthens reward/pride; one anomalous choice does not rewrite identity; opposed choices partially counteract.

**Priority/disposition:** P2 extension, folded into Idea 8 and earned-habit/expertise work rather than approved as an independent engine.

### F. Personal life projects

**Status and overlap:** **Partial.** The generic `ProjectState`/objective/blocker/lead hierarchy is live, but self-generated, long-duration personal purpose is missing.

**Core idea:** A character may pursue a life project such as founding a Household, mastering a craft, restoring a Place, reconciling a relationship, or establishing a school.

**Manageable first version:** Add a few project templates generated from existing needs, values, turning points, and already-known world opportunities. Limit opportunity inputs to perceived objects, current leads, and a deterministic candidate cap; limit each entity to one life project inside existing project bandwidth.

**Frequency and impact:** Low creation and transition frequency. Primarily entity-local, with some Household or Place outcomes.

**Balance/data surface:** Template prerequisites, utility, abandonment conditions, and completion objectives belong in a small project-template catalog.

**Review scenarios:** Eligible character adopts a project; urgent survival interrupts but does not erase it; blocker creates a detour; completion changes the world; impossible project eventually abandons cleanly.

**Priority/disposition:** P2 extension after existing goal/project activation gaps are stable.

### G. Mentorship and traditions of technique

**Status and overlap:** **Planned overlap.** Idea 6 covers teaching, Idea 22 includes a mentor relationship role, and Idea 26 covers expertise earned through living.

**Core idea:** A trusted expert can teach a learner, and techniques can retain a lightweight lineage of who taught whom.

**Manageable first version:** A mentor role, one teaching proposal, eligibility based on expertise difference, and a bounded learning benefit. Track teacher identity on the learned technique only if that information has a visible consumer.

**Frequency and impact:** Low, pair-local, with generational narrative effects.

**Balance/data surface:** Expertise gap, trust requirement, teaching duration, and transfer efficiency. Technique definitions may live with the relevant skill/expertise data.

**Review scenarios:** Qualified mentor accepted; untrusted teacher refused; learner cannot exceed the designed transfer ceiling; mentor death leaves learned expertise intact; repeated teaching cannot duplicate rewards.

**Priority/disposition:** P2; do not create a separate milestone—compose Ideas 6/22/26.

### H. Guardianship and adoption

**Status and overlap:** **New.** This family behavior would build on planned parentage, dependents, marriage, and Household state.

**Core idea:** A dependent can receive a responsible guardian even when biological parents die, disappear, or are unsuitable.

**Manageable first version:** One active guardian assignment and reassignment on guardian death. Adoption may change Household membership but need not rewrite biological parentage.

**Frequency and impact:** Rare. Normally Household-local; succession consequences may reach campaign continuity.

**Balance/data surface:** Guardian eligibility, relationship threshold, capacity, and priority ordering. Start with deterministic rules rather than a large guardian-policy catalog.

**Review scenarios:** Orphan joins a related Household; no eligible guardian exists; guardian dies; biological parentage remains recorded; circular or self-guardianship is rejected.

**Priority/disposition:** P2 fold into M3 plus Household review; not useful before dependents exist.

### I. Caregiving and rescue

**Status and overlap:** **Partial.** Flag-gated cooperation contains a rescue posture/outcome, protection contracts and guard behavior exist, and recovery services exist, but ordinary characters do not form one dependable care loop.

**Core idea:** Strong bonds or obligations can make a character protect, escort, heal, feed, or extract a vulnerable ally.

**Manageable first version:** One rescue action selected for a nearby incapacitated or critically threatened bonded ally. Start with extraction/protection; add resource transfer or healing only after direct transfer and wound recovery are authoritative.

**Frequency and impact:** Low/medium during danger. Pair/group-local; should use nearby/perceived candidates only.

**Balance/data surface:** Danger threshold, bond/commitment requirement, self-preservation floor, and rescue cooldown.

**Review scenarios:** Loyal ally attempts rescue; cautious low-health ally refuses suicidal rescue; stranger receives no automatic priority; successful rescue affects trust; rescue cannot target an inactive corpse.

**Priority/disposition:** P2 extension of cooperation/recovery, not a new care simulation.

### J. Apprenticeship and role succession

**Status and overlap:** **Planned overlap.** This composes occupation changes, mentorship, Household continuity, and Idea 64's economic vacancy.

**Core idea:** A skilled worker can prepare an apprentice who may fill a role after retirement, death, or departure.

This is a specific economic consumer of Candidate G's teaching mechanism, not a second training loop.

**Manageable first version:** One mentor-apprentice link for economically unique roles and a deterministic vacancy candidate preference. Do not simulate full labor markets or schools.

**Frequency and impact:** Rare/low. Pair-local during training; Place-level consequences when succession occurs.

**Balance/data surface:** Minimum expertise, training progress, vacancy eligibility, and preference strength.

**Review scenarios:** Apprentice succeeds a dead craftsperson; unqualified apprentice is rejected; multiple candidates break ties deterministically; mentor changes occupation; no apprentice leaves a visible vacancy.

**Priority/disposition:** P2; fold into Ideas 21, 26, and 64 rather than introduce an independent system.

### K. Mourning and death consequences

**Status and overlap:** **New.** The behavior would reuse existing death, corpse, Chronicle, bond, grief/nemesis, succession, and proposed Household state.

**Core idea:** A socially meaningful death creates a bounded response after knowledge of the death reaches an eligible mourner: mourners recognize the loss, immediate obligations adjust, and the death becomes legible to the local world.

**Manageable first version:** One authoritative death-consequence event plus a short mourning concern for close bonds or Household members who witnessed the death or later received a verified report. A Chronicle entry records highly salient deaths. Defer funerals, graves, ceremonies, religious rules, and material death economies to Candidate P or later review.

**Frequency and impact:** Rare but potentially broad. Household/Place range; exceptional deaths reach Chronicle or campaign memory.

**Balance/data surface:** Bond threshold, mourning duration, salience, and Chronicle threshold. Single defaults are sufficient initially.

**Review scenarios:** Unwitnessed stranger death causes no community response; a discovered corpse produces a death report; an absent Household member mourns only after learning the news; duplicate reports do not duplicate mourning; mass death is capped/batched; mourning does not resurrect or delay authoritative deactivation.

**Priority/disposition:** P2 bounded extension after death correctness and grief reachability are repaired.

### L. Conflicting identities and loyalty dilemmas

**Status and overlap:** **New.** Its required inputs are planned: Household, relationship roles, Clan, affiliation change, home/exile, and commitments.

**Core idea:** A character sometimes must choose between incompatible obligations such as family, faction, home, mentor, and party.

**Manageable first version:** Detect conflicts between two already-scored commitments and expose the winning reason. Do not invent a new identity state or universal moral solver.

**Frequency and impact:** Low. Entity-local decision with Household/faction consequences.

**Balance/data surface:** Priority weights, emergency overrides, and breach consequences; these must reuse commitment/appraisal data rather than create a second loyalty model.

**Review scenarios:** Family versus faction order; survival overrides both; equal priorities resolve deterministically; the losing obligation records a consequence; no conflict event when both goals are compatible.

**Priority/disposition:** P3 defer until the identity inputs exist.

### M. Reconciliation and restorative action

**Status and overlap:** **New.** It would compose live trust, grudge, debt, betrayal, Contracts, and appraisal.

**Core idea:** A damaged relationship can improve through apology, restitution, fulfilled service, or mediated agreement rather than only passive score decay.

**Manageable first version:** One restitution proposal with appraisal and a concrete fulfilled action. It may reduce grudge but never erase betrayal history automatically.

**Frequency and impact:** Low, pair-local; occasionally Household/group.

**Balance/data surface:** Eligibility, restitution magnitude, trust ceiling after severe betrayal, and repeated-offer fatigue.

**Review scenarios:** Sincere restitution accepted; total distrust refuses; promise fulfilled reduces grudge; repeated cheap apologies do not farm trust; victim remains free to reject.

**Priority/disposition:** P3 later proposal type after commitments and voluntary interaction are live.

### N. Property, permission, and theft

**Status and overlap:** **Partial.** Theft legality exists, but meaningful per-instance ownership is absent and Idea 30 already identifies that infrastructure gap.

**Core idea:** Taking an item should differ depending on ownership and consent, enabling gifts, loans, theft, recovery, and inheritance to mean different things.

**Present MVP:** None recommended yet. A minimal owner field still affects inventory transfer, loot, corpses, shops, Household storage, crime, reputation, and replay state.

**Frequency and impact:** Medium/high. Entity and economy-wide, with potentially large legality and performance effects.

**Balance/data surface:** Consent, abandonment, inheritance, theft severity, and ownership decay are all unsettled.

**Review scenarios before promotion:** Owner alive/dead; abandoned item; Household property; loan versus gift; theft unseen versus witnessed; stolen item sold; duplicated transfer rejected.

**Priority/disposition:** P3 defer and review with Idea 30. Do not hide this large system inside direct trading or Household work.

### O. Downtime and reflection

**Status and overlap:** **Partial.** Rest, fatigue recovery, town service, project interruption, and some memory/turning-point systems already exist. A reflective downtime behavior does not.

**Core idea:** Periods of safety may consolidate recovery, values, habits, relationships, and projects.

**Manageable first version:** Do not create a new global phase. Attach one bounded consequence to existing rest completion, safe-town cadence, or episode boundary when another approved feature needs it.

**Frequency and impact:** Medium, entity-local. A new per-tick reflection scan would be unjustified.

**Balance/data surface:** Cooldown and maximum changes per rest period.

**Review scenarios:** Rest heals biological pressure; only salient pending experience consolidates; repeated short rests cannot farm changes; combat interruption prevents completion; no-op rest creates no update.

**Priority/disposition:** P3 fold into recovery, habit, value, or campaign work; reject as a standalone engine.

### P. Local customs and cultural rites

**Status and overlap:** **Dormant.** Cultural derivation and bias application exist but lack a live owner. Belief, settlement personality, death ritual, and local identity ideas depend on this area.

**Core idea:** Places or cultures may prefer different rites, hospitality rules, succession customs, or responses to death and betrayal.

**Present MVP:** None before cultural derivation is live. A later bounded experiment could allow one or two approved features to read a small qualitative custom tag. Avoid a universal law/religion simulator.

**Frequency and impact:** Low/periodic reads; Place/faction range.

**Balance/data surface:** A catalog would eventually be appropriate because customs are multi-instance content. Exact behavioral effects require separate review.

**Review scenarios:** Same event receives different local presentation without violating invariant mechanics; unknown custom falls back safely; moving Places changes local expectation but not stored identity instantly.

**Priority/disposition:** P3 defer until the cultural substrate is activated and at least one consumer is approved.

## What should become independent ideas

Only three candidates currently justify independent design identities:

1. **Household continuity** — a missing durable unit with legacy precedent.
2. **Promises, favors, debts, and oaths** — a missing live loop despite extensive typed substrate.
3. **Witnessed deeds and testimony propagation** — a connective mechanism not adequately owned by any one existing idea.

Meaningful failure is valuable enough for P1 review but appears to be a focused integration/repair rather than a new durable feature family.

Everything else should first be treated as an extension, composition, or deferred option. This avoids inflating Ideas 1-66 into a second equally large roadmap.

## Simulation-cost guardrails

Any promoted candidate should satisfy these constraints:

- No all-entity pair scan for social behavior.
- No event-by-entity witness cross product; use local/perceived candidates and deterministic caps.
- No new global phase when an existing event or cadence can own the transition.
- No unbounded history lists; retain salient records and deterministic eviction.
- No universal proposal state machine for domain outcomes.
- No duplicate motivation, loyalty, reputation, or memory model without first choosing the existing authority.
- No high-frequency update whose only consumer is presentation.
- No new content catalog until at least one live behavior reads it.
- Every mutation remains a typed `StateUpdate` refined through the authoritative pipeline.

## Balance and content strategy

Use data when the feature has multiple authored instances with meaningfully different behavior:

- deed/reputation rules;
- life-project templates;
- later commitment kinds;
- later cultural customs.

Use code defaults initially for universal safety limits:

- caps and cooldowns;
- decay/saturation;
- survival overrides;
- bounded record counts;
- deterministic tie-breaking.

The first balance tests should be directional rather than asserting one perfect value. Examples:

- increasing commitment strength should not reduce fulfillment rate;
- increasing witness trust should not reduce belief acceptance;
- repeated failures should increase adaptation but never eliminate all eligible goals;
- increasing Household support should not reduce dependent survival;
- stronger reconciliation evidence should not worsen trust unless a conflicting betrayal occurs.

## Proposal-level delivery order

This is not an implementation plan. It is the order in which the ideas should be reviewed and, if accepted, investigated further.

1. **Integration-first review:** meaningful failure and commitments, because much of their substrate already exists.
2. **Bounded information review:** witnessed deeds, including performance and local-reputation authority.
3. **Durable social-unit review:** Household, coordinated with marriage, dependents, home/Place, and succession.
4. **Composed extensions:** values, life projects, mentorship, guardianship, caregiving, and role succession.
5. **Death and identity consequences:** mourning, loyalty dilemmas, and reconciliation.
6. **Deferred structural ideas:** property law, standalone downtime, and local customs.

High priority does not bypass prerequisites. Household is P1 in value but may be less ready than meaningful failure.

## Review questions before promotion

1. Which current cognition representation is authoritative for commitments and values?
2. Should Household return as authoritative state, or can family/home links provide the same outcomes without a registry?
3. Does witnessed reputation attach to entities, Places, factions, or an evidence record read by all three?
4. Which events are salient enough to justify witness processing?
5. What is the maximum acceptable active commitment, witness, Household-member, and turning-point count?
6. Which candidates produce visible behavior in existing corpus worlds without new content?
7. Which candidates require Idea 66's Place model, and which can remain independent?
8. Which proposal should be removed if it cannot demonstrate a complete producer-to-consumer scenario?

## Non-goals of this proposal

- Assigning Ideas 67-82.
- Updating the Atlas, roadmap, plans, schemas, tickets, or agent records.
- Selecting final field names or pipeline phases.
- Inventing exact balance values.
- Treating historical tickets as proof that a feature is live today.
- Building a legal, religious, education, or family simulator in full.
- Starting implementation before a separate proposal review and investigation phase.

## Source anchors

- Current strategic projects and Contracts: [`src/core/strategic.py`](../../../src/core/strategic.py)
- Current social state: [`src/core/models/social.py`](../../../src/core/models/social.py)
- Dormant commitments, values, and memory hierarchy: [`src/core/cognition.py`](../../../src/core/cognition.py)
- Contract lifecycle and appraisal: [`contracts.py`](../../../src/systems/social_systems/contracts.py) and [`appraisal.py`](../../../src/systems/social_systems/appraisal.py)
- Turning-point learning: [`learning.py`](../../../src/systems/strategic_systems/learning.py)
- Perception filtering: [`filter.py`](../../../src/domains/perception/filter.py)
- Rumor/belief lifecycle: [`belief.py`](../../../src/systems/strategic_systems/belief.py)
- Current Household-adjacent storage: [`home_storage.py`](../../../src/town/home_storage.py)
- Legacy Household model: [`build/lib/src_legacy/core/models/households.py`](../../../build/lib/src_legacy/core/models/households.py)
