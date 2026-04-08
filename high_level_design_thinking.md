Here is the design, stripped down to the real problem.

You do **not** want a “story system.”
You want a **life-simulation cognition layer** that produces stories as a side effect.

Your current engine already has the beginnings of that substrate: personality, motives, subjective beliefs, emotions, narrative memory, routines, social stance, place attachments, group coordination, rumor sharing, interpreted life events, and a per-tick cognitive pipeline. But the present mind is still mostly immediate and tactical; it scores goals like combat, flee, explore, loot, trade, rest, craft, social, guard, sleep, and eat, then picks a state for the next span of time. That is good local behavior, but it is not yet durable life-direction.

So the design below is for a **persistent, subjective, branching life-direction system** that sits above moment-to-moment action and allows each entity to build its own history.

## 1. The design target

The target is not:

- authored quests
- fixed branching story trees
- a giant prebuilt graph of all stories
- a single “smartness” stat

The target is this:

Each entity should be able to:

- care about enduring things
- interpret events personally
- maintain unfinished business
- reason under incomplete knowledge
- create and suspend projects
- discover blockers
- seek information or help
- bind itself socially through obligations
- reprioritize when the world changes
- remember what happened and let it shape future judgment

If these capacities are present, stories emerge.

If they are absent, all you have is a reactive state machine wearing a narrative costume.

## 2. Core worldview: three interacting graphs

Think in three layers, not one.

### Shared world graph

This is objective reality:

- terrain, towns, camps, ruins, mountains
- buildings like guild, class hall, inn, blacksmith, store, hero houses
- factions, NPCs, monsters, bosses
- resources, items, material sources, threats, routes, travel constraints

Your engine already expresses parts of this through grid terrain, buildings, camps, resource nodes, factions, and world entities. Guild visits already reveal camp and resource locations into terrain memory, and class hall visits already expose progression-related opportunities.

### Subjective affordance graph

This is what one entity currently believes is possible, valuable, risky, and reachable.

It is shaped by:

- vision and attention
- stale or fresh beliefs
- direct versus indirect knowledge
- confidence and source trust
- personality
- motives
- role
- routines
- attachments
- grudges
- group membership
- social bonds
- obligations
- remembered outcomes

Your engine already supports subjective beliefs with freshness, confidence, directness, and source confidence; selective attention; personality and motive biases; emotional state; social stance; and place attachments.

### Active decision slice

This is the small part of the subjective graph the entity is actively considering right now.

Most of the world is ignored most of the time. The active slice is narrowed by:

- urgency
- salience
- ongoing commitments
- proximity
- survival pressure
- social expectations
- current blockers
- current opportunities

This is critical. Without an active slice, cognition becomes combinatorial garbage. With it, each entity can have a huge latent possibility space while only reasoning over a relevant local front.

## 3. The true structure of an entity mind

The current `MindAspect` is already decomposed into decision, perception, emotion, navigation, narrative, routine, social, and lived-structure pieces. That is the right base.

What is missing is a **Strategic Layer**. Conceptually, the mind should contain five strata:

### A. Identity stratum

This is who the entity believes it is.

Not cosmetic identity. Behavioral identity.

It contains:

- archetype
- role in the world
- faction identity
- loyalty orientation
- ambition orientation
- threat tolerance
- moral boundaries
- self-concept labels

Your engine already seeds archetypes and initial motives such as build wealth, prove strength, serve faction, seek safety, or explore, and also seeds world roles and place attachments.

The design requirement is that identity must do more than bias utilities. It must answer:

- What kinds of obligations feel binding?
- What kinds of losses feel personal?
- Which humiliations demand response?
- Which tradeoffs are acceptable?
- What kinds of unfinished business keep mattering?

### B. Belief stratum

This is what the entity thinks is true.

Not only about visible enemies, but about:

- places
- routes
- materials
- faction intentions
- boss difficulty
- rumor credibility
- possible opportunities
- people’s trustworthiness
- what other entities know
- what is reachable with current strength

