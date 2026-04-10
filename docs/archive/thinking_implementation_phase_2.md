[Phase 2] - Strategic Appraisal and Project Selection

[Phase Description]
Phase 2 adds the missing decision layer between perception/appraisal and tactical state selection. The design doc is clear that the current engine already has a per-tick cognitive pipeline and useful local goal scoring, but it is still mostly immediate and tactical. What is missing is a persistent strategic layer that owns directives, projects, objectives, concerns, and interruptions, while the tactical stratum stays narrow and handles only immediate execution such as movement, attack, rest, sleep, loot, and flee.

The current `AIBrain` already has the right seam for this. It runs a phased pipeline: sensory perception, memory appraisal, tactical deliberation, and finalization. It also already tracks tactical continuity fields such as `last_goal`, `goal_scores`, `goal_committed_at`, boredom multipliers, social utility biases, and goal locking. That means Phase 2 is not a rewrite of the AI stack. It is an insertion of a strategic pass above `_deliberation_tactical_phase`, so project continuity and interruption logic can govern what the tactical layer is even allowed to consider.

[Phase technical implementation]
Add a strategic appraisal pass to `AIBrain` that reads `mind.strategic`, identity-linked motives, social context, beliefs, memory, attachments, and current world pressure, then does five things:

1. refresh or maintain the current strategic commitment
2. surface the active decision slice
3. decide whether to keep, suspend, replace, or spawn a project
4. derive one current strategic objective from the chosen project
5. constrain tactical goal evaluation and state selection based on that objective

This should be implemented as new strategy-oriented services, not embedded as ad hoc branching inside every tactical state handler. `AIContext` should be extended to carry strategic context, and `AIBrain.decide()` should emit typed strategic updates rather than mutating live strategic state. Tactical state handlers should remain downstream execution mechanisms.

[Phase important notes]
The most important rule is persistence. The design explicitly says entities should have meaningful unfinished business and projects should not be abandoned casually. If Phase 2 still recomputes life direction from scratch every tick, then the strategic layer becomes decorative and the engine stays a reactive state machine.

The second rule is bounded cognition. The design’s “active decision slice” exists to prevent combinatorial garbage. Strategic appraisal must narrow consideration based on urgency, salience, ongoing commitments, proximity, blockers, opportunities, and social expectations, rather than letting every possible directive and project compete every tick.

The third rule is separation of layers. Tactical utility AI still matters, but only after strategy has chosen what the entity is currently trying to do. Tactical selection should answer “how do I act now,” not “what life thread matters.”

[Phase acceptance criteria]
At the end of Phase 2, an entity can maintain or replace a current project across ticks, derive a current objective from that project, suspend work when a stronger concern interrupts it, and route tactical goal selection through that strategic commitment rather than treating all tactical goals as equally eligible every tick. The resulting decisions still run through the existing worker/snapshot/proposal pipeline and do not introduce direct AI-side mutation.

## Task

[x] (checkbox) - [Task 1] - Extend `AIContext` to expose strategic cognition inputs

[Task Description]
The current `AIContext` is already the shared read-only decision surface for the AI pipeline. Phase 2 needs that context to include strategic data so the brain can reason over commitments, concerns, blockers, leads, attachments, and interruption pressure in one place instead of pulling pieces from scattered fields. Right now the brain already builds context from actor, snapshot, config, RNG, faction registry, and visible entities. Strategic context needs to become equally first-class.

[Task technical implementation]
Extend `AIContext` with strategic-facing properties or cached selectors such as:

- active directives
- active projects
- suspended projects
- open concerns
- current blockers
- open leads
- obligations/contracts
- current strategic commitment
- place-attachment summary
- recent salient memory summary
- currently relevant social support surface

Do not stuff all of this into raw fields if it makes context noisy. Prefer computed properties over duplicating data. For example:

- `ctx.current_project`
- `ctx.current_objective`
- `ctx.active_concerns`
- `ctx.relevant_projects`
- `ctx.recent_salient_events`
- `ctx.attachment_pressure`
- `ctx.available_support_candidates`

This task is purely about access surface, not new reasoning yet.

