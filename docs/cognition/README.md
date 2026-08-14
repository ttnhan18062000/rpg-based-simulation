---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Cognition Subsystem

`src/cognition/` implements the entity's internal cognitive architecture — the layer between raw world state and domain-level decisions. It is a standalone subsystem with its own pipeline step (`SelfModelUpdatePhase`) and its own bundle type (`SelfModelBundle`).

---

## What the cognition subsystem IS

- The entity's internal model of **itself** (health, weaknesses, strengths, confidence)
- The entity's **capability estimates** (can it fight this enemy? can it craft this recipe?)
- The entity's **world knowledge** (what facts has it learned from providers?)
- The entity's **interpreted biological needs** (hunger → need.healing, sleep_debt → need.rest)

## What the cognition subsystem is NOT

- **Not strategy** — `src/strategy/` (bounded cognition capacity management) reads the self-model produced here but does not live here
- **Not domain decision logic** — `src/domains/motivation/` and `src/domains/perception/` consume cognition output but are separate systems
- **Not AI personality** — `src/ai/` (goal scoring, personality traits) is a separate subsystem
- **Not social or intelligence** — `src/systems/strategic_systems/intelligence.py` is the strategic decision engine; this subsystem produces the self-model that intelligence reads

---

## Subsystem files

| File | Pipeline step | What it does |
|---|---|---|
| `self_model_phase.py` | Orchestrator | Runs the 4-step pipeline; dirty check; emits trace events |
| `self_assessment.py` | Step 2 | Evaluates entity health, weaknesses, strengths, confidence, stress |
| `need_interpretation.py` | Step 3 | Converts self-awareness → prioritised need signals |
| `capability_estimate.py` | Step 4 | Scoped estimates: can entity fight/travel/gather/craft? |
| `knowledge_model.py` | Step 1 | Assimilates InformationResponse → KnowledgeFact/UnknownFact |
| `trace_events.py` | All steps | Typed observability events emitted for warehouse/history |

---

## Pipeline: SelfModelUpdatePhase

Runs every tick for all alive/active entities:

```
Step 1: Knowledge assimilation (KnowledgeModelService.assimilate)
         └─ Only if InformationResponse events exist for this entity this tick
         └─ Events sourced from AuthoritativeState.pending_self_model_information_events
            (compile-time-seeded, filtered by actor_id; confirmed matching code 2026-07-04,
            TCK-20260703-SIMQ-UPLIFT3-BRANCH-B — see self_model_contract.md's "Phase lifecycle"
            section for detail)
Step 2: Self-assessment (SelfAssessmentService.assess)
         └─ Dirty check: skip steps 3–4 if nothing changed
Step 3: Need interpretation (NeedInterpretationService.interpret)
         └─ Only if dirty check triggered
Step 4: Capability estimation (CapabilityEstimateService.estimate)
         └─ Only if caller provides CapabilityContext (scoped)
```

Output: `SelfModelBundle` written to `entity.self_model` via `EntityUpdate(self_model_bundle_set=...)`.

---

## Relationship to other subsystems

| Consumer | What it reads from cognition |
|---|---|
| `src/domains/motivation/` | `entity.self_model.needs.dominant_need` → route bias |
| `src/domains/perception/` | `entity.self_model.needs` → attention focus for salience scoring |
| `src/domains/adventure/` | Ad-hoc `CapabilityEstimateService.estimate()` call from `AdventureRouteScorer.score()` (GATHER_RESOURCE/CRAFT_UPGRADE only) → `confidence_bonus`; NOT via `entity.self_model.capabilities`, which remains empty in production (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) |
| `src/systems/strategic_systems/intelligence.py` | `entity.self_model` (full bundle) → blocker inference, project evaluation |
| `src/strategy/` | `entity.self_model` → cognition capacity limits |
| `src/world/motivation/pressure_resolver.py` | World-side, runs before the cognition step; provides need_profile/drive_profile that feed into need interpretation |
| `src/world/perception/gate.py` | World-side, runs before the perception gate step; determines which signals reach the entity |

---

## Detailed contracts

| Doc | Contents |
|---|---|
| [self_model_contract.md](self_model_contract.md) | Self-assessment algorithm, dirty check, phase lifecycle |
| [capability_and_knowledge_contract.md](capability_and_knowledge_contract.md) | Capability estimation formulas, knowledge model assimilation |
| [need_interpretation_contract.md](need_interpretation_contract.md) | Drive-to-need translation, urgency thresholds, trace events |
