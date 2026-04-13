Good. Milestone 2 is where the system stops being a storage exercise and starts becoming a mind.

But do not fool yourself: this milestone is still **not** about making the AI globally smarter. It is about inserting a real **strategic appraisal layer above tactical choice** so the engine can preserve continuity instead of re-deciding life direction every tick. The reference material is explicit: the tactical layer should remain narrow, and the missing loop is identity to directives to projects to objectives to local action to interpreted events back into updated strategy.

# Milestone 2 — Strategic appraisal and project continuity

## What this milestone actually delivers

At the end of Milestone 2, an entity should be able to:

- keep pursuing the same project across multiple ticks
- derive a current objective from that project
- suspend work when something stronger interrupts it
- resume that work later
- explain current tactical behavior in terms of project/objective continuity, not just flat utility scores

That is the first point where the engine starts having **unfinished business** instead of endlessly refreshed tactical intent.

What Milestone 2 does **not** need yet:

- deep uncertainty search
- social contract negotiation
- major event-driven identity mutation
- full investigation trees

Those come later. Right now you are only wiring durable strategic continuity into the existing brain pipeline.

---

## The correct implementation order

### Step 1 — Write continuity tests before touching `AIBrain`

Do not start by editing evaluators. That is how people create spaghetti.

Start by defining the behaviors that must now be true:

- a current project can persist across ticks
- a current objective can persist under that project
- an interruption can suspend the project
- the project can later resume
- tactical state chosen after strategic appraisal aligns with the active project/objective

If you cannot express those as tests, you do not understand the milestone well enough to implement it.

### Step 2 — Add a strategic appraisal stage to the brain pipeline

The reference note already points to the right insertion point: before tactical deliberation, not inside it. The current code already has a staged brain pipeline; Milestone 2 adds a strategic pass above the existing tactical evaluator rather than stuffing more logic into local goal scoring.

Conceptually, the order becomes:

1. perception / memory refresh
2. strategic appraisal
3. choose or maintain current project
4. choose current objective
5. translate current objective into tactical goal/state bias
6. run tactical deliberation on that narrowed slice
7. emit normal proposal plus strategic state updates if needed

That is the whole move. You are not replacing tactical AI. You are subordinating it.

### Step 3 — Introduce a bounded active slice

This is non-negotiable.

The design doc is blunt: the mind should not reason over the entire latent possibility space every tick. The entity should only consider a bounded active slice shaped by urgency, salience, commitments, proximity, obligations, blockers, and opportunities.

So Milestone 2 needs a **strategic working set**, not just a giant rescore of all directives and projects.

A good first pass:

- active concerns
- current project
- maybe one or two top suspended projects
- urgent obligations
- direct blockers tied to current project
- direct objective candidates under current project

That is enough. Anything broader in Phase 2 is you getting lost in abstraction.

### Step 4 — Add project commitment logic

Right now the obvious failure mode is tactical churn wearing strategic labels.

You need rules that make project continuity sticky:

- keep current project unless a materially stronger interruption appears
- use commitment windows or lock semantics
- treat project switching as costly
- allow suspension rather than deletion
- record the interrupted project so it can resume later

This is where you start using fields like:

- `current_project_id`
- `current_objective_id`
- `interrupted_project_id`
- `project_lock_until`

Those already fit the strategic state direction established in Milestone 1 and the implementation notes.

### Step 5 — Derive objectives from projects

Do not let projects map directly to actions. That would skip the middle layer and flatten the design.

Milestone 2 needs the first real `project -> objective -> tactical` bridge.

Examples:

- project: `become_stronger`
- objective: `visit_class_hall`
- tactical translation: move to hall / interact / rest if needed

Or:

- project: `defend_home_region`
- objective: `return_home`
- tactical translation: path home / avoid distractions / prioritize movement

At this stage the objective selector can stay simple:

- choose the current top unresolved objective under the project
- if none exists, derive a trivial objective from project type/status
- do not introduce deep planner recursion yet

### Step 6 — Translate objectives into tactical pressure, not direct hard overrides

This matters.

The tactical layer still needs to own local execution. Strategic appraisal should **bias and narrow**, not completely bypass local reasoning.

That means the strategic layer should influence:

- candidate goals
- score boosts
- state preference
- location targets
- building interaction preference
- interruption tolerance

It should not hardcode raw actions except in the most direct cases.

Otherwise you will just rebuild a worse planner on top of the tactical layer.