[Task possible affected files]

- `src/ai/states/base.py` or wherever `AIContext` is defined
- `src/ai/brain.py`
- `src/core/aspects/mind.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not let `AIContext` become a second state store. It should remain a read-only decision surface derived from snapshot actor state and world state. Any strategic mutation still belongs in typed updates and authoritative application.

Also, avoid deep eager computation for everything. The active decision slice exists precisely because most possibilities should stay latent. Context should make relevant data accessible, not pre-expand the whole strategic space.

[Task check list]

- [x] Add strategic accessors to `AIContext`
- [x] Expose current project/objective references
- [x] Expose concern/lead/blocker summaries
- [x] Expose recent salient narrative pressure inputs
- [x] Expose place-attachment and social-support views
- [x] Keep the context read-only and lightweight

[Task acceptance criteria]
`AIBrain` can read all strategic inputs needed for appraisal from `AIContext` without reaching into unrelated systems or introducing direct state mutation.

---

[x] (checkbox) - [Task 2] - Add a strategic evaluator service above `GoalEvaluator`

[Task Description]
The existing `GoalEvaluator` is built for tactical goal scoring. That is useful, but insufficient. Phase 2 needs a new evaluator that reasons over directives, projects, objectives, concerns, interruptions, and persistence before tactical goal scoring starts. The design explicitly says life direction should follow the sequence `identity -> directives -> projects -> objectives -> local action`, not `raw utility score -> action`.

[Task technical implementation]
Create a new service, likely `src/ai/strategy/strategic_evaluator.py`, with responsibilities such as:

- scoring project continuation vs project switching
- scoring concern preemption
- selecting a primary project
- deriving a current objective
- optionally generating a small ranked set of candidate strategic commitments

Inputs should include:

- directives
- project properties such as urgency, emotional charge, persistence, reversibility, and recovery behavior
- concern pressure
- attachment relevance
- recent life-event resonance
- belief confidence and uncertainty
- obligations/contracts
- social feasibility
- current blocker state

Outputs should not directly be tactical AI states. They should be something like:

- `StrategicDecision`
- `selected_project_id`
- `selected_objective_id`
- `interruption_reason`
- `confidence`
- `candidate_projects_ranked`

This service must be deterministic given the snapshot and RNG inputs.

[Task possible affected files]

- `src/ai/strategy/strategic_evaluator.py`
- `src/ai/brain.py`
- `src/core/models/strategy.py`
- maybe `src/ai/goals/__init__.py` or registry files if shared interfaces are used

[Task important notes]
Do not subclass or overload `GoalEvaluator` into a two-headed mess. Tactical goal scoring and strategic project selection are different jobs. Merging them guarantees flattening everything back into temporary score nudges, which the design explicitly warns against.

Also, this evaluator should rank a small number of candidates, not every project/objective in the universe. That is the whole point of bounded strategic cognition.

[Task check list]

- [x] Create a dedicated strategic evaluator service
- [x] Define deterministic input/output models
- [x] Score continuation, switching, and interruption separately
- [x] Include directives, projects, concerns, blockers, attachments, and obligations in scoring
- [x] Keep tactical goal scoring out of this service
- [x] Bound candidate evaluation to a small slice

[Task acceptance criteria]
A deterministic strategic evaluator exists and can choose or rank current strategic commitments without collapsing them into direct tactical goal scores.

---

[x] (checkbox) - [Task 3] - Implement strategic commitment and continuity rules

[Task Description]
This is the anti-thrashing task. The design states that projects should not be abandoned casually and unfinished business should persist. The current tactical layer already has a primitive continuity concept through `goal_committed_at`, boredom, and goal locks, but that is still tactical continuity, not life-direction continuity. Phase 2 must move commitment up to the project/objective level.

[Task technical implementation]
Add commitment rules to strategic evaluation and strategic state, for example:

- `current_project_id`
- `current_objective_id`
- `project_committed_at`
- `project_lock_reason`
- `project_lock_until`
- `interruption_policy`
- `resume_priority`
- `abandonment_cost`

The evaluator should prefer continuing the current project when:

- it is still valid
- blockers are not terminal
- no stronger concern or obligation preempts it
- the project’s persistence is high
- abandonment cost is non-trivial

It should switch only when:

- a concern outranks it
- an obligation preempts it
- the current project becomes invalid or blocked in a way that requires suspension
- the entity reaches a completion or project handoff condition

This should emit `StrategicUpdate`s that set or change current commitment references rather than mutating live state inside the evaluator.

[Task possible affected files]

- `src/ai/strategy/strategic_evaluator.py`
- `src/ai/brain.py`
- `src/core/models/strategy.py`
- `src/actions/base.py`

[Task important notes]
Do not blindly reuse tactical “goal lock” semantics. Tactical locks exist to avoid short-term action jitter. Strategic commitment is heavier: it needs interruption rules, suspension logic, and resumption semantics. These are not the same thing.

Also, a suspended project is not a failed project. The design explicitly treats suspension and unfinished business as core story structure.

[Task check list]

- [x] Add current project/objective commitment fields
- [x] Add project continuity and abandonment cost rules
- [x] Add suspension/resumption semantics
- [x] Emit commitment changes through strategic updates
- [x] Prevent per-tick commitment thrash
- [x] Separate tactical locks from strategic commitment

[Task acceptance criteria]
Entities can keep pursuing the same project across multiple ticks, suspend it when interrupted, and later resume it without recomputing life direction from zero.

---

[x] (checkbox) - [Task 4] - Implement active decision slice filtering

[Task Description]
The design explicitly says the active decision slice is the narrow, currently relevant part of the subjective affordance graph. Without it, cognition becomes combinatorial garbage. This task ensures Phase 2 does not turn into evaluating every directive, project, concern, and lead every tick.

[Task technical implementation]
Introduce a preselection layer that narrows strategic candidates before scoring them. Candidate selection should consider:

- current commitment
- urgent concerns
- high-salience recent events
- nearby or directly relevant leads
- currently actionable objectives
- obligations with deadlines or social cost
- projects whose blockers just changed
- attached-place threats
- social opportunities that match current blockers

This can be implemented as a `StrategicCandidateBuilder` service that returns a bounded set of candidate projects/objectives/concerns for evaluation. For example:

- always include current project
- include top N urgent concerns
- include top N projects with changed pressure
- include top N obligations
- include top N newly actionable objectives

This builder should run before the strategic evaluator.

[Task possible affected files]

- `src/ai/strategy/candidate_builder.py`
- `src/ai/brain.py`
- `src/ai/strategy/strategic_evaluator.py`

[Task important notes]
Do not let this become a hidden evaluator. Its job is filtering, not deciding. Keep the heuristics simple and deterministic.

Also, always include the current project unless it is invalid. Otherwise continuity gets destroyed by the filter before the evaluator can defend it.

[Task check list]

- [x] Add candidate-builder or filtering stage
- [x] Bound candidate count deterministically
- [x] Always consider current commitment when valid
- [x] Surface urgent concerns and obligations
- [x] Surface newly actionable objectives and changed blockers
- [x] Keep filtering separate from ranking

[Task acceptance criteria]
Strategic evaluation works on a small bounded candidate set driven by salience, urgency, and continuity rather than the full latent possibility graph.

---

[x] (checkbox) - [Task 5] - Add project-to-objective derivation logic

[Task Description]
Projects are not directly executable. The design says a project is a medium-to-long-term pursuit and an objective is the actionable subproblem inside it. Phase 2 needs a way to derive one current objective from the chosen project, otherwise the tactical layer will still have no bridge from strategic intent to executable behavior.

[Task technical implementation]
Create an `ObjectiveDerivationService` that maps project state to one current objective. Examples of objective classes the design already defines:

- informational objectives
- capability objectives
- access objectives
- social objectives
- defensive objectives
- retributive objectives
- maintenance objectives

The derivation service should:

- inspect current blockers and project stage
- inspect known leads and confidence
- inspect obligations and social requirements
- choose the next objective type
- either activate an existing objective record or spawn/update a new objective record via `StrategicUpdate`

This should not yet generate precise movement targets or actions. It should produce structured objectives like:

- consult class authority
- gather rumor
- scout candidate region
- return home
- recruit ally
- gain trust
- train strength
- acquire material
- defend attached location

That objective then becomes the input to tactical translation.

[Task possible affected files]

- `src/ai/strategy/objective_derivation.py`
- `src/ai/brain.py`
- `src/core/models/strategy.py`
- `src/actions/base.py`

[Task important notes]
Do not skip this layer and map projects directly to AI states. That would collapse the entire strategic hierarchy and recreate the current problem under new names.

Also, objective derivation should be resumable. If a project is suspended and resumed later, objective history should still make sense.

[Task check list]

- [x] Add objective derivation service
- [x] Support objective classes from the design
- [x] Derive objectives based on blockers, stage, leads, obligations, and feasibility
- [x] Emit objective creation/activation as strategic updates
- [x] Keep objectives abstract enough to survive interruption
- [x] Avoid direct action generation at this layer

[Task acceptance criteria]
Given a selected project, the engine can derive a structured current objective that is concrete enough to guide tactics but abstract enough to persist across interruptions.

---

[x] (checkbox) - [Task 6] - Translate strategic objectives into tactical goal constraints

[Task Description]
This task is the actual bridge from strategy to the existing tactical system. The engine already has tactical goals, tactical state handlers, and a `GoalEvaluator`. Phase 2 should not replace them. It should constrain them so tactics serve the selected objective instead of free-floating local utility.

[Task technical implementation]
Add a translation layer, likely `src/ai/strategy/objective_to_goal_mapper.py`, that maps objective classes to tactical goal affordances and weights. For example:

- `consult_class_authority` biases travel/social/building-visit goals toward class hall interaction
- `gather_rumor` biases guild/inn/social/information-seeking behavior
- `return_home` heavily biases defensive/homeward travel
- `train_strength` biases training-capable routines or facilities
- `recruit_ally` biases social contact with suitable candidates
- `defend_attached_location` biases return/guard/combat near target area

This mapping should not hard-force exact actions unless the project is in a hard-commitment state. Prefer constrained tactical search:

- allowed goals
- disallowed goals
- goal weight multipliers
- required world anchors
- preferred destinations/entities
- fallback tactical behaviors if blocked

It can be stored in `AIContext` as a transient “tactical directive surface” derived from the current objective. Then `GoalEvaluator.evaluate(ctx)` uses that surface during scoring.

[Task possible affected files]

- `src/ai/strategy/objective_to_goal_mapper.py`
- `src/ai/goals/...` evaluators
- `src/ai/brain.py`
- `src/ai/states/base.py`

[Task important notes]
Do not hardcode every objective into every state handler. That guarantees explosion. The translation layer should bias tactical selection centrally.

Also, do not let tactical boredom or local temptation easily override current objective without going back through the strategic interruption rules.

[Task check list]

- [x] Add objective-to-goal translation layer
- [x] Produce tactical constraints rather than direct actions
- [x] Integrate translation surface into goal evaluation
- [x] Allow objective-specific preferred anchors/targets
- [x] Preserve tactical fallback behavior when partially blocked
- [x] Prevent tactical drift from casually breaking strategy

[Task acceptance criteria]
When an objective is active, tactical goal scoring clearly favors actions that advance that objective, without eliminating the existing tactical AI architecture.

---

[x] (checkbox) - [Task 7] - Implement interruption and reprioritization logic

[Task Description]
This is the branch engine for Phase 2. The design explicitly rejects the amateur pattern of “event happens, utility plus five.” Reprioritization must compare directive alignment, emotional charge, urgency, irreversibility, social cost of inaction, likelihood of success, current project stage, memory resonance, and attachment relevance. Concerns are the mechanism that inject pressure without automatically becoming projects.

[Task technical implementation]
Create a `StrategicInterruptionService` that:

- evaluates whether a concern or obligation should preempt the current project
- determines whether preemption means suspend, mutate, or abandon
- computes interruption reason and recovery mode
- optionally spawns a new project from a concern if the concern crosses a threshold

Inputs should include:

- current project persistence
- concern urgency and irreversibility
- place attachment relevance
- obligation binding strength
- social consequences of delay
- proximity/travel feasibility
- recent salient memories and turning points
- current blocker landscape

This service should return structured interruption decisions that become `StrategicUpdate`s. For example:

- suspend `project_A`
- activate `concern_defend_town`
- derive objective `return_home`
- mark recovery mode as `resume_after_concern`

The existing tactical AI should then respond through the new objective mapping.

[Task possible affected files]

- `src/ai/strategy/interruption.py`
- `src/ai/brain.py`
- `src/core/models/strategy.py`
- `src/actions/base.py`

[Task important notes]
Do not let every concern become a new project immediately. The design is explicit: a concern is pressure seeking response, not automatically a project. That distinction matters because concerns are what create branching and interruption pressure.

Also, interruption should be filtered by identity and attachment. Otherwise every entity responds to world events the same way, which the design specifically rejects.

[Task check list]

- [x] Add interruption evaluation service
- [x] Compare concern pressure against current project continuity
- [x] Support suspend, mutate, abandon, and continue decisions
- [x] Include attachment, obligation, and social cost in reprioritization
- [x] Emit structured interruption updates
- [x] Keep concern and project semantics distinct

[Task acceptance criteria]
A high-pressure concern or obligation can interrupt the current project in a structured, explainable way, while lower-pressure noise does not cause life-direction thrashing.

---

[x] (checkbox) - [Task 8] - Persist strategic reasoning outputs through typed updates

[Task Description]
Phase 2 introduces actual reasoning outputs: current commitment, objective selection, suspension state, interruption reasons, and possibly newly spawned objectives or concerns. These outputs must be persisted through the same typed-update path established in Phase 1. Otherwise strategic reasoning remains ephemeral and the next tick starts blind again.

[Task technical implementation]
Extend `AIBrain.decide()` so the new strategic pass appends `StrategicUpdate` records before or alongside the existing `MindUpdate`, `PerceptionUpdate`, and `NavigationUpdate` list. These updates should capture:

- current project selection
- current objective selection
- project status transition
- concern activation/resolution
- suspension/resumption metadata
- optionally project/objective driver details for inspection

Then ensure the final `ActionProposal` includes these updates so authoritative application writes them back to `mind.strategic`. Tactical AI state changes still happen through the normal proposal/new state path.

[Task possible affected files]

- `src/ai/brain.py`
- `src/actions/base.py`
- `src/systems/gameplay/action_system.py`
- `src/core/models/strategy.py`

[Task important notes]
Do not allow Phase 2 reasoning to live only inside local variables or transient proposal metadata. The whole value of strategic cognition is persistence.

Also, keep the outputs structured enough that later inspection can explain why a project was selected or suspended.

[Task check list]

- [x] Append strategic updates from `AIBrain`
- [x] Persist commitment and interruption results
- [x] Route updates through existing proposal pipeline
- [x] Keep tactical state transition separate from strategic state updates
- [x] Include inspection-friendly reasoning fields where justified

[Task acceptance criteria]
Strategic reasoning results survive the tick boundary and are written back to entity state through authoritative updates, allowing the next tick to build on prior strategic commitments.

---

[x] (checkbox) - [Task 9] - Add observability for strategic choice and tactical translation

[Task Description]
Phase 2 is where the system can start lying to you. It may look alive while actually just generating arbitrary switches. You need explicit visibility into which project was chosen, why it beat alternatives, what objective it derived, and how that objective constrained tactical scoring. The current code already has decision drivers, last-goal tracking, and inspection surfaces for narrative and reputation; Phase 2 needs similar visibility for strategy.

[Task technical implementation]
Add structured debug/inspection fields such as:

- strategic candidate list with scores
- selected project and objective IDs
- interruption reason
- top reprioritization drivers
- objective-to-goal constraints
- why the final tactical state was considered aligned

These should be recorded in a compact structured form, likely through strategic driver records analogous to existing `DecisionDriver` usage. Extend inspector and any API debug views to display:

- current project
- current objective
- shortlisted alternatives
- interruption history for the current tick
- tactical goals allowed/boosted/suppressed by current objective

This is not fluff. It is how you verify the strategic layer is governing tactics instead of being bypassed.

[Task possible affected files]

- `src/ai/brain.py`
- `src/core/models/strategy.py`
- `src/ui/cli/inspector.py`
- API debug/inspection modules

[Task important notes]
Do not dump raw evaluator internals. Show the decision surface that matters. Too much debug noise becomes useless.

Also, keep this structured. Decorative prose explanations are less useful than clean machine-readable drivers while the system is still stabilizing.

[Task check list]

- [x] Add strategic decision-driver records
- [x] Record selected project/objective and top alternatives
- [x] Record interruption causes
- [x] Record tactical constraint mapping
- [x] Render this in inspector/debug views
- [x] Keep output compact and structured

[Task acceptance criteria]
You can inspect one tick of AI reasoning and clearly see which strategic commitment was active, why it won, what objective it produced, and how that changed tactical goal selection.

---

[x] (checkbox) - [Task 10] - Add regression tests for continuity, interruption, and tactical alignment

[Task Description]
Phase 2 introduces behavior, so the tests now need to prove continuity and non-thrashing. Without tests, the strategic layer will silently collapse back into tactical oscillation or get bypassed by direct tactical scoring. The design’s coherence rules explicitly require unfinished business, persistence, and filtered interruption.

[Task technical implementation]
Add tests that cover:

- current project persists across multiple ticks when valid
- urgent concern interrupts current project when thresholds are met
- lower-priority noise does not interrupt
- objective derivation produces the right objective class for a chosen project
- objective-to-goal mapping biases tactical selection appropriately
- current project is always considered by the active decision slice
- suspended project resumes when concern clears
- deterministic ranking and interruption behavior under fixed snapshot and RNG

Use minimal fixtures around `AIBrain`, `AIContext`, and strategic state, not full simulation runs unless needed for one or two smoke tests. The current engine already depends on deterministic order in scheduling and snapshot-based worker decision, so these tests should protect that property.

[Task possible affected files]

- `tests/ai/test_strategic_evaluator.py`
- `tests/ai/test_project_continuity.py`
- `tests/ai/test_interruption_logic.py`
- `tests/ai/test_objective_to_goal_mapping.py`
- `tests/ai/test_active_decision_slice.py`

[Task important notes]
Do not rely on subjective “looks better” simulation runs. This phase needs hard behavior invariants.

Also, test negative cases aggressively. The main failure mode is not obvious breakage; it is the silent reintroduction of tactical drift and per-tick project churn.

[Task check list]

- [x] Add continuity tests
- [x] Add interruption threshold tests
- [x] Add active-slice filtering tests
- [x] Add objective derivation tests
- [x] Add tactical alignment tests
- [x] Add deterministic repeatability tests
- [x] Add suspension/resumption tests

[Task acceptance criteria]
Automated tests prove that strategic commitment persists, interruption is selective, objective derivation is stable, and tactical behavior stays aligned with current strategic intent under deterministic inputs.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of Phase 2 as “smarter goal scoring.” It is not. It is a governance layer over goal scoring. The design is explicit that the current tactical layer is already useful but insufficient, and that continuity lives in projects, objectives, concerns, and interruption logic above the tactical stratum.

What actions must be taken immediately
Do Tasks 1 through 4 first. That creates the strategic decision surface, evaluator, continuity rules, and active-slice filter. Then do Tasks 5 through 8 to connect projects to objectives, objectives to tactics, and reasoning outputs to persistence. Finish with Tasks 9 and 10 so you can actually verify the layer is doing real work.

What must stop or be eliminated
Stop letting tactical `GoalEvaluator` act as the top-level brain. Stop using `last_goal` and boredom as a substitute for durable commitment. Stop letting every event act as a flat score bump. Stop allowing tactical temptations to bypass strategic commitments without going through explicit interruption logic.

The consequences and opportunity cost if this fails
You will have a strategic schema from Phase 1 sitting in memory, but the actual decision loop will still be driven by per-tick tactical utility. That means the feature will look architecturally complete while behavior remains hollow. That is the worst kind of failure because it wastes time and hides the real gap.
