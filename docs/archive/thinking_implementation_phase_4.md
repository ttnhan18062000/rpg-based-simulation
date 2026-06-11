---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

[Phase 4] - Social Contracts, Party Formation, and Cooperative Coordination

[Phase Description]
Phase 4 upgrades the social layer from background flavor into a real strategic force multiplier. The design is explicit: some projects should be structurally hard to complete alone, parties should be purposeful temporary social machines, and social promises must have cost. The current engine already has the right ingredients — directed social bonds with trust, fear, loyalty, resentment, admiration, rivalry, debt, and familiarity; public reputation; group records with leader, members, shared goal, anchor position, and cohesion; inn gossip; and social utility biasing in appraisal — but these pieces are still too tactical and too thinly unified.

The blunt truth is that the current group layer is not yet a party system. `GroupRecord` only carries tactical coordination fields like `shared_goal`, `target_id`, `member_ids`, `anchor_pos`, `cohesion_level`, and `bonuses`, and `GroupSystem` currently auto-forms cliques from same-faction, same-cluster entities with a default `EXPLORE` goal and maintenance logic based mostly on distance, leader survival, and membership count. The AI then applies a simple coordination bias by boosting the group shared goal and nudging non-leaders to follow the anchor if they drift too far. That is useful infrastructure, but it is still proximity-and-cohesion glue, not negotiated cooperation.

[Phase technical implementation]
Phase 4 should introduce an explicit contract layer that sits above the current tactical `GroupRecord`. The strategic layer from Phase 1 should gain social contract and group-project ownership records; the strategic evaluator from Phase 2 should gain ally selection, recruitment, and negotiation logic; and the uncertainty layer from Phase 3 should feed social uncertainty, trust judgment, and specialist search into party formation. The result should be a two-level model:

1. a **social contract layer** that stores purpose, terms, expectations, fallback conditions, dissolution conditions, and social consequences
2. a **tactical group layer** that executes shared movement, proximity, focus, and combat coordination once a contract-backed party exists

That preserves the existing group infrastructure while giving it a real reason to exist. Contracts should be persisted through typed strategic updates; group membership and tactical cohesion should still be maintained through world systems; and social bond plus reputation changes should flow through the existing authoritative relationship and reputation services when terms are honored or broken.

[Phase important notes]
The biggest trap is mistaking groups for cooperation. The source already proves the engine can form and maintain small groups, but they are currently auto-clustered social cliques with default goals, not negotiated parties with explicit terms. If Phase 4 only adds more group bonuses or more follow-leader behavior, it will fail. The design explicitly says the missing layer is purpose and expectation.

The second trap is making contracts cosmetic. The design is clear that whether terms are honored must feed trust, debt, reputation, and future recruitment viability. The current code already has the authoritative machinery to update social bonds and public reputation. Phase 4 should use that machinery instead of inventing side-channel “relationship flavor.”

The third trap is homogenized recruitment. The design says entities should ask who knows something, who owes them, who trusts them enough, who is brave enough, who benefits, who may betray, and who is already busy. That means party formation has to inspect trust, debt, loyalty, admiration, rivalry, reputation, obligations, and current project load rather than just pick nearby allies.

[Phase acceptance criteria]
At the end of Phase 4, an entity can determine that a project is not solo-viable, identify and rank candidate allies, negotiate a contract-backed party or pact with explicit terms, create or join a purpose-driven tactical group tied to that contract, and generate persistent trust/debt/reputation consequences when members honor, abandon, betray, or complete the shared undertaking. Group behavior is no longer “same cluster, same faction, stand near leader”; it becomes “shared project, negotiated terms, remembered consequences.”

## Task

[x] (checkbox) - [Task 1] - Define social contract and party records in the strategic domain

[Task Description]
Phase 4 needs explicit records for the things the design says are currently missing: social contracts, party purpose, negotiated terms, role expectations, fallback conditions, dissolution conditions, ownership of rewards, and social memory when promises are broken. The current `GroupRecord` is only sufficient for tactical coordination; it is not expressive enough for contracts.

