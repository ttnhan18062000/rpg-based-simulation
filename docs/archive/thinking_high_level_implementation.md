I reviewed both the design memo and the codebase. The blunt truth is that the engine already has a strong tactical substrate: `MindAspect` is split into decision, perception, emotion, navigation, narrative, routine, and social domains; beliefs already carry freshness, confidence, directness, and source quality; turning points, interpreted life events, reputation, place attachment, groups, gossip, immutable snapshots, and authoritative action application already exist. The missing piece is exactly what the design doc says: a persistent **strategic layer** that survives interruptions and converts memory, uncertainty, and social consequence into durable projects rather than just better next-tick choices.

The design doc is also right about what not to do: this should not become authored quest trees or a pile of extra shallow goals. The target is a life-direction system built from directives, projects, objectives, concerns, leads, blockers, obligations, and social contracts, with the tactical AI remaining narrow and subordinate.

## Phase 1 Stage 1-6 — Strategic domain as a first-class state model

**Description**
Introduce a dedicated strategic layer into entity mind/state so the engine has somewhere to store unfinished business, instead of trying to smuggle long-term intent through `goal_scores`, `last_goal`, mood, or ad hoc memory tags. Right now the code has the right lower layers, but no durable container for directives, projects, concerns, leads, blockers, obligations, or contracts.

**Technical implement (high-level)**
Create new typed models, ideally under something like `src/core/models/strategy.py`, then add a `strategic` field to `MindAspect`. At minimum, define:

- `DirectiveRecord`
- `ProjectRecord`
- `ObjectiveRecord`
- `ConcernRecord`
- `LeadRecord`
- `BlockerRecord`
- `ObligationRecord`
- `SocialContractRecord`

These should be typed, compact, and serializable like the rest of the simulation models, not free-form prose. Then add matching typed updates, for example `StrategicUpdate`, so worker AI can propose strategic changes and the authoritative `ActionSystem` can apply them through the same deferred update pipeline already used for mind, perception, navigation, progression, social, and reputation updates. That keeps the existing snapshot/worker/resolution architecture intact instead of creating a second hidden mutation path.

**Important notes**
The source already has the right architecture for this: immutable snapshots are created per tick, workers decide against snapshots, and world mutation happens later in the authoritative application phase. Do not bypass that discipline by letting AI handlers mutate strategic state directly. Strategic state must behave like every other authoritative domain.

Also, keep the strategic records typed and sparse. The design memo explicitly warns against fake emergence and utility flattening. If you make projects into vague strings or stuff everything into memory logs, you will recreate the problem in a messier form.

**Acceptance criteria**
An entity can persist at least:

- a small set of enduring directives,
- one or more active or suspended projects,
- structured blockers and leads tied to those projects,
- obligations and contracts with other entities,
- and this state survives snapshotting, worker decision, replay, and authoritative application without direct mutation leaks.

## Phase 1 Stage 7 — Strategic appraisal and project selection

**Description**
Right now `AIBrain` already runs a clean pipeline: sensory perception, memory appraisal, deliberation, finalization. That is the correct insertion point. The missing layer is not another local state handler; it is a pre-tactical stage that converts identity, memory, attachments, social state, and uncertainty into an **active decision slice** and a current strategic commitment.

**Technical implement (high-level)**
Extend the brain pipeline with a strategic pass before tactical deliberation:

1. Read directives, active projects, suspended projects, concerns, obligations.
2. Score only a bounded active slice, not the whole latent possibility space.
3. Choose or maintain a primary project unless a stronger concern or obligation interrupts it.
4. Derive one current strategic objective from that project.
5. Only then translate that objective into existing tactical goals and AI states.

In practical terms, this likely means:

- adding a strategic evaluator service beside `GoalEvaluator`,
- extending `AIContext` to expose strategic state,
- storing “current project id / current objective id / interrupted project id” in mind decision or strategic state,
- and generating tactical proposals from project objectives rather than directly from flat utility competition.

**Important notes**
Do not let every tick completely rescore life direction from scratch. The design’s whole point is persistence: projects should not be abandoned casually, and entities should have meaningful unfinished business. The source already tracks `goal_committed_at` and similar fields; use that concept, but move commitment up to projects/objectives rather than only goals.

