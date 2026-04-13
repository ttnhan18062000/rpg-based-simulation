Here is the right high-level plan.

Your current instinct is directionally correct, but the order matters. Do **not** start with “export the graph” as the main feature. That is backward. First make the strategic state real, deterministic, and authoritative. Then make it visible. Then use that visibility to test the final-system path. That sequencing is exactly what the reference material is pushing toward: the missing piece is the persistent strategic layer above the tactical substrate, and Phase 1 is a contract layer, not optional prep.

## High-level roadmap

### Milestone 0 — Lock the test harness before feature work

This is the foundation for TDD. Define the minimal “final-system” execution path you trust for regression:

- headless run path = CLI or shared headless bootstrap
- deterministic seed
- fixed tick count
- result artifacts = replay + entity cognition export
- golden assertions = structural, not prose-based

The important correction is this: the CLI is already a good execution harness, but it is not yet a sufficient verification harness because replay is too shallow for full thinking validation. So this milestone defines the test surface before implementation starts.

**Tests first**

- A deterministic headless run finishes and produces artifacts.
- Re-running with the same seed produces the same strategic summary/export.
- The harness can select one or more target entities for inspection/export.

**Exit condition**
You have one stable end-to-end test path that the next milestones can progressively enrich.

---

### Milestone 1 — Strategic state foundation

This is the real start. Add the missing strategic stratum as first-class persisted state.

Scope:

- `StrategicState`
- typed records for directives, projects, objectives, concerns, leads, blockers, obligations, contracts
- attach `mind.strategic`
- add typed `StrategicUpdate`
- authoritative application in `ActionSystem`
- snapshot-safe and serialization-safe integration

This is straight from the Phase 1 reference, and it is the correct first milestone because without it everything else becomes hidden heuristics and string soup.

**Tests first**

- `MindAspect` contains valid empty `StrategicState` by default.
- Strategy records validate and serialize.
- `ActionProposal` carries `StrategicUpdate`.
- `ActionSystem` applies add/update/remove deterministically by stable ID.
- Snapshot copy preserves strategy without aliasing.
- Replay/API serialization does not break.

**Exit condition**
Strategic continuity exists as real state, not tactical residue.

---

### Milestone 2 — Strategic appraisal above tactical choice

Now make the brain use the new layer.

Scope:

- add a strategic appraisal pass before tactical deliberation
- maintain/select current project and current objective
- allow interruption, suspension, and resumption
- convert strategic objective into the narrow tactical slice

This is where the system stops re-deciding life direction every tick and starts carrying unfinished business across time. The design doc is explicit that this is the actual story machine: identity to directives to projects to objectives to action to interpretation back into identity and projects.

**Tests first**

- A project survives across multiple ticks.
- An entity resumes a suspended project after interruption.
- Tactical state can be explained by current project/objective, not only raw utility.
- Strong concerns or obligations can interrupt the current project in a predictable way.

**Exit condition**
The engine has project continuity, not just better next-tick scoring.

---

### Milestone 3 — Leads, uncertainty, and blockers

Now give the strategic layer search pressure instead of fake omniscience.

Scope:

- formalize uncertain leads
- add candidate zones / hypotheses
- add blocker types
- convert blocker detection into detour objectives
- promote guild, blacksmith, class-hall, rumor, and social intel into typed lead/blocker producers

This matters because uncertainty is where branching comes from. Without it, the engine is just executing hidden coordinates.

**Tests first**

- A vague clue becomes a lead, not a direct coordinate.
- A project blocked by low capability generates a training or upgrade detour.
- A project blocked by unknown location generates an investigation detour.
- Rejected or stale leads are recorded and do not get re-consumed blindly.

**Exit condition**
Projects can fail productively and branch into detours.

---

### Milestone 4 — Social contracts and non-solo viability

Turn social structure into decision-critical strategy instead of flavor.

Scope:

- formalize social contracts / party purpose / terms
- recruitment as a strategic objective
- party formation based on trust, fit, debt, reputation, obligations
- contract consequences for betrayal, refusal, or successful cooperation

The code already has social bonds and group machinery, but the reference is blunt: that is not enough. Cooperation needs explicit semantics and cost.

**Tests first**

- A non-solo-viable project triggers recruitment instead of blind solo execution.
- Candidate allies are filtered by trust/reputation/capability.
- A contract survives across ticks and influences later behavior.
- Breaking terms changes future recruitment viability.

**Exit condition**
Projects can require social coordination in a durable, testable way.

---

### Milestone 5 — Event-driven strategic reprioritization

This is where memory and place attachment start mattering causally.

Scope:

- translate major interpreted events into concerns, directive changes, or project mutation
- home/place threat handling
- betrayal / rescue / near-death / ally death effects on strategy
- reprioritization based on urgency, irreversibility, attachment, obligation, and emotional charge

Do not reduce this to utility nudges. That would miss the whole point of the design.

**Tests first**

- Home damage generates a concern and reprioritizes strategy for attached entities.
- Ally death can suspend an old project and create a revenge or protection concern.
- Repeated failure mutates recovery behavior rather than resetting to baseline.
- Different personalities/attachments respond differently to the same world event.