### Step 7 — Persist strategic continuity through typed updates

If strategic appraisal mutates project/objective state, it must still use the authoritative update discipline from Milestone 1.

That means the brain can produce:

- set current project
- set current objective
- suspend project
- resume project
- update project status/priority
- update interruption metadata

But the actual mutation still goes through the proposal/update/application pipeline. No direct live entity mutation. The Phase 1 notes already made that boundary explicit, and you do not get to relax it now because behavior has started.

---

## What the actual implementation should probably look like

## A. Add a strategic evaluator service

Do not bury this inside the goal evaluator.

Create something like:

- `src/ai/strategic_appraisal.py`
- `StrategicAppraisalService`
- maybe `StrategicSelectionResult`

Its job is:

- read `mind.strategic`
- inspect current/suspended projects, concerns, obligations
- return chosen `project_id`, `objective_id`, interruption info, and tactical bias hints

That gives you separation of concerns and keeps later milestones from bloating `AIBrain` into a landfill.

## B. Extend the AI context

The appraisal layer will need context beyond raw project records:

- current tick
- entity state
- snapshot
- current tactical state
- maybe nearby threats/opportunities
- maybe building access

So extend whatever context object the brain already uses, instead of passing random loose arguments everywhere.

## C. Add structured explanation fields

You will need visibility into why a project persisted or got interrupted.

So add or reuse structured driver fields that can capture:

- kept current project due to commitment lock
- switched to concern due to urgency
- resumed suspended project because blocker cleared
- preferred objective because project stage is incomplete

This is not optional. Without structured reasons, debugging Milestone 2 will become guesswork. The codebase already leans toward explainability, so continue that discipline.

## D. Keep objective classes minimal in Phase 2

Use a tiny vocabulary first:

- go to place
- interact with building
- train / level-capability step
- return home
- pursue target
- maintain / rest for project readiness

Do not jump into full investigation, recruiting, route unlocking, or social repair yet. Those belong to later milestones.

---

## TDD sequence for Milestone 2

Use this order.

### Test batch A — project persistence

Write failing tests that prove:

- entity with active project keeps same `current_project_id` across several ticks
- `current_objective_id` also persists when nothing stronger interrupts

Then implement the simplest maintain-current-project logic.

### Test batch B — interruption

Write failing tests that prove:

- a high-priority concern interrupts the current project
- interrupted project is recorded
- current project changes predictably

Then implement interruption rules.

### Test batch C — resumption

Write failing tests that prove:

- once interruption pressure is gone, the entity can resume the previously interrupted project
- resumed project restores a valid current objective

Then implement resume logic.

### Test batch D — objective bridge

Write failing tests that prove:

- a project yields a concrete current objective
- tactical state selection reflects that objective
- current objective narrows tactical possibilities instead of random tactical scoring taking over

Then implement project-to-objective and objective-to-tactical translation.

### Test batch E — explainability

Write failing tests that prove:

- structured explanation includes strategic reasons
- explanations show whether project was kept, interrupted, or resumed

Then add explanation records.

That is the right sequence because it locks continuity first, then branching, then observability.

---

## Suggested file targets

Likely new or changed files:

- `src/ai/brain.py`
- `src/ai/strategic_appraisal.py` or similar
- `src/ai/context.py` or equivalent context carrier
- `src/actions/base.py`
- `src/systems/gameplay/action_system.py`
- `src/api/presenters/ai_presenter.py`
- possibly strategy model file for project/objective status fields

Suggested tests:

- `tests/ai/test_strategic_project_persistence.py`
- `tests/ai/test_strategic_interruption_and_resume.py`
- `tests/ai/test_project_to_objective_translation.py`
- `tests/ai/test_strategic_explainability.py`

---

## Definition of done for Milestone 2

Milestone 2 is done only when all of this is true:

- the brain has a distinct strategic appraisal pass before tactical deliberation
- an entity can maintain a current project across ticks
- that project maps to a current objective
- interruptions suspend rather than erase continuity
- suspended work can resume later
- tactical behavior is measurably shaped by the active project/objective
- all of that is covered by deterministic automated tests

If you do not have resumption, you do not have continuity.
If you do not have interruption, you do not have branching.
If you do not have the objective bridge, you are still flattening strategy into tactics.

---

## Milestone 2 checklist

- [x] Add failing tests for project persistence across multiple ticks

- [x] Add failing tests for objective persistence under a stable project

