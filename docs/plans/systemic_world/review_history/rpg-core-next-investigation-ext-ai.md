---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `rpg-core-next-investigation-ext-ai.md` on 2026-09-27. An input to the planning work, not current status.

## Objective

Perform a repo-grounded investigation of how the current RPG simulation represents and uses the factors that shape an entity's:

* moment-to-moment decisions,
* behavioral continuity,
* preferences and dispositions,
* relationships and social behavior,
* capability development,
* long-term life trajectory,
* role/status evolution,
* identity and reputation,
* and emergent characterization over time.

`archetype`, `personality`, and `characteristics` are only starting examples.

The real question is broader:

> **What currently causes two otherwise similar entities to make different choices, develop differently, form different relationships, pursue different opportunities, and become meaningfully different people over a lifetime?**

This is an investigation and architecture review.

Do **not** make implementation changes or modify World Rules unless separately instructed.

---

# 1. Start from the current authoritative architecture

Review the relevant current sources, including at minimum:

* frozen World Rule Catalog,
* Agency / Perception / Knowledge rules,
* Capability / Progression / Conflict rules,
* Social / Family / Lineage rules,
* Organizations / Politics / Law where relevant,
* Culture / Collective Belief where relevant,
* Identity / History / Provenance rules,
* Life / Body rules,
* Objects / Economy where they influence development,
* Mechanism Registry,
* relevant mechanism implementations,
* existing scenario/evaluation material,
* any existing concepts or code named around:

  * personality,
  * characteristic,
  * trait,
  * archetype,
  * temperament,
  * disposition,
  * preference,
  * value,
  * motivation,
  * goal,
  * desire,
  * fear,
  * need,
  * habit,
  * memory,
  * belief,
  * affinity,
  * affection,
  * loyalty,
  * reputation,
  * relationship,
  * role,
  * profession,
  * identity,
  * status,
  * ambition,
  * aspiration,
  * behavior,
  * decision,
  * utility,
  * priority,
  * skill,
  * experience,
  * progression,
  * development,
  * life history.

Use repo evidence rather than assuming these concepts do or do not exist.

Remember:

> absence from the Mechanism Registry does not prove absence from the repository.

---

# 2. Do not treat all character concepts as the same kind of thing

For each relevant concept you find, classify its semantic role.

Use at least these categories.

### A. Causal world state

State that actually exists in the simulation and can affect future outcomes.

Examples may include:

* beliefs,
* goals,
* preferences,
* persistent dispositions,
* relationships,
* capabilities,
* injuries,
* resources,
* social status,
* memories,
* fears,
* loyalties.

Do not assume the examples already exist.

Verify.

---

### B. Derived world characteristic

A summary or interpretation of lower-level state/history.

Examples:

* veteran,
* wealthy,
* experienced,
* dangerous,
* isolated,
* well-connected,
* skilled swordsman.

Test:

> If the label disappeared but the underlying history/state remained unchanged, would simulation behavior remain unchanged?

If yes, it is probably derived rather than authoritative state.

---

### C. Socially recognized label

A derived identity that becomes causal because other entities actually know, believe, recognize, or react to it.

Examples:

* hero,
* criminal,
* monster slayer,
* famous swordsman,
* traitor,
* saint.

Distinguish:

```text
objective history
≠ derived description
≠ somebody's belief about the entity
≠ widely propagated reputation
```

A label becoming socially consequential should happen through existing Information / Knowledge / Social / Culture semantics rather than by narrative fiat.

---

### D. Narrative / analytical interpretation

Concepts that may be useful to a storyteller, UI, analyst, or biography generator but do not need to exist inside the simulated world.

Examples:

* archetype,
* character arc,
* wandering swordsman,
* reluctant leader,
* fallen hero,
* mentor figure,
* protagonist,
* redemption arc.

Investigate whether the current repo already represents any of these.

If it does, determine whether they are:

* causal simulation state,
* derived metadata,
* content-generation metadata,
* authoring hints,
* legacy abstractions,
* or something else.

Do not automatically conclude that archetypes belong outside simulation; report what the actual implementation does and whether that role is coherent.

---

# 3. Specifically investigate Personality

Determine exactly what `personality` means in the current system, if it exists.

