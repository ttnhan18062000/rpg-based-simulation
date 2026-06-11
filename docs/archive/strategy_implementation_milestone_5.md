---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

Good. Milestone 5 is where the system stops having memory as decoration and starts having memory as causation.

Up to Milestone 4, you can have continuity, blockers, detours, and cooperation. That still is not enough. An entity can carry projects across ticks and recruit allies, but if near death, betrayal, ally loss, home damage, or public success do not materially change what it pursues next, then the system is still strategically hollow. Milestone 5 is the point where interpreted events become **strategic reprioritization**, not temporary flavor or utility noise. That is exactly what the design reference demands: events should generate concerns, mutate directives, suspend or replace projects, and change future judgment based on attachment, obligation, irreversibility, and emotional charge.

### Milestone 5 Implementation Comments
- **Strategic Interpretation**: Implemented a "watermarked" reflective phase in `AIBrain` where the `StrategicEventInterpreter` scans narrative memory for uninterpreted events. This ensures events discovered while the entity is away (e.g. "I returned and my house is burned") trigger strategic shifts.
- **Project Pivoting**: Projects now support "pivoting" (transformation) where an `EXPLORATION` project becomes `DEVELOPMENT` (repair/fortification) upon home damage.
- **Social Feedback**: Betrayal trauma is now persistent and affects future cooperation, bridging Milestone 4 (Recruitment) with Milestone 5 (Events).
- **Determinism**: Validated that `last_interpreted_event_tick` is authoritatively persisted in the `ActionSystem`, ensuring idempotent appraisal.

# Milestone 5 — Event-driven strategic reprioritization

## What this milestone actually delivers

At the end of Milestone 5, an entity should be able to:

- experience a major interpreted event
- convert that event into a strategic concern or project mutation
- reprioritize its life direction based on history, not just current utility
- react differently depending on identity, place attachment, obligations, and prior memory
- preserve causal continuity after success, failure, betrayal, loss, or threat

That is the milestone where the engine starts producing different **biographies**, not just different tactical traces.

What Milestone 5 still does **not** need:

- full literary story generation
- giant emotion simulation
- deep faction politics
- free-form personality rewriting every tick

This milestone is about strategic consequence, not narrative poetry.

---

## The real problem you are solving

The trap here is amateur design: an event happens, some score gets `+5`, mood dips a bit, and then the system goes back to baseline.

That is worthless.

The design notes explicitly reject shallow reprioritization. A town attack should not just add generic urgency. It should be evaluated through:

- attachment strength
- protector identity
- social cost of absence
- project reversibility
- travel feasibility
- memory resonance
- obligations and shame cost
- irreversibility of loss

Likewise, betrayal, ally death, public defense, or repeated failure should not be treated as the same kind of disturbance. They should create different strategic mutations.

---

## What must exist by the end of this milestone

You need five things.

### 1. Event-to-strategy interpretation

The engine already has interpreted life events, turning points, social consequences, and place attachments in the substrate described by the reference notes. Milestone 5 needs a dedicated layer that says:

- this event generates a concern
- this event strengthens or weakens a directive
- this event suspends or replaces a project
- this event changes willingness to contract, return home, seek revenge, or avoid risk

Without that explicit bridge, memory remains archival instead of causal.

### 2. Concern generation from major events

Certain events should create urgent concerns with clear provenance.

Examples:

- home damaged -> `defend_or_restore_home`
- ally died nearby -> `protect_group` or `avenge_loss`
- betrayal by ally -> `punish_betrayal` or `avoid_dependency`
- near death -> `recover_and_reassess`
- public defense success -> `capitalize_on_reputation` or `double_down_on_protector_role`

Concerns are not generic “important flags.” They are pressures that compete with or override current projects.

### 3. Directive mutation

Some events should alter enduring orientation, not just current focus.

Examples:

- repeated rescue of others strengthens protector identity
- repeated betrayal weakens trust-based cooperation
- catastrophic home loss shifts attachment and life direction
- public heroic success strengthens prestige- or duty-oriented directives

Do not mutate directives casually. This should happen only on events with enough interpreted weight or repetition.

### 4. Project suspension, replacement, or transformation

A major event should be able to:

- suspend current project
- replace it with a more urgent one
- transform it into a new related one
- mark old work as abandoned, delayed, or emotionally reinterpreted

Examples:

- exploration project suspended by town attack
- recruitment project transformed into rescue project after ally capture
- advancement project delayed after near-fatal failure
- resource-gathering project replaced by rebuild-home project

That is real branching.

### 5. Divergent responses to the same event

This is where the system becomes believable.

The same town raid should not affect everyone equally.
The same betrayal should not produce the same retaliation.
The same near-death moment should not shift every entity into identical caution.

Inputs must include:

