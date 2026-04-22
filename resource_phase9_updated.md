Below is the **Phase 9 remaining-tasks implementation plan only**, based on the uploaded current branch [all_src_v2_p9.py](sandbox:/mnt/data/all_src_v2_p9.py) and [all_test_v2_p9.py](sandbox:/mnt/data/all_test_v2_p9.py), reviewed against the original [all_src.py](sandbox:/mnt/data/all_src.py) and [all_test.py](sandbox:/mnt/data/all_test.py). The current V2 branch already has real coverage for belief cycle, cognition export, narrative memory, parts of social consequence, genetics/skill scaling, and dynamic quest generation, but it still lacks several original RPG consequence families that are explicit in the legacy test surface.

# Phase 9 Remaining Tasks Implementation Plan

## [Milestone 1] - Routine, Biological Needs, and Life-Rhythm Closure

### Why this remains

The original legacy tests explicitly cover sleep bias, forced rest, hunger/eating, home/inn-driven recovery, routine disruption, and quiet-tick biological progression. That surface is not convincingly closed in the uploaded Phase 9 V2 branch.

### Remaining tasks

#### [ ] Task 1 - Implement routine-state model for sleep, rest, hunger, and eating

Add explicit long-horizon state for:

- sleep debt / rest pressure
- hunger / appetite pressure
- eating satisfaction / recovery
- off-hours forced-rest conditions
- routine disruption state where preserved

Possible affected files:

- `src_v2/ai/**`
- `src_v2/strategic/**`
- `src_v2/core/cognition/**`
- `src_v2/core/state/**`

Acceptance criteria:

- biological needs are explicit state, not inferred ad hoc
- sleep/rest/hunger pressures persist across ticks
- no hidden perfect-reset behavior remains

#### [ ] Task 2 - Implement routine goal biasing and life-rhythm transitions

Recover preserved logic for:

- sleep utility at night
- rest-to-sleep transition
- forced off-hours rest
- hunger-driven eating behavior
- attack-driven routine suppression
- routine disruption panic where preserved

Possible affected files:

- `src_v2/ai/**`
- `src_v2/strategic/**`
- `tests_v2/ai/**`

Acceptance criteria:

- routine priorities are explicit and deterministic
- biological needs materially affect long-horizon choice
- routine suppression/disruption is test-visible

#### [ ] Task 3 - Add direct contract tests for routine and biological-needs logic

Add focused tests covering:

- sleep goal utility at night
- hunger bias
- forced sleep/rest
- home/inn-driven eating/sleeping
- quiet-tick biological recovery/decay
- routine disruption under threat or attack

Possible affected files:

- `tests_v2/ai/test_routine_service.py`
- `tests_v2/ai/test_biological_needs.py`
- `tests_v2/integration/strategy/**`

Acceptance criteria:

- this logic is proven directly, not implied by broad sims

---

## [Milestone 2] - Hero Lifecycle, Permadeath, Succession, and Heirloom Closure

### Why this remains

The original legacy surface explicitly includes aging/death, hero permadeath, succession, heirlooms, near-death aftermath, and death-linked continuity. I did not find that family convincingly closed in the uploaded Phase 9 V2 branch.

### Remaining tasks

#### [ ] Task 1 - Implement hero lifecycle state and death classification

Add explicit lifecycle semantics for:

- aging and death triggers where preserved
- near-death state and survival aftermath
- hero permadeath vs non-hero death distinctions where required

Possible affected files:

- `src_v2/progression/**`
- `src_v2/social/**`
- `src_v2/core/progression/**`
- `src_v2/core/state/**`

Acceptance criteria:

- lifecycle outcomes are explicit
- near-death and true death are not flattened together

#### [ ] Task 2 - Implement succession and heirloom transfer semantics

Recover preserved continuity rules for:

- successor creation / successor designation
- heirloom transfer
- legacy carryover or inheritance effects where preserved
- death-triggered continuity records

Possible affected files:

- `src_v2/progression/**`
- `src_v2/social/**`
- `src_v2/core/progression/**`
- `src_v2/core/social/**`

Acceptance criteria:

- death can trigger bounded continuity rather than hard discontinuity only
- heirloom/succession behavior is deterministic and documented

#### [ ] Task 3 - Add direct tests for permadeath, succession, and heirlooms

Add focused tests for:

- hero permadeath
- near-death survival consequence
- succession creation
- heirloom transfer
- death-linked consequence records

Possible affected files:

- `tests_v2/progression/test_lifecycle.py`
- `tests_v2/social/test_succession.py`
- `tests_v2/integration/strategy/**`

Acceptance criteria:

- lifecycle continuity is directly proven

---

## [Milestone 3] - Recruitment Negotiation and Contract Richness Closure

### Why this remains

The uploaded branch has meaningful social work, but the original test surface is richer: counter-offers, haggling thresholds, recruiter-side evaluation, debt/greed/loyalty/friction, and more than simple accept/decline. The current V2 branch appears materially thinner here.

### Remaining tasks

#### [ ] Task 1 - Expand recruitment from accept/decline to negotiation semantics

Implement preserved negotiation logic for:

- counter-offers
- recruiter evaluation of counter-offers
- bounded haggling rounds or threshold logic
- refusal memory where preserved

Possible affected files:

- `src_v2/social/**`
- `src_v2/strategic/**`
- `src_v2/core/social/**`

Acceptance criteria:

- recruitment is not a one-pass scalar check only
- negotiation results are deterministic and explainable

#### [ ] Task 2 - Add richer willingness factors to contract/recruitment evaluation

Recover preserved contribution from:

- trust
- debt
- loyalty
- resentment / betrayal memory
- greed / compensation thresholds
- recruiter reputation / prior interaction where preserved

Possible affected files:

- `src_v2/social/**`
- `src_v2/core/social/**`
- `tests_v2/social/**`

Acceptance criteria:

- willingness is multi-factor and bounded
- factors are explicit rather than hidden constants

#### [ ] Task 3 - Add direct contract tests for negotiation richness

Add focused tests for:

- counter-offer generation
- haggling threshold acceptance/failure
- recruiter-side evaluation
- debt/trust/loyalty effects
- betrayal/resentment effects on offers

Possible affected files:

- `tests_v2/social/test_recruitment_negotiation.py`
- `tests_v2/social/test_contract_evaluation.py`

Acceptance criteria:

- richer social negotiation is directly proven

---

## [Milestone 4] - Region-Scale Strategic Consequence Closure

### Why this remains

The original RPG-core includes regional suppression, control shifts, danger pivots, conquered-region consequences, and stronghold-trigger logic. That world-scale strategic consequence layer is still not clearly closed in the uploaded Phase 9 branch.

### Remaining tasks

#### [ ] Task 1 - Implement explicit region-consequence records and interpretation

Add explicit state and update rules for:

- regional suppression
- region danger
- conquered-region records
- fatigue / pressure records where preserved
- strategic interpretation of region state

Possible affected files:

- `src_v2/strategic/**`
- `src_v2/world/**`
- `src_v2/core/strategic/**`

Acceptance criteria:

- region-scale consequences are explicit state, not loose narrative outputs

#### [ ] Task 2 - Implement preserved regional pivots and stronghold consequences

Recover supported logic for:

- pivoting due to regional danger
- consequences of conquest
- stronghold creation/effects where preserved
- region consequence propagation into strategic choice

Possible affected files:

- `src_v2/strategic/**`
- `src_v2/world/**`
- `tests_v2/strategy/**`

Acceptance criteria:

- region-scale events materially change long-horizon choices
- local tactical logic is not confused with region consequence logic

#### [ ] Task 3 - Add direct tests for region consequence logic

Add focused tests for:

- regional suppression
- strategic pivot on regional danger
- conquered-region effects
- stronghold triggers
- region-consequence records

Possible affected files:

- `tests_v2/strategy/test_region_consequences.py`
- `tests_v2/integration/strategy/**`

Acceptance criteria:

- region-scale consequence logic is directly proven

---

## [Milestone 5] - Anchored-World Behavior: Home, Place Attachment, Leash, Camp, Bonding

### Why this remains

The original tests cover place attachment, home response, home-driven retreat/eating, leash return, chase abandonment, camp reinforcement, and proximity bonding. These are small families, but they are real and currently under-evidenced in the uploaded Phase 9 branch.

### Remaining tasks

#### [ ] Task 1 - Implement place attachment and home-aware long-horizon behavior

Recover preserved logic for:

- place attachment
- home location persistence
- home-priority retreat where preserved
- home-visit consequences such as eating/rest transitions where those belong in long-horizon behavior

Possible affected files:

- `src_v2/strategic/**`
- `src_v2/social/**`
- `src_v2/core/state/**`

Acceptance criteria:

- home/place attachment is explicit and behaviorally meaningful

#### [ ] Task 2 - Implement leash and camp-anchored ecology where still owned by Phase 9