Questions to answer:

* Is personality stored persistently?
* What owns it?
* Is it generated at entity creation?
* Can it change?
* Can lived history modify it?
* Does it influence decisions?
* Through what mechanism?
* Is it deterministic or merely biasing?
* Is personality directly consumed, or stored but inert?
* Are personality dimensions independent?
* Is personality just metadata used by content generation?
* Does personality affect:

  * risk tolerance,
  * aggression,
  * social preference,
  * exploration,
  * ambition,
  * loyalty,
  * cooperation,
  * greed,
  * curiosity,
  * persistence,
  * fear response,
  * relationship formation,
  * career selection,
  * faction behavior?
* Are any such effects actually verified at runtime?

Important distinction:

```text
persistent disposition
+ current context
+ knowledge/belief
+ goals/needs
+ relationships
+ opportunity
+ constraints
→ decision
```

Check whether the existing architecture behaves approximately like this or whether one input dominates / bypasses the others.

---

# 4. Specifically investigate Characteristics / Traits

Determine whether `characteristic`, `trait`, or equivalent concepts exist.

For each:

* Is it innate?
* acquired?
* derived?
* temporary?
* permanent?
* mutable?
* observable by others?
* causal?
* merely descriptive?

Check whether characteristics may arise from:

```text
biology
history
training
injury
culture
profession
relationship
social recognition
magic
equipment
environment
```

Also identify whether different concepts are being overloaded under one generic `trait` system despite having different semantics.

Example potential problem:

```text
brave
scarred
noble-born
fire-resistant
merchant
famous
```

should not necessarily all behave as the same semantic category merely because all are called `traits`.

Report if the current architecture collapses unlike concepts into one container.

---

# 5. Specifically investigate Archetypes

Locate all archetype-related concepts in the current repo.

Determine:

* who assigns an archetype,
* when,
* whether it is mutable,
* whether multiple archetypes can coexist,
* whether archetype affects decisions,
* whether it changes stats/capability,
* whether it selects behaviors,
* whether it is used for generation only,
* whether it is inferred from history,
* whether agents know their own archetype,
* whether other entities know it,
* whether it exists only for authoring/content systems.

Then evaluate the directionality.

Potentially coherent:

```text
history + behavior + capability + role
→ derived archetype
```

Potentially dangerous unless intentionally designed:

```text
archetype = HERO
→ entity automatically chooses heroic decisions
```

Do not label either model wrong without checking current design intent.

Report the actual model and consequences.

---

# 6. Expand beyond those three concepts

This investigation should identify the **full set of factors currently used to produce entity decisions and long-term development**.

Do not constrain the answer to personality/archetype/characteristic.

Look for factors such as:

### Internal state

* needs,
* desires,
* goals,
* values,
* motivations,
* fears,
* emotions,
* mood,
* stress,
* trauma,
* habits,
* memories,
* beliefs,
* expectations,
* preferences,
* personality,
* disposition.

### Physical / capability state

* body,
* health,
* age,
* species,
* innate capability,
* learned skills,
* experience,
* equipment,
* magic,
* fatigue,
* injury.

### Social state

* relationships,
* affection,
* trust,
* loyalty,
* kinship,
* rivalry,
* debt,
* obligation,
* reputation,
* role,
* rank,
* organization membership.

### Economic state

* wealth,
* property,
* employment,
* access to resources,
* profession,
* contracts,
* trade relationships.

### Spatial / environmental state

* location,
* reachable opportunities,
* danger,
* local resources,
* local law,
* nearby actors,
* travel capability.

### Informational state

* knowledge,
* misinformation,
* rumors,
* memory,
* uncertainty,
* awareness of opportunity,
* awareness of consequences.

### Political / institutional state

* authority,
* obligations,
* law,
* faction interest,
* social class,
* titles,
* institutional constraints.

### Historical state

* past victories,
* failures,
* injuries,
* major relationships,
* previous choices,
* promises,
* betrayals,
* accumulated provenance.

### External opportunity / pressure

* quests,
* jobs,
* threats,
* wars,
* trade opportunities,
* social requests,
* faction recruitment,
* crises,
* environmental change,
* supernatural events.

This list is not a requirement that all must exist.

It is a search space.

---