Your engine already has `BeliefRecord` with confidence, directness, source confidence, apparent role/class/faction, perceived reputation, and threat estimate, plus gossip-style indirect sharing.

The design extension is that beliefs should cover not just “who is that entity,” but also:

- “where might the flower be?”
- “which region is likely relevant?”
- “how strong is the guardian likely to be?”
- “who might join my party?”
- “which guide is reliable?”
- “how threatened is my home?”

This is the substrate for uncertain narrative development.

### C. Narrative-memory stratum

This is what the entity thinks has happened in a personally meaningful way.

Your engine already distinguishes:

- raw memory log entries
- interpreted life events
- turning points
- reputation consequences
- relationship consequences

That is a strong foundation.

The design requirement is that memory must be **causal**, not just archival. The entity should be able to treat memories as:

- evidence
- warnings
- obligations
- grievances
- proof of competence
- proof of danger
- anchors for self-story

Examples:

- “I almost died at the frozen pass.”
- “The guild’s rumor about the ruins was false.”
- “That hero abandoned me.”
- “I avenged my ally once; I am the sort who answers blood with blood.”
- “The class master told me what I lack.”

Turning points must alter not just mood, but future project creation and reprioritization.

### D. Strategic stratum

This is the missing layer.

This stratum holds:

- enduring directives
- active projects
- suspended projects
- concerns
- leads
- obligations
- blockers
- social contracts
- resumable unfinished business

This is where continuity lives.

### E. Tactical stratum

This is your current utility and state-based layer.

It should remain narrow:

- immediate local choice
- movement
- attack
- use skill
- rest
- sleep
- eat
- visit building
- loot
- flee

It should not try to own the whole story.

## 4. The universal units of story

Do not encode stories directly. Encode these units.

### Directive

A directive is an enduring orientation, usually rooted in archetype, role, identity, or history.

Examples:

- protect home
- become strong
- uphold faction
- gain wealth
- seek safety
- pursue prestige
- explore the unknown
- avenge wrongs

Directives are not tasks. They are sources of recurring project generation.

A directive can be:

- foundational: seeded at birth/creation
- acquired: born from turning points or social bonds
- transformed: altered after major life events

Example:
A balanced hero may begin with “explore” and “grow stronger.”
After ally death, “avenge fallen comrades” may become enduring.

### Project

A project is a medium-to-long-term pursuit serving one or more directives.

Projects have:

- purpose
- current status
- progress
- blockers
- urgency
- emotional weight
- reversibility
- social cost of abandonment
- expected reward
- current sub-objectives

Examples:

- class breakthrough
- rebuild house
- secure iron supply
- investigate mountain rumor
- destroy goblin camp
- recruit expedition
- restore reputation
- rescue captured ally

Projects are the main carriers of life continuity.

### Objective

An objective is an actionable subproblem inside a project.

Examples:

- visit class hall
- ask master about breakthrough
- raise STR to threshold
- gather ore
- visit guild for leads
- scout candidate region
- test cave entrance
- recruit a tank and healer
- save gold for expedition supplies
- return to town after warning
- defend the gate
- find who spread the rumor

Objectives should be concrete enough to map to local goals and state handlers, but abstract enough to survive interruptions.

### Concern

A concern is an urgent pressure injected by the world or by unresolved emotion.

Concerns are what create branching.

Examples:

- town attacked
- home damaged
- ally died nearby
- debt overdue
- rumor contradicted
- guardian spotted
- rival insulted reputation
- faction leader summoned support

A concern is not automatically a project. It is a pressure seeking response.

### Lead

A lead is uncertain, partial, or second-hand information relevant to a project.

Examples:

- “flower grows where snow never melts”
- “iron caravans disappear near grey hills”
- “orc warlord holds enchanted dust”
- “an old hunter saw lights in the ruins”
- “the class master hinted your spirit is unready”

The lead must carry:

- subject
- source
- certainty
- freshness
- directness
- interpreted meaning
- candidate places/entities/topics
- whether it has already been tested

This is the backbone of investigation and discovery.

### Blocker

A blocker is the explicit reason a project or objective cannot progress.

Examples:

- too weak
- location unknown
- lack required material
- path unsafe
- not enough allies
- trust too low
- guild closed
- obligation conflict
- time window missed
- target already moved
- wrong climate/season
- town emergency overrides

Blockers matter because they create detours instead of dead ends.

### Obligation

An obligation is a socially or morally binding commitment.

Examples:

- promised equal pay to allies
- accepted guild quest
- owe gold to merchant
- sworn to defend town
- pledged to escort wounded hero
- vowed revenge over ally’s corpse

Obligations are crucial because they keep entities from behaving like purely selfish optimizers.

### Social contract

A social contract is an explicit negotiated coordination structure.

Examples:

- temporary party
- mercenary hire
- alliance for boss kill
- defensive pact
- trade arrangement
- mutual protection agreement

Your engine already has group formation and cohesion, plus social bonds and alliance-like closeness in hero familiarity. The missing design layer is explicit purpose and expectation.

## 5. The life-direction model

Every entity’s life should be understood as a sequence of transformations in this form:

**identity -> directives -> projects -> objectives -> local action -> events -> interpretation -> updated identity/directives/projects**

That loop is the true “story machine.”

The loop must be history-sensitive:

- success reinforces some directives and weakens others
- failure creates blockers and caution
- betrayal changes trust and willingness to recruit
- gossip changes knowledge and source weighting
- public events change reputation and social affordances
- home damage strengthens place attachment or grief
- repeated neglect may dissolve old commitments

This is how looping feels infinite instead of repetitive.

## 6. Project anatomy

Projects should not be shallow records. They should have an inner life.

A good project has the following conceptual dimensions.

### Origin

Why does this project exist?

- directive-derived
- event-derived
- obligation-derived
- social imitation
- opportunistic discovery

### Ownership

Who claims it?

- individual
- pair
- group
- faction-delegated
- socially shared but privately weighted

### Emotional charge

How much does this project matter beyond utility?

- pride
- fear
- grief
- shame
- hope
- duty
- greed
- curiosity

### Visibility

Who knows about it?

- private
- shared with allies
- publicly declared
- inferred by others

### Persistence

How resistant is it to interruption?

- fragile
- stable
- obsessive
- sacred

### Recovery behavior

If interrupted, does it:

- disappear
- suspend
- split into subprojects
- mutate into revenge/rebuild/avoidance
- stay as dormant unfinished business

### Completion semantics

When is it done?

- objective satisfied
- symbolic closure achieved
- target eliminated
- obligation fulfilled
- emotional closure reached
- abandoned as no longer meaningful

This matters because “kill goblin chief” and “avenge family” are not the same kind of completion. One is objective closure; the other may require emotional and social interpretation.

## 7. Objective classes

Objectives should come from a small, reusable vocabulary.

### Informational objectives

Used when knowledge is missing.

- ask expert
- gather rumor
- observe target
- scout region
- verify clue
- follow trail
- inspect site
- interrogate witness
- compare conflicting sources

### Capability objectives

Used when the entity lacks means.

- level up
- train attribute
- improve mastery
- learn skill
- attempt breakthrough
- craft upgrade
- obtain consumables
- gather funds

Your current class hall and blacksmith/guild loops already imply some of these, but presently they are not formalized as durable objectives. Guilds provide resource hints and quests; class halls reveal skills and breakthroughs; blacksmith logic already reasons about missing materials and gold.

### Access objectives

Used when something is known but not reachable.

- unlock route
- find safe path
- obtain key/permission
- secure escort
- time travel with weather/day cycle
- gain political access

### Social objectives

Used when help, trust, or coordination is needed.

- recruit ally
- repay debt
- negotiate terms
- restore trust
- request training
- spread warning
- seek faction backing
- hire specialist

