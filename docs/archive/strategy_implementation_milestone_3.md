---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

Good. Milestone 3 is where the system stops faking knowledge.

Up to Milestone 2, you can get continuity. That is necessary, but it is still not enough. An entity can carry a project across ticks and still be cheating if the world conveniently hands it exact answers. Milestone 3 is the point where projects start colliding with uncertainty, and the engine has to respond with investigation, detours, and blocker-driven behavior instead of silent omniscience. The design reference is explicit: without uncertainty, there is no search, no rumor, no suspense, and no divergence. Leads, blockers, and candidate regions are the substrate for that.

# Milestone 3 — Leads, uncertainty, blockers, and detours

## What this milestone actually delivers

At the end of Milestone 3, an entity should be able to:

- receive vague or partial information
- store it as a lead, not collapse it into a coordinate
- detect that a current project is blocked
- classify why it is blocked
- generate a detour objective instead of abandoning the project or magically knowing the answer
- keep a record of tested or failed leads so it does not behave like a goldfish

That is the difference between “goal with flavor text” and “search under uncertainty.”

What Milestone 3 still does **not** need:

- full party negotiation logic
- explicit contract economics
- deep emotional reprioritization from major events
- giant planner trees

This milestone is about epistemic discipline, not social depth yet.

---

## The real problem you are solving

Right now the biggest trap is obvious: you already have a belief system, gossip, guild intel, building interactions, and some progression hints, so it is tempting to pretend that is enough.

It is not enough.

Why? Because most of that still risks behaving like this:

- entity hears a rumor
- internal code translates rumor into exact actionable truth
- entity acts as if uncertainty never existed

That is architectural dishonesty. The design notes explicitly warn against this. A vague clue should generate a search space, not a marker. A blocker should create a detour, not a dead end or an invisible cheat.

---

## What must exist by the end of this milestone

You need four things.

### 1. First-class leads

A lead is partial, uncertain, source-bound information relevant to a project.

It should carry at least:

- stable ID
- related project or topic
- subject
- source
- certainty/confidence
- freshness
- direct vs indirect quality
- candidate places/entities/topics
- whether it has been tested
- whether it was contradicted or confirmed

Do not overload entity-memory beliefs for this. Entity beliefs and strategic leads overlap, but they are not the same thing. A belief answers “what I think is true.” A lead answers “what I think might be worth pursuing.” That distinction matters.

### 2. Explicit blockers

A blocker is the reason a project or objective cannot currently progress.

Start with a bounded blocker taxonomy:

- knowledge blocker
- location blocker
- capability blocker
- social blocker
- access blocker
- safety blocker
- resource blocker
- time-window blocker

Without an explicit blocker type, every failure becomes mush and the system cannot choose the right detour.

### 3. Candidate zones or hypotheses

This is where vague information lives before it becomes certainty.

Examples:

- several mountain regions might satisfy a rumor
- a material source is likely in one of three biomes
- a boss location is narrowed but not known
- an informant might exist in a certain settlement

This structure is what prevents rumor from collapsing into exact world truth.

### 4. Detour objective generation

Once a blocker is recognized, the system must generate a response that fits the blocker type.

Examples:

- capability blocker -> train / upgrade / gather better gear
- location blocker -> scout / gather rumor / inspect site
- social blocker -> recruit / repair trust / seek faction backing
- resource blocker -> earn gold / gather materials / trade
- safety blocker -> secure escort / delay / scout safer route

If blocker handling does not produce detours, Milestone 3 fails.

---

## The correct implementation order

### Step 1 — Write tests that forbid silent omniscience

This is the most important first move.

Write failing tests that prove:

- vague lead stays vague
- rumor does not immediately become exact location
- unknown target location produces a lead or hypothesis set, not a coordinate
- failed progress creates a blocker
- blocker creates a detour objective
- tested leads are remembered and not blindly retried

If you skip these tests, you will accidentally build a cheat engine and call it cognition.

### Step 2 — Extend the strategy schema just enough