# 7. Reconstruct the actual decision pipeline

From real code/mechanisms, determine as precisely as possible:

```text
What information reaches an entity before a decision?
↓
How candidate actions/opportunities are formed
↓
How they are evaluated/prioritized
↓
Which state modifies the evaluation
↓
How a choice is selected
↓
How action is executed
↓
How consequences update future decisions
```

Identify:

* hard gates,
* weights,
* utility functions,
* rule engines,
* random selection,
* scripted behavior,
* planners,
* AI policies,
* heuristic scoring,
* behavior trees/state machines if present,
* fallback behavior.

Do not infer sophistication that is not present.

---

# 8. Reconstruct the development / progression pipeline

Separately trace:

```text
experience/event
↓
persistent change
↓
new capability / relationship / identity / opportunity
↓
changed future behavior
↓
further history
```

Investigate whether entities can actually develop through lived history.

Examples:

```text
combat
→ experience
→ sword capability
→ stronger contracts
→ reputation
→ higher-level opponents
```

or:

```text
merchant relationship
→ trust
→ better trade terms
→ wealth
→ new business opportunities
→ social status
```

or:

```text
traumatic defeat
→ persistent behavioral change
→ avoids similar risks
```

For each type currently supported, identify the actual causal chain.

---

# 9. Look for disconnected state

A particularly important output is state that exists but does not meaningfully participate in future simulation.

Examples:

```text
personality exists
but decision system never consumes it

reputation changes
but nobody checks reputation

relationship score changes
but action selection ignores relationships

skill increases
but available actions never change

history recorded
but future behavior cannot inspect it

archetype assigned
but has no consumer
```

Classify such cases carefully as appropriate:

* implementation gap,
* wiring gap,
* inactive/off mechanism,
* derived-only by design,
* narrative-only by design,
* unknown.

Do not automatically call inert descriptive metadata a bug if it was never intended to be causal.

---

# 10. Look for missing behavioral continuity

Test whether the current simulation can support this basic requirement:

> Two entities with similar objective circumstances but different histories or persistent internal state should be able to make meaningfully different choices for understandable causal reasons.

Example:

```text
Entity A:
high trust toward faction X
history of support from X
low risk tolerance

Entity B:
resentment toward X
previous betrayal by X
high ambition

Same offer arrives.
```

Can the system plausibly produce different decisions because of those differences?

If not, identify what part of the causal model is missing.

---

# 11. Look for development beyond combat progression

Audit whether long-term entity development is disproportionately centered on combat/skills.

Check support for trajectories such as:

```text
novice merchant
→ successful trader
→ guild member
→ wealthy patron
→ political influence
```

```text
ordinary villager
→ religious follower
→ respected priest
→ regional religious authority
```

```text
minor noble
→ marriage alliance
→ territorial influence
→ political faction leader
```

```text
craft apprentice
→ master craftsman
→ famous workshop
→ historical artifact creator
```

```text
criminal
→ gang member
→ gang leader
→ local power
```

The requirement is not that all trajectories already exist.

Determine what the current rules/mechanisms allow, partially allow, or cannot currently express.

---

# 12. Investigate opportunity generation

Character development requires things to react to.

Determine where opportunities come from:

* world conditions,
* organizations,
* markets,
* relationships,
* quests,
* threats,
* shortages,
* wars,
* geography,
* reputation,
* skill level,
* random generation,
* scripted content.

Determine whether opportunity availability itself can be causally affected by an entity's history.

Example:

```text
high reputation with merchant guild
→ higher-value caravan contracts become available
```

rather than:

```text
level 10
→ arbitrary higher-tier quest unlocked
```

Both may exist; identify actual semantics.

---

# 13. Investigate choice → identity feedback

Check whether repeated actions can gradually produce durable identity without requiring preassigned identity.

Example:

```text
repeated monster hunting
→ capability
→ known history
→ reputation
→ contracts
→ stronger monsters
→ "monster hunter" becomes socially meaningful
```

Potentially:

```text
behavior
→ history
→ recognition
→ identity
→ opportunity
→ more behavior
```

Determine whether current World Rules and implementation support this loop.

This is closely related to the existing lived-history/significance direction.

---

# 14. Investigate failure, setbacks, and negative development