- role / identity
- place attachment
- active obligations
- current project stage
- risk tolerance
- prior similar memories
- faction loyalty
- emotional interpretation
- reversibility of current mission

Without divergence, you still have a scripted response layer.

---

## The correct implementation order

### Step 1 — Write tests that forbid shallow reprioritization

Start with anti-fake tests.

Write failing tests that prove:

- home threat creates different concern levels for attached vs non-attached entities
- ally death can suspend one entity’s project but not another’s
- betrayal changes future cooperation preference
- near death can alter project choice or risk handling
- repeated success/failure can mutate directive weights or priority
- [x] **Goal**: Major narrative events (trauma, victory, betrayal) reliably shift strategic priorities.
- [x] **Event Interpretation**: Memories are converted to semantic `InterpretedLifeEvent` during appraisal.
- [x] **Watermarking**: Redundant processing is prevented via `last_interpreted_event_tick`.
- [x] **Divergence**: Personality (Loyalty) and Lived Structure (PlaceAttachment) modulate concern priority.
- [x] **Feedback**: Betrayal concerns now lower willingness to accept recruitment offers.

If you do not write these tests first, you will accidentally implement utility nudges and call it strategic change.

### Step 2 — Add an event-to-strategy interpreter

Create a dedicated layer that consumes interpreted events and emits strategic updates.

It should:

- inspect event type and impact
- inspect entity identity, attachments, obligations, and current project context
- produce concern additions, directive mutations, and project updates
- annotate reasons for explainability

Do not spread this logic across combat handlers, building handlers, and social handlers. Centralize the policy, even if the event sources stay distributed.

### Step 3 — Implement concern generation rules

Start with a bounded set of major event classes:

- home/place threat
- ally death or severe harm
- betrayal / contract breach
- near death / severe trauma
- major public success
- repeated objective failure

For each class, define:

- when it becomes a concern
- urgency
- provenance
- likely project interaction
- expiry or resolution semantics

This will give you an explicit pressure layer instead of invisible score spikes.

### Step 4 — Implement directive mutation rules

Do this conservatively.

A sensible first pass:

- major single events can strengthen/weaken an existing directive
- repeated events above threshold can add a new acquired directive
- some events can mark a directive as conflicted or deprioritized

Examples:

- `protect_home` strengthened after home attack
- `seek_safety` strengthened after repeated near-death events
- `trust_allies` weakened after repeated betrayal/breach
- `uphold_faction` strengthened after public defense success

Keep it deterministic and threshold-based.

### Step 5 — Implement project reprioritization rules

Now translate concerns and directive mutation into active strategy changes.

This needs:

- suspend current project when concern outranks it
- replace current objective when event is more urgent and irreversible
- preserve interrupted project for later resumption
- possibly transform a project rather than simply dropping it

This is the milestone where Milestone 2 continuity and Milestone 5 consequence finally meet.

### Step 6 — Feed outcomes back into future cooperation and search

Event-driven reprioritization must connect to prior milestones.

Examples:

- betrayal lowers willingness to recruit similar allies
- home threat increases return-home and defense weighting
- repeated false leads lowers trust in rumor sources
- public success improves recruitment response or obligation load
- severe failure changes willingness to reattempt risky blockers

That is how the system accumulates a life history rather than isolated reactions.

### Step 7 — Expose why reprioritization happened

You will need structured reasons.

At minimum, explainability should show:

- triggering event
- created concern or directive change
- old project
- new project or suspension outcome
- major weighting factors like attachment, obligation, irreversibility, or betrayal memory

Without this, Milestone 5 will be impossible to debug.

---

## What the implementation should probably look like

## A. Add an event-to-strategy interpreter service

Create something like:

- `src/ai/event_strategy_interpreter.py`
- `EventStrategyInterpreter`

Its job:

- consume interpreted events or turning points
- evaluate strategic significance
- emit `StrategicUpdate` plus reason records

That is cleaner than scattering reprioritization heuristics in `AIBrain` or `ActionSystem`.

## B. Add a reprioritization evaluator

Create something like:

- `src/ai/strategic_reprioritization.py`
- `StrategicReprioritizationService`

Its job:

- compare active project against new concern pressure
- weigh urgency, irreversibility, attachment, obligation, and continuity cost
- decide keep, suspend, replace, or transform

This should remain bounded and deterministic. Do not turn it into a giant optimization problem.

## C. Reuse turning points and interpreted events as inputs

Do not invent a second event system. The reference notes already make it clear that narrative memory, interpreted life events, and turning points exist and should become causal. Reuse those outputs as input to strategic mutation.

## D. Keep private meaning separate from public consequence

This matters.

An entity may privately interpret an event as humiliation, grief, or duty, while the world only sees reputation gain or loss. Both should matter, but they should not be conflated.