Milestone 1 gave you the foundation. Now add what is missing for uncertainty.

You likely need:

- richer `LeadRecord`
- `HypothesisRecord` and/or `CandidateZoneRecord`
- blocker classification fields
- maybe a lightweight search-history or tested-lead record

Keep it bounded. Do not invent an academic knowledge graph. You only need enough structure to drive search and detour behavior. The implementation notes already point toward leads, blockers, and candidate zones as first-class units.

### Step 3 — Add lead producers

This is where you connect existing world systems to strategic uncertainty.

Natural first producers:

- guild intel
- class hall hints
- blacksmith material hints
- rumor/gossip exchange
- observed world facts that are partial or distant
- failed objective attempts

Do not make these producers return exact solutions. They should return leads with source quality and uncertainty.

### Step 4 — Add blocker detection

You need a dedicated blocker-detection layer, not ad hoc `if cannot progress` spaghetti spread through handlers.

A project/objective should be able to say:

- I cannot progress because I do not know where
- I cannot progress because I am too weak
- I cannot progress because I lack material or gold
- I cannot progress because I need allies
- I cannot progress because trust/access is insufficient
- I cannot progress because the route is too dangerous

That classification is what drives the next step.

### Step 5 — Add detour generation

Once blocker detection exists, build the smallest useful detour generator.

It should map blocker types to objective templates:

- `location_unknown` -> `gather_rumor`, `scout_region`, `ask_expert`
- `too_weak` -> `train`, `upgrade_gear`, `visit_class_hall`
- `need_resource` -> `gather_material`, `earn_gold`, `trade`
- `need_allies` -> `recruit_support`
- `unsafe_route` -> `scout_safer_path`, `delay_departure`

Do not try to generate deep chains yet. One blocker producing one reasonable detour objective is enough for this milestone.

### Step 6 — Add tested-lead memory

This is easy to underestimate and stupid to postpone.

If the system does not remember tested leads, it will loop into nonsense:

- hear clue
- try thing
- fail
- forget
- try same thing again

You need at least:

- lead tested flag
- last tested tick
- outcome classification
- contradiction/confirmation markers

That alone will remove a huge amount of fake intelligence.

### Step 7 — Feed detour results back into projects

Detours are not standalone mini-goals. They exist in service of blocked projects.

So when a detour succeeds:

- blocker weakens or resolves
- project can resume
- objective can advance
- lead confidence updates
- candidate zone set narrows

This closes the loop between Milestone 2 continuity and Milestone 3 uncertainty.

---

## What the implementation should probably look like

## A. Add a strategic knowledge layer, not just bigger beliefs

Do not keep stuffing more fields into whatever belief model already exists. That will turn the belief system into an incoherent junk drawer.

Create a small uncertainty-oriented strategic domain, probably adjacent to your strategy models:

- `LeadRecord`
- `HypothesisRecord`
- `CandidateZoneRecord`
- blocker type/status enrichment

This keeps tactical perception beliefs separate from strategic search artifacts.

## B. Add a blocker evaluation service

Create something like:

- `src/ai/strategic_blockers.py`
- `StrategicBlockerService`

Its job:

- inspect current project/objective
- identify what is preventing progress
- classify blocker
- emit blocker updates or detour recommendations

Do not bury all of this inside objective execution or building logic. You will regret that almost immediately.

## C. Add a detour generation service

Create something like:

- `src/ai/strategic_detours.py`
- `StrategicDetourService`

Its job:

- translate blocker type into one or more candidate detour objectives
- rank them cheaply
- return the smallest reasonable next move

Again, keep it modular. Otherwise Milestone 4 and 5 will turn your brain code into sludge.

## D. Reuse existing producers instead of inventing new content

You already have likely producers in the world:

- guild
- class hall
- blacksmith
- gossip
- observed regions/materials/threats

Use them.

The mistake would be adding a fake “lead generator” disconnected from the actual engine. The goal is to make existing systems emit typed strategic uncertainty, not to add more decorative systems.