Progression must not mean only improvement.

Find whether entities can accumulate:

* permanent injuries,
* lost skills/capability,
* debt,
* ruined reputation,
* broken relationships,
* trauma/fear,
* loss of rank,
* organizational expulsion,
* poverty,
* failed ambitions,
* dependency,
* corruption,
* social isolation.

Determine whether these consequences actually alter future choices/opportunities.

---

# 15. Investigate entity-specific versus general rules

For every discovered concept, ask:

> Is this genuinely an entity-development semantic, or is it already naturally explained by another domain?

Avoid inventing a giant `Character Development` domain if existing domains already own the truth.

Preserve:

```text
Semantic Home
≠ State Ownership
≠ Participating Domains
```

For example:

* wealth belongs to economy,
* reputation may belong to information/social,
* injury belongs to life/body,
* skill belongs to capability,
* relationship belongs to social,
* organization rank belongs to organization,
* belief belongs to cognition/knowledge.

A person's life trajectory is likely a **cross-domain causal composition**, not a single new owner.

---

# 16. Evaluate the World Rule Catalog

After reconstructing the current architecture, classify findings into:

### Already covered adequately

World Rules already define the needed semantics.

### Covered but realization incomplete

The target semantic exists but repo mechanisms/code do not fully realize it.

### Semantically ambiguous

Current Rules allow multiple interpretations and do not clearly define expected behavior.

### Genuine World Rule gap

A causal capability needed for coherent autonomous entity development is absent from the target world model.

### Derived/narrative concern only

Useful for story generation or analysis but should not modify World Rules.

Do not turn every useful storytelling concept into a World Rule.

---

# 17. Pay special attention to these possible semantic gaps

Investigate rather than assume:

### Persistent behavioral disposition

Does an entity carry stable tendencies across situations?

### Value / preference formation

Can preferences be innate, culturally influenced, learned, or changed?

### Goal formation

Can entities generate goals from their own circumstances rather than only receive tasks?

### Goal persistence

Can goals survive across ticks/events until fulfilled, abandoned, or replaced?

### Goal conflict

Can an entity choose between competing objectives?

### History-conditioned behavior

Can past outcomes alter later decision-making?

### Relationship-conditioned behavior

Can the same opportunity produce different choices depending on who is involved?

### Opportunity-conditioned development

Can entities grow into paths created by circumstances rather than predefined classes?

### Role transition

Can a person's social/economic/organizational role change through history?

### Behavioral drift

Can an entity genuinely become different over decades?

### Self-reinforcing trajectory

Can:

```text
choice
→ experience
→ capability/reputation/network
→ new opportunity
→ further choice
```

happen naturally?

### Counterforces

Can trajectories stall, reverse, or collapse?

---

# 18. Consider biography / Life Chronicle as a validation lens

Do not implement a story generator.

Use this only as an architecture test.

Imagine generating a first-person life chronicle such as:

```text
Age 18:
left home with merchant caravan.

Age 20:
started accepting independent contracts.

Age 22:
formed recurring partnership with a mage.

Age 25:
became recognized regional swordsman.

Age 31:
failed a major hunt, survived, changed tactics.

Age 36:
reputation led to political recruitment.

Age 42:
founded a mercenary company.

Age 51:
lost company during war.

Age 58:
became teacher.

Age 70:
returned home.
```

For each meaningful life event, ask:

> Could the current simulation explain why this happened through actual causal state and mechanisms?

We should be able to answer:

* why this entity chose it,
* why the opportunity existed,
* why they succeeded or failed,
* what changed afterward,
* why later opportunities differed,
* how relationships affected it,
* how capability evolved,
* how reputation propagated,
* how the world reacted.

If the answer would require an author simply deciding that “this is the next chapter,” note the missing simulation capability.

---

# 19. Do not require deterministic explainability

The target is not:

```text
given state X
→ action Y must happen
```

Randomness, incomplete information, competing motives, and stochastic outcomes are valid.

The requirement is closer to:

> Important choices and long-term trajectories should have plausible causal support from the simulated entity and world state.

---

# 20. Distinguish actor truth from observer interpretation

For concepts such as:

```text
brave
cowardly
heroic
greedy
loyal
wanderer
leader
villain
```