Also, the tactical layer should stay narrow. Movement, attack, rest, sleep, loot, visit-building, and flee are downstream execution machinery, not the place to own story continuity.

**Acceptance criteria**
For a multi-tick span, an entity can:

- keep pursuing the same project across interruptions,
- derive a current objective from that project,
- resume suspended work later,
- and explain the chosen tactical state in terms of project/objective continuity rather than only raw utility scores.

## Phase 1 Stage 8-11 — Strategic knowledge, leads, and blockers

**Description**
Your current belief system is entity-centric and already supports direct vs indirect knowledge, source confidence, and gossip propagation. That is a strong foundation, but it is still too narrow. The design explicitly requires beliefs about places, routes, materials, candidate regions, likely threats, trusted informants, and what other entities might know. Without that, you cannot get investigation, rumor chasing, or proper blocker detours.

**Technical implement (high-level)**
Do not overload `BeliefRecord` further. Add a separate strategic-knowledge model:

- `LeadRecord` for uncertain clues,
- `HypothesisRecord` or candidate-zone structures for vague locations,
- blocker types tied to projects/objectives,
- and a search-history structure that tracks tested leads and contradictions.

Then extend guild/class-hall/blacksmith/social interactions so they produce typed leads and blockers rather than only tactical effects or immediate hints. The source already has guild intel, material hints, class hall progression, blacksmith material logic, and gossip propagation; those should become first-class producers of strategic knowledge.

**Important notes**
The design memo is explicit here: vague leads must not collapse into coordinates. A lead should create a hypothesis set and a ranked search space, not a marker. If “far snow mountain” becomes an exact tile the moment it is heard, the whole knowledge system becomes fake.

Also, blockers must generate detours, not dead ends. “Too weak,” “location unknown,” “not enough allies,” and “trust too low” should spawn new objectives such as train, gather rumor, recruit help, or gain trust. That is the branch engine.

**Acceptance criteria**
An entity can:

- receive a vague clue,
- store it as a lead with uncertainty and source quality,
- convert it into candidate regions or next investigation steps,
- detect a blocker when progress fails,
- and spawn a detour objective instead of dropping the project or magically knowing the answer.

## Phase 1 Stage 12-14 — Social contracts and parties

**Description**
The code already has social bonds, reputation, group records, cohesion, and gossip. But the current group layer is still shallow: groups are formed from cluster/faction proximity, default to `EXPLORE`, and are maintained mostly as tactical cohesion structures. That is not enough for expedition parties, revenge pacts, escorts, or negotiated cooperation.

**Technical implement (high-level)**
Replace or extend `GroupRecord` with a strategic/social contract layer:

- party purpose,
- formation reason,
- expected roles,
- reward terms,
- fallback and dissolution conditions,
- ownership of loot/credit,
- and contract memory when terms are broken.

Then make recruitment a project/objective type. Recruitment should query social bonds, trust, debt, familiarity, public reputation, current obligations, and capability fit. Existing social registry and reputation already give you the raw ingredients; the missing piece is contract semantics and strategic use.

**Important notes**
Do not confuse “group exists” with “cooperation exists.” The design doc is blunt: group behavior as mere proximity is a dead end. The current group system proves the infrastructure exists, but it is still mostly formation/maintenance plumbing and even contains debug-style behavior. That means this phase should be treated as a semantic upgrade, not a minor tweak.

Also, promises must have cost. Breaking a contract must feed trust, debt, reputation, and future recruitment viability, or cooperation will remain cheap noise.

**Acceptance criteria**
An entity can:

- decide a project is not solo-viable,
- identify candidate allies based on trust/reputation/fit,
- create a party or contract with purpose and terms,
- coordinate around that shared objective,
- and produce persistent social consequences if members flee, betray, refuse payment, or succeed together.

## Phase 1 Stage 15-17 — Strategic reprioritization from life events

**Description**
This is where the system stops feeling like tactical AI with lore taped on top. The source already interprets combat into social life events, turning points, relationship deltas, and public reputation, and it already seeds routines and place attachments. The design requirement is to make those events causally strategic: they must create concerns, mutate directives, suspend projects, and change what the entity now considers worth doing.

