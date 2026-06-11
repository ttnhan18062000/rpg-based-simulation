---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

Good. Milestone 4 is where the system stops pretending that “nearby entities in a group” equals cooperation.

It does not.

Up to Milestone 3, an entity can have continuity, uncertainty, blockers, and detours. But if every hard problem is still solved as a solo agent, the social layer remains decorative. Milestone 4 is the point where cooperation becomes structurally real: some projects are not solo-viable, recruitment becomes a strategic objective, and alliances have explicit purpose, terms, and consequences. That is exactly what the design reference demands when it distinguishes social bonds and groups from actual social contracts and dependency.

# Milestone 4 — Social contracts and purpose-driven parties

## What this milestone actually delivers

At the end of Milestone 4, an entity should be able to:

- recognize that a project is not worth attempting alone
- identify candidate allies based on trust, debt, familiarity, reputation, role fit, and availability
- form a party or contract with an explicit purpose
- carry shared expectations across ticks
- react meaningfully when terms are honored, broken, or abandoned

That is the moment where social behavior becomes a strategic system instead of flavor text around clustering and pathing.

What Milestone 4 still does **not** need:

- full diplomatic simulation across all factions
- deep economy or negotiation trees
- emotionally rich betrayal interpretation
- public narrative consequences beyond the basics

This milestone is about making cooperation explicit, durable, and costly.

---

## The real problem you are solving

The trap here is obvious: the code already has social bonds, group records, cohesion, familiarity, gossip, and some alliance-like behavior, so it is tempting to say “we already have parties.”

You do not.

What you have is social substrate. That is useful, but it is not the same as a contract-backed cooperative structure with shared purpose and consequences. The design notes are explicit that real social dependency should answer questions like:

- who knows something I lack
- who owes me
- who is brave enough
- who benefits from helping
- who is likely to betray
- who is already busy with their own obligations

That is not the same as “entities nearby with decent cohesion.”

---

## What must exist by the end of this milestone

You need five things.

### 1. Non-solo viability checks

Some projects must be recognized as poor solo choices.

That does not mean hardcoded “must have party” flags everywhere. It means the strategic layer can conclude:

- risk is too high
- role coverage is poor
- expected success is too low
- reward does not justify solo risk
- social access or witness requirements exist

That decision is what triggers recruitment instead of blind solo execution.

### 2. Explicit contract records

You already introduced strategic foundation earlier. Now the contract record must become meaningful.

A first useful contract should include:

- stable ID
- purpose
- initiator
- members
- requested roles
- terms or reward expectations
- duration or dissolution condition
- status
- created/updated/resolved ticks

Do not overbuild legal simulation. You only need enough semantics to make coordination durable and testable.

### 3. Recruitment as a strategic objective

Recruitment should become a first-class detour or sub-objective.

That means an entity can decide:

- I need a tank
- I need a healer
- I need someone trustworthy
- I need someone who knows the area
- I need someone indebted enough to say yes

This is the first time the social layer becomes part of strategic planning rather than post-hoc reaction.

### 4. Candidate ally evaluation

The system must be able to rank who is worth asking.

Inputs should include:

- trust
- fear
- loyalty
- debt
- admiration or resentment where relevant
- public reputation
- role/class/strength fit
- current obligations
- current project conflict
- distance and reachability

This should be a scoring layer, not a random ask-everyone routine.

### 5. Persistent consequences for cooperation outcomes

If the contract is accepted and honored, something should improve.
If it is broken, something should degrade.

At minimum:

- trust changes
- debt changes
- reputation changes where public
- future recruitment viability changes

Without this, contracts are fake wrappers around one-off coordination.

---

## The correct implementation order

### Step 1 — Write tests that prove groups are not enough

Start with the anti-fake tests.

You need failing tests that prove:

- a hard project can trigger recruitment instead of solo execution
- candidate ally choice depends on social and capability fit
- a formed party persists across ticks
- contract breach creates lasting consequences
- successful cooperation improves future willingness or trust

If you do not write these first, you will accidentally re-skin the existing group system and call it done.

### Step 2 — Enrich the contract schema just enough

Your strategic model likely already has a contract record placeholder from Milestone 1. Now make it actually useful.

Add:

- purpose / project linkage
- member list
- requested roles
- contribution expectations
- reward semantics
- status fields like proposed, active, completed, broken, dissolved
- fulfillment/breach markers

Keep it bounded. Do not turn this into a giant negotiation DSL. That would be a classic overengineering mistake.

### Step 3 — Add non-solo project evaluation

Before recruitment exists, the system needs to know when recruitment is worth doing.

Create a service that checks whether the current project/objective is solo-viable based on:

- expected threat
- entity strength
- blocker state
- need for role coverage
- social or witness requirement
- risk tolerance

This is where the strategic layer decides to branch into recruitment.

### Step 4 — Add recruitment objective generation

Once non-solo need is recognized, the system should generate objectives like:

- recruit frontliner
- recruit healer
- recruit scout
- recruit guide
- recruit any trusted ally

At Phase 4, keep this simple and role-driven. Do not try to model nuanced persuasion trees yet.

### Step 5 — Add ally ranking and invitation logic

Now build the candidate selection layer.

A clean first pass:

- filter unavailable or hostile candidates
- filter candidates with incompatible obligations
- rank remaining candidates by fit, trust, debt, and reachability
- invite top candidate or top small set deterministically

Do not brute-force every entity. That would be noisy and stupid.

### Step 6 — Bind party formation to contracts, not just groups

If the contract is accepted:

- create or update the contract
- mark members
- link it to the project
- optionally create/update the tactical group wrapper

The important thing is the contract is the semantic truth, and the group structure becomes the execution shell. That is the correct layering.

### Step 7 — Add cooperation outcome handling

When a contract-backed effort succeeds or fails:

- update trust/debt/reputation
- mark contract completion or breach
- update future recruitment viability
- possibly create new obligations or resentment

This is what gives social memory teeth.

---

## What the implementation should probably look like

## A. Add a cooperation evaluation service

Create something like:

- `src/ai/strategic_cooperation.py`
- `CooperationNeedService`

Its job:

- inspect current project/objective
- decide whether solo execution is acceptable
- return cooperation need and desired role profile

That keeps “need for allies” separate from the rest of strategic appraisal.

## B. Add an ally selection service

Create something like:

- `src/ai/recruitment_selection.py`
- `RecruitmentSelectionService`

Its job:

- gather candidate entities
- score them by trust, debt, capability fit, obligations, and availability
- return ranked candidates and reasons

This should be deterministic and explainable.

## C. Add a contract lifecycle service

Create something like:

- `src/core/logic/social_contracts.py`
- `SocialContractApplicator` or lifecycle helper

Its job:

- propose contract
- activate contract
- mark completion or breach
- apply side effects to social and reputation state

This is better than scattering contract consequences across multiple handlers.

## D. Reuse group mechanics as execution support, not semantic truth

This part matters.

If you already have `GroupRecord` or similar, do not throw it away immediately. Use it as the tactical wrapper for movement/cohesion/shared target behavior.

But the **reason** the group exists and the **terms** of participation should live in strategic contracts, not in the group record itself. Otherwise you keep flattening strategy into tactics.

---

## TDD sequence for Milestone 4

Use this order.

### Test batch A — project recognizes need for allies

Write failing tests that prove:

- a high-risk or role-incomplete project triggers a recruitment objective
- a clearly solo-viable project does not trigger recruitment unnecessarily

Then implement non-solo viability checks.

### Test batch B — ally selection is meaningful

Write failing tests that prove:

- candidates are filtered by hostility, trust, obligations, or availability
- ranking prefers fit and relationship quality over random proximity
- candidate choice is deterministic

Then implement ally selection.

### Test batch C — contract formation persists

Write failing tests that prove:

- accepted recruitment creates a contract record
- contract links to the relevant project
- contract survives across ticks
- party members remain associated while active

Then implement contract lifecycle basics.

### Test batch D — contract outcomes have consequences

Write failing tests that prove:

- successful cooperation increases trust or future viability
- failure or abandonment marks breach
- breach affects trust, debt, or future recruitment willingness

Then implement outcome application.

### Test batch E — strategic continuity uses contracts

Write failing tests that prove:

- a blocked project can resume once required allies are recruited
- the social contract remains part of the project context while active
- recruitment is not forgotten immediately after formation

Then wire contract-backed cooperation into Milestone 2 and 3 continuity.

That is the right order because it forces you to establish necessity, then selection, then persistence, then consequence.

---

## Suggested file targets

Likely new or changed files:

- `src/core/models/strategy.py`
- `src/ai/brain.py`
- `src/ai/strategic_cooperation.py`
- `src/ai/recruitment_selection.py`
- `src/core/logic/social_contracts.py`
- `src/actions/base.py`
- `src/systems/gameplay/action_system.py`
- existing social registry or group coordination modules
- inspector / presenter modules for contract visibility

Suggested tests:

- `tests/ai/test_cooperation_need_detection.py`
- `tests/ai/test_recruitment_selection.py`
- `tests/ai/test_social_contract_lifecycle.py`
- `tests/ai/test_contract_consequences.py`
- `tests/ai/test_project_resume_with_recruited_party.py`

---

## Definition of done for Milestone 4

Milestone 4 is done only when all of this is true:

- some projects can be recognized as poor solo choices
- recruitment can become a strategic objective
- ally selection uses social and capability fit, not random grouping
- cooperation is represented by explicit contracts, not just tactical groups
- contracts persist across ticks and affect project continuity
- success and breach produce lasting social consequences
- all of that is covered by deterministic tests

If hard projects still default to solo execution, you failed.
If party formation is just proximity with a label, you failed.
If contracts have no consequences, you failed.
If future recruitment ignores past cooperation outcomes, you failed.