- [x] Add failing tests for project interruption by a stronger concern or obligation

- [x] Add failing tests for resuming a suspended project

- [x] Add failing tests proving tactical behavior aligns with current objective

- [x] Add failing tests for strategic explainability fields

- [x] Create a dedicated strategic appraisal service/module [DONE in `src/ai/strategy/strategic_evaluator.py`]

- [x] Insert strategic appraisal into the brain pipeline before tactical deliberation [DONE in `src/ai/brain.py`]

- [x] Extend AI context to include strategic state and needed appraisal inputs

- [x] Implement bounded active-slice selection for strategic reasoning [DONE in `src/ai/strategy/candidate_builder.py`]

- [x] Include current project, urgent concerns, relevant obligations, and direct blockers in the active slice

- [x] Avoid whole-graph rescore every tick

- [x] Implement maintain-current-project logic

- [x] Implement project commitment / lock behavior [DONE in `src/ai/strategy/interruption.py`]

- [x] Implement cost or threshold for project switching

- [x] Persist `current_project_id`

- [x] Persist `current_objective_id`

- [x] Persist `interrupted_project_id`

- [x] Persist `project_lock_until` or equivalent continuity field

- [x] Implement interruption rules for stronger concerns/obligations

- [x] Mark current project as suspended instead of deleting it [DONE]

- [x] Record interruption cause

- [x] Implement resume logic once interruption pressure clears

- [x] Implement project-to-objective derivation [DONE in `src/ai/strategy/objective_derivation.py`]

- [x] Support minimal objective classes for Phase 2

- [x] Implement objective-to-tactical biasing [DONE in `src/ai/strategy/objective_to_goal_mapper.py`]

- [x] Narrow tactical candidate space from strategic objective

- [x] Keep tactical layer in control of local execution

- [x] Avoid hardcoding full action plans at the strategic layer

- [x] Emit strategic continuity updates through typed updates

- [x] Route project/objective continuity mutations through authoritative application

- [x] Avoid direct live mutation from the brain

- [x] Add structured strategic reason/explanation records

- [x] Expose keep/switch/suspend/resume reasons in explainability output

- [x] Verify inspection/debug surfaces can show current project/objective state

- [x] Add deterministic integration tests for multi-tick continuity

- [x] Add deterministic integration tests for interruption and resumption

- [x] Verify no brittle churn under small score fluctuations

- [x] Confirm milestone definition of done with passing automated tests

---

## Implementation Notes

### Strategic Appraisal Pass
The `AIBrain` pipeline has been extended with a dedicated `_strategic_appraisal_phase`. This pass occurs *after* perception but *before* tactical goal selection. It uses the `StrategicEvaluator` to choose a core commitment (Project or Concern) and derive a specific `Objective`.

### Continuity & Interruption
We utilize the `StrategicInterruptionService` to handle the tension between sticking to a current project and reacting to new concerns.
- **Hysteresis**: The `project_lock_until` field ensures that once a project is chosen, the entity stays committed for a minimum duration (e.g., 50 ticks) unless a critical threshold is breached.
- **Interruption Threshold**: Entities compare a new candidate's priority against (current priority + threshold + persistence boost). This prevents "jitter" and ensures strategic stability.
- **Suspension**: When interrupted, the current project is marked as `StrategicStatus.SUSPENDED` and its ID is stored in `interrupted_project_id`, allowing for later resumption once the interrupter is resolved.

### Objective Derivation
The `ObjectiveDerivationService` maps high-level commitments to actionable `ObjectiveRecord` instances. These objectives are then translated into tactical utility biases by the `ObjectiveToGoalMapper`, ensuring that the tactical layer remains focused on strategic goals without losing the ability to handle immediate needs (e.g., survival).

Priority Plan

What you must change in mindset or assumptions:
Stop thinking strategy means “pick a bigger goal.” Strategy here means continuity, interruption, and resumability above tactics.

What actions you must take immediately:
Write the persistence, interruption, and resumption tests first. Then add a dedicated strategic appraisal stage. Then wire the project-objective-tactical bridge.

What you must stop or eliminate:
Stop letting the tactical layer impersonate long-term intent. Stop rescoring life direction from scratch every tick. Stop skipping the objective layer.

The consequences and opportunity cost if you fail to change:
You will keep building an engine that looks richer in code but still behaves like a reactive state machine with better labels. That wastes the entire point of Milestone 1.