**Technical implement (high-level)**
Add an event-to-strategy interpreter after life-event interpretation:

- turning points can strengthen, weaken, or create directives,
- threats to attached places can generate high-priority concerns,
- betrayal or rescue can alter contract willingness and ally selection,
- repeated failures can mutate project recovery behavior,
- public events can alter which future opportunities appear.

This should likely run in or adjacent to the authoritative post-action pipeline, because the source already interprets action outcomes into social events inside `ActionSystem`. Build on that rather than inventing a separate late-bound narrative processor.

**Important notes**
Do not reduce reprioritization to “event adds +5 utility.” The design explicitly rejects that. Reprioritization must weigh directive alignment, urgency, irreversibility, social cost, likelihood of success, project stage, memory resonance, and attachment relevance. Otherwise town raids, ally deaths, and betrayal will produce generic behavior instead of divergence.

Also, private narrative and public narrative must remain separate. The code already has both ingredients: turning points and reputation. The implementation must keep them distinct so “what I think this meant” and “what others think I am” can diverge and both matter.

**Acceptance criteria**
After a major event such as near death, ally death, betrayal, home damage, or public defense:

- a concern is generated,
- one or more projects are suspended, replaced, or reprioritized,
- directives or contract preferences can change,
- and later behavior clearly reflects that history instead of resetting to baseline.

## Phase 6 — Wire strategy cleanly into existing buildings, world systems, and observability

**Description**
The engine already has the world loop phases, snapshot creation, authoritative action application, guild/class hall/building interactions, and inspection tooling. The last phase is not “add content.” It is making the strategic system visible, queryable, and naturally fed by existing world systems instead of leaving it trapped inside AI internals.

**Technical implement (high-level)**
Integrate strategic producers and consumers:

- guild visits produce leads, rumors, and obligations,
- class hall visits produce capability blockers and breakthrough objectives,
- blacksmith/store/home/inn interactions produce maintenance and capability objectives,
- calamities, raids, regional danger, and local scars produce concerns,
- API/inspector output exposes directives, active projects, blockers, concerns, leads, and contracts in structured form.

The source already has regional consequence data, local scars, building semantics, and inspector views for turning points and public reputation. Extend those same explainability surfaces rather than inventing a parallel debug-only channel.

**Important notes**
Do not measure success by hidden model complexity. The design memo is clear: the feature feels alive only when an observer can describe entity lives in plain language. So observability is not optional polish; it is part of the design contract.

Also, keep the active project count low. The design explicitly warns against infinite combinatorics. The UI and debug output should make it obvious when an entity is carrying too much strategic state.

**Acceptance criteria**
From inspection or API output, you can see for a given entity:

- current directives,
- active/suspended projects,
- current objective,
- known leads and blockers,
- obligations/contracts,
- why reprioritization happened,
- and how recent turning points or place threats changed strategy.

## Recommended sequencing

The right order is:

1. strategic state model
2. strategic appraisal/project selection
3. uncertainty/leads/blockers
4. contracts/party formation
5. event-driven reprioritization
6. integration and observability

That order matches the codebase instead of fighting it. The engine already has strong phase boundaries, immutable snapshots, and authoritative update application, so the strategic layer should be added as another typed domain flowing through those boundaries, not as a special-case subsystem glued onto tactical AI.

Priority Plan

What must change in mindset or assumptions
Stop thinking in terms of “add smarter goals.” That is the wrong abstraction. The source already has enough tactical machinery. The real missing object is durable strategic state with typed continuity across ticks.

What actions must be taken immediately
Define the strategic schema first, then insert a strategic appraisal pass into `AIBrain`, then route strategic updates through the same authoritative `ActionSystem` pipeline the engine already trusts.

What must stop or be eliminated
Stop using tactical goals, prose memory, or group proximity as substitutes for long-term intent, social commitment, or investigation. Stop collapsing rumors into coordinates. Stop letting emotions remain temporary score nudges with no lasting strategic effect.

The consequence and opportunity cost if this is ignored
You will keep extending a reactive state machine that looks richer in code but still produces interchangeable lives. The world will get broader, but the agents will stay tactically busy and strategically hollow.

If you want, I can turn this into a concrete module-by-module implementation map next.