Recover preserved logic for:

- beyond-leash return
- chase abandonment outside leash
- camp return and reinforcement
- free-wander/no-leash distinctions

Possible affected files:

- `src_v2/world/**`
- `src_v2/strategic/**`
- `tests_v2/world/**`
- `tests_v2/strategy/**`

Acceptance criteria:

- leash/camp behavior is explicit and deterministic
- ownership is clear if some cases stay with Phase 8

#### [ ] Task 3 - Implement proximity bonding / small cooperative continuity

Recover preserved low-intensity social-world linkages such as:

- bonding by proximity
- cooperation-linked state changes where preserved

Possible affected files:

- `src_v2/social/**`
- `src_v2/strategic/**`
- `tests_v2/social/**`

Acceptance criteria:

- these behaviors are no longer implicit or dropped

#### [ ] Task 4 - Add direct tests for anchored-world behavior

Add focused tests for:

- place attachment
- home-driven behavior
- leash return / chase abandonment
- camp reinforcement
- proximity bonding

Possible affected files:

- `tests_v2/world/test_place_attachment.py`
- `tests_v2/world/test_leash_and_camp.py`
- `tests_v2/social/test_proximity_bonding.py`

Acceptance criteria:

- anchored-world behavior is directly proven

---

## [Milestone 6] - Role, Trait, and Identity-Weighted Decision Closure

### Why this remains

The original tests explicitly cover role derivation, dynamic role transition with hysteresis, and role-aware tactical bias. I did not find that family clearly surfaced as closed in the uploaded Phase 9 review. Traits and role identity are too important to leave implicit.

### Remaining tasks

#### [ ] Task 1 - Implement explicit role derivation and role transition law

Recover preserved logic for:

- initial role derivation
- dynamic role transition
- hysteresis / transition stability
- role persistence over time

Possible affected files:

- `src_v2/strategic/**`
- `src_v2/ai/**`
- `src_v2/core/strategic/**`

Acceptance criteria:

- roles are explicit, bounded, and stable across ticks

#### [ ] Task 2 - Implement role-aware biasing and trait-linked behavioral identity

Recover preserved logic for:

- role-aware tactical or strategic bias
- trait influence on utility / specialization
- identity-weighted behavioral nudges where preserved

Possible affected files:

- `src_v2/ai/**`
- `src_v2/progression/**`
- `src_v2/core/gameplay/**`
- `tests_v2/ai/**`

Acceptance criteria:

- trait/role identity materially affects decisions where preserved
- not reduced to decorative metadata

#### [ ] Task 3 - Add direct tests for role and trait identity behavior

Add focused tests for:

- initial role derivation
- role transitions with hysteresis
- role-aware bias
- trait contribution to decision or progression behavior where preserved

Possible affected files:

- `tests_v2/ai/test_role_derivation.py`
- `tests_v2/ai/test_role_bias.py`
- `tests_v2/progression/test_trait_identity.py`

Acceptance criteria:

- role/trait identity logic is directly proven

---

## [Milestone 7] - Phase 9 Remainder Proof and Exit Correction

### Why this remains

Once the missing families above are added, you still need to correct the Phase 9 truth surface so the phase can be honestly closed.

### Remaining tasks

#### [ ] Task 1 - Update the Phase 9 support boundary after remainder closure

Restate exactly what Phase 9 now supports in:

- strategic continuity
- routine/biology
- lifecycle/succession
- recruitment/contract richness
- region consequences
- anchored-world behavior
- role/trait identity
- progression/reward math

Acceptance criteria:

- no lingering overclaim or underclaim remains

#### [ ] Task 2 - Add parity/characterization coverage for the newly closed families

Build or extend parity tests for:

- routine/needs
- lifecycle/succession
- negotiation richness
- region consequences
- anchored-world behavior
- role/trait identity

Acceptance criteria:

- preserved claims are evidence-backed, not merely implemented

#### [ ] Task 3 - Rebuild the Phase 9 proof bundle and exit package

Only after the missing families above are closed, rebuild:

- proof bundle
- support matrix
- divergence log
- exit package
- Phase 10 readiness input

Acceptance criteria:

- Phase 9 exit truth matches actual closure

---

# Execution order

Use this order:

1. Routine / biological needs
2. Hero lifecycle / succession / heirlooms
3. Recruitment negotiation richness
4. Region-scale consequences
5. Anchored-world behavior
6. Role / trait identity
7. Proof + exit-package correction