**Exit condition**
History changes future life direction.

---

### Milestone 6 — Exportable entity cognition graph

Only now should you build the export feature as a first-class artifact.

Scope:

- exporter for entity-centered cognition graph
- nodes: entity, directives, projects, objectives, concerns, blockers, leads, obligations, contracts, candidate zones, hypotheses, turning points, beliefs
- edges: owns, blocked_by, informed_by, generated_from, interrupted_by, bound_by, etc.
- lazy materialization and caching if needed
- output shape suitable for machine assertions and inspection

This should be derived from persisted state, not become a second source of truth. It is an observability layer over real strategic state. That matches your earlier requirement to “export the stored graph of an entity” and use it to test the whole thinking feature.

**Tests first**

- Export from empty strategy is valid and stable.
- Export from populated strategy produces the expected node/edge structure.
- Export is deterministic for the same input state.
- Export does not mutate entity state.

**Exit condition**
You have a canonical observable form of persisted cognition.

---

### Milestone 7 — Final-system CLI verification path

Now tie everything together into the production-like test flow you described.

Scope:

- unify or reuse canonical headless bootstrap
- run real world loop
- persist replay
- export selected entity cognition graphs at end-of-run
- assert structural invariants against both replay and graph export

This is the moment where “run CLI -> engine execution -> result” becomes a real regression path instead of a demo run.

**Tests first**

- Same seed, same ticks, same entity selection => same graph structure.
- A scenario designed to create a blocker/lead/project interruption actually does so.
- Replay strategic summary and exported graph agree on current project/objective.
- End-to-end run proves strategic continuity across multiple ticks.

**Exit condition**
You can test the whole thinking pipeline through a minimal final-system path.

---

## TDD order inside each milestone

For every milestone, use the same loop:

1. Write the narrowest failing structural test.
2. Implement the minimum model or application path.
3. Add one deterministic integration test.
4. Refactor only after invariants are locked.
5. Add inspection/export assertions last, not first.

That is the right discipline here because the biggest risk is architectural drift, not lack of ideas.

## Recommended delivery sequence

If you want the shortest path to something real and testable, do it in this exact order:

- Milestone 0
- Milestone 1
- Milestone 2
- Milestone 6
- Milestone 7
- Milestone 3
- Milestone 4
- Milestone 5

That is not the pure conceptual order. It is the fastest **useful** order.

Why? Because after Milestones 1 and 2, exporting the cognition graph and wiring the CLI verification path gives you a real inspection and regression surface early. Then the harder behavioral phases — uncertainty, social coordination, event reprioritization — can be added without flying blind.

## What I think you should build first

The first concrete implementation slice should be:

- strategic schema
- `mind.strategic`
- `StrategicUpdate`
- authoritative apply path
- one minimal project continuity test
- one minimal graph export for directives/projects/objectives
- one end-to-end CLI regression that asserts the export exists

## What you will have when this is done

### 1. A real strategic mind layer

Each entity will have a first-class `mind.strategic` state, not scattered pseudo-strategy hidden in `goal_scores`, memory prose, or metadata blobs. That state is typed, persisted, snapshot-safe, and authoritatively mutated through the same update pipeline as the rest of the engine.

### 2. Multi-tick continuity

An entity will be able to keep pursuing a project, suspend it, resume it, get interrupted by a stronger concern, and still preserve causal continuity. That means the simulation starts producing lives with unfinished business instead of endless tactical resets.

### 3. Investigation instead of fake omniscience

Entities will be able to hold uncertain leads, candidate zones, and blockers, then generate detours such as scouting, training, recruiting, or asking for information. That is the difference between “the system knows the answer already” and “the system has to search under uncertainty.”

### 4. Social cooperation with actual cost

Groups stop being proximity fluff. You get explicit contracts, recruitment logic, purpose-driven parties, and persistent consequences when terms are honored or broken. That turns social structure into a strategic force multiplier instead of a decorative layer.

### 5. History that actually changes behavior

Turning points, betrayals, home threats, ally deaths, and major successes stop being temporary score nudges. They become strategic causes of reprioritization, new concerns, mutated directives, and changed contract preferences. That is the point where the system starts producing different biographies, not just different moves.

### 6. A canonical cognition export

You will have an exportable entity cognition graph derived from persisted state, with stable nodes and edges for directives, projects, blockers, leads, obligations, contracts, beliefs, and turning points. That becomes your proof surface for “thinking,” not a hand-wavy demo artifact.

### 7. A real final-system regression path

You will be able to run a minimal production-like headless path, let the real engine execute, capture replay plus cognition export, and assert structural invariants. That is not just useful for testing. It is what prevents the system from rotting while you keep adding content.

## What you still will not have

You will not magically have a general planner that solves arbitrary world problems. You will have something better for this engine: a bounded, deterministic, inspectable strategic layer that produces durable lives inside your simulation constraints. That is enough. Chasing more than that too early is how you destroy the architecture.