### Defensive objectives

Used when existing commitments are threatened.

- return home
- defend town
- protect ally
- reinforce gate
- evacuate civilians
- recover body
- rebuild building

### Retributive objectives

Used when a harm event is interpreted as demanding response.

- investigate attacker
- identify responsible faction
- retaliate
- seek justice
- publicly expose betrayal
- exact symbolic revenge

### Maintenance objectives

Used to keep life coherent.

- sleep
- eat
- sell loot
- store items
- visit home
- repair gear
- reduce stress
- resume suspended project

These matter because entities without maintenance become unbelievable and tactically brittle. Your engine already has routine and bio-needs for sleep/eat and routines anchored by role and time windows.

## 8. The role of uncertainty

Without uncertainty, there is no search, no rumor, no suspense, and no divergence.

The design needs several forms of uncertainty.

### Epistemic uncertainty

The entity does not know if something is true.
Example:

- “flower may be in the far snow mountains”

### Locational uncertainty

The subject is real but exact location is unknown.
Example:

- multiple candidate regions

### Capability uncertainty

The entity does not know if it is strong enough.
Example:

- it knows a guardian exists, but not exact combat viability

### Social uncertainty

The entity does not know whether others will help or betray.
Example:

- possible recruits may refuse or overcharge

### Temporal uncertainty

The opportunity may shift over time.
Example:

- a caravan passes only sometimes
- attacks may occur while absent

Your belief system already has direct versus indirect knowledge and confidence decay. That is exactly the right foundation for this design.

The design principle is simple:
uncertainty should create **investigative behavior**, not paralysis.

## 9. The social layer as a force multiplier

A real story system cannot be solitary.

Your engine already has:

- social bonds with trust, fear, loyalty, resentment, admiration, rivalry, debt, familiarity
- interpreted life events that update relationship and reputation
- group records with leader, members, shared goal, anchor position, cohesion
- rumor and memory sharing at inns
- social utility biasing in appraisal

That is strong. The design should elevate this from flavor to necessity.

### Social dependency

Some projects should be structurally hard to complete alone.
Not because the game forbids solo behavior, but because:

- risk is too high
- role coverage is poor
- trust unlocks access
- specialists provide unique knowledge
- witnesses authenticate truth
- public action affects reputation

### Social perception

An entity should not simply ask “Can I do this?”
It should ask:

- Who knows something I lack?
- Who owes me?
- Who trusts me enough to come?
- Who is brave enough?
- Who benefits from helping?
- Who is likely to betray?
- Who is already busy with their own obligations?

### Social contracts and memory

When alliances form, terms matter:

- equal split
- payment in advance
- claim on rare material
- shared revenge
- future favor
- guild duty
- oath-backed obligation

Whether the contract is honored should feed:

- trust
- debt
- reputation
- future recruitment viability

This is where stories become socially sticky rather than individually random.

## 10. Place attachment and home defense

Your engine already seeds place attachments and home positions as part of lived structure. That is important.

The design consequence is that “town attacked” should not be a generic event. It should hit different entities differently.

A place threat should be evaluated through:

- attachment strength
- whether loved/allied people are there
- whether the entity sees itself as protector
- faction loyalty
- shame cost of absence
- current project reversibility
- distance and travel feasibility

Possible personal responses:

- immediate return
- rally others first
- send warning
- keep current mission because return is impossible
- guilt and later revenge
- decide home is lost and relocate attachment
- radicalize into anti-goblin crusader identity

This is where the same event produces different lives.

## 11. Reprioritization design

Branching should not be “event happens, utility plus five.”

That is amateur design.

Reprioritization should compare:

- directive alignment
- emotional charge
- urgency
- irreversibility
- social cost of inaction
- likelihood of success
- current project stage
- memory resonance
- attachment relevance

For example, a town attack can outrank a strength-gain project because:

- it threatens a highly attached location
- it triggers protector identity
- it threatens obligations
- delayed response increases irreversible loss