[Task technical implementation]
Extend `src/core/models/strategy.py` with contract-facing records such as:

- `SocialContractRecord`
- `PartyRecord` or `GroupProjectRecord`
- `RecruitmentOfferRecord`
- `ContractTermRecord`
- `ContractOutcomeRecord`

At minimum, `SocialContractRecord` should include:

- `contract_id`
- `contract_type` such as expedition, escort, militia, mercenary, revenge pact
- `purpose`
- `formation_reason`
- `project_id`
- `founder_id`
- `member_ids`
- `invited_ids`
- `required_roles`
- `reward_logic`
- `terms`
- `fallback_conditions`
- `dissolution_conditions`
- `status`
- `created_tick`
- `expires_tick` or review tick
- `breach_history`
- `visibility`
- `shared_or_private`

This should live in strategic state, not inside `GroupRecord`, because it is long-lived social meaning, not movement glue. `GroupRecord` can later reference `contract_id` or `party_id` once the tactical group is instantiated.

[Task possible affected files]

- `src/core/models/strategy.py`
- `src/core/aspects/mind.py`
- `src/actions/base.py`
- optionally `src/core/models/lived_structure.py` if `GroupRecord` gains a contract reference

[Task important notes]
Do not overload `GroupRecord` into a giant hybrid object. It already serves tactical coordination. If you mix contract semantics and tactical execution into one record, you will create a maintenance mess and destroy the clean layer separation you need.

[Task check list]

- [x] Add strategic contract records
- [x] Add party-purpose and reward-term fields
- [x] Add breach and dissolution metadata
- [x] Add stable IDs and lifecycle fields
- [x] Keep tactical group and strategic contract separate

[Task acceptance criteria]
The engine can represent a negotiated cooperative arrangement as a first-class strategic object rather than inferring one from raw group membership.

---

[x] (checkbox) - [Task 2] - Extend strategic updates and authoritative application for contracts and party state

[Task Description]
Once contracts exist as records, they need the same authoritative lifecycle as other strategic state. Recruitment offers, accepted terms, member additions/removals, breaches, payout resolution, and dissolution cannot be handled as incidental local variables in AI code. They must survive ticks and be applied deterministically.

[Task technical implementation]
Extend `StrategicUpdate` and the strategic applicator from Phase 1 to support:

- add/update/remove social contract
- issue recruitment offer
- accept/decline recruitment offer
- activate contract
- attach/detach project ownership to contract
- mark breach event
- resolve reward distribution
- dissolve contract
- sync contract to tactical group creation/removal

This can either live entirely in `StrategicUpdate` or use a dedicated `ContractUpdate` if the strategic update class is already getting crowded. The authoritative applicator should update `mind.strategic` and, where appropriate, notify the world/social systems that a tactical group must be created or retired.

[Task possible affected files]