---

## Milestone 4 checklist

- [/] Add failing tests that prove some projects trigger recruitment instead of solo execution

- [/] Add failing tests that prove solo-viable projects do not recruit unnecessarily

- [/] Add failing tests for candidate ally filtering by trust, hostility, obligations, and availability

- [/] Add failing tests for deterministic ally ranking by fit and relationship quality

- [x] Add failing tests for contract persistence across ticks

- [x] Add failing tests for trust/debt/reputation consequences from contract success or breach

- [x] Add failing tests for blocked-project resumption after successful recruitment

- [x] Enrich `SocialContractRecord` with purpose, project linkage, member list, requested roles, terms, status, and lifecycle fields

- [x] Add stable IDs and deterministic ordering for contract records [DONE]

- [x] Add fulfillment and breach markers

- [x] Ensure contract records serialize and inspect cleanly

- [x] Create a cooperation-need evaluation service/module [DONE in `src/ai/strategy/strategic_evaluator.py`]

- [x] Detect when a project is not solo-viable due to risk, role gap, access need, or social requirement [DONE]

- [x] Keep solo-viability checks bounded and deterministic

- [x] Feed cooperation need into strategic appraisal as a real branch, not an afterthought

- [x] Add recruitment objective generation [DONE in `src/ai/strategy/recruitment_negotiation.py`]

- [x] Support simple role-targeted recruitment objectives

- [x] Link recruitment objectives to the blocked or non-solo project

- [x] Preserve project continuity while recruitment is in progress

- [x] Create an ally selection service/module [DONE in `src/ai/strategy/recruitment_selection.py`]

- [x] Filter candidates by hostility, trust floor, obligations, and availability

- [x] Score candidates by capability fit, trust, debt, familiarity, reputation, distance, and conflict with current commitments

- [x] Keep selection deterministic and explainable

- [x] Avoid brute-force noisy invitation behavior

- [x] Implement contract proposal and activation flow [DONE]

- [x] Link accepted contracts to the relevant project

- [x] Bind contracts to tactical group formation where useful

- [x] Use tactical group structure as execution support, not the semantic source of cooperation

- [x] Ensure active contracts persist across ticks

- [x] Implement contract outcome handling [DONE in `src/ai/strategy/contract_outcome.py`]

- [x] Mark contracts as completed, broken, declined, or dissolved

- [x] Apply trust changes from cooperation success/failure

- [x] Apply debt or obligation effects where relevant

- [x] Apply public reputation effects where appropriate

- [x] Update future recruitment viability based on past outcomes

- [x] Feed successful recruitment back into blocked-project continuation

- [x] Resume original project when ally requirements are satisfied

- [x] Preserve contract context while joint project remains active

- [x] Prevent recruited cooperation from being forgotten immediately after formation

- [x] Extend inspector/debug output to show active contracts, member roles, terms, and contract status

- [x] Extend presenter/API output if needed for explainability

- [x] Keep visibility structured and compact

- [x] Add deterministic unit tests for cooperation-need detection

- [x] Add deterministic unit tests for ally ranking and filtering

- [x] Add deterministic unit tests for contract lifecycle transitions

- [x] Add deterministic integration tests for recruitment-to-project-resume flow

- [x] Confirm milestone definition of done with passing automated tests

---

## Implementation Notes

### Strategic Cooperation Logic
We have moved beyond simple proximity-based grouping. Cooperation is now a strategic response to project requirements.
- **Project Viability**: The `StrategicEvaluator` determines if a project is `solo_viable` based on the actor's level, equipment, and current health vs the project's risk. If not solo-viable, it triggers a `RECRUITMENT` objective.
- **RecruitmentNegotiationService**: Handles the proposal/counter-proposal (haggling) flow and creates explicit `SocialContractRecord` instances.
- **ContractOutcomeService**: Bridges the strategic and social layers. Successful contract completion boosts trust and heroism; failure or breach (abandoning the project) tank reputation and breed resentment between members.
- **Persistence**: Contracts are stored in `StrategicState.contracts` and persist across ticks until explicitly resolved or cancelled, ensuring that entities remember their joint commitments.

Priority Plan

What you must change in mindset or assumptions:
Stop treating cooperation as a tactical convenience. In this system, cooperation must become a strategic response to risk, uncertainty, and role gaps.

What actions you must take immediately:
Write the non-solo viability and ally-selection tests first, then implement contract schema and lifecycle, then wire recruitment back into blocked project continuity.

What you must stop or eliminate:
Stop confusing existing group mechanics with real cooperation. Stop allowing socially costly commitments to vanish after one tick. Stop making ally choice feel random.

The consequences and opportunity cost if you fail to change:
You will keep a decorative social layer that looks busy but never becomes necessary. That means the system stays fundamentally solitary, and you lose one of the main sources of emergent divergence and believable lives.