identify whether they are:

* internal dispositions,
* behavioral observations,
* social judgments,
* cultural labels,
* narrator interpretations.

Do not silently collapse these.

Example:

```text
high risk tolerance
```

may be actual internal state.

```text
"brave"
```

may be somebody's interpretation of repeated risky behavior.

```text
"hero"
```

may be a socially propagated reputation.

```text
Hero Archetype
```

may only be a narrative abstraction.

These can coexist without being the same fact.

---

# 21. Return an entity-development causal map

Produce a concise map similar to:

```text
BIOLOGY / BODY
       ↓
DISPOSITIONS / NEEDS / VALUES
       ↓
KNOWLEDGE + BELIEFS + MEMORY
       ↓
GOALS / MOTIVATIONS
       ↓
RELATIONSHIPS + SOCIAL POSITION
       ↓
AVAILABLE OPPORTUNITIES
       ↓
DECISION
       ↓
ACTION
       ↓
WORLD CONSEQUENCE
       ↓
HISTORY / EXPERIENCE
       ↓
CAPABILITY / RELATIONSHIP / REPUTATION / RESOURCE CHANGE
       ↓
NEW OPPORTUNITIES + CHANGED FUTURE DECISIONS
```

But replace this conceptual sketch with the architecture actually found in the repo.

Identify missing or weak edges.

---

# 22. Required reply format

Return one investigation report.

Do not make changes yet.

Structure the response approximately as:

## A. Executive finding

In a few paragraphs:

* how entity decision/development currently works,
* whether personality/traits/archetypes already participate,
* biggest strengths,
* biggest structural gaps.

## B. Existing concept inventory

For each significant concept:

```text
Concept
Semantic owner
Stored/derived
Causal/non-causal
Main consumers
Mutable?
Runtime evidence
World Rule coverage
```

## C. Decision pipeline

Actual repo-grounded causal flow.

## D. Development / life-trajectory pipeline

How entities currently change over time.

## E. Personality / Characteristic / Archetype findings

Detailed treatment of these specifically.

## F. Other important factors discovered

Especially factors we did not explicitly ask about.

## G. Broken or unproven causal edges

Examples:

```text
state exists → no consumer
history exists → no behavioral feedback
relationship exists → decision ignores it
progression exists → no opportunity effect
```

## H. World Rule assessment

Separate:

* already covered,
* implementation gap,
* ambiguous,
* genuine semantic gap,
* narrative/derived only.

## I. Life-Chronicle stress test

Choose 2–3 plausible entity trajectories and show whether the current architecture could causally generate them.

At least one should **not** be combat-centered.

## J. Recommendations

Recommend only architectural directions, ordered by importance.

Do not propose implementation detail unless needed to explain a gap.

Explicitly state whether you recommend:

* no World Rule change,
* refinement of existing Rules,
* new Rule(s),
* new derived semantic layer,
* implementation/mechanism work only,
* or further investigation.

---

# 23. Important constraints

Do not:

* assume Personality is missing because it was not highlighted in previous reviews,
* assume Archetype belongs outside simulation without checking existing architecture,
* turn every descriptive label into authoritative state,
* add a new domain simply to group character-development concepts,
* treat combat progression as the whole of development,
* use story structure as simulation truth,
* equate stored state with functioning causal state,
* equate source presence with runtime effect,
* equate `UNKNOWN` with `MISSING`,
* rewrite World Rules during this investigation.

Do:

* verify actual repo semantics,
* trace consumers,
* trace feedback loops,
* distinguish world truth / actor belief / social belief / derived interpretation,
* distinguish immediate decision-making from long-term development,
* look for multi-domain causal composition,
* report uncertainty explicitly.

---

# Governing question

The investigation should ultimately allow us to answer:

> **Does the current simulation contain enough causal machinery for an ordinary entity to begin with some body, history, disposition, knowledge, relationships, and circumstances; make locally understandable choices; gain and lose capabilities, resources, relationships and reputation; encounter different opportunities because of those changes; gradually become a substantially different person; and eventually accumulate a unique life trajectory without an author having to prescribe that trajectory in advance?**

Personality, characteristics, and archetypes are evidence toward that answer.

They are not the answer by themselves.