So keep separate:

- private concern / directive mutation
- public reputation / contract effect

Otherwise every internal event becomes a public status shift, which is lazy design.

---

## TDD sequence for Milestone 5

Use this order.

### Test batch A — concern generation from major events

Write failing tests that prove:

- home threat generates concern for attached entities
- ally death generates concern for socially invested entities
- betrayal generates concern or contract aversion
- near death generates recovery/reassessment concern

Then implement concern-generation rules.

### Test batch B — directive mutation

Write failing tests that prove:

- repeated near death can strengthen safety-oriented directives
- repeated defense success can strengthen protector/faction directives
- repeated betrayal can weaken trust/cooperation-oriented directives
- mutation is threshold-based, not arbitrary

Then implement directive mutation rules.

### Test batch C — project suspension and replacement

Write failing tests that prove:

- urgent concern can suspend a lower-priority project
- interrupted project is preserved for later resumption
- some events transform a project rather than simply replacing it
- old and new project state is explainable

Then implement project reprioritization.

### Test batch D — divergent responses

Write failing tests that prove:

- two entities react differently to the same town threat based on attachment or role
- two entities react differently to betrayal based on trust history or personality
- two entities react differently to near death based on prior risk orientation or obligations

Then implement divergence logic using existing identity/attachment/history data.

### Test batch E — feedback into future behavior

Write failing tests that prove:

- betrayal affects later recruitment willingness
- home threat affects return-home or defense prioritization later
- repeated failure changes reattempt behavior for related projects
- public success changes future opportunity acceptance or cooperation attractiveness

Then wire reprioritization back into prior milestone systems.

That is the right order because it locks event consequence first, then enduring mutation, then branching, then downstream behavioral effect.

---

## Suggested file targets

Likely new or changed files:

- `src/ai/event_strategy_interpreter.py`
- `src/ai/strategic_reprioritization.py`
- `src/ai/brain.py`
- `src/core/models/strategy.py`
- `src/actions/base.py`
- `src/systems/gameplay/action_system.py`
- existing turning-point or interpreted-event modules
- social contract consequence handlers
- inspector / presenter modules for reprioritization visibility

Suggested tests:

- `tests/ai/test_event_to_concern_generation.py`
- `tests/ai/test_directive_mutation_from_events.py`
- `tests/ai/test_project_suspension_and_replacement.py`
- `tests/ai/test_divergent_event_responses.py`
- `tests/ai/test_reprioritization_feedback_loops.py`

---

## Definition of done for Milestone 5

Milestone 5 is done only when all of this is true:

- [x] major interpreted events can generate strategic concerns
- [x] events can strengthen, weaken, or acquire directives in a bounded way
- [x] urgent concerns can suspend, replace, or transform active projects
- [x] interrupted projects are preserved for later continuity
- [x] different entities can respond differently to the same event
- [x] event-driven changes affect later cooperation, search, or project choice
- [x] all of that is covered by deterministic tests

If events only change mood, you failed.
If events only nudge utility without changing strategic state, you failed.
If every entity responds the same way to the same event, you failed.
If reprioritization cannot be explained structurally, you failed.

---

## Milestone 5 checklist


- [x] Feed event consequences back into future project selection and risk handling

- [x] Prevent major events from evaporating after one tick

- [x] Keep private interpretation separate from public reputation consequence

- [x] Apply reputation effects only where events are socially visible

- [x] Avoid conflating internal grief/fear/duty with public fame or notoriety

- [x] Extend inspector/debug output to show triggering events, generated concerns, directive changes, and project suspension/replacement reasons

- [x] Extend presenter/API output if needed for explainability

- [x] Keep output structured and causal, not decorative prose

- [x] Add deterministic unit tests for event-to-concern mapping

- [x] Add deterministic unit tests for directive mutation logic

- [x] Add deterministic unit tests for reprioritization decisions

- [x] Add deterministic integration tests for project suspension/replacement/resume

- [x] Add deterministic integration tests for divergent event response

- [x] Confirm milestone definition of done with passing automated tests

Priority Plan

What you must change in mindset or assumptions:
Stop treating memory and turning points as narrative garnish. In this system they must become strategic causes.

What actions you must take immediately:
Write the anti-shallow tests first, then implement event-to-strategy interpretation, then directive mutation, then project reprioritization, then downstream feedback into cooperation and search.

What you must stop or eliminate:
Stop using mood shifts as a substitute for strategic change. Stop making all major events collapse into the same urgency bump. Stop making identical entities out of different histories.

The consequences and opportunity cost if you fail to change:
You will have a system that can carry projects and contracts but still has no real life history. That means the engine remains mechanically competent and emotionally empty, which is exactly the kind of clever-looking failure the design was trying to avoid.