But for a cowardly survivor far away with weak home attachment, the same event may produce:

- avoid returning
- wait for clearer info
- seek safety
- rationalize non-involvement

That divergence is the whole point.

## 12. The design of blockers and detours

A blocker is not failure. It is story fuel.

When a project hits a blocker, the system should not ask only:

- continue or stop?

It should ask:

- What kind of blocker is this?
- Which detour types are appropriate?
- Is the blocker factual, social, logistical, or emotional?
- Does the blocker spawn new objectives?
- Does it suspend the project, mutate it, or redirect it?

Blocker types:

- knowledge blocker
- capability blocker
- access blocker
- social blocker
- moral blocker
- timing blocker
- emotional blocker
- competing obligation blocker

Typical detour families:

- train more
- gather materials
- seek a guide
- recruit allies
- earn money
- gain trust
- find alternative route
- postpone until season/day
- abandon as not worth it
- reinterpret project into a different one

This is how you avoid scripting story branches explicitly while still getting structured branching.

## 13. Investigative behavior and vague leads

The scenario you described depends on partial information. This deserves its own design.

A vague lead should never directly become:
“Go to exact coordinate.”

It should become:

- a hypothesis set
- a ranked search space
- a reason to seek further narrowing clues
- a potential social chain of consultation

A good lead system contains:

- source identity
- source trustworthiness
- whether source had direct sight or hearsay
- semantic tags
- inferred region types
- confidence
- contradiction status
- search history
- derived candidate zones
- already tested interpretations

Examples:
“far snow mountain”
could map not to one tile but to:

- remote snowy regions
- high-altitude cells
- old shrine rumors nearby
- guardian-likely locations
- rare flora biome compatibility

This makes investigation feel like investigation instead of quest-arrow marching.

Your current guild already provides terrain and material hints, which proves the world can leak structured knowledge into the mind. The design should generalize that into a real lead system.

## 14. Group and party design

Your existing group layer gives members, leader, shared goal, anchor position, and cohesion, and the AI already biases toward group shared goals and following leaders when far away.

Good. The design extension is this:

A party is not just a group with proximity. It is a **purposeful temporary social machine**.

A party should have:

- purpose
- formation reason
- agreed reward logic
- role expectations
- fallback conditions
- dissolving conditions
- ownership of loot/reward/credit
- social memory if promises are broken

Types:

- hunt party
- defensive militia
- escort team
- expedition party
- revenge pact
- mercenary team

A party should be formed when:

- blocker analysis concludes solo failure is likely
- multiple entities have aligned or negotiable interests
- trust and incentive thresholds are sufficient

A party should dissolve when:

- project complete
- objective impossible
- casualties break morale
- reward dispute fractures trust
- leader dies or flees
- emergency redirects members

This design makes “ask other heroes for help” a general mechanism, not a bespoke script.

## 15. Public narrative vs private narrative

A believable life system needs both.

### Private narrative

What the entity believes its life means.
Examples:

- “I failed my town.”
- “I am meant for greatness.”
- “The guild is useful.”
- “I cannot trust greedy allies.”
- “The frozen guardian is my unfinished trial.”

### Public narrative

What the world believes about the entity.
Examples:

- hero
- coward
- unreliable
- avenger
- goblin-slayer
- oath-breaker
- defender of the walls

Your engine already has interpreted life events and reputation profiles with heroism, cowardice, greed, defender score, trustworthiness, and threat notoriety.

The design requirement is that public narrative should affect:

- recruitment success
- rumor credibility
- fear response from others
- willingness to trade or ally
- faction access
- future obligations offered

This creates second-order stories:
not just what you did, but what others think you did.

## 16. Narrative salience and forgetting

Not everything should matter equally.

If every event becomes permanent, minds become cluttered and behavior becomes noisy.
If nothing persists, there is no continuity.

So memories, concerns, and projects need salience rules.

A thing becomes salient when it is:

- near death
- ally death
- betrayal
- rescue
- public humiliation
- home damage
- first major success
- promise made under pressure
- discovery of major lead
- repeated blocker encounter

Your current turning point model already treats near death, ally death, revenge, betrayal, rescue, disgrace, boss encounter, or first kill as life-defining categories. That is the right intuition.

The design rule:
salience determines persistence, emotional residue, and future project-generation power.

## 17. The story grammar

This is the compact rule set that replaces authored story trees.

A small number of generic patterns should be enough.

### Pursuit pattern

Want something -> identify missing requirements -> acquire knowledge/capability/access -> pursue

### Investigation pattern

Know subject but not truth -> gather clues -> test hypotheses -> refine search -> resolve or misresolve

### Blocked ambition pattern

Attempt something too early -> hit blocker -> prep detour -> retry later

### Obligation pattern

Accept promise/duty -> constrain future choices -> fulfill, delay, or break -> social consequence

### Threat response pattern

Threat emerges -> assess attachment/urgency -> defend, flee, ignore, warn, or avenge

### Group assembly pattern

Project exceeds solo capability -> seek compatible allies -> negotiate terms -> coordinate -> success/failure -> aftermath

### Loss/revenge pattern

Suffer loss -> assign blame -> choose revenge, justice, grief, avoidance, or hardening

### Reputation spiral pattern

Publicly visible actions -> reputation shifts -> changes future access and trust -> alters future opportunities

### Homecoming pattern

Return to attached place after growth/failure -> compare expectations to reality -> renew, rebuild, abandon, or recommit

These patterns are enough to produce hundreds of story shapes because the contents vary.

## 18. The hero example, generalized correctly

Your hero scenario is not a special story. It is the composition of several generic patterns.

The actual sequence is:

- identity: honorable/protective/ambitious hero
- directive: protect people by becoming stronger
- project: increase power
- objective: evaluate growth routes
- informational objective: consult class authority
- knowledge acquisition: breakthrough requirements learned
- capability objectives: raise attributes, gather rare material
- informational objective: ask guide about material
- lead acquired: vague clue, low certainty
- investigation objective: search candidate regions
- threat discovery: guardian encountered
- blocker inferred: insufficient capability
- strategic response: retreat, preserve life
- social objective: recruit allies with fair terms
- group project: expedition
- interruption: town attacked
- concern outranks current project
- branch: defend town if possible, or revenge/rebuild if not
- suspended project persists
- later resumption under changed identity and conditions

That is not one story path. It is a lawful traversal through generic units.

## 19. What makes different entities build different stories

Three entities in the same world should traverse different paths because of:

### Different identities

Ambitious glory-seeker, honorable defender, cowardly survivor, greedy opportunist. Your engine already seeds archetypes with different personality dimensions and initial motives.

### Different knowledge

One saw the guardian directly, one heard a rumor, one trusts the guide, one distrusts the guild.

### Different attachments

One’s home is in town, one is rootless, one is faction-devoted, one is self-protective.

### Different social capital

One is trusted and can recruit; another has debts and bad reputation.

### Different emotional histories

One already lost a sibling to goblins; another has no personal grievance.

### Different capability profiles

One can nearly solo the boss; another must form a party.

### Different obligation loads

One is escorting someone; another accepted a guild quest; another owes money.

This is why the same event should not create the same branch for everyone.

## 20. Coherence rules

This kind of system can turn to sludge if you do not enforce coherence.

The design needs a few hard invariants.

### Invariant 1: entities should have unfinished business

Not dozens. A meaningful few.

### Invariant 2: projects should not be abandoned casually

Dropping commitments every few ticks destroys story.

### Invariant 3: interruption must be filtered by identity and attachment

Otherwise the world yanks everyone around equally.

### Invariant 4: vague information should create search, not certainty

Otherwise knowledge systems collapse into markers.

### Invariant 5: social promises must have cost

Otherwise cooperation is free noise.

### Invariant 6: consequences must persist

Broken contracts, betrayal, cowardice, rescue, revenge, major failure — these must echo.