---

## TDD sequence for Milestone 3

Use this order.

### Test batch A — leads stay uncertain

Write failing tests that prove:

- a vague rumor becomes a lead with uncertainty
- candidate zones or hypotheses are produced instead of an exact coordinate
- direct observation and indirect rumor are represented differently

Then implement lead storage and candidate-zone/hypothesis models.

### Test batch B — blockers are explicit

Write failing tests that prove:

- a project that cannot continue produces a classified blocker
- different failure causes produce different blocker types
- blocker records attach to the right project/objective

Then implement blocker detection.

### Test batch C — blockers generate detours

Write failing tests that prove:

- a location blocker creates an investigation detour
- a capability blocker creates a training/upgrade detour
- a resource blocker creates a gathering/earning detour
- a social blocker creates a recruit/trust detour

Then implement detour generation.

### Test batch D — tested leads are remembered

Write failing tests that prove:

- failed leads are marked tested
- confirmed leads increase confidence
- contradicted leads decrease confidence or become stale
- the same failed lead is not immediately retried without new information

Then implement tested-lead memory and lead outcome updates.

### Test batch E — project resumption after detour

Write failing tests that prove:

- once a detour resolves a blocker, the original project becomes resumable
- the strategic layer returns to the blocked project instead of losing continuity

Then wire results back into Milestone 2 continuity logic.

That is the right order because it forces you to preserve uncertainty first, then reason about failure, then recover from it.

---

## Suggested file targets

Likely new or changed files:

- `src/core/models/strategy.py`
- `src/ai/strategic_blockers.py`
- `src/ai/strategic_detours.py`
- `src/ai/brain.py`
- `src/actions/base.py`
- `src/systems/gameplay/action_system.py`
- building or presenter modules that currently emit hints or progression intel
- possibly API/inspector serializers for new lead/blocker structures

Suggested tests:

- `tests/ai/test_strategic_leads_and_uncertainty.py`
- `tests/ai/test_blocker_detection.py`
- `tests/ai/test_detour_generation.py`
- `tests/ai/test_tested_lead_memory.py`
- `tests/ai/test_project_resume_after_blocker_resolution.py`

---

## Definition of done for Milestone 3

Milestone 3 is done only when all of this is true:

- uncertain information is stored as leads, not collapsed into exact truth
- projects/objectives can become explicitly blocked
- blockers are classified, not generic failure mush
- blocker types produce different detour objectives
- tested leads are remembered and updated by outcome
- successful detours feed back into project continuity
- all of that is covered by deterministic tests

If leads collapse into coordinates, you failed.
If blockers do not exist as first-class state, you failed.
If detours do not emerge from blockers, you failed.
If tested leads are forgotten, you failed.

---

## Milestone 3 checklist

- [x] Add failing tests that prove vague information stays uncertain

- [x] Add failing tests that prove rumors do not collapse into exact coordinates

- [x] Add failing tests for candidate zones and/or hypothesis generation

- [x] Add failing tests for blocker classification

- [x] Add failing tests for blocker-driven detour objective generation [DONE in `tests/unit/ai/strategy/test_strategic_uncertainty.py`]

- [x] Add failing tests for tested-lead memory and retry prevention

- [x] Add failing tests for project resumption after blocker resolution

- [x] Extend `LeadRecord` to carry source, certainty, freshness, directness, candidate targets, and tested status

- [x] Add `HypothesisRecord` and/or `CandidateZoneRecord`

- [x] Add lifecycle and status fields for lead testing, confirmation, contradiction, and staleness

- [x] Enrich blocker modeling with explicit blocker types

- [x] Ensure blocker records link to the right project/objective

- [x] Add lead producers from guild intel [DONE in `src/core/logic/strategic_knowledge_ingestion.py`]

- [x] Add lead producers from class hall or progression hint systems

- [x] Add lead producers from blacksmith/material hint systems

- [x] Add lead producers from rumor/gossip sharing