- `src/actions/base.py`
- `src/systems/gameplay/action_system.py`
- `src/core/logic/strategic_state_applicator.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not let contract acceptance or breach effects mutate social bonds directly inside recruiter logic. Contract state and relationship consequences are related but distinct. Contract updates should be authoritative first, then relationship and reputation services can consume the resulting consequences.

[Task check list]

- [x] Extend strategic update operations for contracts
- [x] Add authoritative apply paths for contract lifecycle
- [x] Support recruitment offer issuance and response
- [x] Support breach and payout resolution
- [x] Support sync hooks into tactical group creation/removal

[Task acceptance criteria]
Contract-backed cooperation can be created, changed, and resolved through deterministic typed updates, with no direct AI mutation shortcuts.

---

[x] (checkbox) - [Task 3] - Build ally discovery and candidate ranking logic

[Task Description]
The design is explicit that entities should ask who knows something they lack, who owes them, who trusts them enough, who is brave enough, who benefits, who may betray, and who is already busy with their own obligations. The current engine already has the raw data for that through social bonds, public reputation, place attachments, narrative memory, and current project state, but no reusable service for recruitment ranking.

[Task technical implementation]
Create a `SocialCandidateSelectionService` that ranks potential allies using:

- trust
- loyalty
- debt
- admiration
- rivalry and resentment penalties
- fear or cowardice risk
- public trustworthiness / reputation
- current project load and obligations
- capability fit for required roles
- proximity / travel feasibility
- specialist value such as healer, tank, guide, crafter

Inputs should come from `AIContext`, `SocialRegistry`, public reputation, and the active project’s required roles or blockers. Output should be a bounded ranked list of recruitment candidates with driver explanations. This should feed Phase 2 strategic evaluation when a blocker implies “not enough allies” or “role coverage poor.”

[Task possible affected files]

- `src/ai/strategy/social_candidate_selection.py`
- `src/ai/brain.py`
- `src/core/models/social.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not reduce ally selection to “highest trust nearby.” The design explicitly wants socially believable tradeoffs, including risk of betrayal, debt leverage, bravery, and current unavailability.

[Task check list]

- [x] Add candidate selection service
- [x] Score trust, debt, loyalty, rivalry, fear, and reputation
- [x] Score required-role fit
- [x] Penalize obligation conflicts and unavailability
- [x] Emit bounded ranked candidate list with reasons

[Task acceptance criteria]
When a project needs allies, the engine can produce a ranked set of socially plausible candidates rather than defaulting to nearest compatible unit or same-cluster ally.

---

[x] (checkbox) - [Task 4] - Implement recruitment, negotiation, and offer/response mechanics

[Task Description]
A party system without negotiation is fake. The design explicitly includes negotiate terms, hire specialist, repay debt, request training, seek faction backing, and hire specialist as social objectives, and says party formation should happen when blocker analysis says solo failure is likely and trust/incentive thresholds are sufficient. Recruitment must therefore include offer creation, acceptance, refusal, and term shaping.

[Task technical implementation]
Create a `RecruitmentNegotiationService` that:

- generates an offer from recruiter to candidate
- selects proposed terms based on relationship and project type
- scores candidate willingness to accept
- allows refusal, acceptance, counter-demand, or deferment
- materializes a contract if terms are accepted

Offer content can include:

- equal split
- fixed payment
- future favor
- guild duty
- shared revenge
- exclusive claim on specific loot
- escort fee
- defensive obligation

This service should update strategic state with offer and contract records, not directly spawn groups. Acceptance should depend on trust, debt, loyalty, greed, fear, public reputation, current obligations, and current risk estimate.

[Task possible affected files]

- `src/ai/strategy/recruitment_negotiation.py`
- `src/core/models/strategy.py`
- `src/actions/base.py`
- `src/ai/brain.py`

[Task important notes]
Do not shortcut negotiation into a yes/no join roll. That loses the whole point of terms, obligations, and future consequences. Even a lightweight first version should distinguish refusal, acceptance, and counter-demand.

[Task check list]

- [x] Add recruitment offer model and service
- [x] Add acceptance/refusal/counter-demand outcomes
- [x] Base willingness on relationship, risk, and incentives
- [x] Create contract on successful negotiation
- [x] Persist negotiation history for future memory

[Task acceptance criteria]
Entities can recruit others through explicit offers and negotiated terms, and different relationship/reputation contexts produce different outcomes.

---

[x] (checkbox) - [Task 5] - Connect contracts to tactical group instantiation and maintenance

[Task Description]
The current `GroupSystem` already forms and maintains groups, but it does so through implicit cluster logic and default goals. Phase 4 should keep the maintenance strengths of this system while changing the reason groups come into existence. Tactical groups should become execution vehicles for contract-backed projects, not auto-formed social cliques.

[Task technical implementation]
Refactor `GroupSystem` so it supports two formation modes:

- legacy/social clique mode for ambient world behavior
- contract-backed party mode for strategic cooperation

For contract-backed parties:

- create `GroupRecord` from accepted `SocialContractRecord`
- map contract purpose/project to `shared_goal`
- attach `target_id` or anchor to the party’s current objective
- set leader from contract founder or negotiated leader
- populate bonuses or coordination flags based on role composition
- dissolve or update the group when the contract changes state

This should likely use a `GroupInstantiationService` that reads strategic contract state and creates/updates `GroupRecord`s authoritatively. The existing maintenance logic for anchor, cohesion, and member liveness can then be reused.

[Task possible affected files]

- `src/systems/social/group_system.py`
- `src/core/models/lived_structure.py`
- `src/core/models/strategy.py`
- `src/systems/social/group_instantiation_service.py`

[Task important notes]
Do not delete the current group system and start over. It already provides useful maintenance and tactical cohesion logic. The right move is to separate why a group exists from how it is maintained.

[Task check list]

- [x] Add contract-backed group formation path
- [x] Map contract/project purpose to shared tactical goal
- [x] Preserve existing maintenance logic where valid
- [x] Support leader and target updates from contract/objective changes
- [x] Support clean dissolution when contract ends

[Task acceptance criteria]
Accepted contracts can materialize into tactical groups that reuse the engine’s existing coordination infrastructure while now having a real strategic purpose.

---

[x] (checkbox) - [Task 6] - Upgrade group coordination from generic follow-leader bias to role-aware party behavior

[Task Description]
The current AI only uses group membership to bias the shared goal and to push non-leaders toward the anchor when they drift too far. That is a good start, but a contract-backed expedition, escort, militia, or revenge pact needs more than “follow leader” and “share explore/combat bias.”

[Task technical implementation]
Extend the objective-to-goal and group coordination layers so party role expectations can affect tactics. For example:

- escort party -> protect principal, regroup when separated, avoid reckless pursuit
- expedition party -> scout, rally, verify lead, retreat if role coverage collapses
- defensive militia -> anchor to threatened place, defend gate, recover wounded
- mercenary team -> maintain cohesion until contract scope is met, then disengage
- revenge pact -> prioritize target pursuit but preserve group survival thresholds

This can be modeled by enriching either `GroupRecord.bonuses` or a new transient group-execution context with:

- party role assignments
- regroup thresholds
- retreat conditions
- risk tolerance
- special protection targets
- reward-linked persistence thresholds

The AI should then derive tactical biases from party role, not only from generic shared-goal multipliers.

[Task possible affected files]

- `src/ai/brain.py`
- `src/ai/strategy/objective_to_goal_mapper.py`
- `src/core/models/lived_structure.py`
- `src/systems/social/group_system.py`

[Task important notes]
Do not overbuild formation AI first. Keep the first version focused on execution expectations: who protects whom, when the party retreats, how escorts differ from hunt parties, and how contract type biases tactics.

[Task check list]

- [x] Add role-aware party execution fields
- [x] Map party type to tactical coordination behavior
- [x] Extend AI group bias beyond generic shared-goal multiplication
- [x] Add regroup and retreat thresholds
- [x] Support protection targets and escort logic

[Task acceptance criteria]
Different contract-backed party types produce meaningfully different tactical coordination patterns instead of all collapsing into “share goal, stay near leader.”

---

[x] (checkbox) - [Task 7] - Apply social and reputational consequences when contracts are honored or broken

[Task Description]
The design explicitly says promises must have cost and that whether contracts are honored should feed trust, debt, reputation, and future recruitment viability. The current engine already has the right consequence infrastructure: `RelationshipService` applies directed social bond changes through `SocialUpdate`, and `ReputationService` applies public reputation changes like trustworthiness, greed, cowardice, heroism, and defender score. Phase 4 should plug contract outcomes into those systems.

[Task technical implementation]
Create a `ContractConsequenceService` that emits:

- `SocialUpdate`s for trust, loyalty, resentment, admiration, debt
- `ReputationUpdate`s for trustworthiness, greed, cowardice, heroism, defender score
- optional narrative/turning-point events for major betrayals, rescues, or loyal stand-fast outcomes

Examples:

- fulfilled equal split -> trust up, debt neutralized, trustworthiness up
- refused promised payout -> resentment up, debt up, greed reputation up, trustworthiness down
- fled while under defensive pact -> loyalty down, cowardice up, trust down
- honored risky escort -> admiration up, defender score up, future recruitment bonus
- mercenary abandoned due to unpaid fee -> breach attributed to employer, not escort

These updates should be generated authoritatively from contract outcome records, not guessed later from combat logs.

[Task possible affected files]

- `src/core/logic/contract_consequence_service.py`
- `src/core/logic/relationship_service.py`
- `src/core/logic/reputation_service.py`
- `src/actions/base.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not make all party breakups morally equivalent. A mercenary leaving after non-payment is different from betraying an oath-backed militia defense.

[Task check list]

- [x] Add contract consequence service
- [x] Emit social bond changes from outcomes
- [x] Emit reputation changes from visible contract outcomes
- [x] Distinguish justified exit from betrayal
- [x] Support major-outcome narrative hooks

[Task acceptance criteria]
Honoring or breaking a contract creates durable social and public consequences that affect later cooperation and recruitment.

---

[x] (checkbox) - [Task 8] - Integrate public reputation into recruitment and alliance viability

[Task Description]
The design says public narrative should affect recruitment success, rumor credibility, fear response, willingness to trade or ally, faction access, and future obligations offered. The source already models public reputation through scores like heroism, cowardice, greed, defender score, trustworthiness, and threat notoriety. Phase 4 should make those fields operational in social coordination, not just inspectable.

[Task technical implementation]
Extend ally selection and recruitment willingness so public reputation affects:

- acceptance probability
- payment demands
- willingness to risk high-danger coordination
- whether desperate or greedy candidates tolerate low trustworthiness
- whether defensive or honorable candidates prefer high defender/trustworthiness reputations
- whether outcast or threatening figures trigger fear-based refusal

This should combine:

- subjective bond state from `SocialRegistry`
- public profile from `ReputationProfile`
- recent salient memories if available

The result should be that public narrative becomes a second-order cooperation filter rather than dead metadata.

[Task possible affected files]

- `src/ai/strategy/social_candidate_selection.py`
- `src/ai/strategy/recruitment_negotiation.py`
- `src/core/logic/reputation_service.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not double count reputation and trust as if they are the same thing. Public trustworthiness and private trust are related but not identical.

[Task check list]

- [x] Feed public reputation into ally ranking
- [x] Feed public reputation into negotiation outcomes
- [x] Distinguish private bond vs public narrative effects
- [x] Reflect cowardice/greed/trustworthiness/defender score in party viability

[Task acceptance criteria]
Entities with different public reputations experience different recruitment and alliance outcomes even when their direct relationship values are similar.

---

[x] (checkbox) - [Task 9] - Upgrade inn and social interaction systems into party-relevant social surfaces

[Task Description]
The current inn/social layer already supports gossip and some hero-to-hero trading, and familiarity can grow into informal “allies.” That is useful, but Phase 4 needs the inn and similar locations to become recruiting, negotiating, and contract-maintenance surfaces instead of just rumor and incidental trade surfaces.

[Task technical implementation]
Extend inn/guild/social visit logic so co-located heroes can:

- propose help on a current project
- seek specialists
- negotiate terms
- settle debts or pay shares
- renew or dissolve old pacts
- spread warnings to potential defenders
- recruit for escort, militia, or expedition tasks

This does not need a full conversation engine. It can be a structured social interaction handler that uses current projects, blockers, candidate rankings, and contract offers to produce the right strategic updates.