### Invariant 7: loops must be history-sensitive

Returning to town after a disaster cannot feel identical to returning after a triumph.

## 21. Failure modes to avoid

These are the traps.

### Fake emergence

The system produces random detours and calls them stories.

### Utility flattening

Everything is reduced to temporary score nudges, so nothing truly persists.

### Infinite combinatorics

Too many possible concerns/projects/objectives become simultaneously active.

### Social emptiness

Parties and allies exist physically but have no contract memory or expectation.

### Knowledge collapse

Rumors immediately become precise truth.

### Emotional theater

Entities “feel” panic, dread, or joy, but these feelings do not create new commitments or alter obligations. Your current system already applies emotional biases, but this layer must be extended into durable strategic effect.

### Homogenized lives

Every hero ends up chasing the same template because the subjective graph is not differentiated enough.

## 22. What “smartness” means in this design

Not IQ.

Smartness here means quality of traversal through the entity’s private graph.

A “smarter” entity should not have a magic answer key. It should have:

- better hypothesis ranking
- better blocker diagnosis
- better ally selection
- better contract judgment
- better memory use
- lower chance of false certainty
- stronger ability to suspend/resume coherently
- better distinction between urgent and merely tempting concerns

A “dumber” entity should:

- overcommit to weak leads
- misjudge trust
- panic-reprioritize poorly
- forget obligations
- loop on bad strategies
- mistake rumors for certainty
- abandon important projects too easily
- get socially exploited more often

That is believable intelligence in a sim.

## 23. What makes the feature feel alive to a player or observer

Not the hidden models. The visible consequences.

A good life-direction system produces entities that can be described in plain language:

- “She left town seeking power, but after the goblin raid she became obsessed with retaliation.”
- “He trusted the wrong guide and spent weeks chasing a false mountain clue.”
- “That ranger became famous not for strength, but for always bringing people home alive.”
- “Those two heroes only teamed up once, but that debt kept them linked afterward.”
- “He nearly broke through, retreated from the guardian, then came back later with a hired party.”

If observers can say that without you hand-authoring the sequence, the design is correct.

## 24. Grounded fit with the current engine

This design is not floating in fantasy. It matches what the engine already wants to become.

The current mind already supports:

- personality and motives
- belief records with uncertainty and source quality
- memory and turning points
- reputation and social bonds
- place attachment and routines
- group shared goals and cohesion
- inn gossip and knowledge propagation
- guild hints and location revelation
- class hall learning and breakthrough opportunities
- event bus for important world events

The present limitation is that these pieces are still too tactical and too thinly unified. The design above is the conceptual unification: one mind that can live across time instead of merely choosing the next state.

## 25. The full design in one sentence

A story-capable entity is an identity-bearing, belief-limited, socially entangled agent that carries persistent projects across interruptions, uses partial information to create investigative and cooperative behavior, and converts meaningful events into durable reprioritization.

That is the feature.

Not “quest AI.”
Not “emergent narrative.”
Not “story graph.”

A **subjective life-direction system**.

Priority Plan

What you must change in mindset or assumptions
Stop thinking about story as authored branching content. The correct design object is persistent agency under uncertainty, memory, and social consequence.

What actions you must take immediately
Define the feature in terms of universal units: directives, projects, objectives, concerns, leads, blockers, obligations, contracts, attachments, and turning points. Make every design discussion about how these units transform into one another over time.

What you must stop or eliminate
Stop adding more shallow local goals and calling that depth. Stop treating rumors as coordinates. Stop treating group behavior as mere proximity. Stop treating emotions as temporary score nudges with no lasting strategic meaning.

The consequences and opportunity cost if you fail to change
You will keep building content-shaped AI instead of life-shaped AI. The world may get larger, but the entities will still feel interchangeable, forgetful, and fake.

If you want, the next step is a taxonomy of all major narrative patterns this design should support, with examples of how each one differs by archetype, attachment, and social context.