- [x] Add lead producers from partial direct observation where appropriate

- [x] Prevent all producers from returning exact truth unless certainty is actually justified

- [x] Create a blocker detection service/module [DONE in `src/ai/strategy/blocker_inference.py`]

- [x] Detect knowledge/location blockers

- [x] Detect capability blockers

- [x] Detect resource blockers

- [x] Detect social/access blockers

- [x] Detect safety/route blockers

- [x] Emit blocker updates through typed strategic updates

- [x] Create a detour generation service/module [DONE in `src/ai/strategy/detour_suggestion.py`]

- [x] Map location blockers to investigation objectives

- [x] Map capability blockers to training/upgrade objectives

- [x] Map resource blockers to gather/earn/trade objectives

- [x] Map social blockers to recruit/trust-repair objectives

- [x] Map safety blockers to scout/delay/route objectives

- [x] Keep detour generation bounded and deterministic

- [x] Add tested-lead tracking

- [x] Mark leads as tested after investigation attempts

- [x] Record confirmation, contradiction, or failure outcomes

- [x] Update lead confidence and freshness based on outcomes

- [x] Prevent blind immediate retry of failed leads without new information

- [x] Feed blocker resolution back into project continuity

- [x] Resolve or weaken blockers when detours succeed

- [x] Narrow candidate zones when evidence improves

- [x] Resume original project when blocker pressure clears

- [x] Preserve current/interrupted project continuity from Milestone 2

- [x] Extend inspector/debug output to show leads, blockers, tested state, and candidate zones

- [x] Extend API/presenter output if needed for explainability

- [x] Keep visibility structured, not decorative prose

- [x] Add deterministic unit tests for lead modeling

- [x] Add deterministic unit tests for blocker detection

- [x] Add deterministic unit tests for detour generation

- [x] Add deterministic integration tests for blocker-to-detour-to-project-resume flow

- [x] Confirm milestone definition of done with passing automated tests

---

## Implementation Notes

### Epistemic Discipline (Leads & Uncertainty)
We have implemented a robust strategic knowledge layer that prevents "omniscient cheating."
- **LeadRecords**: Instead of immediately knowing coordinates, entities store `LeadRecord` instances with source confidence and `is_exhausted` flags. 
- **Candidate Zones**: Rumors specify broad regions (`CandidateZoneRecord`) rather than precise points, forcing entities to use the `INVESTIGATE` objective to narrow the search.
- **Knowledge Ingestion**: The `StrategicKnowledgeIngestionService` provides a centralized bridge for converting world intel (Guild info, rumors, blacksmith needs) into strategic leads and blockers.

### Blocker Inference & Detours
The `StrategicEvaluator` now detects when an objective is non-progressible.
- **BlockerInferenceService**: Classifies failures into typed blockers: `KNOWLEDGE` (missing location), `CAPABILITY` (underpowered), `MATERIAL` (missing items/gold), or `ACCESS` (physical barriers).
- **DetourSuggestionService**: Maps these blockers to remediation objectives. For example, a `KNOWLEDGE` blocker triggers a `detour_investigate_*` objective using the freshest available lead.
- **Resume Loop**: Once a detour objective is `RESOLVED`, the parent project's blocker is cleared, allows the commitment to resume in the next appraisal tick.

Priority Plan

What you must change in mindset or assumptions:
Stop assuming incomplete information is just a weaker version of complete information. It is a different kind of state, and the engine must model it honestly.

What actions you must take immediately:
Write the anti-cheating tests first, then implement leads and candidate zones, then blocker detection, then detour generation, then tested-lead memory.

What you must stop or eliminate:
Stop turning rumors into coordinates. Stop treating all project failure as the same thing. Stop letting the system retry failed leads with no memory.

The consequences and opportunity cost if you fail to change:
You will end up with agents that look strategic on paper but still act like they secretly know the map. That destroys suspense, divergence, and credibility, and it will poison every later milestone built on top of it.