Locations can bias party type:

- inn -> rumor, recruiting, negotiation, debt settlement
- guild -> duty, contract brokering, quest-backed expeditions
- home/town -> militia, defense pacts, escort obligations

This builds on existing social surfaces instead of creating abstract invisible recruitment logic.

[Task possible affected files]

- inn/social handler modules
- guild visit handler modules
- `src/ai/strategy/recruitment_negotiation.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not turn buildings into menus in code form. They should act as contextual social amplifiers, not scripted recruitment terminals.

[Task check list]

- [x] Add recruit/negotiation interactions to inn/guild/social surfaces
- [x] Support debt settlement and contract renewal
- [x] Support warning-spread and militia assembly behaviors
- [x] Reuse current project/blocker context in interaction selection

[Task acceptance criteria]
Social locations become meaningful coordination hubs where parties can actually be formed, negotiated, and maintained.

---

[x] (checkbox) - [Task 10] - Add observability and regression tests for cooperation, breach, and consequence loops

[Task Description]
Phase 4 can easily become theater: the engine says there are parties and contracts, but under the hood nothing binds behavior and nothing persists after betrayal or completion. You need explicit visibility and tests that prove contracts affect recruitment, group execution, and later relationships. The design is explicit that visible consequences are what make the feature feel alive.

[Task technical implementation]
Add inspector/API visibility for:

- active contracts
- party type and purpose
- negotiated terms
- current members and required roles
- breach history
- recent payout or contract-resolution outcomes
- projected social consequences
- current tactical group linked to contract

Add tests for:

- candidate ranking uses trust/debt/reputation rather than only proximity
- successful negotiation creates contract and tactical group
- refusal and counter-demand paths persist correctly
- fulfilled terms increase trustworthiness/trust as expected
- breached terms increase resentment/debt and reduce recruitment viability
- contract-backed groups dissolve correctly on completion, leader death, or explicit failure
- different party types produce different tactical coordination biases

Use deterministic fixtures and assert stable outcomes under fixed world state and RNG.

[Task possible affected files]

- `src/ui/cli/inspector.py`
- API debug/inspection modules
- `tests/ai/test_social_candidate_selection.py`
- `tests/ai/test_recruitment_negotiation.py`
- `tests/systems/test_contract_group_integration.py`
- `tests/core/test_contract_consequences.py`

[Task important notes]
Do not rely on anecdotal simulation stories as proof. This phase needs hard assertions that contracts alter later cooperation and reputation.

[Task check list]

- [x] Add contract and party inspection views
- [x] Add recruitment ranking tests
- [x] Add negotiation and contract lifecycle tests
- [x] Add breach consequence tests
- [x] Add group-integration tests
- [x] Add deterministic repeatability coverage

[Task acceptance criteria]
You can prove that cooperation is negotiated, tactically instantiated, and socially remembered, rather than being a temporary movement bonus with narrative dressing.

---

Priority Plan

What must change in mindset or assumptions
Stop treating the current group system as “close enough” to a party system. It is not. It is tactical coordination infrastructure. The design gap is explicit purpose, negotiated terms, and remembered consequences.

What actions must be taken immediately
Do Tasks 1 through 5 first: define contract records, persist them authoritatively, build ally ranking, implement negotiation, and connect accepted contracts to tactical groups. Then do Tasks 6 through 9 so different party types behave differently and social hubs actually matter. Finish with Task 10 before declaring the phase done.

What must stop or be eliminated
Stop using same-cluster auto-grouping and default shared-goal bias as a substitute for cooperation. Stop making public reputation inspectable but behaviorally irrelevant. Stop treating broken promises as flavor text instead of state transitions with cost.

The consequences and opportunity cost if this fails
You will have a world where entities can stand together and even move together, but cannot actually rely on each other, negotiate, owe each other, betray each other meaningfully, or come back later shaped by that history. That means the social layer stays cosmetic and the most human part of the design never materializes.
